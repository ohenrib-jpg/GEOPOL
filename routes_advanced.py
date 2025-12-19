# Flask/routes_advanced.py
"""
Routes API pour les fonctionnalités avancées :
- Analyse bayésienne
- Corroboration d'articles
"""

from flask import request, jsonify
import logging
import sqlite3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def register_advanced_routes(app, db_manager, bayesian_analyzer, corroboration_engine):
    """Enregistre les routes avancées (analyse bayésienne et corroboration)"""
    
    # ============================================================
    # ROUTES ANALYSE BAYÉSIENNE
    # ============================================================
    
    @app.route('/api/bayesian/batch-analyze', methods=['POST'], endpoint='bayesian_batch_analyze')
    def batch_analyze_bayesian():
        """Analyse bayésienne d'un lot d'articles"""
        try:
            data = request.get_json()
            articles = data.get('articles', [])
            
            if not articles:
                return jsonify({'error': 'Aucun article fourni'}), 400
            
            results = []
            for article in articles:
                # Récupérer les données de corroboration
                corroborations = get_corroborations_for_article(article.get('id'), db_manager)
                
                # Analyse bayésienne
                result = bayesian_analyzer.analyze_article_sentiment(article, corroborations)
                results.append(result)
            
            return jsonify({
                'success': True,
                'results': results,
                'count': len(results)
            })
            
        except Exception as e:
            logger.error(f"Erreur analyse bayésienne batch: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================
    # ROUTES CORROBORATION
    # ============================================================
    
    @app.route('/api/corroboration/find', methods=['POST'], endpoint='corroboration_find')
    def find_corroborations():
        """Trouve les articles corroborants pour un article donné"""
        try:
            data = request.get_json()
            article = data.get('article')
            candidates = data.get('candidates', [])
            threshold = data.get('threshold', 0.65)
            
            if not article:
                return jsonify({'error': 'Article manquant'}), 400
            
            corroborations = corroboration_engine.find_corroborations(
                article, candidates, threshold=threshold
            )
            
            return jsonify({
                'success': True,
                'corroborations': corroborations,
                'count': len(corroborations)
            })
            
        except Exception as e:
            logger.error(f"Erreur recherche corroboration: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/corroboration/analyze-coherence', methods=['POST'], endpoint='corroboration_analyze_coherence')
    def analyze_coherence():
        """Analyse la cohérence des sentiments dans un cluster d'articles"""
        try:
            data = request.get_json()
            articles = data.get('articles', [])
            
            if len(articles) < 2:
                return jsonify({'error': 'Au moins 2 articles requis pour l\'analyse de cohérence'}), 400
            
            # Calculer les similarités et vérifier la cohérence
            coherence_scores = []
            total_similarity = 0
            sentiment_matches = 0
            
            for i, article1 in enumerate(articles):
                for j, article2 in enumerate(articles):
                    if i < j:  # Éviter les doublons
                        similarity = corroboration_engine.compute_similarity(article1, article2)
                        sentiment1 = article1.get('sentiment_type', 'neutral')
                        sentiment2 = article2.get('sentiment_type', 'neutral')
                        
                        sentiment_match = 1 if sentiment1 == sentiment2 else 0
                        
                        coherence_scores.append({
                            'article1_id': article1.get('id'),
                            'article2_id': article2.get('id'),
                            'similarity': similarity,
                            'sentiment_match': sentiment_match
                        })
                        
                        total_similarity += similarity
                        sentiment_matches += sentiment_match
            
            pair_count = len(coherence_scores)
            avg_similarity = total_similarity / pair_count if pair_count > 0 else 0
            coherence_ratio = sentiment_matches / pair_count if pair_count > 0 else 0
            
            return jsonify({
                'success': True,
                'coherence_analysis': {
                    'pair_count': pair_count,
                    'average_similarity': avg_similarity,
                    'coherence_ratio': coherence_ratio,
                    'detailed_scores': coherence_scores
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur analyse cohérence: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/corroboration/stats', methods=['GET'], endpoint='corroboration_stats')
    def get_corroboration_stats():
        """Récupère les statistiques de corroboration"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Statistiques générales
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_corroborations,
                    AVG(similarity_score) as avg_similarity,
                    COUNT(DISTINCT article_id) as articles_with_corroborations
                FROM article_corroborations
            """)
            
            stats = cursor.fetchone()
            
            # Distribution par similarité
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN similarity_score >= 0.9 THEN '0.9-1.0'
                        WHEN similarity_score >= 0.8 THEN '0.8-0.9'
                        WHEN similarity_score >= 0.7 THEN '0.7-0.8'
                        WHEN similarity_score >= 0.6 THEN '0.6-0.7'
                        ELSE '0.5-0.6'
                    END as similarity_range,
                    COUNT(*) as count
                FROM article_corroborations
                GROUP BY similarity_range
                ORDER BY similarity_range DESC
            """)
            
            distribution = cursor.fetchall()
            
            conn.close()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_corroborations': stats[0],
                    'average_similarity': round(stats[1], 3) if stats[1] else 0,
                    'articles_with_corroborations': stats[2],
                    'similarity_distribution': [
                        {'range': row[0], 'count': row[1]} for row in distribution
                    ]
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur stats corroboration: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/corroboration/find/<int:article_id>', methods=['GET'])
    def find_article_corroborations(article_id):
        """Trouve les articles corroborants pour un article donné"""
        try:
            # Récupérer l'article source
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, content, pub_date, feed_url
                FROM articles WHERE id = ?
            """, (article_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Article non trouvé'}), 404
            
            article = {
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'pub_date': row[3],
                'feed_url': row[4]
            }
            
            # Récupérer les thèmes de l'article
            cursor.execute("""
                SELECT theme_id
                FROM theme_analyses
                WHERE article_id = ?
            """, (article_id,))
            
            article['themes'] = [row[0] for row in cursor.fetchall()]
            
            # Récupérer les articles récents (7 derniers jours)
            cursor.execute("""
                SELECT id, title, content, pub_date, feed_url, 
                       sentiment_type, sentiment_score
                FROM articles 
                WHERE pub_date >= DATE('now', '-7 days')
                AND id != ?
                ORDER BY pub_date DESC
                LIMIT 200
            """, (article_id,))
            
            candidates = []
            for row in cursor.fetchall():
                cand = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'feed_url': row[4],
                    'sentiment_type': row[5],
                    'sentiment_score': row[6]
                }
                
                # Récupérer les thèmes du candidat
                cursor.execute("""
                    SELECT theme_id
                    FROM theme_analyses
                    WHERE article_id = ?
                """, (cand['id'],))
                
                cand['themes'] = [r[0] for r in cursor.fetchall()]
                candidates.append(cand)
            
            conn.close()
            
            # Trouver les corroborations
            threshold = float(request.args.get('threshold', 0.65))
            top_n = int(request.args.get('top_n', 10))
            
            corroborations = corroboration_engine.find_corroborations(
                article,
                candidates,
                threshold=threshold,
                top_n=top_n
            )
            
            # Sauvegarder dans la base
            if corroborations:
                corroboration_engine._save_corroborations(
                    article_id,
                    corroborations,
                    db_manager
                )
            
            return jsonify({
                'success': True,
                'article_id': article_id,
                'corroborations': corroborations
            })
            
        except Exception as e:
            logger.error(f"Erreur recherche corroboration: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/corroboration/batch-process', methods=['POST'])
    def batch_process_corroborations():
        """Traite la corroboration pour plusieurs articles"""
        try:
            data = request.get_json()
            article_ids = data.get('article_ids', [])
            
            if not article_ids:
                # Traiter tous les articles récents
                conn = db_manager.get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id FROM articles 
                    WHERE pub_date >= DATE('now', '-7 days')
                    ORDER BY pub_date DESC
                    LIMIT 100
                """)
                
                article_ids = [row[0] for row in cursor.fetchall()]
                conn.close()
            
            # Récupérer tous les articles
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Articles à traiter
            placeholders = ','.join('?' * len(article_ids))
            cursor.execute(f"""
                SELECT id, title, content, pub_date, feed_url
                FROM articles 
                WHERE id IN ({placeholders})
            """, article_ids)
            
            articles = []
            for row in cursor.fetchall():
                art = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'feed_url': row[4]
                }
                
                # Récupérer les thèmes
                cursor.execute("""
                    SELECT theme_id
                    FROM theme_analyses
                    WHERE article_id = ?
                """, (art['id'],))
                art['themes'] = [r[0] for r in cursor.fetchall()]
                
                articles.append(art)
            
            # Pool de candidats (articles récents)
            cursor.execute("""
                SELECT id, title, content, pub_date, feed_url,
                       sentiment_type, sentiment_score
                FROM articles 
                WHERE pub_date >= DATE('now', '-7 days')
                ORDER BY pub_date DESC
                LIMIT 300
            """)
            
            recent_articles = []
            for row in cursor.fetchall():
                cand = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'feed_url': row[4],
                    'sentiment_type': row[5],
                    'sentiment_score': row[6]
                }
                
                cursor.execute("""
                    SELECT theme_id
                    FROM theme_analyses
                    WHERE article_id = ?
                """, (cand['id'],))
                cand['themes'] = [r[0] for r in cursor.fetchall()]
                
                recent_articles.append(cand)
            
            conn.close()
            
            # Traitement batch
            stats = corroboration_engine.batch_process_articles(
                articles,
                recent_articles,
                db_manager
            )
            
            return jsonify({
                'success': True,
                'stats': stats
            })
            
        except Exception as e:
            logger.error(f"Erreur batch corroboration: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/corroboration/stats/<int:article_id>')
    def get_article_corroboration_stats(article_id):
        """Récupère les statistiques de corroboration pour un article"""
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
            count = row[0] if row else 0
            avg_similarity = row[1] if row else 0
            
            # Corroborations détaillées
            cursor.execute("""
                SELECT ac.similar_article_id, ac.similarity_score,
                       a.title, a.sentiment_type
                FROM article_corroborations ac
                JOIN articles a ON ac.similar_article_id = a.id
                WHERE ac.article_id = ?
                ORDER BY ac.similarity_score DESC
                LIMIT 10
            """, (article_id,))
            
            corroborations = []
            for row in cursor.fetchall():
                corroborations.append({
                    'article_id': row[0],
                    'similarity': row[1],
                    'title': row[2],
                    'sentiment': row[3]
                })
            
            conn.close()
            
            return jsonify({
                'article_id': article_id,
                'corroboration_count': count,
                'average_similarity': round(avg_similarity, 4) if avg_similarity else 0,
                'top_corroborations': corroborations
            })
            
        except Exception as e:
            logger.error(f"Erreur stats corroboration: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================
    # ROUTE COMBINÉE : ANALYSE COMPLÈTE
    # ============================================================
    
    @app.route('/api/advanced/full-analysis/<int:article_id>', methods=['POST'])
    def full_advanced_analysis(article_id):
        """Analyse complète : corroboration + bayésien"""
        try:
            # 1. Trouver les corroborations
            corr_response = find_article_corroborations(article_id)
            corr_data = corr_response.get_json()
            
            if not corr_data.get('success'):
                return jsonify({'error': 'Erreur corroboration'}), 500
            
            # 2. Récupérer l'article pour l'analyse bayésienne
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, title, content, sentiment_score, sentiment_type
                FROM articles WHERE id = ?
            """, (article_id,))
            
            row = cursor.fetchone()
            if not row:
                return jsonify({'error': 'Article non trouvé'}), 404
            
            article = {
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'sentiment_score': row[3],
                'sentiment_type': row[4]
            }
            
            conn.close()
            
            # 3. Analyse bayésienne avec corroborations
            corroborations = get_corroborations_for_article(article_id, db_manager)
            bayes_result = bayesian_analyzer.analyze_article_sentiment(article, corroborations)
            
            return jsonify({
                'success': True,
                'article_id': article_id,
                'corroboration': {
                    'count': len(corr_data.get('corroborations', [])),
                    'articles': corr_data.get('corroborations', [])
                },
                'bayesian_analysis': bayes_result
            })
            
        except Exception as e:
            logger.error(f"Erreur analyse complète: {e}")
            return jsonify({'error': str(e)}), 500
    
    # ============================================================
    # ROUTE POUR L'HISTORIQUE DES ANALYSES
    # ============================================================
    
    @app.route('/api/analyzed-articles')
    def get_analyzed_articles():
        """Récupère la liste des articles ayant été analysés avec le système avancé"""
        try:
            limit = int(request.args.get('limit', 50))
            
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Articles avec analyse bayésienne OU corroboration
            cursor.execute("""
                SELECT DISTINCT 
                    a.id,
                    a.title,
                    a.content,
                    a.pub_date,
                    a.sentiment_score,
                    a.sentiment_type,
                    a.bayesian_confidence,
                    a.bayesian_evidence_count,
                    a.analyzed_at,
                    (SELECT COUNT(*) FROM article_corroborations 
                     WHERE article_id = a.id) as corroboration_count
                FROM articles a
                WHERE (a.bayesian_confidence IS NOT NULL 
                       OR EXISTS (
                           SELECT 1 FROM article_corroborations 
                           WHERE article_id = a.id
                       ))
                ORDER BY a.analyzed_at DESC, a.pub_date DESC
                LIMIT ?
            """, (limit,))
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2][:200] if row[2] else '',
                    'pub_date': row[3],
                    'sentiment_score': row[4],
                    'sentiment_type': row[5],
                    'bayesian_confidence': row[6],
                    'bayesian_evidence_count': row[7],
                    'analyzed_at': row[8],
                    'corroboration_count': row[9]
                })
            
            conn.close()
            
            return jsonify(articles)
            
        except Exception as e:
            logger.error(f"Erreur récupération articles analysés: {e}")
            return jsonify({'error': str(e)}), 500
    
    logger.info("✅ Routes avancées enregistrées (avec /api/analyzed-articles)")


def get_corroborations_for_article(article_id, db_manager):
    """Récupère les corroborations d'un article depuis la base"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT ac.similar_article_id, ac.similarity_score,
                   a.sentiment_score, a.sentiment_type, a.title
            FROM article_corroborations ac
            JOIN articles a ON ac.similar_article_id = a.id
            WHERE ac.article_id = ?
            ORDER BY ac.similarity_score DESC
            LIMIT 10
        """, (article_id,))
        
        corroborations = []
        for row in cursor.fetchall():
            corroborations.append({
                'similar_article_id': row[0],
                'similarity_score': row[1],
                'sentiment_score': row[2],
                'sentiment_type': row[3],
                'title': row[4]
            })
        
        return corroborations
    finally:
        conn.close()

    # routes pdf advanced-analysis rajout maj 2811 debug

    @app.route('/api/generate-pdf', methods=['POST'])
    def generate_pdf_report():
        """Génère un PDF à partir du contenu HTML"""
        try:
            data = request.get_json()
            html_content = data.get('html_content', '')
            title = data.get('title', 'Rapport GEOPOL')

            if not html_content:
                return jsonify({'success': False, 'error': 'Contenu HTML requis'}), 400

            # Utiliser une bibliothèque PDF comme weasyprint ou xhtml2pdf
            # Solution temporaire : retourner le HTML pour le moment
            return jsonify({
                'success': True,
                'message': 'Génération PDF à implémenter',
                'html_content': html_content,
                'title': title
            }), 200

        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500




    @app.route('/api/generate-ia-report', methods=['POST'])
    def generate_ia_report():
        """Génère un rapport d'analyse IA"""
    try:
        data = request.get_json()
        
        # Simulation de génération de rapport
        report_data = {
            'success': True,
            'report_type': data.get('report_type', 'géopolitique'),
            'articles_analyzed': 150,
            'themes_covered': data.get('themes', []),
            'period': f"{data.get('start_date', '2024-01-01')} à {data.get('end_date', '2024-01-07')}",
            'analysis_html': '<h1>Rapport d\'analyse géopolitique</h1><p>Ceci est un rapport simulé. L\'intégration IA complète est en cours de développement.</p>',
            'llama_status': {'success': True, 'mode': 'simulation'}
        }
        
        return jsonify(report_data), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

