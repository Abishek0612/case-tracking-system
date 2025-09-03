import json
import hashlib
from typing import Any, Optional
from datetime import datetime, timedelta
import logging


class CacheManager:
    """Simple in-memory cache manager"""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def _generate_key(self, namespace: str, key: str) -> str:
        """Generate cache key"""
        combined = f"{namespace}:{key}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    async def get(self, namespace: str, key: str, ttl: int = 3600) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._generate_key(namespace, key)
        
        if cache_key not in self._cache:
            return None
        
        timestamp = self._timestamps.get(cache_key)
        if timestamp and (datetime.now() - timestamp).total_seconds() > ttl:
            del self._cache[cache_key]
            del self._timestamps[cache_key]
            return None
        
        return self._cache[cache_key]
    
    async def set(self, namespace: str, key: str, value: Any):
        """Set value in cache"""
        cache_key = self._generate_key(namespace, key)
        self._cache[cache_key] = value
        self._timestamps[cache_key] = datetime.now()
    
    async def delete(self, namespace: str, key: str):
        """Delete value from cache"""
        cache_key = self._generate_key(namespace, key)
        self._cache.pop(cache_key, None)
        self._timestamps.pop(cache_key, None)
    
    async def clear_namespace(self, namespace: str):
        """Clear all keys in a namespace"""
        keys_to_delete = []
        namespace_prefix = f"{namespace}:"
        
        for cache_key in self._cache.keys():
            for stored_key in list(self._cache.keys()):
                if self._generate_key(namespace, "") in stored_key:
                    keys_to_delete.append(stored_key)
        
        for key in keys_to_delete:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)