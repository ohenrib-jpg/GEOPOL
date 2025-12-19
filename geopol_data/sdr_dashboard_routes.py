# Flask/geopol_data/sdr_dashboard_routes.py
"""
Routes API pour le dashboard SDR temps réel.

Fonctionnalités :
- Résumé global (métriques globales)
- Timeline d'évolution 24h
- Métriques par zone
- Alertes récentes
- Données pour graphiques

Version: 1.0.0
"""

from flask import Blueprint, jsonify, request, render_template
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def create_sdr_dashboard_blueprint(db_manager, dashboard_manager=None, sdr_analyzer=None):
    """
    Crée le blueprint pour le dashboard SDR.

    Args:
        db_manager: Gestionnaire de base de données
        dashboard_manager: Instance de DashboardManager (optionnel)
        sdr_analyzer: Instance de SDRAnalyzer (optionnel)

    Returns:
        Blueprint Flask
    """

    bp = Blueprint('sdr_dashboard', __name__, url_prefix='/api/sdr/dashboard')

    # Si dashboard_manager n'est pas fourni, le créer
    if not dashboard_manager:
        from .sdr_monitoring.dashboard_manager import DashboardManager
        dashboard_manager = DashboardManager(db_manager, sdr_analyzer)

    @bp.route('/summary', methods=['GET'])
    def get_dashboard_summary():
        """
        Récupère le résumé complet du dashboard.

        Returns:
            Métriques globales, par zone, alertes récentes
        """
        try:
            # Récupérer le résumé
            summary = dashboard_manager.get_dashboard_summary()

            return jsonify({
                'success': True,
                'data': summary.to_dict(),
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur résumé dashboard: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/global', methods=['GET'])
    def get_global_metrics():
        """
        Récupère les métriques globales uniquement.

        Returns:
            {total_active, total_inactive, total_stations, availability_rate}
        """
        try:
            global_metrics = dashboard_manager._get_global_metrics()

            return jsonify({
                'success': True,
                'global': global_metrics,
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur métriques globales: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/zones', methods=['GET'])
    def get_zone_metrics():
        """
        Récupère les métriques par zone géopolitique.

        Returns:
            Métriques détaillées par zone
        """
        try:
            zone_metrics = dashboard_manager._get_zone_metrics()

            return jsonify({
                'success': True,
                'zones': zone_metrics,
                'num_zones': len(zone_metrics),
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur métriques zones: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/timeline', methods=['GET'])
    def get_timeline():
        """
        Récupère la timeline d'évolution.

        Query params:
            - hours: int (default: 24)
            - interval_minutes: int (default: 30)

        Returns:
            Timeline [{timestamp, active_stations, availability_rate}, ...]
        """
        try:
            hours = request.args.get('hours', 24, type=int)
            interval_minutes = request.args.get('interval_minutes', 30, type=int)

            timeline = dashboard_manager.get_timeline_data(hours, interval_minutes)

            return jsonify({
                'success': True,
                'timeline': timeline,
                'period_hours': hours,
                'interval_minutes': interval_minutes,
                'num_points': len(timeline),
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur timeline: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/alerts', methods=['GET'])
    def get_recent_alerts():
        """
        Récupère les alertes/anomalies récentes.

        Query params:
            - limit: int (default: 10)

        Returns:
            Liste des anomalies récentes
        """
        try:
            limit = request.args.get('limit', 10, type=int)

            anomalies = dashboard_manager._get_recent_anomalies(limit)

            return jsonify({
                'success': True,
                'alerts': anomalies,
                'count': len(anomalies),
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur alertes récentes: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/charts/zone-distribution', methods=['GET'])
    def get_zone_distribution():
        """
        Données pour graphique de distribution par zone (camembert).

        Returns:
            {labels: [...], values: [...]}
        """
        try:
            distribution = dashboard_manager.get_zone_distribution()

            return jsonify({
                'success': True,
                'data': distribution,
                'chart_type': 'pie',
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur distribution zones: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/charts/status-distribution', methods=['GET'])
    def get_status_distribution():
        """
        Données pour graphique de distribution des statuts (camembert).

        Returns:
            {labels: [...], values: [...], colors: [...]}
        """
        try:
            distribution = dashboard_manager.get_status_distribution()

            return jsonify({
                'success': True,
                'data': distribution,
                'chart_type': 'pie',
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur distribution statuts: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/charts/availability-trend', methods=['GET'])
    def get_availability_trend():
        """
        Données pour graphique de tendance de disponibilité (ligne).

        Query params:
            - hours: int (default: 24)

        Returns:
            [{timestamp, availability_rate}, ...]
        """
        try:
            hours = request.args.get('hours', 24, type=int)

            trend = dashboard_manager.get_availability_trend(hours)

            return jsonify({
                'success': True,
                'data': trend,
                'chart_type': 'line',
                'period_hours': hours,
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur tendance disponibilité: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/charts/anomaly-timeline', methods=['GET'])
    def get_anomaly_timeline():
        """
        Données pour graphique timeline des anomalies.

        Query params:
            - hours: int (default: 24)

        Returns:
            [{timestamp, total_count, critical_count}, ...]
        """
        try:
            hours = request.args.get('hours', 24, type=int)

            timeline = dashboard_manager.get_anomaly_timeline(hours)

            return jsonify({
                'success': True,
                'data': timeline,
                'chart_type': 'bar',
                'period_hours': hours,
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur timeline anomalies: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return bp


def create_sdr_dashboard_page_blueprint():
    """
    Crée le blueprint pour la page HTML du dashboard.

    Returns:
        Blueprint Flask
    """

    bp = Blueprint('sdr_dashboard_page', __name__, url_prefix='/sdr')

    @bp.route('/dashboard')
    def dashboard_page():
        """
        Page HTML du dashboard SDR.

        Returns:
            Template HTML
        """
        return render_template('sdr_dashboard.html')

    return bp
