# Flask/geopol_data/overlays/__init__.py
"""Package des surcouches de visualisation"""

from .weather_overlay import WeatherOverlay

__all__ = ['WeatherOverlay']


# Flask/geopol_data/overlays/weather_overlay.py
"""
Surcouche météorologique pour la carte Leaflet
Gère les couches de données Open-Meteo (température, précipitations, vent)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION DES COUCHES
# ============================================================================

@dataclass
class LayerConfig:
    """Configuration d'une couche météo"""
    name: str
    visible: bool = False
    opacity: float = 0.7
    color_scheme: str = 'viridis'  # viridis, plasma, inferno, magma
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'visible': self.visible,
            'opacity': self.opacity,
            'color_scheme': self.color_scheme,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'unit': self.unit
        }

# ============================================================================
# CLASSE PRINCIPALE : WEATHER OVERLAY
# ============================================================================

class WeatherOverlay:
    """
    Gestionnaire des couches météorologiques pour Leaflet
    Prépare les données pour l'affichage front-end
    """
    
    def __init__(self):
        """Initialise les configurations de couches"""
        
        # Configuration des couches disponibles
        self.layers = {
            'temperature': LayerConfig(
                name='Température',
                visible=True,
                opacity=0.7,
                color_scheme='plasma',
                min_value=-20,
                max_value=45,
                unit='°C'
            ),
            'precipitation': LayerConfig(
                name='Précipitations',
                visible=False,
                opacity=0.6,
                color_scheme='viridis',
                min_value=0,
                max_value=50,
                unit='mm'
            ),
            'wind': LayerConfig(
                name='Vent',
                visible=False,
                opacity=0.5,
                color_scheme='inferno',
                min_value=0,
                max_value=100,
                unit='km/h'
            ),
            'air_quality': LayerConfig(
                name='Qualité de l\'air',
                visible=False,
                opacity=0.6,
                color_scheme='magma',
                min_value=0,
                max_value=300,
                unit='AQI'
            )
        }
        
        logger.info("WeatherOverlay initialisé")
    
    # ========================================================================
    # MÉTHODES PRINCIPALES
    # ========================================================================
    
    def get_layer_config(self, layer_type: str) -> Optional[LayerConfig]:
        """Récupère la configuration d'une couche"""
        return self.layers.get(layer_type)
    
    def set_layer_visibility(self, layer_type: str, visible: bool):
        """Active/désactive une couche"""
        if layer_type in self.layers:
            self.layers[layer_type].visible = visible
            logger.info(f"Couche {layer_type}: visible={visible}")
    
    def set_layer_opacity(self, layer_type: str, opacity: float):
        """Modifie l'opacité d'une couche"""
        if layer_type in self.layers:
            # Limiter entre 0 et 1
            opacity = max(0.0, min(1.0, opacity))
            self.layers[layer_type].opacity = opacity
            logger.info(f"Couche {layer_type}: opacity={opacity}")
    
    def get_all_layers_config(self) -> Dict[str, Dict[str, Any]]:
        """Retourne la configuration de toutes les couches"""
        return {
            layer_type: config.to_dict()
            for layer_type, config in self.layers.items()
        }
    
    # ========================================================================
    # PRÉPARATION DES DONNÉES POUR LEAFLET
    # ========================================================================
    
    def prepare_temperature_layer(self, weather_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Prépare les données de température pour Leaflet
        
        Args:
            weather_data: Liste de dicts avec {latitude, longitude, temperature}
        
        Returns:
            Dict prêt pour L.heatLayer ou markers colorés
        """
        config = self.layers['temperature']
        
        # Format pour Leaflet HeatMap
        heat_points = []
        for data in weather_data:
            if data.get('temperature') is not None:
                # Normaliser la température (0-1)
                temp_normalized = self._normalize_value(
                    data['temperature'],
                    config.min_value,
                    config.max_value
                )
                
                heat_points.append({
                    'lat': data['latitude'],
                    'lng': data['longitude'],
                    'value': data['temperature'],
                    'intensity': temp_normalized,
                    'color': self._get_color(temp_normalized, config.color_scheme)
                })
        
        return {
            'type': 'temperature',
            'points': heat_points,
            'config': config.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def prepare_precipitation_layer(self, weather_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prépare les données de précipitations"""
        config = self.layers['precipitation']
        
        points = []
        for data in weather_data:
            if data.get('precipitation') is not None and data['precipitation'] > 0:
                precip_normalized = self._normalize_value(
                    data['precipitation'],
                    config.min_value,
                    config.max_value
                )
                
                points.append({
                    'lat': data['latitude'],
                    'lng': data['longitude'],
                    'value': data['precipitation'],
                    'intensity': precip_normalized,
                    'color': self._get_color(precip_normalized, config.color_scheme)
                })
        
        return {
            'type': 'precipitation',
            'points': points,
            'config': config.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def prepare_wind_layer(self, weather_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prépare les données de vent (vitesse)"""
        config = self.layers['wind']
        
        points = []
        for data in weather_data:
            if data.get('wind_speed') is not None:
                wind_normalized = self._normalize_value(
                    data['wind_speed'],
                    config.min_value,
                    config.max_value
                )
                
                points.append({
                    'lat': data['latitude'],
                    'lng': data['longitude'],
                    'value': data['wind_speed'],
                    'intensity': wind_normalized,
                    'color': self._get_color(wind_normalized, config.color_scheme)
                })
        
        return {
            'type': 'wind',
            'points': points,
            'config': config.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def prepare_air_quality_layer(self, air_quality_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prépare les données de qualité de l'air"""
        config = self.layers['air_quality']
        
        points = []
        for data in air_quality_data:
            if data.get('aqi') is not None:
                aqi_normalized = self._normalize_value(
                    data['aqi'],
                    config.min_value,
                    config.max_value
                )
                
                points.append({
                    'lat': data['latitude'],
                    'lng': data['longitude'],
                    'value': data['aqi'],
                    'level': data.get('aqi_level', 'UNKNOWN'),
                    'intensity': aqi_normalized,
                    'color': self._get_aqi_color(data['aqi'])
                })
        
        return {
            'type': 'air_quality',
            'points': points,
            'config': config.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    # ========================================================================
    # MÉTHODES UTILITAIRES
    # ========================================================================
    
    def _normalize_value(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normalise une valeur entre 0 et 1
        
        Args:
            value: Valeur à normaliser
            min_val: Minimum de l'échelle
            max_val: Maximum de l'échelle
        
        Returns:
            Valeur normalisée (0-1)
        """
        if max_val == min_val:
            return 0.5
        
        normalized = (value - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))
    
    def _get_color(self, normalized_value: float, scheme: str = 'viridis') -> str:
        """
        Retourne une couleur hex selon un schéma de couleurs
        
        Args:
            normalized_value: Valeur normalisée (0-1)
            scheme: Nom du schéma (viridis, plasma, inferno, magma)
        
        Returns:
            Code couleur hex (ex: '#FF5733')
        """
        # Palettes de couleurs simplifiées (5 points)
        palettes = {
            'viridis': [
                '#440154', '#31688e', '#35b779', '#fde724', '#fde724'
            ],
            'plasma': [
                '#0d0887', '#7e03a8', '#cc4778', '#f89540', '#f0f921'
            ],
            'inferno': [
                '#000004', '#420a68', '#932667', '#dd513a', '#fcffa4'
            ],
            'magma': [
                '#000004', '#3b0f70', '#8c2981', '#de4968', '#fcfdbf'
            ]
        }
        
        palette = palettes.get(scheme, palettes['viridis'])
        
        # Interpoler entre les couleurs
        index = normalized_value * (len(palette) - 1)
        idx1 = int(index)
        idx2 = min(idx1 + 1, len(palette) - 1)
        
        return palette[idx1]  # Simplification: retourne la couleur la plus proche
    
    def _get_aqi_color(self, aqi: int) -> str:
        """
        Retourne la couleur EPA standard pour un AQI donné
        
        Args:
            aqi: Air Quality Index (0-500)
        
        Returns:
            Code couleur hex
        """
        if aqi <= 50:
            return '#00e400'  # Vert (Good)
        elif aqi <= 100:
            return '#ffff00'  # Jaune (Moderate)
        elif aqi <= 150:
            return '#ff7e00'  # Orange (Unhealthy for Sensitive)
        elif aqi <= 200:
            return '#ff0000'  # Rouge (Unhealthy)
        elif aqi <= 300:
            return '#8f3f97'  # Violet (Very Unhealthy)
        else:
            return '#7e0023'  # Marron (Hazardous)
    
    # ========================================================================
    # MÉTHODES DE CONVERSION
    # ========================================================================
    
    def to_geojson(self, layer_type: str, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convertit les données en GeoJSON pour Leaflet
        
        Args:
            layer_type: Type de couche (temperature, precipitation, etc.)
            data: Données brutes
        
        Returns:
            GeoJSON FeatureCollection
        """
        features = []
        
        for point in data:
            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [point['longitude'], point['latitude']]
                },
                'properties': {
                    'value': point.get('value'),
                    'intensity': point.get('intensity'),
                    'color': point.get('color'),
                    'layer_type': layer_type
                }
            }
            features.append(feature)
        
        return {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'layer_type': layer_type,
                'count': len(features),
                'timestamp': datetime.utcnow().isoformat()
            }
        }

# ============================================================================
# FONCTION HELPER
# ============================================================================

def create_weather_overlay() -> WeatherOverlay:
    """Factory pour créer une instance de WeatherOverlay"""
    return WeatherOverlay()

# ============================================================================
# EXTENSION POUR CountrySnapshot
# ============================================================================

def enrich_snapshot_with_weather(snapshot, weather_data: Optional[Dict[str, Any]]):
    """
    Enrichit un CountrySnapshot avec des données météo Open-Meteo
    
    Args:
        snapshot: Instance de CountrySnapshot à enrichir
        weather_data: Dict avec 'weather' et 'air_quality'
    
    Returns:
        CountrySnapshot enrichi (modification in-place)
    
    Example:
        >>> from ..connectors.open_meteo import OpenMeteoConnector
        >>> connector = OpenMeteoConnector()
        >>> weather = connector.fetch_complete_data(48.8566, 2.3522)
        >>> enrich_snapshot_with_weather(snapshot, weather)
    """
    if not weather_data:
        return snapshot
    
    # Ajouter les données météo
    if 'weather' in weather_data and weather_data['weather']:
        weather = weather_data['weather']
        snapshot.calculated_indices['current_temperature'] = weather.temperature
        snapshot.calculated_indices['current_precipitation'] = weather.precipitation
        snapshot.calculated_indices['current_wind_speed'] = weather.wind_speed
        snapshot.calculated_indices['current_cloud_cover'] = weather.cloud_cover
    
    # Ajouter les données de qualité de l'air
    if 'air_quality' in weather_data and weather_data['air_quality']:
        air = weather_data['air_quality']
        snapshot.calculated_indices['current_aqi'] = air.aqi
        snapshot.calculated_indices['current_aqi_level'] = air.get_aqi_level()
        snapshot.calculated_indices['current_pm2_5'] = air.pm2_5
        snapshot.calculated_indices['current_pm10'] = air.pm10
    
    logger.info(f"Snapshot enrichi avec données météo pour {snapshot.country_code}")
    return snapshot

# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == '__main__':
    # Configuration logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("TEST WEATHER OVERLAY")
    print("=" * 70)
    
    # Créer l'overlay
    overlay = WeatherOverlay()
    
    # Test 1: Configuration des couches
    print("\n1. Configuration des couches:")
    config = overlay.get_all_layers_config()
    for layer, conf in config.items():
        print(f"   {layer}: visible={conf['visible']}, opacity={conf['opacity']}")
    
    # Test 2: Données simulées
    print("\n2. Préparation données température (simulées):")
    mock_weather = [
        {'latitude': 48.8566, 'longitude': 2.3522, 'temperature': 15.5},
        {'latitude': 52.5200, 'longitude': 13.4050, 'temperature': 12.3},
        {'latitude': 51.5074, 'longitude': -0.1278, 'temperature': 14.8}
    ]
    
    temp_layer = overlay.prepare_temperature_layer(mock_weather)
    print(f"   Points: {len(temp_layer['points'])}")
    print(f"   Exemple: {temp_layer['points'][0]}")
    
    # Test 3: Modification de couche
    print("\n3. Modification couche:")
    overlay.set_layer_visibility('precipitation', True)
    overlay.set_layer_opacity('precipitation', 0.8)
    print(f"   Précipitations: visible={overlay.layers['precipitation'].visible}")
    print(f"   Opacité: {overlay.layers['precipitation'].opacity}")
    
    print("\n" + "=" * 70)
    print("TESTS TERMINÉS")
    print("=" * 70)
