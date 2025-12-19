# Geo/Flask/routes_learning_integrated.py
"""
Routes intégrées pour l'apprentissage continu
"""

from flask import jsonify, request  # ← CORRECTION CRITIQUE: ajout de 'request'
from .database import DatabaseManager
from .continuous_learning import get_learning_engine

def register_learning_routes(app, db_manager: DatabaseManager):
    """Enregistrer les routes d'apprentissage intégrées"""
    
    @app.route('/api/learning/collect-feedback', methods=['POST'])
    def collect_user_feedback():
        """Collecter le feedback utilisateur depuis l'interface"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'Données manquantes'}), 400
            
            required_fields = ['article_id', 'predicted', 'corrected', 'text']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Champ manquant: {field}'}), 400
            
            # Obtenir le sentiment analyzer et learning engine
            sentiment_analyzer = app.config.get('SENTIMENT_ANALYZER')
            if not sentiment_analyzer:
                from .sentiment_analyzer import SentimentAnalyzer
                sentiment_analyzer = SentimentAnalyzer()
            
            learning_engine = get_learning_engine(db_manager, sentiment_analyzer)
            
            # Collecter le feedback
            learning_engine.collect_feedback(
                article_id=data['article_id'],
                predicted_sentiment=data['predicted'],
                corrected_sentiment=data['corrected'],
                text_content=data['text'],
                confidence=data.get('confidence', 0.5)
            )
            
            return jsonify({
                'status': 'success',
                'message': 'Feedback enregistré avec succès'
            }), 200
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Erreur collecte feedback: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/learning/predict/<int:article_id>', methods=['GET'])
    def predict_with_continuous_model(article_id):
        """Prédire le sentiment avec le modèle continu"""
        try:
            # Récupérer l'article
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT title, content FROM articles WHERE id = ?
            """, (article_id,))
            
            article = cursor.fetchone()
            conn.close()
            
            if not article:
                return jsonify({'error': 'Article non trouvé'}), 404
            
            # Obtenir le learning engine
            sentiment_analyzer = app.config.get('SENTIMENT_ANALYZER')
            if not sentiment_analyzer:
                from .sentiment_analyzer import SentimentAnalyzer
                sentiment_analyzer = SentimentAnalyzer()
            
            learning_engine = get_learning_engine(db_manager, sentiment_analyzer)
            
            # Prédiction
            text = f"{article[0]} {article[1]}"
            result = learning_engine.predict_sentiment(text)
            
            return jsonify(result), 200
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Erreur prédiction continue: {e}")
            return jsonify({'error': str(e)}), 500
