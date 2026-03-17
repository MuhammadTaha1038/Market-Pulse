#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Manual Color Processing Service - For Color Processing Page

This service handles the manual color workflow:
1. Import Excel → Show sorted preview
2. User selects/deletes rows and applies rules
3. Save processed colors to output file

This is SEPARATE from admin panel buffer logic.
"""
from typing import Dict, List, Optional, Tuple
import pandas as pd
from datetime import datetime
import logging
import os
import json
from pathlib import Path

from storage_config import storage
from models.color import ColorRaw, ColorProcessed
from services.ranking_engine import RankingEngine
from services.output_service import get_output_service
from services.column_config_service import get_column_config
from rules_service import apply_rules
from manual_upload_service import get_buffered_files
import logging_service

logger = logging.getLogger(__name__)

# Initialize services
ranking_engine = RankingEngine()
output_service = get_output_service()
column_config = get_column_config()

# Manual color session directory (temporary storage for preview)
MANUAL_SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "manual_color_sessions")
os.makedirs(MANUAL_SESSION_DIR, exist_ok=True)


class ManualColorSession:
    """
    Manages a manual color processing session
    """
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_file = os.path.join(MANUAL_SESSION_DIR, f"{session_id}.json")
        self.data = self._load_session()
    
    def _load_session(self) -> Dict:
        """Load session data from file"""
        if os.path.exists(self.session_file):
            with open(self.session_file, 'r') as f:
                return json.load(f)
        return {
            "session_id": self.session_id,
            "created_at": datetime.now().isoformat(),
            "original_filename": None,
            "raw_data": [],
            "sorted_data": [],
            "filtered_data": [],
            "applied_rules": [],
            "deleted_rows": [],
            "status": "new"
        }
    
    def save_session(self):
        """Save session data to file"""
        with open(self.session_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def update(self, **kwargs):
        """Update session data"""
        self.data.update(kwargs)
        self.data["updated_at"] = datetime.now().isoformat()
        self.save_session()
    
    def delete_session(self):
        """Delete session file"""
        if os.path.exists(self.session_file):
            os.remove(self.session_file)


def generate_session_id(user_id: int = 1) -> str:
    """Generate unique session ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"manual_color_{user_id}_{timestamp}"


