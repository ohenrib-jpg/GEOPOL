"""
Routes API pour l'intégration USGS Earthquake
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_earthquake_blueprint(earthquake_integration):
    """Crée le blueprint API pour Earthquakes"""

    bp = Blueprint('earthquake_api', __name__, url_prefix='/api/earthquakes')

    @bp.route('/health', methods=['GET'])
    def get_health():
        """Vérification de santé du service USGS"""
        try:
            status = earthquake_integration.get_health_status()
            return jsonify(status), 200
        except Exception as e:
            logger.error(f"❌ Erreur health USGS: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/config', methods=['GET'])
    def get_config():
        """Récupère la configuration de la couche sismique"""
        try:
            config = earthquake_integration.get_layer_config()
            return jsonify({
                'success': True,
                'config': config,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        except Exception as e:
            logger.error(f"❌ Erreur config: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/config', methods=['POST'])
    def update_config():
        """Met à jour la configuration de la couche"""
        try:
            data = request.get_json() or {}

            min_magnitude = data.get('min_magnitude')
            time_period = data.get('time_period')
            max_results = data.get('max_results')

            changed = earthquake_integration.update_layer_config(
                min_magnitude=min_magnitude,
                time_period=time_period,
                max_results=max_results
            )

            config = earthquake_integration.get_layer_config()

            return jsonify({
                'success': True,
                'changed': changed,
                'config': config,
                'message': 'Configuration mise à jour' if changed else 'Aucun changement'
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur update config: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/data', methods=['GET'])
    def get_earthquakes_data():
        """Récupère les données sismiques brutes"""
        try:
            earthquakes = earthquake_integration.fetch_earthquakes()

            earthquakes_data = [eq.to_dict() for eq in earthquakes]

            return jsonify({
                'success': True,
                'earthquakes': earthquakes_data,
                'count': len(earthquakes_data),
                'timestamp': datetime.utcnow().isoformat()
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur données séismes: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/geojson', methods=['GET'])
    def get_earthquakes_geojson():
        """Récupère les données sismiques en format GeoJSON"""
        try:
            # Récupérer les paramètres optionnels
            min_magnitude = request.args.get('min_magnitude', type=float)
            time_period = request.args.get('time_period', type=str)
            max_results = request.args.get('max_results', type=int)

            # Mettre à jour la configuration si des paramètres sont fournis
            if min_magnitude is not None or time_period is not None or max_results is not None:
                earthquake_integration.update_layer_config(
                    min_magnitude=min_magnitude,
                    time_period=time_period,
                    max_results=max_results
                )

            geojson = earthquake_integration.generate_geojson()

            return jsonify({
                'success': True,
                'geojson': geojson,
                'count': len(geojson['features']),
                'config': {
                    'min_magnitude': earthquake_integration.layer.min_magnitude,
                    'time_period': earthquake_integration.layer.time_period,
                    'max_results': earthquake_integration.layer.max_results
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur GeoJSON séismes: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 500

    @bp.route('/statistics', methods=['GET'])
    def get_statistics():
        """Récupère les statistiques sur les séismes"""
        try:
            stats = earthquake_integration.get_statistics()

            return jsonify({
                'success': True,
                'statistics': stats,
                'timestamp': datetime.utcnow().isoformat()
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur statistiques: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/toggle', methods=['POST'])
    def toggle_layer():
        """Active/désactive la couche sismique"""
        try:
            data = request.get_json() or {}
            visible = data.get('visible')

            success = earthquake_integration.toggle_layer(visible)

            return jsonify({
                'success': success,
                'visible': earthquake_integration.layer.visible,
                'message': f'Couche séismes {"activée" if earthquake_integration.layer.visible else "désactivée"}'
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur toggle: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/opacity', methods=['POST'])
    def set_opacity():
        """Modifie l'opacité de la couche"""
        try:
            data = request.get_json() or {}
            opacity = data.get('opacity')

            if opacity is None:
                return jsonify({
                    'success': False,
                    'error': 'Paramètre opacity requis'
                }), 400

            success = earthquake_integration.set_layer_opacity(float(opacity))

            return jsonify({
                'success': success,
                'opacity': earthquake_integration.layer.opacity,
                'message': f'Opacité mise à jour: {earthquake_integration.layer.opacity}'
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur opacité: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/cache/clear', methods=['POST'])
    def clear_cache():
        """Vide le cache des données sismiques"""
        try:
            earthquake_integration.clear_cache()

            return jsonify({
                'success': True,
                'message': 'Cache séismes vidé',
                'timestamp': datetime.utcnow().isoformat()
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur vidage cache: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return bp
