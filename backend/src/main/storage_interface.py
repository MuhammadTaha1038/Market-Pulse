"""
Storage abstraction interface
Allows switching between JSON, S3, and Oracle storage
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class StorageInterface(ABC):
    """
    Base interface for all storage implementations
    Implementations: JSONStorage, S3Storage, OracleStorage
    """
    
    @abstractmethod
    def save(self, key: str, data: Any):
        """
        Save data to storage
        
        Args:
            key: Storage key/identifier
            data: Data to save (dict, list, etc.)
        """
        pass
    
    @abstractmethod
    def load(self, key: str) -> Optional[Any]:
        """
        Load data from storage
        
        Args:
            key: Storage key/identifier
            
        Returns:
            Data if found, None otherwise
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if key exists in storage
        
        Args:
            key: Storage key/identifier
            
        Returns:
            True if exists, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, key: str):
        """
        Delete data from storage
        
        Args:
            key: Storage key/identifier
        """
        pass
    
    @abstractmethod
    def list_keys(self, prefix: str = "") -> list:
        """
        List all keys with optional prefix filter
        
        Args:
            prefix: Optional prefix to filter keys
            
        Returns:
            List of keys
        """
        pass
