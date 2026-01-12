"""
Gestionnaire de cache intelligent pour le module economique
Gestion cache SQLite avec expiration et fallback automatique
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import hashlib

logger = logging.getLogger(__name__)

class CacheManager:
    """Gestionnaire de cache intelligent avec expiration et fallback"""

    def __init__(self, db_manager):
        """
        Initialise le gestionnaire de cache

        Args:
            db_manager: Instance du DatabaseManager
        """
        self.db_manager = db_manager

    def get_cached_data(
        self,
        cache_key: str,
        max_age_hours: Optional[int] = None,
        allow_stale: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Recupere des donnees du cache

        Args:
            cache_key: Cle unique du cache
            max_age_hours: Age maximum acceptable (heures)
            allow_stale: Autoriser donnees expirees en fallback

        Returns:
            Dictionnaire avec les donnees ou None
            Format: {
                'data': {...},
                'is_fresh': True/False,
                'cached_at': timestamp,
                'source': 'yfinance',
                'metadata': {...}
            }
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Tenter de recuperer donnees valides
            cursor.execute("""
                SELECT data_value, data_source, is_fresh, timestamp, metadata, expiry_datetime
                FROM economic_cache
                WHERE cache_key = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (cache_key,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                logger.debug(f"[CACHE] Aucune donnee trouvee pour cle: {cache_key}")
                return None

            data_value, data_source, is_fresh, timestamp, metadata, expiry_datetime = row

            # Parser les donnees JSON
            try:
                data = json.loads(data_value)
                meta = json.loads(metadata) if metadata else {}
            except json.JSONDecodeError as e:
                logger.error(f"[CACHE] Erreur decodage JSON pour {cache_key}: {e}")
                return None

            # Verifier expiration
            expiry = datetime.fromisoformat(expiry_datetime)
            now = datetime.now()
            is_expired = now > expiry

            if not is_expired:
                # Donnees valides
                logger.info(f"[CACHE] HIT (fresh) - {cache_key}")
                return {
                    'data': data,
                    'is_fresh': True,
                    'cached_at': timestamp,
                    'source': data_source,
                    'metadata': meta
                }

            # Donnees expirees - verifier si fallback autorise
            if allow_stale:
                # Verifier age maximum
                cached_at = datetime.fromisoformat(timestamp)
                age_days = (now - cached_at).days

                max_days = 7  # Par defaut 7 jours
                if max_age_hours:
                    max_days = max_age_hours / 24

                if age_days <= max_days:
                    logger.warning(f"[CACHE] HIT (stale) - {cache_key} (age: {age_days} jours)")
                    return {
                        'data': data,
                        'is_fresh': False,
                        'cached_at': timestamp,
                        'source': data_source,
                        'metadata': meta
                    }

            logger.debug(f"[CACHE] MISS (expired) - {cache_key}")
            return None

        except Exception as e:
            logger.error(f"[CACHE] Erreur recuperation cache {cache_key}: {e}")
            return None

    def set_cached_data(
        self,
        cache_key: str,
        data: Any,
        data_source: str,
        data_type: str,
        expiry_hours: int = 12,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Stocke des donnees dans le cache

        Args:
            cache_key: Cle unique du cache
            data: Donnees a cacher (dict ou serialisable JSON)
            data_source: Source des donnees (yfinance, eurostat, etc.)
            data_type: Type de donnees (index, commodity, crypto, etc.)
            expiry_hours: Duree de validite en heures
            metadata: Metadonnees supplementaires

        Returns:
            True si succes, False sinon
        """
        try:
            # Serialiser les donnees
            data_value = json.dumps(data, ensure_ascii=False)
            metadata_value = json.dumps(metadata or {}, ensure_ascii=False)

            # Calculer expiration
            now = datetime.now()
            expiry = now + timedelta(hours=expiry_hours)

            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Inserer ou mettre a jour
            cursor.execute("""
                INSERT INTO economic_cache (
                    cache_key, data_source, data_type, data_value, metadata,
                    timestamp, expiry_datetime, is_fresh, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    data_value = excluded.data_value,
                    data_source = excluded.data_source,
                    data_type = excluded.data_type,
                    metadata = excluded.metadata,
                    timestamp = excluded.timestamp,
                    expiry_datetime = excluded.expiry_datetime,
                    is_fresh = 1,
                    updated_at = excluded.updated_at
            """, (
                cache_key, data_source, data_type, data_value, metadata_value,
                now.isoformat(), expiry.isoformat(), now.isoformat(), now.isoformat()
            ))

            conn.commit()
            conn.close()

            logger.info(f"[CACHE] SET - {cache_key} (expiry: {expiry_hours}h)")
            return True

        except Exception as e:
            logger.error(f"[CACHE] Erreur stockage cache {cache_key}: {e}")
            return False

    def invalidate_cache(self, cache_key: str) -> bool:
        """Invalide une entree de cache"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM economic_cache WHERE cache_key = ?", (cache_key,))
            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()

            if deleted:
                logger.info(f"[CACHE] INVALIDATE - {cache_key}")
            return deleted

        except Exception as e:
            logger.error(f"[CACHE] Erreur invalidation cache {cache_key}: {e}")
            return False

    def cleanup_old_cache(self, days: int = 30) -> int:
        """
        Nettoie les entrees de cache anciennes

        Args:
            days: Supprimer entrees plus vieilles que X jours

        Returns:
            Nombre d'entrees supprimees
        """
        try:
            cutoff = datetime.now() - timedelta(days=days)

            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM economic_cache
                WHERE created_at < ?
            """, (cutoff.isoformat(),))

            conn.commit()
            deleted = cursor.rowcount
            conn.close()

            logger.info(f"[CACHE] CLEANUP - {deleted} entrees supprimees (>{days} jours)")
            return deleted

        except Exception as e:
            logger.error(f"[CACHE] Erreur cleanup cache: {e}")
            return 0

    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur le cache"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Total entrees
            cursor.execute("SELECT COUNT(*) FROM economic_cache")
            total = cursor.fetchone()[0]

            # Entrees fraiches
            cursor.execute("SELECT COUNT(*) FROM economic_cache WHERE expiry_datetime > ?",
                          (datetime.now().isoformat(),))
            fresh = cursor.fetchone()[0]

            # Par source
            cursor.execute("""
                SELECT data_source, COUNT(*) as count
                FROM economic_cache
                GROUP BY data_source
            """)
            by_source = dict(cursor.fetchall())

            # Par type
            cursor.execute("""
                SELECT data_type, COUNT(*) as count
                FROM economic_cache
                GROUP BY data_type
            """)
            by_type = dict(cursor.fetchall())

            conn.close()

            return {
                'total_entries': total,
                'fresh_entries': fresh,
                'stale_entries': total - fresh,
                'by_source': by_source,
                'by_type': by_type
            }

        except Exception as e:
            logger.error(f"[CACHE] Erreur stats cache: {e}")
            return {}

    @staticmethod
    def generate_cache_key(prefix: str, *args) -> str:
        """
        Genere une cle de cache unique

        Args:
            prefix: Prefixe (ex: 'yfinance', 'eurostat')
            *args: Arguments additionnels pour unicite

        Returns:
            Cle de cache unique
        """
        components = [prefix] + [str(arg) for arg in args]
        key = '_'.join(components)
        return key
