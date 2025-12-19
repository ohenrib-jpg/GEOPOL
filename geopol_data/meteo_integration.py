# Flask/geopol_data/meteo_integration.py
"""
Intégration Open-Meteo pour les couches météorologiques sur la carte
Gère les overlays de température, précipitations et qualité de l'air
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from .connectors.open_meteo import OpenMeteoConnector
from .constants import CAPITALS_GPS

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION DES COUCHES
# ============================================================================

@dataclass
class WeatherLayer:
    """Configuration d'une couche météo"""
    id: str
    name: str
    description: str
    data_field: str  # Champ de données à afficher (temperature, pm2_5, etc.)
    unit: str
    color_scale: List[tuple]  # [(valeur, couleur), ...]
    visible: bool = False
    opacity: float = 0.6

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# Échelles de couleurs
TEMPERATURE_SCALE = [
    (-20, '#0000ff'),  # Bleu foncé (très froid)
    (0, '#00bfff'),    # Bleu clair (froid)
    (10, '#00ff00'),   # Vert (frais)
    (20, '#ffff00'),   # Jaune (agréable)
    (30, '#ffa500'),   # Orange (chaud)
    (40, '#ff0000'),   # Rouge (très chaud)
]

PRECIPITATION_SCALE = [
    (0, '#ffffff'),    # Blanc (pas de pluie)
    (1, '#e0f3f8'),    # Bleu très clair
    (5, '#abd9e9'),    # Bleu clair
    (10, '#74add1'),   # Bleu
    (20, '#4575b4'),   # Bleu foncé
    (50, '#313695'),   # Bleu très foncé
]

AQI_SCALE = [
    (0, '#00e400'),    # Vert (bon)
    (50, '#ffff00'),   # Jaune (modéré)
    (100, '#ff7e00'),  # Orange (mauvais pour sensibles)
    (150, '#ff0000'),  # Rouge (mauvais)
    (200, '#8f3f97'),  # Violet (très mauvais)
    (300, '#7e0023'),  # Marron (dangereux)
]

# Définition des couches
WEATHER_LAYERS = {
    'temperature': WeatherLayer(
        id='temperature',
        name='Température',
        description='Température actuelle en °C',
        data_field='temperature',
        unit='°C',
        color_scale=TEMPERATURE_SCALE,
        visible=False,
        opacity=0.6
    ),
    'precipitation': WeatherLayer(
        id='precipitation',
        name='Précipitations',
        description='Précipitations actuelles en mm',
        data_field='precipitation',
        unit='mm',
        color_scale=PRECIPITATION_SCALE,
        visible=False,
        opacity=0.5
    ),
    'air_quality': WeatherLayer(
        id='air_quality',
        name='Qualité de l\'air',
        description='Indice de qualité de l\'air (AQI)',
        data_field='aqi',
        unit='AQI',
        color_scale=AQI_SCALE,
        visible=False,
        opacity=0.7
    ),
}

# ============================================================================
# CLASSE PRINCIPALE : OPEN-METEO INTEGRATION
# ============================================================================

