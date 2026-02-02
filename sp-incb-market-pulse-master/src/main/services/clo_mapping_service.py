#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLO Mapping Service - Manages column visibility per CLO type
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class CLOMappingService:
    """
    Manages CLO (Collateralized Loan Obligation) to column mappings
    Super admin can configure which columns each CLO type can see
    """
    
    def __init__(self, mappings_file: str = None, clo_structure_file: str = None):
        """
        Initialize CLO mapping service
        
        Args:
            mappings_file: Path to JSON file storing CLO-column mappings
            clo_structure_file: Path to JSON file with CLO hierarchy
        """
        if mappings_file is None:
            base_dir = Path(__file__).parent.parent
            mappings_file = base_dir / "data" / "clo_mappings.json"
        
        if clo_structure_file is None:
            base_dir = Path(__file__).parent.parent
            clo_structure_file = base_dir / "data" / "clo_structure.json"
        
        self.mappings_file = str(mappings_file)
        self.clo_structure_file = str(clo_structure_file)
        
        # Load CLO structure
        self.clo_structure = self._load_clo_structure()
        
        # Load or initialize mappings
        self.mappings = self._load_mappings()
        
        logger.info(f"CLOMappingService initialized: {len(self.clo_structure.get('main_clos', []))} main CLOs")
    
    def _load_clo_structure(self) -> dict:
        """Load CLO hierarchy structure"""
        try:
            with open(self.clo_structure_file, 'r') as f:
                structure = json.load(f)
                logger.info(f"Loaded CLO structure from {self.clo_structure_file}")
                return structure
        except FileNotFoundError:
            logger.warning("CLO structure file not found, using empty structure")
            return {"main_clos": []}
        except Exception as e:
            logger.error(f"Error loading CLO structure: {e}")
            return {"main_clos": []}
    
    def _load_mappings(self) -> dict:
        """Load existing CLO-column mappings"""
        try:
            with open(self.mappings_file, 'r') as f:
                mappings = json.load(f)
                logger.info(f"Loaded {len(mappings.get('mappings', []))} CLO mappings")
                return mappings
        except FileNotFoundError:
            logger.info("No existing mappings, initializing with default (all columns visible)")
            return self._initialize_default_mappings()
        except Exception as e:
            logger.error(f"Error loading mappings: {e}")
            return self._initialize_default_mappings()
    
    def _initialize_default_mappings(self) -> dict:
        """
        Initialize default mappings where all CLO types see all columns
        Called on first run or if mappings file doesn't exist
        """
        from services.column_config_service import get_column_config
        column_config = get_column_config()
        all_columns = [col['oracle_name'] for col in column_config.config['columns']]
        
        mappings = {
            "version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "mappings": []
        }
        
        # Create mapping for each main CLO
        for main_clo in self.clo_structure.get('main_clos', []):
            mappings['mappings'].append({
                "clo_id": main_clo['id'],
                "clo_type": "main",
                "visible_columns": all_columns.copy(),
                "hidden_columns": [],
                "updated_by": "system",
                "updated_at": datetime.now().isoformat()
            })
            
            # Create mapping for each sub CLO
            for sub_clo in main_clo.get('sub_clos', []):
                mappings['mappings'].append({
                    "clo_id": sub_clo['id'],
                    "clo_type": "sub",
                    "parent_clo_id": sub_clo['parent_clo_id'],
                    "visible_columns": all_columns.copy(),
                    "hidden_columns": [],
                    "updated_by": "system",
                    "updated_at": datetime.now().isoformat()
                })
        
        # Save initial mappings
        self._save_mappings(mappings)
        logger.info(f"Initialized {len(mappings['mappings'])} default CLO mappings (all columns visible)")
        return mappings
    
    def _save_mappings(self, mappings: dict):
        """Save mappings to file"""
        try:
            # Create directory if it doesn't exist
            Path(self.mappings_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.mappings_file, 'w') as f:
                json.dump(mappings, f, indent=2)
            logger.info(f"Saved CLO mappings to {self.mappings_file}")
        except Exception as e:
            logger.error(f"Error saving mappings: {e}")
            raise
    
    def get_clo_hierarchy(self) -> dict:
        """Get full CLO hierarchy"""
        return self.clo_structure
    
    def get_all_mappings(self) -> List[dict]:
        """Get all CLO-column mappings"""
        return self.mappings.get('mappings', [])
    
    def get_mapping_by_clo(self, clo_id: str) -> Optional[dict]:
        """
        Get column mapping for a specific CLO
        
        Args:
            clo_id: CLO identifier
            
        Returns:
            Mapping dict or None if not found
        """
        for mapping in self.mappings.get('mappings', []):
            if mapping['clo_id'] == clo_id:
                return mapping
        return None
    
    def get_visible_columns_for_clo(self, clo_id: str) -> List[str]:
        """
        Get list of visible column names for a CLO type
        
        Args:
            clo_id: CLO identifier
            
        Returns:
            List of column oracle_names that are visible
        """
        mapping = self.get_mapping_by_clo(clo_id)
        if mapping:
            return mapping.get('visible_columns', [])
        
        # Default: all columns visible
        from services.column_config_service import get_column_config
        column_config = get_column_config()
        return [col['oracle_name'] for col in column_config.config['columns']]
    
    def update_clo_mapping(
        self,
        clo_id: str,
        visible_columns: List[str],
        updated_by: str = "admin"
    ) -> dict:
        """
        Update column visibility for a CLO type
        
        Args:
            clo_id: CLO identifier
            visible_columns: List of column oracle_names to make visible
            updated_by: Username of admin making the change
            
        Returns:
            Updated mapping dict
        """
        from services.column_config_service import get_column_config
        column_config = get_column_config()
        all_columns = [col['oracle_name'] for col in column_config.config['columns']]
        
        # Calculate hidden columns
        hidden_columns = [col for col in all_columns if col not in visible_columns]
        
        # Find and update existing mapping
        updated = False
        for i, mapping in enumerate(self.mappings['mappings']):
            if mapping['clo_id'] == clo_id:
                self.mappings['mappings'][i].update({
                    "visible_columns": visible_columns,
                    "hidden_columns": hidden_columns,
                    "updated_by": updated_by,
                    "updated_at": datetime.now().isoformat()
                })
                updated = True
                break
        
        if not updated:
            # Create new mapping if doesn't exist
            self.mappings['mappings'].append({
                "clo_id": clo_id,
                "clo_type": "unknown",  # Will be determined from CLO ID
                "visible_columns": visible_columns,
                "hidden_columns": hidden_columns,
                "updated_by": updated_by,
                "updated_at": datetime.now().isoformat()
            })
        
        # Update timestamp
        self.mappings['last_updated'] = datetime.now().isoformat()
        
        # Save to file
        self._save_mappings(self.mappings)
        
        logger.info(f"Updated CLO mapping for {clo_id}: {len(visible_columns)} visible, {len(hidden_columns)} hidden")
        
        return self.get_mapping_by_clo(clo_id)
    
    def get_clo_details(self, clo_id: str) -> Optional[dict]:
        """
        Get CLO details from hierarchy
        
        Args:
            clo_id: CLO identifier
            
        Returns:
            CLO details dict or None
        """
        # Check main CLOs
        for main_clo in self.clo_structure.get('main_clos', []):
            if main_clo['id'] == clo_id:
                return {
                    **main_clo,
                    "clo_type": "main",
                    "parent_clo": None
                }
            
            # Check sub CLOs
            for sub_clo in main_clo.get('sub_clos', []):
                if sub_clo['id'] == clo_id:
                    return {
                        **sub_clo,
                        "clo_type": "sub",
                        "parent_clo": main_clo['name']
                    }
        
        return None
    
    def get_mapping_with_column_details(self, clo_id: str) -> Optional[dict]:
        """
        Get CLO mapping with full column details (not just names)
        
        Args:
            clo_id: CLO identifier
            
        Returns:
            Mapping with column metadata
        """
        from services.column_config_service import get_column_config
        column_config = get_column_config()
        
        mapping = self.get_mapping_by_clo(clo_id)
        clo_details = self.get_clo_details(clo_id)
        
        if not mapping or not clo_details:
            return None
        
        # Get full details for visible columns
        visible_columns_details = []
        for col_name in mapping.get('visible_columns', []):
            for col in column_config.config['columns']:
                if col['oracle_name'] == col_name:
                    visible_columns_details.append(col)
                    break
        
        # Get full details for hidden columns
        hidden_columns_details = []
        for col_name in mapping.get('hidden_columns', []):
            for col in column_config.config['columns']:
                if col['oracle_name'] == col_name:
                    hidden_columns_details.append(col)
                    break
        
        return {
            "clo_id": clo_id,
            "clo_name": clo_details.get('display_name', clo_details.get('name')),
            "clo_type": clo_details.get('clo_type'),
            "parent_clo": clo_details.get('parent_clo'),
            "visible_columns": visible_columns_details,
            "hidden_columns": hidden_columns_details,
            "total_columns": len(visible_columns_details) + len(hidden_columns_details),
            "updated_by": mapping.get('updated_by'),
            "updated_at": mapping.get('updated_at')
        }
    
    def get_user_columns(self, clo_id: str) -> Optional[dict]:
        """
        Get user-visible columns for a CLO (simplified format for API response)
        This is what the dashboard API needs for column filtering
        
        Args:
            clo_id: CLO identifier
            
        Returns:
            Dict with clo_id, clo_name, clo_type, parent_clo, visible_columns (list of names)
        """
        mapping = self.get_mapping_by_clo(clo_id)
        clo_details = self.get_clo_details(clo_id)
        
        if not mapping or not clo_details:
            return None
        
        return {
            "clo_id": clo_id,
            "clo_name": clo_details.get('display_name', clo_details.get('name')),
            "clo_type": clo_details.get('clo_type'),
            "parent_clo": clo_details.get('parent_clo'),
            "visible_columns": mapping.get('visible_columns', []),
            "column_count": len(mapping.get('visible_columns', []))
        }


# Singleton instance
_clo_mapping_service = None

def get_clo_mapping_service() -> CLOMappingService:
    """Get singleton CLO mapping service instance"""
    global _clo_mapping_service
    if _clo_mapping_service is None:
        _clo_mapping_service = CLOMappingService()
    return _clo_mapping_service
