#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generic Search API - Column-config driven dynamic search
"""
from fastapi import APIRouter, Query, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import logging
import io
import pandas as pd
import numpy as np
from services.output_service import get_output_service
from services.column_config_service import get_column_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["Search"])

output_service = get_output_service()
column_config = get_column_config()


class SearchFilter(BaseModel):
    """Single search filter"""
    field: str
    operator: str = "equals"  # equals, contains, starts_with, gt, lt, gte, lte, between
    value: Any
    value2: Optional[Any] = None  # For 'between' operator
    logical_operator: str = "AND"  # AND or OR (applies from second condition onward)


class SearchRequest(BaseModel):
    """Generic search request"""
    filters: List[SearchFilter] = []
    skip: int = 0
    limit: int = 10
    sort_by: Optional[str] = None
    sort_order: str = "desc"  # asc or desc
    clo_id: Optional[str] = None  # CLO ID for column filtering
    include_related_hierarchy: bool = True


class SearchResponse(BaseModel):
    """Search results with metadata"""
    total_count: int
    returned_count: int
    page: int
    page_size: int
    results: List[Dict[str, Any]]
    available_fields: List[str]


@router.post("/generic", response_model=SearchResponse)
def generic_search(request: SearchRequest):
    """
    **Generic Column-Driven Search API**
    
    **Key Features:**
    - Search by ANY field in column_config.json
    - Works with current Excel and future S3 storage
    - Column names are configurable (no hardcoding)
    - Multiple filter operators supported
    - Sorting and pagination included
    
    **Example Request:**
    ```json
    {
      "filters": [
        {"field": "CUSIP", "operator": "equals", "value": "12345"},
        {"field": "SECTOR", "operator": "equals", "value": "Technology"},
        {"field": "PRICE_LEVEL", "operator": "gte", "value": 100}
      ],
      "skip": 0,
      "limit": 10,
      "sort_by": "DATE",
      "sort_order": "desc"
    }
    ```
    
    **Operators:**
    - `equals`: Exact match
    - `contains`: Substring match (case-insensitive)
    - `starts_with`: Prefix match
    - `gt`, `lt`, `gte`, `lte`: Numeric/date comparisons
    - `between`: Range (requires value and value2)
    
    **Returns:** Filtered and paginated results
    """
    try:
        # Get visible columns from CLO if provided
        visible_columns = None
        if request.clo_id:
            from services.clo_mapping_service import CLOMappingService
            clo_service = CLOMappingService()
            user_columns = clo_service.get_user_columns(request.clo_id)
            if user_columns:
                visible_columns = user_columns.get('visible_columns', [])
                logger.info(f"CLO '{request.clo_id}' visible columns: {visible_columns}")
        
        # Get available columns from config (or CLO-filtered)
        if visible_columns:
            available_columns = visible_columns
        else:
            available_columns = [col['oracle_name'] for col in column_config.config['columns']]
        
        # Validate filter fields
        for filter_item in request.filters:
            if filter_item.field not in available_columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid field '{filter_item.field}'. Available fields: {', '.join(available_columns)}"
                )
        
        logger.info(
            f"Generic search: {len(request.filters)} filters, "
            f"limit={request.limit}, clo_id={request.clo_id}"
        )
        
        # Read ALL records so filtering + skip/limit pagination works correctly.
        # output_service handles local vs S3 efficiently internally.
        all_records = output_service.read_processed_colors(limit=None)
        
        if not all_records:
            return SearchResponse(
                total_count=0,
                returned_count=0,
                page=1,
                page_size=request.limit,
                results=[],
                available_fields=available_columns
            )
        
        # Apply filters with AND/OR support
        if request.filters:
            combined_ids = None
            all_ids = {id(r) for r in all_records}

            for idx, filter_item in enumerate(request.filters):
                matched_records = _apply_filter(all_records, filter_item)
                matched_ids = {id(r) for r in matched_records}

                if idx == 0 or combined_ids is None:
                    combined_ids = matched_ids
                else:
                    op = str(filter_item.logical_operator or "AND").upper()
                    if op == "OR":
                        combined_ids = combined_ids.union(matched_ids)
                    else:
                        combined_ids = combined_ids.intersection(matched_ids)

                logger.info(
                    f"After filter {filter_item.field} {filter_item.operator} "
                    f"{filter_item.value} [{filter_item.logical_operator}]: "
                    f"{len(combined_ids or all_ids)} records"
                )

            filtered_records = [r for r in all_records if id(r) in (combined_ids or all_ids)]
        else:
            filtered_records = all_records

        # If searching by CUSIP / MESSAGE_ID, include related hierarchy rows so
        # table can display parent-child context (across historical runs too).
        filter_fields_upper = {str(f.field or '').upper() for f in request.filters}
        should_expand_hierarchy = request.include_related_hierarchy and (
            "CUSIP" in filter_fields_upper or "MESSAGE_ID" in filter_fields_upper
        )
        if should_expand_hierarchy and len(filtered_records) > 0:
            base_df = pd.DataFrame(filtered_records)
            all_df = pd.DataFrame(all_records)
            if "MESSAGE_ID" in all_df.columns and "PARENT_MESSAGE_ID" in all_df.columns:
                base_message_ids = {
                    str(v) for v in base_df.get("MESSAGE_ID", pd.Series(dtype=object)).dropna().tolist()
                }
                base_parent_ids = {
                    str(v) for v in base_df.get("PARENT_MESSAGE_ID", pd.Series(dtype=object)).dropna().tolist()
                }

                parents = all_df[all_df["MESSAGE_ID"].astype(str).isin(base_parent_ids)]
                children = all_df[all_df["PARENT_MESSAGE_ID"].astype(str).isin(base_message_ids)]
                expanded_df = pd.concat([base_df, parents, children], ignore_index=True).drop_duplicates()
                filtered_records = expanded_df.to_dict('records')
        
        # Sort results
        if request.sort_by and request.sort_by in available_columns:
            df = pd.DataFrame(filtered_records)
            ascending = request.sort_order.lower() == "asc"
            df = df.sort_values(by=request.sort_by, ascending=ascending)
            filtered_records = df.to_dict('records')
        else:
            # Default deterministic order: newest processed rows first
            df = pd.DataFrame(filtered_records)
            sort_cols = []
            ascending = []
            if "PROCESSED_AT" in df.columns:
                sort_cols.append("PROCESSED_AT")
                ascending.append(False)
            if "RUN_ID" in df.columns:
                sort_cols.append("RUN_ID")
                ascending.append(False)
            if "DATE" in df.columns:
                sort_cols.append("DATE")
                ascending.append(False)
            if sort_cols:
                df = df.sort_values(by=sort_cols, ascending=ascending, kind='mergesort')
                filtered_records = df.to_dict('records')
        
        # Pagination (limit <= 0 means no limit)
        total_count = len(filtered_records)
        if request.limit and request.limit > 0:
            paginated_records = filtered_records[request.skip:request.skip + request.limit]
            page_size = request.limit
            page = (request.skip // request.limit) + 1
        else:
            paginated_records = filtered_records[request.skip:]
            page_size = total_count
            page = 1
        
        # Filter columns in results if CLO filtering is active
        if visible_columns:
            system_columns = {
                "IS_PARENT", "PARENT_MESSAGE_ID", "CHILDREN_COUNT",
                "MESSAGE_ID", "CUSIP", "DATE", "DATE_1", "RUN_ID", "PROCESSED_AT"
            }
            filtered_paginated = []
            for record in paginated_records:
                filtered_record = {k: v for k, v in record.items() if k in visible_columns or k in system_columns}
                filtered_paginated.append(filtered_record)
            paginated_records = filtered_paginated
            logger.info(f"Filtered results to {len(visible_columns)} visible columns")
        
        logger.info(f"Search complete: {total_count} total, returning {len(paginated_records)}")
        
        return SearchResponse(
            total_count=total_count,
            returned_count=len(paginated_records),
            page=page,
            page_size=page_size,
            results=paginated_records,
            available_fields=available_columns
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generic search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fields", response_model=Dict[str, Any])
async def get_searchable_fields(clo_id: Optional[str] = Query(None, description="CLO ID for column filtering")):
    """
    **Get All Searchable Fields**
    
    Returns all columns defined in column_config.json that can be used for searching.
    If clo_id is provided, returns only columns visible for that CLO.
    This endpoint helps frontends build dynamic search UIs.
    
    **Returns:**
    ```json
    {
      "version": "1.0",
      "total_fields": 15,
      "fields": [
        {
          "name": "MESSAGE_ID",
          "display_name": "Message ID",
          "data_type": "INTEGER",
          "searchable": true
        },
        ...
      ]
    }
    ```
    """
    try:
        # Get visible columns from CLO if provided
        visible_columns = None
        if clo_id:
            from services.clo_mapping_service import CLOMappingService
            clo_service = CLOMappingService()
            user_columns = clo_service.get_user_columns(clo_id)
            if user_columns:
                visible_columns = user_columns.get('visible_columns', [])
                logger.info(f"Returning fields for CLO '{clo_id}': {len(visible_columns)} columns")
        
        fields_info = []
        for col in column_config.config['columns']:
            # Skip columns not visible for this CLO
            if visible_columns and col['oracle_name'] not in visible_columns:
                continue
                
            fields_info.append({
                "name": col['oracle_name'],
                "display_name": col.get('display_name', col['oracle_name']),
                "data_type": col.get('data_type', 'VARCHAR'),
                "required": col.get('required', False),
                "description": col.get('description', ''),
                "searchable": True
            })
        
        return {
            "version": column_config.config.get('version', '1.0'),
            "total_fields": len(fields_info),
            "fields": fields_info,
            "clo_filtered": clo_id is not None,
            "supported_operators": {
                "STRING": ["equals", "contains", "starts_with"],
                "INTEGER": ["equals", "gt", "lt", "gte", "lte", "between"],
                "FLOAT": ["equals", "gt", "lt", "gte", "lte", "between"],
                "DATE": ["equals", "gt", "lt", "gte", "lte", "between"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting searchable fields: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _apply_filter(records: List[Dict], filter_item: SearchFilter) -> List[Dict]:
    """Apply a single filter to records"""
    filtered = []
    op = str(filter_item.operator or "").strip().lower().replace(" ", "_")
    
    for record in records:
        field_value = record.get(filter_item.field)
        
        # Skip null values
        if field_value is None:
            continue
        
        try:
            # Apply operator
            if op == "equals":
                if str(field_value).upper() == str(filter_item.value).upper():
                    filtered.append(record)

            elif op in ("not_equals", "not_equal_to"):
                if str(field_value).upper() != str(filter_item.value).upper():
                    filtered.append(record)
            
            elif op == "contains":
                if str(filter_item.value).upper() in str(field_value).upper():
                    filtered.append(record)
            
            elif op == "starts_with":
                if str(field_value).upper().startswith(str(filter_item.value).upper()):
                    filtered.append(record)

            elif op in ("ends_with", "endswith"):
                if str(field_value).upper().endswith(str(filter_item.value).upper()):
                    filtered.append(record)
            
            elif op == "gt":
                if float(field_value) > float(filter_item.value):
                    filtered.append(record)
            
            elif op == "lt":
                if float(field_value) < float(filter_item.value):
                    filtered.append(record)
            
            elif op == "gte":
                if float(field_value) >= float(filter_item.value):
                    filtered.append(record)
            
            elif op == "lte":
                if float(field_value) <= float(filter_item.value):
                    filtered.append(record)
            
            elif op == "between":
                if filter_item.value2 is None:
                    continue
                val = float(field_value)
                if float(filter_item.value) <= val <= float(filter_item.value2):
                    filtered.append(record)
        
        except (ValueError, TypeError):
            # Skip records where type conversion fails
            continue
    
    return filtered


# Convenience GET endpoint for simple searches
@router.get("/simple", response_model=SearchResponse)
def simple_search(
    field: str = Query(..., description="Field name from column_config.json"),
    value: str = Query(..., description="Value to search for"),
    operator: str = Query("equals", description="Search operator (equals, contains, etc.)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    **Simple GET-based Search**
    
    Quick search by a single field. For complex multi-field searches, use POST /generic endpoint.
    
    **Example:**
    ```
    GET /api/search/simple?field=CUSIP&value=12345&operator=equals&limit=10
    GET /api/search/simple?field=TICKER&value=AAPL&operator=equals
    GET /api/search/simple?field=SECTOR&value=Tech&operator=contains
    ```
    
    **Note:** Field names come from column_config.json (configurable, not hardcoded)
    """
    search_request = SearchRequest(
        filters=[SearchFilter(field=field, operator=operator, value=value)],
        skip=skip,
        limit=limit
    )
    return generic_search(search_request)


