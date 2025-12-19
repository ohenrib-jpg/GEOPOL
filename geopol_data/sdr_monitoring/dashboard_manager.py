"""
Gestionnaire du dashboard SDR temps réel.

Fonctionnalités :
- Métriques globales (stations actives, taux de disponibilité)
- Métriques par zone géopolitique
- Timeline d'évolution
- Alertes récentes
- Données pour graphiques

Version: 1.0.0
Author: GEOPOL Analytics
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class DashboardMetrics:
    """Métriques du dashboard."""

    # Métriques globales
    total_active: int = 0
    total_inactive: int = 0
    total_stations: int = 0
    availability_rate: float = 0.0

    # Métriques par zone
    zones: Dict[str, Dict] = field(default_factory=dict)

    # Alertes récentes
    recent_anomalies: List[Dict] = field(default_factory=list)

    # Timeline
    timeline_data: List[Dict] = field(default_factory=list)

    # Timestamp
    last_update: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            'global': {
                'total_active': self.total_active,
                'total_inactive': self.total_inactive,
                'total_stations': self.total_stations,
                'availability_rate': self.availability_rate
            },
            'zones': self.zones,
            'recent_anomalies': self.recent_anomalies,
            'timeline': self.timeline_data,
            'last_update': self.last_update
        }


class DashboardManager:
    """
    Gestionnaire du dashboard SDR temps réel.

    Fournit les métriques et données nécessaires pour le dashboard :
    - Statut global du réseau SDR
    - Métriques par zone géopolitique
    - Timeline d'évolution 24h
    - Alertes récentes
    """

    def __init__(self, db_manager, sdr_analyzer=None):
        """
        Initialise le gestionnaire de dashboard.

        Args:
            db_manager: Gestionnaire de base de données
            sdr_analyzer: Instance de SDRAnalyzer (optionnel)
        """
        self.db_manager = db_manager
        self.sdr_analyzer = sdr_analyzer

        # Définition des zones géopolitiques
        self.zones = {
            'NATO': {
                'name': 'OTAN',
                'countries': ['US', 'GB', 'FR', 'DE', 'IT', 'ES', 'CA', 'TR']
            },
            'BRICS': {
                'name': 'BRICS+',
                'countries': ['BR', 'RU', 'IN', 'CN', 'ZA']
            },
            'MIDDLE_EAST': {
                'name': 'Moyen-Orient',
                'countries': ['SA', 'IR', 'IQ', 'SY', 'YE', 'AE']
            },
            'ASIA_PACIFIC': {
                'name': 'Asie-Pacifique',
                'countries': ['JP', 'KR', 'AU', 'NZ', 'TH', 'VN']
            }
        }

        logger.info("📊 DashboardManager initialisé")

    def get_dashboard_summary(self) -> DashboardMetrics:
        """
        Récupère le résumé complet du dashboard.

        Returns:
            DashboardMetrics avec toutes les métriques
        """
        logger.info("📊 Génération résumé dashboard...")

        metrics = DashboardMetrics()

        # Récupérer les métriques globales
        global_metrics = self._get_global_metrics()
        metrics.total_active = global_metrics['total_active']
        metrics.total_inactive = global_metrics['total_inactive']
        metrics.total_stations = global_metrics['total_stations']
        metrics.availability_rate = global_metrics['availability_rate']

        # Récupérer les métriques par zone
        metrics.zones = self._get_zone_metrics()

        # Récupérer les alertes récentes
        metrics.recent_anomalies = self._get_recent_anomalies(limit=10)

        # Timestamp
        metrics.last_update = datetime.utcnow().isoformat()

        logger.info(f"✅ Dashboard généré : {metrics.total_active}/{metrics.total_stations} actives")

        return metrics

    def _get_global_metrics(self) -> Dict[str, Any]:
        """
        Récupère les métriques globales.

        Returns:
            Métriques globales
        """
        try:
            # Récupérer les stations depuis le scraper
            from ..connectors.sdr_scrapers import SDRScrapers
            scraper = SDRScrapers()
            stations = scraper.get_stations_as_dict(force_refresh=False)

            # Compter les actives et inactives
            total_stations = len(stations)
            total_active = sum(1 for s in stations if s.get('status') == 'ACTIVE')
            total_inactive = total_stations - total_active

            # Calculer le taux de disponibilité
            availability_rate = (total_active / total_stations * 100) if total_stations > 0 else 0.0

            return {
                'total_active': total_active,
                'total_inactive': total_inactive,
                'total_stations': total_stations,
                'availability_rate': round(availability_rate, 1)
            }

        except Exception as e:
            logger.error(f"❌ Erreur récupération métriques globales: {e}")
            return {
                'total_active': 0,
                'total_inactive': 0,
                'total_stations': 0,
                'availability_rate': 0.0
            }

    def _get_zone_metrics(self) -> Dict[str, Dict]:
        """
        Récupère les métriques par zone géopolitique.

        Returns:
            Métriques par zone {zone_id: {name, active, inactive, rate, status}}
        """
        zone_metrics = {}

        try:
            # Si SDRAnalyzer disponible, utiliser ses métriques
            if self.sdr_analyzer:
                # Traiter les données SDR avec l'analyzer
                scan_data = []  # TODO: Récupérer vraies données
                processed = self.sdr_analyzer.process_scan_data(scan_data, detect_anomalies=True)

                for zone_id, zone_data in processed.get('zones', {}).items():
                    zone_info = self.zones.get(zone_id, {})

                    # Extraire les métriques
                    metrics = zone_data.get('metrics', {})
                    num_stations = metrics.get('num_active_stations', 0)
                    activity = metrics.get('total_activity', 0.0)
                    health = metrics.get('communication_health', 0.0)

                    zone_metrics[zone_id] = {
                        'name': zone_info.get('name', zone_id),
                        'active': num_stations,
                        'inactive': 0,  # TODO: Calculer inactives
                        'total': num_stations,
                        'availability_rate': round(activity * 100, 1),
                        'health': round(health, 1),
                        'status': zone_data.get('status', 'UNKNOWN'),
                        'anomaly_count': zone_data.get('anomaly_count', 0),
                        'critical_anomalies': zone_data.get('critical_anomalies', 0)
                    }
            else:
                # Mode simulation
                for zone_id, zone_info in self.zones.items():
                    zone_metrics[zone_id] = {
                        'name': zone_info['name'],
                        'active': 0,
                        'inactive': 0,
                        'total': 0,
                        'availability_rate': 0.0,
                        'health': 0.0,
                        'status': 'UNKNOWN',
                        'anomaly_count': 0,
                        'critical_anomalies': 0
                    }

        except Exception as e:
            logger.error(f"❌ Erreur récupération métriques zones: {e}")

        return zone_metrics

    def _get_recent_anomalies(self, limit: int = 10) -> List[Dict]:
        """
        Récupère les anomalies récentes.

        Args:
            limit: Nombre maximum d'anomalies à retourner

        Returns:
            Liste des anomalies récentes
        """
        try:
            # Requête pour récupérer les anomalies récentes depuis la BDD
            query = """
                SELECT
                    zone_id,
                    metric_name,
                    current_value,
                    baseline_value,
                    sigma_deviation,
                    level,
                    description,
                    timestamp
                FROM sdr_anomalies
                WHERE timestamp >= datetime('now', '-24 hours')
                ORDER BY timestamp DESC
                LIMIT ?
            """

            result = self.db_manager.execute_query(query, (limit,))

            if not result:
                logger.info("ℹ️ Pas d'anomalies récentes")
                return []

            # Convertir en liste de dicts
            anomalies = []
            for row in result:
                anomalies.append({
                    'zone_id': row[0],
                    'metric_name': row[1],
                    'current_value': row[2],
                    'baseline_value': row[3],
                    'sigma_deviation': row[4],
                    'level': row[5],
                    'description': row[6],
                    'timestamp': row[7]
                })

            return anomalies

        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération anomalies (normal si table inexistante): {e}")
            return []

    def get_timeline_data(self, hours: int = 24, interval_minutes: int = 30) -> List[Dict]:
        """
        Récupère les données de timeline pour graphiques.

        Args:
            hours: Nombre d'heures d'historique
            interval_minutes: Intervalle entre points (minutes)

        Returns:
            Timeline [{timestamp, active_stations, availability_rate, anomaly_count}, ...]
        """
        try:
            # Requête pour récupérer l'historique
            query = """
                SELECT
                    timestamp,
                    SUM(num_active_stations) as total_active,
                    AVG(communication_health) as avg_health,
                    COUNT(*) as num_zones
                FROM sdr_health_metrics
                WHERE timestamp >= datetime('now', ? || ' hours')
                GROUP BY strftime('%Y-%m-%d %H:%M', timestamp)
                ORDER BY timestamp ASC
            """

            result = self.db_manager.execute_query(query, (f'-{hours}',))

            if not result:
                logger.info(f"ℹ️ Pas de données historiques ({hours}h)")
                return []

            # Convertir en timeline
            timeline = []
            for row in result:
                timeline.append({
                    'timestamp': row[0],
                    'active_stations': row[1] or 0,
                    'avg_health': round(row[2] or 0, 1),
                    'num_zones': row[3] or 0
                })

            return timeline

        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération timeline: {e}")
            return []

    def get_zone_distribution(self) -> Dict[str, Any]:
        """
        Récupère la distribution des stations par zone (pour graphique camembert).

        Returns:
            Distribution {labels: [...], values: [...]}
        """
        zone_metrics = self._get_zone_metrics()

        labels = []
        values = []

        for zone_id, metrics in zone_metrics.items():
            labels.append(metrics['name'])
            values.append(metrics['active'])

        return {
            'labels': labels,
            'values': values,
            'total': sum(values)
        }

    def get_status_distribution(self) -> Dict[str, Any]:
        """
        Récupère la distribution des statuts (pour graphique camembert).

        Returns:
            Distribution {labels: [...], values: [...], colors: [...]}
        """
        zone_metrics = self._get_zone_metrics()

        # Compter les statuts
        status_count = {
            'OPTIMAL': 0,
            'STABLE': 0,
            'WARNING': 0,
            'HIGH_RISK': 0,
            'CRITICAL': 0
        }

        for metrics in zone_metrics.values():
            status = metrics.get('status', 'UNKNOWN')
            if status in status_count:
                status_count[status] += 1

        # Préparer pour graphique
        labels = list(status_count.keys())
        values = list(status_count.values())
        colors = ['#00ff00', '#90ee90', '#ffd700', '#ff6b00', '#ff0000']

        return {
            'labels': labels,
            'values': values,
            'colors': colors,
            'total': sum(values)
        }

    def get_availability_trend(self, hours: int = 24) -> List[Dict]:
        """
        Récupère la tendance de disponibilité (pour graphique ligne).

        Args:
            hours: Nombre d'heures d'historique

        Returns:
            Tendance [{timestamp, availability_rate}, ...]
        """
        try:
            query = """
                SELECT
                    timestamp,
                    AVG(communication_health) as avg_availability
                FROM sdr_health_metrics
                WHERE timestamp >= datetime('now', ? || ' hours')
                GROUP BY strftime('%Y-%m-%d %H', timestamp)
                ORDER BY timestamp ASC
            """

            result = self.db_manager.execute_query(query, (f'-{hours}',))

            if not result:
                return []

            trend = []
            for row in result:
                trend.append({
                    'timestamp': row[0],
                    'availability_rate': round(row[1] or 0, 1)
                })

            return trend

        except Exception as e:
            logger.warning(f"⚠️ Erreur récupération tendance: {e}")
            return []

    def get_anomaly_timeline(self, hours: int = 24) -> List[Dict]:
        """
        Récupère la timeline des anomalies (pour graphique).

        Args:
            hours: Nombre d'heures d'historique

        Returns:
            Timeline [{timestamp, count, critical_count}, ...]
        """
        try:
            query = """
                SELECT
                    strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                    COUNT(*) as total_count,
                    SUM(CASE WHEN level = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count
                FROM sdr_anomalies
                WHERE timestamp >= datetime('now', ? || ' hours')
                GROUP BY hour
                ORDER BY hour ASC
            """

            result = self.db_manager.execute_query(query, (f'-{hours}',))

            if not result:
                return []

            timeline = []
            for row in result:
                timeline.append({
                    'timestamp': row[0],
                    'total_count': row[1] or 0,
                    'critical_count': row[2] or 0
                })

            return timeline

        except Exception as e:
            logger.warning(f"⚠️ Erreur timeline anomalies: {e}")
            return []
