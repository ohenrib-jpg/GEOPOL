"""
Routes Flask pour le module Satellite

API REST complète pour :
- Récupération des couches disponibles
- Génération d'URLs de tuiles/WMS
- Activation/désactivation mode avancé
- Métadonnées et recherche
- Page HTML interface utilisateur

Version: 2.0.0
Author: GEOPOL Analytics
"""

from flask import Blueprint, jsonify, request, render_template, session
from typing import Dict, Any
import logging

from .satellite_manager import get_satellite_manager

logger = logging.getLogger(__name__)


def create_satellite_blueprint() -> Blueprint:
    """
    Crée le blueprint Flask pour le module Satellite.

    Returns:
        Blueprint configuré
    """
    bp = Blueprint('satellite', __name__, url_prefix='/satellite')

    # ========================================
    # PAGE HTML
    # ========================================

    @bp.route('/')
    @bp.route('/panel')
    def satellite_panel():
        """
        Page principale du panneau satellite.

        Returns:
            Template HTML
        """
        try:
            return render_template('satellite_panel.html')
        except Exception as e:
            logger.error(f"❌ Erreur chargement template: {e}")
            return f"Erreur: {e}", 500

    # ========================================
    # API - COUCHES DISPONIBLES
    # ========================================

    @bp.route('/api/layers', methods=['GET'])
    def get_layers():
        """
        Récupère toutes les couches satellite disponibles.

        Query params:
            - category: Filter by category (satellite, basemap, thematic)
            - type: Filter by type (satellite, basemap, wms)
            - use_cache: Use cache (default: true)

        Returns:
            {
                "success": true,
                "layers": {...},
                "count": 26,
                "advanced_enabled": false
            }
        """
        try:
            manager = get_satellite_manager()

            # Paramètres
            category = request.args.get('category')
            layer_type = request.args.get('type')
            use_cache = request.args.get('use_cache', 'true').lower() == 'true'

            # Récupérer les couches
            layers = manager.get_available_layers(use_cache=use_cache)

            # Filtrer si nécessaire
            if category:
                layers = {
                    k: v for k, v in layers.items()
                    if v.get('category') == category
                }

            if layer_type:
                layers = {
                    k: v for k, v in layers.items()
                    if v.get('type') == layer_type
                }

            # Statut mode avancé
            advanced_enabled = manager._is_advanced_mode_enabled()

            return jsonify({
                'success': True,
                'layers': layers,
                'count': len(layers),
                'advanced_enabled': advanced_enabled
            })

        except Exception as e:
            logger.error(f"❌ Erreur récupération couches: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/layers/<layer_id>', methods=['GET'])
    def get_layer_metadata(layer_id: str):
        """
        Récupère les métadonnées d'une couche spécifique.

        Args:
            layer_id: Identifiant de la couche

        Returns:
            {
                "success": true,
                "layer": {...}
            }
        """
        try:
            manager = get_satellite_manager()
            metadata = manager.get_layer_metadata(layer_id)

            if metadata:
                return jsonify({
                    'success': True,
                    'layer': metadata
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Couche {layer_id} non trouvée'
                }), 404

        except Exception as e:
            logger.error(f"❌ Erreur métadonnées couche: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # ========================================
    # API - GÉNÉRATION URLS
    # ========================================

    @bp.route('/api/layer-url/<layer_id>', methods=['GET'])
    def get_layer_url(layer_id: str):
        """
        Génère l'URL pour une couche satellite.

        Args:
            layer_id: Identifiant de la couche

        Query params:
            - bbox: Bounding box (min_lon,min_lat,max_lon,max_lat)
            - width: Width in pixels (default: 512)
            - height: Height in pixels (default: 512)
            - date: Date YYYY-MM-DD (optional, for Sentinel)

        Returns:
            {
                "success": true,
                "url": "https://...",
                "layer_id": "s2cloudless"
            }
        """
        try:
            manager = get_satellite_manager()

            # Paramètres
            bbox_str = request.args.get('bbox')
            width = request.args.get('width', 512, type=int)
            height = request.args.get('height', 512, type=int)
            date = request.args.get('date')

            # Parser bbox si fourni
            bbox = None
            if bbox_str:
                try:
                    bbox = tuple(map(float, bbox_str.split(',')))
                    if len(bbox) != 4:
                        raise ValueError("Bbox doit avoir 4 valeurs")
                except ValueError as e:
                    return jsonify({
                        'success': False,
                        'error': f'Bbox invalide: {e}'
                    }), 400

            # Générer l'URL
            url = manager.get_layer_url(
                layer_id=layer_id,
                bbox=bbox,
                width=width,
                height=height,
                date=date
            )

            if url:
                return jsonify({
                    'success': True,
                    'url': url,
                    'layer_id': layer_id
                })
            else:
                return jsonify({
                    'success': False,
                    'error': f'Impossible de générer URL pour {layer_id}'
                }), 404

        except Exception as e:
            logger.error(f"❌ Erreur génération URL: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # ========================================
    # API - RECOMMANDATIONS
    # ========================================

    @bp.route('/api/recommend', methods=['POST'])
    def recommend_layers():
        """
        Recommande les meilleures couches pour une zone.

        Body:
            {
                "bbox": [min_lon, min_lat, max_lon, max_lat],
                "purpose": "general|vegetation|urban|disaster|maritime",
                "max_layers": 3
            }

        Returns:
            {
                "success": true,
                "recommended": ["s2cloudless", "osm_standard", ...],
                "purpose": "general"
            }
        """
        try:
            manager = get_satellite_manager()

            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Body JSON requis'
                }), 400

            bbox = data.get('bbox')
            purpose = data.get('purpose', 'general')
            max_layers = data.get('max_layers', 3)

            if not bbox or len(bbox) != 4:
                return jsonify({
                    'success': False,
                    'error': 'Bbox valide requis [min_lon, min_lat, max_lon, max_lat]'
                }), 400

            # Recommander
            recommended = manager.get_recommended_layers(
                bbox=tuple(bbox),
                purpose=purpose,
                max_layers=max_layers
            )

            return jsonify({
                'success': True,
                'recommended': recommended,
                'purpose': purpose,
                'count': len(recommended)
            })

        except Exception as e:
            logger.error(f"❌ Erreur recommandation: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # ========================================
    # API - RECHERCHE
    # ========================================

    @bp.route('/api/search', methods=['GET'])
    def search_layers():
        """
        Recherche de couches par mot-clé.

        Query params:
            - query: Search query
            - category: Filter by category (optional)
            - limit: Max results (default: 10)

        Returns:
            {
                "success": true,
                "results": [...],
                "count": 5,
                "query": "sentinel"
            }
        """
        try:
            manager = get_satellite_manager()

            query = request.args.get('query', '')
            category = request.args.get('category')
            limit = request.args.get('limit', 10, type=int)

            if not query:
                return jsonify({
                    'success': False,
                    'error': 'Query parameter required'
                }), 400

            # Rechercher
            results = manager.search_layers(
                query=query,
                category=category,
                limit=limit
            )

            return jsonify({
                'success': True,
                'results': results,
                'count': len(results),
                'query': query
            })

        except Exception as e:
            logger.error(f"❌ Erreur recherche: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # ========================================
    # API - MODE AVANCÉ
    # ========================================

    @bp.route('/api/advanced/enable', methods=['POST'])
    def enable_advanced_mode():
        """
        Active le mode avancé avec identifiants Sentinel Hub.

        Body:
            {
                "client_id": "your-client-id",
                "client_secret": "your-client-secret"
            }

        Returns:
            {
                "success": true,
                "message": "Mode avancé activé"
            }
        """
        try:
            manager = get_satellite_manager()

            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Body JSON requis'
                }), 400

            client_id = data.get('client_id')
            client_secret = data.get('client_secret')

            if not client_id or not client_secret:
                return jsonify({
                    'success': False,
                    'error': 'client_id et client_secret requis'
                }), 400

            # Activer
            success = manager.enable_advanced_mode(client_id, client_secret)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'Mode avancé activé avec succès'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Échec validation identifiants'
                }), 401

        except Exception as e:
            logger.error(f"❌ Erreur activation mode avancé: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/advanced/disable', methods=['POST'])
    def disable_advanced_mode():
        """
        Désactive le mode avancé.

        Returns:
            {
                "success": true,
                "message": "Mode avancé désactivé"
            }
        """
        try:
            manager = get_satellite_manager()
            manager.disable_advanced_mode()

            return jsonify({
                'success': True,
                'message': 'Mode avancé désactivé'
            })

        except Exception as e:
            logger.error(f"❌ Erreur désactivation mode avancé: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/advanced/status', methods=['GET'])
    def get_advanced_status():
        """
        Récupère le statut du mode avancé.

        Returns:
            {
                "success": true,
                "enabled": true,
                "has_credentials": true
            }
        """
        try:
            manager = get_satellite_manager()
            enabled = manager._is_advanced_mode_enabled()

            return jsonify({
                'success': True,
                'enabled': enabled,
                'has_credentials': enabled
            })

        except Exception as e:
            logger.error(f"❌ Erreur statut mode avancé: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # ========================================
    # API - CACHE
    # ========================================

    @bp.route('/api/cache/clear', methods=['POST'])
    def clear_cache():
        """
        Vide le cache du gestionnaire satellite.

        Returns:
            {
                "success": true,
                "message": "Cache vidé"
            }
        """
        try:
            manager = get_satellite_manager()
            manager.clear_cache()

            return jsonify({
                'success': True,
                'message': 'Cache vidé avec succès'
            })

        except Exception as e:
            logger.error(f"❌ Erreur vidage cache: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # ========================================
    # HEALTH CHECK
    # ========================================

    @bp.route('/api/health', methods=['GET'])
    def health_check():
        """
        Vérification de santé du module satellite.

        Returns:
            {
                "success": true,
                "status": "healthy",
                "sources_loaded": true,
                "advanced_available": false
            }
        """
        try:
            manager = get_satellite_manager()

            return jsonify({
                'success': True,
                'status': 'healthy',
                'sources_loaded': manager.sources is not None,
                'advanced_available': manager._is_advanced_mode_enabled(),
                'cache_size': len(manager.cache)
            })

        except Exception as e:
            logger.error(f"❌ Erreur health check: {e}")
            return jsonify({
                'success': False,
                'status': 'unhealthy',
                'error': str(e)
            }), 500

    logger.info("✅ Blueprint Satellite créé")
    return bp
