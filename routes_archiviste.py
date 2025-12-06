# Flask/routes_archiviste.py - VERSION AVEC ANALYSE RÉELLE
from flask import Blueprint, jsonify, request, render_template
import logging

logger = logging.getLogger(__name__)

def create_archiviste_blueprint(db_manager, comparative_archiviste):
    """Crée le blueprint pour les routes Archiviste avec analyse comparative"""
    
    archiviste_bp = Blueprint('archiviste', __name__, url_prefix='/archiviste')
    
    @archiviste_bp.route('/')
    def archiviste_page():
        """Page principale Archiviste"""
        return render_template('archiviste.html')
    
    @archiviste_bp.route('/api/periods')
    def get_historical_periods():
        """Retourne les périodes historiques disponibles"""
        try:
            if hasattr(comparative_archiviste, 'historical_periods'):
                periods = comparative_archiviste.historical_periods
                return jsonify({
                    'success': True,
                    'periods': periods
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Archiviste non initialisé correctement'
                }), 500
        except Exception as e:
            logger.error(f"❌ Erreur get_historical_periods: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/themes')
    def get_archiviste_themes():
        """Retourne les thèmes disponibles avec IDs numériques"""
        try:
            themes = comparative_archiviste.get_available_themes()
            
            # S'assurer que les IDs sont numériques
            normalized_themes = []
            for theme in themes:
                normalized_themes.append({
                    'id': int(theme['id']) if isinstance(theme['id'], (int, str)) and str(theme['id']).isdigit() else theme['id'],
                    'name': theme['name'],
                    'keywords': theme['keywords'],
                    'description': theme.get('description', ''),
                    'color': theme.get('color', '#6366f1')
                })
            
            logger.info(f"✅ {len(normalized_themes)} thèmes retournés")
            
            return jsonify({
                'success': True,
                'themes': normalized_themes
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_archiviste_themes: {e}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/stats')
    def get_archiviste_stats():
        """Retourne les statistiques Archiviste"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Nombre d'analyses historiques
            cursor.execute("""
                SELECT COUNT(*) FROM archiviste_period_analyses
            """)
            total_analyses = cursor.fetchone()[0]
            
            # Nombre d'items archivés
            cursor.execute("""
                SELECT COUNT(*) FROM archiviste_items
            """)
            total_items = cursor.fetchone()[0]
            
            # Analyses récentes
            cursor.execute("""
                SELECT period_name, theme_id, items_analyzed, created_at
                FROM archiviste_period_analyses
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            recent_analyses = []
            for row in cursor.fetchall():
                recent_analyses.append({
                    'period_name': row[0],
                    'theme_id': row[1],
                    'items_analyzed': row[2],
                    'created_at': row[3]
                })
            
            conn.close()
            
            stats = {
                'total_analyses': total_analyses,
                'total_archived_items': total_items,
                'available_periods': len(comparative_archiviste.historical_periods),
                'available_themes': len(comparative_archiviste.get_available_themes()),
                'recent_analyses': recent_analyses
            }
            
            return jsonify({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_archiviste_stats: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/analyze-period', methods=['POST'])
    def analyze_historical_period():
        """
        Analyse comparative d'une période historique avec un thème
        VRAIE recherche et analyse sur Archive.org
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Données JSON requises'
                }), 400
            
            period_key = data.get('period_key')
            theme_id_raw = data.get('theme_id')
            max_items = data.get('max_items', 50)
            
            logger.info(f"📥 Requête d'analyse comparative: période={period_key}, thème={theme_id_raw}")
            
            # Validation
            if not period_key:
                return jsonify({
                    'success': False,
                    'error': 'period_key requis'
                }), 400
            
            if theme_id_raw is None:
                return jsonify({
                    'success': False,
                    'error': 'theme_id requis'
                }), 400
            
            # Convertir theme_id en entier
            try:
                theme_id = int(theme_id_raw)
                if theme_id <= 0:
                    raise ValueError("theme_id doit être positif")
            except (ValueError, TypeError) as e:
                logger.error(f"❌ Conversion theme_id échouée: {theme_id_raw}")
                return jsonify({
                    'success': False,
                    'error': f'theme_id invalide: {theme_id_raw}'
                }), 400
            
            logger.info(f"🎯 Lancement analyse comparative réelle - Période: {period_key}, Thème: {theme_id}")
            
            # Lancer l'analyse comparative RÉELLE
            result = comparative_archiviste.analyze_period_with_theme(
                period_key=period_key,
                theme_id=theme_id,
                max_items=max_items
            )
            
            # Logger le résultat
            if result.get('success'):
                logger.info(f"✅ Analyse réussie - {result.get('historical_items_analyzed', 0)} items historiques analysés")
            else:
                logger.warning(f"⚠️ Analyse échouée - {result.get('error', 'Erreur inconnue')}")
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur analyze_historical_period: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': f'Erreur serveur: {str(e)}'
            }), 500
    
    @archiviste_bp.route('/api/analysis-history')
    def get_analysis_history():
        """Récupère l'historique des analyses comparatives"""
        try:
            limit = int(request.args.get('limit', 20))
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    id,
                    period_key,
                    period_name,
                    theme_id,
                    total_items,
                    items_analyzed,
                    analysis_summary,
                    created_at
                FROM archiviste_period_analyses
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            analyses = []
            for row in cursor.fetchall():
                import json
                
                summary = {}
                if row[6]:
                    try:
                        summary = json.loads(row[6])
                    except:
                        pass
                
                analyses.append({
                    'id': row[0],
                    'period_key': row[1],
                    'period_name': row[2],
                    'theme_id': row[3],
                    'total_items': row[4],
                    'items_analyzed': row[5],
                    'summary': summary,
                    'created_at': row[7]
                })
            
            conn.close()
            
            return jsonify({
                'success': True,
                'analyses': analyses,
                'count': len(analyses)
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_analysis_history: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @archiviste_bp.route('/api/analysis-detail/<int:analysis_id>')
    def get_analysis_detail(analysis_id):
        """Récupère les détails d'une analyse spécifique"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT raw_data
                FROM archiviste_period_analyses
                WHERE id = ?
            """, (analysis_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row or not row[0]:
                return jsonify({
                    'success': False,
                    'error': 'Analyse non trouvée'
                }), 404
            
            import json
            analysis_data = json.loads(row[0])
            
            return jsonify({
                'success': True,
                'analysis': analysis_data
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_analysis_detail: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    logger.info("✅ Routes Archiviste avec analyse comparative enregistrées")
    return archiviste_bp