# ===========================================================
# SECURITY SEARCH - Search processed output by ID / CUSIP
# ===========================================================

class SecuritySearchRequest(BaseModel):
    """Request for security search by identifier"""
    query: str
    search_type: str = "any"   # "message_id", "cusip", or "any"
    limit: Optional[int] = None
    include_related_hierarchy: bool = True


class SecuritySearchResponse(BaseModel):
    """Security search response"""
    total_count: int
    results: List[Dict[str, Any]]
    search_query: str
    search_type: str


@router.post("/security", response_model=SecuritySearchResponse)
def security_search(request: SecuritySearchRequest):
    """
    **Security Search**

    Search the processed output (local Excel or S3) by Message ID or CUSIP.
    Fetches full rows for matching records.

    - `search_type` = "message_id" → exact match on MESSAGE_ID
    - `search_type` = "cusip"      → case-insensitive match on CUSIP
    - `search_type` = "any"        → tries both MESSAGE_ID and CUSIP
    """
    try:
        query = request.query.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        logger.info(f"Security search: query='{query}', type={request.search_type}")

        # Read ALL processed records
        all_records = output_service.read_processed_colors(limit=None)

        if not all_records:
            return SecuritySearchResponse(
                total_count=0,
                results=[],
                search_query=query,
                search_type=request.search_type
            )

        df = pd.DataFrame(all_records)
        matched = pd.DataFrame()

        search_by = request.search_type.lower()

        if search_by in ("message_id", "any"):
            if "MESSAGE_ID" in df.columns:
                try:
                    mid = int(query)
                    rows = df[df["MESSAGE_ID"] == mid]
                    matched = pd.concat([matched, rows])
                except ValueError:
                    # query is not numeric – only try as CUSIP
                    pass

        if search_by in ("cusip", "any"):
            if "CUSIP" in df.columns:
                rows = df[df["CUSIP"].astype(str).str.upper() == query.upper()]
                matched = pd.concat([matched, rows])

        # Also check for partial message_id string match when search_type=any
        if search_by == "any" and "MESSAGE_ID" in df.columns:
            rows = df[df["MESSAGE_ID"].astype(str).str.contains(query, na=False, case=False)]
            matched = pd.concat([matched, rows])

        matched = matched.drop_duplicates()

        # Include related hierarchy rows so users see complete parent/child context
        # for the matched CUSIP / message IDs across historical runs.
        if request.include_related_hierarchy and len(matched) > 0:
            if "MESSAGE_ID" in df.columns and "PARENT_MESSAGE_ID" in df.columns:
                base_message_ids = {
                    str(v) for v in matched["MESSAGE_ID"].dropna().tolist()
                }
                base_parent_ids = {
                    str(v) for v in matched["PARENT_MESSAGE_ID"].dropna().tolist()
                }

                # Restrict hierarchy expansion to the same CUSIPs only — different
                # securities can share a MESSAGE_ID so we must not cross-contaminate.
                matched_cusips = set(matched["CUSIP"].dropna().astype(str).tolist()) if "CUSIP" in matched.columns else None

                # 1) Parent rows for matched children (same CUSIP only)
                parents_mask = df["MESSAGE_ID"].astype(str).isin(base_parent_ids)
                if matched_cusips is not None and "CUSIP" in df.columns:
                    parents_mask &= df["CUSIP"].astype(str).isin(matched_cusips)
                parents = df[parents_mask]

                # 2) Child rows for matched parents (same CUSIP only)
                children_mask = df["PARENT_MESSAGE_ID"].astype(str).isin(base_message_ids)
                if matched_cusips is not None and "CUSIP" in df.columns:
                    children_mask &= df["CUSIP"].astype(str).isin(matched_cusips)
                children = df[children_mask]

                matched = pd.concat([matched, parents, children]).drop_duplicates()

        # Stable ordering: newest processed run first, then latest business DATE.
        sort_cols = []
        ascending = []
        if "PROCESSED_AT" in matched.columns:
            sort_cols.append("PROCESSED_AT")
            ascending.append(False)
        if "RUN_ID" in matched.columns:
            sort_cols.append("RUN_ID")
            ascending.append(False)
        if "DATE" in matched.columns:
            sort_cols.append("DATE")
            ascending.append(False)

        if sort_cols:
            matched = matched.sort_values(by=sort_cols, ascending=ascending, kind="mergesort")

        if request.limit and request.limit > 0:
            matched = matched.head(request.limit)

        results = _to_json_safe_records(matched)
        logger.info(f"Security search returned {len(results)} records for query='{query}'")

        return SecuritySearchResponse(
            total_count=len(results),
            results=results,
            search_query=query,
            search_type=request.search_type
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Security search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------
# IDENTIFIER AUTO-DETECTION HELPERS
# ---------------------------------------------------------------

# Maps normalized uploaded-file column names → processed-output column to match against
_IDENTIFIER_MAP: dict = {
    # Message ID variants
    "MESSAGE_ID": "MESSAGE_ID",
    "MESSAGEID": "MESSAGE_ID",
    "MSG_ID": "MESSAGE_ID",
    "MSGID": "MESSAGE_ID",
    "MESSAGE_ID_": "MESSAGE_ID",
    "BOND_ID": "MESSAGE_ID",
    "SECURITY_ID": "MESSAGE_ID",
    # CUSIP
    "CUSIP": "CUSIP",
    # ISIN
    "ISIN": "ISIN",
    # Ticker
    "TICKER": "TICKER",
    "SYMBOL": "TICKER",
    "TICK": "TICKER",
}


def _clean_id(val: str) -> str:
    """
    Normalise a raw cell string to a plain identifier string:
    - Scientific notation  → integer string  ('1.76787808852868e+16' → '17678780885286800')
    - Whole-number floats  → integer string  ('17678780885286800.0'  → '17678780885286800')
    - Everything else      → returned unchanged
    Precision is limited to float64 (~15-16 sig. digits), which matches how
    Excel stores large integers internally.
    """
    val = val.strip()
    if not val:
        return val
    lower = val.lower()
    if 'e+' in lower or 'e-' in lower or '.' in val:
        try:
            f = float(val)
            if f == int(f):
                return str(int(f))
        except (ValueError, OverflowError):
            pass
    return val


def _to_json_safe_records(df: pd.DataFrame, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Convert dataframe rows into JSON-safe records by replacing NaN/Inf with None.
    """
    view = df.head(limit) if limit else df
    safe = view.copy()
    safe = safe.replace([np.inf, -np.inf], np.nan)
    safe = safe.astype(object).where(pd.notnull(safe), None)
    return safe.to_dict("records")


def _detect_identifier_columns(ids_df: pd.DataFrame) -> dict:
    """
    Auto-detect identifier type from ALL cell values — including the column-name
    row, which contains data when the uploaded file has no header row.
    Classification is by character length after float normalisation:
      CUSIP      = exactly 9 characters
      Message ID = more than 9 characters
    Column naming in the uploaded file is irrelevant.
    Returns dict: {output_column -> set_of_cleaned_strings}
    """
    cusip_values: set[str] = set()
    message_id_values: set[str] = set()
    SKIP = {"NAN", "NONE", "NULL", "N/A", "NA", ""}

    def classify(raw) -> None:
        val = _clean_id(str(raw).strip())
        if not val or val.upper() in SKIP:
            return
        if len(val) == 9:
            cusip_values.add(val.upper())   # CUSIPs are case-insensitive
        elif len(val) > 9:
            message_id_values.add(val)

    for col in ids_df.columns:
        # The column name may itself be data when the file has no header row
        # (pandas treats row 1 as column names by default).
        classify(col)
        for raw in ids_df[col].dropna():
            classify(raw)

    detected: dict[str, set] = {}
    if cusip_values:
        detected["CUSIP"] = cusip_values
    if message_id_values:
        detected["MESSAGE_ID"] = message_id_values
    return detected


async def _run_ids_search(contents_io: io.BytesIO):
    """Read IDs from Excel BytesIO, search processed output. Returns (matched_df, detected_col_names)."""
    ids_df = pd.read_excel(contents_io, dtype=object)
    detected = _detect_identifier_columns(ids_df)

    detected_col_names = list(detected.keys())
    if not detected:
        raise HTTPException(
            status_code=400,
            detail=(
                "No identifiable values found in the uploaded file. "
                "Values with exactly 9 characters are treated as CUSIPs; "
                "values with more than 9 characters are treated as Message IDs."
            )
        )

    all_records = output_service.read_processed_colors(limit=None)
    if not all_records:
        raise HTTPException(status_code=404, detail="No processed data available to search")

    df = pd.DataFrame(all_records)
    matched = pd.DataFrame()

    for output_col, values in detected.items():
        if output_col not in df.columns:
            continue
        if output_col == "CUSIP":
            # Case-insensitive string match
            upper_vals = {v.upper() for v in values}
            rows = df[df[output_col].astype(str).str.upper().isin(upper_vals)]
        else:
            # MESSAGE_ID: use float comparison so that Excel-stored float64 values
            # (which may have lost ~1-2 ULP precision vs. the stored int64) still match.
            try:
                float_vals = set()
                for v in values:
                    try:
                        float_vals.add(float(v))
                    except (ValueError, OverflowError):
                        pass
                output_as_float = pd.to_numeric(df[output_col], errors='coerce')
                rows = df[
                    output_as_float.isin(float_vals) |
                    df[output_col].astype(str).isin(values)
                ]
            except Exception:
                rows = df[df[output_col].astype(str).isin(values)]
        matched = pd.concat([matched, rows])

    matched = matched.drop_duplicates()
    return matched, detected_col_names


async def _run_ids_search_with_summary(contents_io: io.BytesIO):
    """Same as _run_ids_search but also returns a search summary dict."""
    ids_df = pd.read_excel(contents_io, dtype=object)
    detected = _detect_identifier_columns(ids_df)

    detected_col_names = list(detected.keys())
    if not detected:
        raise HTTPException(
            status_code=400,
            detail=(
                "No identifiable values found in the uploaded file. "
                "Values with exactly 9 characters are treated as CUSIPs; "
                "values with more than 9 characters are treated as Message IDs."
            )
        )

    all_records = output_service.read_processed_colors(limit=None)
    if not all_records:
        raise HTTPException(status_code=404, detail="No processed data available to search")

    df = pd.DataFrame(all_records)
    matched = pd.DataFrame()
    summary = {}

    for output_col, values in detected.items():
        if output_col not in df.columns:
            summary[output_col] = {"searched": len(values), "found": 0, "note": "column not in output"}
            continue
        if output_col in ("CUSIP", "ISIN", "TICKER"):
            upper_vals = {v.upper() for v in values}
            rows = df[df[output_col].astype(str).str.upper().isin(upper_vals)]
        else:
            try:
                float_vals = set()
                for v in values:
                    try:
                        float_vals.add(float(v))
                    except (ValueError, OverflowError):
                        pass
                output_as_float = pd.to_numeric(df[output_col], errors='coerce')
                rows = df[
                    output_as_float.isin(float_vals) |
                    df[output_col].astype(str).isin(values)
                ]
            except Exception:
                rows = df[df[output_col].astype(str).isin(values)]
        summary[output_col] = {"searched": len(values), "found": len(rows)}
        matched = pd.concat([matched, rows])

    matched = matched.drop_duplicates()
    return matched, detected_col_names, summary


@router.post("/import-ids")
async def search_by_imported_ids(file: UploadFile = File(...)):
    """
    **Import IDs → Search → Download Excel**

    Upload an Excel file containing Message IDs and/or CUSIPs.
    The system will:
    1. Auto-detect identifier columns from the uploaded file
    2. Search the processed output (S3 or local) for matching rows
    3. Return a downloadable Excel file with the full matching records

    Identifier columns are auto-detected — column names are matched case-insensitively
    against MESSAGE_ID, CUSIP, ISIN, TICKER and similar known identifiers.
    """
    try:
        if not file.filename.lower().endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=400, detail="Only .xlsx and .xls files are supported")

        contents = await file.read()
        matched, detected_cols = await _run_ids_search(io.BytesIO(contents))

        if matched.empty:
            raise HTTPException(
                status_code=404,
                detail="No matching records found for the provided identifiers"
            )

        output_buffer = io.BytesIO()
        with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
            matched.to_excel(writer, index=False, sheet_name="Search Results")
        output_buffer.seek(0)

        filename = f"security_search_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            output_buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import-IDs search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-ids/preview")
async def preview_imported_ids(file: UploadFile = File(...)):
    """
    **Import IDs → Preview in Table**

    Upload an Excel file containing identifier columns (Message ID, CUSIP, ISIN, Ticker, etc.).
    The system auto-detects identifier columns, searches processed output, and returns JSON rows
    for table preview. Use /import-ids to download the full matched result as Excel.

    Returns:
    - detected_columns: list of identifier column names found in uploaded file
    - total_matches: number of rows matched
    - results: matched rows (up to 1000)
    - search_summary: what was searched
    """
    try:
        if not file.filename.lower().endswith((".xlsx", ".xls")):
            raise HTTPException(status_code=400, detail="Only .xlsx and .xls files are supported")

        contents = await file.read()
        matched, detected_cols, summary = await _run_ids_search_with_summary(io.BytesIO(contents))

        total = len(matched)
        results = _to_json_safe_records(matched, limit=1000)

        logger.info(f"Import-IDs preview: {total} matches, detected: {detected_cols}")
        return {
            "detected_columns": detected_cols,
            "total_matches": total,
            "results": results,
            "search_summary": summary
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import-IDs preview error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
