# Flask/geopol_data/service.py
"""
Service d'orchestration du module Geopol-Data
Gère le cache, la logique métier et l'agrégation des données
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from .models import CountrySnapshot
from .connectors.world_bank import WorldBankConnector
from .config import Config, CacheConfig
from .constants import CORE_INDICATORS, PRIORITY_COUNTRIES

logger = logging.getLogger(__name__)

# ============================================================================
# CLASSE PRINCIPALE : DATA SERVICE
# ============================================================================

class DataService:
    """
    Service d'orchestration pour les données géopolitiques
    Gère le cache, l'agrégation et la logique métier
    """
    
    def __init__(self, use_cache: bool = True):
        """
        Initialise le service
        
        Args:
            use_cache: Activer le cache en mémoire
        """
        self.wb_connector = WorldBankConnector()
        self.use_cache = use_cache and CacheConfig.ENABLED
        
        # Cache en mémoire
        self._cache: Dict[str, tuple[CountrySnapshot, datetime]] = {}
        self._cache_ttl = CacheConfig.TTL
        
        # Statistiques
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'total_requests': 0,
            'errors': 0
        }
        
        logger.info(f"DataService initialisé (cache: {self.use_cache})")
    
    # ========================================================================
    # MÉTHODE PRINCIPALE : Get Country Snapshot
    # ========================================================================
    
    def get_country_snapshot(self, country_code: str) -> Optional[CountrySnapshot]:
        """
        Récupère le snapshot complet d'un pays
        Utilise le cache si disponible et valide
        
        Args:
            country_code: Code ISO Alpha-2 (ex: 'FR', 'US')
        
        Returns:
            CountrySnapshot ou None si erreur
        
        Example:
            >>> service = DataService()
            >>> snapshot = service.get_country_snapshot('FR')
            >>> print(snapshot.format_gdp())
            '2.78T$'
        """
        self._stats['total_requests'] += 1
        country_code = country_code.upper()
        
        logger.info(f"Requête snapshot pour {country_code}")
        
        # Vérifier le cache
        if self.use_cache:
            cached = self._get_from_cache(country_code)
            if cached:
                self._stats['cache_hits'] += 1
                logger.debug(f"✓ Cache hit pour {country_code}")
                return cached
        
        self._stats['cache_misses'] += 1
        
        # Récupérer depuis World Bank
        try:
            snapshot = self._fetch_country_snapshot(country_code)
            
            if snapshot:
                # Mettre en cache
                if self.use_cache:
                    self._put_in_cache(country_code, snapshot)
                
                logger.info(f"✅ Snapshot créé pour {country_code}")
                return snapshot
            else:
                logger.warning(f"⚠️ Aucune donnée pour {country_code}")
                self._stats['errors'] += 1
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur snapshot {country_code}: {e}")
            self._stats['errors'] += 1
            return None
    
    # ========================================================================
    # MÉTHODES PRIVÉES : Cache
    # ========================================================================
    
    def _get_from_cache(self, country_code: str) -> Optional[CountrySnapshot]:
        """Récupère depuis le cache si valide"""
        if country_code not in self._cache:
            return None
        
        snapshot, cached_at = self._cache[country_code]
        
        # Vérifier si expiré
        if datetime.utcnow() - cached_at > self._cache_ttl:
            logger.debug(f"Cache expiré pour {country_code}")
            del self._cache[country_code]
            return None
        
        return snapshot
    
    def _put_in_cache(self, country_code: str, snapshot: CountrySnapshot):
        """Met en cache un snapshot"""
        self._cache[country_code] = (snapshot, datetime.utcnow())
        logger.debug(f"Snapshot mis en cache: {country_code}")
        
        # Nettoyer le cache si trop grand
        if len(self._cache) > CacheConfig.MAX_SIZE:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Nettoie les entrées expirées du cache"""
        now = datetime.utcnow()
        expired_keys = [
            key for key, (_, cached_at) in self._cache.items()
            if now - cached_at > self._cache_ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cache nettoyé: {len(expired_keys)} entrées supprimées")
    
    # ========================================================================
    # MÉTHODES PRIVÉES : Fetch Data
    # ========================================================================
    
    def _fetch_country_snapshot(self, country_code: str) -> Optional[CountrySnapshot]:
        """
        Récupère les données depuis World Bank et crée un snapshot
        
        Args:
            country_code: Code ISO du pays
        
        Returns:
            CountrySnapshot ou None
        """
        try:
            # Récupérer les indicateurs
            raw_data = self.wb_connector.fetch_indicators(
                country_code,
                CORE_INDICATORS
            )
            
            if not raw_data:
                logger.warning(f"Aucune donnée World Bank pour {country_code}")
                return None
            
            # Récupérer le nom du pays
            country_info = self.wb_connector.fetch_country_info(country_code)
            country_name = country_info.get('name', country_code) if country_info else country_code
            
            # Créer le snapshot
            snapshot = CountrySnapshot.from_world_bank(
                country_code=country_code,
                country_name=country_name,
                wb_data=raw_data
            )
            
            # Vérifier la complétude
            if not snapshot.is_complete(min_indicators=3):
                logger.warning(f"Snapshot incomplet pour {country_code} (< 3 indicateurs)")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Erreur fetch {country_code}: {e}")
            return None
    
    # ========================================================================
    # MÉTHODES UTILITAIRES
    # ========================================================================
    
    def get_multiple_snapshots(self, country_codes: List[str]) -> Dict[str, CountrySnapshot]:
        """
        Récupère plusieurs snapshots en une fois
        
        Args:
            country_codes: Liste de codes ISO
        
        Returns:
            Dict {code: snapshot}
        """
        results = {}
        
        for code in country_codes:
            snapshot = self.get_country_snapshot(code)
            if snapshot:
                results[code] = snapshot
        
        logger.info(f"Snapshots multiples: {len(results)}/{len(country_codes)} réussis")
        return results
    
    def preload_priority_countries(self):
        """
        Pré-charge les pays prioritaires dans le cache
        Utile au démarrage de l'application
        """
        logger.info(f"Pré-chargement de {len(PRIORITY_COUNTRIES)} pays prioritaires...")
        
        loaded = 0
        for code in PRIORITY_COUNTRIES[:20]:  # Limiter à 20 pour ne pas surcharger
            try:
                snapshot = self.get_country_snapshot(code)
                if snapshot:
                    loaded += 1
            except Exception as e:
                logger.error(f"Erreur pré-chargement {code}: {e}")
        
        logger.info(f"✅ {loaded}/{20} pays pré-chargés")
    
    def clear_cache(self):
        """Vide complètement le cache"""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache vidé: {count} entrées supprimées")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache
        
        Returns:
            Dict avec statistiques
        """
        total_requests = self._stats['total_requests']
        hits = self._stats['cache_hits']
        
        return {
            'cache_enabled': self.use_cache,
            'cache_size': len(self._cache),
            'cache_max_size': CacheConfig.MAX_SIZE,
            'cache_ttl_hours': CacheConfig.TTL_HOURS,
            'total_requests': total_requests,
            'cache_hits': hits,
            'cache_misses': self._stats['cache_misses'],
            'hit_rate': (hits / total_requests * 100) if total_requests > 0 else 0,
            'errors': self._stats['errors'],
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Retourne le status du service
        
        Returns:
            Dict avec informations de status
        """
        return {
            'service': 'DataService',
            'status': 'running',
            'world_bank_connection': self.wb_connector.test_connection(),
            'cache': self.get_cache_stats(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_available_countries(self) -> List[str]:
        """
        Retourne la liste des codes pays prioritaires
        
        Returns:
            Liste de codes ISO
        """
        return PRIORITY_COUNTRIES.copy()
    
    # ========================================================================
    # MÉTHODE DE FALLBACK
    # ========================================================================
    
    def get_fallback_snapshot(self, country_code: str) -> CountrySnapshot:
        """
        Retourne un snapshot de fallback avec données par défaut
        Utilisé quand l'API World Bank est inaccessible
        
        Args:
            country_code: Code ISO du pays
        
        Returns:
            CountrySnapshot avec données minimales
        """
        logger.warning(f"Utilisation du fallback pour {country_code}")
        
        # Mapping basique de noms
        fallback_names = {
            'FR': 'France',
            'US': 'United States',
            'GB': 'United Kingdom',
            'DE': 'Germany',
            'CN': 'China',
            'JP': 'Japan',
        }
        
        return CountrySnapshot(
            country_code=country_code,
            country_name=fallback_names.get(country_code, country_code),
            source='fallback',
            last_updated=datetime.utcnow()
        )

# ============================================================================
# INSTANCE GLOBALE (singleton pattern)
# ============================================================================

_service_instance: Optional[DataService] = None

def get_data_service() -> DataService:
    """
    Retourne l'instance singleton du DataService
    
    Returns:
        Instance unique du DataService
    """
    global _service_instance
    
    if _service_instance is None:
        _service_instance = DataService()
    
    return _service_instance

# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == '__main__':
    # Configuration logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("TEST DATA SERVICE")
    print("=" * 70)
    
    # Créer le service
    service = DataService()
    
    # Test 1: Récupérer un pays
    print("\n1. Test récupération France...")
    snapshot = service.get_country_snapshot('FR')
    if snapshot:
        print(snapshot.to_summary())
    
    # Test 2: Vérifier le cache
    print("\n2. Test cache (2ème requête)...")
    snapshot2 = service.get_country_snapshot('FR')
    print(f"✅ Snapshot récupéré depuis le cache")
    
    # Test 3: Statistiques
    print("\n3. Statistiques du service:")
    stats = service.get_cache_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 70)
    print("TESTS TERMINÉS")
    print("=" * 70)
