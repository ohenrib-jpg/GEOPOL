"""
Module Economique - GEOPOL Analytics
Blueprint factory pour le module des indicateurs economiques

Refonte complete - Version 2.0
"""
import logging
from flask import Blueprint

logger = logging.getLogger(__name__)

def create_economic_blueprint(db_manager):
    """
    Factory pour creer le blueprint du module economique

    Args:
        db_manager: Instance du DatabaseManager

    Returns:
        Blueprint configure pour le module economique
    """
    logger.info("[ECONOMIC] Initialisation du module economique v2.0...")

    # Creation du blueprint principal
    economic_bp = Blueprint('economic', __name__, url_prefix='/economic')

    try:
        # Import des services
        from .services.france_service import FranceService
        from .services.commodity_service import CommodityService
        from .services.market_service import MarketService
        from .services.watchlist_service import WatchlistService
        from .services.international_service import InternationalService
        from .services.alert_service import AlertService
        from .services.trade_service import TradeService
        from .services.crypto_service import CryptoService

        # Initialisation des services
        france_service = FranceService(db_manager)
        logger.info("[ECONOMIC] FranceService initialise")

        commodity_service = CommodityService(db_manager)
        logger.info("[ECONOMIC] CommodityService initialise")

        market_service = MarketService(db_manager)
        logger.info("[ECONOMIC] MarketService initialise")

        watchlist_service = WatchlistService(db_manager)
        logger.info("[ECONOMIC] WatchlistService initialise")

        international_service = InternationalService(db_manager)
        logger.info("[ECONOMIC] InternationalService initialise")

        alert_service = AlertService(db_manager)
        logger.info("[ECONOMIC] AlertService initialise")

        trade_service = TradeService(db_manager)
        logger.info("[ECONOMIC] TradeService initialise")

        crypto_service = CryptoService(db_manager)
        logger.info("[ECONOMIC] CryptoService initialise")

        # Initialisation du scheduler d'alertes
        from .schedulers.alert_scheduler import AlertScheduler
        alert_scheduler = AlertScheduler(
            alert_service=alert_service,
            market_service=market_service,
            commodity_service=commodity_service,
            international_service=international_service,
            france_service=france_service
        )
        logger.info("[ECONOMIC] AlertScheduler initialise")

        # Démarrer le scheduler si configuré
        from .config import EconomicConfig
        if EconomicConfig.SCHEDULER_ENABLED:
            try:
                alert_scheduler.start(interval_minutes=EconomicConfig.ALERT_CHECK_INTERVAL_MINUTES)
                logger.info(f"[ECONOMIC] Scheduler démarré (intervalle: {EconomicConfig.ALERT_CHECK_INTERVAL_MINUTES} minutes)")
            except Exception as e:
                logger.error(f"[ECONOMIC] Erreur démarrage scheduler: {e}")
        else:
            logger.info("[ECONOMIC] Scheduler désactivé (configuration)")

        # Import des routes
        from .routes import pages, api_indicators, api_commodities, api_markets, api_watchlist, api_international, api_alerts, api_trade, api_crypto

        # Injection des services dans les APIs
        api_indicators.init_service(france_service)
        api_commodities.init_service(commodity_service)
        api_markets.init_service(market_service)
        api_watchlist.init_service(watchlist_service)
        api_international.init_service(international_service)
        api_alerts.init_service(alert_service)
        api_trade.init_trade_api(trade_service)
        api_crypto.init_crypto_api(crypto_service)

        # Enregistrement des blueprints de routes
        economic_bp.register_blueprint(pages.pages_bp)
        economic_bp.register_blueprint(api_indicators.api_bp, url_prefix='/api')
        economic_bp.register_blueprint(api_commodities.api_bp, url_prefix='/api')
        economic_bp.register_blueprint(api_markets.api_bp, url_prefix='/api')
        economic_bp.register_blueprint(api_watchlist.api_bp, url_prefix='/api')
        economic_bp.register_blueprint(api_international.api_bp, url_prefix='/api')
        economic_bp.register_blueprint(api_alerts.api_bp, url_prefix='/api')
        economic_bp.register_blueprint(api_trade.api_bp, url_prefix='/api')
        economic_bp.register_blueprint(api_crypto.api_bp, url_prefix='/api')

        logger.info("[ECONOMIC] Routes enregistrees:")
        logger.info("  - Pages: /economic/")
        logger.info("  - API: /economic/api/indicators/france")
        logger.info("  - API: /economic/api/international/available-indicators")
        logger.info("  - API: /economic/api/international/selected-indicators")
        logger.info("  - API: /economic/api/international/historical/<id>")
        logger.info("  - API: /economic/api/commodities")
        logger.info("  - API: /economic/api/markets/indices")
        logger.info("  - API: /economic/api/markets/summary")
        logger.info("  - API: /economic/api/watchlist (GET/POST/DELETE)")
        logger.info("  - API: /economic/api/watchlist/stats")
        logger.info("  - API: /economic/api/health")
        logger.info("  - API: /economic/api/stats")
        logger.info("  - API: /economic/api/alerts (GET/POST/PUT/DELETE)")
        logger.info("  - API: /economic/api/alerts/triggered")
        logger.info("  - API: /economic/api/alerts/stats")

        # Configuration du contexte du blueprint
        @economic_bp.before_request
        def before_request():
            """Hook avant chaque requete"""
            pass

        @economic_bp.after_request
        def after_request(response):
            """Hook apres chaque requete"""
            response.headers['X-Economic-Module-Version'] = '2.0'
            return response

        logger.info("[ECONOMIC] Module economique v2.0 pret!")

    except Exception as e:
        logger.error(f"[ECONOMIC] Erreur initialisation module: {e}")
        import traceback
        traceback.print_exc()
        raise

    return economic_bp

# Export du factory
__all__ = ['create_economic_blueprint']
