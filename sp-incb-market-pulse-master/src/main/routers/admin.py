#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Admin Router - APIs for system configuration and column management
"""
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import logging
from services.column_config_service import get_column_config
from services.database_service import DatabaseService
from services.data_source_factory import get_data_source, get_data_source_info
from services.output_destination_factory import get_output_destination, get_output_destination_info

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Initialize services
column_config = get_column_config()
db_service = DatabaseService()


# Pydantic models for API
class ColumnCreate(BaseModel):
    oracle_name: str = Field(..., description="Column name in Oracle database")
    display_name: str = Field(..., description="Display name for frontend")
    data_type: str = Field(..., description="Data type (VARCHAR, INTEGER, FLOAT, DATE)")
    required: bool = Field(default=False, description="Is this column required?")
    description: str = Field(default="", description="Column description")


class ColumnUpdate(BaseModel):
    oracle_name: Optional[str] = None
    display_name: Optional[str] = None
    data_type: Optional[str] = None
    required: Optional[bool] = None
    description: Optional[str] = None


class OracleConfigUpdate(BaseModel):
    host: str
    port: int = 1521
    service_name: str
    user: str
    password: str


@router.get("/columns")
async def get_all_columns():
    """
    Get all configured columns
    
    Returns list of columns that will be extracted from Oracle
    Admin can add/remove columns to customize data extraction
    """
    try:
        columns = column_config.get_all_columns()
        table_name = column_config.get_oracle_table_name()
        
        return {
            "success": True,
            "oracle_table": table_name,
            "total_columns": len(columns),
            "columns": columns
        }
    except Exception as e:
        logger.error(f"Error fetching columns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/columns")
async def add_column(column: ColumnCreate):
    """
    Add new column to configuration
    
    This will affect SQL queries when extracting from Oracle
    """
    try:
        logger.info(f"Adding new column: {column.oracle_name}")
        
        new_column = column_config.add_column({
            "oracle_name": column.oracle_name,
            "display_name": column.display_name,
            "data_type": column.data_type,
            "required": column.required,
            "description": column.description
        })
        
        return {
            "success": True,
            "message": f"Column '{column.oracle_name}' added successfully",
            "column": new_column
        }
    except Exception as e:
        logger.error(f"Error adding column: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/columns/{column_id}")
async def delete_column(column_id: int):
    """
    Delete column from configuration
    
    WARNING: This will remove the column from SQL extraction queries
    """
    try:
        logger.info(f"Deleting column ID: {column_id}")
        
        success = column_config.delete_column(column_id)
        
        if success:
            return {
                "success": True,
                "message": f"Column {column_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Column {column_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting column: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/columns/{column_id}")
async def update_column(column_id: int, updates: ColumnUpdate):
    """
    Update existing column configuration
    """
    try:
        logger.info(f"Updating column ID: {column_id}")
        
        # Remove None values
        update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
        
        updated_column = column_config.update_column(column_id, update_dict)
        
        if updated_column:
            return {
                "success": True,
                "message": f"Column {column_id} updated successfully",
                "column": updated_column
            }
        else:
            raise HTTPException(status_code=404, detail=f"Column {column_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating column: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/oracle-table")
async def update_oracle_table(table_name: str = Body(..., embed=True)):
    """
    Update Oracle table name
    
    This is the table name used in SELECT queries
    """
    try:
        logger.info(f"Updating Oracle table name to: {table_name}")
        column_config.update_oracle_table(table_name)
        
        return {
            "success": True,
            "message": f"Oracle table updated to '{table_name}'",
            "table_name": table_name
        }
    except Exception as e:
        logger.error(f"Error updating Oracle table: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sql-preview")
async def preview_sql_query(where_clause: Optional[str] = None):
    """
    Preview the SQL query that will be used to extract data from Oracle
    
    Based on current column configuration
    """
    try:
        sql = column_config.generate_sql_select(where_clause or "")
        
        return {
            "success": True,
            "sql_query": sql,
            "column_count": len(column_config.get_oracle_column_names()),
            "oracle_table": column_config.get_oracle_table_name()
        }
    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oracle/test-connection")
async def test_oracle_connection():
    """
    Test Oracle database connection with current configuration
    
    Use this to verify Oracle credentials before enabling production mode
    """
    try:
        logger.info("Testing Oracle connection")
        result = db_service.test_oracle_connection()
        
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=503, detail=result)
    except Exception as e:
        logger.error(f"Oracle connection test failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/oracle/enable")
async def enable_oracle(config: OracleConfigUpdate):
    """
    Enable Oracle database mode
    
    Switches from Excel fallback to Oracle production database
    Requires valid AWS credentials and database access
    """
    try:
        logger.info("Enabling Oracle mode with provided credentials")
        
        oracle_config = {
            'host': config.host,
            'port': config.port,
            'service_name': config.service_name,
            'user': config.user,
            'password': config.password,
            'encoding': 'UTF-8'
        }
        
        db_service.enable_oracle(oracle_config)
        
        return {
            "success": True,
            "message": "Oracle mode enabled successfully",
            "connection_info": db_service.get_connection_info()
        }
    except Exception as e:
        logger.error(f"Failed to enable Oracle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connection-info")
async def get_connection_info():
    """
    Get current database connection information
    
    Shows whether system is using Excel or Oracle, and column configuration
    """
    try:
        info = db_service.get_connection_info()
        return {
            "success": True,
            **info
        }
    except Exception as e:
        logger.error(f"Error getting connection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-status")
async def get_system_status():
    """
    Get comprehensive system status including data source and output destination
    
    Returns:
        - Data source type and connection status
        - Output destination type and connection status
        - Configuration details
        - Integration readiness
    """
    try:
        # Get data source information
        data_source = get_data_source()
        data_source_info = data_source.get_source_info()
        data_source_test = data_source.test_connection()
        
        # Get output destination information
        output_destination = get_output_destination()
        output_dest_info = get_output_destination_info()
        
        # Test output destination(s)
        if isinstance(output_destination, list):
            output_dest_tests = []
            for dest in output_destination:
                test_result = dest.test_connection()
                output_dest_tests.append({
                    "type": dest.get_destination_info()['type'],
                    "status": test_result['status'],
                    "message": test_result['message']
                })
            output_dest_status = {
                "mode": "multiple",
                "tests": output_dest_tests
            }
        else:
            output_dest_test = output_destination.test_connection()
            output_dest_status = {
                "mode": "single",
                "type": output_dest_info['type'],
                "status": output_dest_test['status'],
                "message": output_dest_test['message']
            }
        
        # Overall readiness assessment
        data_source_ready = data_source_test['status'] == 'success'
        
        if isinstance(output_destination, list):
            output_ready = all(test['status'] == 'success' for test in output_dest_tests)
        else:
            output_ready = output_dest_test['status'] == 'success'
        
        overall_ready = data_source_ready and output_ready
        
        return {
            "success": True,
            "overall_status": "ready" if overall_ready else "not_ready",
            "data_source": {
                "info": data_source_info,
                "connection_test": data_source_test,
                "ready": data_source_ready
            },
            "output_destination": {
                "info": output_dest_info,
                "connection_test": output_dest_status,
                "ready": output_ready
            },
            "integrations": {
                "oracle": {
                    "configured": data_source_info.get('type') == 'Oracle',
                    "ready": data_source_ready if data_source_info.get('type') == 'Oracle' else False,
                    "instructions": "Set environment variables in .env file (see .env.example)"
                },
                "s3": {
                    "configured": output_dest_info.get('type') == 'AWS S3' or 
                                   (output_dest_info.get('mode') == 'multiple' and 
                                    any(d.get('type') == 'AWS S3' for d in output_dest_info.get('destinations', []))),
                    "ready": output_ready if (output_dest_info.get('type') == 'AWS S3' or 
                                              (output_dest_info.get('mode') == 'multiple' and 
                                               any(d.get('type') == 'AWS S3' for d in output_dest_info.get('destinations', [])))) else False,
                    "instructions": "Set environment variables in .env file (see .env.example)"
                }
            },
            "configuration_file": ".env (copy from .env.example if not exists)"
        }
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
