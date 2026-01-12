"""
Système de monitoring des métriques de cache pour les connecteurs sécurité & gouvernance
Collecte et affiche les statistiques d'utilisation du cache intelligent

Usage:
    from cache_monitoring import CacheMonitor

    monitor = CacheMonitor()
    stats = monitor.get_cache_statistics()
    print(monitor.generate_report())
"""
import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

# Import du cache manager
try:
    import sys
    flask_dir = os.path.join(os.path.dirname(__file__), '..')
    if flask_dir not in sys.path:
        sys.path.insert(0, flask_dir)

    from cache_manager import cache_manager
    CACHE_AVAILABLE = True
except ImportError as e:
    CACHE_AVAILABLE = False
    cache_manager = None
    logger.error(f"CacheManager non disponible: {e}")


class CacheMonitor:
    """
    Moniteur de métriques de cache
    Collecte et analyse les statistiques d'utilisation du cache
    """

    def __init__(self):
        """Initialise le moniteur de cache"""
        self.cache_manager = cache_manager if CACHE_AVAILABLE else None

    def is_available(self) -> bool:
        """Vérifie si le monitoring est disponible"""
        return CACHE_AVAILABLE and self.cache_manager is not None

    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Récupère les statistiques globales du cache

        Returns:
            Dict avec statistiques complètes
        """
        if not self.is_available():
            return {
                'available': False,
                'error': 'Cache manager non disponible'
            }

        try:
            cache_dir = self.cache_manager.cache_dir

            # Compter les fichiers de cache
            total_files = 0
            total_size = 0
            sources = {}

            if os.path.exists(cache_dir):
                for source_name in os.listdir(cache_dir):
                    source_path = os.path.join(cache_dir, source_name)
                    if os.path.isdir(source_path):
                        files = [f for f in os.listdir(source_path) if f.endswith('.cache')]
                        file_count = len(files)

                        # Calculer taille
                        source_size = 0
                        for file in files:
                            file_path = os.path.join(source_path, file)
                            if os.path.exists(file_path):
                                source_size += os.path.getsize(file_path)

                        sources[source_name] = {
                            'files': file_count,
                            'size_bytes': source_size,
                            'size_mb': round(source_size / (1024 * 1024), 2)
                        }

                        total_files += file_count
                        total_size += source_size

            return {
                'available': True,
                'timestamp': datetime.now().isoformat(),
                'cache_directory': cache_dir,
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'total_size_gb': round(total_size / (1024 * 1024 * 1024), 3),
                'sources': sources,
                'source_count': len(sources)
            }

        except Exception as e:
            logger.error(f"Erreur récupération statistiques cache: {e}")
            return {
                'available': False,
                'error': str(e)
            }

    def get_source_details(self, source: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une source spécifique

        Args:
            source: Nom de la source (ex: 'ucdp', 'transparency_cpi')

        Returns:
            Dict avec détails de la source
        """
        if not self.is_available():
            return {
                'available': False,
                'error': 'Cache manager non disponible'
            }

        try:
            source_path = os.path.join(self.cache_manager.cache_dir, source)

            if not os.path.exists(source_path):
                return {
                    'available': True,
                    'source': source,
                    'exists': False,
                    'files': []
                }

            files_info = []
            for file in os.listdir(source_path):
                if file.endswith('.cache'):
                    file_path = os.path.join(source_path, file)

                    # Informations fichier
                    file_size = os.path.getsize(file_path)
                    file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))

                    # Essayer de charger métadonnées
                    metadata = None
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            cached_data = json.load(f)
                            metadata = {
                                'expires_at': cached_data.get('expires_at'),
                                'created_at': cached_data.get('created_at'),
                                'data_size': len(str(cached_data.get('data', {}))),
                                'compressed': cached_data.get('metadata', {}).get('compressed', False)
                            }
                    except:
                        pass

                    files_info.append({
                        'filename': file,
                        'size_bytes': file_size,
                        'size_kb': round(file_size / 1024, 2),
                        'modified': file_modified.isoformat(),
                        'metadata': metadata
                    })

            # Trier par date de modification (plus récent d'abord)
            files_info.sort(key=lambda x: x['modified'], reverse=True)

            total_size = sum(f['size_bytes'] for f in files_info)

            return {
                'available': True,
                'source': source,
                'exists': True,
                'path': source_path,
                'total_files': len(files_info),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'files': files_info
            }

        except Exception as e:
            logger.error(f"Erreur récupération détails source {source}: {e}")
            return {
                'available': False,
                'error': str(e)
            }

    def calculate_hit_rate(self, source: Optional[str] = None) -> Dict[str, Any]:
        """
        Calcule le taux de hit du cache (estimé)

        Args:
            source: Source spécifique (None pour global)

        Returns:
            Dict avec taux de hit estimé
        """
        # Note: Pour un vrai taux de hit, il faudrait logger les accès
        # Cette version estime basée sur la fréquence d'utilisation

        if not self.is_available():
            return {
                'available': False,
                'error': 'Cache manager non disponible'
            }

        return {
            'available': True,
            'note': 'Taux de hit estimé - nécessite instrumentation complète',
            'estimated_hit_rate': 'N/A',
            'recommendation': 'Implémenter logging des accès cache pour métriques précises'
        }

    def get_cache_health(self) -> Dict[str, Any]:
        """
        Évalue la santé du cache

        Returns:
            Dict avec indicateurs de santé
        """
        if not self.is_available():
            return {
                'healthy': False,
                'status': 'unavailable',
                'error': 'Cache manager non disponible'
            }

        try:
            stats = self.get_cache_statistics()

            if not stats.get('available'):
                return {
                    'healthy': False,
                    'status': 'error',
                    'error': stats.get('error')
                }

            # Critères de santé
            total_size_mb = stats['total_size_mb']
            total_files = stats['total_files']

            warnings = []
            errors = []

            # Vérifier taille (warning si > 500MB, erreur si > 1GB)
            if total_size_mb > 1000:
                errors.append(f"Taille cache excessive: {total_size_mb}MB (max recommandé: 1GB)")
            elif total_size_mb > 500:
                warnings.append(f"Taille cache élevée: {total_size_mb}MB (recommandé: <500MB)")

            # Vérifier nombre de fichiers (warning si > 1000)
            if total_files > 1000:
                warnings.append(f"Nombre élevé de fichiers cache: {total_files} (recommandé: <1000)")

            # Déterminer statut
            if errors:
                status = 'critical'
                healthy = False
            elif warnings:
                status = 'warning'
                healthy = True
            else:
                status = 'healthy'
                healthy = True

            return {
                'healthy': healthy,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'metrics': {
                    'total_size_mb': total_size_mb,
                    'total_files': total_files,
                    'source_count': stats['source_count']
                },
                'warnings': warnings,
                'errors': errors,
                'recommendations': self._get_recommendations(stats, warnings, errors)
            }

        except Exception as e:
            logger.error(f"Erreur évaluation santé cache: {e}")
            return {
                'healthy': False,
                'status': 'error',
                'error': str(e)
            }

    def _get_recommendations(self, stats: Dict, warnings: List[str], errors: List[str]) -> List[str]:
        """Génère des recommandations basées sur les statistiques"""
        recommendations = []

        if errors:
            recommendations.append("🚨 Action immédiate requise: Purger le cache ou augmenter les limites")

        if warnings:
            recommendations.append("⚠️ Surveillance recommandée: Vérifier stratégies TTL")

        if stats['total_files'] == 0:
            recommendations.append("ℹ️ Cache vide: Normal au démarrage, sera rempli avec l'utilisation")

        if stats['source_count'] < 3:
            recommendations.append("ℹ️ Peu de sources utilisent le cache: Intégrer plus de connecteurs")

        return recommendations

    def generate_report(self, include_details: bool = False) -> str:
        """
        Génère un rapport textuel du cache

        Args:
            include_details: Inclure détails par source

        Returns:
            Rapport formaté en texte
        """
        if not self.is_available():
            return "❌ Monitoring du cache non disponible (CacheManager introuvable)\n"

        report = []
        report.append("=" * 80)
        report.append("RAPPORT DE MONITORING DU CACHE".center(80))
        report.append("=" * 80)
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Statistiques globales
        stats = self.get_cache_statistics()
        if stats.get('available'):
            report.append("📊 STATISTIQUES GLOBALES")
            report.append("-" * 80)
            report.append(f"  Répertoire cache: {stats['cache_directory']}")
            report.append(f"  Nombre de fichiers: {stats['total_files']}")
            report.append(f"  Taille totale: {stats['total_size_mb']} MB ({stats['total_size_gb']} GB)")
            report.append(f"  Sources actives: {stats['source_count']}")
            report.append("")

        # Santé du cache
        health = self.get_cache_health()
        status_emoji = "✅" if health['status'] == 'healthy' else "⚠️" if health['status'] == 'warning' else "❌"
        report.append(f"🏥 SANTÉ DU CACHE: {status_emoji} {health['status'].upper()}")
        report.append("-" * 80)

        if health.get('warnings'):
            report.append("  Avertissements:")
            for warning in health['warnings']:
                report.append(f"    ⚠️ {warning}")

        if health.get('errors'):
            report.append("  Erreurs:")
            for error in health['errors']:
                report.append(f"    ❌ {error}")

        if health.get('recommendations'):
            report.append("  Recommandations:")
            for rec in health['recommendations']:
                report.append(f"    {rec}")

        report.append("")

        # Détails par source
        if include_details and stats.get('available') and stats.get('sources'):
            report.append("📁 DÉTAILS PAR SOURCE")
            report.append("-" * 80)
            for source_name, source_stats in stats['sources'].items():
                report.append(f"  {source_name}:")
                report.append(f"    Fichiers: {source_stats['files']}")
                report.append(f"    Taille: {source_stats['size_mb']} MB")
                report.append("")

        report.append("=" * 80)

        return "\n".join(report)

    def clear_expired_cache(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Nettoie les entrées de cache expirées

        Args:
            dry_run: Si True, simule sans supprimer

        Returns:
            Résumé du nettoyage
        """
        if not self.is_available():
            return {
                'success': False,
                'error': 'Cache manager non disponible'
            }

        try:
            deleted_count = 0
            deleted_size = 0
            sources_cleaned = []

            cache_dir = self.cache_manager.cache_dir
            if not os.path.exists(cache_dir):
                return {
                    'success': True,
                    'deleted_count': 0,
                    'deleted_size_mb': 0,
                    'sources_cleaned': [],
                    'dry_run': dry_run
                }

            for source_name in os.listdir(cache_dir):
                source_path = os.path.join(cache_dir, source_name)
                if not os.path.isdir(source_path):
                    continue

                source_deleted = 0
                for file in os.listdir(source_path):
                    if not file.endswith('.cache'):
                        continue

                    file_path = os.path.join(source_path, file)

                    try:
                        # Charger et vérifier expiration
                        with open(file_path, 'r', encoding='utf-8') as f:
                            cached_data = json.load(f)

                        expires_at = datetime.fromisoformat(cached_data['expires_at'])
                        if expires_at < datetime.now():
                            # Expiré
                            file_size = os.path.getsize(file_path)
                            deleted_size += file_size
                            deleted_count += 1
                            source_deleted += 1

                            if not dry_run:
                                os.remove(file_path)
                                logger.info(f"Cache expiré supprimé: {file_path}")

                    except Exception as e:
                        logger.warning(f"Erreur vérification {file_path}: {e}")
                        continue

                if source_deleted > 0:
                    sources_cleaned.append({
                        'source': source_name,
                        'deleted': source_deleted
                    })

            return {
                'success': True,
                'deleted_count': deleted_count,
                'deleted_size_bytes': deleted_size,
                'deleted_size_mb': round(deleted_size / (1024 * 1024), 2),
                'sources_cleaned': sources_cleaned,
                'dry_run': dry_run,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Erreur nettoyage cache: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def get_cache_monitor() -> CacheMonitor:
    """Factory pour obtenir le moniteur de cache"""
    return CacheMonitor()


__all__ = ['CacheMonitor', 'get_cache_monitor']
