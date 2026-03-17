#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Output Service - Write processed colors to output destination

Configuration via OUTPUT_DESTINATION in .env:
  local  – append with duplicate prevention to local Excel (default)
  s3     – upload one file per sub-asset to S3
  both   – append locally AND upload per sub-asset to S3

Duplicate prevention:
  Rows whose MESSAGE_ID already exists in the local file are replaced by the
  newest version (old entry removed, new one appended).  No row count limits.

S3 output:
  Each run groups processed rows by SECTOR (which maps to a CLO sub-asset ID).
  ALL columns are always written to S3 — no column filtering at write time.
  Column visibility (CLO config) is applied only at READ time (search API layer)
  so that historical data is never lost when an admin changes column settings.
  S3 key pattern:  {S3_PREFIX}{SECTOR}/Processed_Colors_{SECTOR}.{S3_FILE_FORMAT}
"""
import io
import os
import pandas as pd
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import logging
import threading
from models.color import ColorProcessed
from services.output_destination_factory import get_output_destination
from services.s3_destination import S3Destination
from storage_config import storage

logger = logging.getLogger(__name__)

# Computed output columns that are always kept regardless of CLO visible_columns config.
# These are not raw-input columns so they won't appear in clo_mappings visible_columns.
_ALWAYS_INCLUDE = frozenset({
    'PROCESSED_AT', 'PROCESSING_TYPE',
    'RANK', 'BIAS', 'COV_PRICE', 'PERCENT_DIFF', 'PRICE_DIFF',
    'CONFIDENCE', 'DIFF_STATUS', 'IS_PARENT', 'PARENT_MESSAGE_ID', 'CHILDREN_COUNT',
})


class OutputService:
    """
    Service for writing processed color data to configured output destination(s).
    Supports: Local Excel files, AWS S3, or both.
    """

    def __init__(self, output_file_path: str = None):
        if output_file_path is None:
            # Respect OUTPUT_DIR env var if set; otherwise default to Data-main/ root
            output_dir = os.getenv("OUTPUT_DIR", "").strip()
            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
                output_file_path = Path(output_dir) / "Processed_Colors_Output.xlsx"
            else:
                base_dir = Path(__file__).parents[4]
                output_file_path = base_dir / "Processed_Colors_Output.xlsx"

        self.output_file_path = str(output_file_path)
        self._dest_type = os.getenv("OUTPUT_DESTINATION", "local").lower()
        self._preserve_history = os.getenv("OUTPUT_PRESERVE_HISTORY", "true").lower() != "false"

        # Destination instances (primarily used for S3 uploads)
        self.destination = get_output_destination()
        self.use_multiple_destinations = isinstance(self.destination, list)
        self._cache_lock = threading.Lock()
        self._cached_df: Optional[pd.DataFrame] = None

        # Resolve S3 destination for per-CLO uploads
        if self._dest_type == "s3":
            self._s3_dest = self.destination if isinstance(self.destination, S3Destination) else None
        elif self._dest_type == "both":
            dests = self.destination if isinstance(self.destination, list) else [self.destination]
            self._s3_dest = next((d for d in dests if isinstance(d, S3Destination)), None)
        else:
            self._s3_dest = None

        logger.info(
            f"OutputService initialized | mode={self._dest_type} | "
            f"preserve_history={self._preserve_history} | file={self.output_file_path}"
        )
        self._ensure_output_file()

    def _ensure_output_file(self):
        """Create output Excel file with headers if it does not yet exist."""
        if not os.path.exists(self.output_file_path):
            logger.info("Creating new output file with headers")
            df = pd.DataFrame(columns=[
                'RUN_ID', 'PROCESSED_AT', 'PROCESSING_TYPE',
                'MESSAGE_ID', 'TICKER', 'SECTOR', 'CUSIP', 'DATE',
                'PRICE_LEVEL', 'BID', 'ASK', 'PX', 'SOURCE', 'BIAS', 'RANK',
                'COV_PRICE', 'PERCENT_DIFF', 'PRICE_DIFF', 'CONFIDENCE',
                'DATE_1', 'DIFF_STATUS', 'IS_PARENT', 'PARENT_MESSAGE_ID', 'CHILDREN_COUNT',
            ])
            df.to_excel(self.output_file_path, index=False, engine='openpyxl')
            logger.info(f"Created output file: {self.output_file_path}")

    def _bump_output_version(self, action: str, run_id: Optional[int] = None, rows_changed: Optional[int] = None):
        """Persist lightweight output version metadata for cheap dashboard invalidation checks."""
        try:
            # Invalidate in-memory read cache on any output mutation.
            with self._cache_lock:
                self._cached_df = None

            current = storage.load("dashboard_output_version") or {}
            seq = int(current.get("seq", 0) or 0) + 1
            payload = {
                "seq": seq,
                "updated_at": datetime.now().isoformat(),
                "action": action,
                "run_id": run_id,
                "rows_changed": rows_changed,
                "destination": self._dest_type,
            }
            storage.save("dashboard_output_version", payload)
        except Exception as e:
            logger.warning(f"Could not update dashboard output version metadata: {e}")
    
    # ── public write API ─────────────────────────────────────────────────────

    def append_processed_colors(
        self,
        colors: List[ColorProcessed],
        processing_type: str = "AUTOMATED",
        run_id: Optional[int] = None,
    ) -> int:
        """
        Persist processed colors to configured destination(s).

        local / both:
            Reads existing local Excel, removes any stale rows whose MESSAGE_ID
            appears in the new batch (newest version wins), appends, and writes
            back.  No row-count or file-size limits.

        s3 / both:
            Uploads one file per SECTOR (sub-asset) to S3.  ALL columns are
            always written — write path is never column-filtered.  Column
            visibility (CLO config) is applied at read time in the search API
            layer so no historical data is ever lost when an admin changes
            column settings.

        Returns the number of new records written.
        """
        # Always ensure the output file exists (even for empty runs)
        if self._dest_type in ("local", "both"):
            self._ensure_output_file()

        if not colors:
            logger.warning("No colors to append — 0 records passed the exclusion rules")
            return 0

        logger.info(
            f"Saving {len(colors)} processed colors "
            f"(type={processing_type}, dest={self._dest_type})"
        )
        new_df = self._colors_to_dataframe(colors, processing_type, run_id)

        if self._dest_type in ("local", "both"):
            self._append_to_local_file(new_df)

        if self._dest_type in ("s3", "both"):
            self._save_per_clo_to_s3(new_df)

        self._bump_output_version(
            action="append_processed_colors",
            run_id=run_id,
            rows_changed=len(new_df)
        )

        return len(new_df)

    # ── private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _colors_to_dataframe(
        colors: List[ColorProcessed],
        processing_type: str,
        run_id: Optional[int] = None,
    ) -> pd.DataFrame:
        """Convert a list of ColorProcessed objects to a flat DataFrame."""
        processed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        records = []
        for color in colors:
            records.append({
                'RUN_ID': run_id,
                'PROCESSED_AT': processed_at,
                'PROCESSING_TYPE': processing_type,
                'MESSAGE_ID': color.message_id,
                'TICKER': color.ticker,
                'SECTOR': color.sector,
                'CUSIP': color.cusip,
                'DATE': color.date.strftime("%Y-%m-%d") if color.date else None,
                'PRICE_LEVEL': color.price_level,
                'BID': color.bid,
                'ASK': color.ask,
                'PX': color.px,
                'SOURCE': color.source,
                'BIAS': color.bias,
                'RANK': color.rank,
                'COV_PRICE': color.cov_price,
                'PERCENT_DIFF': color.percent_diff,
                'PRICE_DIFF': color.price_diff,
                'CONFIDENCE': color.confidence,
                'DATE_1': color.date_1.strftime("%Y-%m-%d") if color.date_1 else None,
                'DIFF_STATUS': color.diff_status,
                'IS_PARENT': color.is_parent,
                'PARENT_MESSAGE_ID': color.parent_message_id,
                'CHILDREN_COUNT': color.children_count,
            })
        return pd.DataFrame(records)

    def _append_to_local_file(self, new_df: pd.DataFrame):
        """
        Merge new rows into the local Excel file.

        In history-preserving mode (default), rows from earlier runs are kept so
        search can show full run history for the same CUSIP/MESSAGE_ID.
        Legacy dedup behavior can be re-enabled with OUTPUT_PRESERVE_HISTORY=false.
        """
        try:
            existing_df = pd.read_excel(self.output_file_path, engine='openpyxl')
            logger.info(f"Existing records in local file: {len(existing_df)}")
        except Exception as e:
            logger.warning(f"Could not read existing file ({e}) — starting fresh.")
            existing_df = pd.DataFrame()

        # Optional legacy dedup path (kept for backward compatibility)
        if (not self._preserve_history) and len(existing_df) > 0 and 'MESSAGE_ID' in existing_df.columns:
            new_ids = set(new_df['MESSAGE_ID'].dropna())
            before = len(existing_df)
            existing_df = existing_df[~existing_df['MESSAGE_ID'].isin(new_ids)]
            replaced = before - len(existing_df)
            if replaced:
                logger.info(
                    f"Dedup: replaced {replaced} stale row(s) "
                    f"(same MESSAGE_ID — newest version kept)"
                )

        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
        combined_df.to_excel(self.output_file_path, index=False, engine='openpyxl')
        logger.info(
            f"✅ Local file written: {len(new_df)} new + "
            f"{len(existing_df)} retained = {len(combined_df)} total"
        )

    # ── S3 helpers ────────────────────────────────────────────────────────────

    def _apply_clo_column_filter(
        self, df: pd.DataFrame, sector: str, clo_service
    ) -> pd.DataFrame:
        """
        Project *df* through the current CLO column-visibility config.

        Logic:
        - Always keep RUN_ID + PROCESSED_AT + PROCESSING_TYPE + MESSAGE_ID + SECTOR
          (collectively the audit / dedup spine — never hidden).
        - Always keep _ALWAYS_INCLUDE computed columns.
        - Keep any column the admin has marked visible for *sector*.
        - Drop everything else.

        If the CLO service is unavailable or the sector has no mapping, all
        columns are retained (safe default).
        """
        # Spine columns that must always travel with the data
        _SPINE = frozenset({'RUN_ID', 'PROCESSED_AT', 'PROCESSING_TYPE', 'MESSAGE_ID', 'SECTOR'})

        if clo_service is None:
            return df

        visible_cols = clo_service.get_visible_columns_for_clo(str(sector))
        if not visible_cols:
            return df   # No mapping → keep all

        keep = [
            c for c in df.columns
            if c in visible_cols or c in _ALWAYS_INCLUDE or c in _SPINE
        ]
        if not keep:
            logger.warning(f"CLO filter for '{sector}' would remove all columns — keeping all")
            return df

        return df[keep]

    def _save_per_clo_to_s3(self, new_df: pd.DataFrame, *, force_sectors: list = None):
        """
        Append processed rows into per-sector S3 files with full-schema preservation.

        **Core principle — write path is NEVER column-filtered.**
        All columns produced by the processing pipeline are always written to S3
        regardless of what the admin has set in the CLO column-visibility config.
        Column visibility is a READ-TIME concern (applied in the search API layer
        before returning data to the frontend).  This guarantees:
          * Historical data is never deleted when an admin removes a column.
          * Adding a column later: old rows show NaN for it, new rows have values.
          * No schema inconsistency or data loss across config changes.

          **Per-sector strategy — download → merge → upload (history-preserving):**
          1. Download the existing accumulated file for this sector from S3
             (empty DF on first run — safe).
             2. Concat: pd.concat takes the column UNION — NaN fills any gaps
             caused by schema additions between runs.
             3. Upload: overwrites the sector’s S3 object with the full merged DF.

          Legacy dedup behavior can be re-enabled with OUTPUT_PRESERVE_HISTORY=false.

        S3 key pattern:
          {S3_PREFIX}{SECTOR}/Processed_Colors_{SECTOR}.{S3_FILE_FORMAT}
        """
        if self._s3_dest is None:
            logger.error("S3 destination not configured — skipping S3 upload")
            return

        # Fallback: no SECTOR column → single combined upload
        if 'SECTOR' not in new_df.columns or new_df['SECTOR'].isna().all():
            filename = "Processed_Colors_ALL"
            existing = self._s3_dest.load_output(filename)
            if (not self._preserve_history) and len(existing) > 0 and 'MESSAGE_ID' in existing.columns:
                new_ids = set(new_df['MESSAGE_ID'].dropna())
                existing = existing[~existing['MESSAGE_ID'].isin(new_ids)]
            merged = pd.concat([existing, new_df], ignore_index=True)
            result = self._s3_dest.save_output(merged, filename)
            logger.info(f"S3 fallback (no SECTOR): {result.get('message', result)}")
            return

        # Determine which sectors to process
        if force_sectors is not None:
            sectors = [s for s in force_sectors if str(s).strip()]
        else:
            sectors = [s for s in new_df['SECTOR'].dropna().unique() if str(s).strip()]

        logger.info(f"S3 per-CLO upload ({len(sectors)} sub-asset(s)): {sectors}")

        for sector in sectors:
            filename = f"{sector}/Processed_Colors_{sector}"

            # Step 1: download existing accumulation for this sector
            try:
                existing_df = self._s3_dest.load_output(filename)
            except Exception as e:
                logger.warning(f"Could not download existing S3 data for '{sector}': {e} — starting fresh")
                existing_df = pd.DataFrame()

            # Step 2: optional legacy dedup — remove rows superseded by new batch
            new_sector_df = new_df[new_df['SECTOR'] == sector].copy() if 'SECTOR' in new_df.columns else new_df.copy()
            if (not self._preserve_history) and len(existing_df) > 0 and 'MESSAGE_ID' in existing_df.columns and len(new_sector_df) > 0:
                new_ids = set(new_sector_df['MESSAGE_ID'].dropna())
                before = len(existing_df)
                existing_df = existing_df[~existing_df['MESSAGE_ID'].isin(new_ids)]
                replaced = before - len(existing_df)
                if replaced:
                    logger.info(f"S3 dedup [{sector}]: replaced {replaced} stale row(s)")

            # Step 3: merge — column union, NaN fills schema gaps (no data loss)
            merged_df = pd.concat([existing_df, new_sector_df], ignore_index=True)

            # Step 4: upload full schema — NO column filtering here
            result = self._s3_dest.save_output(merged_df, filename)
            if result.get('status') == 'success':
                logger.info(
                    f"✅ S3 [{sector}]: {result['message']} "
                    f"({len(merged_df)} total rows, {len(merged_df.columns)} cols)"
                )
            else:
                logger.error(f"❌ S3 [{sector}]: {result.get('message', 'unknown error')}")
    
    def get_processed_count(self) -> dict:
        """
        Get statistics about processed data from configured destination
        
        Returns:
            Dictionary with counts by processing type
        """
        try:
            # Use abstracted reader
            from services.processed_data_reader import get_processed_data_reader
            reader = get_processed_data_reader()
            df = reader.read_processed_data()
            
            total = len(df)
            automated = len(df[df['PROCESSING_TYPE'] == 'AUTOMATED'])
            manual = len(df[df['PROCESSING_TYPE'] == 'MANUAL'])
            parents = len(df[df['IS_PARENT'] == True])
            children = len(df[df['IS_PARENT'] == False])
            
            return {
                'total_processed': total,
                'automated': automated,
                'manual': manual,
                'parents': parents,
                'children': children,
                'output_file': self.output_file_path
            }
        except Exception as e:
            logger.error(f"Error reading processed data: {e}")
            return {
                'total_processed': 0,
                'automated': 0,
                'manual': 0,
                'parents': 0,
                'children': 0,
                'output_file': self.output_file_path
            }
    
    def clear_output_file(self):
        """Clear all data from output file (keep headers)"""
        logger.warning("Clearing output file")
        # Remove existing file so _ensure_output_file recreates it fresh
        if os.path.exists(self.output_file_path):
            os.remove(self.output_file_path)
        self._ensure_output_file()
        self._bump_output_version(action="clear_output_file", rows_changed=0)
        logger.info("Output file cleared")

    def delete_run_output(self, run_id: int) -> dict:
        """
        Remove all output rows that belong to a specific automation run.

        Local: reads the Excel file, drops rows where RUN_ID == run_id, rewrites.
        S3:    re-uploads each affected CLO file without those rows.

        Returns a dict with 'deleted' (row count) and 'message'.
        """
        deleted_total = 0

        # ── local ────────────────────────────────────────────────────────────
        if self._dest_type in ("local", "both"):
            try:
                df = pd.read_excel(self.output_file_path, engine='openpyxl')
                if 'RUN_ID' in df.columns:
                    before = len(df)
                    df = df[df['RUN_ID'] != run_id]
                    deleted_local = before - len(df)
                    df.to_excel(self.output_file_path, index=False, engine='openpyxl')
                    deleted_total += deleted_local
                    logger.info(
                        f"✅ Deleted {deleted_local} row(s) for RUN_ID={run_id} from local file"
                    )
                else:
                    logger.warning(
                        "RUN_ID column missing in local output file — "
                        "rows from older runs cannot be targeted by run_id"
                    )
            except Exception as e:
                logger.error(f"Error deleting run output from local file: {e}")
                raise

        # ── S3 ────────────────────────────────────────────────────────────────
        # Single-file-per-sector design: each sector has one accumulated file
        # named {PREFIX}{SECTOR}/Processed_Colors_{SECTOR}.{ext}
        # To delete a run: download each sector file, filter out rows with
        # RUN_ID == run_id, then re-upload.  Sectors with no matching rows are
        # left unchanged (no re-upload needed).
        if self._dest_type in ("s3", "both") and self._s3_dest is not None:
            try:
                s3_client = self._s3_dest._get_s3_client()
                bucket = self._s3_dest.bucket_name
                prefix = self._s3_dest.prefix.lstrip('/')
                ext = f'.{self._s3_dest.file_format}'
                fmt = self._s3_dest.file_format

                # Find all Processed_Colors_*.{ext} sector files
                sector_keys = []
                paginator = s3_client.get_paginator('list_objects_v2')
                for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                    for obj in page.get('Contents', []):
                        key = obj['Key']
                        fname = key.split('/')[-1]
                        if fname.startswith('Processed_Colors_') and key.endswith(ext):
                            sector_keys.append(key)

                if not sector_keys:
                    logger.info(f"S3: no sector files found for RUN_ID={run_id} deletion")
                else:
                    for key in sector_keys:
                        try:
                            response = s3_client.get_object(Bucket=bucket, Key=key)
                            body = response['Body'].read()
                            if fmt == 'csv':
                                sector_df = pd.read_csv(io.BytesIO(body))
                            elif fmt == 'parquet':
                                sector_df = pd.read_parquet(io.BytesIO(body), engine='pyarrow')
                            else:
                                sector_df = pd.read_excel(io.BytesIO(body), engine='openpyxl')

                            if 'RUN_ID' not in sector_df.columns:
                                continue

                            before = len(sector_df)
                            sector_df = sector_df[sector_df['RUN_ID'] != run_id]
                            removed = before - len(sector_df)

                            if removed == 0:
                                continue  # Nothing to do for this sector

                            deleted_total += removed
                            # Re-upload the filtered file
                            buf = io.BytesIO()
                            if fmt == 'csv':
                                sector_df.to_csv(buf, index=False)
                            elif fmt == 'parquet':
                                sector_df.to_parquet(buf, index=False, engine='pyarrow')
                            else:
                                sector_df.to_excel(buf, index=False, engine='openpyxl')
                            buf.seek(0)
                            s3_client.put_object(
                                Bucket=bucket,
                                Key=key,
                                Body=buf.getvalue(),
                            )
                            logger.info(
                                f"✅ S3 [{key}]: removed {removed} row(s) for RUN_ID={run_id}"
                            )
                        except Exception as e:
                            logger.error(f"Error processing S3 sector file {key}: {e}")

            except Exception as e:
                logger.error(f"Error deleting run output from S3: {e}")

        if deleted_total == 0:
            return {
                "deleted": 0,
                "message": (
                    f"No rows found for RUN_ID={run_id}. "
                    "Run may have produced no output or used an older schema without RUN_ID."
                )
            }

        self._bump_output_version(
            action="delete_run_output",
            run_id=run_id,
            rows_changed=deleted_total
        )
        return {
            "deleted": deleted_total,
            "message": f"Deleted {deleted_total} output row(s) for RUN_ID={run_id}"
        }
    
    def read_processed_colors(
        self, 
        processing_type: str = None,
        limit: int = None,
        cusip: str = None,
        ticker: str = None,
        message_id: int = None,
        date_from: str = None,
        date_to: str = None
    ) -> List[dict]:
        """
        Read processed colors from configured output destination (local Excel or S3)
        FULLY ABSTRACTED - reads from local or S3 based on .env configuration
        
        Args:
            processing_type: Filter by "AUTOMATED" or "MANUAL" (None = all)
            limit: Maximum number of records to return
            cusip: Filter by specific CUSIP
            ticker: Filter by ticker symbol
            message_id: Filter by message ID
            date_from: Start date filter (YYYY-MM-DD)
            date_to: End date filter (YYYY-MM-DD)
            
        Returns:
            List of color dictionaries
        """
        try:
            # Use abstracted reader (works with local Excel or S3)
            from services.processed_data_reader import get_processed_data_reader
            reader = get_processed_data_reader()

            with self._cache_lock:
                cached = self._cached_df

            if cached is not None and len(cached) > 0:
                df = cached.copy()
                logger.info(f"Using in-memory processed-data cache: {len(df)} rows")
            else:
                # For local Excel: applying nrows is a genuine performance win (reading stops at row N).
                # For S3: nrows does NOT prevent full file downloads — skip the optimization.
                if self._dest_type == "local" and limit and limit < 100:
                    nrows_to_read = min(limit * 10, 2000)
                    logger.info(f"PERFORMANCE: Reading only {nrows_to_read} rows for limit={limit}")
                    df = reader.read_processed_data(nrows=nrows_to_read)
                else:
                    df = reader.read_processed_data()

                # Cache only full reads, not nrows-limited samples.
                if not (self._dest_type == "local" and limit and limit < 100):
                    with self._cache_lock:
                        self._cached_df = df.copy()
            
            if len(df) == 0:
                logger.warning("Processed data is empty")
                return []
            
            logger.info(f"Initial data loaded: {len(df)} rows")
            
            # Apply filters
            if processing_type:
                df = df[df['PROCESSING_TYPE'] == processing_type]
                logger.info(f"After processing_type filter: {len(df)} rows")
            
            if cusip:
                df = df[df['CUSIP'].str.upper() == cusip.upper()]
                logger.info(f"After cusip filter: {len(df)} rows")
            
            if ticker:
                df = df[df['TICKER'].str.upper() == ticker.upper()]
                logger.info(f"After ticker filter: {len(df)} rows")
            
            if message_id:
                df = df[df['MESSAGE_ID'] == message_id]
                logger.info(f"After message_id filter: {len(df)} rows")
            
            # Date range filtering
            if date_from or date_to:
                df['DATE_PARSED'] = pd.to_datetime(df['DATE'], errors='coerce')
                if date_from:
                    df = df[df['DATE_PARSED'] >= pd.to_datetime(date_from)]
                if date_to:
                    df = df[df['DATE_PARSED'] <= pd.to_datetime(date_to)]
                df = df.drop('DATE_PARSED', axis=1)
                logger.info(f"After date range filter: {len(df)} rows")
            
            # Sort by most recent date first (primary), then processed time (secondary)
            if 'DATE' in df.columns:
                df['DATE_PARSED'] = pd.to_datetime(df['DATE'], errors='coerce')
                if 'PROCESSED_AT' in df.columns:
                    df['PROCESSED_AT_PARSED'] = pd.to_datetime(df['PROCESSED_AT'], errors='coerce')
                    df = df.sort_values(['DATE_PARSED', 'PROCESSED_AT_PARSED'], ascending=[False, False])
                    df = df.drop('PROCESSED_AT_PARSED', axis=1)
                else:
                    df = df.sort_values('DATE_PARSED', ascending=False)
                df = df.drop('DATE_PARSED', axis=1)
                logger.info("Sorted by DATE (most recent first)")
            elif 'PROCESSED_AT' in df.columns:
                # Fallback if DATE column missing
                df = df.sort_values('PROCESSED_AT', ascending=False)
                logger.info("Sorted by PROCESSED_AT (fallback)")
            
            # Apply limit
            if limit:
                df = df.head(limit)
            
            # Convert to list of dicts
            records = df.to_dict('records')
            
            logger.info(f"✅ Returning {len(records)} processed colors")
            return records
            
        except Exception as e:
            logger.error(f"Error reading processed colors: {e}")
            return []


# Singleton instance
_output_service_instance = None

def get_output_service() -> OutputService:
    """Get singleton output service instance"""
    global _output_service_instance
    if _output_service_instance is None:
        _output_service_instance = OutputService()
    return _output_service_instance
