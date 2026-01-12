"""
Routes pour les pages HTML du module economique
"""
from flask import Blueprint, render_template, current_app
import logging

logger = logging.getLogger(__name__)

# Creation du blueprint pour les pages
pages_bp = Blueprint('economic_pages', __name__)

@pages_bp.route('/')
def dashboard():
    """Dashboard principal du module economique"""
    try:
        return render_template('economic/dashboard.html',
                             page_title='Indicateurs Economiques')
    except Exception as e:
        logger.error(f"[PAGES] Erreur dashboard: {e}")
        return f"Erreur: {e}", 500

@pages_bp.route('/france')
def france():
    """Page indicateurs France"""
    try:
        return render_template('economic/france.html',
                             page_title='Indicateurs France')
    except Exception as e:
        logger.error(f"[PAGES] Erreur page France: {e}")
        return f"Erreur: {e}", 500

@pages_bp.route('/international')
def international():
    """Page indicateurs internationaux"""
    try:
        return render_template('economic/international.html',
                             page_title='Indicateurs Internationaux')
    except Exception as e:
        logger.error(f"[PAGES] Erreur page international: {e}")
        return f"Erreur: {e}", 500

@pages_bp.route('/markets')
def markets():
    """Page marches financiers"""
    try:
        return render_template('economic/markets.html',
                             page_title='Marches Financiers')
    except Exception as e:
        logger.error(f"[PAGES] Erreur page markets: {e}")
        return f"Erreur: {e}", 500

@pages_bp.route('/commodities')
def commodities():
    """Page commodites strategiques"""
    try:
        return render_template('economic/commodities.html',
                             page_title='Commodites Strategiques')
    except Exception as e:
        logger.error(f"[PAGES] Erreur page commodities: {e}")
        return f"Erreur: {e}", 500

@pages_bp.route('/crypto')
def crypto():
    """Page cryptomonnaies"""
    try:
        return render_template('economic/crypto.html',
                             page_title='Cryptomonnaies')
    except Exception as e:
        logger.error(f"[PAGES] Erreur page crypto: {e}")
        return f"Erreur: {e}", 500

@pages_bp.route('/watchlist')
def watchlist():
    """Page surveillance personnalisee"""
    try:
        return render_template('economic/watchlist.html',
                             page_title='Surveillance Personnalisee')
    except Exception as e:
        logger.error(f"[PAGES] Erreur page watchlist: {e}")
        return f"Erreur: {e}", 500

@pages_bp.route('/alerts')
def alerts():
    """Page configuration alertes"""
    try:
        return render_template('economic/alerts.html',
                             page_title='Configuration Alertes')
    except Exception as e:
        logger.error(f"[PAGES] Erreur page alerts: {e}")
        return f"Erreur: {e}", 500
