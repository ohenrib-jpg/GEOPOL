# Flask/geopol_data/earthquake_integration.py
"""
Intégration USGS Earthquake pour la couche sismique sur la carte
Gère l'affichage des séismes avec filtrage par magnitude
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from .connectors.earthquake_usgs import USGSEarthquakeConnector, Earthquake

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION DES COUCHES
# ============================================================================

@dataclass
class EarthquakeLayer:
    """Configuration de la couche sismique"""
    id: str
    name: str
    description: str
    min_magnitude: float
    time_period: str  # 'hour', 'day', 'week', 'month'
    max_results: int
    color_scale: List[tuple]  # [(magnitude, couleur), ...]
    visible: bool = False
    opacity: float = 0.8

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# Échelle de couleurs par magnitude
MAGNITUDE_SCALE = [
    (3.0, '#00ff00'),   # Vert - Mineur (< 3)
    (4.0, '#ffff00'),   # Jaune - Léger (3-4)
    (5.0, '#ffa500'),   # Orange - Modéré (4-5)
    (6.0, '#ff4500'),   # Orange foncé - Fort (5-6)
    (7.0, '#ff0000'),   # Rouge - Majeur (6-7)
    (8.0, '#8b0000'),   # Rouge foncé - Catastrophique (7-8)
    (10.0, '#000000'),  # Noir - Exceptionnel (8+)
]

# Échelle de taille par magnitude (pour les marqueurs)
MAGNITUDE_SIZE_SCALE = [
    (3.0, 4),    # Petit
    (4.0, 6),    # Moyen
    (5.0, 8),    # Grand
    (6.0, 12),   # Très grand
    (7.0, 16),   # Énorme
    (8.0, 20),   # Catastrophique
]

# Configuration par défaut
DEFAULT_EARTHQUAKE_LAYER = EarthquakeLayer(
    id='earthquakes',
    name='Séismes',
    description='Séismes en temps réel (USGS)',
    min_magnitude=4.5,
    time_period='week',
    max_results=100,
    color_scale=MAGNITUDE_SCALE,
    visible=False,
    opacity=0.8
)

# ============================================================================
# CLASSE PRINCIPALE : EARTHQUAKE INTEGRATION
# ============================================================================

class EarthquakeIntegration:
    """
    Gère l'intégration des données sismiques USGS dans la carte géopolitique
    """

    def __init__(self):
        self.connector = USGSEarthquakeConnector()
        self.layer = DEFAULT_EARTHQUAKE_LAYER
        self._data_cache = {}  # Cache des données

        logger.info("✅ EarthquakeIntegration initialisée")

    # ========================================================================
    # GESTION DE LA COUCHE
    # ========================================================================

    def get_layer_config(self) -> Dict[str, Any]:
        """Retourne la configuration de la couche"""
        return self.layer.to_dict()

    def update_layer_config(self,
                           min_magnitude: Optional[float] = None,
                           time_period: Optional[str] = None,
                           max_results: Optional[int] = None) -> bool:
        """
        Met à jour la configuration de la couche

        Args:
            min_magnitude: Magnitude minimale (1.0 à 10.0)
            time_period: Période ('hour', 'day', 'week', 'month')
            max_results: Nombre maximum de résultats

        Returns:
            True si la configuration a changé
        """
        changed = False

        if min_magnitude is not None and min_magnitude != self.layer.min_magnitude:
            self.layer.min_magnitude = max(1.0, min(10.0, min_magnitude))
            changed = True
            logger.info(f"Magnitude minimale mise à jour: {self.layer.min_magnitude}")

        if time_period is not None and time_period != self.layer.time_period:
            if time_period in ['hour', 'day', 'week', 'month']:
                self.layer.time_period = time_period
                changed = True
                logger.info(f"Période mise à jour: {self.layer.time_period}")

        if max_results is not None and max_results != self.layer.max_results:
            self.layer.max_results = max(10, min(500, max_results))
            changed = True
            logger.info(f"Max résultats mis à jour: {self.layer.max_results}")

        # Vider le cache si la configuration a changé
        if changed:
            self._data_cache.clear()

        return changed

    def toggle_layer(self, visible: Optional[bool] = None) -> bool:
        """Active/désactive la couche"""
        if visible is None:
            self.layer.visible = not self.layer.visible
        else:
            self.layer.visible = visible

        logger.info(f"Couche séismes: {'activée' if self.layer.visible else 'désactivée'}")
        return True

    def set_layer_opacity(self, opacity: float) -> bool:
        """Modifie l'opacité de la couche"""
        self.layer.opacity = max(0.0, min(1.0, opacity))
        logger.info(f"Opacité séismes: {self.layer.opacity}")
        return True

    # ========================================================================
    # RÉCUPÉRATION DES DONNÉES
    # ========================================================================

    def fetch_earthquakes(self) -> List[Earthquake]:
        """
        Récupère les séismes selon la configuration actuelle

        Returns:
            Liste d'objets Earthquake
        """
        logger.info(f"Récupération séismes: mag ≥ {self.layer.min_magnitude}, période: {self.layer.time_period}")

        try:
            earthquakes = self.connector.fetch_earthquakes(
                min_magnitude=self.layer.min_magnitude,
                time_period=self.layer.time_period,
                max_results=self.layer.max_results
            )

            logger.info(f"✅ {len(earthquakes)} séismes récupérés")
            return earthquakes

        except Exception as e:
            logger.error(f"❌ Erreur récupération séismes: {e}")
            return []

    # ========================================================================
    # GÉNÉRATION GEOJSON
    # ========================================================================

    def generate_geojson(self, earthquakes: Optional[List[Earthquake]] = None) -> Dict[str, Any]:
        """
        Génère un GeoJSON pour la couche sismique

        Args:
            earthquakes: Liste d'objets Earthquake (si None, récupère les données)

        Returns:
            GeoJSON compatible Leaflet
        """
        if earthquakes is None:
            earthquakes = self.fetch_earthquakes()

        features = []

        for eq in earthquakes:
            try:
                # Calculer la couleur selon la magnitude
                color = self._get_color_for_magnitude(eq.magnitude)

                # Calculer la taille selon la magnitude
                size = self._get_size_for_magnitude(eq.magnitude)

                # Créer la feature GeoJSON
                feature = {
                    'type': 'Feature',
                    'id': eq.id,
                    'properties': {
                        'magnitude': eq.magnitude,
                        'magnitude_category': eq.get_magnitude_category(),
                        'place': eq.place,
                        'time': eq.time.isoformat() if eq.time else None,
                        'time_formatted': eq.time.strftime('%Y-%m-%d %H:%M UTC') if eq.time else None,
                        'depth': eq.depth,
                        'depth_category': eq.get_depth_category(),
                        'tsunami': eq.tsunami,
                        'url': eq.url,
                        'color': color,
                        'size': size,
                        'status': eq.status
                    },
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [eq.longitude, eq.latitude, eq.depth]
                    }
                }

                features.append(feature)

            except Exception as e:
                logger.error(f"Erreur feature GeoJSON séisme: {e}")
                continue

        geojson = {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'total_earthquakes': len(features),
                'min_magnitude': self.layer.min_magnitude,
                'time_period': self.layer.time_period,
                'source': 'USGS Earthquake Hazards Program'
            }
        }

        logger.info(f"GeoJSON généré: {len(features)} séismes")
        return geojson

    def _get_color_for_magnitude(self, magnitude: float) -> str:
        """Calcule la couleur selon la magnitude"""
        sorted_scale = sorted(self.layer.color_scale, key=lambda x: x[0])

        if magnitude <= sorted_scale[0][0]:
            return sorted_scale[0][1]

        if magnitude >= sorted_scale[-1][0]:
            return sorted_scale[-1][1]

        for i in range(len(sorted_scale) - 1):
            mag1, color1 = sorted_scale[i]
            mag2, color2 = sorted_scale[i + 1]

            if mag1 <= magnitude < mag2:
                return color1

        return '#808080'  # Gris par défaut

    def _get_size_for_magnitude(self, magnitude: float) -> int:
        """Calcule la taille du marqueur selon la magnitude"""
        sorted_scale = sorted(MAGNITUDE_SIZE_SCALE, key=lambda x: x[0])

        if magnitude <= sorted_scale[0][0]:
            return sorted_scale[0][1]

        if magnitude >= sorted_scale[-1][0]:
            return sorted_scale[-1][1]

        for i in range(len(sorted_scale) - 1):
            mag1, size1 = sorted_scale[i]
            mag2, size2 = sorted_scale[i + 1]

            if mag1 <= magnitude < mag2:
                # Interpolation linéaire
                ratio = (magnitude - mag1) / (mag2 - mag1)
                return int(size1 + (size2 - size1) * ratio)

        return 8  # Taille par défaut

    # ========================================================================
    # STATISTIQUES
    # ========================================================================

    def get_statistics(self, earthquakes: Optional[List[Earthquake]] = None) -> Dict[str, Any]:
        """
        Calcule des statistiques sur les séismes

        Returns:
            Dict avec statistiques
        """
        if earthquakes is None:
            earthquakes = self.fetch_earthquakes()

        if not earthquakes:
            return {
                'total': 0,
                'max_magnitude': 0,
                'avg_magnitude': 0,
                'by_category': {},
                'tsunami_count': 0
            }

        magnitudes = [eq.magnitude for eq in earthquakes]
        categories = {}
        tsunami_count = 0

        for eq in earthquakes:
            category = eq.get_magnitude_category()
            categories[category] = categories.get(category, 0) + 1
            if eq.tsunami:
                tsunami_count += 1

        return {
            'total': len(earthquakes),
            'max_magnitude': max(magnitudes),
            'min_magnitude': min(magnitudes),
            'avg_magnitude': sum(magnitudes) / len(magnitudes),
            'by_category': categories,
            'tsunami_count': tsunami_count,
            'time_period': self.layer.time_period,
            'generated_at': datetime.utcnow().isoformat()
        }

    # ========================================================================
    # UTILITAIRES
    # ========================================================================

    def get_health_status(self) -> Dict[str, Any]:
        """Vérifie la santé du service USGS"""
        try:
            is_healthy = self.connector.test_connection()

            return {
                'service': 'USGS Earthquake',
                'status': 'healthy' if is_healthy else 'degraded',
                'connector': 'operational' if is_healthy else 'error',
                'min_magnitude': self.layer.min_magnitude,
                'time_period': self.layer.time_period,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'service': 'USGS Earthquake',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def clear_cache(self):
        """Vide le cache des données"""
        self._data_cache.clear()
        self.connector.clear_cache()
        logger.info("Cache séismes vidé")

# ============================================================================
# SINGLETON
# ============================================================================

_earthquake_integration_instance = None

def get_earthquake_integration() -> EarthquakeIntegration:
    """Retourne l'instance singleton de EarthquakeIntegration"""
    global _earthquake_integration_instance

    if _earthquake_integration_instance is None:
        _earthquake_integration_instance = EarthquakeIntegration()

    return _earthquake_integration_instance
