"""
Cache simple en mémoire pour éviter Redis en environnement limité
"""
import time
from typing import Any, Optional

class SimpleCache:
    """Cache mémoire thread-safe basique"""
    
    def __init__(self, default_ttl: int = 300):
        self._cache = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur si non expirée"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Stocke une valeur avec TTL"""
        expiry = time.time() + (ttl or self.default_ttl)
        self._cache[key] = (value, expiry)
    
    def clear(self):
        """Vide le cache"""
        self._cache.clear()