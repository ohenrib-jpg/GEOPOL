"""
Détecteur d'anomalies SDR à faible latence.

Principe :
- Analyse spectrale uniquement (pas d'écoute audio)
- Détection basée sur écarts statistiques (moyenne mobile + écart-type)
- Latence cible : < 5 minutes
- Objectif : Détecter événements anthropiques soudains

Version: 1.0.0
Author: GEOPOL Analytics
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import logging

logger = logging.getLogger(__name__)


class AnomalyLevel(Enum):
    """Niveaux de sévérité des anomalies."""
    INFO = "INFO"              # < 2σ - Variations normales
    WARNING = "WARNING"        # 2-3σ - À surveiller
    HIGH_RISK = "HIGH_RISK"    # 3-4σ - Anomalie probable
    CRITICAL = "CRITICAL"      # > 4σ - Anomalie confirmée


@dataclass
class AnomalyDetectionConfig:
    """Configuration de la détection d'anomalies."""

    # Fenêtre temporelle pour la baseline (en heures)
    baseline_window_hours: int = 24

    # Seuils en nombre d'écarts-types (sigma)
    threshold_warning: float = 2.0
    threshold_high_risk: float = 3.0
    threshold_critical: float = 4.0

    # Fenêtre minimale de données pour détecter (en points)
    min_data_points: int = 10

    # Latence de détection (en minutes)
    detection_interval_minutes: int = 5

    # Seuils spécifiques par zone (optionnel)
    zone_thresholds: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class Anomaly:
    """Représente une anomalie détectée."""

    timestamp: datetime
    zone_id: str
    zone_name: str
    metric_name: str
    current_value: float
    baseline_value: float
    std_deviation: float
    sigma_deviation: float  # Nombre d'écarts-types
    level: AnomalyLevel
    description: str
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convertit en dictionnaire."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'zone_id': self.zone_id,
            'zone_name': self.zone_name,
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'baseline_value': self.baseline_value,
            'std_deviation': self.std_deviation,
            'sigma_deviation': round(self.sigma_deviation, 2),
            'level': self.level.value,
            'description': self.description,
            'metadata': self.metadata
        }


