# Flask/geopol_data/sdr_analyzer.py
"""
Analyseur SDR amélioré avec détection d'anomalies à faible latence.

Version: 2.0.0
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from .sdr_monitoring.anomaly_detector import (
    AnomalyDetector,
    AnomalyDetectionConfig,
    AnomalyLevel
)

logger = logging.getLogger(__name__)


class SDRAnalyzer:
    """
    Analyseur SDR avec détection d'anomalies intelligente.

    Fonctionnalités :
    - Analyse des métriques par zone géopolitique
    - Détection d'anomalies à faible latence
    - Calcul de statut de santé
    - Génération de GeoJSON pour visualisation
    """

    def __init__(self, db_manager, anomaly_config: Optional[AnomalyDetectionConfig] = None):
        """
        Initialise l'analyseur SDR.

        Args:
            db_manager: Gestionnaire de base de données
            anomaly_config: Configuration de détection d'anomalies (optionnel)
        """
        self.db_manager = db_manager

        # Initialiser le détecteur d'anomalies
        self.anomaly_detector = AnomalyDetector(anomaly_config)

        # Définition des zones géopolitiques
        self.zones = {
            'NATO': {
                'name': 'OTAN',
                'center': [50.0, 10.0],  # [lat, lon]
                'coordinates': [
                    [35, -10], [35, 30], [70, 30], [70, -10]
                ],
                'countries': ['US', 'GB', 'FR', 'DE', 'IT', 'ES', 'CA', 'TR']
            },
            'BRICS': {
                'name': 'BRICS+',
                'center': [40.0, 80.0],
                'coordinates': [
                    [-35, -80], [-35, 150], [60, 150], [60, -80]
                ],
                'countries': ['BR', 'RU', 'IN', 'CN', 'ZA']
            },
            'MIDDLE_EAST': {
                'name': 'Moyen-Orient',
                'center': [30.0, 45.0],
                'coordinates': [
                    [12, 30], [12, 60], [40, 60], [40, 30]
                ],
                'countries': ['SA', 'IR', 'IQ', 'SY', 'YE', 'AE']
            },
            'ASIA_PACIFIC': {
                'name': 'Asie-Pacifique',
                'center': [20.0, 120.0],
                'coordinates': [
                    [-45, 70], [-45, 180], [60, 180], [60, 70]
                ],
                'countries': ['JP', 'KR', 'AU', 'NZ', 'TH', 'VN']
            }
        }

        logger.info("🔬 SDRAnalyzer initialisé avec détection d'anomalies")

    def process_scan_data(
        self,
        scan_data: List[Dict],
        detect_anomalies: bool = True
    ) -> Dict[str, Any]:
        """
        Traite les données de scan SDR avec détection d'anomalies.

        Args:
            scan_data: Données de scan SDR
            detect_anomalies: Activer la détection d'anomalies

        Returns:
            Métriques par zone avec anomalies détectées
        """
        metrics = {}
        all_anomalies = []

        for zone_id, zone in self.zones.items():
            # Calculer les métriques pour la zone
            zone_metrics = self._calculate_zone_metrics(zone_id, scan_data)

            # Détecter les anomalies si activé
            zone_anomalies = []
            if detect_anomalies:
                historical_data = self._get_historical_data(zone_id)

                if historical_data:
                    zone_anomalies = self.anomaly_detector.detect_anomalies(
                        zone_id=zone_id,
                        zone_name=zone['name'],
                        current_metrics=zone_metrics,
                        historical_data=historical_data
                    )
                    all_anomalies.extend(zone_anomalies)

            # Déterminer le statut global de la zone
            status = self._determine_zone_status(zone_metrics, zone_anomalies)

            # Compiler les métriques
            metrics[zone_id] = {
                'zone_id': zone_id,
                'name': zone['name'],
                'metrics': zone_metrics,
                'status': status,
                'anomalies': [a.to_dict() for a in zone_anomalies],
                'anomaly_count': len(zone_anomalies),
                'critical_anomalies': sum(1 for a in zone_anomalies if a.level == AnomalyLevel.CRITICAL),
                'timestamp': datetime.utcnow().isoformat()
            }

        return {
            'zones': metrics,
            'total_anomalies': len(all_anomalies),
            'anomaly_summary': self.anomaly_detector.get_anomaly_summary(all_anomalies),
            'timestamp': datetime.utcnow().isoformat()
        }

    def _calculate_zone_metrics(
        self,
        zone_id: str,
        scan_data: List[Dict]
    ) -> Dict[str, float]:
        """
        Calcule les métriques pour une zone géopolitique.

        Args:
            zone_id: ID de la zone
            scan_data: Données de scan

        Returns:
            Métriques {metric_name: value}
        """
        # Pour l'instant, simulation améliorée
        # TODO: Remplacer par vraies données spectrales

        base_activity = {
            'NATO': 0.35,
            'BRICS': 0.42,
            'MIDDLE_EAST': 0.28,
            'ASIA_PACIFIC': 0.38
        }.get(zone_id, 0.30)

        # Ajouter variation temporelle réaliste
        hour = datetime.utcnow().hour
        day_factor = np.sin((hour - 6) * np.pi / 12) * 0.15 + 1.0  # Pic à midi

        # Ajouter variation aléatoire faible
        noise = np.random.normal(0, 0.05)

        metrics = {
            'total_activity': float(base_activity * day_factor + noise),
            'num_active_stations': int(15 + np.random.poisson(5)),
            'avg_signal_strength': float(50 + np.random.normal(0, 10)),
            'spectral_occupation': float(0.2 + np.random.random() * 0.3),
            'num_peaks': int(20 + np.random.poisson(10)),
            'communication_health': float(60 + np.random.normal(0, 15))
        }

        # S'assurer que les valeurs restent dans des limites raisonnables
        metrics['total_activity'] = max(0.0, min(1.0, metrics['total_activity']))
        metrics['avg_signal_strength'] = max(0, min(100, metrics['avg_signal_strength']))
        metrics['spectral_occupation'] = max(0.0, min(1.0, metrics['spectral_occupation']))
        metrics['communication_health'] = max(0, min(100, metrics['communication_health']))

        return metrics

    def _get_historical_data(
        self,
        zone_id: str,
        hours: int = 24
    ) -> List[Dict[str, float]]:
        """
        Récupère les données historiques pour une zone.

        Args:
            zone_id: ID de la zone
            hours: Nombre d'heures d'historique

        Returns:
            Liste de métriques historiques
        """
        try:
            # Requête SQL pour récupérer les données historiques
            query = """
                SELECT
                    total_activity,
                    num_active_stations,
                    avg_signal_strength,
                    spectral_occupation,
                    num_peaks,
                    communication_health,
                    timestamp
                FROM sdr_health_metrics
                WHERE zone_id = ?
                  AND timestamp >= datetime('now', ? || ' hours')
                ORDER BY timestamp DESC
            """

            result = self.db_manager.execute_query(
                query,
                (zone_id, f'-{hours}')
            )

            if not result:
                logger.warning(f"Pas de données historiques pour {zone_id}")
                return []

            # Convertir en liste de dicts
            historical_data = []
            for row in result:
                historical_data.append({
                    'total_activity': row[0],
                    'num_active_stations': row[1],
                    'avg_signal_strength': row[2],
                    'spectral_occupation': row[3],
                    'num_peaks': row[4],
                    'communication_health': row[5],
                    'timestamp': row[6]
                })

            return historical_data

        except Exception as e:
            logger.error(f"Erreur récupération données historiques: {e}")
            return []

    def _determine_zone_status(
        self,
        metrics: Dict[str, float],
        anomalies: List
    ) -> str:
        """
        Détermine le statut global d'une zone.

        Args:
            metrics: Métriques de la zone
            anomalies: Anomalies détectées

        Returns:
            Statut (OPTIMAL, STABLE, WARNING, HIGH_RISK, CRITICAL)
        """
        # Si anomalies critiques, statut critique
        critical_anomalies = [a for a in anomalies if a.level == AnomalyLevel.CRITICAL]
        if critical_anomalies:
            return 'CRITICAL'

        # Si anomalies HIGH_RISK
        high_risk_anomalies = [a for a in anomalies if a.level == AnomalyLevel.HIGH_RISK]
        if high_risk_anomalies:
            return 'HIGH_RISK'

        # Si anomalies WARNING
        warning_anomalies = [a for a in anomalies if a.level == AnomalyLevel.WARNING]
        if warning_anomalies:
            return 'WARNING'

        # Sinon, basé sur les métriques
        activity = metrics.get('total_activity', 0)
        health = metrics.get('communication_health', 50)

        if activity > 0.7 and health > 80:
            return 'OPTIMAL'
        elif activity > 0.4 and health > 60:
            return 'STABLE'
        elif activity > 0.2 and health > 40:
            return 'WARNING'
        else:
            return 'HIGH_RISK'

    def get_geojson_overlay(self, include_anomalies: bool = True) -> Dict[str, Any]:
        """
        Génère un GeoJSON pour Leaflet avec statuts temps réel.

        Args:
            include_anomalies: Inclure les anomalies dans les propriétés

        Returns:
            GeoJSON FeatureCollection
        """
        # Traiter les données actuelles
        scan_data = []  # TODO: Récupérer vraies données
        processed = self.process_scan_data(scan_data, detect_anomalies=include_anomalies)

        features = []

        for zone_id, zone in self.zones.items():
            # Créer un polygon
            coordinates = [[lon, lat] for lat, lon in zone['coordinates']]

            # Récupérer le statut et les métriques
            zone_data = processed['zones'].get(zone_id, {})
            status = zone_data.get('status', 'UNKNOWN')

            # Couleurs par statut
            status_colors = {
                'CRITICAL': '#ff0000',
                'HIGH_RISK': '#ff6b00',
                'WARNING': '#ffd700',
                'STABLE': '#90ee90',
                'OPTIMAL': '#00ff00',
                'UNKNOWN': '#cccccc'
            }

            # Propriétés du feature
            properties = {
                'zone_id': zone_id,
                'name': zone['name'],
                'health_status': status,
                'color': status_colors.get(status, '#cccccc'),
                'center': zone['center'],
                'description': f'Zone de surveillance {zone["name"]}',
                'metrics': zone_data.get('metrics', {}),
                'anomaly_count': zone_data.get('anomaly_count', 0),
                'critical_anomalies': zone_data.get('critical_anomalies', 0)
            }

            if include_anomalies:
                properties['anomalies'] = zone_data.get('anomalies', [])

            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [coordinates]
                },
                'properties': properties
            })

        return {
            'type': 'FeatureCollection',
            'features': features,
            'total_anomalies': processed.get('total_anomalies', 0),
            'timestamp': datetime.utcnow().isoformat()
        }

    def get_zone_timeline(
        self,
        zone_id: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        Récupère la timeline d'une zone sur X heures.

        Args:
            zone_id: ID de la zone
            hours: Nombre d'heures

        Returns:
            Timeline avec métriques et anomalies
        """
        historical_data = self._get_historical_data(zone_id, hours)

        if not historical_data:
            return {
                'zone_id': zone_id,
                'data': [],
                'anomalies': [],
                'summary': {}
            }

        # Extraire les timestamps et métriques
        timeline = []
        for data in historical_data:
            timeline.append({
                'timestamp': data['timestamp'],
                'total_activity': data['total_activity'],
                'num_active_stations': data['num_active_stations'],
                'communication_health': data['communication_health']
            })

        return {
            'zone_id': zone_id,
            'zone_name': self.zones[zone_id]['name'],
            'data': timeline,
            'data_points': len(timeline),
            'timestamp': datetime.utcnow().isoformat()
        }
