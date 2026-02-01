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
        required_cols = column_config.get_required_columns()
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")
        
        # Convert DataFrame to ColorRaw objects
        raw_colors = []
        parsing_errors = []
        
        for idx, row in df.iterrows():
            try:
                color_raw = ColorRaw(
                    message_id=row.get('MESSAGE_ID', f"MANUAL_{idx}"),
                    cusip=row['CUSIP'],
                    ticker=row.get('TICKER', ''),
                    date=pd.to_datetime(row['DATE']),
                    rank=int(row.get('RANK', 0)),
                    px=float(row.get('PX', 0)) if pd.notna(row.get('PX')) else None,
                    bid=float(row.get('BID', 0)) if pd.notna(row.get('BID')) else None,
                    mid=float(row.get('MID', 0)) if pd.notna(row.get('MID')) else None,
                    ask=float(row.get('ASK', 0)) if pd.notna(row.get('ASK')) else None,
                    source=row.get('SOURCE', 'MANUAL'),
                    bias=row.get('BIAS', '')
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
                "cusip": c.cusip,
                "ticker": c.ticker,
                "date": c.date.isoformat(),
                "rank": c.rank,
                "px": c.px,
                "bid": c.bid,
                "mid": c.mid,
                "ask": c.ask,
                "source": c.source,
                "bias": c.bias
            }
            for idx, c in enumerate(raw_colors)
        ]
        
        sorted_data_dict = [
            {
                "row_id": idx,
                "message_id": c.message_id,
                "cusip": c.cusip,
                "ticker": c.ticker,
                "date": c.date.isoformat(),
                "rank": c.rank,
                "px": c.px,
                "bid": c.bid,
                "mid": c.mid,
                "ask": c.ask,
                "source": c.source,
                "bias": c.bias,
                "is_parent": c.is_parent,
                "parent_id": c.parent_id,
                "child_count": c.child_count,
                "color": c.color
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
            "remaining_rows": len(updated_data),
            "data": updated_data
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
            "data": filtered_data,
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
        
        final_data = session.data.get("filtered_data", [])
        
        if not final_data:
            return {
                "success": False,
                "error": "No data to save"
            }
        
        logger.info(f"💾 Saving {len(final_data)} manual colors to output file")
        
        # Convert back to ColorProcessed objects
        processed_colors = []
        for row in final_data:
            color = ColorProcessed(
                message_id=row["message_id"],
                cusip=row["cusip"],
                ticker=row.get("ticker", ""),
                date=pd.to_datetime(row["date"]),
                rank=row["rank"],
                px=row.get("px"),
                bid=row.get("bid"),
                mid=row.get("mid"),
                ask=row.get("ask"),
                source=row.get("source", "MANUAL"),
                bias=row.get("bias", ""),
                is_parent=row["is_parent"],
                parent_id=row.get("parent_id"),
                child_count=row.get("child_count", 0),
                color=row.get("color", "")
            )
            processed_colors.append(color)
        
        # Save to output file using output service
        output_result = output_service.save_colors(
            processed_colors,
            source="manual_color_processing",
            metadata={
                "session_id": session_id,
                "original_filename": session.data.get("original_filename"),
                "user_id": user_id,
                "applied_rules": session.data.get("applied_rules", []),
                "deleted_rows_count": len(session.data.get("deleted_rows", []))
            }
        )
        
        if not output_result.get("success"):
            raise Exception(output_result.get("error", "Failed to save output"))
        
        # Update session status
        session.update(
            status="saved",
            output_file=output_result.get("output_file"),
            saved_at=datetime.now().isoformat()
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Manual colors saved successfully in {duration:.2f}s")
        
        return {
            "success": True,
            "session_id": session_id,
            "rows_saved": len(final_data),
            "output_file": output_result.get("output_file"),
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
