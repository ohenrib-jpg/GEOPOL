"""
Routes API pour l'intégration Open-Meteo
"""

from flask import Blueprint, jsonify, request, current_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_open_meteo_blueprint(meteo_integration):
    """Crée le blueprint API pour Open-Meteo"""
    
    bp = Blueprint('open_meteo_api', __name__, url_prefix='/api/weather')
    
    @bp.route('/health', methods=['GET'])
    def get_health():
        """Vérification de santé du service Open-Meteo"""
        try:
            status = meteo_integration.get_health_status()
            return jsonify(status), 200
        except Exception as e:
            logger.error(f"❌ Erreur health Open-Meteo: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/country/<country_code>', methods=['GET'])
    def get_country_weather(country_code: str):
        """Récupère les données météo d'un pays"""
        try:
            data = meteo_integration.fetch_country_weather(country_code)
            
            if data:
                return jsonify({
                    'success': True,
                    'data': data,
                    'timestamp': datetime.utcnow().isoformat()
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': f'Données météo non disponibles pour {country_code}'
                }), 404
                
        except Exception as e:
            logger.error(f"❌ Erreur météo pays {country_code}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/countries', methods=['POST'])
    def get_multiple_countries_weather():
        """Récupère les données météo de plusieurs pays"""
        try:
            data = request.get_json()
            country_codes = data.get('country_codes', [])
            
            if not country_codes:
                return jsonify({
                    'success': False,
                    'error': 'Paramètre country_codes requis'
                }), 400
            
            result = meteo_integration.fetch_multiple_countries(country_codes)
            
            return jsonify({
                'success': result['success'],
                'data': result,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
                
        except Exception as e:
            logger.error(f"❌ Erreur météo multiples pays: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/layers', methods=['GET'])
    def get_all_layers():
        """Récupère toutes les couches météo"""
        try:
            layers = meteo_integration.get_all_layers()
            
            return jsonify({
                'success': True,
                'layers': layers,
                'count': len(layers),
                'timestamp': datetime.utcnow().isoformat()
            }), 200
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération couches: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/layer/<layer_id>', methods=['GET'])
    def get_layer_data(layer_id: str):
        """Récupère les données d'une couche spécifique"""
        try:
            # Liste statique des pays prioritaires pour éviter les problèmes d'import
            priority_countries = [
                'FR', 'US', 'GB', 'DE', 'CN', 'JP', 'RU', 'IN', 'BR', 'CA',
                'IT', 'ES', 'KR', 'AU', 'MX', 'TR', 'SA', 'ID', 'NL', 'SE'
            ]

            # Limiter le nombre de pays pour ne pas surcharger l'API
            country_codes = priority_countries[:15]

            logger.info(f"Récupération données météo pour {len(country_codes)} pays...")

            # Télécharger les données
            countries_data = []
            for code in country_codes:
                try:
                    data = meteo_integration.fetch_country_weather(code)
                    if data:
                        countries_data.append(data)
                except Exception as e:
                    logger.warning(f"Erreur données {code}: {e}")
                    continue

            logger.info(f"Données récupérées pour {len(countries_data)} pays")

            # Générer le GeoJSON
            geojson = meteo_integration.generate_geojson_layer(layer_id, countries_data)

            # Récupérer la configuration de la couche
            layer_config = meteo_integration.get_layer(layer_id)

            return jsonify({
                'success': True,
                'layer_id': layer_id,
                'layer_config': layer_config,
                'geojson': geojson,
                'countries_processed': len(countries_data),
                'timestamp': datetime.utcnow().isoformat()
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur couche {layer_id}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 500
    
    @bp.route('/layer/<layer_id>/toggle', methods=['POST'])
    def toggle_layer(layer_id: str):
        """Active/désactive une couche"""
        try:
            data = request.get_json() or {}
            visible = data.get('visible')
            
            success = meteo_integration.toggle_layer(layer_id, visible)
            
            if success:
                return jsonify({
                    'success': True,
                    'layer_id': layer_id,
                    'visible': meteo_integration.layers[layer_id].visible if layer_id in meteo_integration.layers else False,
                    'message': f'Couche {layer_id} mise à jour'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': f'Couche {layer_id} non trouvée'
                }), 404
                
        except Exception as e:
            logger.error(f"❌ Erreur toggle couche {layer_id}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/layer/<layer_id>/opacity', methods=['POST'])
    def set_layer_opacity(layer_id: str):
        """Modifie l'opacité d'une couche"""
        try:
            data = request.get_json()
            opacity = data.get('opacity')
            
            if opacity is None:
                return jsonify({
                    'success': False,
                    'error': 'Paramètre opacity requis'
                }), 400
            
            success = meteo_integration.set_layer_opacity(layer_id, float(opacity))
            
            if success:
                return jsonify({
                    'success': True,
                    'layer_id': layer_id,
                    'opacity': float(opacity),
                    'message': f'Opacité couche {layer_id} mise à jour'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': f'Couche {layer_id} non trouvée'
                }), 404
                
        except Exception as e:
            logger.error(f"❌ Erreur opacité couche {layer_id}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/control-panel', methods=['GET'])
    def get_control_panel():
        """Récupère la configuration du panneau de contrôle"""
        try:
            config = meteo_integration.get_control_panel_config()
            
            return jsonify({
                'success': True,
                'control_panel': config,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
                
        except Exception as e:
            logger.error(f"❌ Erreur panneau de contrôle: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/cache/clear', methods=['POST'])
    def clear_cache():
        """Vide le cache des données météo"""
        try:
            meteo_integration.clear_cache()
            
            return jsonify({
                'success': True,
                'message': 'Cache Open-Meteo vidé',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
                
        except Exception as e:
            logger.error(f"❌ Erreur vidage cache: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/preload', methods=['POST'])
    def preload_countries():
        """Pré-charge les données météo"""
        try:
            data = request.get_json() or {}
            country_codes = data.get('country_codes')
            
            if country_codes:
                meteo_integration.preload_priority_countries(country_codes)
            else:
                meteo_integration.preload_priority_countries()
            
            return jsonify({
                'success': True,
                'message': 'Pré-chargement terminé',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
                
        except Exception as e:
            logger.error(f"❌ Erreur pré-chargement: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return bp