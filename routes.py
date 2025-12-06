# Flask/routes.py - VERSION COMPLÈTEMENT CORRIGÉE

from flask import Flask, render_template, request, jsonify, send_file, Response
from datetime import datetime, timedelta
import json
import logging
import csv
from io import StringIO, BytesIO
from xhtml2pdf import pisa
import tempfile
import sqlite3
import os
from .database import DatabaseManager
from .theme_manager import ThemeManager
from .theme_analyzer import ThemeAnalyzer
from .rss_manager import RSSManager
from .llama_client import LlamaClient

# AJOUT DES IMPORTS MANQUANTS
from .sentiment_analyzer import SentimentAnalyzer
from .corroboration_engine import CorroborationEngine
from .bayesian_analyzer import BayesianSentimentAnalyzer
from .batch_sentiment_analyzer import create_batch_analyzer

logger = logging.getLogger(__name__)

def register_routes(app: Flask, db_manager: DatabaseManager, theme_manager: ThemeManager,
                    theme_analyzer: ThemeAnalyzer, rss_manager: RSSManager, 
                    advanced_theme_manager=None, llama_client: LlamaClient = None,
                    sentiment_analyzer=None, batch_analyzer=None):  # AJOUT DES NOUVEAUX PARAMÈTRES
    """Enregistre toutes les routes de l'application"""

    # Si advanced_theme_manager n'est pas fourni, créer une instance
    if advanced_theme_manager is None:
        from .theme_manager_advanced import AdvancedThemeManager
        advanced_theme_manager = AdvancedThemeManager(db_manager)

    # 🆕 UTILISER LES COMPOSANTS D'ANALYSE BATCH EXISTANTS
    logger.info("🚀 Initialisation du système d'analyse batch cohérente...")
    
    # Si les analyseurs ne sont pas fournis, les créer
    if sentiment_analyzer is None:
        sentiment_analyzer = SentimentAnalyzer()
    
    if batch_analyzer is None:
        corroboration_engine = CorroborationEngine()
        bayesian_analyzer = BayesianSentimentAnalyzer()
        batch_analyzer = create_batch_analyzer(
            sentiment_analyzer,
            corroboration_engine,
            bayesian_analyzer
        )
    
    logger.info("✅ Analyseur batch initialisé avec succès")
    
    # ===== ROUTES PRINCIPALES =====
    @app.route('/')
    def index():
        """Page principale"""
        return render_template('index.html')

    @app.route('/dashboard')
    def dashboard():
        """Tableau de bord avec statistiques"""
        return render_template('dashboard.html')

    @app.route('/ia-analysis')
    def ia_analysis():
        """Page d'analyse IA"""
        return render_template('ia_analysis.html')

    # ===== API ROUTES - THÈMES =====
    @app.route('/api/themes', methods=['GET'])
    def get_themes():
        """Récupère tous les thèmes"""
        try:
            themes = theme_manager.get_all_themes()
            return jsonify({'themes': themes})
        except Exception as e:
            logger.error(f"Erreur récupération thèmes: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes', methods=['POST'])
    def create_theme():
        """Crée un nouveau thème"""
        try:
            data = request.get_json()
            theme_id = data.get('id')
            name = data.get('name')
            keywords = data.get('keywords', [])
            color = data.get('color', '#6366f1')
            description = data.get('description', '')

            if not theme_id or not name:
                return jsonify({'error': 'ID et nom requis'}), 400

            success = theme_manager.create_theme(theme_id, name, keywords, color, description)

            if success:
                return jsonify({'message': 'Thème créé avec succès'})
            else:
                return jsonify({'error': 'Erreur création thème'}), 500

        except Exception as e:
            logger.error(f"Erreur création thème: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>', methods=['PUT'])
    def update_theme(theme_id):
        """Met à jour un thème"""
        try:
            data = request.get_json()
            success = theme_manager.update_theme(
                theme_id,
                name=data.get('name'),
                keywords=data.get('keywords'),
                color=data.get('color'),
                description=data.get('description')
            )

            if success:
                theme_analyzer.clear_cache()
                return jsonify({'message': 'Thème mis à jour avec succès'})
            else:
                return jsonify({'error': 'Thème non trouvé'}), 404

        except Exception as e:
            logger.error(f"Erreur mise à jour thème: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>', methods=['DELETE'])
    def delete_theme(theme_id):
        """Supprime un thème"""
        try:
            success = theme_manager.delete_theme(theme_id)

            if success:
                return jsonify({'message': 'Thème supprimé avec succès'})
            else:
                return jsonify({'error': 'Erreur suppression thème'}), 500

        except Exception as e:
            logger.error(f"Erreur suppression thème: {e}")
            return jsonify({'error': str(e)}), 500

    # ===== API ROUTES - ARTICLES =====
    @app.route('/api/articles')
    def get_articles():
        """Récupère les articles avec filtres"""
        try:
            theme = request.args.get('theme')
            sentiment = request.args.get('sentiment')
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))

            conn = db_manager.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT a.id, a.title, a.content, a.link, a.pub_date, 
                       a.sentiment_type, a.sentiment_score, a.feed_url,
                       a.detailed_sentiment, a.roberta_score
                FROM articles a
            """
            params = []

            if theme:
                query += """
                    JOIN theme_analyses ta ON a.id = ta.article_id
                    JOIN themes t ON ta.theme_id = t.id
                    WHERE t.id = ? AND ta.confidence >= 0.3
                """
                params.append(theme)
            else:
                query += " WHERE 1=1"

            if sentiment and sentiment != 'all':
                if sentiment in ['positive', 'negative', 'neutral_positive', 'neutral_negative']:
                    query += " AND a.detailed_sentiment = ?"
                else:
                    query += " AND a.sentiment_type = ?"
                params.append(sentiment)

            query += " ORDER BY a.pub_date DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            articles = []

            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2][:200] + '...' if row[2] and len(row[2]) > 200 else row[2],
                    'link': row[3],
                    'pub_date': row[4],
                    'sentiment': row[5],
                    'sentiment_score': row[6],
                    'feed_url': row[7],
                    'detailed_sentiment': row[8],
                    'roberta_score': row[9]
                })

            conn.close()
            return jsonify({'articles': articles})

        except Exception as e:
            logger.error(f"Erreur récupération articles: {e}")
            return jsonify({'error': str(e)}), 500

    # ===== API ROUTES - STATISTIQUES =====
    @app.route('/api/stats')
    def get_stats():
        """Récupère les statistiques avec les 4 catégories de sentiment"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            # 1. Compter les articles par catégorie détaillée
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN detailed_sentiment = 'positive' THEN 1 END) as positive,
                    COUNT(CASE WHEN detailed_sentiment = 'neutral_positive' THEN 1 END) as neutral_positive, 
                    COUNT(CASE WHEN detailed_sentiment = 'neutral_negative' THEN 1 END) as neutral_negative,
                    COUNT(CASE WHEN detailed_sentiment = 'negative' THEN 1 END) as negative,
                    COUNT(CASE WHEN detailed_sentiment IS NULL AND sentiment_type = 'positive' THEN 1 END) as legacy_positive,
                    COUNT(CASE WHEN detailed_sentiment IS NULL AND sentiment_type = 'negative' THEN 1 END) as legacy_negative,
                    COUNT(CASE WHEN detailed_sentiment IS NULL AND sentiment_type = 'neutral' THEN 1 END) as legacy_neutral,
                    COUNT(*) as total
                FROM articles
            """)
            
            row = cursor.fetchone()
            
            # 2. Combiner données RoBERTa (nouvelles) et données legacy (anciennes)
            positive_count = (row[0] or 0) + (row[4] or 0)
            neutral_positive_count = (row[1] or 0) + (row[6] or 0) // 2
            neutral_negative_count = (row[2] or 0) + (row[6] or 0) - ((row[6] or 0) // 2)
            negative_count = (row[3] or 0) + (row[5] or 0)
            
            total_articles = row[7] or 0
            
            # 3. Distribution des sentiments (4 catégories)
            sentiment_distribution = {
                'positive': positive_count,
                'neutral_positive': neutral_positive_count,
                'neutral_negative': neutral_negative_count,
                'negative': negative_count,
                'positive_percent': round((positive_count / total_articles * 100), 1) if total_articles > 0 else 0,
                'neutral_positive_percent': round((neutral_positive_count / total_articles * 100), 1) if total_articles > 0 else 0,
                'neutral_negative_percent': round((neutral_negative_count / total_articles * 100), 1) if total_articles > 0 else 0,
                'negative_percent': round((negative_count / total_articles * 100), 1) if total_articles > 0 else 0
            }
            
            # 4. Statistiques RoBERTa vs Traditional
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN analysis_model = 'roberta' THEN 1 END) as roberta_articles,
                    COUNT(CASE WHEN analysis_model = 'traditional' THEN 1 END) as traditional_articles,
                    COUNT(CASE WHEN analysis_model IS NULL THEN 1 END) as no_model_articles,
                    AVG(CASE WHEN roberta_score IS NOT NULL THEN roberta_score END) as avg_roberta_score
                FROM articles
            """)
            
            model_stats_row = cursor.fetchone()
            
            # 5. Stats des thèmes
            cursor.execute("""
                SELECT 
                    t.id, 
                    t.name, 
                    t.color,
                    COUNT(DISTINCT ta.article_id) as article_count
                FROM themes t
                LEFT JOIN theme_analyses ta ON t.id = ta.theme_id AND ta.confidence >= 0.3
                GROUP BY t.id, t.name, t.color
                ORDER BY article_count DESC
            """)
            
            theme_stats = {}
            for theme_row in cursor.fetchall():
                theme_id, name, color, count = theme_row
                theme_stats[theme_id] = {
                    'name': name,
                    'color': color,
                    'article_count': count
                }
            
            conn.close()

            return jsonify({
                'success': True,
                'total_articles': total_articles,
                'sentiment_distribution': sentiment_distribution,
                'model_usage': {
                    'roberta': model_stats_row[0] if model_stats_row and model_stats_row[0] is not None else 0,
                    'traditional': model_stats_row[1] if model_stats_row and model_stats_row[1] is not None else 0,
                    'legacy': model_stats_row[2] if model_stats_row and model_stats_row[2] is not None else 0,
                    'avg_roberta_score': round(model_stats_row[3], 4) if model_stats_row and model_stats_row[3] is not None else 0
                },
                'theme_stats': theme_stats,
                'categories_explanation': {
                    'positive': 'Sentiment clairement positif (> 0.3)',
                    'neutral_positive': 'Légèrement positif (0.05 à 0.3)', 
                    'neutral_negative': 'Légèrement négatif (-0.3 à -0.05)',
                    'negative': 'Sentiment clairement négatif (< -0.3)'
                }
            })

        except Exception as e:
            logger.error(f"Erreur récupération stats: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e),
                'fallback_data': {
                    'total_articles': 0,
                    'sentiment_distribution': {
                        'positive': 0,
                        'neutral_positive': 0,
                        'neutral_negative': 0, 
                        'negative': 0
                    }
                }
            }), 500

    # ===== ROUTE TIMELINE MANQUANTE - CORRECTION =====
    @app.route('/api/stats/timeline')
    def get_timeline_stats():
        """Récupère les données d'évolution temporelle - NOUVELLE ROUTE"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            # Récupérer les données des 30 derniers jours
            cursor.execute("""
                SELECT 
                    DATE(pub_date) as date,
                    COUNT(CASE WHEN detailed_sentiment = 'positive' THEN 1 END) as positive,
                    COUNT(CASE WHEN detailed_sentiment = 'negative' THEN 1 END) as negative,
                    COUNT(CASE WHEN detailed_sentiment = 'neutral_positive' THEN 1 END) as neutral_positive,
                    COUNT(CASE WHEN detailed_sentiment = 'neutral_negative' THEN 1 END) as neutral_negative,
                    COUNT(CASE WHEN detailed_sentiment IS NULL AND sentiment_type = 'positive' THEN 1 END) as legacy_positive,
                    COUNT(CASE WHEN detailed_sentiment IS NULL AND sentiment_type = 'negative' THEN 1 END) as legacy_negative,
                    COUNT(CASE WHEN detailed_sentiment IS NULL AND sentiment_type = 'neutral' THEN 1 END) as legacy_neutral,
                    COUNT(*) as total
                FROM articles 
                WHERE pub_date >= DATE('now', '-30 days')
                GROUP BY DATE(pub_date)
                ORDER BY date ASC
                LIMIT 30
            """)
            
            timeline_data = []
            for row in cursor.fetchall():
                date, positive, negative, neutral_positive, neutral_negative, legacy_positive, legacy_negative, legacy_neutral, total = row
                
                # Combiner données RoBERTa et legacy
                combined_positive = (positive or 0) + (legacy_positive or 0)
                combined_negative = (negative or 0) + (legacy_negative or 0)
                combined_neutral = (neutral_positive or 0) + (neutral_negative or 0) + (legacy_neutral or 0)
                
                timeline_data.append({
                    'date': date,
                    'positive': combined_positive,
                    'negative': combined_negative,
                    'neutral': combined_neutral,
                    'neutral_positive': neutral_positive or 0,
                    'neutral_negative': neutral_negative or 0,
                    'total': total or 0
                })
            
            conn.close()
            
            # Si pas de données, créer des données factices pour le graphique
            if not timeline_data:
                logger.info("Aucune donnée timeline, génération de données factices")
                today = datetime.now().date()
                for i in range(7):
                    date = today - timedelta(days=6-i)
                    timeline_data.append({
                        'date': date.isoformat(),
                        'positive': max(0, 5 + i),
                        'negative': max(0, 2 + i//2),
                        'neutral': max(0, 3 + i//3),
                        'neutral_positive': max(0, 1 + i//2),
                        'neutral_negative': max(0, 1 + i//3),
                        'total': max(0, 10 + i*2)
                    })

            return jsonify({
                'success': True,
                'timeline': timeline_data,
                'period': f'{len(timeline_data)} derniers jours',
                'total_points': len(timeline_data)
            })

        except Exception as e:
            logger.error(f"Erreur récupération timeline: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'timeline': []
            }), 500

    # ===== API ROUTES - RSS =====
    @app.route('/api/update-feeds', methods=['POST'])
    def update_feeds():
        """Met à jour les flux RSS"""
        try:
            data = request.get_json()
            feed_urls = data.get('feeds', [])

            if not feed_urls:
                return jsonify({'error': 'Aucun flux fourni'}), 400

            results = rss_manager.update_feeds(feed_urls)

            return jsonify({
                'message': 'Mise à jour terminée',
                'results': results
            })

        except Exception as e:
            logger.error(f"Erreur mise à jour flux: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/test-feed')
    def test_feed():
        """Teste un flux RSS et retourne les informations"""
        try:
            feed_url = request.args.get('url')
            if not feed_url:
                return jsonify({'error': 'URL manquante'}), 400

            articles = rss_manager.parse_feed(feed_url)

            return jsonify({
                'success': True,
                'feed_url': feed_url,
                'articles_found': len(articles),
                'articles': articles[:3]
            })

        except Exception as e:
            url = request.args.get('url', 'URL inconnue')
            logger.error(f"Erreur test flux {url}: {e}")
            return jsonify({'error': str(e)}), 500

    # ===== API ROUTES - FILTRES =====
    @app.route('/api/themes/<theme_id>/articles')
    def get_theme_articles(theme_id):
        """Récupère les articles pour un thème spécifique"""
        try:
            limit = int(request.args.get('limit', 50))
            articles = theme_analyzer.get_articles_by_theme(theme_id, limit)
            return jsonify({'articles': articles})
        except Exception as e:
            logger.error(f"Erreur récupération articles thème: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/sources')
    def get_sources():
        """Récupère toutes les sources RSS uniques"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT feed_url 
                FROM articles 
                WHERE feed_url IS NOT NULL
                ORDER BY feed_url
            """)

            sources = [row[0] for row in cursor.fetchall()]
            conn.close()

            return jsonify({'sources': sources})

        except Exception as e:
            logger.error(f"Erreur récupération sources: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/articles/filter')
    def filter_articles():
        """Filtre les articles selon plusieurs critères"""
        try:
            theme = request.args.get('theme')
            sentiment = request.args.get('sentiment')
            source = request.args.get('source')
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            search = request.args.get('search', '')
            limit = int(request.args.get('limit', 100))

            conn = db_manager.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT DISTINCT a.id, a.title, a.content, a.link, a.pub_date, 
                       a.sentiment_type, a.sentiment_score, a.feed_url,
                       a.detailed_sentiment, a.roberta_score
                FROM articles a
            """

            joins = []
            conditions = []
            params = []

            if theme and theme != 'all':
                joins.append("""
                    LEFT JOIN theme_analyses ta ON a.id = ta.article_id
                """)
                conditions.append("ta.theme_id = ? AND ta.confidence >= 0.3")
                params.append(theme)

            if sentiment and sentiment != 'all':
                if sentiment in ['positive', 'negative', 'neutral_positive', 'neutral_negative']:
                    conditions.append("a.detailed_sentiment = ?")
                else:
                    conditions.append("a.sentiment_type = ?")
                params.append(sentiment)

            if source and source != 'all':
                conditions.append("a.feed_url = ?")
                params.append(source)

            if date_from:
                conditions.append("DATE(a.pub_date) >= ?")
                params.append(date_from)

            if date_to:
                conditions.append("DATE(a.pub_date) <= ?")
                params.append(date_to)

            if search:
                conditions.append("(a.title LIKE ? OR a.content LIKE ?)")
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])

            query += " ".join(joins)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY a.pub_date DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'link': row[3],
                    'pub_date': row[4],
                    'sentiment': row[5],
                    'sentiment_score': row[6],
                    'feed_url': row[7],
                    'detailed_sentiment': row[8],
                    'roberta_score': row[9]
                })

            conn.close()
            return jsonify({'articles': articles})

        except Exception as e:
            logger.error(f"Erreur filtrage articles: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/articles/export')
    def export_articles():
        """Exporte les articles filtrés en CSV"""
        try:
            theme = request.args.get('theme')
            sentiment = request.args.get('sentiment')
            source = request.args.get('source')
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            search = request.args.get('search', '')

            conn = db_manager.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT DISTINCT a.id, a.title, a.content, a.link, a.pub_date, 
                       a.sentiment_type, a.sentiment_score, a.feed_url,
                       a.detailed_sentiment, a.roberta_score
                FROM articles a
            """

            joins = []
            conditions = []
            params = []

            if theme and theme != 'all':
                joins.append("LEFT JOIN theme_analyses ta ON a.id = ta.article_id")
                conditions.append("ta.theme_id = ? AND ta.confidence >= 0.3")
                params.append(theme)

            if sentiment and sentiment != 'all':
                if sentiment in ['positive', 'negative', 'neutral_positive', 'neutral_negative']:
                    conditions.append("a.detailed_sentiment = ?")
                else:
                    conditions.append("a.sentiment_type = ?")
                params.append(sentiment)

            if source and source != 'all':
                conditions.append("a.feed_url = ?")
                params.append(source)

            if date_from:
                conditions.append("DATE(a.pub_date) >= ?")
                params.append(date_from)

            if date_to:
                conditions.append("DATE(a.pub_date) <= ?")
                params.append(date_to)

            if search:
                conditions.append("(a.title LIKE ? OR a.content LIKE ?)")
                search_pattern = f"%{search}%"
                params.extend([search_pattern, search_pattern])

            query += " ".join(joins)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY a.pub_date DESC LIMIT 1000"

            cursor.execute(query, params)

            output = StringIO()
            writer = csv.writer(output)

            writer.writerow(['ID', 'Titre', 'Contenu', 'Lien', 'Date', 'Sentiment', 'Score', 'Source', 'Sentiment Détaillé', 'Score RoBERTa'])

            for row in cursor.fetchall():
                writer.writerow(row)

            conn.close()

            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': 'attachment; filename=articles_export.csv'
                }
            )

        except Exception as e:
            logger.error(f"Erreur export articles: {e}")
            return jsonify({'error': str(e)}), 500



    # ===== FONCTIONS INTERNES POUR IA =====
    def generate_ia_analysis(articles, report_type, themes, start_date, end_date):
        """
        Génère l'analyse IA avec le serveur Llama
        Utilise llama_client.py pour la communication
        """
        try:
            # Préparer le contexte pour Llama
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0, 'neutral_positive': 0, 'neutral_negative': 0}
            for article in articles:
                sentiment = article.get('detailed_sentiment') or article.get('sentiment', 'neutral')
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            
            context = {
            'period': f"{start_date or 'début'} → {end_date or 'Ce jour'}",
            'themes': themes if themes else ['Tous thèmes'],
            'sentiment_positive': sentiment_counts.get('positive', 0),
            'sentiment_negative': sentiment_counts.get('negative', 0),
            'sentiment_neutral': sentiment_counts.get('neutral', 0),
            'sentiment_neutral_positive': sentiment_counts.get('neutral_positive', 0),
            'sentiment_neutral_negative': sentiment_counts.get('neutral_negative', 0),
            'total_articles': len(articles)
            }
            
            # Appel au client Llama
            if llama_client is None:
                from .llama_client import get_llama_client
                current_llama_client = get_llama_client()
            else:
                current_llama_client = llama_client
                
            result = current_llama_client.generate_analysis(
                report_type=report_type,
                articles=articles,
                context=context
            )
            
            # Convertir le markdown en HTML
            analysis_text = result.get('analysis', '')
            
            # Nettoyer le texte des balises ChatML résiduelles
            analysis_text = analysis_text.replace('<|im_start|>', '').replace('<|im_end|>', '')
            
            # Conversion markdown → HTML améliorée
            lines = analysis_text.split('\n')
            html_lines = []
            in_list = False
            in_paragraph = False
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    if in_list:
                        html_lines.append('</ul>')
                        in_list = False
                    if in_paragraph:
                        html_lines.append('</p>')
                        in_paragraph = False
                    html_lines.append('<br>')
                    continue
                
                # Titres H2
                if line.startswith('## '):
                    if in_list:
                        html_lines.append('</ul>')
                        in_list = False
                    if in_paragraph:
                        html_lines.append('</p>')
                        in_paragraph = False
                    html_lines.append(f'<h2 class="text-xl font-bold mt-4 mb-2">{line[3:]}</h2>')
                
                # Titres H3
                elif line.startswith('### '):
                    if in_list:
                        html_lines.append('</ul>')
                        in_list = False
                    if in_paragraph:
                        html_lines.append('</p>')
                        in_paragraph = False
                    html_lines.append(f'<h3 class="text-lg font-semibold mt-3 mb-1">{line[4:]}</h3>')
                
                # Listes
                elif line.startswith('- ') or line.startswith('* '):
                    if not in_list:
                        html_lines.append('<ul class="list-disc ml-6 mb-2">')
                        in_list = True
                    if in_paragraph:
                        html_lines.append('</p>')
                        in_paragraph = False
                    html_lines.append(f'<li>{line[2:]}</li>')
                
                # Texte gras **texte**
                elif '**' in line:
                    if in_paragraph:
                        html_lines.append('</p>')
                        in_paragraph = False
                    line = line.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
                    html_lines.append(f'<p class="mb-2">{line}</p>')
                
                # Paragraphe normal
                else:
                    if in_list:
                        html_lines.append('</ul>')
                        in_list = False
                    if not in_paragraph:
                        html_lines.append('<p class="mb-2">')
                        in_paragraph = True
                    else:
                        html_lines.append('<br>')
                    html_lines.append(line)
            
            if in_list:
                html_lines.append('</ul>')
            if in_paragraph:
                html_lines.append('</p>')
            
            html_content = '\n'.join(html_lines)
            
            # Ajouter un badge de statut
            if result.get('success'):
                status_badge = f'''
                <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                    <div class="flex items-center">
                        <i class="fas fa-robot text-green-600 text-xl mr-3"></i>
                        <div>
                            <strong class="text-green-800">✅ Analyse générée par IA Llama 3.2</strong><br>
                            <small class="text-green-600">Modèle: {result.get('model_used', 'llama3.2-3b-Q4_K_M')}</small>
                        </div>
                    </div>
                </div>
                '''
            else:
                status_badge = f'''
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                    <div class="flex items-center">
                        <i class="fas fa-exclamation-triangle text-yellow-600 text-xl mr-3"></i>
                        <div>
                            <strong class="text-yellow-800">⚠️ Mode dégradé</strong><br>
                            <small class="text-yellow-600">Raison: {result.get('error', 'Serveur Llama indisponible')}</small>
                        </div>
                    </div>
                </div>
                '''
            
            html_content = status_badge + html_content
            
            return {
                'html_content': html_content,
                'recommendations': result.get('recommendations', ''),
                'llama_success': result.get('success', False),
                'llama_error': result.get('error'),
                'model_used': result.get('model_used')
            }
        except Exception as e:
            logger.error(f"Erreur génération analyse IA: {e}")
            return {
                'html_content': f'''
                <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div class="flex items-center">
                        <i class="fas fa-exclamation-circle text-red-600 text-xl mr-3"></i>
                        <div>
                            <strong class="text-red-800">❌ Erreur lors de la génération de l'analyse IA</strong><br>
                            <small class="text-red-600">{str(e)}</small>
                        </div>
                    </div>
                </div>
                ''',
                'recommendations': '',
                'llama_success': False,
                'llama_error': str(e)
            }

    # ===== ROUTES IA =====
    @app.route('/api/generate-ia-report', methods=['POST'])
    def generate_ia_report():
        """Génère un rapport d'analyse IA à partir des articles"""
        try:
            data = request.get_json()
            
            report_type = data.get('report_type', 'geopolitique')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            themes = data.get('themes', [])
            include_sentiment = data.get('include_sentiment', True)
            include_sources = data.get('include_sources', True)
            generate_pdf = data.get('generate_pdf', False)
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id, title, content, pub_date, sentiment_type, detailed_sentiment, 
                       feed_url, roberta_score 
                FROM articles 
                WHERE 1=1
            """
            params = []
            
            if start_date:
                query += " AND DATE(pub_date) >= ?"
                params.append(start_date)
            if end_date:
                query += " AND DATE(pub_date) <= ?"
                params.append(end_date)
            if themes:
                placeholders = ','.join('?' * len(themes))
                query += f" AND id IN (SELECT DISTINCT article_id FROM theme_analyses WHERE theme_id IN ({placeholders}) AND confidence >= 0.3)"
                params.extend(themes)
            
            query += " ORDER BY pub_date DESC LIMIT 100"
            
            cursor.execute(query, params)
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'sentiment': row[4],
                    'detailed_sentiment': row[5],
                    'source': row[6],
                    'roberta_score': row[7]
                })
            
            conn.close()
            
            if not articles:
                return jsonify({
                    'success': False,
                    'error': 'Aucun article trouvé avec les critères sélectionnés'
                }), 400
            
            # APPEL AU CLIENT LLAMA
            analysis_result = generate_ia_analysis(
                articles, 
                report_type, 
                themes,
                start_date,
                end_date
            )
            
            response_data = {
                'success': True,
                'report_type': report_type,
                'articles_analyzed': len(articles),
                'themes_covered': themes,
                'period': f"{start_date} to {end_date}" if start_date and end_date else "Toutes périodes",
                'analysis_html': analysis_result['html_content'],
                'recommendations': analysis_result.get('recommendations', ''),
                'llama_status': {
                    'success': analysis_result.get('llama_success', False),
                    'error': analysis_result.get('llama_error'),
                    'model_used': analysis_result.get('model_used'),
                    'mode': 'IA' if analysis_result.get('llama_success') else 'Dégradé'
                }
            }
            
            if generate_pdf:
                response_data['pdf_generation_available'] = True
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Erreur génération rapport IA: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Erreur génération rapport IA: {str(e)}'
            }), 500

    @app.route('/api/generate-pdf', methods=['POST'])
    def generate_pdf_report():
        """Génère un PDF à partir du contenu de l'analyse IA"""
        try:
            data = request.get_json()
            html_content = data.get('html_content', '')
            title = data.get('title', 'Rapport GEOPOL')
            report_type = data.get('type', 'geopolitique')

            if not html_content:
                return jsonify({
                    'success': False,
                    'error': 'Contenu HTML requis'
                }), 400

            # Nettoyer le HTML pour le PDF (supprimer les classes Tailwind)
            import re
            clean_html = re.sub(r'class="[^"]*"', '', html_content)
            clean_html = clean_html.replace('bg-green-50', '')
            clean_html = clean_html.replace('border-green-200', '')
            clean_html = clean_html.replace('text-green-600', '')
            clean_html = clean_html.replace('text-green-800', '')
            clean_html = clean_html.replace('bg-yellow-50', '')
            clean_html = clean_html.replace('border-yellow-200', '')
            clean_html = clean_html.replace('text-yellow-600', '')
            clean_html = clean_html.replace('text-yellow-800', '')

            # Créer le HTML complet pour le PDF
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
                <style>
                    @page {{
                        size: a4;
                        margin: 2cm;
                    }}
                    body {{
                        font-family: 'Helvetica', sans-serif;
                        margin: 0;
                        padding: 0;
                        line-height: 1.4;
                        color: #000;
                        font-size: 12px;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                        border-bottom: 2px solid #3498db;
                        padding-bottom: 15px;
                    }}
                    h1 {{
                        color: #2c3e50;
                        margin-bottom: 8px;
                        font-size: 18px;
                    }}
                    .timestamp {{
                        color: #7f8c8d;
                        font-size: 10px;
                    }}
                    .content {{
                        margin-top: 15px;
                    }}
                    .footer {{
                        margin-top: 30px;
                        text-align: center;
                        font-size: 9px;
                        color: #95a5a6;
                        border-top: 1px solid #bdc3c7;
                        padding-top: 10px;
                    }}
                    h2 {{
                        font-size: 14px;
                        color: #2c3e50;
                        margin-top: 20px;
                        margin-bottom: 10px;
                    }}
                    h3 {{
                        font-size: 12px;
                        color: #34495e;
                        margin-top: 15px;
                        margin-bottom: 8px;
                    }}
                    p, li {{
                        font-size: 11px;
                        margin-bottom: 8px;
                    }}
                    ul {{
                        margin-left: 20px;
                    }}
                    .status-badge {{
                        padding: 8px;
                        border-radius: 4px;
                        margin-bottom: 15px;
                        font-size: 10px;
                    }}
                    .ia-badge {{
                        background: #d4edda;
                        border: 1px solid #c3e6cb;
                        padding: 10px;
                        border-radius: 5px;
                        margin-bottom: 15px;
                    }}
                    .degrade-badge {{
                        background: #fff3cd;
                        border: 1px solid #ffeeba;
                        padding: 10px;
                        border-radius: 5px;
                        margin-bottom: 15px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{title}</h1>
                    <p class="timestamp">Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} • GEOPOL Analytics</p>
                </div>
                <div class="content">
                    {clean_html}
                </div>
                <div class="footer">
                    Rapport généré automatiquement par GEOPOL avec Llama 3.2
                </div>
            </body>
            </html>
            """

            # Générer le PDF avec xhtml2pdf
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(
                BytesIO(full_html.encode('UTF-8')),
                dest=pdf_buffer,
                encoding='UTF-8'
            )

            if pisa_status.err:
                return jsonify({
                    'success': False,
                    'error': 'Erreur lors de la génération du PDF'
                }), 500

            pdf_buffer.seek(0)

            # Créer un fichier temporaire pour l'envoi
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                tmp_file.write(pdf_buffer.getvalue())
                pdf_path = tmp_file.name

            try:
                return send_file(
                    pdf_path,
                    as_attachment=True,
                    download_name=f"rapport_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mimetype='application/pdf'
                )
            finally:
                # Nettoyer le fichier temporaire après l'envoi
                try:
                    os.remove(pdf_path)
                except Exception as e:
                    logger.warning(f"Erreur lors de la suppression du fichier temporaire {pdf_path}: {e}")

        except Exception as e:
            logger.error(f"Erreur génération PDF: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': f'Erreur génération PDF: {str(e)}'
            }), 500

    # ===== ROUTES AVANCÉES =====
    @app.route('/api/themes/advanced', methods=['POST'])
    def create_advanced_theme():
        """Crée un thème avec configuration avancée"""
        try:
            data = request.get_json()
            result = advanced_theme_manager.create_advanced_theme(data)

            if result['success']:
                return jsonify(result), 200
            else:
                return jsonify(result), 400

        except Exception as e:
            logger.error(f"Erreur création thème avancé: {e}")
            return jsonify({
                'success': False,
                'error': f'Erreur serveur: {str(e)}'
            }), 500

    @app.route('/api/themes/<theme_id>/details')
    def get_theme_details(theme_id):
        """Récupère les détails complets d'un thème"""
        try:
            theme = advanced_theme_manager.get_theme_with_details(theme_id)

            if not theme:
                return jsonify({'error': 'Thème non trouvé'}), 404

            return jsonify({'theme': theme})
        except Exception as e:
            logger.error(f"Erreur récupération détails: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>/statistics')
    def get_theme_statistics_advanced(theme_id):
        """Récupère les statistiques avancées d'un thème"""
        try:
            stats = advanced_theme_manager.get_theme_statistics(theme_id)
            return jsonify({'statistics': stats})
        except Exception as e:
            logger.error(f"Erreur statistiques: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>/keywords/<keyword>/weight', methods=['PUT'])
    def update_keyword_weight(theme_id, keyword):
        """Met à jour le poids d'un mot-clé"""
        try:
            data = request.get_json()
            new_weight = data.get('weight')

            if new_weight is None:
                return jsonify({'error': 'Poids requis'}), 400

            success = advanced_theme_manager.update_keyword_weight(
                theme_id, keyword, float(new_weight)
            )

            if success:
                return jsonify({'message': 'Poids mis à jour'})
            else:
                return jsonify({'error': 'Erreur mise à jour'}), 500

        except Exception as e:
            logger.error(f"Erreur update poids: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>/synonyms', methods=['POST'])
    def add_theme_synonym(theme_id):
        """Ajoute un synonyme à un mot-clé"""
        try:
            data = request.get_json()
            original_word = data.get('original_word')
            synonym = data.get('synonym')

            if not original_word or not synonym:
                return jsonify({'error': 'Mot original et synonyme requis'}), 400

            success = advanced_theme_manager.add_synonym(
                theme_id, original_word, synonym
            )

            if success:
                return jsonify({'message': 'Synonyme ajouté'})
            else:
                return jsonify({'error': 'Erreur ajout synonyme'}), 500

        except Exception as e:
            logger.error(f"Erreur ajout synonyme: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>/suggest-keywords')
    def suggest_theme_keywords(theme_id):
        """Suggère de nouveaux mots-clés pour un thème"""
        try:
            limit = int(request.args.get('limit', 10))
            suggestions = advanced_theme_manager.suggest_new_keywords(theme_id, limit)

            return jsonify({'suggestions': suggestions})
        except Exception as e:
            logger.error(f"Erreur suggestion mots-clés: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/<theme_id>/export')
    def export_theme_configuration(theme_id):
        """Exporte la configuration d'un thème"""
        try:
            config = advanced_theme_manager.export_theme_config(theme_id)

            return Response(
                json.dumps(config, ensure_ascii=False, indent=2),
                mimetype='application/json',
                headers={
                    'Content-Disposition': f'attachment; filename=theme_{theme_id}.json'
                }
            )
        except Exception as e:
            logger.error(f"Erreur export thème: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/themes/import', methods=['POST'])
    def import_theme_configuration():
        """Importe une configuration de thème"""
        try:
            config = request.get_json()
            success = advanced_theme_manager.import_theme_config(config)

            if success:
                return jsonify({'message': 'Thème importé avec succès'})
            else:
                return jsonify({'error': 'Erreur import'}), 500

        except Exception as e:
            logger.error(f"Erreur import thème: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/reanalyze-articles', methods=['POST'])
    def reanalyze_articles():
        """Ré-analyse tous les articles avec les thèmes actuels"""
        try:
            logger.info("🔄 Démarrage de la ré-analyse des articles...")
            theme_analyzer.reanalyze_all_articles()

            conn = db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(DISTINCT article_id) 
                FROM theme_analyses 
                WHERE confidence >= 0.2
            """)
            analyzed_articles = cursor.fetchone()[0]

            cursor.execute("""
                SELECT theme_id, COUNT(DISTINCT article_id) as count
                FROM theme_analyses
                WHERE confidence >= 0.2
                GROUP BY theme_id
            """)

            theme_counts = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()

            return jsonify({
                'success': True,
                'message': 'Ré-analyse terminée avec succès',
                'results': {
                    'total_articles': total_articles,
                    'analyzed_articles': analyzed_articles,
                    'themes_detected': len(theme_counts),
                    'theme_distribution': theme_counts
                }
            })

        except Exception as e:
            logger.error(f"Erreur ré-analyse: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

     # ===== API ROUTES - ANALYSE BATCH COHÉRENTE =====
    
    @app.route('/api/batch/analyze-coherent', methods=['POST'])
    def batch_analyze_coherent():
        """
        Analyse batch avec garantie de cohérence
        POST /api/batch/analyze-coherent
        Body: {
            "days": 7,  # optionnel, défaut 7
            "force_reanalysis": false  # optionnel
        }
        """
        try:
            data = request.get_json() or {}
            days = data.get('days', 7)
            force_reanalysis = data.get('force_reanalysis', False)
            
            logger.info(f"🚀 Démarrage analyse batch cohérente ({days} jours)")
            
            # Lancer l'analyse
            results = batch_analyzer.analyze_recent_articles(
                db_manager,
                days=days
            )
            
            return jsonify({
                'success': True,
                'results': results,
                'message': f'Analyse terminée : {results.get("analyzed", 0)} articles traités'
            })
            
        except Exception as e:
            logger.error(f"Erreur analyse batch: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/batch/cluster-report', methods=['GET'])
    def get_cluster_report():
        """
        Récupère un rapport sur les clusters détectés
        GET /api/batch/cluster-report
        """
        try:
            report = batch_analyzer.get_cluster_report(db_manager)
            
            return jsonify({
                'success': True,
                'report': report
            })
            
        except Exception as e:
            logger.error(f"Erreur génération rapport: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/batch/analyze-specific', methods=['POST'])
    def batch_analyze_specific_articles():
        """
        Analyse un lot spécifique d'articles
        POST /api/batch/analyze-specific
        Body: {
            "article_ids": [1, 2, 3, 4, 5]
        }
        """
        try:
            data = request.get_json()
            article_ids = data.get('article_ids', [])
            
            if not article_ids:
                return jsonify({
                    'success': False,
                    'error': 'Liste article_ids requise'
                }), 400
            
            # Récupérer les articles
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(article_ids))
            cursor.execute(f"""
                SELECT id, title, content, pub_date, feed_url, 
                       sentiment_score, sentiment_type, detailed_sentiment, roberta_score
                FROM articles
                WHERE id IN ({placeholders})
            """, article_ids)
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'feed_url': row[4],
                    'sentiment_score': row[5],
                    'sentiment_type': row[6],
                    'detailed_sentiment': row[7],
                    'roberta_score': row[8]
                })
            
            conn.close()
            
            if not articles:
                return jsonify({
                    'success': False,
                    'error': 'Aucun article trouvé'
                }), 404
            
            # Analyser
            results = batch_analyzer.analyze_batch_with_coherence(
                articles,
                db_manager
            )
            
            return jsonify({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Erreur analyse spécifique: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/batch/compare-before-after/<int:article_id>', methods=['GET'])
    def compare_sentiment_changes(article_id):
        """
        Compare le sentiment avant/après harmonisation
        GET /api/batch/compare-before-after/<article_id>
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT sentiment_score, sentiment_type, detailed_sentiment,
                       harmonized, cluster_size, analysis_metadata,
                       bayesian_confidence, roberta_score
                FROM articles
                WHERE id = ?
            """, (article_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return jsonify({
                    'success': False,
                    'error': 'Article non trouvé'
                }), 404
            
            import json
            metadata = {}
            if row[5]:
                try:
                    metadata = json.loads(row[5])
                except:
                    metadata = {}
            
            return jsonify({
                'success': True,
                'article_id': article_id,
                'current': {
                    'score': row[0],
                    'type': row[1],
                    'detailed_sentiment': row[2],
                    'harmonized': bool(row[3]),
                    'cluster_size': row[4],
                    'bayesian_confidence': row[6],
                    'roberta_score': row[7]
                },
                'original': {
                    'score': metadata.get('initial_score'),
                    'deviation_reduced': metadata.get('deviation_reduced', 0),
                    'model': metadata.get('model', 'unknown')
                },
                'metadata': metadata
            })
            
        except Exception as e:
            logger.error(f"Erreur comparaison: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/batch/statistics', methods=['GET'])
    def get_batch_statistics():
        """
        Statistiques globales sur l'analyse batch
        GET /api/batch/statistics
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Total d'articles analysés
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            # Articles harmonisés
            cursor.execute("SELECT COUNT(*) FROM articles WHERE harmonized = 1")
            harmonized = cursor.fetchone()[0]
            
            # Distribution des sentiments (4 catégories)
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN detailed_sentiment = 'positive' THEN 1 END) as positive,
                    COUNT(CASE WHEN detailed_sentiment = 'neutral_positive' THEN 1 END) as neutral_positive,
                    COUNT(CASE WHEN detailed_sentiment = 'neutral_negative' THEN 1 END) as neutral_negative,
                    COUNT(CASE WHEN detailed_sentiment = 'negative' THEN 1 END) as negative,
                    COUNT(CASE WHEN detailed_sentiment IS NULL AND sentiment_type = 'positive' THEN 1 END) as legacy_positive,
                    COUNT(CASE WHEN detailed_sentiment IS NULL AND sentiment_type = 'negative' THEN 1 END) as legacy_negative,
                    COUNT(CASE WHEN detailed_sentiment IS NULL AND sentiment_type = 'neutral' THEN 1 END) as legacy_neutral
                FROM articles
            """)
            
            row = cursor.fetchone()
            sentiment_distribution = {
                'positive': (row[0] or 0) + (row[4] or 0),
                'neutral_positive': (row[1] or 0) + ((row[6] or 0) // 2),
                'neutral_negative': (row[2] or 0) + ((row[6] or 0) - ((row[6] or 0) // 2)),
                'negative': (row[3] or 0) + (row[5] or 0)
            }
            
            # Confiance moyenne
            cursor.execute("""
                SELECT AVG(bayesian_confidence)
                FROM articles
                WHERE bayesian_confidence IS NOT NULL
            """)
            avg_confidence = cursor.fetchone()[0] or 0
            
            # Articles par taille de cluster
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN cluster_size = 1 THEN 1 ELSE 0 END) as isolated,
                    SUM(CASE WHEN cluster_size BETWEEN 2 AND 5 THEN 1 ELSE 0 END) as small_clusters,
                    SUM(CASE WHEN cluster_size > 5 THEN 1 ELSE 0 END) as large_clusters
                FROM articles
            """)
            cluster_row = cursor.fetchone()
            
            # Modèles utilisés
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN analysis_model = 'roberta_enhanced' THEN 1 END) as roberta_enhanced,
                    COUNT(CASE WHEN analysis_model = 'traditional_enhanced' THEN 1 END) as traditional_enhanced,
                    COUNT(CASE WHEN analysis_model = 'roberta' THEN 1 END) as roberta_legacy,
                    COUNT(CASE WHEN analysis_model IS NULL THEN 1 END) as no_model
                FROM articles
            """)
            model_row = cursor.fetchone()
            
            conn.close()
            
            return jsonify({
                'success': True,
                'statistics': {
                    'total_articles': total_articles,
                    'harmonized_articles': harmonized,
                    'harmonization_rate': round(harmonized / total_articles * 100, 1) if total_articles > 0 else 0,
                    'sentiment_distribution': sentiment_distribution,
                    'average_confidence': round(avg_confidence, 3),
                    'clustering': {
                        'isolated': cluster_row[0] or 0,
                        'small_clusters': cluster_row[1] or 0,
                        'large_clusters': cluster_row[2] or 0
                    },
                    'model_usage': {
                        'roberta_enhanced': model_row[0] or 0,
                        'traditional_enhanced': model_row[1] or 0,
                        'roberta_legacy': model_row[2] or 0,
                        'no_model': model_row[3] or 0
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur statistiques batch: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # ===== API ROUTES - CORROBORATION (existant mais amélioré) =====
    
    @app.route('/api/corroboration/batch-process', methods=['POST'])
    def batch_process_corroboration():
        """
        Traite la corroboration par lots
        POST /api/corroboration/batch-process
        Body: {
            "days": 7  # optionnel
        }
        """
        try:
            data = request.get_json() or {}
            days = data.get('days', 7)
            
            logger.info(f"🔍 Démarrage traitement corroboration ({days} jours)")
            
            # Récupérer les articles récents
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, content, pub_date, feed_url, 
                       sentiment_type, sentiment_score, detailed_sentiment
                FROM articles
                WHERE pub_date >= datetime('now', '-' || ? || ' days')
                ORDER BY pub_date DESC
            """, (days,))
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'feed_url': row[4],
                    'sentiment_type': row[5],
                    'sentiment_score': row[6],
                    'detailed_sentiment': row[7]
                })
            
            conn.close()
            
            if not articles:
                return jsonify({
                    'success': True,
                    'stats': {
                        'processed': 0,
                        'corroborations_found': 0,
                        'errors': 0
                    },
                    'message': 'Aucun article à traiter'
                })
            
            # Traitement batch
            stats = corroboration_engine.batch_process_articles(
                articles,
                articles,  # Utiliser la même liste comme pool de candidats
                db_manager
            )
            
            logger.info(f"✅ Corroboration terminée : {stats['processed']} articles, "
                       f"{stats['corroborations_found']} corroborations trouvées")
            
            return jsonify({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"Erreur batch corroboration: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/corroboration/stats/<int:article_id>', methods=['GET'])
    def get_corroboration_stats(article_id):
        """
        Récupère les statistiques de corroboration d'un article
        GET /api/corroboration/stats/<article_id>
        """
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Nombre de corroborations
            cursor.execute("""
                SELECT COUNT(*), AVG(similarity_score)
                FROM article_corroborations
                WHERE article_id = ?
            """, (article_id,))
            
            row = cursor.fetchone()
            corroboration_count = row[0] or 0
            avg_similarity = row[1] or 0
            
            # Articles similaires
            cursor.execute("""
                SELECT ac.similar_article_id, ac.similarity_score,
                       a.title, a.sentiment_type, a.pub_date
                FROM article_corroborations ac
                JOIN articles a ON ac.similar_article_id = a.id
                WHERE ac.article_id = ?
                ORDER BY ac.similarity_score DESC
                LIMIT 10
            """, (article_id,))
            
            similar_articles = []
            for row in cursor.fetchall():
                similar_articles.append({
                    'id': row[0],
                    'similarity': row[1],
                    'title': row[2],
                    'sentiment': row[3],
                    'pub_date': row[4]
                })
            
            conn.close()
            
            return jsonify({
                'success': True,
                'corroboration_count': corroboration_count,
                'average_similarity': round(avg_similarity, 3),
                'similar_articles': similar_articles
            })
            
        except Exception as e:
            logger.error(f"Erreur stats corroboration: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # ===== API ROUTES - ANALYSE BAYÉSIENNE =====
    
    @app.route('/api/bayesian/batch-analyze', methods=['POST'])
    def batch_analyze_bayesian():
        """
        Analyse bayésienne par lots
        POST /api/bayesian/batch-analyze
        Body: {
            "days": 7  # optionnel
        }
        """
        try:
            data = request.get_json() or {}
            days = data.get('days', 7)
            
            logger.info(f"🧮 Démarrage analyse bayésienne ({days} jours)")
            
            # Récupérer les articles récents
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, content, pub_date, sentiment_type, 
                       sentiment_score, detailed_sentiment, roberta_score
                FROM articles
                WHERE pub_date >= datetime('now', '-' || ? || ' days')
                ORDER BY pub_date DESC
            """, (days,))
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'sentiment_type': row[4],
                    'sentiment_score': row[5],
                    'detailed_sentiment': row[6],
                    'roberta_score': row[7]
                })
            
            conn.close()
            
            if not articles:
                return jsonify({
                    'success': True,
                    'results': {
                        'analyzed': 0,
                        'updated': 0,
                        'errors': []
                    },
                    'message': 'Aucun article à analyser'
                })
            
            # Traitement bayésien
            results = bayesian_analyzer.batch_analyze_articles(
                articles,
                db_manager
            )
            
            logger.info(f"✅ Analyse bayésienne terminée : {results['analyzed']} articles, "
                       f"{results['updated']} mis à jour")
            
            return jsonify({
                'success': True,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Erreur batch bayésien: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/advanced/full-analysis/<int:article_id>', methods=['POST'])
    def full_analysis_single_article(article_id):
        """
        Analyse complète d'un article (corroboration + bayésien)
        POST /api/advanced/full-analysis/<article_id>
        """
        try:
            logger.info(f"🔬 Analyse complète article {article_id}")
            
            # Récupérer l'article
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, content, pub_date, feed_url,
                       sentiment_type, sentiment_score, detailed_sentiment
                FROM articles
                WHERE id = ?
            """, (article_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Article non trouvé'
                }), 404
            
            article = {
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'pub_date': row[3],
                'feed_url': row[4],
                'sentiment_type': row[5],
                'sentiment_score': row[6],
                'detailed_sentiment': row[7]
            }
            
            # Récupérer les articles récents pour la corroboration
            cursor.execute("""
                SELECT id, title, content, pub_date, feed_url,
                       sentiment_type, sentiment_score
                FROM articles
                WHERE pub_date >= datetime('now', '-7 days')
                AND id != ?
                ORDER BY pub_date DESC
                LIMIT 200
            """, (article_id,))
            
            candidates = []
            for row in cursor.fetchall():
                candidates.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'feed_url': row[4],
                    'sentiment_type': row[5],
                    'sentiment_score': row[6]
                })
            
            conn.close()
            
            # 1. Corroboration
            corroborations = corroboration_engine.find_corroborations(
                article,
                candidates,
                threshold=0.65,
                top_n=10
            )
            
            # Sauvegarder les corroborations
            if corroborations:
                corroboration_engine._save_corroborations(
                    article_id,
                    corroborations,
                    db_manager
                )
            
            # 2. Analyse bayésienne
            bayesian_result = bayesian_analyzer.analyze_article_sentiment(
                article,
                corroborations
            )
            
            # Sauvegarder l'analyse bayésienne
            bayesian_analyzer._save_bayesian_analysis(
                article_id,
                bayesian_result,
                db_manager
            )
            
            return jsonify({
                'success': True,
                'article_id': article_id,
                'corroboration': {
                    'count': len(corroborations),
                    'articles': corroborations[:5]  # Top 5
                },
                'bayesian_analysis': bayesian_result
            })
            
        except Exception as e:
            logger.error(f"Erreur analyse complète: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/debug/routes')
    def debug_routes():
        """Affiche toutes les routes enregistrées"""
        routes = []
        for rule in app.url_map.iter_rules():
            if any(part in rule.rule for part in ['api', 'weak-indicators', 'alerts']):
                routes.append({
                    'endpoint': rule.endpoint,
                    'path': rule.rule,
                    'methods': list(rule.methods)
                })
        return jsonify({'routes': routes})

    @app.route('/weak-indicators/')
    def serve_weak_indicators_page():
        """Sert la page weak indicators"""
        return render_template('weak_indicators.html')

    @app.route('/shutdown-complete')
    def shutdown_complete():
        """Page de confirmation d'arrêt"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Arrêt réussi - GEOPOL</title>
            <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        </head>
        <body class="bg-gray-100 flex items-center justify-center min-h-screen">
            <div class="bg-white p-8 rounded-lg shadow-md text-center max-w-md">
                <div class="text-green-500 text-6xl mb-4">
                    <i class="fas fa-check-circle"></i>
                </div>
                <h1 class="text-2xl font-bold text-gray-800 mb-4">Système arrêté</h1>
                <p class="text-gray-600 mb-6">
                    L'application GEOPOL Analytics a été arrêtée proprement.
                    Vous pouvez fermer cette fenêtre.
                </p>
                <button onclick="window.close()" 
                        class="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg">
                    Fermer la fenêtre
                </button>
            </div>
        </body>
        </html>
        """

    logger.info("✅ Routes enregistrées avec intégration analyse batch cohérente")
    logger.info("✅ Routes enregistrées avec intégration Llama complète et correction timeline")
   