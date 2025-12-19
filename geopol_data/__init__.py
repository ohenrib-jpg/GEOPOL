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
    'SDR_CONFIG',
    'init_meteo_module',
    'init_earthquake_module',
    'init_config_module',
    'init_sdr_coverage_module',
    'init_sdr_dashboard_module'
]

def init_geopol_data_module(app, db_manager):
    """
    Initialise le module Geopol-Data pour l'application Flask.
    """
    try:
        from .routes import create_geopol_data_blueprint
        from .service import get_data_service
        from .connectors.sdr_scraper import SDRScraper

        # Récupérer ou créer le service
        service = get_data_service()

        # Créer le scraper SDR avec cache de 10 minutes
        sdr_scraper = SDRScraper(cache_ttl_minutes=10)
        logging.getLogger(__name__).info("📡 SDR Scraper initialisé (cache: 10 min)")

        # Créer le blueprint principal avec le scraper
        blueprint = create_geopol_data_blueprint(db_manager, service, sdr_scraper)
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

def init_meteo_module(app):
    """Initialise le module Open-Meteo"""
    try:
        from .meteo_integration import get_meteo_integration
        from .open_meteo_routes import create_open_meteo_blueprint

        # Créer l'instance d'intégration
        meteo_integration = get_meteo_integration()

        # Créer le blueprint API
        meteo_bp = create_open_meteo_blueprint(meteo_integration)

        # Enregistrer dans l'app
        app.register_blueprint(meteo_bp)

        # Pré-charger les données des pays prioritaires (optionnel)
        # meteo_integration.preload_priority_countries()

        logging.getLogger(__name__).info("✅ Module Open-Meteo initialisé")

        return {
            'integration': meteo_integration,
            'blueprint': meteo_bp
        }

    except Exception as e:
        logging.getLogger(__name__).error(f"❌ Erreur initialisation Open-Meteo: {e}")
        import traceback
        traceback.print_exc()
        return None

def init_earthquake_module(app):
    """Initialise le module USGS Earthquake"""
    try:
        from .earthquake_integration import get_earthquake_integration
        from .earthquake_routes import create_earthquake_blueprint

        # Créer l'instance d'intégration
        earthquake_integration = get_earthquake_integration()

        # Créer le blueprint API
        earthquake_bp = create_earthquake_blueprint(earthquake_integration)

        # Enregistrer dans l'app
        app.register_blueprint(earthquake_bp)

        logging.getLogger(__name__).info("✅ Module USGS Earthquake initialisé")

        return {
            'integration': earthquake_integration,
            'blueprint': earthquake_bp
        }

    except Exception as e:
        logging.getLogger(__name__).error(f"❌ Erreur initialisation Earthquake: {e}")
        import traceback
        traceback.print_exc()
        return None

def init_config_module(app):
    """Initialise le module de gestion des profils de configuration"""
    try:
        from .config_routes import config_bp

        # Enregistrer le blueprint
        app.register_blueprint(config_bp)

        logging.getLogger(__name__).info("✅ Module Gestion des Profils initialisé")

        return {
            'blueprint': config_bp
        }

    except Exception as e:
        logging.getLogger(__name__).error(f"❌ Erreur initialisation Config Manager: {e}")
        import traceback
        traceback.print_exc()
        return None

def init_sdr_coverage_module(app, db_manager):
    """Initialise le module de calcul de couverture SDR"""
    try:
        from .sdr_monitoring.coverage_calculator import CoverageCalculator, CoverageConfig
        from .sdr_coverage_routes import create_sdr_coverage_blueprint

        # Créer l'instance du calculateur de couverture
        coverage_config = CoverageConfig()
        coverage_calculator = CoverageCalculator(coverage_config)

        # Créer le blueprint API
        coverage_bp = create_sdr_coverage_blueprint(db_manager, coverage_calculator)

        # Enregistrer dans l'app
        app.register_blueprint(coverage_bp)

        logging.getLogger(__name__).info("✅ Module SDR Coverage initialisé")

        return {
            'calculator': coverage_calculator,
            'blueprint': coverage_bp
        }

    except Exception as e:
        logging.getLogger(__name__).error(f"❌ Erreur initialisation SDR Coverage: {e}")
        import traceback
        traceback.print_exc()
        return None

def init_sdr_dashboard_module(app, db_manager, sdr_analyzer=None):
    """Initialise le module Dashboard SDR temps réel"""
    try:
        from .sdr_monitoring.dashboard_manager import DashboardManager
        from .sdr_dashboard_routes import (
            create_sdr_dashboard_blueprint,
            create_sdr_dashboard_page_blueprint
        )

        # Créer l'instance du dashboard manager
        dashboard_manager = DashboardManager(db_manager, sdr_analyzer)

        # Créer les blueprints
        dashboard_api_bp = create_sdr_dashboard_blueprint(db_manager, dashboard_manager, sdr_analyzer)
        dashboard_page_bp = create_sdr_dashboard_page_blueprint()

        # Enregistrer dans l'app
        app.register_blueprint(dashboard_api_bp)
        app.register_blueprint(dashboard_page_bp)

        logging.getLogger(__name__).info("✅ Module SDR Dashboard initialisé")

        return {
            'manager': dashboard_manager,
            'api_blueprint': dashboard_api_bp,
            'page_blueprint': dashboard_page_bp
        }

    except Exception as e:
        logging.getLogger(__name__).error(f"❌ Erreur initialisation SDR Dashboard: {e}")
        import traceback
        traceback.print_exc()
        return None