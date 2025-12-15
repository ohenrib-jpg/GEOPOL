# Flask/weak_indicators/utils.py
"""Utilitaires pour le module"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

class CacheManager:
    """Gestionnaire de cache simple"""
    
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
    
    def set(self, key: str, value: Any, expire_minutes: int = 30):
        """Stocke une valeur dans le cache"""
        self._cache[key] = value
        self._timestamps[key] = datetime.utcnow() + timedelta(minutes=expire_minutes)
        logger.debug(f"Cache set: {key}")
    
    def get(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        return self._cache.get(key)
    
    def is_expired(self, key: str) -> bool:
        """Vérifie si une entrée est expirée"""
        if key not in self._timestamps:
            return True
        
        return datetime.utcnow() > self._timestamps[key]
    
    def clear_expired(self):
        """Nettoie les entrées expirées"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if now > timestamp
        ]
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
        
        if expired_keys:
            logger.debug(f"Cache cleared: {len(expired_keys)} entries")

def format_currency(amount: float) -> str:
    """Formate un montant en devise"""
    return f"{amount:,.2f}"

def format_percentage(value: float) -> str:
    """Formate un pourcentage"""
    return f"{value:+.2f}%" if value else "0.00%"

def risk_level_to_text(level: int) -> str:
    """Convertit le niveau de risque en texte"""
    levels = {
        1: "Précautions normales",
        2: "Prudence accrue",
        3: "Réenvisager le voyage",
        4: "Ne pas voyager"
    }
    return levels.get(level, "Inconnu")

def risk_level_to_color(level: int) -> str:
    """Convertit le niveau de risque en couleur"""
    colors = {
        1: "green",
        2: "yellow",
        3: "orange",
        4: "red"
    }
    return colors.get(level, "gray")