def import_manual_colors(
    file_path: str,
    filename: str,
    user_id: int = 1
) -> Dict:
    """
    Step 1: Import Excel file and return sorted preview
    
    Args:
        file_path: Path to uploaded Excel file
        filename: Original filename
        user_id: User ID
    
    Returns:
        Dict with session_id, sorted preview data, and statistics
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"📂 Importing manual colors from: {filename}")
        
        # Read Excel file
        df = pd.read_excel(file_path)
        logger.info(f"✅ Read {len(df)} rows from Excel")
        
        # Validate required columns
        required_cols_objs = column_config.get_required_columns()
        # Extract just the oracle_name from each column object
        required_cols = [col['oracle_name'] for col in required_cols_objs if isinstance(col, dict)]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
        
        # Convert DataFrame to ColorRaw objects
        raw_colors = []
        parsing_errors = []
        
        for idx, row in df.iterrows():
            try:
                color_raw = ColorRaw(
                    message_id=int(row.get('MESSAGE_ID', idx)) if pd.notna(row.get('MESSAGE_ID')) else idx,
                    ticker=str(row.get('TICKER', '')) if pd.notna(row.get('TICKER')) else '',
                    sector=str(row.get('SECTOR', '')) if pd.notna(row.get('SECTOR')) else '',
                    cusip=str(row['CUSIP']) if pd.notna(row.get('CUSIP')) else '',
                    date=pd.to_datetime(row['DATE']) if pd.notna(row.get('DATE')) else datetime.now(),
                    price_level=float(row.get('PRICE_LEVEL', 0)) if pd.notna(row.get('PRICE_LEVEL')) else 0.0,
                    bid=float(row.get('BID', 0)) if pd.notna(row.get('BID')) else 0.0,
                    ask=float(row.get('ASK', 0)) if pd.notna(row.get('ASK')) else 0.0,
                    px=float(row.get('PX', 0)) if pd.notna(row.get('PX')) else 0.0,
                    source=str(row.get('SOURCE', 'MANUAL')) if pd.notna(row.get('SOURCE')) else 'MANUAL',
                    bias=str(row.get('BIAS', '')) if pd.notna(row.get('BIAS')) else '',
                    rank=int(row.get('RANK', 1)) if pd.notna(row.get('RANK')) else 1,
                    cov_price=float(row.get('COV_PRICE', 0)) if pd.notna(row.get('COV_PRICE')) else 0.0,
                    percent_diff=float(row.get('PERCENT_DIFF', 0)) if pd.notna(row.get('PERCENT_DIFF')) else 0.0,
                    price_diff=float(row.get('PRICE_DIFF', 0)) if pd.notna(row.get('PRICE_DIFF')) else 0.0,
                    confidence=int(row.get('CONFIDENCE', 5)) if pd.notna(row.get('CONFIDENCE')) else 5,
                    date_1=pd.to_datetime(row.get('DATE_1', row.get('DATE', datetime.now()))) if pd.notna(row.get('DATE_1')) or pd.notna(row.get('DATE')) else datetime.now(),
                    diff_status=str(row.get('DIFF_STATUS', '')) if pd.notna(row.get('DIFF_STATUS')) else ''
                )
                raw_colors.append(color_raw)
            except Exception as e:
                parsing_errors.append(f"Row {idx + 2}: {str(e)}")
                logger.warning(f"⚠️ Failed to parse row {idx + 2}: {e}")
        
        logger.info(f"✅ Parsed {len(raw_colors)} valid colors, {len(parsing_errors)} errors")
        
        # Apply sorting logic (RankingEngine)
        logger.info("🔄 Applying sorting logic...")
        sorted_colors = ranking_engine.run_colors(raw_colors)
        logger.info(f"✅ Sorted {len(sorted_colors)} colors")
        
        # Create session
        session_id = generate_session_id(user_id)
        session = ManualColorSession(session_id)
        
        # Convert to dict for storage
        raw_data_dict = [
            {
                "row_id": idx,
                "message_id": c.message_id,
                "ticker": c.ticker,
                "sector": c.sector,
                "cusip": c.cusip,
                "date": c.date.isoformat(),
                "price_level": c.price_level,
                "bid": c.bid,
                "ask": c.ask,
                "px": c.px,
                "source": c.source,
                "bias": c.bias,
                "rank": c.rank,
                "cov_price": c.cov_price,
                "percent_diff": c.percent_diff,
                "price_diff": c.price_diff,
                "confidence": c.confidence,
                "date_1": c.date_1.isoformat(),
                "diff_status": c.diff_status
            }
            for idx, c in enumerate(raw_colors)
        ]
        
        sorted_data_dict = [
            {
                "row_id": idx,
                "message_id": c.message_id,
                "ticker": c.ticker,
                "sector": c.sector,
                "cusip": c.cusip,
                "date": c.date.isoformat() if c.date else None,
                "price_level": c.price_level,
                "bid": c.bid,
                "ask": c.ask,
                "px": c.px,
                "source": c.source,
                "bias": c.bias,
                "rank": c.rank,
                "cov_price": c.cov_price,
                "percent_diff": c.percent_diff,
                "price_diff": c.price_diff,
                "confidence": c.confidence,
                "date_1": c.date_1.isoformat() if c.date_1 else None,
                "diff_status": c.diff_status,
                "is_parent": c.is_parent,
                "parent_message_id": c.parent_message_id,
                "children_count": c.children_count
            }
            for idx, c in enumerate(sorted_colors)
        ]
        
        # Save session
        session.update(
            original_filename=filename,
            raw_data=raw_data_dict,
            sorted_data=sorted_data_dict,
            filtered_data=sorted_data_dict.copy(),  # Initially same as sorted
            rows_imported=len(raw_colors),
            rows_valid=len(raw_colors) - len(parsing_errors),
            parsing_errors=parsing_errors,
            status="preview"
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Manual color import completed in {duration:.2f}s")
        
        return {
            "success": True,
            "session_id": session_id,
            "filename": filename,
            "rows_imported": len(raw_colors),
            "rows_valid": len(raw_colors) - len(parsing_errors),
            "parsing_errors": parsing_errors,
            "sorted_preview": sorted_data_dict,
            "statistics": {
                "total_rows": len(sorted_colors),
                "parent_rows": sum(1 for c in sorted_colors if c.is_parent),
                "child_rows": sum(1 for c in sorted_colors if not c.is_parent),
                "unique_cusips": len(set(c.cusip for c in sorted_colors))
            },
            "duration_seconds": duration
        }
        
    except Exception as e:
        logger.error(f"❌ Manual color import failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        }


def _load_buffered_manual_colors() -> Tuple[List[ColorRaw], List[str], List[int]]:
    """
    Read pending files from manual upload buffer and parse them into ColorRaw rows.

    Returns:
        (buffered_colors, warnings, consumed_buffer_ids)
    """
    buffered_colors: List[ColorRaw] = []
    warnings: List[str] = []
    consumed_buffer_ids: List[int] = []

    try:
        from manual_upload_service import (
            get_buffered_files,
            parse_excel_to_colors,
            read_buffered_entry_dataframe,
        )

        buffered_files = get_buffered_files()
        if not buffered_files:
            return buffered_colors, warnings, consumed_buffer_ids

        # Deduplicate by upload id — keep only the first occurrence so a stale
        # duplicate registry entry (e.g. from the self-heal recovery) never
        # causes the same physical file to be read more than once.
        seen_ids: set = set()
        deduped: list = []
        for _e in buffered_files:
            _eid = _e.get("id")
            if _eid is not None and _eid in seen_ids:
                logger.warning(f"⚠️ Skipping duplicate buffer entry id={_eid} (file: {_e.get('filename')})")
                continue
            seen_ids.add(_eid)
            deduped.append(_e)
        buffered_files = deduped

        for entry in buffered_files:
            file_path = entry.get("file_path")
            filename = entry.get("filename") or os.path.basename(str(file_path or "buffer_file"))

            if not file_path or not os.path.exists(file_path):
                msg = f"Buffered file missing: {filename}"
                logger.warning(msg)
                warnings.append(msg)
                continue

            try:
                df = read_buffered_entry_dataframe(entry)
                parsed_colors, parsing_errors = parse_excel_to_colors(df)

                buffered_colors.extend(parsed_colors)
                if parsed_colors and isinstance(entry.get("id"), int):
                    consumed_buffer_ids.append(entry["id"])
                if parsing_errors:
                    msg = f"{filename}: {len(parsing_errors)} row(s) could not be parsed"
                    logger.warning(msg)
                    warnings.append(msg)

                logger.info(f"📎 Loaded {len(parsed_colors)} buffered rows from {filename}")
            except Exception as file_err:
                msg = f"Failed reading buffered file {filename}: {file_err}"
                logger.warning(msg)
                warnings.append(msg)

    except Exception as e:
        msg = f"Unable to read manual upload buffer: {e}"
        logger.warning(msg)
        warnings.append(msg)

    return buffered_colors, warnings, consumed_buffer_ids


def _clear_consumed_buffer_entries(upload_ids: List[int]) -> int:
    """Remove consumed upload IDs from buffer and mark upload history as processed by manual save."""
    if not upload_ids:
        return 0

    try:
        from manual_upload_service import (
            get_buffered_files,
            save_buffered_files,
            get_upload_history,
            save_upload_history,
        )

        id_set = set(upload_ids)
        buffered_files = get_buffered_files()

        removed_entries = [entry for entry in buffered_files if entry.get("id") in id_set]
        remaining_entries = [entry for entry in buffered_files if entry.get("id") not in id_set]

        # Remove the actual buffered files from disk so they are not re-consumed.
        for entry in removed_entries:
            try:
                path = entry.get("file_path")
                if path and os.path.exists(path):
                    os.remove(path)
            except Exception as file_err:
                logger.warning(f"Failed removing buffered file for ID {entry.get('id')}: {file_err}")

        save_buffered_files(remaining_entries)

        history = get_upload_history()
        now_iso = datetime.now().isoformat()
        for h in history:
            if h.get("id") in id_set:
                h["status"] = "success"
                h["processing_time"] = now_iso
                h["rows_processed"] = h.get("rows_uploaded", 0)
                h["message"] = "Processed via Manual Color save (included in combined session)"
        save_upload_history(history)

        logger.info(f"🧹 Cleared {len(removed_entries)} consumed buffered upload(s): {sorted(id_set)}")
        return len(removed_entries)
    except Exception as e:
        logger.warning(f"Could not clear consumed buffered uploads: {e}")
        return 0


def _get_next_execution_log_id() -> int:
    """Return the next ID for cron-style execution logs stored under cron_logs."""
    try:
        logs_data = storage.load("cron_logs")
        logs = (logs_data or {}).get("logs", [])
        if not logs:
            return 1
        return max(int(log.get("id", 0)) for log in logs) + 1
    except Exception:
        return 1


def _save_manual_execution_log(log_entry: Dict):
    """Persist a manual execution entry into cron_logs for Restore section visibility."""
    logs_data = storage.load("cron_logs") or {"logs": []}
    logs = logs_data.get("logs", [])

    if not log_entry.get("id"):
        log_entry["id"] = _get_next_execution_log_id()

    logs.insert(0, log_entry)
    logs = logs[:100]
    storage.save("cron_logs", {"logs": logs})


def fetch_from_clo_query(clo_id: str, user_id: int = 1) -> Dict:
    """
    Fetch data for a CLO using the configured data source (Excel or Oracle),
    apply sorting logic (same as automated run), and create an editable session.

    Uses DATA_SOURCE env var via DatabaseService factory — no hardcoded Oracle dependency.
    With DATA_SOURCE=excel  → reads from the configured Excel file (local dev / demo).
    With DATA_SOURCE=oracle → executes the CLO's saved query against Oracle (production).

    Args:
        clo_id: CLO identifier (e.g. 'EURO_ABS_AUTO_LEASE')
        user_id: User ID for session naming

    Returns:
        Dict with session_id, sorted_preview, rows_imported, statistics
        (same format as import_manual_colors so the frontend can reuse the same code path)
    """
    start_time = datetime.now()
    try:
        from services.database_service import DatabaseService

        data_src = os.getenv("DATA_SOURCE", "excel")
        logger.info(
            f"🔍 Fetching data for CLO '{clo_id}' via DatabaseService (DATA_SOURCE={data_src})"
        )

        # DatabaseService respects DATA_SOURCE env var automatically
        db = DatabaseService(clo_id=clo_id)
        source_colors = db.fetch_all_colors()

        logger.info(f"✅ Fetched {len(source_colors)} source rows for CLO '{clo_id}'")

        # Append pending manual uploads so manual review runs on combined input.
        pending_buffer_entries = get_buffered_files()
        pending_buffer_ids = [int(entry.get("id")) for entry in pending_buffer_entries if entry.get("id") is not None]
        buffered_colors, buffer_warnings, consumed_buffer_ids = _load_buffered_manual_colors()
        if buffered_colors:
            logger.info(
                f"📎 Appending {len(buffered_colors)} buffered rows to source data "
                f"({len(source_colors)} + {len(buffered_colors)})"
            )

        raw_colors = source_colors + buffered_colors

        if not raw_colors:
            return {
                "success": False,
                "error": (
                    f"No data returned for CLO '{clo_id}' and no buffered manual uploads found. "
                    f"Data source is '{data_src}'. "
                    "If using Excel, check that the input file exists and has data. "
                    "If using Oracle, ensure the CLO has a saved query in the admin panel."
                ),
            }

        logger.info(
            f"✅ Combined rows for manual session: {len(raw_colors)} "
            f"(source={len(source_colors)}, buffered={len(buffered_colors)})"
        )
        logger.info(
            f"📦 Buffer state before session save: pending_files={len(pending_buffer_entries)} "
            f"pending_ids={pending_buffer_ids} consumed_ids={consumed_buffer_ids}"
        )
        if consumed_buffer_ids:
            logger.info(f"📌 Buffered upload IDs included in this session: {consumed_buffer_ids}")

        # Apply sorting (RankingEngine, no rules) — same as the automated cron run
        sorted_colors = ranking_engine.run_colors(raw_colors)

        # Create session for the frontend to work with
        session_id = generate_session_id(user_id)
        session = ManualColorSession(session_id)

        sorted_data_dict = [
            {
                "row_id": i,
                "message_id": c.message_id,
                "ticker": c.ticker,
                "sector": c.sector,
                "cusip": c.cusip,
                "date": c.date.isoformat() if c.date else None,
                "price_level": c.price_level,
                "bid": c.bid,
                "ask": c.ask,
                "px": c.px,
                "source": c.source,
                "bias": c.bias,
                "rank": c.rank,
                "cov_price": c.cov_price,
                "percent_diff": c.percent_diff,
                "price_diff": c.price_diff,
                "confidence": c.confidence,
                "date_1": c.date_1.isoformat() if c.date_1 else None,
                "diff_status": c.diff_status,
                "is_parent": c.is_parent,
                "parent_message_id": c.parent_message_id,
                "children_count": c.children_count,
            }
            for i, c in enumerate(sorted_colors)
        ]

        session.update(
            original_filename=f"datasource_{clo_id}",
            sorted_data=sorted_data_dict,
            filtered_data=sorted_data_dict.copy(),
            consumed_buffer_upload_ids=consumed_buffer_ids,
            rows_imported=len(raw_colors),
            rows_valid=len(raw_colors),
            parsing_errors=buffer_warnings,
            status="preview",
        )

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Data fetch completed in {duration:.2f}s — session {session_id}")

        return {
            "success": True,
            "session_id": session_id,
            "filename": f"datasource_{clo_id}",
            "data_source": str(data_src).lower(),
            "rows_imported": len(raw_colors),
            "rows_valid": len(raw_colors),
            "parsing_errors": buffer_warnings,
            "sorted_preview": sorted_data_dict,
            "statistics": {
                "total_rows": len(sorted_colors),
                "parent_rows": sum(1 for c in sorted_colors if c.is_parent),
                "child_rows": sum(1 for c in sorted_colors if not c.is_parent),
                "unique_cusips": len(set(c.cusip for c in sorted_colors)),
                "source_rows": len(source_colors),
                "buffered_rows_appended": len(buffered_colors),
                "buffer_pending_files": len(pending_buffer_entries),
                "buffer_pending_ids": pending_buffer_ids,
                "buffered_upload_ids": consumed_buffer_ids,
            },
            "duration_seconds": duration,
        }

    except Exception as e:
        logger.error(f"❌ fetch_from_clo_query failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "data_source": str(os.getenv("DATA_SOURCE", "excel")).lower(),
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
        }

def get_session_preview(session_id: str) -> Dict:
    """
    Get current preview data for session
    
    Args:
        session_id: Session identifier
    
    Returns:
        Dict with current filtered data
    """
    try:
        session = ManualColorSession(session_id)
        
        if not session.data.get("filtered_data"):
            return {
                "success": False,
                "error": "Session not found or no data available"
            }
        
        return {
            "success": True,
            "session_id": session_id,
            "data": session.data["filtered_data"],
            "applied_rules": session.data.get("applied_rules", []),
            "deleted_rows": session.data.get("deleted_rows", []),
            "statistics": {
                "total_rows": len(session.data["filtered_data"]),
                "parent_rows": sum(1 for c in session.data["filtered_data"] if c.get("is_parent")),
                "child_rows": sum(1 for c in session.data["filtered_data"] if not c.get("is_parent"))
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to get session preview: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def delete_rows(session_id: str, row_ids: List[int]) -> Dict:
    """
    Delete selected rows from preview
    
    Args:
        session_id: Session identifier
        row_ids: List of row IDs to delete
    
    Returns:
        Dict with updated data
    """
    try:
        session = ManualColorSession(session_id)
        
        # Filter out deleted rows
        current_data = session.data["filtered_data"]
        deleted_rows = session.data.get("deleted_rows", [])
        
        # Add to deleted list
        deleted_rows.extend(row_ids)
        
        # Remove from filtered data
        updated_data = [row for row in current_data if row["row_id"] not in row_ids]
        
        session.update(
            filtered_data=updated_data,
            deleted_rows=deleted_rows
        )
        
        logger.info(f"✅ Deleted {len(row_ids)} rows from session {session_id}")
        
        return {
            "success": True,
            "deleted_count": len(row_ids),
            "remaining_count": len(updated_data),
            "updated_preview": updated_data,
            "statistics": {
                "total_deleted": len(deleted_rows),
                "remaining_rows": len(updated_data)
            }
        }
    except Exception as e:
        logger.error(f"❌ Failed to delete rows: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def apply_selected_rules(session_id: str, rule_ids: List[int]) -> Dict:
    """
    Apply selected rules to manual color data
    
    Args:
        session_id: Session identifier
        rule_ids: List of rule IDs to apply
    
    Returns:
        Dict with filtered data after applying rules
    """
    try:
        session = ManualColorSession(session_id)
        
        current_data = session.data["filtered_data"]
        
        if not current_data:
            return {
                "success": False,
                "error": "No data available in session"
            }
        
        logger.info(f"🔍 Applying {len(rule_ids)} rules to {len(current_data)} rows")
        
        # Apply rules using existing rules service
        rules_result = apply_rules(current_data, specific_rule_ids=rule_ids)
        
        filtered_data = rules_result["filtered_data"]
        excluded_count = rules_result["excluded_count"]
        rules_applied_info = rules_result["rules_applied"]
        
        # Update session
        applied_rules = session.data.get("applied_rules", [])
        applied_rules.extend(rule_ids)
        
        session.update(
            filtered_data=filtered_data,
            applied_rules=list(set(applied_rules))  # Remove duplicates
        )
        
        logger.info(f"✅ Rules applied: excluded {excluded_count} rows")
        
        return {
            "success": True,
            "rules_applied": len(rule_ids),
            "excluded_count": excluded_count,
            "remaining_rows": len(filtered_data),
            "updated_preview": filtered_data,
            "statistics": {
                "total_rows": len(current_data),
                "excluded_rows": excluded_count,
                "remaining_rows": len(filtered_data)
            },
            "rules_info": rules_applied_info
        }
    except Exception as e:
        logger.error(f"❌ Failed to apply rules: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


def save_manual_colors(session_id: str, user_id: int = 1) -> Dict:
    """
    Step 3: Save processed manual colors to output file (S3 in future)
    
    Args:
        session_id: Session identifier
        user_id: User ID
    
    Returns:
        Dict with save status and output file path
    """
    start_time = datetime.now()
    
    try:
        session = ManualColorSession(session_id)
        
        # Get the current filtered/edited data from the session
        final_data = session.data.get("filtered_data")
        if not final_data:
            # If no filtered data exists, use the sorted preview
            final_data = session.data.get("sorted_preview", [])
        
        if not final_data:
            return {
                "success": False,
                "error": "No data to save"
            }
        
        logger.info(f"💾 Saving {len(final_data)} manual colors to output file")
        
        # Convert dict data back to ColorProcessed objects
        processed_colors = []
        for row in final_data:
            try:
                color = ColorProcessed(
                    message_id=row.get("message_id"),
                    ticker=row.get("ticker", ""),
                    sector=row.get("sector", ""),
                    cusip=row.get("cusip", ""),
                    date=pd.to_datetime(row.get("date")) if row.get("date") else None,
                    price_level=row.get("price_level", 0.0),
                    bid=row.get("bid", 0.0),
                    ask=row.get("ask", 0.0),
                    px=row.get("px", 0.0),
                    source=row.get("source", "MANUAL"),
                    bias=row.get("bias", ""),
                    rank=row.get("rank", 1),
                    cov_price=row.get("cov_price", 0.0),
                    percent_diff=row.get("percent_diff", 0.0),
                    price_diff=row.get("price_diff", 0.0),
                    confidence=row.get("confidence", 5),
                    date_1=pd.to_datetime(row.get("date_1")) if row.get("date_1") else None,
                    diff_status=row.get("diff_status", ""),
                    is_parent=row.get("is_parent", False),
                    parent_message_id=row.get("parent_message_id"),
                    children_count=row.get("children_count", 0)
                )
                processed_colors.append(color)
            except Exception as e:
                logger.warning(f"⚠️ Failed to parse row {row.get('row_id', '?')}: {e}")
                continue
        
        if not processed_colors:
            return {
                "success": False,
                "error": "No valid data to save after parsing"
            }
        
        logger.info(f"📦 Converted {len(processed_colors)} rows to ColorProcessed objects")
        
        # Reserve a run ID and use it for both output rows and restore history.
        # This makes manual saves removable via the same run-based restore flow.
        manual_run_id = _get_next_execution_log_id()

        # Save to output file using output service
        rows_saved = output_service.append_processed_colors(
            colors=processed_colors,
            processing_type="MANUAL",
            run_id=manual_run_id
        )

        # Clear consumed buffered uploads after successful save.
        # This prevents those buffer files from being re-processed in cron later.
        buffer_cleared_count = 0
        dest_mode = str(getattr(output_service, "_dest_type", os.getenv("OUTPUT_DESTINATION", "local"))).lower()
        consumed_ids = session.data.get("consumed_buffer_upload_ids", []) or []
        pending_buffer_entries = get_buffered_files()
        pending_buffer_ids = [int(entry.get("id")) for entry in pending_buffer_entries if entry.get("id") is not None]

        # Fallback: query-based sessions include all pending uploads in principle.
        # If consumed IDs are unexpectedly empty but pending uploads exist, clear those pending IDs.
        if not consumed_ids and pending_buffer_ids and str(session.data.get("original_filename", "")).startswith("datasource_"):
            consumed_ids = pending_buffer_ids.copy()
            logger.warning(
                "⚠️ consumed_buffer_upload_ids missing for datasource session; "
                f"falling back to pending IDs for clear: {consumed_ids}"
            )

        if consumed_ids:
            buffer_cleared_count = _clear_consumed_buffer_entries(consumed_ids)
        logger.info(
            f"🧹 Buffer clear after manual save | mode={dest_mode} "
            f"| consumed_ids={consumed_ids} | pending_ids={pending_buffer_ids} "
            f"| cleared={buffer_cleared_count}"
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Add a cron-style execution entry so Email & Restore table can list it.
        _save_manual_execution_log({
            "id": manual_run_id,
            "job_id": 0,
            "job_name": "Manual Cleaning",
            "triggered_by": "manual",
            "start_time": start_time.isoformat(),
            "status": "success",
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "original_count": int(session.data.get("rows_imported", len(final_data)) or len(final_data)),
            "excluded_count": max(
                int(session.data.get("rows_imported", len(final_data)) or len(final_data)) - int(rows_saved),
                0,
            ),
            "processed_count": int(rows_saved),
            "rules_applied": len(session.data.get("applied_rules", [])),
            "manual_files_processed": int(buffer_cleared_count),
            "manual_files_failed": 0,
        })

        # Also add a unified restore log entry with an explicit indicator.
        logging_service.add_log(
            module='restore',
            action='manual_cleaning',
            description=(
                f"Manual cleaning saved as run #{manual_run_id} "
                f"({rows_saved} row(s) saved)"
            ),
            performed_by=f"user_{user_id}",
            entity_id=manual_run_id,
            can_revert=False,
            metadata={
                "run_id": manual_run_id,
                "processing_type": "MANUAL",
                "session_id": session_id,
                "buffer_cleared_count": buffer_cleared_count,
            }
        )
        
        # Update session status
        session.update(
            status="saved",
            output_file=output_service.output_file_path,
            saved_at=datetime.now().isoformat(),
            rows_saved=rows_saved,
            run_id=manual_run_id,
            buffer_cleared_count=buffer_cleared_count
        )

        
        logger.info(f"✅ Manual colors saved successfully in {duration:.2f}s")
        
        return {
            "success": True,
            "session_id": session_id,
            "rows_saved": rows_saved,
            "run_id": manual_run_id,
            "output_file": output_service.output_file_path,
            "duration_seconds": duration,
            "metadata": {
                "applied_rules_count": len(session.data.get("applied_rules", [])),
                "deleted_rows_count": len(session.data.get("deleted_rows", [])),
                "consumed_buffer_upload_ids": consumed_ids,
                "pending_buffer_upload_ids": pending_buffer_ids,
                "buffer_cleared_count": buffer_cleared_count,
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to save manual colors: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "duration_seconds": (datetime.now() - start_time).total_seconds()
        }


def get_active_sessions(user_id: Optional[int] = None) -> List[Dict]:
    """
    Get list of active manual color sessions
    
    Args:
        user_id: Optional user ID filter
    
    Returns:
        List of session summaries
    """
    try:
        sessions = []
        
        for session_file in Path(MANUAL_SESSION_DIR).glob("*.json"):
            with open(session_file, 'r') as f:
                session_data = json.load(f)
                
                # Filter by user if specified
                if user_id and not session_data["session_id"].endswith(f"_{user_id}_"):
                    continue
                
                sessions.append({
                    "session_id": session_data["session_id"],
                    "created_at": session_data.get("created_at"),
                    "updated_at": session_data.get("updated_at"),
                    "filename": session_data.get("original_filename"),
                    "status": session_data.get("status"),
                    "rows_count": len(session_data.get("filtered_data", []))
                })
        
        return sessions
    except Exception as e:
        logger.error(f"❌ Failed to get active sessions: {e}")
        return []


def cleanup_old_sessions(days: int = 1) -> int:
    """
    Clean up old session files
    
    Args:
        days: Delete sessions older than this many days
    
    Returns:
        Number of sessions deleted
    """
    try:
        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (days * 86400)
        
        for session_file in Path(MANUAL_SESSION_DIR).glob("*.json"):
            if session_file.stat().st_mtime < cutoff_time:
                session_file.unlink()
                deleted_count += 1
        
        logger.info(f"🧹 Cleaned up {deleted_count} old sessions")
        return deleted_count
    except Exception as e:
        logger.error(f"❌ Failed to cleanup sessions: {e}")
        return 0
