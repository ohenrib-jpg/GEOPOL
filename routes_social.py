# Flask/routes_social.py
"""
Routes API pour l'agrégation et la comparaison des réseaux sociaux
"""

from flask import request, jsonify, render_template  
import logging
from datetime import datetime, timedelta
from .database import DatabaseManager
from .social_aggregator import get_social_aggregator
from .social_comparator import get_social_comparator

logger = logging.getLogger(__name__)

def register_social_routes(app, db_manager: DatabaseManager):
    """
    Enregistre les routes pour les réseaux sociaux
    """
    social_aggregator = get_social_aggregator(db_manager)
    social_comparator = get_social_comparator(db_manager)
    
    @app.route('/social')
    def social_page():
        """Page principale réseaux sociaux"""
        return render_template('social.html')

    # ============================================================
    # ROUTES D'AGRÉGATION
    # ============================================================

    @app.route('/api/social/fetch-posts', methods=['POST'])
    def fetch_social_posts():
        """
        Récupère et analyse les posts des réseaux sociaux
        """
        try:
            data = request.get_json() or {}
            days = int(data.get('days', 1))
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Récupérer les posts récents
            posts = social_aggregator.fetch_recent_posts(cutoff_date)
            
            if not posts:
                return jsonify({
                    'success': True,
                    'message': 'Aucun post récent trouvé',
                    'posts_count': 0
                })
            
            # Analyser le sentiment
            posts_with_sentiment = social_aggregator.analyze_social_sentiment(posts)
            
            # Sauvegarder en base
            saved_count = social_aggregator.save_social_posts(posts_with_sentiment)
            
            return jsonify({
                'success': True,
                'posts_count': len(posts_with_sentiment),
                'saved_count': saved_count,
                'posts': posts_with_sentiment[:50]  # Limite pour l'API
            })
            
        except Exception as e:
            logger.error(f"Erreur fetch social posts: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/social/top-themes', methods=['GET'])
    def get_top_emotion_themes():
        """
        Récupère les 5 thèmes émotionnels les plus discussés
        """
        try:
            days = int(request.args.get('days', 1))
            
            top_themes = social_aggregator.get_top_emotion_themes(days)
            
            return jsonify({
                'success': True,
                'themes': top_themes,
                'period_days': days
            })
            
        except Exception as e:
            logger.error(f"Erreur top themes: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/social/statistics', methods=['GET'])
    def get_social_statistics():
        """
        Récupère les statistiques des posts sociaux
        """
        try:
            days = int(request.args.get('days', 7))
            
            stats = social_aggregator.get_social_statistics(days)
            
            return jsonify({
                'success': True,
                'statistics': stats
            })
            
        except Exception as e:
            logger.error(f"Erreur social statistics: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/social/posts', methods=['GET'])
    def get_social_posts():
        """
        Récupère les posts sociaux avec filtres
        """
        try:
            limit = int(request.args.get('limit', 50))
            source_type = request.args.get('source_type')
            sentiment = request.args.get('sentiment')
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM social_posts WHERE 1=1"
            params = []
            
            if source_type and source_type != 'all':
                query += " AND source_type = ?"
                params.append(source_type)
            
            if sentiment and sentiment != 'all':
                query += " AND sentiment_type = ?"
                params.append(sentiment)
            
            query += " ORDER BY pub_date DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            posts = []
            for row in cursor.fetchall():
                posts.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'link': row[3],
                    'pub_date': row[4],
                    'source': row[5],
                    'source_type': row[6],
                    'author': row[7],
                    'sentiment_score': row[8],
                    'sentiment_type': row[9],
                    'sentiment_confidence': row[10],
                    'engagement': row[11]
                })
            
            conn.close()
            
            return jsonify({
                'success': True,
                'posts': posts
            })
            
        except Exception as e:
            logger.error(f"Erreur get social posts: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ============================================================
    # ROUTES DE COMPARAISON
    # ============================================================
    
    @app.route('/api/social/compare', methods=['POST'])
    def compare_rss_vs_social():
        """
        Compare les sentiments RSS vs réseaux sociaux
        """
        try:
            data = request.get_json() or {}
            days = int(data.get('days', 1))
            
            result = social_comparator.compare_rss_vs_social(days)
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Erreur comparison: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/social/comparison-history', methods=['GET'])
    def get_comparison_history():
        """
        Récupère l'historique des comparaisons
        """
        try:
            limit = int(request.args.get('limit', 20))
            
            history = social_comparator.get_comparison_history(limit)
            
            return jsonify({
                'success': True,
                'history': history
            })
            
        except Exception as e:
            logger.error(f"Erreur comparison history: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/social/compare/by-theme', methods=['POST'])
    def compare_by_theme():
        """
        Compare les sentiments par thème spécifique
        """
        try:
            data = request.get_json() or {}
            theme = data.get('theme')
            days = int(data.get('days', 1))
            
            if not theme:
                return jsonify({
                    'success': False,
                    'error': 'Thème requis'
                }), 400
            
            # Récupérer les articles RSS par thème
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute("""
                SELECT a.id, a.title, a.content, a.sentiment_score, a.sentiment_type
                FROM articles a
                JOIN theme_analyses ta ON a.id = ta.article_id
                WHERE ta.theme_id = ? AND ta.confidence >= 0.3 AND a.pub_date >= ?
                ORDER BY a.pub_date DESC
                LIMIT 100
            """, (theme, cutoff_date))
            
            rss_articles = []
            for row in cursor.fetchall():
                rss_articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'sentiment_score': row[3],
                    'sentiment_type': row[4]
                })
            
            # Récupérer les posts sociaux par thème
            cursor.execute("""
                SELECT id, title, content, sentiment_score, sentiment_type
                FROM social_posts
                WHERE pub_date >= ? AND (title LIKE ? OR content LIKE ?)
                ORDER BY pub_date DESC
                LIMIT 100
            """, (cutoff_date, f'%{theme}%', f'%{theme}%'))
            
            social_posts = []
            for row in cursor.fetchall():
                social_posts.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'sentiment_score': row[3],
                    'sentiment_type': row[4]
                })
            
            conn.close()
            
            # Comparaison
            if not rss_articles or not social_posts:
                return jsonify({
                    'success': False,
                    'error': 'Données insuffisantes pour le thème demandé',
                    'rss_count': len(rss_articles),
                    'social_count': len(social_posts)
                })
            
            # Utiliser la méthode de comparaison existante
            rss_analysis = social_comparator._analyze_sentiment_distribution(rss_articles, 'rss')
            social_analysis = social_comparator._analyze_sentiment_distribution(social_posts, 'social')
            divergence = social_comparator._calculate_divergence(rss_analysis, social_analysis)
            factor_z = social_comparator._calculate_factor_z(rss_analysis, social_analysis)
            
            return jsonify({
                'success': True,
                'theme': theme,
                'rss_count': len(rss_articles),
                'social_count': len(social_posts),
                'rss_analysis': rss_analysis,
                'social_analysis': social_analysis,
                'divergence': divergence,
                'factor_z': factor_z
            })
            
        except Exception as e:
            logger.error(f"Erreur compare by theme: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # ============================================================
    # NOUVELLES ROUTES POUR LA GESTION DES INSTANCES
    # ============================================================

    @app.route('/api/social/instances-status', methods=['GET'])
    def get_instances_status():
        """Statut des instances Nitter"""
        try:
            status = social_aggregator.get_instance_status()
            return jsonify({
                'success': True,
                'instances': status
            })
        except Exception as e:
            logger.error(f"Erreur statut instances: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/social/instances', methods=['POST'])
    def add_custom_instance():
        """Ajoute une instance personnalisée"""
        try:
            data = request.get_json()
            instance_url = data.get('url')
            
            if not instance_url:
                return jsonify({'success': False, 'error': 'URL requise'}), 400
            
            social_aggregator.add_custom_instance(instance_url)
            return jsonify({'success': True, 'message': f'Instance {instance_url} ajoutée'})
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/social/instances/<path:instance_url>', methods=['DELETE'])
    def remove_instance(instance_url):
        """Supprime une instance"""
        try:
            social_aggregator.remove_instance(instance_url)
            return jsonify({'success': True, 'message': f'Instance {instance_url} supprimée'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/social/reset-blacklist', methods=['POST'])
    def reset_blacklist():
        """Réinitialise la blacklist"""
        try:
            social_aggregator.reset_blacklist()
            return jsonify({'success': True, 'message': 'Blacklist réinitialisée'})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    logger.info("✅ Routes réseaux sociaux enregistrées")