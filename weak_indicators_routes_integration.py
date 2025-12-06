# Flask/weak_indicators_routes_integration.py
"""
Routes Flask intégrées pour les indicateurs faibles
Utilise les vrais services : Travel Advisories, KiwiSDR, Stock Data
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Blueprint
weak_indicators_integrated_bp = Blueprint('weak_indicators_integrated', __name__, url_prefix='/weak-indicators/api')


def register_integrated_routes(app, db_manager):
    """
    Enregistre toutes les routes des indicateurs divers avec les services op
    """
    
    # ============================================
    # IMPORTATIONS DES SERVICES RÉELS
    # ============================================
    
    try:
        from .travel_advisories_service import TravelAdvisoriesService
        TRAVEL_SERVICE_AVAILABLE = True
    except ImportError:
        logger.error("❌ TravelAdvisoriesService non disponible")
        TRAVEL_SERVICE_AVAILABLE = False
    
    try:
        from .kiwisdr_real_service import KiwiSDRRealService, SDRFrequencyPresets
        KIWISDR_SERVICE_AVAILABLE = True
    except ImportError:
        logger.error("❌ KiwiSDRRealService non disponible")
        KIWISDR_SERVICE_AVAILABLE = False
    
    try:
        from .real_stock_data import RealStockData
        STOCK_SERVICE_AVAILABLE = True
    except ImportError:
        logger.error("❌ RealStockData non disponible")
        STOCK_SERVICE_AVAILABLE = False
    
    # ============================================
    # ROUTES AVIS AUX VOYAGEURS
    # ============================================
    
    @weak_indicators_integrated_bp.route('/travel-advisories/scan', methods=['POST'])
    def scan_travel_advisories():
        """Lance un scan des avis aux voyageurs"""
        if not TRAVEL_SERVICE_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Service Travel Advisories non disponible'
            }), 503
        
        try:
            result = TravelAdvisoriesService.scan_advisories(db_manager)
            return jsonify(result)
        except Exception as e:
            logger.error(f"❌ Erreur scan advisories: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @weak_indicators_integrated_bp.route('/travel-advisories/countries', methods=['GET'])
    def get_travel_countries():
        """Récupère tous les pays avec niveaux de risque"""
        try:
            # Implémentation existante
            countries = []  # Remplacez par votre code
            return jsonify({
                'success': True,
                'countries': countries,
                'total': len(countries)
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @weak_indicators_integrated_bp.route('/status', methods=['GET'])
    def get_services_status():
        """Statut des services"""
        return jsonify({
            'success': True,
            'services': {
                'travel_advisories': True,
                'kiwisdr': True,
                'stock_data': True,
                'sdr_streams': True
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @weak_indicators_integrated_bp.route('/travel-advisories/country/<country_code>', methods=['GET'])
    def get_country_advisory(country_code):
        """Détails d'un pays spécifique"""
        try:
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            # Récupérer toutes les sources pour ce pays
            cur.execute("""
                SELECT country_code, country_name, risk_level, source, summary, last_updated
                FROM travel_advisories
                WHERE country_code = ?
                ORDER BY risk_level DESC
            """, (country_code.upper(),))
            
            rows = cur.fetchall()
            conn.close()
            
            if not rows:
                return jsonify({
                    'success': True,
                    'country': country_code,
                    'advisory': {
                        'country_code': country_code,
                        'risk_level': 1,
                        'sources': [],
                        'recommendations': 'Aucune information disponible'
                    }
                })
            
            # Agréger les sources
            sources = []
            max_risk = 1
            country_name = rows[0][1] or country_code
            
            for row in rows:
                max_risk = max(max_risk, row[2])
                sources.append({
                    'source': row[3],
                    'risk_level': row[2],
                    'summary': row[4],
                    'last_updated': row[5]
                })
            
            return jsonify({
                'success': True,
                'country': country_code,
                'advisory': {
                    'country_code': country_code,
                    'country_name': country_name,
                    'risk_level': max_risk,
                    'sources': sources,
                    'recommendations': f"Niveau de risque maximum : {max_risk}/4",
                    'last_updated': sources[0]['last_updated'] if sources else None
                }
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur country advisory: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ============================================
    # ROUTES SDR STREAMS (CORRECTION)
    # ============================================
    
    @weak_indicators_integrated_bp.route('/sdr-streams', methods=['GET', 'POST'])
    def manage_sdr_streams():
        """Gestion des flux SDR - ROUTE CORRIGÉE"""
        try:
            if request.method == 'GET':
                return get_all_sdr_streams(db_manager)
            else:
                return add_sdr_stream(db_manager)
        except Exception as e:
            logger.error(f"Erreur gestion flux SDR: {e}")
            return jsonify({"error": str(e)}), 500

    @weak_indicators_integrated_bp.route('/sdr-streams/<int:stream_id>', methods=['DELETE'])
    def delete_sdr_stream(stream_id):
        """Supprime un flux SDR"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("DELETE FROM sdr_streams WHERE id = ?", (stream_id,))
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "message": "Flux supprimé"})
        except Exception as e:
            logger.error(f"Erreur suppression flux: {e}")
            return jsonify({"error": str(e)}), 500

    @weak_indicators_integrated_bp.route('/sdr-streams/<int:stream_id>/activity')
    def get_stream_activity(stream_id):
        """Activité d'un flux SDR"""
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT date, activity_count 
                FROM sdr_daily_activity 
                WHERE stream_id = ? AND date >= date('now', '-30 days')
                ORDER BY date
            """, (stream_id,))
            
            activity_data = []
            for row in cur.fetchall():
                activity_data.append({
                    "date": row[0],
                    "activity_count": row[1]
                })
            
            conn.close()
            return jsonify({
                "stream_id": stream_id,
                "activity": activity_data
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ============================================
    # FONCTIONS HELPER POUR SDR STREAMS
    # ============================================

    def get_all_sdr_streams(db_manager):
        """Récupère tous les flux SDR"""
        try:
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, name, url, frequency_khz, type, description, active, created_at
                FROM sdr_streams 
                ORDER BY created_at DESC
            """)
            
            streams = []
            for row in cur.fetchall():
                streams.append({
                    "id": row[0],
                    "name": row[1],
                    "url": row[2],
                    "frequency_khz": row[3],
                    "type": row[4],
                    "description": row[5],
                    "active": bool(row[6]),
                    "created_at": row[7]
                })
            
            conn.close()
            return jsonify(streams)
            
        except Exception as e:
            logger.error(f"Erreur récupération flux SDR: {e}")
            return jsonify({"error": str(e)}), 500

    def add_sdr_stream(db_manager):
        """Ajoute un flux SDR"""
        try:
            data = request.get_json()
            
            if not data or 'name' not in data or 'url' not in data:
                return jsonify({"error": "Champs requis: name, url"}), 400
            
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO sdr_streams (name, url, frequency_khz, type, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data['name'],
                data['url'],
                data.get('frequency_khz', 0),
                data.get('type', 'kiwisdr'),
                data.get('description', '')
            ))
            
            stream_id = cur.lastrowid
            conn.commit()
            conn.close()
            
            return jsonify({
                "success": True,
                "id": stream_id,
                "message": "Flux SDR ajouté"
            })
            
        except Exception as e:
            logger.error(f"Erreur ajout flux SDR: {e}")
            return jsonify({"error": str(e)}), 500

    def get_db_connection():
        """Connexion à la base de données"""
        import sqlite3
        import os
        
        instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        db_path = os.path.join(instance_dir, 'geopol.db')
        return sqlite3.connect(db_path)
    
    # ============================================
    # ROUTES DONNÉES BOURSIÈRES
    # ============================================
    
    @weak_indicators_integrated_bp.route('/stock/real-data', methods=['GET'])
    def get_real_stock_data():
        """Récupère les données boursières réelles via yfinance"""
        if not STOCK_SERVICE_AVAILABLE:
            return jsonify({
                'success': False,
                'error': 'Service Stock Data non disponible'
            }), 503
        
        try:
            stock_manager = RealStockData(db_manager)
            
            # Récupérer toutes les données
            indices = stock_manager.get_geopolitical_indices()
            commodities = stock_manager.get_commodity_prices()
            cryptos = stock_manager.get_crypto_prices()
            
            # Sauvegarder en cache
            _save_stock_data_to_cache(db_manager, indices, 'index')
            _save_stock_data_to_cache(db_manager, commodities, 'commodity')
            _save_stock_data_to_cache(db_manager, cryptos, 'crypto')
            
            # Compter données valides
            valid_indices = len([v for v in indices.values() if not v.get('error') and v.get('current_price', 0) > 0])
            valid_commodities = len([v for v in commodities.values() if not v.get('error') and v.get('current_price', 0) > 0])
            valid_cryptos = len([v for v in cryptos.values() if not v.get('error') and v.get('current_price', 0) > 0])
            
            return jsonify({
                'success': True,
                'indices': indices,
                'commodities': commodities,
                'cryptos': cryptos,
                'stats': {
                    'valid_indices': valid_indices,
                    'valid_commodities': valid_commodities,
                    'valid_cryptos': valid_cryptos,
                    'total_assets': valid_indices + valid_commodities + valid_cryptos
                },
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur stock data: {e}")
            return jsonify({
                'success': False,
                'error': str(e),
                'note': 'Vérifiez que yfinance est installé : pip install yfinance'
            }), 500
    
    @weak_indicators_integrated_bp.route('/stock/cached', methods=['GET'])
    def get_cached_stock_data():
        """Récupère les données boursières depuis le cache"""
        try:
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT symbol, name, asset_type, current_price, change_percent, 
                       change_direction, country, last_updated
                FROM stock_data_cache
                WHERE last_updated > datetime('now', '-1 hour')
                ORDER BY asset_type, ABS(change_percent) DESC
            """)
            
            cached_data = []
            for row in cur.fetchall():
                cached_data.append({
                    'symbol': row[0],
                    'name': row[1],
                    'asset_type': row[2],
                    'current_price': row[3],
                    'change_percent': row[4],
                    'change_direction': row[5],
                    'country': row[6],
                    'last_updated': row[7]
                })
            
            conn.close()
            
            return jsonify({
                'success': True,
                'data': cached_data,
                'count': len(cached_data),
                'source': 'cache'
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur cache stock: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # ============================================
    # ROUTES GLOBALES
    # ============================================
    
    @weak_indicators_integrated_bp.route('/update-all', methods=['POST'])
    def update_all_data():
        """Met à jour toutes les données"""
        results = {
            'travel_advisories': {'success': False, 'error': None},
            'kiwisdr_servers': {'success': False, 'error': None},
            'stock_data': {'success': False, 'error': None}
        }
        
        # Travel Advisories
        if TRAVEL_SERVICE_AVAILABLE:
            try:
                travel_result = TravelAdvisoriesService.scan_advisories(db_manager)
                results['travel_advisories'] = {
                    'success': True,
                    'details': travel_result
                }
            except Exception as e:
                results['travel_advisories']['error'] = str(e)
        
        # KiwiSDR
        if KIWISDR_SERVICE_AVAILABLE:
            try:
                servers_data = KiwiSDRRealService.get_active_servers()
                if servers_data['servers']:
                    KiwiSDRRealService.save_servers_to_db(db_manager, servers_data['servers'])
                results['kiwisdr_servers'] = {
                    'success': True,
                    'count': servers_data['total']
                }
            except Exception as e:
                results['kiwisdr_servers']['error'] = str(e)
        
        # Stock Data
        if STOCK_SERVICE_AVAILABLE:
            try:
                stock_manager = RealStockData(db_manager)
                indices = stock_manager.get_geopolitical_indices()
                commodities = stock_manager.get_commodity_prices()
                
                _save_stock_data_to_cache(db_manager, indices, 'index')
                _save_stock_data_to_cache(db_manager, commodities, 'commodity')
                
                results['stock_data'] = {
                    'success': True,
                    'indices': len(indices),
                    'commodities': len(commodities)
                }
            except Exception as e:
                results['stock_data']['error'] = str(e)
        
        return jsonify({
            'success': True,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @weak_indicators_integrated_bp.route('/status', methods=['GET'])
    def get_services_status():
        """Statut des services"""
        return jsonify({
            'success': True,
            'services': {
                'travel_advisories': TRAVEL_SERVICE_AVAILABLE,
                'kiwisdr': KIWISDR_SERVICE_AVAILABLE,
                'stock_data': STOCK_SERVICE_AVAILABLE
            },
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # ============================================
    # ENREGISTREMENT
    # ============================================
    
    app.register_blueprint(weak_indicators_integrated_bp)
    logger.info("✅ Routes intégrées indicateurs faibles enregistrées")


# ============================================
# FONCTIONS HELPER
# ============================================

def _save_stock_data_to_cache(db_manager, data_dict, asset_type):
    """Sauvegarde les données boursières en cache"""
    try:
        conn = db_manager.get_connection()
        cur = conn.cursor()
        
        for symbol, data in data_dict.items():
            if data.get('error'):
                continue
            
            cur.execute("""
                INSERT OR REPLACE INTO stock_data_cache 
                (symbol, name, asset_type, current_price, change_percent, 
                 change_direction, country, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                data.get('name', symbol),
                asset_type,
                data.get('current_price', 0),
                data.get('change_percent', 0),
                data.get('change_direction', 'stable'),
                data.get('country', 'Global'),
                datetime.utcnow().isoformat()
            ))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Erreur cache stock: {e}")
