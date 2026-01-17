#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
User and Permission Models
"""
from pydantic import BaseModel, EmailStr, Field
from typing import List


class UserPermissions(BaseModel):
    """
    User permissions and asset class mapping
    Stored in S3: user-permissions/user-mapping.json
    """
    user_email: EmailStr = Field(..., description="User email address")
    allowed_asset_classes: List[str] = Field(..., description="List of allowed sectors/asset classes")
    role: str = Field(..., description="User role: admin or viewer")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_email": "john@company.com",
                "allowed_asset_classes": ["MM-CLO", "2.0_Mezz"],
                "role": "admin"
            }
        }


class User(BaseModel):
    """
    User model for API requests
    """
    email: EmailStr
    name: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@company.com",
                "name": "John Doe"
            }
        }
