"""
Calculateur de couverture réseau SDR.

Principe :
- Calcul de heatmap de densité de stations
- Identification des zones sous-couvertes
- Statistiques de couverture par région
- Support évolution temporelle

Version: 1.0.0
Author: GEOPOL Analytics
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime
import math
import logging

logger = logging.getLogger(__name__)


@dataclass
class SDRStation:
    """Représente une station SDR."""
    station_id: str
    name: str
    latitude: float
    longitude: float
    status: str  # ACTIVE, INACTIVE, DEGRADED
    last_seen: datetime
    signal_strength: Optional[float] = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class CoverageConfig:
    """Configuration du calcul de couverture."""

    # Rayon de couverture d'une station (km)
    coverage_radius_km: float = 100.0

    # Résolution de la grille pour heatmap (degrés)
    grid_resolution: float = 2.0

    # Seuil de densité pour zone sous-couverte (stations par 100km)
    min_density_threshold: float = 0.5

    # Seuil critique (alerte)
    critical_density_threshold: float = 0.2

    # Zone d'intérêt (bounds)
    bounds: Dict[str, float] = field(default_factory=lambda: {
        'lat_min': -60.0,
        'lat_max': 75.0,
        'lon_min': -180.0,
        'lon_max': 180.0
    })


class CoverageCalculator:
    """
    Calculateur de couverture réseau SDR.

    Fonctionnalités :
    - Heatmap de densité de stations
    - Identification zones sous-couvertes
    - Statistiques de couverture
    - GeoJSON pour Leaflet
    """

    def __init__(self, config: Optional[CoverageConfig] = None):
        """
        Initialise le calculateur de couverture.

        Args:
            config: Configuration optionnelle
        """
        self.config = config or CoverageConfig()
        logger.info(f"🗺️ CoverageCalculator initialisé (rayon={self.config.coverage_radius_km}km)")

    def calculate_coverage(
        self,
        stations: List[SDRStation],
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Calcule la couverture réseau complète.

        Args:
            stations: Liste des stations SDR
            active_only: Considérer uniquement les stations actives

        Returns:
            Statistiques de couverture complètes
        """
        # Filtrer les stations si nécessaire
        if active_only:
            stations = [s for s in stations if s.status == 'ACTIVE']

        logger.info(f"📊 Calcul couverture avec {len(stations)} stations")

        # Générer la heatmap
        heatmap = self.generate_heatmap(stations)

        # Identifier zones sous-couvertes
        undercovered_zones = self.identify_undercovered_zones(heatmap)

        # Calculer statistiques
        stats = self.calculate_statistics(stations, heatmap)

        return {
            'heatmap': heatmap,
            'undercovered_zones': undercovered_zones,
            'statistics': stats,
            'num_stations': len(stations),
            'timestamp': datetime.utcnow().isoformat()
        }

    def generate_heatmap(
        self,
        stations: List[SDRStation]
    ) -> List[Dict[str, float]]:
        """
        Génère une heatmap de densité de stations.

        Args:
            stations: Liste des stations

        Returns:
            Liste de points {lat, lon, intensity}
        """
        heatmap_points = []

        # Créer une grille de points
        lat_min = self.config.bounds['lat_min']
        lat_max = self.config.bounds['lat_max']
        lon_min = self.config.bounds['lon_min']
        lon_max = self.config.bounds['lon_max']
        resolution = self.config.grid_resolution

        lat = lat_min
        while lat <= lat_max:
            lon = lon_min
            while lon <= lon_max:
                # Calculer la densité à ce point
                density = self._calculate_density_at_point(
                    lat, lon, stations
                )

                # Ajouter le point si densité > 0
                if density > 0:
                    heatmap_points.append({
                        'lat': lat,
                        'lon': lon,
                        'intensity': density
                    })

                lon += resolution
            lat += resolution

        logger.info(f"✅ Heatmap générée : {len(heatmap_points)} points")
        return heatmap_points

    def _calculate_density_at_point(
        self,
        lat: float,
        lon: float,
        stations: List[SDRStation]
    ) -> float:
        """
        Calcule la densité de stations à un point donné.

        Args:
            lat: Latitude du point
            lon: Longitude du point
            stations: Liste des stations

        Returns:
            Densité (nombre de stations dans le rayon de couverture)
        """
        count = 0
        for station in stations:
            distance = self._haversine_distance(
                lat, lon,
                station.latitude, station.longitude
            )
            if distance <= self.config.coverage_radius_km:
                count += 1

        return float(count)

    def _haversine_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        Calcule la distance en km entre deux points GPS (formule haversine).

        Args:
            lat1, lon1: Coordonnées point 1
            lat2, lon2: Coordonnées point 2

        Returns:
            Distance en kilomètres
        """
        R = 6371  # Rayon de la Terre en km

        # Convertir en radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        # Formule haversine
        a = (math.sin(delta_lat / 2) ** 2 +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) ** 2)

        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def identify_undercovered_zones(
        self,
        heatmap: List[Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        Identifie les zones sous-couvertes.

        Args:
            heatmap: Points de la heatmap

        Returns:
            Liste des zones sous-couvertes
        """
        undercovered = []
        critical = []

        for point in heatmap:
            intensity = point['intensity']

            # Zone critique (très peu de stations)
            if intensity <= self.config.critical_density_threshold:
                critical.append({
                    'lat': point['lat'],
                    'lon': point['lon'],
                    'density': intensity,
                    'level': 'CRITICAL'
                })
            # Zone sous-couverte
            elif intensity <= self.config.min_density_threshold:
                undercovered.append({
                    'lat': point['lat'],
                    'lon': point['lon'],
                    'density': intensity,
                    'level': 'LOW'
                })

        logger.info(
            f"⚠️ Zones identifiées : {len(critical)} critiques, "
            f"{len(undercovered)} sous-couvertes"
        )

        return critical + undercovered

    def calculate_statistics(
        self,
        stations: List[SDRStation],
        heatmap: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        Calcule des statistiques de couverture.

        Args:
            stations: Liste des stations
            heatmap: Points de la heatmap

        Returns:
            Statistiques
        """
        if not heatmap:
            return {
                'total_stations': len(stations),
                'avg_density': 0.0,
                'max_density': 0.0,
                'min_density': 0.0,
                'coverage_percentage': 0.0
            }

        densities = [p['intensity'] for p in heatmap]

        # Points bien couverts (> seuil min)
        well_covered = sum(
            1 for d in densities
            if d > self.config.min_density_threshold
        )

        coverage_percentage = (well_covered / len(heatmap) * 100) if heatmap else 0

        return {
            'total_stations': len(stations),
            'avg_density': sum(densities) / len(densities),
            'max_density': max(densities),
            'min_density': min(densities),
            'coverage_percentage': round(coverage_percentage, 1),
            'well_covered_points': well_covered,
            'total_points': len(heatmap)
        }

    def generate_geojson_heatmap(
        self,
        heatmap: List[Dict[str, float]],
        max_intensity: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Génère un GeoJSON pour Leaflet Heatmap.

        Args:
            heatmap: Points de la heatmap
            max_intensity: Intensité max pour normalisation (optionnel)

        Returns:
            GeoJSON compatible Leaflet Heatmap
        """
        if not heatmap:
            return {
                'type': 'FeatureCollection',
                'features': []
            }

        # Déterminer intensité max
        if max_intensity is None:
            max_intensity = max(p['intensity'] for p in heatmap)

        features = []
        for point in heatmap:
            # Normaliser intensité (0-1)
            normalized = point['intensity'] / max_intensity if max_intensity > 0 else 0

            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [point['lon'], point['lat']]
                },
                'properties': {
                    'intensity': point['intensity'],
                    'normalized': normalized,
                    'weight': normalized  # Pour Leaflet Heatmap
                }
            })

        return {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'max_intensity': max_intensity,
                'num_points': len(features),
                'timestamp': datetime.utcnow().isoformat()
            }
        }

    def generate_undercovered_geojson(
        self,
        undercovered_zones: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Génère un GeoJSON pour les zones sous-couvertes.

        Args:
            undercovered_zones: Zones sous-couvertes

        Returns:
            GeoJSON avec cercles pour zones sous-couvertes
        """
        features = []

        for zone in undercovered_zones:
            # Couleur selon le niveau
            color = '#ff0000' if zone['level'] == 'CRITICAL' else '#ff9900'

            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [zone['lon'], zone['lat']]
                },
                'properties': {
                    'level': zone['level'],
                    'density': zone['density'],
                    'color': color,
                    'radius': self.config.coverage_radius_km * 1000,  # en mètres
                    'description': f"Zone {zone['level']} (densité: {zone['density']:.1f})"
                }
            })

        return {
            'type': 'FeatureCollection',
            'features': features,
            'metadata': {
                'total_zones': len(features),
                'critical_zones': sum(1 for z in undercovered_zones if z['level'] == 'CRITICAL'),
                'timestamp': datetime.utcnow().isoformat()
            }
        }

    def calculate_coverage_evolution(
        self,
        historical_stations: List[Tuple[datetime, List[SDRStation]]],
        interval_hours: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Calcule l'évolution de la couverture dans le temps.

        Args:
            historical_stations: Liste de (timestamp, stations)
            interval_hours: Intervalle entre points (heures)

        Returns:
            Timeline de couverture
        """
        evolution = []

        for timestamp, stations in historical_stations:
            coverage = self.calculate_coverage(stations)

            evolution.append({
                'timestamp': timestamp.isoformat(),
                'num_stations': coverage['num_stations'],
                'coverage_percentage': coverage['statistics']['coverage_percentage'],
                'avg_density': coverage['statistics']['avg_density'],
                'undercovered_zones': len(coverage['undercovered_zones'])
            })

        return evolution

    def get_coverage_by_region(
        self,
        stations: List[SDRStation],
        regions: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """
        Calcule la couverture par région géopolitique.

        Args:
            stations: Liste des stations
            regions: Définition des régions {id: {name, bounds}}

        Returns:
            Couverture par région
        """
        coverage_by_region = {}

        for region_id, region in regions.items():
            # Filtrer stations dans cette région
            region_stations = [
                s for s in stations
                if self._is_in_bounds(s, region.get('bounds', {}))
            ]

            # Calculer couverture
            if region_stations:
                coverage = self.calculate_coverage(region_stations)
                coverage_by_region[region_id] = {
                    'name': region.get('name', region_id),
                    'num_stations': len(region_stations),
                    'coverage_percentage': coverage['statistics']['coverage_percentage'],
                    'avg_density': coverage['statistics']['avg_density']
                }
            else:
                coverage_by_region[region_id] = {
                    'name': region.get('name', region_id),
                    'num_stations': 0,
                    'coverage_percentage': 0.0,
                    'avg_density': 0.0
                }

        return coverage_by_region

    def _is_in_bounds(
        self,
        station: SDRStation,
        bounds: Dict[str, float]
    ) -> bool:
        """
        Vérifie si une station est dans une zone géographique.

        Args:
            station: Station SDR
            bounds: Limites {lat_min, lat_max, lon_min, lon_max}

        Returns:
            True si dans les limites
        """
        if not bounds:
            return True

        return (
            bounds.get('lat_min', -90) <= station.latitude <= bounds.get('lat_max', 90) and
            bounds.get('lon_min', -180) <= station.longitude <= bounds.get('lon_max', 180)
        )
