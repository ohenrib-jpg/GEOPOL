# Flask/geopol_data/routes.py - VERSION CORRIGÉE

"""
Routes pour le module Geopol-Data
API REST pour accéder aux données géopolitiques par pays
"""

from flask import Blueprint, jsonify, request, render_template
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

def create_geopol_data_blueprint(db_manager, data_service):
    """
    Crée le blueprint Flask pour les routes Geopol-Data
    
    CORRECTION: Retourne TOUJOURS un Blueprint, jamais None
    
    Args:
        db_manager: Instance du DatabaseManager
        data_service: Instance du DataService
    
    Returns:
        Blueprint Flask (JAMAIS None)
    """
    
    # ============================================================
    # CRÉER LE BLUEPRINT
    # ============================================================
    
    bp = Blueprint('geopol_data_api', __name__, url_prefix='/api/geopol')
    
    logger.info("🔧 Création blueprint geopol_data_api...")
    
    # ============================================================
    # VALIDATION DES SERVICES
    # ============================================================
    
    if data_service is None:
        logger.error("❌ DataService est None - Routes en mode dégradé")
        # MAIS ON RETOURNE QUAND MÊME LE BLUEPRINT
        
        @bp.route('/health')
        def health_degraded():
            return jsonify({
                'status': 'degraded',
                'error': 'DataService non initialisé'
            }), 503
        
        # ⚠️ IMPORTANT: Retourner le blueprint même en mode dégradé
        logger.warning("⚠️ Blueprint créé en mode dégradé (DataService manquant)")
        return bp
    
    # ============================================================
    # ROUTES API STANDARD
    # ============================================================
    
    @bp.route('/country/<country_code>')
    def get_country_data(country_code: str):
        """Récupère les données d'un pays par son code ISO"""
        try:
            logger.info(f"API Request - Country data for {country_code.upper()}")
            
            snapshot = data_service.get_country_snapshot(country_code.upper())
            
            if snapshot:
                return jsonify({
                    'success': True,
                    'snapshot': snapshot.to_dict(include_raw=False)
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': f'Aucune donnée disponible pour {country_code.upper()}'
                }), 404
                
        except Exception as e:
            logger.error(f"Erreur API /country/{country_code}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/countries')
    def get_multiple_countries():
        """Récupère les données de plusieurs pays"""
        try:
            codes_param = request.args.get('codes', '')
            if not codes_param:
                return jsonify({
                    'success': False,
                    'error': 'Paramètre "codes" requis (ex: ?codes=FR,US,DE)'
                }), 400
            
            country_codes = [code.strip().upper() for code in codes_param.split(',')]
            snapshots = data_service.get_multiple_snapshots(country_codes)
            
            result = {
                code: snapshot.to_dict(include_raw=False)
                for code, snapshot in snapshots.items()
            }
            
            return jsonify({
                'success': True,
                'data': result,
                'requested': len(country_codes),
                'found': len(result)
            }), 200
            
        except Exception as e:
            logger.error(f"Erreur API /countries: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/status')
    def get_service_status():
        """Récupère le statut du service Geopol-Data"""
        try:
            status = data_service.get_service_status()
            return jsonify(status), 200
        except Exception as e:
            logger.error(f"Erreur API /status: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/health')
    def health_check():
        """Vérification de santé du module"""
        return jsonify({
            'status': 'ok',
            'module': 'geopol_data',
            'data_service': 'initialized',
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }), 200
    
    # ============================================================
    # ROUTES TEMPLATES
    # ============================================================
    
    @bp.route('/map')
    def geopol_map_page():
        """Page HTML interactive de la carte géopolitique"""
        try:
            return render_template('geopol_data_map.html')
        except Exception as e:
            logger.error(f"Erreur chargement template: {e}")
            # Fallback HTML simple
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Carte Géopolitique - GEOPOL</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 2rem; background: #1e293b; color: #e2e8f0; }
                    .container { max-width: 800px; margin: 0 auto; }
                    h1 { color: #f59e0b; }
                    .api-links { display: flex; gap: 1rem; margin: 2rem 0; }
                    .api-link { padding: 1rem; background: #3b82f6; color: white; text-decoration: none; border-radius: 5px; }
                    .api-link:hover { background: #2563eb; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🌍 Carte Géopolitique</h1>
                    <p>Le module de carte est en cours de chargement. Vous pouvez utiliser l'API en attendant :</p>
                    
                    <div class="api-links">
                        <a href="/api/geopol/country/FR" class="api-link">Données France</a>
                        <a href="/api/geopol/status" class="api-link">Statut du service</a>
                        <a href="/api/geopol/health" class="api-link">Santé du module</a>
                    </div>
                    
                    <h2>Endpoints disponibles :</h2>
                    <ul>
                        <li><code>GET /api/geopol/country/&lt;code&gt;</code> - Données d'un pays</li>
                        <li><code>GET /api/geopol/countries?codes=FR,US,DE</code> - Données multiples</li>
                        <li><code>GET /api/geopol/status</code> - Statut du service</li>
                        <li><code>GET /api/geopol/health</code> - Santé du module</li>
                    </ul>
                </div>
            </body>
            </html>
            ''', 200
    
    # ============================================================
    # ROUTES UTILITAIRES
    # ============================================================
    
    @bp.route('/cache/stats')
    def get_cache_stats():
        """Récupère les statistiques du cache"""
        try:
            stats = data_service.get_cache_stats()
            return jsonify(stats), 200
        except Exception as e:
            logger.error(f"Erreur API /cache/stats: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/cache/clear', methods=['POST'])
    def clear_cache():
        """Vide le cache du service"""
        try:
            data_service.clear_cache()
            return jsonify({
                'success': True,
                'message': 'Cache vidé avec succès'
            }), 200
        except Exception as e:
            logger.error(f"Erreur API /cache/clear: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ============================================================
    # RETOUR DU BLUEPRINT (CRITIQUE)
    # ============================================================
    
    logger.info(f"✅ Blueprint '{bp.name}' créé avec succès")
    
    # ⚠️ LIGNE CRITIQUE: TOUJOURS retourner le blueprint
    return bp  # ← VÉRIFIER QUE CETTE LIGNE EST BIEN LÀ


# ============================================================
# FONCTION D'ENREGISTREMENT DES ROUTES MÉTÉO (OPTIONNEL)
# ============================================================

def register_weather_routes(bp, data_service):
    """
    Enregistre les routes météo sur le blueprint existant
    (Voir artifact weather_routes pour l'implémentation complète)
    """
    logger.info("🌦️ Enregistrement routes météo...")
    
    try:
        from .connectors.open_meteo import OpenMeteoConnector
        from .overlays.weather_overlay import WeatherOverlay
        
        # Initialiser les services météo
        weather_connector = OpenMeteoConnector()
        weather_overlay = WeatherOverlay()
        
        # Route de test simple
        @bp.route('/weather/test')
        def test_weather():
            try:
                is_connected = weather_connector.test_connection()
                return jsonify({
                    'success': True,
                    'status': 'connected' if is_connected else 'disconnected'
                }), 200
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        logger.info("✅ Routes météo enregistrées")
        
    except ImportError as e:
        logger.warning(f"⚠️ Module météo non disponible: {e}")
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement routes météo: {e}")


# ============================================================
# VALIDATION AU CHARGEMENT DU MODULE
# ============================================================

logger.info("✅ Module routes.py chargé")