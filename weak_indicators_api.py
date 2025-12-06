# geo/Flask/weak_indicators_api.py
from flask import Blueprint, jsonify, request
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
weak_indicators_bp = Blueprint('weak_indicators', __name__)

# Globales pour les services
sdr_analyzer = None
travel_advisor = None
financial_watcher = None

def register_weak_indicators_api(app, db_manager):
    """Enregistre l'API des indicateurs faibles"""
    global sdr_analyzer, travel_advisor, financial_watcher
    
    # Initialiser les services
    from .sdr_analyzer import SDRAnalyzer, init_sdr_database
    from .travel_advisor import TravelAdvisor, init_travel_database
    from .financial_watcher import FinancialWatcher, init_financial_database
    
    sdr_analyzer = SDRAnalyzer(db_manager)
    travel_advisor = TravelAdvisor(db_manager)
    financial_watcher = FinancialWatcher(db_manager)
    
    # Initialiser les bases de données
    init_sdr_database(db_manager)
    init_travel_database(db_manager)
    init_financial_database(db_manager)
    
    # Enregistrer les routes
    app.register_blueprint(weak_indicators_bp, url_prefix='/api/weak-indicators')
    
    logger.info("✅ API Indicateurs Faibles enregistrée")

@weak_indicators_bp.route('/sdr/monitor', methods=['GET'])
async def monitor_sdr():
    """Endpoint de monitoring SDR"""
    try:
        results = await sdr_analyzer.monitor_geopolitical_bands()
        return jsonify({
            'success': True,
            'data': results,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur API SDR: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@weak_indicators_bp.route('/travel/advisories', methods=['GET'])
async def get_travel_advisories():
    """Endpoint des avis de voyage"""
    try:
        results = await travel_advisor.fetch_advisories()
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        logger.error(f"Erreur API Voyage: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@weak_indicators_bp.route('/financial/commodities', methods=['GET'])
async def monitor_commodities():
    """Endpoint de surveillance financière"""
    try:
        results = await financial_watcher.monitor_strategic_commodities()
        return jsonify({
            'success': True,
            'data': results,
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur API Financière: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@weak_indicators_bp.route('/dashboard', methods=['GET'])
async def get_dashboard():
    """Endpoint du dashboard consolidé"""
    try:
        # Exécuter toutes les analyses en parallèle
        sdr_task = sdr_analyzer.monitor_geopolitical_bands()
        travel_task = travel_advisor.fetch_advisories()
        financial_task = financial_watcher.monitor_strategic_commodities()
        
        sdr_data, travel_data, financial_data = await asyncio.gather(
            sdr_task, travel_task, financial_task,
            return_exceptions=True
        )
        
        return jsonify({
            'success': True,
            'sdr_monitoring': sdr_data if not isinstance(sdr_data, Exception) else {'error': str(sdr_data)},
            'travel_advisories': travel_data if not isinstance(travel_data, Exception) else {'error': str(travel_data)},
            'financial_monitoring': financial_data if not isinstance(financial_data, Exception) else {'error': str(financial_data)},
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Erreur Dashboard: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
