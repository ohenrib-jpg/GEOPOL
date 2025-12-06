# Flask/weak_indicators/routes.py - VERSION CORRIGÉE ET AMÉLIORÉE

from flask import Blueprint, jsonify, request, render_template
import logging
from datetime import datetime
import asyncio
import sys

logger = logging.getLogger(__name__)

def create_weak_indicators_blueprint(db_manager, config=None):
    """Crée le blueprint des Weak Indicators avec gestion d'erreur robuste"""
    
    weak_bp = Blueprint('weak_indicators', __name__)
    
    # Configuration par défaut
    if config is None:
        config = {
            'real_mode': False,
            'sdr_enabled': True,
            'travel_enabled': True,
            'financial_enabled': True
        }
    
    # Initialiser le service avec gestion d'erreur robuste
    weak_indicators_service = None
    try:
        from .service import WeakIndicatorsService
        weak_indicators_service = WeakIndicatorsService(db_manager, config)
        logger.info("✅ Service Weak Indicators initialisé dans le blueprint")
    except ImportError as e:
        logger.error(f"❌ Erreur import service: {e}")
        weak_indicators_service = None
    except Exception as e:
        logger.error(f"❌ Erreur initialisation service dans blueprint: {e}")
        weak_indicators_service = None
    
    # === ROUTE PRINCIPALE DU DASHBOARD ===
    @weak_bp.route('/weak-indicators/api/dashboard')
    async def get_dashboard():
        """Endpoint principal du dashboard - VERSION CORRIGÉE"""
        try:
            if not weak_indicators_service:
                return jsonify({
                    'success': True,
                    'data': {
                        'sdr': {
                            'active_monitors': [
                                {'frequency': '14300 kHz', 'status': 'active', 'signal_strength': -65},
                                {'frequency': '2182 kHz', 'status': 'active', 'signal_strength': -72}
                            ],
                            'total_monitors': 2,
                            'last_scan': datetime.now().isoformat(),
                            'source': 'fallback_service'
                        },
                        'travel': {
                            'countries': [
                                {'code': 'FR', 'name': 'France', 'risk_level': 1, 'advice': 'Normal'},
                                {'code': 'UA', 'name': 'Ukraine', 'risk_level': 4, 'advice': 'Avoid all travel'}
                            ],
                            'last_update': datetime.now().isoformat(),
                            'source': 'fallback_service'
                        },
                        'financial': {
                            'indices': {
                                'CAC40': {'value': 7345.67, 'change': +1.2},
                                'S&P500': {'value': 5123.45, 'change': +0.8}
                            },
                            'last_update': datetime.now().isoformat(),
                            'source': 'fallback_service'
                        }
                    },
                    'metadata': {
                        'timestamp': datetime.now().isoformat(),
                        'real_mode': False,
                        'services_available': {
                            'sdr': False, 
                            'travel': False, 
                            'financial': False
                        }
                    }
                }), 200
            
            # Exécuter la coroutine asynchrone
            data = await weak_indicators_service.get_dashboard_data()
            return jsonify(data)
            
        except Exception as e:
            logger.error(f"❌ Erreur critique dans get_dashboard: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    # === ROUTE STATUT ===
    @weak_bp.route('/weak-indicators/api/status')
    def get_status():
        """Statut des services"""
        try:
            if not weak_indicators_service:
                return jsonify({
                    'success': True,
                    'status': 'fallback',
                    'services': {
                        'sdr': {'available': False, 'mode': 'fallback'},
                        'travel': {'available': False, 'mode': 'fallback'},
                        'financial': {'available': False, 'mode': 'fallback'}
                    },
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Service en mode fallback'
                }), 200
            
            return jsonify(weak_indicators_service.get_service_status())
        except Exception as e:
            logger.error(f"Erreur statut: {e}")
            return jsonify({
                'success': True,
                'status': 'error_fallback',
                'timestamp': datetime.now().isoformat(),
                'message': f'Erreur: {str(e)}'
            }), 200
    
    # === ROUTES SPÉCIFIQUES ===
    @weak_bp.route('/weak-indicators/api/sdr/monitors')
    async def get_sdr_monitors():
        """Données SDR spécifiques"""
        try:
            if not weak_indicators_service or not weak_indicators_service.sdr_service:
                return jsonify({
                    'success': True,
                    'data': {
                        'active_monitors': [
                            {
                                'frequency': '14300 kHz',
                                'description': 'Fréquence diplomatique internationale',
                                'status': 'active',
                                'signal_strength': -65,
                                'last_activity': datetime.now().isoformat()
                            }
                        ],
                        'total_active': 1,
                        'last_scan': datetime.now().isoformat(),
                        'source': 'fallback_route'
                    }
                }), 200
            
            data = await weak_indicators_service.sdr_service.get_active_monitoring()
            return jsonify({'success': True, 'data': data})
            
        except Exception as e:
            logger.error(f"Erreur SDR: {e}")
            return jsonify({
                'success': True, 
                'data': {
                    'active_monitors': [],
                    'error': str(e),
                    'fallback': True,
                    'source': 'error_fallback'
                }
            }), 200
    
    @weak_bp.route('/weak-indicators/api/travel/countries')
    async def get_travel_countries():
        """Données voyage spécifiques"""
        try:
            if not weak_indicators_service or not weak_indicators_service.travel_service:
                return jsonify({
                    'success': True,
                    'data': {
                        'countries': [
                            {
                                'country_code': 'FR',
                                'country_name': 'France',
                                'risk_level': 1,
                                'advice': 'Précautions normales',
                                'last_updated': datetime.now().isoformat(),
                                'sources': ['fallback_route']
                            }
                        ],
                        'total_countries': 1,
                        'last_update': datetime.now().isoformat(),
                        'source': 'fallback_route'
                    }
                }), 200
            
            data = await weak_indicators_service.travel_service.get_country_risks()
            return jsonify({'success': True, 'data': data})
            
        except Exception as e:
            logger.error(f"Erreur voyage: {e}")
            return jsonify({
                'success': True,
                'data': {
                    'countries': [],
                    'error': str(e),
                    'fallback': True,
                    'source': 'error_fallback'
                }
            }), 200
    
    @weak_bp.route('/weak-indicators/api/financial/markets')
    async def get_financial_data():
        """Données financières spécifiques"""
        try:
            if not weak_indicators_service or not weak_indicators_service.financial_service:
                return jsonify({
                    'success': True,
                    'data': {
                        'commodities': {
                            'XAU': {
                                'name': 'Or',
                                'current_price': 1832.50,
                                'change_percent': 0.8,
                                'anomaly': False,
                                'fallback': True
                            }
                        },
                        'indices': {
                            '^FCHI': {
                                'name': 'CAC 40',
                                'current_price': 7345.67,
                                'change_percent': 1.2,
                                'trend': 'up',
                                'country': 'France',
                                'fallback': True
                            }
                        },
                        'last_update': datetime.now().isoformat(),
                        'source': 'fallback_route'
                    }
                }), 200
            
            data = await weak_indicators_service.financial_service.get_market_data()
            return jsonify({'success': True, 'data': data})
            
        except Exception as e:
            logger.error(f"Erreur financier: {e}")
            return jsonify({
                'success': True,
                'data': {
                    'commodities': {},
                    'indices': {},
                    'error': str(e),
                    'fallback': True,
                    'source': 'error_fallback'
                }
            }), 200
    
    # === ROUTE HTML ===
    @weak_bp.route('/weak-indicators')
    def weak_indicators_page():
        """Page principale"""
        try:
            return render_template('weak_indicators.html')
        except Exception as e:
            logger.error(f"Erreur rendu template: {e}")
            return f"""
            <html>
                <head><title>Indicateurs Faibles</title></head>
                <body>
                    <h1>Surveillance SDR - Indicateurs Faibles</h1>
                    <p>Module en cours de chargement...</p>
                    <p><a href="/">Retour au tableau de bord</a></p>
                </body>
            </html>
            """, 200
    
    # === ROUTE DE TEST ===
    @weak_bp.route('/weak-indicators/api/test')
    def test_endpoint():
        """Endpoint de test simple"""
        return jsonify({
            'success': True,
            'message': 'API Weak Indicators fonctionnelle',
            'timestamp': datetime.now().isoformat(),
            'service_available': weak_indicators_service is not None,
            'config': config,
            'python_version': sys.version
        }), 200
    
    # === ROUTE DE CONFIGURATION ===
    @weak_bp.route('/weak-indicators/api/config')
    def get_config():
        """Retourne la configuration actuelle"""
        return jsonify({
            'success': True,
            'config': config,
            'service_initialized': weak_indicators_service is not None
        }), 200
    
    logger.info("✅ Blueprint Weak Indicators créé avec succès")
    return weak_bp