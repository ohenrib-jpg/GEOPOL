# Flask/sdr_unified_routes.py
"""
Routes unifiées SDR - Compatible RTL-SDR, WebSDR et KiwiSDR
Évite les conflits de routes
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Blueprint unifié avec préfixe unique
sdr_bp = Blueprint('sdr', __name__, url_prefix='/api/sdr')

def register_unified_sdr_routes(app, db_manager):
    """Enregistre toutes les routes SDR sans conflits"""
    
    # === ROUTES UNIFIÉES SDR ===
    
    @sdr_bp.route('/streams', methods=['GET', 'POST'])
    def manage_sdr_streams():
        """Gestion unifiée des flux SDR"""
        try:
            if request.method == 'GET':
                return get_all_sdr_streams(db_manager)
            else:
                return add_sdr_stream(db_manager)
        except Exception as e:
            logger.error(f"Erreur gestion flux SDR: {e}")
            return jsonify({"error": str(e)}), 500

    @sdr_bp.route('/streams/<int:stream_id>', methods=['DELETE'])
    def delete_sdr_stream(stream_id):
        """Supprime un flux SDR"""
        try:
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("DELETE FROM sdr_streams WHERE id = ?", (stream_id,))
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "message": "Flux supprimé"})
        except Exception as e:
            logger.error(f"Erreur suppression flux: {e}")
            return jsonify({"error": str(e)}), 500

    @sdr_bp.route('/streams/<int:stream_id>/activity')
    def get_stream_activity(stream_id):
        """Activité d'un flux SDR"""
        try:
            conn = db_manager.get_connection()
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

    # === ROUTES RTL-SDR SPÉCIFIQUES ===
    
    @sdr_bp.route('/rtlsdr/waterfall/<int:frequency_khz>')
    def get_rtlsdr_waterfall(frequency_khz):
        """Waterfall RTL-SDR - Route spécifique sans conflit"""
        try:
            from .rtlsdr_manager import RTLSDRAnalyzer
            analyzer = RTLSDRAnalyzer(db_manager)
            
            waterfall_data = analyzer.capture_waterfall_data(
                frequency_khz=frequency_khz,
                duration_seconds=30
            )
            
            return jsonify({
                "success": True,
                "type": "rtlsdr",
                "frequency_khz": frequency_khz,
                "waterfall_data": waterfall_data,
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Erreur waterfall RTL-SDR: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @sdr_bp.route('/rtlsdr/spectrum/<int:frequency_khz>')
    def get_rtlsdr_spectrum(frequency_khz):
        """Spectre RTL-SDR"""
        try:
            from .rtlsdr_manager import RTLSDRAnalyzer
            analyzer = RTLSDRAnalyzer(db_manager)
            
            spectrum_data = analyzer.get_spectrum_data(
                center_freq_khz=frequency_khz,
                span_khz=1000
            )
            
            return jsonify({
                "success": True,
                "type": "rtlsdr",
                "frequency_khz": frequency_khz,
                "spectrum": spectrum_data
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # === ROUTES COMPATIBILITÉ WEBSDR ===
    
    @sdr_bp.route('/websdr/servers')
    def get_websdr_servers_compat():
        """Compatibilité WebSDR - Route renommée"""
        servers = [
            {
                'id': 0,
                'name': 'University of Twente (NL)',
                'url': 'http://websdr.ewi.utwente.nl:8901/',
                'type': 'websdr',
                'status': 'online'
            }
        ]
        return jsonify({"servers": servers})

    # === ROUTES MÉTADONNÉES SDR ===
    
    @sdr_bp.route('/sources')
    def get_available_sources():
        """Liste toutes les sources SDR disponibles"""
        sources = {
            "rtlsdr": {
                "available": True,
                "description": "RTL-SDR Local - Haute résolution",
                "type": "local"
            },
            "websdr": {
                "available": True, 
                "description": "WebSDR Public - Accès distant",
                "type": "remote"
            },
            "kiwisdr": {
                "available": True,
                "description": "KiwiSDR - Réseau mondial",
                "type": "remote"
            }
        }
        return jsonify({"sources": sources})

    @sdr_bp.route('/status')
    def get_sdr_system_status():
        """Statut global du système SDR"""
        return jsonify({
            "rtlsdr": {
                "status": "active",
                "devices_available": 1,
                "sample_rate": "2.4 MHz"
            },
            "websdr": {
                "status": "available", 
                "servers_online": 3
            },
            "system": {
                "total_streams": get_total_streams(db_manager),
                "last_update": datetime.utcnow().isoformat()
            }
        })

    # Enregistrer le blueprint unifié
    app.register_blueprint(sdr_bp)
    logger.info("✅ Routes SDR unifiées enregistrées")

def get_all_sdr_streams(db_manager):
    """Récupère tous les flux SDR"""
    conn = db_manager.get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, name, url, frequency_khz, type, created_at
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
            "created_at": row[5]
        })
    
    conn.close()
    return jsonify(streams)

def add_sdr_stream(db_manager):
    """Ajoute un flux SDR"""
    data = request.get_json()
    
    conn = db_manager.get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO sdr_streams (name, url, frequency_khz, type)
        VALUES (?, ?, ?, ?)
    """, (
        data.get('name'),
        data.get('url'),
        data.get('frequency_khz'),
        data.get('type', 'rtlsdr')
    ))
    
    conn.commit()
    stream_id = cur.lastrowid
    conn.close()
    
    return jsonify({
        "success": True,
        "id": stream_id,
        "message": "Flux SDR ajouté"
    })

def get_total_streams(db_manager):
    """Compte le total des flux SDR"""
    conn = db_manager.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sdr_streams")
    count = cur.fetchone()[0]
    conn.close()
    return count