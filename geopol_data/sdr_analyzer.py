# Flask/geopol_data/sdr_analyzer.py
"""
Analyseur SDR complet
"""

import numpy as np
from datetime import datetime
from typing import Dict, List, Any

class SDRAnalyzer:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.zones = {
            'NATO': {
                'name': 'OTAN',
                'center': [50.0, 10.0],  # [lat, lon]
                'coordinates': [
                    [35, -10], [35, 30], [70, 30], [70, -10]
                ]
            },
            'BRICS': {
                'name': 'BRICS+',
                'center': [40.0, 80.0],  # [lat, lon]
                'coordinates': [
                    [-35, -80], [-35, 150], [60, 150], [60, -80]
                ]
            },
            'MIDDLE_EAST': {
                'name': 'Moyen-Orient',
                'center': [30.0, 45.0],  # [lat, lon]
                'coordinates': [
                    [12, 30], [12, 60], [40, 60], [40, 30]
                ]
            }
        }
    
    def process_scan_data(self, scan_data: List[Dict]) -> Dict[str, Any]:
        """Traite les données de scan SDR"""
        metrics = {}
        
        for zone_id, zone in self.zones.items():
            # Simulation simple
            activity = 0.1 + np.random.random() * 0.4
            anomaly = 20 + np.random.random() * 60
            
            metrics[zone_id] = {
                'zone_id': zone_id,
                'name': zone['name'],
                'total_activity': round(activity, 3),
                'anomaly_score': round(anomaly, 1),
                'geopolitical_risk': round(30 + np.random.random() * 50, 1),
                'communication_health': round(40 + np.random.random() * 40, 1),
                'status': self._get_status(anomaly),
                'timestamp': datetime.utcnow().isoformat()
            }
        
        return metrics
    
    def _get_status(self, anomaly_score: float) -> str:
        """Détermine le statut santé"""
        if anomaly_score > 80:
            return 'CRITICAL'
        elif anomaly_score > 60:
            return 'HIGH_RISK'
        elif anomaly_score > 40:
            return 'WARNING'
        elif anomaly_score > 20:
            return 'STABLE'
        else:
            return 'OPTIMAL'
    
    def get_geojson_overlay(self) -> Dict[str, Any]:
        """Génère un GeoJSON pour Leaflet"""
        features = []
        
        for zone_id, zone in self.zones.items():
            # Créer un polygon simple
            coordinates = [[lon, lat] for lat, lon in zone['coordinates']]
            
            # Déterminer la couleur
            status_colors = {
                'CRITICAL': '#ff0000',
                'HIGH_RISK': '#ff6b00',
                'WARNING': '#ffd700',
                'STABLE': '#90ee90',
                'OPTIMAL': '#00ff00'
            }
            
            # Simulation d'un statut
            status = 'HIGH_RISK' if zone_id == 'MIDDLE_EAST' else 'WARNING'
            
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [coordinates]
                },
                'properties': {
                    'zone_id': zone_id,
                    'name': zone['name'],
                    'health_status': status,
                    'color': status_colors.get(status, '#cccccc'),
                    'center': zone['center'],
                    'description': f'Zone de surveillance {zone["name"]}'
                }
            })
        
        return {
            'type': 'FeatureCollection',
            'features': features,
            'timestamp': datetime.utcnow().isoformat()
        }