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
        
        # Save to output file using output service
        rows_saved = output_service.append_processed_colors(
            colors=processed_colors,
            processing_type="MANUAL"
        )
        
        # Update session status
        session.update(
            status="saved",
            output_file=output_service.output_file_path,
            saved_at=datetime.now().isoformat(),
            rows_saved=rows_saved
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Manual colors saved successfully in {duration:.2f}s")
        
        return {
            "success": True,
            "session_id": session_id,
            "rows_saved": rows_saved,
            "output_file": output_service.output_file_path,
            "duration_seconds": duration,
            "metadata": {
                "applied_rules_count": len(session.data.get("applied_rules", [])),
                "deleted_rows_count": len(session.data.get("deleted_rows", []))
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
