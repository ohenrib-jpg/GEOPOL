"""
Cache intelligent pour les connecteurs sécurité et gouvernance
Utilise le CacheManager global avec stratégies de cache adaptées
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Callable, Tuple, List
import hashlib
import json
import time

logger = logging.getLogger(__name__)

# Import du cache_manager global
try:
    # Import absolu depuis Flask
    import sys
    import os
    # Ajouter le répertoire parent au path si nécessaire
    flask_dir = os.path.join(os.path.dirname(__file__), '..')
    if flask_dir not in sys.path:
        sys.path.insert(0, flask_dir)

    from cache_manager import cache_manager
    CACHE_AVAILABLE = True
    logger.info("CacheManager global importé avec succès")
except ImportError as e:
    CACHE_AVAILABLE = False
    cache_manager = None
    logger.warning(f"CacheManager non disponible: {e}. Le cache sera désactivé.")

# Import du circuit breaker
try:
    from .circuit_breaker import CircuitBreakerManager, with_circuit_breaker
    CIRCUIT_BREAKER_AVAILABLE = True
    logger.info("CircuitBreaker importé avec succès")
except ImportError as e:
    CIRCUIT_BREAKER_AVAILABLE = False
    CircuitBreakerManager = None
    with_circuit_breaker = lambda *args, **kwargs: lambda func: func  # Décorateur factice
    logger.warning(f"CircuitBreaker non disponible: {e}")

# Stratégies de cache par source de données
CACHE_STRATEGIES = {
    # UCDP: données de conflits récents (fréquence quotidienne)
    'ucdp': {
        'ttl_hours': 1,           # 1 heure pour données récentes
        'stale_ttl_hours': 24,    # 24 heures pour données périmées (fallback)
        'compress': True,
        'description': 'UCDP conflict data (daily updates)',
        'circuit_breaker': True,  # Activer circuit breaker
        'circuit_threshold': 3,   # 3 échecs avant ouverture
        'circuit_reset': 300      # 5 minutes avant réessai
    },
    # Transparency International CPI: données annuelles
    'transparency_cpi': {
        'ttl_hours': 24,          # 24 heures (données annuelles)
        'stale_ttl_hours': 168,   # 1 semaine pour fallback
        'compress': True,
        'description': 'CPI corruption data (annual updates)',
        'circuit_breaker': True,
        'circuit_threshold': 2,
        'circuit_reset': 600      # 10 minutes
    },
    # World Bank corruption data
    'worldbank_corruption': {
        'ttl_hours': 12,
        'stale_ttl_hours': 72,
        'compress': True,
        'description': 'World Bank control of corruption',
        'circuit_breaker': True,
        'circuit_threshold': 3,
        'circuit_reset': 300
    },
    # OCHA/HDX: crises humanitaires (fréquence quotidienne)
    'ocha_hdx': {
        'ttl_hours': 2,
        'stale_ttl_hours': 48,
        'compress': True,
        'description': 'UN OCHA humanitarian data',
        'circuit_breaker': True,
        'circuit_threshold': 3,
        'circuit_reset': 180      # 3 minutes
    },
    # Global Incident Map
    'global_incident': {
        'ttl_hours': 1,
        'stale_ttl_hours': 24,
        'compress': True,
        'description': 'Global security incidents',
        'circuit_breaker': True,
        'circuit_threshold': 3,
        'circuit_reset': 120      # 2 minutes
    },
    # ACLED
    'acled': {
        'ttl_hours': 1,
        'stale_ttl_hours': 24,
        'compress': True,
        'description': 'ACLED conflict data',
        'circuit_breaker': True,
        'circuit_threshold': 3,
        'circuit_reset': 180
    },
    # OFAC sanctions - OPTIMISÉ pour résilience
    'ofac_sdn': {
        'ttl_hours': 12,          # Augmenté à 12h (données moins fréquentes)
        'stale_ttl_hours': 168,   # 1 semaine pour fallback (augmenté)
        'compress': True,
        'description': 'OFAC sanctions list',
        'circuit_breaker': True,
        'circuit_threshold': 2,   # Plus sensible aux échecs
        'circuit_reset': 900,     # 15 minutes avant réessai
        'fallback_enabled': True,
        'hierarchical_cache': True  # Cache hiérarchique
    },
    # Sanctions plugin - nouvelle stratégie
    'sanctions_monitor': {
        'ttl_hours': 6,           # 6 heures pour données mixtes
        'stale_ttl_hours': 96,    # 4 jours pour fallback
        'compress': True,
        'description': 'Sanctions monitor plugin data',
        'circuit_breaker': True,
        'circuit_threshold': 3,
        'circuit_reset': 600,
        'fallback_enabled': True,
        'hierarchical_cache': True
    },
    # Douanes Françaises
    'douanes_fr': {
        'ttl_hours': 8,
        'stale_ttl_hours': 72,
        'compress': True,
        'description': 'Douanes Françaises sanctions',
        'circuit_breaker': True,
        'circuit_threshold': 2,
        'circuit_reset': 300
    },
    # Sanctions UE
    'eu_sanctions': {
        'ttl_hours': 12,
        'stale_ttl_hours': 168,
        'compress': True,
        'description': 'EU sanctions data',
        'circuit_breaker': True,
        'circuit_threshold': 2,
        'circuit_reset': 600
    },
    # GDELT Global Incident Map
    'gdelt': {
        'ttl_hours': 1,
        'stale_ttl_hours': 24,
        'compress': True,
        'description': 'GDELT global incidents',
        'circuit_breaker': True,
        'circuit_threshold': 3,
        'circuit_reset': 180
    },
    # OpenSanctions
    'opensanctions': {
        'ttl_hours': 6,
        'stale_ttl_hours': 48,
        'compress': True,
        'description': 'OpenSanctions data',
        'circuit_breaker': True,
        'circuit_threshold': 3,
        'circuit_reset': 300
    }
}


class SecurityCache:
    """Classe helper pour la gestion du cache des connecteurs sécurité"""

    @staticmethod
    def generate_key(source: str, method: str, *args, **kwargs) -> str:
        """
        Génère une clé de cache unique basée sur la source, méthode et paramètres

        Args:
            source: Source de données (ex: 'ucdp', 'transparency_cpi')
            method: Méthode appelée (ex: 'get_recent_conflicts')
            *args, **kwargs: Paramètres de la méthode

        Returns:
            Clé de cache unique
        """
        # Convertir arguments en chaîne stable
        args_str = json.dumps(args, sort_keys=True, default=str)
        kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)

        # Créer une empreinte unique
        key_parts = [source, method, args_str, kwargs_str]
        key_string = '_'.join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()

        return f"{source}_{method}_{key_hash[:12]}"

    @staticmethod
    def get_cache_strategy(source: str) -> Dict[str, Any]:
        """
        Retourne la stratégie de cache pour une source

        Args:
            source: Source de données

        Returns:
            Dictionnaire de stratégie ou stratégie par défaut
        """
        return CACHE_STRATEGIES.get(source, {
            'ttl_hours': 6,
            'stale_ttl_hours': 48,
            'compress': True,
            'description': 'Default cache strategy',
            'circuit_breaker': False,
            'circuit_threshold': 3,
            'circuit_reset': 60,
            'fallback_enabled': False,
            'hierarchical_cache': False
        })

    @staticmethod
    def get_circuit_breaker(source: str, fallback_func: Optional[Callable] = None):
        """
        Obtient un circuit breaker pour une source

        Args:
            source: Source de données
            fallback_func: Fonction de fallback optionnelle

        Returns:
            CircuitBreaker ou None si non disponible
        """
        if not CIRCUIT_BREAKER_AVAILABLE:
            logger.debug(f"Circuit breaker non disponible pour {source}")
            return None

        try:
            strategy = SecurityCache.get_cache_strategy(source)
            if not strategy.get('circuit_breaker', False):
                logger.debug(f"Circuit breaker désactivé pour {source}")
                return None

            breaker_name = f"security_{source}"
            threshold = strategy.get('circuit_threshold', 3)
            reset_timeout = strategy.get('circuit_reset', 60)

            breaker = CircuitBreakerManager.get_breaker(
                name=breaker_name,
                failure_threshold=threshold,
                reset_timeout=reset_timeout,
                fallback_func=fallback_func
            )

            logger.debug(f"Circuit breaker obtenu pour {source}: threshold={threshold}, reset={reset_timeout}s")
            return breaker

        except Exception as e:
            logger.error(f"Erreur création circuit breaker pour {source}: {e}")
            return None

    @staticmethod
    def with_circuit_breaker(source: str, fallback_func: Optional[Callable] = None):
        """
        Décorateur pour ajouter un circuit breaker à une fonction

        Args:
            source: Source de données
            fallback_func: Fonction de fallback

        Returns:
            Décorateur avec circuit breaker
        """
        if not CIRCUIT_BREAKER_AVAILABLE:
            logger.debug(f"Circuit breaker non disponible - décorateur ignoré pour {source}")
            return lambda func: func

        try:
            strategy = SecurityCache.get_cache_strategy(source)
            if not strategy.get('circuit_breaker', False):
                logger.debug(f"Circuit breaker désactivé - décorateur ignoré pour {source}")
                return lambda func: func

            breaker_name = f"security_{source}"
            threshold = strategy.get('circuit_threshold', 3)
            reset_timeout = strategy.get('circuit_reset', 60)

            logger.debug(f"Création décorateur circuit breaker pour {source}")
            return with_circuit_breaker(
                breaker_name=breaker_name,
                failure_threshold=threshold,
                reset_timeout=reset_timeout,
                fallback_func=fallback_func
            )

        except Exception as e:
            logger.error(f"Erreur création décorateur circuit breaker pour {source}: {e}")
            return lambda func: func

    @staticmethod
    def get_cached_data(source: str, method: str, *args, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Récupère des données du cache avec support hiérarchique

        Args:
            source: Source de données
            method: Méthode appelée
            *args, **kwargs: Paramètres de la méthode

        Returns:
            Données en cache ou None si non trouvées/expirées
        """
        if not CACHE_AVAILABLE or not cache_manager:
            logger.warning("CacheManager non disponible - retourne None")
            return None

        try:
            cache_key = SecurityCache.generate_key(source, method, *args, **kwargs)
            strategy = SecurityCache.get_cache_strategy(source)

            # Vérifier si cache hiérarchique activé
            if strategy.get('hierarchical_cache', False):
                return SecurityCache._get_hierarchical_cache(source, method, cache_key, strategy, *args, **kwargs)

            # Cache standard
            return SecurityCache._get_standard_cache(source, method, cache_key, strategy)

        except Exception as e:
            logger.error(f"Erreur récupération cache {source}.{method}: {e}")
            return None

    @staticmethod
    def _get_standard_cache(source: str, method: str, cache_key: str, strategy: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Récupération cache standard"""
        # Essayer d'abord avec données fraîches
        cached = cache_manager.get(source, cache_key, ignore_expiration=False)

        if cached:
            logger.debug(f"[CACHE HIT] {source}.{method} - données fraîches")
            return cached['data']

        # Si données fraîches non disponibles, essayer avec données périmées (fallback)
        logger.debug(f"[CACHE MISS] {source}.{method} - essai avec données périmées")
        stale_cached = cache_manager.get(source, cache_key, ignore_expiration=True)

        if stale_cached:
            # Vérifier si données périmées sont acceptables (délai stale_ttl)
            expires_at = datetime.fromisoformat(stale_cached['expires_at'])
            stale_cutoff = datetime.now() - timedelta(hours=strategy['stale_ttl_hours'])

            if expires_at > stale_cutoff:
                logger.info(f"[CACHE STALE] {source}.{method} - utilisation données périmées")
                return stale_cached['data']
            else:
                logger.debug(f"[CACHE EXPIRED] {source}.{method} - données trop anciennes")

        return None

    @staticmethod
    def _get_hierarchical_cache(source: str, method: str, cache_key: str, strategy: Dict[str, Any], *args, **kwargs) -> Optional[Dict[str, Any]]:
        """Récupération cache hiérarchique (mémoire + disque)"""
        # Niveau 1: Cache mémoire rapide (si disponible)
        memory_cache_key = f"memory_{cache_key}"

        try:
            # Essayer un cache mémoire simple (dictionnaire global)
            if not hasattr(SecurityCache, '_memory_cache'):
                SecurityCache._memory_cache = {}

            if memory_cache_key in SecurityCache._memory_cache:
                cached_entry = SecurityCache._memory_cache[memory_cache_key]
                # Vérifier expiration mémoire (TTL plus court)
                if time.time() - cached_entry['timestamp'] < 300:  # 5 minutes
                    logger.debug(f"[MEMORY CACHE HIT] {source}.{method}")
                    return cached_entry['data']
                else:
                    # Nettoyer entrée expirée
                    del SecurityCache._memory_cache[memory_cache_key]
        except Exception as e:
            logger.debug(f"Erreur cache mémoire {source}.{method}: {e}")

        # Niveau 2: Cache disque (cache_manager standard)
        cached = SecurityCache._get_standard_cache(source, method, cache_key, strategy)

        if cached:
            # Mettre en cache mémoire pour accès futur rapide
            try:
                SecurityCache._memory_cache[memory_cache_key] = {
                    'data': cached,
                    'timestamp': time.time()
                }
                # Limiter taille cache mémoire
                if len(SecurityCache._memory_cache) > 100:
                    # Supprimer les plus anciennes entrées
                    oldest_keys = sorted(SecurityCache._memory_cache.keys(),
                                       key=lambda k: SecurityCache._memory_cache[k]['timestamp'])[:20]
                    for key in oldest_keys:
                        del SecurityCache._memory_cache[key]
            except Exception as e:
                logger.debug(f"Erreur mise en cache mémoire {source}.{method}: {e}")

        return cached

    @staticmethod
    def set_cached_data(source: str, method: str, data: Any, *args, **kwargs) -> bool:
        """
        Stocke des données dans le cache avec support hiérarchique

        Args:
            source: Source de données
            method: Méthode appelée
            data: Données à cacher
            *args, **kwargs: Paramètres de la méthode (pour génération clé)

        Returns:
            True si succès, False sinon
        """
        if not CACHE_AVAILABLE or not cache_manager:
            logger.warning("CacheManager non disponible - skip cache")
            return False

        try:
            cache_key = SecurityCache.generate_key(source, method, *args, **kwargs)
            strategy = SecurityCache.get_cache_strategy(source)
            logger.debug(f"[CACHE SET] Génération clé: {cache_key} pour {source}.{method}")

            # Stocker dans le cache disque principal
            success = cache_manager.set(
                source=source,
                identifier=cache_key,
                data=data,
                ttl_hours=strategy['ttl_hours'],
                compress=strategy['compress']
            )

            if success:
                logger.debug(f"[CACHE SET] {source}.{method} - TTL {strategy['ttl_hours']}h")

                # Si cache hiérarchique activé, mettre aussi en cache mémoire
                if strategy.get('hierarchical_cache', False):
                    SecurityCache._set_memory_cache(source, method, cache_key, data)

            else:
                logger.warning(f"[CACHE FAIL] {source}.{method} - échec stockage")

            return success

        except Exception as e:
            logger.error(f"Erreur stockage cache {source}.{method}: {e}")
            return False

    @staticmethod
    def _set_memory_cache(source: str, method: str, cache_key: str, data: Any):
        """Stocke dans le cache mémoire hiérarchique"""
        try:
            memory_cache_key = f"memory_{cache_key}"

            if not hasattr(SecurityCache, '_memory_cache'):
                SecurityCache._memory_cache = {}

            SecurityCache._memory_cache[memory_cache_key] = {
                'data': data,
                'timestamp': time.time()
            }

            # Limiter taille cache mémoire
            if len(SecurityCache._memory_cache) > 100:
                # Supprimer les plus anciennes entrées
                oldest_keys = sorted(SecurityCache._memory_cache.keys(),
                                   key=lambda k: SecurityCache._memory_cache[k]['timestamp'])[:20]
                for key in oldest_keys:
                    del SecurityCache._memory_cache[key]

            logger.debug(f"[MEMORY CACHE SET] {source}.{method}")

        except Exception as e:
            logger.debug(f"Erreur cache mémoire {source}.{method}: {e}")

    @staticmethod
    def invalidate_cache(source: str, method: str = None, *args, **kwargs) -> bool:
        """
        Invalide une entrée du cache

        Args:
            source: Source de données
            method: Méthode spécifique (None pour toutes les méthodes de la source)
            *args, **kwargs: Paramètres de la méthode (optionnel)

        Returns:
            True si succès, False sinon
        """
        if not CACHE_AVAILABLE or not cache_manager:
            return False

        try:
            if method:
                # Invalider une entrée spécifique
                cache_key = SecurityCache.generate_key(source, method, *args, **kwargs)
                return cache_manager.delete(source, cache_key)
            else:
                # Invalider toutes les entrées de la source
                deleted = cache_manager.clear_source(source)
                logger.info(f"[CACHE CLEAR] Source {source} - {deleted} entrées supprimées")
                return deleted > 0

        except Exception as e:
            logger.error(f"Erreur invalidation cache {source}: {e}")
            return False


def cached_connector_method(*args, **kwargs):
    """
    Décorateur pour les méthodes de connecteur avec cache intelligent

    Usage:
        Style ancien (source uniquement):
        @cached_connector_method('ucdp')
        def get_recent_conflicts(self, days=30, limit=50):
            # logique de récupération
            return data

        Style nouveau (avec cache_type et ttl_seconds):
        @cached_connector_method(cache_type='gdelt', ttl_seconds=1800)
        def get_recent_incidents(self, days=7, limit=100):
            # logique de récupération
            return data
    """
    # Déterminer la source de cache
    source = None
    if 'cache_type' in kwargs:
        source = kwargs['cache_type']
    elif args:
        source = args[0]
    else:
        source = 'default'
        logger.warning("cached_connector_method appelé sans source ni cache_type, utilisation 'default'")

    # ttl_seconds est ignoré car la stratégie de cache utilise ttl_hours
    # mais on pourrait l'utiliser pour créer une stratégie dynamique (option future)

    def decorator(func):
        def wrapper(self, *inner_args, **inner_kwargs):
            # Nom complet de la méthode
            method_name = func.__name__
            logger.debug(f"[CACHE DECORATOR] {source}.{method_name} appelée avec args={inner_args}, kwargs={inner_kwargs}")

            # Essayer de récupérer depuis le cache
            cached_data = SecurityCache.get_cached_data(source, method_name, *inner_args, **inner_kwargs)

            if cached_data is not None:
                logger.debug(f"[CACHE DECORATOR] Données trouvées en cache pour {source}.{method_name}")
                # Ajouter un flag indiquant que les données viennent du cache
                if isinstance(cached_data, dict):
                    cached_data['_cached'] = True
                    cached_data['_cache_source'] = source
                    cached_data['_cache_method'] = method_name
                return cached_data

            logger.debug(f"[CACHE DECORATOR] Cache miss pour {source}.{method_name}")
            # Si non en cache, exécuter la méthode originale
            result = func(self, *inner_args, **inner_kwargs)

            # Stocker le résultat dans le cache si succès
            if result and isinstance(result, dict) and result.get('success', False):
                logger.debug(f"[CACHE DECORATOR] Succès, stockage en cache pour {source}.{method_name}")
                # Stocker les données (sans métadonnées de cache pour éviter récursion)
                cache_data = result.copy()
                SecurityCache.set_cached_data(source, method_name, cache_data, *inner_args, **inner_kwargs)
            else:
                logger.debug(f"[CACHE DECORATOR] Échec ou non stockage pour {source}.{method_name}")

            return result
        return wrapper
    return decorator


# Fonctions utilitaires pour les connecteurs existants
def get_cached_or_fetch(source: str, method: str, fetch_func: Callable, *args, **kwargs) -> Any:
    """
    Fonction utilitaire: récupère depuis le cache ou exécute fetch_func

    Args:
        source: Source de données
        method: Nom de la méthode
        fetch_func: Fonction à exécuter si cache miss
        *args, **kwargs: Arguments pour fetch_func et génération clé cache

    Returns:
        Résultat de fetch_func ou données en cache
    """
    # Essayer cache d'abord
    cached_data = SecurityCache.get_cached_data(source, method, *args, **kwargs)

    if cached_data is not None:
        logger.info(f"[CACHE] Utilisation données cache pour {source}.{method}")
        return cached_data

    # Exécuter fetch_func
    logger.info(f"[CACHE] Cache miss pour {source}.{method}, exécution fetch")
    result = fetch_func(*args, **kwargs)

    # Stocker résultat si succès
    if result and isinstance(result, dict) and result.get('success', False):
        SecurityCache.set_cached_data(source, method, result, *args, **kwargs)

    return result


# Instance globale pour utilisation facile
security_cache = SecurityCache()