import requests
from datetime import datetime
from typing import Dict, List, Tuple
import numpy as np
from flask import current_app
import json

class BasicSatelliteModule:
    def __init__(self):
        """Module satellite basique utilisant uniquement des services publics."""
        self.public_layers = {
            's2cloudless': {
                'name': 'Sentinel-2 Cloudless 2020',
                'url': 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg',
                'attribution': 'EOX IT Services GmbH (s2maps.eu)',
                'type': 'tile',
                'max_zoom': 19
            },
            's2cloudless_latest': {
                'name': 'Sentinel-2 Cloudless Latest',
                'url': 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2023_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.jpg',
                'attribution': 'EOX IT Services GmbH (s2maps.eu)',
                'type': 'tile',
                'max_zoom': 19
            },
            'landsat': {
                'name': 'Landsat 8 Cloudless',
                'url': 'https://tiles.maps.eox.at/wmts/1.0.0/landsat8_pan_3857/default/GoogleMapsCompatible/{z}/{y}/{x}.png',
                'attribution': 'USGS, NASA, EOX',
                'type': 'tile',
                'max_zoom': 12
            },
            'osm': {
                'name': 'OpenStreetMap',
                'url': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                'attribution': 'OpenStreetMap contributors',
                'type': 'tile',
                'max_zoom': 19
            }
        }
        
    def get_public_layers(self) -> Dict:
        """Retourne les couches satellite publiques disponibles."""
        return self.public_layers
    
    def get_layer_url(self, layer_id: str) -> Optional[str]:
        """Retourne l'URL WMTS d'une couche publique."""
        if layer_id in self.public_layers:
            return self.public_layers[layer_id]['url']
        return None
    
    def get_available_dates(self, bbox: Tuple[float, float, float, float]) -> List[Dict]:
        """
        Pour les couches publiques, retourne des dates pré-définies.
        Les mosaïques cloudless sont des composites sur plusieurs mois.
        """
        return [
            {"date": "2020-01-01", "description": "Sentinel-2 Cloudless 2020", "layer": "s2cloudless"},
            {"date": "2023-01-01", "description": "Sentinel-2 Cloudless 2023", "layer": "s2cloudless_latest"},
            {"date": "2022-01-01", "description": "Landsat 8 Composite", "layer": "landsat"}
        ]
    
    def get_metadata_info(self) -> Dict:
        """Retourne les informations de métadonnées des couches publiques."""
        return {
            "s2cloudless": {
                "description": "Mosaïque globale Sentinel-2 sans nuages (2020)",
                "resolution": "10m-60m",
                "coverage": "Global",
                "update_frequency": "Annuel",
                "source": "Copernicus Sentinel-2"
            },
            "s2cloudless_latest": {
                "description": "Mosaïque globale Sentinel-2 sans nuages (2023)",
                "resolution": "10m-60m",
                "coverage": "Global",
                "update_frequency": "Annuel",
                "source": "Copernicus Sentinel-2"
            },
            "landsat": {
                "description": "Mosaïque Landsat 8",
                "resolution": "15m",
                "coverage": "Global",
                "update_frequency": "Annuel",
                "source": "USGS Landsat 8"
            }
        }