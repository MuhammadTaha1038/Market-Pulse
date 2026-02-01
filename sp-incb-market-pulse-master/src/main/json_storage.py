"""
JSON file storage implementation
Used for Phase A (before S3/Oracle credentials)
"""

import json
import os
from typing import Any, Optional
from storage_interface import StorageInterface


class JSONStorage(StorageInterface):
    """
    JSON file-based storage implementation
    Stores data in local JSON files
    """
    
    def __init__(self, data_dir: str = "data"):
        """
        Initialize JSON storage
        
        Args:
            data_dir: Directory to store JSON files
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        print(f"📁 JSON Storage initialized at: {os.path.abspath(data_dir)}")
    
    def _get_path(self, key: str) -> str:
        """Get full file path for a key"""
        return os.path.join(self.data_dir, f"{key}.json")
    
    def save(self, key: str, data: Any):
        """Save data to JSON file"""
        try:
            with open(self._get_path(key), 'w') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Saved: {key}.json")
        except Exception as e:
            print(f"❌ Failed to save {key}: {e}")
            raise
    
    def load(self, key: str) -> Optional[Any]:
        """Load data from JSON file"""
        path = self._get_path(key)
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load {key}: {e}")
            return None
    
    def exists(self, key: str) -> bool:
        """Check if JSON file exists"""
        return os.path.exists(self._get_path(key))
    
    def delete(self, key: str):
        """Delete JSON file"""
        path = self._get_path(key)
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"🗑️ Deleted: {key}.json")
            except Exception as e:
                print(f"❌ Failed to delete {key}: {e}")
                raise
    
    def list_keys(self, prefix: str = "") -> list:
        """List all JSON files with optional prefix"""
        if not os.path.exists(self.data_dir):
            return []
        
        keys = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.json'):
                key = filename[:-5]  # Remove .json extension
                if key.startswith(prefix):
                    keys.append(key)
        
        return keys
