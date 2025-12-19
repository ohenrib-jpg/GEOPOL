"""
Sources satellite publiques - Sans authentification requise

Ce module fournit accès à de nombreuses sources satellite publiques :
- Imagerie satellite gratuite (Sentinel, Landsat, MODIS)
- Fonds de carte (OSM, ESRI, Google)
- Données thématiques (météo, végétation, océans)
- Services WMS publics

Version: 2.0.0
Author: GEOPOL Analytics
"""

from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SatelliteSources:
    """
    Gestionnaire des sources satellite publiques.

    Toutes les sources sont accessibles sans authentification.
    """

    def __init__(self):
        """Initialise les sources satellite."""
        self.public_layers = self._init_public_layers()
        self.wms_sources = self._init_wms_sources()

        logger.info(f"📡 {len(self.public_layers)} couches publiques + {len(self.wms_sources)} sources WMS chargées")

    def _init_public_layers(self) -> Dict[str, Dict]:
        """
        Initialise les couches satellite publiques.

        Sources principales :
        - Sentinel-2 Cloudless
        - OpenStreetMap
        - ESRI World Imagery
        - Google Maps
        - Autres tuiles publiques
        """
        return {
            # ==========================================
            # SENTINEL-2 CLOUDLESS (EOX)
            # ==========================================
            's2cloudless': {
                'name': 'Sentinel-2 Cloudless',
                'description': 'Mosaïque satellite Sentinel-2 sans nuages (EOX)',
                'type': 'satellite',
                'category': 'satellite',
                'url_template': 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2023_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg',
                'attribution': '© EOX IT Services GmbH',
                'resolution': '10m',
                'coverage': 'Mondiale',
                'update_frequency': 'Annuelle',
                'max_zoom': 15
            },

            's2cloudless_2022': {
                'name': 'Sentinel-2 Cloudless 2022',
                'description': 'Mosaïque Sentinel-2 2022',
                'type': 'satellite',
                'category': 'satellite',
                'url_template': 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2022_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg',
                'attribution': '© EOX IT Services GmbH',
                'resolution': '10m',
                'coverage': 'Mondiale',
                'max_zoom': 15
            },

            's2cloudless_2021': {
                'name': 'Sentinel-2 Cloudless 2021',
                'description': 'Mosaïque Sentinel-2 2021',
                'type': 'satellite',
                'category': 'satellite',
                'url_template': 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2021_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg',
                'attribution': '© EOX IT Services GmbH',
                'resolution': '10m',
                'coverage': 'Mondiale',
                'max_zoom': 15
            },

            # ==========================================
            # OPENSTREETMAP
            # ==========================================
            'osm_standard': {
                'name': 'OpenStreetMap Standard',
                'description': 'Carte OSM standard',
                'type': 'basemap',
                'category': 'basemap',
                'url_template': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                'attribution': '© OpenStreetMap contributors',
                'max_zoom': 19
            },

            'osm_humanitarian': {
                'name': 'OpenStreetMap Humanitarian',
                'description': 'Carte OSM style humanitaire',
                'type': 'basemap',
                'category': 'basemap',
                'url_template': 'https://tile-{s}.openstreetmap.fr/hot/{z}/{x}/{y}.png',
                'subdomains': ['a', 'b'],
                'attribution': '© OpenStreetMap contributors',
                'max_zoom': 19
            },

            # ==========================================
            # ESRI
            # ==========================================
            'esri_world_imagery': {
                'name': 'ESRI World Imagery',
                'description': 'Imagerie satellite mondiale ESRI',
                'type': 'satellite',
                'category': 'satellite',
                'url_template': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                'attribution': '© ESRI',
                'resolution': 'Variable (0.3m-1m)',
                'coverage': 'Mondiale',
                'max_zoom': 19
            },

            'esri_world_topo': {
                'name': 'ESRI World Topographic',
                'description': 'Carte topographique mondiale ESRI',
                'type': 'basemap',
                'category': 'basemap',
                'url_template': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
                'attribution': '© ESRI',
                'max_zoom': 19
            },

            'esri_world_street': {
                'name': 'ESRI World Street Map',
                'description': 'Carte des rues mondiale ESRI',
                'type': 'basemap',
                'category': 'basemap',
                'url_template': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
                'attribution': '© ESRI',
                'max_zoom': 19
            },

            # ==========================================
            # CARTO
            # ==========================================
            'carto_light': {
                'name': 'CARTO Light',
                'description': 'Fond de carte clair CARTO',
                'type': 'basemap',
                'category': 'basemap',
                'url_template': 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
                'subdomains': ['a', 'b', 'c', 'd'],
                'attribution': '© CARTO',
                'max_zoom': 19
            },

            'carto_dark': {
                'name': 'CARTO Dark',
                'description': 'Fond de carte sombre CARTO',
                'type': 'basemap',
                'category': 'basemap',
                'url_template': 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
                'subdomains': ['a', 'b', 'c', 'd'],
                'attribution': '© CARTO',
                'max_zoom': 19
            },

            # ==========================================
            # STAMEN
            # ==========================================
            'stamen_terrain': {
                'name': 'Stamen Terrain',
                'description': 'Carte terrain avec relief',
                'type': 'basemap',
                'category': 'basemap',
                'url_template': 'https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png',
                'attribution': '© Stamen Design',
                'max_zoom': 18
            },

            'stamen_watercolor': {
                'name': 'Stamen Watercolor',
                'description': 'Carte style aquarelle',
                'type': 'basemap',
                'category': 'basemap',
                'url_template': 'https://stamen-tiles.a.ssl.fastly.net/watercolor/{z}/{x}/{y}.png',
                'attribution': '© Stamen Design',
                'max_zoom': 16
            },

            # ==========================================
            # GOOGLE MAPS (via proxy)
            # ==========================================
            'google_hybrid': {
                'name': 'Google Hybrid',
                'description': 'Satellite + routes Google',
                'type': 'satellite',
                'category': 'satellite',
                'url_template': 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                'attribution': '© Google',
                'max_zoom': 20
            },

            'google_satellite': {
                'name': 'Google Satellite',
                'description': 'Satellite Google',
                'type': 'satellite',
                'category': 'satellite',
                'url_template': 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                'attribution': '© Google',
                'max_zoom': 20
            },

            'google_terrain': {
                'name': 'Google Terrain',
                'description': 'Terrain avec relief Google',
                'type': 'basemap',
                'category': 'basemap',
                'url_template': 'https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
                'attribution': '© Google',
                'max_zoom': 20
            },
        }

    def _init_wms_sources(self) -> Dict[str, Dict]:
        """
        Initialise les sources WMS publiques.

        Sources WMS (Web Map Service) gratuites et sans authentification.
        """
        return {
            # ==========================================
            # ESA WORLDCOVER
            # ==========================================
            'esa_worldcover': {
                'name': 'ESA WorldCover 2021',
                'description': 'Carte mondiale de couverture des sols (10m)',
                'type': 'wms',
                'category': 'thematic',
                'wms_url': 'https://services.terrascope.be/wms/v2',
                'wms_layers': 'WORLDCOVER_2021_MAP',
                'wms_version': '1.3.0',
                'wms_format': 'image/png',
                'attribution': '© ESA WorldCover',
                'resolution': '10m',
                'coverage': 'Mondiale'
            },

            # ==========================================
            # NASA
            # ==========================================
            'nasa_modis_terra': {
                'name': 'NASA MODIS Terra',
                'description': 'Images MODIS du satellite Terra',
                'type': 'wms',
                'category': 'satellite',
                'wms_url': 'https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi',
                'wms_layers': 'MODIS_Terra_CorrectedReflectance_TrueColor',
                'wms_version': '1.3.0',
                'wms_format': 'image/jpeg',
                'attribution': '© NASA EOSDIS',
                'resolution': '250m',
                'coverage': 'Mondiale'
            },

            'nasa_fires': {
                'name': 'NASA FIRMS Fires',
                'description': 'Détection de feux actifs (MODIS)',
                'type': 'wms',
                'category': 'thematic',
                'wms_url': 'https://firms.modaps.eosdis.nasa.gov/wms',
                'wms_layers': 'fires_modis_24',
                'wms_version': '1.3.0',
                'wms_format': 'image/png',
                'attribution': '© NASA FIRMS',
                'update_frequency': 'Temps réel',
                'coverage': 'Mondiale'
            },

            # ==========================================
            # COPERNICUS
            # ==========================================
            'copernicus_dem': {
                'name': 'Copernicus DEM',
                'description': 'Modèle numérique d\'élévation (30m)',
                'type': 'wms',
                'category': 'thematic',
                'wms_url': 'https://copernicus-dem-30m.s3.amazonaws.com',
                'attribution': '© Copernicus',
                'resolution': '30m',
                'coverage': 'Mondiale'
            },

            # ==========================================
            # USGS
            # ==========================================
            'usgs_topo': {
                'name': 'USGS Topographic',
                'description': 'Cartes topographiques USGS',
                'type': 'wms',
                'category': 'basemap',
                'wms_url': 'https://basemap.nationalmap.gov/arcgis/services/USGSTopo/MapServer/WMSServer',
                'wms_layers': '0',
                'wms_version': '1.3.0',
                'wms_format': 'image/png',
                'attribution': '© USGS',
                'coverage': 'USA'
            },

            # ==========================================
            # BATHYMETRIE
            # ==========================================
            'gebco_bathymetry': {
                'name': 'GEBCO Bathymetry',
                'description': 'Bathymétrie océanique mondiale',
                'type': 'wms',
                'category': 'thematic',
                'wms_url': 'https://www.gebco.net/data_and_products/gebco_web_services/web_map_service/mapserv',
                'wms_layers': 'GEBCO_LATEST',
                'wms_version': '1.3.0',
                'wms_format': 'image/png',
                'attribution': '© GEBCO',
                'coverage': 'Mondiale (océans)'
            }
        }

    def get_public_layers(self) -> Dict[str, Dict]:
        """
        Retourne toutes les couches publiques (tuiles).

        Returns:
            Dictionnaire {layer_id: metadata}
        """
        return self.public_layers.copy()

    def get_wms_sources(self) -> Dict[str, Dict]:
        """
        Retourne toutes les sources WMS publiques.

        Returns:
            Dictionnaire {layer_id: metadata}
        """
        return self.wms_sources.copy()

    def get_all_layers(self) -> Dict[str, Dict]:
        """
        Retourne toutes les couches (tuiles + WMS).

        Returns:
            Dictionnaire combiné
        """
        all_layers = self.public_layers.copy()
        all_layers.update(self.wms_sources)
        return all_layers

    def get_layer_url(
        self,
        layer_id: str,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        width: int = 512,
        height: int = 512
    ) -> Optional[str]:
        """
        Génère l'URL pour une couche.

        Args:
            layer_id: Identifiant de la couche
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            width: Largeur en pixels
            height: Hauteur en pixels

        Returns:
            URL de la couche (template ou WMS)
        """
        # Chercher dans les couches publiques
        if layer_id in self.public_layers:
            layer = self.public_layers[layer_id]
            return layer.get('url_template')

        # Chercher dans les sources WMS
        if layer_id in self.wms_sources:
            if bbox is None:
                logger.warning(f"⚠️ Bbox requis pour couche WMS {layer_id}")
                return None

            layer = self.wms_sources[layer_id]
            return self._generate_wms_url(layer, bbox, width, height)

        logger.warning(f"⚠️ Couche {layer_id} non trouvée")
        return None

    def _generate_wms_url(
        self,
        layer: Dict,
        bbox: Tuple[float, float, float, float],
        width: int,
        height: int
    ) -> str:
        """
        Génère une URL WMS.

        Args:
            layer: Métadonnées de la couche
            bbox: Bounding box
            width: Largeur
            height: Hauteur

        Returns:
            URL WMS complète
        """
        wms_url = layer['wms_url']
        wms_layers = layer['wms_layers']
        wms_version = layer.get('wms_version', '1.3.0')
        wms_format = layer.get('wms_format', 'image/png')

        # Formater la bbox selon la version WMS
        if wms_version == '1.3.0':
            # Version 1.3.0 : lat,lon
            bbox_str = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"
            crs = "EPSG:4326"
        else:
            # Version 1.1.1 : lon,lat
            bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            crs = "EPSG:4326"

        # Construire l'URL
        url = (
            f"{wms_url}?"
            f"SERVICE=WMS&"
            f"VERSION={wms_version}&"
            f"REQUEST=GetMap&"
            f"LAYERS={wms_layers}&"
            f"CRS={crs}&"
            f"BBOX={bbox_str}&"
            f"WIDTH={width}&"
            f"HEIGHT={height}&"
            f"FORMAT={wms_format}&"
            f"TRANSPARENT=TRUE"
        )

        return url

    def get_layers_by_category(self, category: str) -> Dict[str, Dict]:
        """
        Filtre les couches par catégorie.

        Args:
            category: satellite, basemap, thematic

        Returns:
            Couches filtrées
        """
        all_layers = self.get_all_layers()

        filtered = {
            layer_id: metadata
            for layer_id, metadata in all_layers.items()
            if metadata.get('category') == category
        }

        return filtered

    def get_layers_by_type(self, layer_type: str) -> Dict[str, Dict]:
        """
        Filtre les couches par type.

        Args:
            layer_type: satellite, basemap, wms

        Returns:
            Couches filtrées
        """
        all_layers = self.get_all_layers()

        filtered = {
            layer_id: metadata
            for layer_id, metadata in all_layers.items()
            if metadata.get('type') == layer_type
        }

        return filtered
