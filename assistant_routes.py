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
            
            logger.info(f"[CHAT] Requête chat reçue: '{user_message[:50]}...'")
            
            if not user_message:
                return jsonify({
                    'success': False, 
                    'error': 'Message vide',
                    'response': 'Veuillez poser une question sur la géopolitique, l\'économie ou l\'analyse des données.'
                }), 400
            
            # Récupérer le client depuis l'application
            llama_client = current_app.config.get('LLAMA_CLIENT')
            if not llama_client:
                logger.error("[ERROR] LLAMA_CLIENT non trouvé dans app.config")
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
            
            logger.info(f"[OK] Réponse chat générée - Succès: {result.get('success', False)}")
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"[ERROR] Erreur critique endpoint chat: {e}", exc_info=True)
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
                    logger.info(f"[OK] Statut assistant: {message}")
                else:
                    logger.warning(f"[WARN] Statut assistant: {message}")
                    
                return jsonify(status_info)
            else:
                logger.error("[ERROR] Assistant non initialisé - LLAMA_CLIENT manquant")
                return jsonify({
                    'success': False,
                    'connected': False,
                    'message': 'Assistant non initialisé',
                    'service': 'Mistral 7B Assistant'
                }), 503
                
        except Exception as e:
            logger.error(f"[ERROR] Erreur statut assistant: {e}")
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

    @assistant_bp.route('/local-search', methods=['POST'])
    def local_search():
        """
        Effectue une recherche RAG locale multi-sources
        Combine cache + database + RSS + web scraping
        """
        try:
            data = request.get_json()
            query = data.get('query', '').strip()

            if not query:
                return jsonify({
                    'success': False,
                    'error': 'Requête de recherche vide'
                }), 400

            # Paramètres optionnels
            top_k = data.get('top_k', 10)
            sources = data.get('sources')  # None = toutes les sources
            search_depth = data.get('depth', 'medium')  # light, medium, deep

            logger.info(f"[SEARCH] RAG Search: '{query}' (depth={search_depth}, top_k={top_k})")

            # Récupérer le RAG pipeline
            rag_pipeline = current_app.config.get('RAG_PIPELINE')
            if not rag_pipeline:
                # Créer le pipeline si pas déjà fait
                from rag_pipeline import create_rag_pipeline
                rag_pipeline = create_rag_pipeline(db_manager=db_manager)
                current_app.config['RAG_PIPELINE'] = rag_pipeline

            # Ajuster selon la profondeur
            if search_depth == 'light':
                sources = ['cache', 'database']
                top_k = min(top_k, 5)
            elif search_depth == 'medium':
                sources = ['cache', 'database', 'rss']
                top_k = min(top_k, 10)
            elif search_depth == 'deep':
                sources = ['cache', 'database', 'rss', 'web']
                top_k = min(top_k, 20)

            # Exécuter la recherche RAG
            documents, context = rag_pipeline.search(query, top_k=top_k, sources=sources)

            # Formatter les résultats pour le frontend
            results = []
            for doc in documents:
                results.append({
                    'title': doc.title,
                    'content': doc.content[:300] + '...' if len(doc.content) > 300 else doc.content,
                    'source': doc.source,
                    'source_type': doc.source_type,
                    'url': doc.url,
                    'relevance_score': doc.relevance_score,
                    'timestamp': doc.timestamp.isoformat() if doc.timestamp else None
                })

            logger.info(f"[OK] RAG Search: {len(results)} résultats trouvés")

            return jsonify({
                'success': True,
                'query': query,
                'results': results,
                'count': len(results),
                'context': context,
                'depth': search_depth,
                'sources_used': sources
            })

        except Exception as e:
            logger.error(f"[ERROR] Erreur recherche RAG locale: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Erreur interne du serveur',
                'message': str(e)
            }), 500

    return assistant_bp