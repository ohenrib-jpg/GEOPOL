# Geo/Flask/learning_routes.py
"""
Routes pour le système d'apprentissage continu
"""

from flask import Blueprint, jsonify, request
import logging

from .database import DatabaseManager
from .continuous_learning import get_learning_engine

logger = logging.getLogger(__name__)

def create_learning_blueprint(db_manager: DatabaseManager) -> Blueprint:
    """Créer le blueprint pour l'apprentissage continu"""
    
    learning_bp = Blueprint('learning', __name__, url_prefix='/api/learning')
    
    @learning_bp.route('/feedback', methods=['POST'])
    def submit_feedback():
        """Soumettre un feedback utilisateur"""
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({'error': 'Données manquantes'}), 400
            
            required_fields = ['article_id', 'predicted_sentiment', 'corrected_sentiment', 'text_content']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Champ manquant: {field}'}), 400
            
            # Obtenir le learning engine
            from .sentiment_analyzer import SentimentAnalyzer
            sentiment_analyzer = SentimentAnalyzer()
            learning_engine = get_learning_engine(db_manager, sentiment_analyzer)
            
            # Collecter le feedback
            learning_engine.collect_feedback(
                article_id=data['article_id'],
                predicted_sentiment=data['predicted_sentiment'],
                corrected_sentiment=data['corrected_sentiment'],
                text_content=data['text_content'],
                confidence=data.get('confidence', 0.5)
            )
            
            return jsonify({
                'status': 'success',
                'message': 'Feedback collecté avec succès'
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur feedback: {e}")
            return jsonify({'error': str(e)}), 500
    
    @learning_bp.route('/feedback/stats', methods=['GET'])
    def get_feedback_stats():
        """Obtenir les statistiques des feedbacks"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Stats générales
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed,
                    SUM(CASE WHEN processed = 0 THEN 1 ELSE 0 END) as pending
                FROM learning_feedback
            """)
            
            stats = cursor.fetchone()
            
            # Distribution par sentiment corrigé
            cursor.execute("""
                SELECT corrected_sentiment, COUNT(*) as count
                FROM learning_feedback
                GROUP BY corrected_sentiment
                ORDER BY count DESC
            """)
            
            sentiment_distribution = []
            for row in cursor.fetchall():
                sentiment_distribution.append({
                    'sentiment': row[0],
                    'count': row[1]
                })
            
            conn.close()
            
            return jsonify({
                'total_feedbacks': stats[0] if stats else 0,
                'processed_feedbacks': stats[1] if stats else 0,
                'pending_feedbacks': stats[2] if stats else 0,
                'sentiment_distribution': sentiment_distribution
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur stats feedback: {e}")
            return jsonify({'error': str(e)}), 500
    
    @learning_bp.route('/model/status', methods=['GET'])
    def get_model_status():
        """Obtenir le statut du modèle d'apprentissage"""
        try:
            from .sentiment_analyzer import SentimentAnalyzer
            sentiment_analyzer = SentimentAnalyzer()
            learning_engine = get_learning_engine(db_manager, sentiment_analyzer)
            
            # Vérifier si le modèle existe
            import os
            model_path = os.path.join('instance', 'continuous_learning_model.pth')
            model_exists = os.path.exists(model_path)
            
            # Obtenir les stats de feedback
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM learning_feedback WHERE processed = 0")
            pending_feedbacks = cursor.fetchone()[0]
            
            conn.close()
            
            return jsonify({
                'model_exists': model_exists,
                'pending_feedbacks': pending_feedbacks,
                'min_feedback_threshold': learning_engine.min_feedback_threshold,
                'learning_rate': learning_engine.learning_rate
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur statut modèle: {e}")
            return jsonify({'error': str(e)}), 500
    
    @learning_bp.route('/test-prediction', methods=['POST'])
    def test_prediction():
        """Tester une prédiction avec le modèle continu"""
        try:
            data = request.get_json()
            
            if not data or 'text' not in data:
                return jsonify({'error': 'Texte manquant'}), 400
            
            from .sentiment_analyzer import SentimentAnalyzer
            sentiment_analyzer = SentimentAnalyzer()
            learning_engine = get_learning_engine(db_manager, sentiment_analyzer)
            
            result = learning_engine.predict_sentiment(data['text'])
            
            return jsonify(result), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur test prédiction: {e}")
            return jsonify({'error': str(e)}), 500
    
    # NOUVELLE ROUTE POUR DÉCLENCHEMENT MANUEL
    @learning_bp.route('/trigger-learning', methods=['POST'])
    def trigger_learning():
        """Déclencher manuellement une session d'apprentissage"""
        try:
            from .sentiment_analyzer import SentimentAnalyzer
            sentiment_analyzer = SentimentAnalyzer()
            learning_engine = get_learning_engine(db_manager, sentiment_analyzer)
            
            # Déclencher l'apprentissage
            learning_engine._check_and_trigger_learning()
            
            return jsonify({
                'status': 'success',
                'message': 'Apprentissage déclenché'
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement apprentissage: {e}")
            return jsonify({'error': str(e)}), 500
    
    return learning_bp