class OpenMeteoIntegration:
    """
    Gère l'intégration des données Open-Meteo dans la carte géopolitique
    """

    def __init__(self):
        self.connector = OpenMeteoConnector()
        self.layers = {k: v for k, v in WEATHER_LAYERS.items()}
        self._data_cache = {}  # Cache des données par pays

        logger.info("✅ OpenMeteoIntegration initialisée")

    # ========================================================================
    # GESTION DES COUCHES
    # ========================================================================

    def get_all_layers(self) -> List[Dict[str, Any]]:
        """Retourne toutes les couches météo disponibles"""
        return [layer.to_dict() for layer in self.layers.values()]

    def get_layer(self, layer_id: str) -> Optional[Dict[str, Any]]:
        """Retourne une couche spécifique"""
        layer = self.layers.get(layer_id)
        return layer.to_dict() if layer else None

    def toggle_layer(self, layer_id: str, visible: Optional[bool] = None) -> bool:
        """Active/désactive une couche"""
        if layer_id not in self.layers:
            logger.warning(f"Couche inconnue: {layer_id}")
            return False

        if visible is None:
            # Toggle
            self.layers[layer_id].visible = not self.layers[layer_id].visible
        else:
            self.layers[layer_id].visible = visible

        logger.info(f"Couche {layer_id}: {'activée' if self.layers[layer_id].visible else 'désactivée'}")
        return True

    def set_layer_opacity(self, layer_id: str, opacity: float) -> bool:
        """Modifie l'opacité d'une couche"""
        if layer_id not in self.layers:
            return False

        self.layers[layer_id].opacity = max(0.0, min(1.0, opacity))
        logger.info(f"Opacité {layer_id}: {self.layers[layer_id].opacity}")
        return True

    # ========================================================================
    # RÉCUPÉRATION DES DONNÉES
    # ========================================================================

    def fetch_country_weather(self, country_code: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les données météo complètes pour un pays

        Args:
            country_code: Code ISO du pays (ex: 'FR')

        Returns:
            Dict avec weather et air_quality
        """
        # Vérifier le cache
        if country_code in self._data_cache:
            cached_data, cached_time = self._data_cache[country_code]
            # Cache valide pendant 30 minutes
            if (datetime.utcnow() - cached_time).total_seconds() < 1800:
                logger.debug(f"Cache hit météo: {country_code}")
                return cached_data

        # Récupérer les coordonnées de la capitale
        coords = CAPITALS_GPS.get(country_code)
        if not coords:
            logger.warning(f"Coordonnées inconnues pour {country_code}")
            return None

        latitude, longitude = coords

        try:
            # Récupérer les données
            weather = self.connector.fetch_weather(latitude, longitude)
            air_quality = self.connector.fetch_air_quality(latitude, longitude)

            # Construire le résultat
            result = {
                'country_code': country_code,
                'latitude': latitude,
                'longitude': longitude,
                'weather': weather.to_dict() if weather else None,
                'air_quality': air_quality.to_dict() if air_quality else None,
                'timestamp': datetime.utcnow().isoformat()
            }

            # Mettre en cache
            self._data_cache[country_code] = (result, datetime.utcnow())

            logger.info(f"✅ Données météo récupérées: {country_code}")
            return result

        except Exception as e:
            logger.error(f"❌ Erreur récupération météo {country_code}: {e}")
            return None

    def fetch_multiple_countries(self, country_codes: List[str]) -> Dict[str, Any]:
        """
        Récupère les données météo pour plusieurs pays

        Returns:
            Dict avec succès/échecs
        """
        results = {
            'success': True,
            'countries': {},
            'errors': [],
            'total': len(country_codes),
            'fetched': 0
        }

        for code in country_codes:
            try:
                data = self.fetch_country_weather(code)
                if data:
                    results['countries'][code] = data
                    results['fetched'] += 1
                else:
                    results['errors'].append({
                        'country_code': code,
                        'error': 'Données non disponibles'
                    })
            except Exception as e:
                results['errors'].append({
                    'country_code': code,
                    'error': str(e)
                })

        if results['fetched'] == 0:
            results['success'] = False

        logger.info(f"Météo multi-pays: {results['fetched']}/{results['total']}")
        return results

    # ========================================================================
    # GÉNÉRATION GEOJSON
    # ========================================================================

    def generate_geojson_layer(self, layer_id: str, countries_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Génère un GeoJSON pour une couche spécifique

        Args:
            layer_id: ID de la couche (temperature, precipitation, air_quality)
            countries_data: Liste des données pays

        Returns:
            GeoJSON compatible Leaflet
        """
        layer = self.layers.get(layer_id)
        if not layer:
            logger.error(f"Couche inconnue: {layer_id}")
            return {'type': 'FeatureCollection', 'features': []}

        features = []

        for country_data in countries_data:
            try:
                # Extraire la valeur selon le type de couche
                value = self._extract_value(country_data, layer.data_field)

                if value is None:
                    continue

                # Calculer la couleur
                color = self._get_color_for_value(value, layer.color_scale)

                # Créer la feature GeoJSON
                feature = {
                    'type': 'Feature',
                    'properties': {
                        'country_code': country_data['country_code'],
                        'value': value,
                        'unit': layer.unit,
                        'color': color,
                        'layer_id': layer_id,
                        'timestamp': country_data.get('timestamp')
                    },
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [
                            country_data['longitude'],
                            country_data['latitude']
                        ]
                    }
                }

                features.append(feature)

            except Exception as e:
                logger.error(f"Erreur feature GeoJSON: {e}")
                continue

        geojson = {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'layer_id': layer_id,
                'layer_name': layer.name,
                'total_features': len(features),
                'generated_at': datetime.utcnow().isoformat()
            }
        }

        logger.info(f"GeoJSON généré: {layer_id} ({len(features)} features)")
        return geojson

    def _extract_value(self, country_data: Dict[str, Any], field: str) -> Optional[float]:
        """Extrait une valeur spécifique des données pays"""
        if field == 'temperature':
            weather = country_data.get('weather')
            return weather.get('temperature') if weather else None

        elif field == 'precipitation':
            weather = country_data.get('weather')
            return weather.get('precipitation') if weather else None

        elif field == 'aqi':
            air_quality = country_data.get('air_quality')
            return air_quality.get('aqi') if air_quality else None

        return None

    def _get_color_for_value(self, value: float, color_scale: List[tuple]) -> str:
        """Calcule la couleur selon la valeur et l'échelle"""
        if not color_scale:
            return '#cccccc'

        # Trier l'échelle par valeur
        sorted_scale = sorted(color_scale, key=lambda x: x[0])

        # Si valeur inférieure au minimum
        if value <= sorted_scale[0][0]:
            return sorted_scale[0][1]

        # Si valeur supérieure au maximum
        if value >= sorted_scale[-1][0]:
            return sorted_scale[-1][1]

        # Interpoler entre deux couleurs
        for i in range(len(sorted_scale) - 1):
            val1, color1 = sorted_scale[i]
            val2, color2 = sorted_scale[i + 1]

            if val1 <= value <= val2:
                # Pour simplifier, retourner la couleur du seuil inférieur
                # (interpolation RGB serait plus complexe)
                return color1

        return '#cccccc'

    # ========================================================================
    # CONFIGURATION PANNEAU DE CONTRÔLE
    # ========================================================================

    def get_control_panel_config(self) -> Dict[str, Any]:
        """Retourne la configuration du panneau de contrôle météo"""
        return {
            'layers': self.get_all_layers(),
            'active_layers': [
                layer_id for layer_id, layer in self.layers.items()
                if layer.visible
            ],
            'color_scales': {
                layer_id: layer.color_scale
                for layer_id, layer in self.layers.items()
            }
        }

    # ========================================================================
    # UTILITAIRES
    # ========================================================================

    def get_health_status(self) -> Dict[str, Any]:
        """Vérifie la santé du service Open-Meteo"""
        try:
            is_healthy = self.connector.test_connection()

            return {
                'service': 'Open-Meteo',
                'status': 'healthy' if is_healthy else 'degraded',
                'connector': 'operational' if is_healthy else 'error',
                'cache_size': len(self._data_cache),
                'layers': len(self.layers),
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                'service': 'Open-Meteo',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def clear_cache(self):
        """Vide le cache des données"""
        count = len(self._data_cache)
        self._data_cache.clear()
        self.connector.clear_cache()
        logger.info(f"Cache vidé: {count} entrées")

    def preload_priority_countries(self, country_codes: Optional[List[str]] = None):
        """Pré-charge les données pour des pays prioritaires"""
        if country_codes is None:
            from .constants import PRIORITY_COUNTRIES
            country_codes = PRIORITY_COUNTRIES[:20]  # Limiter à 20 pays

        logger.info(f"Pré-chargement météo: {len(country_codes)} pays")

        for code in country_codes:
            try:
                self.fetch_country_weather(code)
            except Exception as e:
                logger.error(f"Erreur pré-chargement {code}: {e}")

        logger.info("✅ Pré-chargement météo terminé")

# ============================================================================
# SINGLETON
# ============================================================================

_meteo_integration_instance = None

def get_meteo_integration() -> OpenMeteoIntegration:
    """Retourne l'instance singleton de OpenMeteoIntegration"""
    global _meteo_integration_instance

    if _meteo_integration_instance is None:
        _meteo_integration_instance = OpenMeteoIntegration()

    return _meteo_integration_instance
