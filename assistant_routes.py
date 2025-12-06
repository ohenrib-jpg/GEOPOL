# Flask/assistant_routes.py - VERSION CORRIGÉE AVEC GESTION D'ERREUR AMÉLIORÉE
from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def create_assistant_blueprint(db_manager):
    assistant_bp = Blueprint('assistant', __name__, url_prefix='/api/assistant')
    
    @assistant_bp.route('/chat', methods=['POST'])
    def assistant_chat():
        """Endpoint chat simple pour l'assistant - VERSION ROBUSTE"""
        try:
            data = request.get_json(silent=True) or {}
            user_message = data.get('message', '').strip()
            
            logger.info(f"💬 Requête chat reçue: '{user_message[:50]}...'")
            
            if not user_message:
                return jsonify({
                    'success': False, 
                    'error': 'Message vide',
                    'response': 'Veuillez poser une question sur la géopolitique, l\'économie ou l\'analyse des données.'
                }), 400
            
            # Récupérer le client depuis l'application
            llama_client = current_app.config.get('LLAMA_CLIENT')
            if not llama_client:
                logger.error("❌ LLAMA_CLIENT non trouvé dans app.config")
                return jsonify({
                    'success': False,
                    'error': 'Assistant non configuré',
                    'response': 'Le service d\'assistant IA n\'est pas configuré.'
                }), 503
            
            # Contexte simple
            context = {
                'timestamp': datetime.now().isoformat(),
                'source': 'assistant_chat'
            }
            
            # Générer la réponse avec timeout
            result = llama_client.generate_chat_response(user_message, context)
            
            logger.info(f"✅ Réponse chat générée - Succès: {result.get('success', False)}")
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur critique endpoint chat: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Erreur interne du serveur',
                'response': "Désolé, une erreur technique s'est produite. Veuillez réessayer plus tard."
            }), 500

    @assistant_bp.route('/status', methods=['GET'])
    def assistant_status():
        """Statut du serveur Mistral"""
        try:
            llama_client = current_app.config.get('LLAMA_CLIENT')
            if llama_client:
                connected, message = llama_client.test_connection()
                
                status_info = {
                    'success': True,
                    'connected': connected,
                    'message': message,
                    'endpoint': llama_client.endpoint,
                    'service': 'Mistral 7B Assistant'
                }
                
                if connected:
                    logger.info(f"✅ Statut assistant: {message}")
                else:
                    logger.warning(f"⚠️ Statut assistant: {message}")
                    
                return jsonify(status_info)
            else:
                logger.error("❌ Assistant non initialisé - LLAMA_CLIENT manquant")
                return jsonify({
                    'success': False,
                    'connected': False,
                    'message': 'Assistant non initialisé',
                    'service': 'Mistral 7B Assistant'
                }), 503
                
        except Exception as e:
            logger.error(f"❌ Erreur statut assistant: {e}")
            return jsonify({
                'success': False,
                'connected': False,
                'message': f'Erreur: {str(e)}',
                'service': 'Mistral 7B Assistant'
            }), 500

    @assistant_bp.route('/test', methods=['GET'])
    def test_assistant():
        """Test simple de l'assistant"""
        try:
            llama_client = current_app.config.get('LLAMA_CLIENT')
            if not llama_client:
                return jsonify({
                    'success': False,
                    'message': 'Client non disponible'
                })
            
            # Test de connexion
            connected, msg = llama_client.test_connection()
            
            return jsonify({
                'success': True,
                'connected': connected,
                'message': msg,
                'timestamp': datetime.now().isoformat(),
                'endpoint': llama_client.endpoint
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })

    return assistant_bp