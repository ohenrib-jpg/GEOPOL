"""
Gestionnaire satellite principal - Thread-safe pour Flask

Architecture :
- Utilise Flask g pour éviter les problèmes de concurrence
- Cache en mémoire pour performances
- Support sources publiques + mode avancé optionnel
- Fallback automatique si mode avancé indisponible

Version: 2.0.0
Author: GEOPOL Analytics
"""

from flask import g, session
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class SatelliteManager:
    """
    Gestionnaire principal satellite - Version thread-safe.

    Utilise Flask g au lieu d'un singleton classique pour garantir
    la thread-safety dans un environnement Flask multi-utilisateurs.
    """

    def __init__(self):
        """Initialisation du gestionnaire."""
        self.sources = None
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes par défaut
        self._init_sources()

        logger.info("📡 SatelliteManager initialisé")

    def _init_sources(self):
        """Initialise le module des sources satellite."""
        try:
            from .satellite_sources import SatelliteSources
            self.sources = SatelliteSources()
            logger.info("[OK] Sources satellite chargées")
        except Exception as e:
            logger.error(f"[ERROR] Erreur chargement sources: {e}")
            self.sources = None

    # ========================================
    # MÉTHODES PRINCIPALES
    # ========================================

    def get_available_layers(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Récupère toutes les couches satellite disponibles.

        Args:
            use_cache: Utiliser le cache ou forcer le rafraîchissement

        Returns:
            Dictionnaire {layer_id: {name, url, type, description, ...}}
        """
        cache_key = "available_layers"

        # Vérifier le cache
        if use_cache and cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() < cached_data['expires']:
                logger.debug("📦 Couches récupérées depuis le cache")
                return cached_data['data']

        # Récupérer les couches
        if not self.sources:
            logger.warning("[WARN] Module sources non disponible")
            return {}

        layers = {}

        # 1. Couches publiques de base
        try:
            public_layers = self.sources.get_public_layers()
            layers.update(public_layers)
            logger.debug(f"[OK] {len(public_layers)} couches publiques chargées")
        except Exception as e:
            logger.error(f"[ERROR] Erreur couches publiques: {e}")

        # 2. Sources WMS publiques
        try:
            wms_layers = self.sources.get_wms_sources()
            layers.update(wms_layers)
            logger.debug(f"[OK] {len(wms_layers)} sources WMS chargées")
        except Exception as e:
            logger.error(f"[ERROR] Erreur sources WMS: {e}")

        # 3. Mode avancé si activé
        if self._is_advanced_mode_enabled():
            try:
                advanced_layers = self._get_advanced_layers()
                layers.update(advanced_layers)
                logger.debug(f"[OK] {len(advanced_layers)} couches avancées chargées")
            except Exception as e:
                logger.warning(f"[WARN] Erreur couches avancées: {e}")

        # 4. Couches Planet si configuré
        try:
            planet_layers = self._get_planet_layers()
            if planet_layers:
                layers.update(planet_layers)
                logger.debug(f"[OK] {len(planet_layers)} couches Planet chargées")
        except Exception as e:
            logger.debug(f"[DEBUG] Planet non disponible: {e}")

        # Mettre en cache
        if use_cache:
            self.cache[cache_key] = {
                'data': layers,
                'expires': datetime.now() + timedelta(seconds=self.cache_ttl)
            }

        logger.info(f"📡 {len(layers)} couches satellite disponibles")
        return layers

    def get_layer_url(
        self,
        layer_id: str,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        width: int = 512,
        height: int = 512,
        date: Optional[str] = None
    ) -> Optional[str]:
        """
        Génère l'URL pour une couche satellite.
        """
        if not self.sources:
            logger.error("[ERROR] Module sources non disponible")
            return None
    
        logger.info(f"[DEBUG] get_layer_url appelé avec layer_id={layer_id}")
        
        try:
            # Essayer mode avancé si disponible
            is_advanced = self._is_advanced_mode_enabled()
            logger.info(f"[DEBUG] Mode avancé activé: {is_advanced}")
            
            if layer_id.startswith(('sentinel', 'SENTINEL')) and is_advanced:
                logger.info(f"[DEBUG] Tentative mode avancé pour {layer_id}")
                if bbox is None:
                    logger.warning("[WARN] Bbox requis pour couches avancées")
                    return None
                    
                url = self._get_advanced_layer_url(layer_id, bbox, width, height, date)
                if url:
                    logger.info(f"[OK] URL avancée générée pour {layer_id}")
                    return url
                logger.warning(f"[WARN] Mode avancé échoué pour {layer_id}")
    
            # Fallback sur sources publiques
            logger.info(f"[DEBUG] Tentative sources publiques pour {layer_id}")
            url = self.sources.get_layer_url(layer_id, bbox, width, height)
    
            if url:
                logger.debug(f"[OK] URL générée pour {layer_id}")
                return url
            else:
                logger.warning(f"[WARN] Aucune URL disponible pour {layer_id}")
                return None
    
        except Exception as e:
            logger.error(f"[ERROR] Erreur génération URL pour {layer_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def get_layer_metadata(self, layer_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les métadonnées d'une couche.

        Args:
            layer_id: Identifiant de la couche

        Returns:
            Métadonnées {name, type, description, resolution, coverage, ...}
        """
        layers = self.get_available_layers(use_cache=True)
        return layers.get(layer_id)

    def get_recommended_layers(
        self,
        bbox: Tuple[float, float, float, float],
        purpose: str = "general",
        max_layers: int = 3
    ) -> List[str]:
        """
        Recommande les meilleures couches pour une région et un usage.

        Args:
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            purpose: Usage (general, vegetation, urban, disaster, maritime)
            max_layers: Nombre maximum de couches à recommander

        Returns:
            Liste d'identifiants de couches recommandées
        """
        recommendations = {
            'general': ['s2cloudless', 'osm_standard', 'esri_world_imagery'],
            'vegetation': ['s2cloudless', 'landsat_8', 'modis_vegetation'],
            'urban': ['esri_world_imagery', 'osm_standard', 'google_hybrid'],
            'disaster': ['s2cloudless', 'sentinel1_grd', 'modis_fires'],
            'maritime': ['s2cloudless', 'gebco_bathymetry', 'osm_standard']
        }

        # Récupérer les recommandations par défaut
        recommended = recommendations.get(purpose, recommendations['general'])

        # Filtrer par disponibilité
        available_layers = self.get_available_layers(use_cache=True)
        available_recommended = [
            layer_id for layer_id in recommended
            if layer_id in available_layers
        ]

        # Limiter au nombre maximum
        return available_recommended[:max_layers]

    def search_layers(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recherche de couches par mot-clé.

        Args:
            query: Mot-clé de recherche
            category: Catégorie optionnelle (satellite, basemap, thematic)
            limit: Nombre maximum de résultats

        Returns:
            Liste de couches correspondantes
        """
        layers = self.get_available_layers(use_cache=True)
        query_lower = query.lower()

        results = []
        for layer_id, metadata in layers.items():
            # Rechercher dans l'ID, le nom et la description
            if (query_lower in layer_id.lower() or
                query_lower in metadata.get('name', '').lower() or
                query_lower in metadata.get('description', '').lower()):

                # Filtrer par catégorie si spécifié
                if category and metadata.get('category') != category:
                    continue

                results.append({
                    'id': layer_id,
                    **metadata
                })

                if len(results) >= limit:
                    break

        return results

    # ========================================
    # GESTION MODE AVANCÉ
    # ========================================

    def _is_advanced_mode_enabled(self) -> bool:
        """Vérifie si le mode avancé est activé."""
        # Vérifier si les identifiants sont en session
        client_id = session.get('satellite_client_id')
        client_secret = session.get('satellite_client_secret')
        return bool(client_id and client_secret)

    def enable_advanced_mode(self, client_id: str, client_secret: str) -> bool:
        """
        Active le mode avancé avec identifiants Sentinel Hub.

        Args:
            client_id: Client ID
            client_secret: Client Secret

        Returns:
            True si activation réussie
        """
        try:
            # Valider les identifiants
            from .satellite_advanced import SatelliteAdvanced
            advanced = SatelliteAdvanced(client_id, client_secret)

            if advanced.test_connection():
                # Stocker en session
                session['satellite_client_id'] = client_id
                session['satellite_client_secret'] = client_secret
                session['satellite_advanced_enabled'] = True

                # Invalider le cache
                self.cache.clear()

                logger.info("[OK] Mode avancé activé")
                return True
            else:
                logger.warning("[WARN] Échec validation identifiants")
                return False

        except Exception as e:
            logger.error(f"[ERROR] Erreur activation mode avancé: {e}")
            return False

    def disable_advanced_mode(self):
        """Désactive le mode avancé."""
        session.pop('satellite_client_id', None)
        session.pop('satellite_client_secret', None)
        session.pop('satellite_advanced_enabled', None)

        # Invalider le cache
        self.cache.clear()

        logger.info("ℹ Mode avancé désactivé")

    def _get_advanced_layers(self) -> Dict[str, Any]:
        """Récupère les couches du mode avancé."""
        try:
            from .satellite_advanced import SatelliteAdvanced

            client_id = session.get('satellite_client_id')
            client_secret = session.get('satellite_client_secret')

            if not client_id or not client_secret:
                return {}

            advanced = SatelliteAdvanced(client_id, client_secret)
            return advanced.get_available_layers()

        except Exception as e:
            logger.error(f"[ERROR] Erreur récupération couches avancées: {e}")
            return {}

    def _get_planet_layers(self) -> Dict[str, Any]:
        """Récupère les couches Planet si configuré."""
        try:
            from .planet_connector import get_planet_connector

            connector = get_planet_connector()
            if connector.is_configured():
                return connector.get_available_layers()
            return {}

        except Exception as e:
            logger.debug(f"[DEBUG] Planet non disponible: {e}")
            return {}

    def _get_advanced_layer_url(
        self,
        layer_id: str,
        bbox: Tuple[float, float, float, float],
        width: int,
        height: int,
        date: Optional[str]
    ) -> Optional[str]:
        """Génère l'URL pour une couche avancée."""
        try:
            from .satellite_advanced import SatelliteAdvanced
    
            client_id = session.get('satellite_client_id')
            client_secret = session.get('satellite_client_secret')
    
            if not client_id or not client_secret:
                logger.warning("[WARN] Identifiants Sentinel Hub non disponibles")
                return None
    
            advanced = SatelliteAdvanced(client_id, client_secret)
            
            # Utiliser la bonne méthode
            url = advanced.get_layer_url(
                layer_id=layer_id,
                bbox=bbox,
                width=width,
                height=height,
                date=date
            )
            
            if url:
                logger.debug(f"[OK] URL générée pour couche avancée {layer_id}")
            else:
                logger.warning(f"[WARN] Aucune URL générée pour {layer_id}")
                
            return url
    
        except Exception as e:
            logger.error(f"[ERROR] Erreur URL couche avancée {layer_id}: {e}")
            return None


    # ========================================
    # GESTION CACHE
    # ========================================

    def clear_cache(self):
        """Vide le cache."""
        self.cache.clear()
        logger.info("🗑 Cache vidé")

    def set_cache_ttl(self, ttl_seconds: int):
        """
        Définit le TTL du cache.

        Args:
            ttl_seconds: Durée de vie en secondes
        """
        self.cache_ttl = ttl_seconds
        logger.info(f"⏱ Cache TTL défini à {ttl_seconds}s")


# ========================================
# FACTORY THREAD-SAFE POUR FLASK
# ========================================

def get_satellite_manager() -> SatelliteManager:
    """
    Factory thread-safe pour récupérer le gestionnaire satellite.

    Utilise Flask g pour garantir une instance par requête.

    Returns:
        Instance de SatelliteManager
    """
    if 'satellite_manager' not in g:
        g.satellite_manager = SatelliteManager()

    return g.satellite_manager
