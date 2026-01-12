"""
Gestionnaire de Cache Avancé pour GEOPOL Analytics
Inspiré de pythonstock/stock
- Compression gzip pour économiser l'espace disque
- Fenêtre glissante (7 jours par défaut)
- Méthodes de nettoyage automatique
- Support multi-sources (INSEE, Eurostat, yFinance, etc.)
"""

import os
import json
import gzip
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
import hashlib

logger = logging.getLogger(__name__)

# Répertoire de cache
CACHE_DIR = Path(__file__).parent.parent / 'cache'
CACHE_DIR.mkdir(exist_ok=True)


class CacheManager:
    """
    Gestionnaire de cache avancé avec compression et expiration
    """

    def __init__(self, cache_dir: Optional[Path] = None, default_ttl_hours: int = 24):
        """
        Initialise le gestionnaire de cache

        Args:
            cache_dir: Répertoire de cache (par défaut: ./cache)
            default_ttl_hours: Durée de vie par défaut du cache en heures
        """
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = timedelta(hours=default_ttl_hours)

        logger.info(f"💾 CacheManager initialisé: {self.cache_dir}")

    def _get_cache_key(self, source: str, identifier: str) -> str:
        """
        Génère une clé de cache unique

        Args:
            source: Source des données (insee, eurostat, yfinance, etc.)
            identifier: Identifiant unique (symbol, indicateur, etc.)

        Returns:
            Clé de cache hashée
        """
        raw_key = f"{source}:{identifier}"
        hash_key = hashlib.md5(raw_key.encode()).hexdigest()
        return f"{source}_{hash_key}"

    def _get_cache_path(self, cache_key: str, compressed: bool = True) -> Path:
        """
        Retourne le chemin du fichier de cache

        Args:
            cache_key: Clé du cache
            compressed: Si True, utilise extension .json.gz, sinon .json

        Returns:
            Path du fichier cache
        """
        ext = '.json.gz' if compressed else '.json'
        return self.cache_dir / f"{cache_key}{ext}"

    def set(self, source: str, identifier: str, data: Any,
            ttl_hours: Optional[int] = None, compress: bool = True) -> bool:
        """
        Stocke des données dans le cache

        Args:
            source: Source des données
            identifier: Identifiant unique
            data: Données à cacher (dict, list, etc.)
            ttl_hours: Durée de vie en heures (None = default_ttl)
            compress: Si True, compresse avec gzip

        Returns:
            True si succès, False sinon
        """
        try:
            cache_key = self._get_cache_key(source, identifier)
            cache_path = self._get_cache_path(cache_key, compressed=compress)

            # Préparer les métadonnées
            ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
            cache_entry = {
                'data': data,
                'cached_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + ttl).isoformat(),
                'source': source,
                'identifier': identifier,
                'compressed': compress
            }

            # Sérialiser en JSON
            json_data = json.dumps(cache_entry, ensure_ascii=False, indent=2)

            # Écrire le fichier (compressé ou non)
            if compress:
                with gzip.open(cache_path, 'wt', encoding='utf-8') as f:
                    f.write(json_data)
                logger.debug(f"💾 Cache compressé: {cache_key}")
            else:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                logger.debug(f"💾 Cache non-compressé: {cache_key}")

            # Statistiques de compression
            if compress:
                original_size = len(json_data.encode('utf-8'))
                compressed_size = cache_path.stat().st_size
                ratio = (1 - compressed_size / original_size) * 100
                logger.debug(f"[DATA] Compression: {ratio:.1f}% ({original_size}→{compressed_size} bytes)")

            return True

        except Exception as e:
            logger.error(f"[ERROR] Erreur cache.set({source}, {identifier}): {e}")
            return False

    def get(self, source: str, identifier: str,
            ignore_expiration: bool = False) -> Optional[Dict[str, Any]]:
        """
        Récupère des données du cache

        Args:
            source: Source des données
            identifier: Identifiant unique
            ignore_expiration: Si True, retourne même si expiré

        Returns:
            Données cachées ou None si non trouvé/expiré
        """
        try:
            cache_key = self._get_cache_key(source, identifier)

            # Chercher fichier compressé puis non-compressé
            cache_path_gz = self._get_cache_path(cache_key, compressed=True)
            cache_path_json = self._get_cache_path(cache_key, compressed=False)

            cache_path = None
            is_compressed = False

            if cache_path_gz.exists():
                cache_path = cache_path_gz
                is_compressed = True
            elif cache_path_json.exists():
                cache_path = cache_path_json
                is_compressed = False

            if not cache_path:
                logger.debug(f"📭 Cache miss: {cache_key}")
                return None

            # Lire le fichier
            if is_compressed:
                with gzip.open(cache_path, 'rt', encoding='utf-8') as f:
                    cache_entry = json.load(f)
            else:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache_entry = json.load(f)

            # Vérifier expiration
            expires_at = datetime.fromisoformat(cache_entry['expires_at'])
            is_expired = datetime.now() > expires_at

            if is_expired and not ignore_expiration:
                logger.debug(f"[CLOCK] Cache expiré: {cache_key}")
                return None

            logger.debug(f"📦 Cache hit: {cache_key}")
            return cache_entry

        except Exception as e:
            logger.error(f"[ERROR] Erreur cache.get({source}, {identifier}): {e}")
            return None

    def delete(self, source: str, identifier: str) -> bool:
        """
        Supprime une entrée du cache

        Args:
            source: Source des données
            identifier: Identifiant unique

        Returns:
            True si supprimé, False sinon
        """
        try:
            cache_key = self._get_cache_key(source, identifier)

            # Supprimer les deux versions possibles
            deleted = False
            for compressed in [True, False]:
                cache_path = self._get_cache_path(cache_key, compressed=compressed)
                if cache_path.exists():
                    cache_path.unlink()
                    deleted = True
                    logger.debug(f"🗑 Cache supprimé: {cache_key}")

            return deleted

        except Exception as e:
            logger.error(f"[ERROR] Erreur cache.delete({source}, {identifier}): {e}")
            return False

    def clear_source(self, source: str) -> int:
        """
        Supprime tous les caches d'une source donnée

        Args:
            source: Source à nettoyer (insee, eurostat, etc.)

        Returns:
            Nombre de fichiers supprimés
        """
        try:
            pattern = f"{source}_*.json*"
            deleted_count = 0

            for cache_file in self.cache_dir.glob(pattern):
                cache_file.unlink()
                deleted_count += 1

            logger.info(f"🗑 Cache source '{source}' nettoyé: {deleted_count} fichiers")
            return deleted_count

        except Exception as e:
            logger.error(f"[ERROR] Erreur cache.clear_source({source}): {e}")
            return 0

    def cleanup_expired(self) -> int:
        """
        Supprime tous les fichiers de cache expirés

        Returns:
            Nombre de fichiers supprimés
        """
        try:
            deleted_count = 0
            now = datetime.now()

            for cache_file in self.cache_dir.glob("*.json*"):
                try:
                    # Lire le fichier pour vérifier expiration
                    is_compressed = cache_file.suffix == '.gz'

                    if is_compressed:
                        with gzip.open(cache_file, 'rt', encoding='utf-8') as f:
                            cache_entry = json.load(f)
                    else:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            cache_entry = json.load(f)

                    expires_at = datetime.fromisoformat(cache_entry['expires_at'])

                    if now > expires_at:
                        cache_file.unlink()
                        deleted_count += 1

                except Exception as e:
                    logger.warning(f"[WARN] Fichier cache invalide: {cache_file.name} - {e}")
                    # Supprimer fichiers invalides
                    cache_file.unlink()
                    deleted_count += 1

            logger.info(f"🧹 Nettoyage cache: {deleted_count} fichiers expirés supprimés")
            return deleted_count

        except Exception as e:
            logger.error(f"[ERROR] Erreur cache.cleanup_expired(): {e}")
            return 0

    def cleanup_old(self, days: int = 7) -> int:
        """
        Supprime les fichiers de cache plus anciens que N jours (fenêtre glissante)

        Args:
            days: Nombre de jours à conserver (défaut 7)

        Returns:
            Nombre de fichiers supprimés
        """
        try:
            deleted_count = 0
            cutoff_date = datetime.now() - timedelta(days=days)

            for cache_file in self.cache_dir.glob("*.json*"):
                try:
                    # Vérifier date de création du fichier
                    file_mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)

                    if file_mtime < cutoff_date:
                        cache_file.unlink()
                        deleted_count += 1

                except Exception as e:
                    logger.warning(f"[WARN] Erreur fichier cache: {cache_file.name} - {e}")

            logger.info(f"🧹 Nettoyage fenêtre glissante: {deleted_count} fichiers >{ days}j supprimés")
            return deleted_count

        except Exception as e:
            logger.error(f"[ERROR] Erreur cache.cleanup_old({days}): {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache

        Returns:
            Dictionnaire avec les stats
        """
        try:
            total_files = 0
            total_size = 0
            compressed_count = 0
            by_source = {}

            for cache_file in self.cache_dir.glob("*.json*"):
                total_files += 1
                total_size += cache_file.stat().st_size

                if cache_file.suffix == '.gz':
                    compressed_count += 1

                # Extraire source depuis le nom de fichier
                source = cache_file.stem.split('_')[0]
                by_source[source] = by_source.get(source, 0) + 1

            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'compressed_files': compressed_count,
                'uncompressed_files': total_files - compressed_count,
                'by_source': by_source,
                'cache_dir': str(self.cache_dir)
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur cache.get_stats(): {e}")
            return {}


# Instance globale du gestionnaire de cache
cache_manager = CacheManager()
