# Flask/entity_routes.py - Routes API pour entités géopolitiques
from flask import Blueprint, jsonify, request
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def register_entity_routes(app, db_manager, entity_extractor, entity_db_manager):
    """
    Enregistre les routes pour les entités géopolitiques
    
    Args:
        app: Application Flask
        db_manager: Gestionnaire de base de données
        entity_extractor: GeopoliticalEntityExtractor
        entity_db_manager: EntityDatabaseManager
    """
    
    @app.route('/api/entities/extract', methods=['POST'])
    def extract_entities():
        """Extrait les entités d'un texte donné"""
        try:
            data = request.get_json()
            text = data.get('text', '')
            
            if not text:
                return jsonify({'error': 'Texte requis'}), 400
            
            entities = entity_extractor.extract_entities(text)
            
            return jsonify({
                'success': True,
                'entities': entities
            })
        
        except Exception as e:
            logger.error(f"Erreur extraction entités: {e}")
            return jsonify({'error': str(e)}), 500

    # ========== Routes de visualisation de la cartographie ===========

    @app.route('/templates/geo_map_visualization.html')
    def serve_geo_map():
        """Sert la page de visualisation cartographique depuis templates/"""
    try:
        with open('templates/geo_map_visualization.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Erreur chargement carte: {str(e)}", 500
    
    @app.route('/api/entities/analyze-article/<int:article_id>', methods=['POST'])
    def analyze_article_entities(article_id):
        """Analyse et stocke les entités d'un article"""
        try:
            # Récupérer l'article
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT title, content
                FROM articles
                WHERE id = ?
            """, (article_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return jsonify({'error': 'Article non trouvé'}), 404
            
            article = {
                'title': row[0],
                'content': row[1]
            }
            
            # Extraire entités
            full_text = f"{article['title']}. {article['content']}"
            entities = entity_extractor.extract_entities(full_text)
            
            # Stocker en base
            success = entity_db_manager.store_article_entities(article_id, entities)
            
            if success:
                return jsonify({
                    'success': True,
                    'article_id': article_id,
                    'entities': entities,
                    'message': 'Entités extraites et stockées'
                })
            else:
                return jsonify({'error': 'Erreur stockage'}), 500
        
        except Exception as e:
            logger.error(f"Erreur analyse article {article_id}: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/entities/batch-analyze', methods=['POST'])
    def batch_analyze_articles():
        """Analyse en masse les articles non traités"""
        try:
            data = request.get_json() or {}
            limit = data.get('limit', 100)
            
            # Récupérer articles sans entités
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT a.id, a.title, a.content
                FROM articles a
                LEFT JOIN article_entities ae ON a.id = ae.article_id
                WHERE ae.id IS NULL
                LIMIT ?
            """, (limit,))
            
            articles = cursor.fetchall()
            conn.close()
            
            processed = 0
            errors = 0
            
            for article_id, title, content in articles:
                try:
                    full_text = f"{title}. {content}"
                    entities = entity_extractor.extract_entities(full_text)
                    
                    if entity_db_manager.store_article_entities(article_id, entities):
                        processed += 1
                    else:
                        errors += 1
                
                except Exception as e:
                    logger.error(f"Erreur traitement article {article_id}: {e}")
                    errors += 1
            
            return jsonify({
                'success': True,
                'processed': processed,
                'errors': errors,
                'total': len(articles)
            })
        
        except Exception as e:
            logger.error(f"Erreur batch analyze: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/entities/top', methods=['GET'])
    def get_top_entities():
        """Récupère les entités les plus fréquentes"""
        try:
            category = request.args.get('category')
            limit = int(request.args.get('limit', 20))
            
            entities = entity_db_manager.get_top_entities(category, limit)
            
            return jsonify({
                'success': True,
                'entities': entities,
                'category': category,
                'count': len(entities)
            })
        
        except Exception as e:
            logger.error(f"Erreur récupération top entités: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/entities/statistics/<entity_text>', methods=['GET'])
    def get_entity_stats(entity_text):
        """Récupère les statistiques d'une entité"""
        try:
            stats = entity_db_manager.get_entity_statistics(entity_text)
            
            if not stats:
                return jsonify({'error': 'Entité non trouvée'}), 404
            
            return jsonify({
                'success': True,
                'statistics': stats
            })
        
        except Exception as e:
            logger.error(f"Erreur stats entité: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/entities/network', methods=['GET'])
    def get_entity_network():
        """Récupère le réseau d'entités pour visualisation"""
        try:
            min_strength = float(request.args.get('min_strength', 1.0))
            limit = int(request.args.get('limit', 100))
            
            network = entity_db_manager.get_entity_network(min_strength, limit)
            
            return jsonify({
                'success': True,
                'network': network,
                'nodes_count': len(network['nodes']),
                'links_count': len(network['links'])
            })
        
        except Exception as e:
            logger.error(f"Erreur réseau entités: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/entities/search', methods=['GET'])
    def search_entities():
        """Recherche d'entités"""
        try:
            search_term = request.args.get('q', '')
            category = request.args.get('category')
            
            if not search_term:
                return jsonify({'error': 'Terme de recherche requis'}), 400
            
            results = entity_db_manager.search_entities(search_term, category)
            
            return jsonify({
                'success': True,
                'results': results,
                'count': len(results)
            })
        
        except Exception as e:
            logger.error(f"Erreur recherche entités: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/entities/article/<int:article_id>', methods=['GET'])
    def get_article_entities(article_id):
        """Récupère les entités d'un article spécifique"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    e.entity_text,
                    e.entity_type,
                    e.category,
                    ae.context
                FROM article_entities ae
                JOIN geopolitical_entities e ON ae.entity_id = e.id
                WHERE ae.article_id = ?
            """, (article_id,))
            
            entities = []
            for row in cursor.fetchall():
                entities.append({
                    'text': row[0],
                    'type': row[1],
                    'category': row[2],
                    'context': row[3]
                })
            
            conn.close()
            
            return jsonify({
                'success': True,
                'article_id': article_id,
                'entities': entities,
                'count': len(entities)
            })
        
        except Exception as e:
            logger.error(f"Erreur entités article: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/entities/categories', methods=['GET'])
    def get_entity_categories():
        """Récupère la répartition par catégories"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT category, COUNT(*) as count, SUM(occurrence_count) as total_mentions
                FROM geopolitical_entities
                GROUP BY category
                ORDER BY count DESC
            """)
            
            categories = [
                {
                    'category': row[0],
                    'unique_count': row[1],
                    'total_mentions': row[2]
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return jsonify({
                'success': True,
                'categories': categories
            })
        
        except Exception as e:
            logger.error(f"Erreur catégories: {e}")
            return jsonify({'error': str(e)}), 500
    
    logger.info("[OK] Routes entités géopolitiques enregistrées")
