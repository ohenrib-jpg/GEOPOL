# Flask/export_routes.py
from flask import Blueprint, jsonify
from .data_exporter import DataExporter

export_bp = Blueprint('export', __name__)

@export_bp.route('/api/export/daily', methods=['POST'])
def export_daily():
    """Export manuel des données quotidiennes"""
    exporter = DataExporter()
    result = exporter.export_daily_analytics()
    
    if result:
        return jsonify({"success": True, "file": result})
    else:
        return jsonify({"error": "Erreur lors de l'export"}), 500

@export_bp.route('/api/export/weekly', methods=['POST'])
def export_weekly():
    """Export manuel du résumé hebdomadaire"""
    exporter = DataExporter()
    result = exporter.create_weekly_summary()
    
    if result:
        return jsonify({"success": True, "file": result})
    else:
        return jsonify({"error": "Erreur lors de l'export"}), 500

@export_bp.route('/api/export/backup', methods=['POST'])
def create_backup():
    """Création manuelle d'une sauvegarde"""
    exporter = DataExporter()
    result = exporter.create_backup()
    
    if result:
        return jsonify({"success": True, "file": result})
    else:
        return jsonify({"error": "Erreur lors de la sauvegarde"}), 500