# Flask/routes_indicators_enhanced.py
"""
Routes Flask pour le dashboard économique amélioré
Utilise le connecteur unifié (Eurostat + INSEE + yFinance)
"""

from flask import Blueprint, jsonify, request, render_template, Response
import logging
from datetime import datetime
import json
from io import StringIO
import csv

logger = logging.getLogger(__name__)


def create_indicators_blueprint_enhanced(db_manager):
    """Crée le blueprint amélioré des indicateurs économiques"""
    
    indicators_bp = Blueprint('indicators', __name__, url_prefix='/indicators')
    
    # Initialiser le connecteur unifié
    from .enhanced_indicators_connector import EnhancedIndicatorsConnector
    from .indicators_alerts import IndicatorAlerts
    
    connector = EnhancedIndicatorsConnector(db_manager)
    alerts_system = IndicatorAlerts(db_manager)
    
    # === PAGE PRINCIPALE ===
    @indicators_bp.route('/')
    def indicators_page():
        """Page principale du dashboard"""
        return render_template('indicators_dashboard.html')
    
    # === API DASHBOARD COMPLET ===
    @indicators_bp.route('/api/dashboard')
    def get_dashboard():
        """
        Récupère toutes les données du dashboard
        Endpoint principal recommandé
        """
        try:
            data = connector.get_dashboard_data()
            
            # Ajouter les alertes
            if data.get('success') and data.get('indicators'):
                alerts = alerts_system.check_alerts(data['indicators'])
                alert_summary = alerts_system.get_alert_summary(data['indicators'])
                
                data['alerts'] = {
                    'items': alerts,
                    'summary': alert_summary
                }
            
            return jsonify(data)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_dashboard: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === API INDICATEURS (rétrocompatibilité) ===
    @indicators_bp.route('/api/data')
    def get_indicators_data():
        """
        API rétrocompatible pour les indicateurs
        Récupère les données des indicateurs
        """
        try:
            # Récupérer toutes les données
            dashboard = connector.get_dashboard_data()
            
            # Formater pour rétrocompatibilité
            result = {
                'success': True,
                'indicators': {},
                'stats': {
                    'total': len(dashboard['indicators']),
                    'successful': len(dashboard['indicators']),
                    'failed': 0
                },
                'timestamp': dashboard['timestamp']
            }
            
            # Convertir au format attendu
            for ind_id, indicator in dashboard['indicators'].items():
                result['indicators'][ind_id] = {
                    'success': True,
                    'indicator_id': indicator['id'],
                    'indicator_name': indicator['name'],
                    'current_value': indicator['value'],
                    'unit': indicator['unit'],
                    'period': indicator['period'],
                    'change_percent': indicator['change_percent'],
                    'change_direction': indicator['change_direction'],
                    'source': indicator['source'],
                    'category': indicator['category'],
                    'description': indicator['description'],
                    'last_update': indicator['last_update'],
                    'reliability': indicator['reliability']
                }
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_indicators_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @indicators_bp.route('/api/available')
    def get_available_indicators():
        """Liste des indicateurs disponibles"""
        try:
            result = connector.get_available_indicators()
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_available_indicators: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @indicators_bp.route('/api/indicator/<indicator_id>')
    def get_single_indicator(indicator_id):
        """Récupère un indicateur spécifique"""
        try:
            result = connector.get_indicator_by_id(indicator_id)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_single_indicator: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === API DONNÉES FINANCIÈRES ===
    @indicators_bp.route('/api/indices')
    def get_financial_indices():
        """Récupère les indices boursiers"""
        try:
            dashboard = connector.get_dashboard_data()
            return jsonify(dashboard['financial_markets'])
            
        except Exception as e:
            logger.error(f"❌ Erreur get_financial_indices: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @indicators_bp.route('/api/historical/<symbol>')
    def get_historical_data(symbol):
        """Données historiques d'un indice"""
        try:
            period = request.args.get('period', '6mo')
            result = connector.yfinance.get_historical_data(symbol, period)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_historical_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === RAFRAÎCHISSEMENT ===
    @indicators_bp.route('/api/refresh', methods=['POST'])
    def force_refresh():
        """Force le rafraîchissement de toutes les sources"""
        try:
            logger.info("🔄 Rafraîchissement forcé demandé")
            result = connector.force_refresh()
            
            # Ajouter les alertes aux données rafraîchies
            if result.get('success') and result.get('indicators'):
                alerts = alerts_system.check_alerts(result['indicators'])
                alert_summary = alerts_system.get_alert_summary(result['indicators'])
                
                result['alerts'] = {
                    'items': alerts,
                    'summary': alert_summary
                }
            
            return jsonify({
                'success': True,
                'message': 'Données rafraîchies',
                'data': result
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur force_refresh: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === ALERTES ===
    @indicators_bp.route('/api/alerts')
    def get_alerts():
        """Récupère les alertes actives"""
        try:
            dashboard = connector.get_dashboard_data()
            if dashboard.get('success') and dashboard.get('indicators'):
                alerts = alerts_system.check_alerts(dashboard['indicators'])
                summary = alerts_system.get_alert_summary(dashboard['indicators'])
                
                return jsonify({
                    'success': True,
                    'alerts': alerts,
                    'summary': summary,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': True,
                    'alerts': [],
                    'summary': {'total_alerts': 0},
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"❌ Erreur get_alerts: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === COMPARAISON INTERNATIONALE ===
    @indicators_bp.route('/api/compare/<countries>')
    def compare_countries(countries):
        """Compare les indicateurs entre plusieurs pays"""
        try:
            country_list = countries.split(',')
            # Pour l'instant, seulement France - extension future
            if 'FR' in country_list:
                dashboard = connector.get_dashboard_data()
                return jsonify({
                    'success': True,
                    'comparison': {
                        'FR': {
                            'name': 'France',
                            'indicators': dashboard.get('indicators', {}),
                            'financial_markets': dashboard.get('financial_markets', {})
                        }
                    },
                    'timestamp': datetime.now().isoformat()
                })
            else:
                return jsonify({
                    'success': False,
                    'error': "Seule la France est supportée pour l'instant"
                })
                
        except Exception as e:
            logger.error(f"❌ Erreur compare_countries: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === EXPORT DES DONNÉES ===
    @indicators_bp.route('/api/export/<format>')
    def export_data(format):
        """Export des données dans différents formats"""
        try:
            dashboard = connector.get_dashboard_data()
            
            if format.lower() == 'json':
                return jsonify(dashboard)
            
            elif format.lower() == 'csv':
                output = StringIO()
                writer = csv.writer(output)
                
                # En-têtes
                writer.writerow(['ID', 'Nom', 'Valeur', 'Unité', 'Période', 'Variation %', 'Source', 'Catégorie'])
                
                # Données
                for ind_id, indicator in dashboard.get('indicators', {}).items():
                    writer.writerow([
                        indicator.get('id', ind_id),
                        indicator.get('name', ''),
                        indicator.get('value', ''),
                        indicator.get('unit', ''),
                        indicator.get('period', ''),
                        indicator.get('change_percent', ''),
                        indicator.get('source', ''),
                        indicator.get('category', '')
                    ])
                
                csv_data = output.getvalue()
                output.close()
                
                return Response(
                    csv_data,
                    mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment; filename=indicators_export.csv'}
                )
            
            else:
                return jsonify({
                    'success': False,
                    'error': 'Format non supporté (json, csv)'
                }), 400
                
        except Exception as e:
            logger.error(f"❌ Erreur export_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === STATUT DU SYSTÈME ===
    @indicators_bp.route('/api/status')
    def get_status():
        """Statut détaillé du système"""
        try:
            dashboard = connector.get_dashboard_data()
            
            # Ajouter les alertes au statut
            alerts_summary = {}
            if dashboard.get('success') and dashboard.get('indicators'):
                from .indicators_alerts import IndicatorAlerts
                temp_alerts = IndicatorAlerts()
                alerts_summary = temp_alerts.get_alert_summary(dashboard['indicators'])
            
            return jsonify({
                'success': True,
                'system_status': 'operational',
                'data_sources': dashboard['sources_status'],
                'data_quality': dashboard['summary']['data_quality'],
                'total_indicators': dashboard['summary']['total_indicators'],
                'reliability_breakdown': dashboard['summary']['by_reliability'],
                'alerts_summary': alerts_summary,
                'timestamp': datetime.now().isoformat(),
                'note': 'Dashboard éducatif - Sources: Eurostat (officiel), INSEE (scraping), Yahoo Finance'
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_status: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === GESTION DES PRÉFÉRENCES (maintenu pour compatibilité) ===
    @indicators_bp.route('/api/preferences', methods=['GET', 'POST'])
    def manage_preferences():
        """Sauvegarde/récupère les préférences utilisateur"""
        try:
            if request.method == 'POST':
                data = request.get_json()
                selected_indicators = data.get('selected_indicators', [])
                display_settings = data.get('display_settings', {})
                
                # Sauvegarder en DB
                if db_manager:
                    conn = db_manager.get_connection()
                    cur = conn.cursor()
                    
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS user_indicator_preferences (
                            user_id TEXT PRIMARY KEY,
                            selected_indicators TEXT,
                            display_settings TEXT,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    
                    cur.execute("""
                        INSERT OR REPLACE INTO user_indicator_preferences 
                        (user_id, selected_indicators, display_settings, updated_at)
                        VALUES (?, ?, ?, ?)
                    """, ('default', json.dumps(selected_indicators), json.dumps(display_settings), datetime.now().isoformat()))
                    
                    conn.commit()
                    conn.close()
                
                return jsonify({
                    'success': True,
                    'message': 'Préférences sauvegardées',
                    'selected_indicators': selected_indicators,
                    'display_settings': display_settings
                })
            
            else:  # GET
                if db_manager:
                    conn = db_manager.get_connection()
                    cur = conn.cursor()
                    
                    cur.execute("""
                        SELECT selected_indicators, display_settings FROM user_indicator_preferences 
                        WHERE user_id = 'default'
                    """)
                    
                    row = cur.fetchone()
                    conn.close()
                    
                    if row:
                        selected = json.loads(row[0]) if row[0] else []
                        display = json.loads(row[1]) if row[1] else {}
                    else:
                        selected = ['eurostat_gdp', 'eurostat_unemployment', 'eurostat_hicp', 'insee_inflation']
                        display = {}
                else:
                    selected = ['eurostat_gdp', 'eurostat_unemployment', 'eurostat_hicp', 'insee_inflation']
                    display = {}
                
                return jsonify({
                    'success': True,
                    'selected_indicators': selected,
                    'display_settings': display
                })
                
        except Exception as e:
            logger.error(f"❌ Erreur manage_preferences: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === ENDPOINT DE SANTÉ ===
    @indicators_bp.route('/api/health')
    def health_check():
        """Health check endpoint"""
        try:
            dashboard = connector.get_dashboard_data()
            
            # Vérifier que nous avons au moins quelques données
            has_data = len(dashboard['indicators']) > 0
            
            # Vérifier les sources
            sources_operational = all(status == 'operational' 
                                    for status in dashboard['sources_status'].values())
            
            return jsonify({
                'status': 'healthy' if (has_data and sources_operational) else 'degraded',
                'indicators_count': len(dashboard['indicators']),
                'data_quality': dashboard['summary']['data_quality'],
                'sources': dashboard['sources_status'],
                'sources_operational': sources_operational,
                'timestamp': datetime.now().isoformat()
            }), 200 if (has_data and sources_operational) else 503
            
        except Exception as e:
            logger.error(f"❌ Erreur health_check: {e}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 503
    
    return indicators_bp