# Flask/geopol_data/__init__.py
"""
Module Geopol-Data
Données géopolitiques via World Bank, Open-Meteo et Natural Earth

Version: 1.0.0
Author: GEOPOL Analytics
"""

__version__ = '1.0.0'
__author__ = 'GEOPOL Analytics'

import logging

# Imports principaux
from .models import CountrySnapshot, GeopoliticalIndex
from .connectors.world_bank import WorldBankConnector, fetch_indicators
from .service import get_data_service, DataService  # AJOUT IMPORTANT

# Import de Config avec fallback absolu pour les environnements IDE qui
# n'interprètent pas correctement les imports relatifs.
try:
    from .config import Config
except Exception:
    try:
        # Fallback : import absolu (chemin de package explicite)
        from Flask.geopol_data.config import Config
    except Exception:
        logging.getLogger(__name__).warning(
            "Impossible d'importer 'Config' depuis .config ou Flask.geopol_data.config."
        )
        Config = None
# Import SDR avec gestion des erreurs

try:
    from .sdr_analyzer import SDRAnalyzer
    from .sdr_config import SDR_CONFIG
except ImportError as e:
    print(f"⚠️  Import SDR échoué: {e}")
    SDRAnalyzer = None
    SDR_CONFIG = None


# Exposer les classes principales
__all__ = [
    'CountrySnapshot',
    'GeopoliticalIndex',
    'SDRAnalyzer',
    'WorldBankConnector',
    'fetch_indicators',
    'DataService',
    'get_data_service',  
    'Config',
    'SDRAnalyzer',         
    'SDR_CONFIG' 
]

def init_geopol_data_module(app, db_manager):
    """
    Initialise le module Geopol-Data pour l'application Flask.
    """
    try:
        from .routes import create_geopol_data_blueprint
        from .service import get_data_service
        
        # Récupérer ou créer le service
        service = get_data_service()
        
        # Créer le blueprint principal
        blueprint = create_geopol_data_blueprint(db_manager, service)
        print("✅ Module Geopol-Data initialisé")       
        return service, blueprint
        
    except Exception as e:
        import traceback
        logging.getLogger(__name__).error(f"Erreur initialisation Geopol-Data: {e}")
        traceback.print_exc()
        return None, None  

    # Ajouter à la fin du fichier existant
def init_sdr_module(app, db_manager):
    """Initialise le module SDR"""
    try:
        from .sdr_analyzer import SDRAnalyzer
        from .sdr_routes import create_sdr_api_blueprint
        from .overlays.sdr_overlay import create_sdr_overlay_layer
        
        # Importer le service SDR existant
        from Flask.sdr_spectrum_service import SDRSpectrumService
        
        # Créer les instances
        sdr_analyzer = SDRAnalyzer(db_manager)
        sdr_service = SDRSpectrumService(db_manager)
        
        # Créer le blueprint API
        sdr_bp = create_sdr_api_blueprint(db_manager, sdr_analyzer, sdr_service)
        
        # Créer la couche Leaflet
        sdr_layer = create_sdr_overlay_layer(db_manager, sdr_analyzer)
        
        # Enregistrer dans l'app
        app.register_blueprint(sdr_bp)
        
        # Ajouter la couche au système de cartes
        if hasattr(app, 'geopol_layers'):
            app.geopol_layers['sdr_health'] = sdr_layer
        
        print.info("✅ Module SDR géopolitique initialisé")
        
        return {
            'analyzer': sdr_analyzer,
            'service': sdr_service,
            'blueprint': sdr_bp,
            'layer': sdr_layer
        }
        
    except Exception as e:
        print.error(f"❌ Erreur initialisation SDR: {e}")
        return None