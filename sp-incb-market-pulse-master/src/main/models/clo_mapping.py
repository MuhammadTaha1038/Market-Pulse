#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLO Mapping Models - User column visibility based on CLO type
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class CLOType(BaseModel):
    """Main CLO type"""
    id: str
    name: str
    display_name: str
    description: Optional[str] = None


class SubCLOType(BaseModel):
    """Sub CLO type under main CLO"""
    id: str
    name: str
    display_name: str
    parent_clo_id: str
    description: Optional[str] = None


class CLOColumnMapping(BaseModel):
    """Column visibility mapping for a CLO type"""
    clo_id: str  # Main CLO or Sub CLO ID
    clo_type: str  # 'main' or 'sub'
    visible_columns: List[str]  # List of column oracle_names that are visible
    hidden_columns: List[str]  # List of column oracle_names that are hidden
    updated_by: Optional[str] = None
    updated_at: Optional[str] = None


class CLOMappingResponse(BaseModel):
    """Response for CLO mapping"""
    clo_id: str
    clo_name: str
    clo_type: str
    parent_clo: Optional[str] = None
    visible_columns: List[Dict[str, Any]]  # Full column details
    hidden_columns: List[Dict[str, Any]]
    total_columns: int


class UpdateCLOMappingRequest(BaseModel):
    """Request to update CLO column mapping"""
    clo_id: str
    clo_type: str
    visible_columns: List[str]  # Column oracle_names to make visible


class CLOHierarchyResponse(BaseModel):
    """Full CLO hierarchy with mappings"""
    main_clos: List[Dict[str, Any]]
    total_main_clos: int
    total_sub_clos: int
