# Flask/geopol_data/sdr_integration.py
"""
Module d'intégration SDR pour GEOPOL
Coordonne l'analyse SDR, la visualisation et les corrélations
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class SDRIntegrationManager:
    """Manager d'intégration SDR pour GEOPOL"""
    
    def __init__(self, app, db_manager, sdr_service=None):
        self.app = app
        self.db_manager = db_manager
        self.sdr_service = sdr_service
        self.sdr_analyzer = None
        self.sdr_overlay = None
        self.sdr_timeline = None
        
        # Initialiser les composants
        self._init_components()
        
        logger.info("✅ SDRIntegrationManager initialisé")
    
    def _init_components(self):
        """Initialise les composants SDR"""
        try:
            # 1. Analyseur SDR
            from .sdr_analyzer import SDRAnalyzer
            self.sdr_analyzer = SDRAnalyzer(self.db_manager)
            logger.info("✅ SDRAnalyzer initialisé")
            
            # 2. Couche Leaflet
            from .overlays.sdr_overlay import SDROverlay, SDRTimeline
            self.sdr_overlay = SDROverlay()
            self.sdr_timeline = SDRTimeline(self.db_manager)
            logger.info("✅ SDROverlay initialisé")
            
            # 3. Service SDR (si fourni)
            if self.sdr_service:
                logger.info(f"✅ Service SDR attaché: {self.sdr_service.__class__.__name__}")
            
        except ImportError as e:
            logger.error(f"❌ Erreur import composants SDR: {e}")
            # Mode dégradé - créer des composants vides
            self.sdr_analyzer = None
            self.sdr_overlay = None
    
    def get_sdr_health_status(self) -> Dict[str, Any]:
        """Retourne le statut santé SDR"""
        components = {
            'analyzer': self.sdr_analyzer is not None,
            'overlay': self.sdr_overlay is not None,
            'service': self.sdr_service is not None,
            'timeline': self.sdr_timeline is not None
        }
        
        return {
            'status': 'healthy' if all(components.values()) else 'degraded',
            'components': components,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def process_realtime_scan(self, scan_data: List[Dict]) -> Dict[str, Any]:
        """
        Traite un scan SDR en temps réel
        
        Args:
            scan_data: Données de scan SDR
            
        Returns:
            Métriques et analyses
        """
        if not self.sdr_analyzer:
            return {
                'success': False,
                'error': 'Analyzer SDR non disponible',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        try:
            # Traiter les données
            zone_metrics = self.sdr_analyzer.process_scan_data(scan_data)
            
            # Générer le GeoJSON
            geojson = self.sdr_analyzer.get_geojson_overlay()
            
            # Préparer la réponse
            response = {
                'success': True,
                'metrics': {k: v.to_dict() for k, v in zone_metrics.items()},
                'geojson': geojson,
                'scans_processed': len(scan_data),
                'zones_analyzed': len(zone_metrics),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Détecter les alertes critiques
            critical_zones = []
            for zone_id, metrics in zone_metrics.items():
                if metrics.get_health_status().value in ['CRITICAL', 'HIGH_RISK']:
                    critical_zones.append({
                        'zone': zone_id,
                        'status': metrics.get_health_status().value,
                        'anomaly_score': metrics.anomaly_score
                    })
            
            if critical_zones:
                response['alerts'] = critical_zones
                self._trigger_sdr_alerts(critical_zones)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement scan: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_sdr_overlay_config(self) -> Dict[str, Any]:
        """Retourne la configuration de la couche SDR"""
        if not self.sdr_overlay:
            return {
                'enabled': False,
                'error': 'Overlay SDR non disponible'
            }
        
        return {
            'enabled': True,
            'name': self.sdr_overlay.name,
            'description': self.sdr_overlay.description,
            'visible': self.sdr_overlay.visible,
            'opacity': self.sdr_overlay.opacity,
            'legend': self.sdr_overlay.get_legend_html(),
            'geojson_endpoint': '/api/sdr/geojson',
            'timeline_endpoint': '/api/sdr/timeline'
        }
    
    def correlate_with_news(self, news_articles: List[Dict]) -> Dict[str, Any]:
        """
        Corrèle les données SDR avec des articles d'actualité
        
        Args:
            news_articles: Liste d'articles avec entités NER
            
        Returns:
            Corrélations détectées
        """
        if not self.sdr_analyzer:
            return {
                'success': False,
                'correlations': [],
                'message': 'Analyzer SDR non disponible'
            }
        
        try:
            # Extraire les entités de tous les articles
            all_entities = {
                'locations': [],
                'organizations': [],
                'persons': []
            }
            
            for article in news_articles:
                entities = article.get('entities', {})
                for key in all_entities.keys():
                    all_entities[key].extend(entities.get(key, []))
            
            # Éliminer les doublons
            for key in all_entities.keys():
                all_entities[key] = list(set(all_entities[key]))
            
            # Corréler avec SDR
            correlations = self.sdr_analyzer.correlate_with_ner_entities(all_entities)
            
            return {
                'success': True,
                'correlations': correlations,
                'articles_analyzed': len(news_articles),
                'entities_found': {k: len(v) for k, v in all_entities.items()}
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur corrélation news: {e}")
            return {
                'success': False,
                'error': str(e),
                'correlations': []
            }
    
    def _trigger_sdr_alerts(self, critical_zones: List[Dict]):
        """Déclenche des alertes SDR"""
        try:
            # Intégration avec le système d'alertes existant
            from .alerts import GeopolAlert, GeopolAlertsService
            
            # Créer des alertes pour chaque zone critique
            alerts_created = []
            
            for zone in critical_zones:
                alert_data = {
                    'name': f'Alerte SDR - Zone {zone["zone"]}',
                    'description': f'Statut SDR critique détecté: {zone["status"]}',
                    'country_code': 'ALLIANCE',  # Code spécial pour alliances
                    'indicator': 'sdr_anomaly_score',
                    'condition': '>',
                    'threshold': 60.0,
                    'actual_value': zone['anomaly_score']
                }
                
                # TODO: Envoyer à l'email service
                alerts_created.append(alert_data)
            
            if alerts_created:
                logger.warning(f"🚨 {len(alerts_created)} alertes SDR déclenchées")
                
        except ImportError:
            logger.warning("⚠️  Système d'alertes non disponible")
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement alertes: {e}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Données pour le dashboard SDR"""
        try:
            # Récupérer les dernières métriques
            latest_metrics = {}
            if self.sdr_analyzer:
                for zone_id in ['NATO', 'BRICS', 'MIDDLE_EAST']:
                    metrics = self.sdr_analyzer._get_latest_metrics(zone_id)
                    if metrics:
                        latest_metrics[zone_id] = metrics.to_dict()
            
            # Récupérer les anomalies récentes
            recent_anomalies = []
            try:
                conn = self.db_manager.get_connection()
                cur = conn.cursor()
                cur.execute("""
                    SELECT zone_id, anomaly_type, severity, timestamp 
                    FROM sdr_anomalies 
                    ORDER BY timestamp DESC 
                    LIMIT 10
                """)
                recent_anomalies = [
                    {'zone': row[0], 'type': row[1], 'severity': row[2], 'time': row[3]}
                    for row in cur.fetchall()
                ]
                conn.close()
            except:
                pass
            
            return {
                'success': True,
                'health_status': self.get_sdr_health_status(),
                'zone_metrics': latest_metrics,
                'recent_anomalies': recent_anomalies,
                'overlay_config': self.get_sdr_overlay_config(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur dashboard SDR: {e}")
            return {
                'success': False,
                'error': str(e),
                'health_status': self.get_sdr_health_status()
            }


# Fonction d'initialisation principale
def init_sdr_module(app, db_manager, sdr_service=None) -> Optional[SDRIntegrationManager]:
    """
    Initialise le module SDR complet
    
    Args:
        app: Application Flask
        db_manager: Gestionnaire de base de données
        sdr_service: Service SDR optionnel (ex: SDRSpectrumService)
        
    Returns:
        Instance de SDRIntegrationManager ou None si échec
    """
    try:
        logger.info("📡 Initialisation du module SDR...")
        
        # Créer le manager d'intégration
        sdr_manager = SDRIntegrationManager(app, db_manager, sdr_service)
        
        # Créer les routes API
        from .sdr_routes import create_sdr_api_blueprint
        sdr_bp = create_sdr_api_blueprint(db_manager, sdr_manager.sdr_analyzer, sdr_service)
        app.register_blueprint(sdr_bp)
        
        # Ajouter la couche aux overlays globaux
        if hasattr(app, 'geopol_overlays'):
            from .overlays.sdr_overlay import create_sdr_overlay_layer
            sdr_layer = create_sdr_overlay_layer(db_manager, sdr_manager.sdr_analyzer)
            app.geopol_overlays['sdr_health'] = sdr_layer
        
        logger.info("✅ Module SDR intégré avec succès")
        return sdr_manager
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation module SDR: {e}")
        import traceback
        traceback.print_exc()
        return None