class AnomalyDetector:
    """
    Détecteur d'anomalies SDR basé sur analyse statistique.

    Algorithme :
    1. Calcul baseline (moyenne mobile sur 24h)
    2. Calcul écart-type pour mesurer volatilité
    3. Détection basée sur nombre de sigma
    4. Classification par niveau de sévérité
    """

    def __init__(self, config: Optional[AnomalyDetectionConfig] = None):
        """
        Initialise le détecteur d'anomalies.

        Args:
            config: Configuration optionnelle (utilise défaut si None)
        """
        self.config = config or AnomalyDetectionConfig()
        logger.info(f"🔍 AnomalyDetector initialisé (baseline={self.config.baseline_window_hours}h)")

    def detect_anomalies(
        self,
        zone_id: str,
        zone_name: str,
        current_metrics: Dict[str, float],
        historical_data: List[Dict[str, float]],
        timestamp: Optional[datetime] = None
    ) -> List[Anomaly]:
        """
        Détecte les anomalies pour une zone géographique.

        Args:
            zone_id: Identifiant de la zone
            zone_name: Nom de la zone
            current_metrics: Métriques actuelles {metric_name: value}
            historical_data: Données historiques (liste de dicts)
            timestamp: Timestamp actuel (défaut: maintenant)

        Returns:
            Liste des anomalies détectées
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        anomalies = []

        # Vérifier qu'on a assez de données
        if len(historical_data) < self.config.min_data_points:
            logger.warning(
                f"Pas assez de données pour {zone_name} "
                f"({len(historical_data)} < {self.config.min_data_points})"
            )
            return anomalies

        # Analyser chaque métrique
        for metric_name, current_value in current_metrics.items():
            anomaly = self._detect_metric_anomaly(
                zone_id=zone_id,
                zone_name=zone_name,
                metric_name=metric_name,
                current_value=current_value,
                historical_data=historical_data,
                timestamp=timestamp
            )

            if anomaly:
                anomalies.append(anomaly)

        return anomalies

    def _detect_metric_anomaly(
        self,
        zone_id: str,
        zone_name: str,
        metric_name: str,
        current_value: float,
        historical_data: List[Dict[str, float]],
        timestamp: datetime
    ) -> Optional[Anomaly]:
        """
        Détecte une anomalie pour une métrique spécifique.

        Args:
            zone_id: ID de la zone
            zone_name: Nom de la zone
            metric_name: Nom de la métrique
            current_value: Valeur actuelle
            historical_data: Données historiques
            timestamp: Timestamp

        Returns:
            Anomaly si détectée, None sinon
        """
        # Extraire les valeurs historiques pour cette métrique
        historical_values = [
            data.get(metric_name, 0)
            for data in historical_data
            if metric_name in data
        ]

        if len(historical_values) < self.config.min_data_points:
            return None

        # Calculer la baseline (moyenne)
        baseline = statistics.mean(historical_values)

        # Calculer l'écart-type
        try:
            std_dev = statistics.stdev(historical_values)
        except statistics.StatisticsError:
            # Pas assez de variation dans les données
            std_dev = 0.0

        # Si écart-type = 0, toutes les valeurs sont identiques
        if std_dev == 0:
            # Détecter uniquement si la valeur actuelle est différente
            if current_value != baseline:
                sigma = float('inf')
            else:
                return None
        else:
            # Calculer le nombre d'écarts-types
            sigma = abs(current_value - baseline) / std_dev

        # Récupérer les seuils (spécifiques à la zone ou par défaut)
        zone_thresholds = self.config.zone_thresholds.get(zone_id, {})
        threshold_warning = zone_thresholds.get('warning', self.config.threshold_warning)
        threshold_high_risk = zone_thresholds.get('high_risk', self.config.threshold_high_risk)
        threshold_critical = zone_thresholds.get('critical', self.config.threshold_critical)

        # Déterminer le niveau d'anomalie
        level = None
        if sigma >= threshold_critical:
            level = AnomalyLevel.CRITICAL
        elif sigma >= threshold_high_risk:
            level = AnomalyLevel.HIGH_RISK
        elif sigma >= threshold_warning:
            level = AnomalyLevel.WARNING

        # Si pas d'anomalie, retourner None
        if level is None:
            return None

        # Créer la description
        direction = "augmentation" if current_value > baseline else "diminution"
        percentage = abs((current_value - baseline) / baseline * 100) if baseline != 0 else 0

        description = (
            f"{level.value}: {direction} anormale de {metric_name} "
            f"dans {zone_name} ({percentage:.1f}% vs baseline, {sigma:.1f}σ)"
        )

        # Créer l'anomalie
        anomaly = Anomaly(
            timestamp=timestamp,
            zone_id=zone_id,
            zone_name=zone_name,
            metric_name=metric_name,
            current_value=current_value,
            baseline_value=baseline,
            std_deviation=std_dev,
            sigma_deviation=sigma,
            level=level,
            description=description,
            metadata={
                'percentage_change': round(percentage, 1),
                'direction': direction,
                'data_points': len(historical_values)
            }
        )

        logger.info(f"🚨 {description}")

        return anomaly

    def calculate_baseline(
        self,
        metric_name: str,
        historical_data: List[Dict[str, float]]
    ) -> Tuple[float, float]:
        """
        Calcule la baseline et l'écart-type pour une métrique.

        Args:
            metric_name: Nom de la métrique
            historical_data: Données historiques

        Returns:
            (baseline, std_deviation)
        """
        values = [
            data.get(metric_name, 0)
            for data in historical_data
            if metric_name in data
        ]

        if len(values) < 2:
            return 0.0, 0.0

        baseline = statistics.mean(values)

        try:
            std_dev = statistics.stdev(values)
        except statistics.StatisticsError:
            std_dev = 0.0

        return baseline, std_dev

    def filter_recent_data(
        self,
        historical_data: List[Dict],
        hours: Optional[int] = None
    ) -> List[Dict]:
        """
        Filtre les données pour ne garder que la fenêtre temporelle récente.

        Args:
            historical_data: Données historiques avec timestamp
            hours: Nombre d'heures (défaut: config.baseline_window_hours)

        Returns:
            Données filtrées
        """
        if hours is None:
            hours = self.config.baseline_window_hours

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        filtered = [
            data for data in historical_data
            if 'timestamp' in data and
               datetime.fromisoformat(data['timestamp']) >= cutoff_time
        ]

        return filtered

    def get_anomaly_summary(
        self,
        anomalies: List[Anomaly]
    ) -> Dict:
        """
        Génère un résumé des anomalies détectées.

        Args:
            anomalies: Liste des anomalies

        Returns:
            Dictionnaire de statistiques
        """
        if not anomalies:
            return {
                'total': 0,
                'by_level': {},
                'by_zone': {},
                'critical_count': 0,
                'high_risk_count': 0,
                'warning_count': 0
            }

        # Compter par niveau
        by_level = {}
        for level in AnomalyLevel:
            by_level[level.value] = sum(1 for a in anomalies if a.level == level)

        # Compter par zone
        by_zone = {}
        for anomaly in anomalies:
            zone_name = anomaly.zone_name
            if zone_name not in by_zone:
                by_zone[zone_name] = 0
            by_zone[zone_name] += 1

        return {
            'total': len(anomalies),
            'by_level': by_level,
            'by_zone': by_zone,
            'critical_count': by_level.get('CRITICAL', 0),
            'high_risk_count': by_level.get('HIGH_RISK', 0),
            'warning_count': by_level.get('WARNING', 0),
            'info_count': by_level.get('INFO', 0)
        }
