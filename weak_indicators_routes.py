# Flask/weak_indicators_routes.py - VERSION OPTIMISÉE POUR APP_FACTORY
"""
Routes des indicateurs faibles - Version optimisée pour app_factory
"""

from flask import Blueprint, jsonify, request, render_template
import logging
import numpy as np
from datetime import datetime, timedelta
import json
import subprocess
import sqlite3
import os

logger = logging.getLogger(__name__)

weak_indicators_bp = Blueprint('weak_indicators', __name__)

# Variable globale pour stocker db_manager
_db_manager = None

def register_weak_indicators_routes(app, db_manager):
    """Enregistre les routes des indicateurs faibles - Version app_factory"""
    global _db_manager
    _db_manager = db_manager
    
    # Initialiser les tables SDR si nécessaire
    init_sdr_streams_table(db_manager)
    
    # === ROUTES DE BASE ===
    
    @weak_indicators_bp.route('/')
    def weak_indicators_dashboard():
        """Page principale des indicateurs faibles"""
        return render_template('weak_indicators.html')
    
    @weak_indicators_bp.route('/api/status')
    def get_weak_indicators_status():
        """Statut du système"""
        return jsonify({
            "success": True,
            "system": "weak_indicators", 
            "status": "active",
            "last_analysis": datetime.utcnow().isoformat()
        })

    @weak_indicators_bp.route('/api/sdr-streams')
    def get_sdr_streams():
        """Retourne tous les flux SDR"""
        try:
            if not _db_manager:
                return jsonify([
                    {
                        "id": 1,
                        "name": "Radio France International",
                        "url": "https://example.com/rfi",
                        "frequency_khz": 15300,
                        "type": "websdr",
                        "description": "Surveillance RFI",
                        "active": True,
                        "created_at": datetime.utcnow().isoformat()
                    }
                ])
            
            conn = _db_manager.get_connection()
            cur = conn.cursor()
            
            # Vérifier si la table existe
            cur.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='sdr_streams'
            """)
            
            if not cur.fetchone():
                init_sdr_streams_table(_db_manager)
            
            cur.execute("""
                SELECT id, name, url, frequency_khz, type, description, active, created_at
                FROM sdr_streams 
                ORDER BY frequency_khz
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
            return jsonify([
                {
                    "id": 1,
                    "name": "Flux Test",
                    "url": "https://example.com/test",
                    "frequency_khz": 10000,
                    "type": "websdr",
                    "description": f"Mode secours - {str(e)}",
                    "active": True,
                    "created_at": datetime.utcnow().isoformat()
                }
            ])

    @weak_indicators_bp.route('/api/sdr-streams/<int:stream_id>/toggle', methods=['POST'])
    def toggle_sdr_stream(stream_id):
        """Active/désactive un flux SDR"""
        try:
            data = request.get_json()
            active = data.get('active', False) if data else False
            
            if not _db_manager:
                return jsonify({"success": False, "error": "Database non disponible"}), 500
            
            conn = _db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("UPDATE sdr_streams SET active = ? WHERE id = ?", (active, stream_id))
            conn.commit()
            conn.close()
            
            return jsonify({"success": True, "active": active})
            
        except Exception as e:
            logger.error(f"Erreur toggle stream {stream_id}: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    # === ROUTES AVIS AUX VOYAGEURS ===
    
    @weak_indicators_bp.route('/api/travel-advisories/countries')
    def get_travel_advisory_countries():
        """Liste des pays avec avis de voyage"""
        countries = [
            {
                "id": 1, "name": "France", "risk_level": 1, "advice": "Normal",
                "last_updated": datetime.utcnow().isoformat(), "alert": "Aucune alerte"
            },
            {
                "id": 2, "name": "Ukraine", "risk_level": 4, "advice": "Déconseillé", 
                "last_updated": datetime.utcnow().isoformat(), "alert": "Zone de conflit"
            },
            {
                "id": 3, "name": "Chine", "risk_level": 2, "advice": "Précautions",
                "last_updated": datetime.utcnow().isoformat(), "alert": "Tensions régionales"
            }
        ]
        
        return jsonify({
            "success": True,
            "countries": countries,
            "total": len(countries)
        })

    @weak_indicators_bp.route('/api/travel-advisories/scan', methods=['POST'])
    def scan_travel_advisories():
        """Lance un scan des avis de voyage"""
        return jsonify({
            "success": True,
            "message": "Scan simulé terminé",
            "timestamp": datetime.utcnow().isoformat()
        })

    # === ROUTES DONNÉES RÉELLES ===
    
    @weak_indicators_bp.route('/api/real-data/update-all', methods=['POST'])
    def update_all_real_data():
        """Met à jour toutes les données"""
        return jsonify({
            "success": True,
            "message": "Mise à jour simulée",
            "timestamp": datetime.utcnow().isoformat()
        })

    @weak_indicators_bp.route('/api/stock/real-data')
    def get_real_stock_data():
        """Données boursières simulées"""
        return jsonify({
            "success": True,
            "indices": {
                "CAC40": {"current_price": 7345.12, "change": 45.67, "change_percent": 0.63},
                "S&P500": {"current_price": 5123.45, "change": 23.45, "change_percent": 0.46}
            },
            "timestamp": datetime.utcnow().isoformat()
        })

    # Enregistrer le blueprint
    app.register_blueprint(weak_indicators_bp, url_prefix='/weak-indicators')
    
    logger.info("✅ Routes Weak Indicators intégrées à app_factory")

# === FONCTIONS UTILITAIRES ===

def init_sdr_streams_table(db_manager):
    """Initialise la table sdr_streams si elle n'existe pas"""
    try:
        conn = db_manager.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sdr_streams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT,
                frequency_khz INTEGER DEFAULT 0,
                type TEXT DEFAULT 'websdr',
                description TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Vérifier si des données existent
        cur.execute("SELECT COUNT(*) FROM sdr_streams")
        count = cur.fetchone()[0]
        
        if count == 0:
            sample_streams = [
                ('Radio France International', 'http://example.com/rfi', 15300, 'websdr', 'Surveillance RFI'),
                ('BBC World Service', 'http://example.com/bbc', 12065, 'websdr', 'Surveillance BBC'),
            ]
            
            cur.executemany("""
                INSERT INTO sdr_streams (name, url, frequency_khz, type, description)
                VALUES (?, ?, ?, ?, ?)
            """, sample_streams)
        
        conn.commit()
        conn.close()
        logger.info("✅ Table sdr_streams initialisée")
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation sdr_streams: {e}")