"""
Service de base pour le module economique
Fournit cache intelligent, retry logic et logging
"""
import logging
import time
from typing import Any, Callable, Dict, Optional
from datetime import datetime

from ..config import EconomicConfig
from ..utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)

class BaseEconomicService:
    """Service de base avec cache intelligent et retry logic"""

    def __init__(self, db_manager):
        """
        Initialise le service de base

        Args:
            db_manager: Instance du DatabaseManager
        """
        self.db_manager = db_manager
        self.cache_manager = CacheManager(db_manager)
        self.config = EconomicConfig

    def fetch_with_cache(
        self,
        cache_key: str,
        fetch_func: Callable,
        data_source: str,
        data_type: str,
        expiry_hours: Optional[int] = None,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Recupere des donnees avec gestion intelligente du cache

        Args:
            cache_key: Cle unique du cache
            fetch_func: Fonction de recuperation des donnees
            data_source: Source des donnees (yfinance, eurostat, etc.)
            data_type: Type de donnees (index, commodity, etc.)
            expiry_hours: Duree de validite (heures)
            force_refresh: Forcer rafraichissement

        Returns:
            Dictionnaire avec donnees ou None
            Format: {
                'value': ...,
                'change_percent': ...,
                'currency': ...,
                'source': ...,
                'fresh': True/False,
                'last_updated': ...,
                'cached_at': ...
            }
        """
        # Determiner duree de cache
        if expiry_hours is None:
            expiry_hours = self.config.get_cache_duration(data_source)

        # Tenter cache d'abord (si pas force_refresh)
        if not force_refresh:
            cached = self.cache_manager.get_cached_data(
                cache_key,
                max_age_hours=expiry_hours,
                allow_stale=self.config.USE_STALE_CACHE_ON_ERROR
            )

            if cached and cached['is_fresh']:
                # Donnees fraiche trouvees
                result = cached['data']
                result['fresh'] = True
                result['cached_at'] = cached['cached_at']
                result['source'] = data_source
                self._log_activity('cache_hit', data_source, 'success',
                                  f"Cache hit (fresh) - {cache_key}")
                return result

        # Tenter de recuperer depuis l'API
        try:
            logger.info(f"[{data_source.upper()}] Fetching fresh data: {cache_key}")
            data = self._fetch_with_retry(fetch_func)

            if data:
                # Stocker dans le cache
                self.cache_manager.set_cached_data(
                    cache_key,
                    data,
                    data_source,
                    data_type,
                    expiry_hours
                )

                # Enrichir les donnees
                data['fresh'] = True
                data['last_updated'] = datetime.now().isoformat()
                data['source'] = data_source

                self._log_activity('data_fetch', data_source, 'success',
                                  f"Fresh data fetched - {cache_key}")
                return data

        except Exception as e:
            logger.error(f"[{data_source.upper()}] Erreur fetch {cache_key}: {e}")
            self._log_activity('data_fetch', data_source, 'error', str(e))

        # Fallback sur cache expire si autorise
        if self.config.USE_STALE_CACHE_ON_ERROR:
            cached = self.cache_manager.get_cached_data(
                cache_key,
                max_age_hours=self.config.MAX_STALE_CACHE_DAYS * 24,
                allow_stale=True
            )

            if cached:
                logger.warning(f"[{data_source.upper()}] Using stale cache - {cache_key}")
                result = cached['data']
                result['fresh'] = False
                result['cached_at'] = cached['cached_at']
                result['source'] = data_source
                self._log_activity('cache_fallback', data_source, 'warning',
                                  f"Using stale cache - {cache_key}")
                return result

        # Aucune donnee disponible
        self._log_activity('data_fetch', data_source, 'error',
                          f"No data available - {cache_key}")
        return None

    def _fetch_with_retry(
        self,
        fetch_func: Callable,
        max_attempts: Optional[int] = None
    ) -> Any:
        """
        Execute une fonction avec retry logic

        Args:
            fetch_func: Fonction a executer
            max_attempts: Nombre max de tentatives

        Returns:
            Resultat de la fonction

        Raises:
            Exception si toutes les tentatives echouent
        """
        if max_attempts is None:
            max_attempts = self.config.API_RETRY_ATTEMPTS

        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                result = fetch_func()
                if result:
                    return result
            except Exception as e:
                last_error = e
                if attempt < max_attempts:
                    # Backoff exponentiel
                    sleep_time = self.config.API_RETRY_BACKOFF ** attempt
                    logger.warning(f"[RETRY] Attempt {attempt}/{max_attempts} failed. "
                                 f"Retrying in {sleep_time}s... Error: {e}")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"[RETRY] All {max_attempts} attempts failed.")

        raise last_error if last_error else Exception("Fetch failed")

    def _log_activity(
        self,
        activity_type: str,
        data_source: str,
        status: str,
        message: str,
        metadata: Optional[Dict] = None
    ):
        """
        Enregistre une activite dans les logs

        Args:
            activity_type: Type d'activite (data_fetch, cache_hit, etc.)
            data_source: Source concernee
            status: Statut (success, error, warning)
            message: Message descriptif
            metadata: Metadonnees additionnelles
        """
        try:
            import json

            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO economic_activity_logs (
                    activity_type, data_source, status, message, metadata, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                activity_type,
                data_source,
                status,
                message,
                json.dumps(metadata or {}),
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"[LOG] Erreur enregistrement log: {e}")

    def get_recent_logs(self, limit: int = 100) -> list:
        """Recupere les logs recents"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT activity_type, data_source, status, message, created_at
                FROM economic_activity_logs
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'activity_type': row[0],
                    'data_source': row[1],
                    'status': row[2],
                    'message': row[3],
                    'created_at': row[4]
                })

            conn.close()
            return logs

        except Exception as e:
            logger.error(f"[LOG] Erreur recuperation logs: {e}")
            return []

    def invalidate_cache(self, cache_key: str) -> bool:
        """Invalide une entree de cache"""
        return self.cache_manager.invalidate_cache(cache_key)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        return self.cache_manager.get_cache_stats()
