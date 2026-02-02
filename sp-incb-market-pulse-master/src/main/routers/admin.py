#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Admin Router - APIs for system configuration and column management
"""
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime
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


class ExecuteQueryRequest(BaseModel):
    query: str = Field(..., description="SQL query to execute and fetch column metadata")
    clo_id: Optional[str] = Field(None, description="CLO ID to associate this query with")


class SaveQueryRequest(BaseModel):
    query: str = Field(..., description="SQL query to save for CLO")
    clo_id: str = Field(..., description="CLO ID to save query for")
    query_name: str = Field(default="base_query", description="Name for this query")


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


@router.post("/oracle/execute-query")
async def execute_oracle_query(request: ExecuteQueryRequest):
    """
    Execute Oracle query and return available columns
    
    This endpoint connects to Oracle database, executes the provided query,
    and returns the column metadata that can be used for CLO mapping configuration.
    """
    try:
        logger.info(f"Executing Oracle query for CLO: {request.clo_id}")
        
        # Get Oracle data source
        from services.data_source_factory import get_data_source
        import os
        
        # Temporarily check if Oracle is configured
        data_source_type = os.getenv('DATA_SOURCE', 'excel')
        if data_source_type != 'oracle':
            raise HTTPException(
                status_code=400, 
                detail="Oracle data source not configured. Set DATA_SOURCE=oracle in .env file"
            )
        
        data_source = get_data_source()
        
        # Execute the query and get column metadata
        try:
            import oracledb
            
            # Fetch credentials
            credentials = data_source._fetch_credentials()
            
            # Create connection
            dsn = oracledb.makedsn(
                data_source.oracle_host,
                data_source.oracle_port,
                service_name=data_source.oracle_service
            )
            
            connection = oracledb.connect(
                user=credentials["username"],
                password=credentials["password"],
                dsn=dsn
            )
            
            cursor = connection.cursor()
            
            # Execute query with ROWNUM limit for safety
            limited_query = f"SELECT * FROM ({request.query}) WHERE ROWNUM <= 1"
            cursor.execute(limited_query)
            
            # Get column metadata
            columns = []
            for desc in cursor.description:
                col_name = desc[0]
                col_type = desc[1].__name__ if hasattr(desc[1], '__name__') else str(desc[1])
                
                # Map Oracle types to our types
                data_type = "VARCHAR"
                if "NUMBER" in col_type or "INT" in col_type:
                    data_type = "INTEGER"
                elif "FLOAT" in col_type or "DECIMAL" in col_type:
                    data_type = "FLOAT"
                elif "DATE" in col_type or "TIMESTAMP" in col_type:
                    data_type = "DATE"
                
                columns.append({
                    "oracle_column_name": col_name,
                    "display_name": col_name.replace("_", " ").title(),
                    "data_type": data_type,
                    "enabled": False,  # Disabled by default
                    "required": False
                })
            
            cursor.close()
            connection.close()
            
            return {
                "success": True,
                "message": f"Query executed successfully. Found {len(columns)} columns.",
                "columns": columns,
                "query": request.query
            }
            
        except Exception as e:
            logger.error(f"Error executing Oracle query: {e}")
            raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in execute_oracle_query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oracle/save-query")
async def save_oracle_query(request: SaveQueryRequest):
    """
    Save Oracle query for a specific CLO
    
    This stores the query in column_config.json so it can be used
    for automated data fetching from Oracle database.
    """
    try:
        logger.info(f"Saving Oracle query for CLO: {request.clo_id}")
        
        # Load current config
        import json
        import os
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
        config_path = os.path.join(project_root, "column_config.json")
        
        config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        
        # Update or create CLO config
        if request.clo_id not in config:
            config[request.clo_id] = {
                "name": request.clo_id,
                "enabled": True,
                "columns": {},
                "queries": {}
            }
        
        # Ensure queries object exists
        if "queries" not in config[request.clo_id]:
            config[request.clo_id]["queries"] = {}
        
        # Save the query in the correct structure
        config[request.clo_id]["queries"][request.query_name] = {
            "query": request.query,
            "updated_at": datetime.now().isoformat()
        }
        
        # Save back to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return {
            "success": True,
            "message": f"Query saved successfully for CLO: {request.clo_id}",
            "clo_id": request.clo_id,
            "query": request.query
        }
        
    except Exception as e:
        logger.error(f"Error saving Oracle query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@router.post("/execute-query")
async def execute_oracle_query(request: ExecuteQueryRequest):
    """
    Execute a SQL query on Oracle database and return available columns.
    This allows super admin to test queries and see what columns are available.
    
    Returns:
        - List of column names
        - Data types for each column
        - Sample of first 5 rows (optional)
    """
    try:
        # Get Oracle data source
        data_source = get_data_source()
        data_source_info = get_data_source_info()
        
        if data_source_info.get('type') != 'Oracle':
            raise HTTPException(
                status_code=400, 
                detail="Oracle data source not configured. Set DATA_SOURCE=oracle in .env"
            )
        
        # Execute query and get column metadata
        logger.info(f"Executing custom query for CLO: {request.clo_id}")
        
        import oracledb
        
        # Get credentials
        credentials = data_source._fetch_credentials()
        
        # Create connection
        dsn = oracledb.makedsn(
            data_source.oracle_host,
            data_source.oracle_port,
            service_name=data_source.oracle_service
        )
        
        connection = oracledb.connect(
            user=credentials["username"],
            password=credentials["password"],
            dsn=dsn
        )
        
        cursor = connection.cursor()
        
        # Execute query with ROWNUM limit for safety
        safe_query = f"SELECT * FROM ({request.query}) WHERE ROWNUM <= 5"
        cursor.execute(safe_query)
        
        # Get column metadata
        columns_metadata = []
        for desc in cursor.description:
            col_name = desc[0]
            col_type = desc[1].__name__ if desc[1] else 'UNKNOWN'
            
            columns_metadata.append({
                "name": col_name,
                "oracle_name": col_name,
                "data_type": col_type,
                "display_name": col_name.replace('_', ' ').title(),
                "enabled": True
            })
        
        # Fetch sample data
        rows = cursor.fetchall()
        sample_data = []
        for row in rows:
            sample_data.append({
                columns_metadata[i]["name"]: str(val) if val is not None else None 
                for i, val in enumerate(row)
            })
        
        cursor.close()
        connection.close()
        
        return {
            "success": True,
            "query": request.query,
            "clo_id": request.clo_id,
            "total_columns": len(columns_metadata),
            "columns": columns_metadata,
            "sample_data": sample_data,
            "message": f"Query executed successfully. Found {len(columns_metadata)} columns."
        }
        
    except oracledb.Error as e:
        logger.error(f"Oracle error executing query: {e}")
        raise HTTPException(status_code=400, detail=f"Oracle error: {str(e)}")
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        raise HTTPException(status_code=500, detail=f"Error executing query: {str(e)}")


@router.post("/save-query")
async def save_clo_query(request: SaveQueryRequest):
    """
    Save a SQL query for a specific CLO in column_config.json.
    This query will be used when fetching data for this CLO.
    """
    try:
        logger.info(f"Saving query for CLO: {request.clo_id}")
        
        # Load current config
        import json
        import os
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        config_path = os.path.join(project_root, "column_config.json")
        
        # Load existing config
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Initialize CLO config if not exists
        if request.clo_id not in config:
            config[request.clo_id] = {
                "name": request.clo_id,
                "enabled": True,
                "queries": {},
                "columns": {}
            }
        
        # Save query
        if "queries" not in config[request.clo_id]:
            config[request.clo_id]["queries"] = {}
        
        config[request.clo_id]["queries"][request.query_name] = {
            "query": request.query,
            "created_at": str(datetime.now()),
            "updated_at": str(datetime.now())
        }
        
        # Save to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return {
            "success": True,
            "message": f"Query saved successfully for CLO: {request.clo_id}",
            "clo_id": request.clo_id,
            "query_name": request.query_name
        }
        
    except Exception as e:
        logger.error(f"Error saving query: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving query: {str(e)}")


@router.post("/update-clo-columns")
async def update_clo_columns(clo_id: str = Body(...), columns: List[Dict] = Body(...)):
    """
    Update which columns are enabled/visible for a specific CLO.
    Admin selects from available columns after executing query.
    """
    try:
        logger.info(f"Updating columns for CLO: {clo_id}")
        
        import json
        import os
        
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        config_path = os.path.join(project_root, "column_config.json")
        
        # Load existing config
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Initialize CLO config if not exists
        if clo_id not in config:
            config[clo_id] = {
                "name": clo_id,
                "enabled": True,
                "queries": {},
                "columns": {}
            }
        
        # Update columns configuration
        config[clo_id]["columns"] = {}
        for col in columns:
            col_key = col.get("name", col.get("oracle_name", ""))
            if col_key:
                config[clo_id]["columns"][col_key] = {
                    "oracle_column_name": col.get("oracle_name", col_key),
                    "display_name": col.get("display_name", col_key),
                    "data_type": col.get("data_type", "VARCHAR"),
                    "enabled": col.get("enabled", True),
                    "required": col.get("required", False)
                }
        
        config[clo_id]["updated_at"] = str(datetime.now())
        
        # Save to file
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return {
            "success": True,
            "message": f"Columns updated successfully for CLO: {clo_id}",
            "clo_id": clo_id,
            "total_columns": len(columns),
            "enabled_columns": sum(1 for col in columns if col.get("enabled", False))
        }
        
    except Exception as e:
        logger.error(f"Error updating CLO columns: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating columns: {str(e)}")
