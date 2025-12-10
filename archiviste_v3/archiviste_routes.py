"""
Routes Flask pour Archiviste v3.0
"""

from flask import Blueprint, jsonify, request, render_template
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def create_archiviste_v3_blueprint(service) -> Blueprint:
    """Crée le blueprint Flask pour Archiviste v3"""
    
    archiviste_bp = Blueprint('archiviste_v3', __name__, url_prefix='/archiviste-v3')
    
    @archiviste_bp.route('/')
    def archiviste_home():
        """Page d'accueil Archiviste v3"""
        return render_template('archiviste_v3.html')
    
    @archiviste_bp.route('/api/periods')
    def get_periods():
        """Retourne les périodes historiques disponibles"""
        try:
            periods = service.get_available_periods()
            return jsonify({
                'success': True,
                'periods': periods
            })
        except Exception as e:
            logger.error(f"❌ Erreur get_periods: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/period-context/<period_key>')
    def get_period_context(period_key):
        """Retourne le contexte d'une période"""
        try:
            context = service.get_period_context(period_key)
            if context:
                return jsonify({
                    'success': True,
                    'context': context
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Période {period_key} non trouvée'
                }), 404
        except Exception as e:
            logger.error(f"❌ Erreur get_period_context: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/analyze-period', methods=['POST'])
    def analyze_period():
        """Analyse une période historique avec un thème"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'Données requises'}), 400
            
            period_key = data.get('period_key')
            theme_id = data.get('theme_id')
            max_items = data.get('max_items', 50)
            
            if not period_key or not theme_id:
                return jsonify({
                    'success': False,
                    'error': 'period_key et theme_id requis'
                }), 400
            
            # Lancer l'analyse
            result = service.analyze_period_with_theme(period_key, theme_id, max_items)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur analyze_period: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/vector-search', methods=['POST'])
    def vector_search():
        """Recherche vectorielle avec SpaCy"""
        try:
            data = request.get_json()
            query_text = data.get('query', '')
            limit = data.get('limit', 10)
            
            if not query_text:
                return jsonify({'success': False, 'error': 'Query requis'}), 400
            
            result = service.vector_search(query_text, limit)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur vector_search: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/historical-analogies', methods=['POST'])
    def get_historical_analogies():
        """Génère des analogies historiques"""
        try:
            data = request.get_json()
            current_text = data.get('current_text', '')
            threshold = data.get('threshold', 0.7)
            max_results = data.get('max_results', 5)
            
            if not current_text:
                return jsonify({'success': False, 'error': 'Texte requis'}), 400
            
            result = service.get_historical_analogies(current_text, threshold, max_results)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur historical_analogies: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/status')
    def get_status():
        """Retourne le statut du service Archiviste"""
        try:
            status = service.get_service_status()
            return jsonify({
                'success': True,
                'status': status
            })
        except Exception as e:
            logger.error(f"❌ Erreur get_status: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/session-stats')
    def get_session_stats():
        """Retourne les statistiques de session"""
        try:
            stats = service.get_session_statistics()
            return jsonify({
                'success': True,
                'stats': stats
            })
        except Exception as e:
            logger.error(f"❌ Erreur get_session_stats: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/analyses-history')
    def get_analyses_history():
        """Retourne l'historique des analyses"""
        try:
            limit = int(request.args.get('limit', 20))
            analyses = []
            if hasattr(service, 'database') and service.database:
                analyses = service.database.get_period_analyses(limit)
            return jsonify({
                'success': True,
                'analyses': analyses,
                'count': len(analyses)
            })
        except Exception as e:
            logger.error(f"❌ Erreur analyses_history: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/clear-cache', methods=['POST'])
    def clear_cache():
        """Vide le cache"""
        try:
            cleared = service.clear_cache()
            return jsonify({
                'success': True,
                'message': f'Cache vidé ({cleared} entrées supprimées)'
            })
        except Exception as e:
            logger.error(f"❌ Erreur clear_cache: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/test')
    def test_api():
        """Route de test"""
        return jsonify({
            'success': True,
            'message': 'Archiviste v3 API fonctionne',
            'version': '3.0',
            'endpoints': [
                '/api/periods',
                '/api/analyze-period',
                '/api/vector-search',
                '/api/historical-analogies',
                '/api/status'
            ]
        })
    
    logger.info("✅ Routes Archiviste v3 enregistrées")
    return archiviste_bp