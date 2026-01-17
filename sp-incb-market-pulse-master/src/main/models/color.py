#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Color Data Models
Based on admin view sample data from client
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class ColorRaw(BaseModel):
    """
    Raw color data from Oracle database
    Matches the structure from Color today.xlsx (18 columns)
    """
    message_id: int = Field(..., description="Unique message identifier")
    ticker: str = Field(..., description="Security ticker symbol")
    sector: str = Field(..., description="Asset class/sector")
    cusip: str = Field(..., description="CUSIP identifier")
    date: datetime = Field(..., description="Trade/color date")
    price_level: float = Field(..., description="Price level")
    bid: float = Field(..., description="Bid price (0.0 if not applicable)")
    ask: float = Field(..., description="Ask/Offer price (0.0 if not applicable)")
    px: float = Field(..., description="Price (same as price_level)")
    source: str = Field(..., description="Data source/bank")
    bias: str = Field(..., description="Color type (BID, OFFER, BWIC COVER, etc)")
    rank: int = Field(..., ge=1, le=6, description="Pre-calculated rank (1=highest priority)")
    cov_price: float = Field(..., description="Coverage price reference")
    percent_diff: float = Field(..., description="Percentage difference")
    price_diff: float = Field(..., description="Price difference")
    confidence: int = Field(..., ge=0, le=10, description="Confidence score")
    date_1: datetime = Field(..., description="Secondary/fallback date")
    diff_status: str = Field(..., description="Difference status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": 17679633591029712,
                "ticker": "WDMNT 2022-9A ER",
                "sector": "MM-CLO",
                "cusip": "97988RBL5",
                "date": "2026-01-11T00:00:00",
                "price_level": 101.700,
                "bid": 101.700,
                "ask": 102.575,
                "px": 101.700,
                "source": "SMBC",
                "bias": "BID",
                "rank": 3,
                "cov_price": 102.200,
                "percent_diff": 0.49,
                "price_diff": -0.500,
                "confidence": 9,
                "date_1": "2026-01-09T00:00:00",
                "diff_status": "Small Difference"
            }
        }


class ColorProcessed(ColorRaw):
    """
    Processed color with parent-child hierarchy
    Extends ColorRaw with computed fields
    """
    is_parent: bool = Field(default=False, description="True if this is the parent color")
    parent_message_id: Optional[int] = Field(default=None, description="Message ID of parent (for children)")
    children_count: int = Field(default=0, description="Number of children (for parents)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": 17679633591029712,
                "ticker": "WDMNT 2022-9A ER",
                "sector": "MM-CLO",
                "cusip": "97988RBL5",
                "date": "2026-01-11T00:00:00",
                "price_level": 101.700,
                "bid": 101.700,
                "ask": 102.575,
                "px": 101.700,
                "source": "SMBC",
                "bias": "BID",
                "rank": 3,
                "cov_price": 102.200,
                "percent_diff": 0.49,
                "price_diff": -0.500,
                "confidence": 9,
                "date_1": "2026-01-09T00:00:00",
                "diff_status": "Small Difference",
                "is_parent": True,
                "parent_message_id": None,
                "children_count": 2
            }
        }


class ColorResponse(BaseModel):
    """
    API response for color queries
    """
    total_count: int
    page: int
    page_size: int
    colors: list[ColorProcessed]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 1106,
                "page": 1,
                "page_size": 100,
                "colors": []
            }
        }


class MonthlyStats(BaseModel):
    """
    Monthly statistics for dashboard chart
    """
    month: str = Field(..., description="Month in YYYY-MM format")
    count: int = Field(..., description="Number of colors received")
    
    class Config:
        json_schema_extra = {
            "example": {
                "month": "2026-01",
                "count": 5213
            }
        }


class MonthlyStatsResponse(BaseModel):
    """
    Response for dashboard monthly statistics
    """
    stats: list[MonthlyStats]
    
    class Config:
        json_schema_extra = {
            "example": {
                "stats": [
                    {"month": "2025-02", "count": 1200},
                    {"month": "2025-03", "count": 2100},
                    {"month": "2025-04", "count": 1800}
                ]
            }
        }
