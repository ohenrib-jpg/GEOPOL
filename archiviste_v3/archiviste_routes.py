"""
Routes Archiviste v3 - VERSION CORRIGÉE
"""

from flask import Blueprint, jsonify, request, render_template
import logging

logger = logging.getLogger(__name__)

def create_archiviste_v3_blueprint(service) -> Blueprint:
    """Crée le blueprint Flask pour Archiviste v3 - VERSION CORRIGÉE"""
    
    archiviste_bp = Blueprint('archiviste_v3', __name__)
    
    # ===== ROUTES =====
    
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
    
    @archiviste_bp.route('/api/analyze-period', methods=['POST'])
    def analyze_period():
        """Analyse une période historique avec un thème"""
        try:
            # Récupérer données
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            if not data:
                return jsonify({'success': False, 'error': 'Données requises'}), 400
            
            period_key = data.get('period_key')
            theme_id_raw = data.get('theme_id')
            max_items = data.get('max_items', 50)
            
            if not period_key:
                return jsonify({'success': False, 'error': 'period_key requis'}), 400
            
            if not theme_id_raw:
                return jsonify({'success': False, 'error': 'theme_id requis'}), 400
            
            # Conversion du theme_id
            try:
                theme_id = int(theme_id_raw)
            except (ValueError, TypeError):
                # Essayer de résoudre par nom
                theme_info = service.get_theme_by_name(str(theme_id_raw))
                if theme_info:
                    theme_id = theme_info['id']
                    logger.info(f"✅ Thème résolu: {theme_id_raw} -> ID {theme_id}")
                else:
                    return jsonify({
                        'success': False,
                        'error': f'theme_id invalide: {theme_id_raw}'
                    }), 400
            
            # Conversion max_items
            try:
                max_items = int(max_items) if max_items else 50
            except (ValueError, TypeError):
                max_items = 50
            
            logger.info(f"🎯 Requête: period={period_key}, theme_id={theme_id}, max={max_items}")
            
            # Lancer l'analyse
            result = service.analyze_period_with_theme(period_key, theme_id, max_items)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur analyze_period: {e}", exc_info=True)
            return jsonify({
                'success': False, 
                'error': f'Erreur serveur: {str(e)}'
            }), 500
    
    @archiviste_bp.route('/api/status')
    def get_status():
        """Retourne le statut du service"""
        try:
            status = service.get_service_status()
            return jsonify({
                'success': True,
                'status': status
            })
        except Exception as e:
            logger.error(f"❌ Erreur get_status: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/analyses-history')
    def get_analyses_history():
        """Retourne l'historique des analyses"""
        try:
            limit = request.args.get('limit', 20)
            try:
                limit = int(limit)
            except:
                limit = 20
            
            analyses = service.get_search_history(limit)
            
            return jsonify({
                'success': True,
                'analyses': analyses,
                'count': len(analyses)
            })
        except Exception as e:
            logger.error(f"❌ Erreur analyses_history: {e}", exc_info=True)
            return jsonify({
                'success': False, 
                'error': f'Erreur serveur: {str(e)}'
            }), 500
    
    @archiviste_bp.route('/api/test-gallica')
    def test_gallica():
        """Test direct de Gallica"""
        try:
            if not hasattr(service, 'gallica_client') or not service.gallica_client:
                return jsonify({'success': False, 'error': 'Gallica client non disponible'})
            
            # Test simple
            results = service.gallica_client.search(
                query="diplomatie",
                start_year=1950,
                end_year=1960,
                max_results=10,
                doc_type='monograph'
            )
            
            return jsonify({
                'success': True,
                'results_count': len(results),
                'results': results[:3],
                'test_query': 'diplomatie 1950-1960'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/test')
    def test_api():
        """Route de test simple"""
        return jsonify({
            'success': True,
            'message': 'Archiviste v3 API fonctionne',
            'version': '3.0-multi-source',
            'features': ['Archive.org', 'Gallica BnF', 'Recherche vectorielle']
        })
    
    logger.info("✅ Routes Archiviste v3 enregistrées")
    return archiviste_bp  