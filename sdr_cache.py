# Flask/sdr_cache.py
"""
Système de cache pour les résultats SDR
"""

import time
from typing import Any, Dict
from datetime import datetime, timedelta
import threading


class SDRCache:
    """Cache thread-safe pour les résultats SDR"""
    
    def __init__(self, default_ttl: int = 60):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.lock = threading.RLock()
        self.cleanup_interval = 300  # Nettoyage toutes les 5 minutes
        self.last_cleanup = time.time()
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        with self.lock:
            self._cleanup_if_needed()
            
            if key in self.cache:
                entry = self.cache[key]
                if time.time() < entry['expires_at']:
                    entry['hits'] += 1
                    entry['last_accessed'] = time.time()
                    return entry['value']
                else:
                    del self.cache[key]
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Stocke une valeur dans le cache"""
        with self.lock:
            ttl = ttl or self.default_ttl
            self.cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl,
                'created_at': time.time(),
                'last_accessed': time.time(),
                'hits': 0,
                'ttl': ttl
            }
    
    def delete(self, key: str) -> bool:
        """Supprime une clé du cache"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Vide complètement le cache"""
        with self.lock:
            self.cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Statistiques du cache"""
        with self.lock:
            now = time.time()
            active = sum(1 for v in self.cache.values() if now < v['expires_at'])
            expired = sum(1 for v in self.cache.values() if now >= v['expires_at'])
            total_hits = sum(v['hits'] for v in self.cache.values() if now < v['expires_at'])
            
            return {
                'total_entries': len(self.cache),
                'active_entries': active,
                'expired_entries': expired,
                'total_hits': total_hits,
                'memory_usage': self._estimate_memory()
            }
    
    def _cleanup_if_needed(self) -> None:
        """Nettoie les entrées expirées si nécessaire"""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_expired()
            self.last_cleanup = now
    
    def _cleanup_expired(self) -> None:
        """Supprime toutes les entrées expirées"""
        now = time.time()
        expired_keys = [k for k, v in self.cache.items() if now >= v['expires_at']]
        for key in expired_keys:
            del self.cache[key]
    
    def _estimate_memory(self) -> int:
        """Estime la mémoire utilisée (en bytes approximatifs)"""
        import sys
        total = 0
        for key, value in self.cache.items():
            total += sys.getsizeof(key)
            total += sys.getsizeof(value)
        return total


# Instance globale
sdr_cache = SDRCache(default_ttl=120)  # 2 minutes par défaut