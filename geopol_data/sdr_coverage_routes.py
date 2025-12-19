# Flask/geopol_data/sdr_coverage_routes.py
"""
Routes API pour le calcul de couverture réseau SDR.

Fonctionnalités :
- Heatmap de densité de stations
- Zones sous-couvertes
- Statistiques de couverture
- Évolution temporelle
- GeoJSON pour Leaflet Heatmap Layer
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def create_sdr_coverage_blueprint(db_manager, coverage_calculator=None):
    """
    Crée le blueprint API pour la couverture SDR.

    Args:
        db_manager: Gestionnaire de base de données
        coverage_calculator: Instance de CoverageCalculator (optionnel)

    Returns:
        Blueprint Flask
    """

    bp = Blueprint('sdr_coverage', __name__, url_prefix='/api/sdr/coverage')

    def _get_stations_from_db(active_only: bool = True) -> List[Dict]:
        """
        Récupère les stations SDR depuis la base de données.

        Args:
            active_only: Filtrer uniquement les stations actives

        Returns:
            Liste de stations
        """
        try:
            # Importer SDRStation
            from .sdr_monitoring.coverage_calculator import SDRStation

            # Récupérer depuis la BDD ou scraper
            from .connectors.sdr_scrapers import SDRScrapers
            scraper = SDRScrapers()
            stations_dict = scraper.get_stations_as_dict(force_refresh=False)

            # Convertir en objets SDRStation
            stations = []
            for station_data in stations_dict:
                try:
                    station = SDRStation(
                        station_id=station_data.get('id', ''),
                        name=station_data.get('name', 'Unknown'),
                        latitude=station_data.get('latitude', 0.0),
                        longitude=station_data.get('longitude', 0.0),
                        status=station_data.get('status', 'ACTIVE'),
                        last_seen=datetime.fromisoformat(station_data.get('last_seen', datetime.utcnow().isoformat())),
                        signal_strength=station_data.get('signal_strength'),
                        metadata=station_data.get('metadata', {})
                    )

                    # Filtrer si nécessaire
                    if not active_only or station.status == 'ACTIVE':
                        stations.append(station)

                except Exception as e:
                    logger.warning(f"Erreur parsing station {station_data.get('id', '?')}: {e}")
                    continue

            return stations

        except Exception as e:
            logger.error(f"❌ Erreur récupération stations: {e}")
            return []

    @bp.route('/calculate', methods=['GET'])
    def calculate_coverage():
        """
        Calcule la couverture complète du réseau SDR.

        Query params:
            - active_only: bool (default: true)

        Returns:
            Couverture complète (heatmap, zones sous-couvertes, statistiques)
        """
        try:
            if not coverage_calculator:
                return jsonify({
                    'success': False,
                    'error': 'CoverageCalculator non initialisé',
                    'timestamp': datetime.utcnow().isoformat()
                }), 503

            # Paramètres
            active_only = request.args.get('active_only', 'true').lower() == 'true'

            # Récupérer les stations
            stations = _get_stations_from_db(active_only)

            if not stations:
                return jsonify({
                    'success': False,
                    'error': 'Aucune station SDR disponible',
                    'timestamp': datetime.utcnow().isoformat()
                }), 404

            # Calculer la couverture
            coverage = coverage_calculator.calculate_coverage(stations, active_only)

            return jsonify({
                'success': True,
                'coverage': coverage,
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur calcul couverture: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/heatmap', methods=['GET'])
    def get_heatmap():
        """
        Génère la heatmap de densité de stations.

        Query params:
            - active_only: bool (default: true)

        Returns:
            Points de la heatmap {lat, lon, intensity}
        """
        try:
            if not coverage_calculator:
                return jsonify({
                    'success': False,
                    'error': 'CoverageCalculator non initialisé'
                }), 503

            active_only = request.args.get('active_only', 'true').lower() == 'true'
            stations = _get_stations_from_db(active_only)

            if not stations:
                return jsonify({
                    'success': True,
                    'heatmap': [],
                    'num_stations': 0,
                    'timestamp': datetime.utcnow().isoformat()
                })

            # Générer la heatmap
            heatmap = coverage_calculator.generate_heatmap(stations)

            return jsonify({
                'success': True,
                'heatmap': heatmap,
                'num_stations': len(stations),
                'num_points': len(heatmap),
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur génération heatmap: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/undercovered', methods=['GET'])
    def get_undercovered_zones():
        """
        Identifie les zones sous-couvertes.

        Query params:
            - active_only: bool (default: true)

        Returns:
            Liste des zones sous-couvertes
        """
        try:
            if not coverage_calculator:
                return jsonify({
                    'success': False,
                    'error': 'CoverageCalculator non initialisé'
                }), 503

            active_only = request.args.get('active_only', 'true').lower() == 'true'
            stations = _get_stations_from_db(active_only)

            if not stations:
                return jsonify({
                    'success': True,
                    'undercovered_zones': [],
                    'timestamp': datetime.utcnow().isoformat()
                })

            # Générer heatmap puis identifier zones
            heatmap = coverage_calculator.generate_heatmap(stations)
            undercovered = coverage_calculator.identify_undercovered_zones(heatmap)

            return jsonify({
                'success': True,
                'undercovered_zones': undercovered,
                'critical_zones': sum(1 for z in undercovered if z['level'] == 'CRITICAL'),
                'low_coverage_zones': sum(1 for z in undercovered if z['level'] == 'LOW'),
                'total_zones': len(undercovered),
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur zones sous-couvertes: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/statistics', methods=['GET'])
    def get_statistics():
        """
        Calcule les statistiques de couverture.

        Query params:
            - active_only: bool (default: true)

        Returns:
            Statistiques de couverture
        """
        try:
            if not coverage_calculator:
                return jsonify({
                    'success': False,
                    'error': 'CoverageCalculator non initialisé'
                }), 503

            active_only = request.args.get('active_only', 'true').lower() == 'true'
            stations = _get_stations_from_db(active_only)

            if not stations:
                return jsonify({
                    'success': True,
                    'statistics': {
                        'total_stations': 0,
                        'avg_density': 0.0,
                        'max_density': 0.0,
                        'min_density': 0.0,
                        'coverage_percentage': 0.0
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })

            # Calculer statistiques
            heatmap = coverage_calculator.generate_heatmap(stations)
            stats = coverage_calculator.calculate_statistics(stations, heatmap)

            return jsonify({
                'success': True,
                'statistics': stats,
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur statistiques: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/geojson/heatmap', methods=['GET'])
    def get_heatmap_geojson():
        """
        Génère un GeoJSON pour Leaflet Heatmap Layer.

        Query params:
            - active_only: bool (default: true)
            - max_intensity: float (optional)

        Returns:
            GeoJSON FeatureCollection pour Leaflet Heatmap
        """
        try:
            if not coverage_calculator:
                return jsonify({
                    'type': 'FeatureCollection',
                    'features': [],
                    'metadata': {
                        'error': 'CoverageCalculator non initialisé'
                    }
                }), 503

            active_only = request.args.get('active_only', 'true').lower() == 'true'
            max_intensity = request.args.get('max_intensity', type=float)

            stations = _get_stations_from_db(active_only)

            if not stations:
                return jsonify({
                    'type': 'FeatureCollection',
                    'features': [],
                    'metadata': {
                        'num_points': 0,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })

            # Générer heatmap et GeoJSON
            heatmap = coverage_calculator.generate_heatmap(stations)
            geojson = coverage_calculator.generate_geojson_heatmap(heatmap, max_intensity)

            return jsonify(geojson)

        except Exception as e:
            logger.error(f"❌ Erreur GeoJSON heatmap: {e}")
            return jsonify({
                'type': 'FeatureCollection',
                'features': [],
                'metadata': {
                    'error': str(e)
                }
            }), 500

    @bp.route('/geojson/undercovered', methods=['GET'])
    def get_undercovered_geojson():
        """
        Génère un GeoJSON pour les zones sous-couvertes.

        Query params:
            - active_only: bool (default: true)

        Returns:
            GeoJSON avec cercles pour zones sous-couvertes
        """
        try:
            if not coverage_calculator:
                return jsonify({
                    'type': 'FeatureCollection',
                    'features': [],
                    'metadata': {
                        'error': 'CoverageCalculator non initialisé'
                    }
                }), 503

            active_only = request.args.get('active_only', 'true').lower() == 'true'
            stations = _get_stations_from_db(active_only)

            if not stations:
                return jsonify({
                    'type': 'FeatureCollection',
                    'features': [],
                    'metadata': {
                        'total_zones': 0,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                })

            # Générer zones sous-couvertes et GeoJSON
            heatmap = coverage_calculator.generate_heatmap(stations)
            undercovered = coverage_calculator.identify_undercovered_zones(heatmap)
            geojson = coverage_calculator.generate_undercovered_geojson(undercovered)

            return jsonify(geojson)

        except Exception as e:
            logger.error(f"❌ Erreur GeoJSON zones sous-couvertes: {e}")
            return jsonify({
                'type': 'FeatureCollection',
                'features': [],
                'metadata': {
                    'error': str(e)
                }
            }), 500

    @bp.route('/evolution', methods=['GET'])
    def get_coverage_evolution():
        """
        Calcule l'évolution de la couverture dans le temps.

        Query params:
            - hours: int (default: 24)
            - interval_hours: int (default: 6)

        Returns:
            Timeline de couverture
        """
        try:
            if not coverage_calculator:
                return jsonify({
                    'success': False,
                    'error': 'CoverageCalculator non initialisé'
                }), 503

            hours = request.args.get('hours', 24, type=int)
            interval_hours = request.args.get('interval_hours', 6, type=int)

            # Récupérer les données historiques depuis la BDD
            # TODO: Implémenter récupération historique réelle
            # Pour l'instant, retourner structure vide

            return jsonify({
                'success': True,
                'evolution': [],
                'period_hours': hours,
                'interval_hours': interval_hours,
                'message': 'Données historiques en cours d\'implémentation',
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur évolution couverture: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/by-region', methods=['POST'])
    def get_coverage_by_region():
        """
        Calcule la couverture par région géopolitique.

        Body:
            regions: Dict[str, Dict] - Définition des régions

        Returns:
            Couverture par région
        """
        try:
            if not coverage_calculator:
                return jsonify({
                    'success': False,
                    'error': 'CoverageCalculator non initialisé'
                }), 503

            data = request.get_json()
            if not data or 'regions' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Définition des régions manquante'
                }), 400

            regions = data['regions']
            active_only = data.get('active_only', True)

            stations = _get_stations_from_db(active_only)

            if not stations:
                return jsonify({
                    'success': True,
                    'coverage_by_region': {},
                    'message': 'Aucune station disponible',
                    'timestamp': datetime.utcnow().isoformat()
                })

            # Calculer couverture par région
            coverage_by_region = coverage_calculator.get_coverage_by_region(stations, regions)

            return jsonify({
                'success': True,
                'coverage_by_region': coverage_by_region,
                'num_regions': len(regions),
                'num_stations': len(stations),
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur couverture par région: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/config', methods=['GET'])
    def get_coverage_config():
        """
        Récupère la configuration actuelle du calculateur.

        Returns:
            Configuration de couverture
        """
        try:
            if not coverage_calculator:
                return jsonify({
                    'success': False,
                    'error': 'CoverageCalculator non initialisé'
                }), 503

            config = coverage_calculator.config

            return jsonify({
                'success': True,
                'config': {
                    'coverage_radius_km': config.coverage_radius_km,
                    'grid_resolution': config.grid_resolution,
                    'min_density_threshold': config.min_density_threshold,
                    'critical_density_threshold': config.critical_density_threshold,
                    'bounds': config.bounds
                },
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur config couverture: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/config', methods=['PUT'])
    def update_coverage_config():
        """
        Met à jour la configuration du calculateur.

        Body:
            coverage_radius_km: float (optional)
            grid_resolution: float (optional)
            min_density_threshold: float (optional)
            critical_density_threshold: float (optional)

        Returns:
            Configuration mise à jour
        """
        try:
            if not coverage_calculator:
                return jsonify({
                    'success': False,
                    'error': 'CoverageCalculator non initialisé'
                }), 503

            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Données de configuration manquantes'
                }), 400

            config = coverage_calculator.config

            # Mettre à jour les paramètres fournis
            if 'coverage_radius_km' in data:
                config.coverage_radius_km = float(data['coverage_radius_km'])
            if 'grid_resolution' in data:
                config.grid_resolution = float(data['grid_resolution'])
            if 'min_density_threshold' in data:
                config.min_density_threshold = float(data['min_density_threshold'])
            if 'critical_density_threshold' in data:
                config.critical_density_threshold = float(data['critical_density_threshold'])

            logger.info(f"✅ Configuration couverture mise à jour")

            return jsonify({
                'success': True,
                'config': {
                    'coverage_radius_km': config.coverage_radius_km,
                    'grid_resolution': config.grid_resolution,
                    'min_density_threshold': config.min_density_threshold,
                    'critical_density_threshold': config.critical_density_threshold,
                    'bounds': config.bounds
                },
                'timestamp': datetime.utcnow().isoformat()
            })

        except Exception as e:
            logger.error(f"❌ Erreur MAJ config: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return bp
