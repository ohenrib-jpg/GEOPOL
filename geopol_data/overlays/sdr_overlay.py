# Flask/geopol_data/overlays/sdr_overlay.py
"""
Couche Leaflet pour visualisation des données SDR
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import numpy as np 

logger = logging.getLogger(__name__)

@dataclass
class SDROverlay:
    """Couche de visualisation SDR pour Leaflet"""
    
    name: str = "SDR Health Monitor"
    description: str = "Surveillance santé réseau radio par zone"
    visible: bool = True
    opacity: float = 0.7
    z_index: int = 900
    
    # Styles par statut
    status_styles: Dict[str, Dict] = field(default_factory=lambda: {
        'CRITICAL': {
            'color': '#ff0000',
            'weight': 3,
            'opacity': 0.8,
            'fillOpacity': 0.4,
            'className': 'sdr-critical'
        },
        'HIGH_RISK': {
            'color': '#ff6b00',
            'weight': 3,
            'opacity': 0.7,
            'fillOpacity': 0.3,
            'className': 'sdr-high-risk'
        },
        'WARNING': {
            'color': '#ffd700',
            'weight': 2,
            'opacity': 0.6,
            'fillOpacity': 0.25,
            'className': 'sdr-warning'
        },
        'STABLE': {
            'color': '#90ee90',
            'weight': 1,
            'opacity': 0.5,
            'fillOpacity': 0.2,
            'className': 'sdr-stable'
        },
        'OPTIMAL': {
            'color': '#00ff00',
            'weight': 1,
            'opacity': 0.4,
            'fillOpacity': 0.15,
            'className': 'sdr-optimal'
        }
    })
    
    def get_geojson_data(self, sdr_analyzer=None) -> Dict[str, Any]:
        """Génère les données GeoJSON pour Leaflet avec vraies stations"""
        try:
        # Récupérer les stations réelles
            from ..connectors.sdr_scrapers import SDRScrapers
            scraper = SDRScrapers()
            stations = scraper.get_stations_as_dict()
        
            features = []
        
        # Créer des points pour chaque station
            for station in stations:
            # Déterminer le statut et la couleur
                status = station.get('status', 'unknown')
                status_colors = {
                    'active': '#00ff00',
                    'online': '#00ff00', 
                    'stable': '#90ee90',
                    'warning': '#ffd700',
                    'offline': '#ff6b00',
                    'unknown': '#cccccc'
                }
            
                color = status_colors.get(status, '#cccccc')
            
                features.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [station['lon'], station['lat']]
                    },
                    'properties': {
                        'id': station['id'],
                        'name': station['name'],
                        'status': status,
                        'country': station.get('country', 'Unknown'),
                        'source': station.get('source', 'Unknown'),
                        'last_seen': station.get('last_seen'),
                        'color': color,
                        'radius': 8 if status == 'active' else 6
                    }
                })
        
        # Ajouter les zones géopolitiques si analyzer disponible
            if sdr_analyzer:
                zone_features = sdr_analyzer.get_geojson_overlay().get('features', [])
                features.extend(zone_features)
        
            return {
                'type': 'FeatureCollection',
                'features': features,
                'timestamp': datetime.utcnow().isoformat(),
                'station_count': len(stations)
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur génération GeoJSON: {e}")
            return self._get_empty_geojson()
    
    def _get_empty_geojson(self) -> Dict[str, Any]:
        """Retourne un GeoJSON vide"""
        return {
            'type': 'FeatureCollection',
            'features': []
        }
    
    def get_legend_html(self) -> str:
        """Génère le HTML de la légende"""
        return '''
        <div class="sdr-legend">
            <h4>🎯 Santé Réseau SDR</h4>
            <div class="legend-items">
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #00ff00;"></span>
                    <span class="legend-label">Optimal</span>
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #90ee90;"></span>
                    <span class="legend-label">Stable</span>
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #ffd700;"></span>
                    <span class="legend-label">Warning</span>
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #ff6b00;"></span>
                    <span class="legend-label">High Risk</span>
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: #ff0000;"></span>
                    <span class="legend-label">Critical</span>
                </div>
            </div>
            <div class="legend-info">
                <small>Anomalies: Activité anormale, blackout, pics</small>
            </div>
        </div>
        '''
    
    def get_popup_html(self, feature_properties: Dict[str, Any]) -> str:
        """Génère le HTML du popup pour une zone"""
        props = feature_properties or {}
        
        html = f'''
        <div class="sdr-popup">
            <h5>📡 Zone: {props.get('name', 'Unknown')}</h5>
            <div class="sdr-metrics">
                <table>
                    <tr>
                        <td><strong>Statut:</strong></td>
                        <td><span class="status-badge {props.get('health_status', '').lower()}">
                            {props.get('health_status', 'UNKNOWN')}
                        </span></td>
                    </tr>
                    <tr>
                        <td><strong>Activité:</strong></td>
                        <td>{props.get('total_activity', 0):.2f}</td>
                    </tr>
                    <tr>
                        <td><strong>Score anomalie:</strong></td>
                        <td>{props.get('anomaly_score', 0):.1f}/100</td>
                    </tr>
                    <tr>
                        <td><strong>Risque géopolitique:</strong></td>
                        <td>{props.get('geopolitical_risk', 0):.1f}/100</td>
                    </tr>
                    <tr>
                        <td><strong>Santé communications:</strong></td>
                        <td>{props.get('communication_health', 0):.1f}/100</td>
                    </tr>
                    <tr>
                        <td><strong>Blackout durée:</strong></td>
                        <td>{props.get('blackout_duration', 0):.1f}h</td>
                    </tr>
                </table>
            </div>
        '''
        
        # Ajouter les actions
        html += '''
            <div class="sdr-actions">
                <button class="btn-small view-details">📊 Détails</button>
                <button class="btn-small view-timeline">📈 Timeline</button>
                <button class="btn-small compare">🔄 Comparer</button>
            </div>
        </div>
        '''
        
        return html
    
    def get_layer_config(self) -> Dict[str, Any]:
        """Configuration de la couche pour Leaflet"""
        return {
            'name': self.name,
            'description': self.description,
            'type': 'geojson',
            'visible': self.visible,
            'opacity': self.opacity,
            'zIndex': self.z_index,
            'style': {
                'default': {
                    'color': '#3388ff',
                    'weight': 2,
                    'opacity': 0.5,
                    'fillOpacity': 0.2
                },
                'hover': {
                    'weight': 3,
                    'opacity': 0.8,
                    'fillOpacity': 0.3
                }
            },
            'interactive': True,
            'popup': True,
            'tooltip': True,
            'legend': self.get_legend_html()
        }


class SDRTimeline:
    """Gestion de la timeline pour l'historique SDR"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def get_zone_timeline(self, zone_id: str, hours: int = 24) -> Dict[str, Any]:
        """Récupère l'historique d'une zone"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    timestamp,
                    total_activity,
                    anomaly_score,
                    geopolitical_risk,
                    communication_health
                FROM sdr_health_metrics
                WHERE zone_id = ? AND timestamp > datetime('now', '-? hours')
                ORDER BY timestamp
            """, (zone_id, hours))
            
            timestamps = []
            activities = []
            anomalies = []
            risks = []
            healths = []
            
            for row in cur.fetchall():
                timestamps.append(row[0])
                activities.append(float(row[1]))
                anomalies.append(float(row[2]))
                risks.append(float(row[3]))
                healths.append(float(row[4]))
            
            conn.close()
            
            return {
                'zone_id': zone_id,
                'timestamps': timestamps,
                'activities': activities,
                'anomalies': anomalies,
                'risks': risks,
                'healths': healths,
                'interval_minutes': 60
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur timeline zone {zone_id}: {e}")
            return {'zone_id': zone_id, 'error': str(e)}
    
    def get_comparison_data(self, zone1: str, zone2: str, hours: int = 24) -> Dict[str, Any]:
        """Compare deux zones"""
        data1 = self.get_zone_timeline(zone1, hours)
        data2 = self.get_zone_timeline(zone2, hours)
        
        return {
            'zone1': data1,
            'zone2': data2,
            'comparison': {
                'avg_activity_diff': np.mean(data1.get('activities', [])) - np.mean(data2.get('activities', [])),
                'avg_risk_diff': np.mean(data1.get('risks', [])) - np.mean(data2.get('risks', [])),
                'correlation': self._calculate_correlation(
                    data1.get('activities', []),
                    data2.get('activities', [])
                )
            }
        }
    
    def _calculate_correlation(self, data1: List[float], data2: List[float]) -> float:
        """Calcule la corrélation entre deux séries"""
        if len(data1) != len(data2) or len(data1) < 2:
            return 0.0
        
        try:
            correlation = np.corrcoef(data1, data2)[0, 1]
            return float(correlation) if not np.isnan(correlation) else 0.0
        except:
            return 0.0


# Export pour le système principal
def create_sdr_overlay_layer(db_manager, sdr_analyzer) -> Dict[str, Any]:
    """Crée une couche SDR pour le système de cartes"""
    overlay = SDROverlay()
    timeline = SDRTimeline(db_manager)
    
    return {
        'layer': overlay,
        'timeline': timeline,
        'config': overlay.get_layer_config(),
        'data_source': lambda: overlay.get_geojson_data(sdr_analyzer),
        'type': 'sdr_health_monitor',
        'category': 'indicators',
        'order': 5
    }