# Flask/routes_geo_narrative.py - Routes API pour l'analyse géo-narrative

from flask import Blueprint, jsonify, request, render_template
import logging

logger = logging.getLogger(__name__)

def create_geo_narrative_blueprint(db_manager, geo_narrative_analyzer):
    """
    Crée le Blueprint pour les routes d'analyse géo-narrative
    
    Args:
        db_manager: Instance du gestionnaire de base de données
        geo_narrative_analyzer: Instance de GeoNarrativeAnalyzer
    
    Returns:
        Blueprint Flask configuré
    """
    
    bp = Blueprint('geo_narrative', __name__, url_prefix='/api/geo-narrative')
    
    # =========================================================================
    # ROUTES API
    # =========================================================================
    
    @bp.route('/patterns', methods=['GET'])
    def get_patterns():
        """
        Récupère les patterns transnationaux détectés
        
        Query params:
            - days: Nombre de jours à analyser (défaut: 7)
            - min_countries: Nombre minimum de pays (défaut: 2)
        
        Returns:
            JSON avec la liste des patterns
        """
        try:
            # Récupérer les paramètres
            days = request.args.get('days', 7, type=int)
            min_countries = request.args.get('min_countries', 2, type=int)
            
            # Valider les paramètres
            if days < 1 or days > 90:
                return jsonify({
                    'error': 'Le paramètre days doit être entre 1 et 90'
                }), 400
            
            if min_countries < 2 or min_countries > 10:
                return jsonify({
                    'error': 'Le paramètre min_countries doit être entre 2 et 10'
                }), 400
            
            logger.info(f"🔍 Requête patterns: days={days}, min_countries={min_countries}")
            
            # Détecter les patterns
            if not geo_narrative_analyzer:
                return jsonify({
                    'error': 'GeoNarrativeAnalyzer non disponible'
                }), 503
            
            patterns = geo_narrative_analyzer.detect_transnational_patterns(
                days=days,
                min_countries=min_countries
            )
            
            return jsonify(patterns), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération patterns: {e}")
            import traceback
            traceback.print_exc()
            
            return jsonify({
                'error': 'Erreur serveur',
                'details': str(e)
            }), 500
    
    @bp.route('/patterns/<pattern_id>', methods=['GET'])
    def get_pattern_details(pattern_id):
        """
        Récupère les détails d'un pattern spécifique
        
        Args:
            pattern_id: ID ou texte du pattern
        
        Returns:
            JSON avec les détails du pattern
        """
        try:
            days = request.args.get('days', 7, type=int)
            
            if not geo_narrative_analyzer:
                return jsonify({
                    'error': 'GeoNarrativeAnalyzer non disponible'
                }), 503
            
            # Décoder le pattern_id (peut contenir des espaces)
            from urllib.parse import unquote
            pattern_text = unquote(pattern_id)
            
            details = geo_narrative_analyzer.get_pattern_details(
                pattern=pattern_text,
                days=days
            )
            
            return jsonify(details), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur détails pattern: {e}")
            return jsonify({
                'error': 'Erreur serveur',
                'details': str(e)
            }), 500
    
    @bp.route('/countries', methods=['GET'])
    def get_countries_analysis():
        """
        Analyse des pays avec statistiques
        
        Returns:
            JSON avec statistiques par pays
        """
        try:
            days = request.args.get('days', 7, type=int)
            
            if not geo_narrative_analyzer:
                return jsonify({
                    'error': 'GeoNarrativeAnalyzer non disponible'
                }), 503
            
            # Récupérer les articles par pays
            articles_by_country = geo_narrative_analyzer._get_recent_articles_by_country(days)
            
            # Calculer les statistiques
            stats = {}
            for country, articles in articles_by_country.items():
                stats[country] = {
                    'country_code': country,
                    'article_count': len(articles),
                    'latest_article': articles[0]['pub_date'] if articles else None
                }
            
            return jsonify(stats), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse pays: {e}")
            return jsonify({
                'error': 'Erreur serveur',
                'details': str(e)
            }), 500
    
    @bp.route('/export', methods=['POST'])
    def export_patterns():
        """
        Exporte les patterns en JSON
        
        Body:
            - days: Nombre de jours
            - min_countries: Nombre minimum de pays
            - format: Format d'export ('json', 'csv')
        
        Returns:
            Fichier exporté
        """
        try:
            data = request.get_json()
            
            days = data.get('days', 7)
            min_countries = data.get('min_countries', 2)
            export_format = data.get('format', 'json')
            
            if not geo_narrative_analyzer:
                return jsonify({
                    'error': 'GeoNarrativeAnalyzer non disponible'
                }), 503
            
            # Détecter les patterns
            patterns = geo_narrative_analyzer.detect_transnational_patterns(
                days=days,
                min_countries=min_countries
            )
            
            if export_format == 'json':
                import json
                from datetime import datetime
                
                filename = f"patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                json_data = json.dumps(patterns, ensure_ascii=False, indent=2)
                
                from flask import Response
                return Response(
                    json_data,
                    mimetype='application/json',
                    headers={'Content-Disposition': f'attachment; filename={filename}'}
                )
            
            elif export_format == 'csv':
                import csv
                import io
                from datetime import datetime
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # En-têtes
                writer.writerow(['Pattern', 'Pays', 'Nombre Pays', 'Occurrences', 'Date Détection'])
                
                # Données
                for pattern in patterns:
                    writer.writerow([
                        pattern['pattern'],
                        ', '.join(pattern['countries']),
                        pattern.get('country_count', len(pattern['countries'])),
                        pattern.get('total_occurrences', 0),
                        pattern.get('first_detected', '')
                    ])
                
                filename = f"patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                from flask import Response
                return Response(
                    output.getvalue(),
                    mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename={filename}'}
                )
            
            else:
                return jsonify({
                    'error': 'Format non supporté. Utilisez json ou csv'
                }), 400
            
        except Exception as e:
            logger.error(f"❌ Erreur export: {e}")
            return jsonify({
                'error': 'Erreur serveur',
                'details': str(e)
            }), 500
    
    @bp.route('/stats', methods=['GET'])
    def get_statistics():
        """
        Statistiques globales sur les patterns
        
        Returns:
            JSON avec statistiques globales
        """
        try:
            days = request.args.get('days', 7, type=int)
            
            if not geo_narrative_analyzer:
                return jsonify({
                    'error': 'GeoNarrativeAnalyzer non disponible'
                }), 503
            
            # Récupérer les patterns
            patterns = geo_narrative_analyzer.detect_transnational_patterns(
                days=days,
                min_countries=2
            )
            
            # Calculer les statistiques
            if not patterns:
                return jsonify({
                    'total_patterns': 0,
                    'countries_involved': 0,
                    'strongest_pattern': None,
                    'average_countries_per_pattern': 0,
                    'total_occurrences': 0
                }), 200
            
            # Pays uniques
            all_countries = set()
            for pattern in patterns:
                all_countries.update(pattern['countries'])
            
            # Pattern le plus fort
            strongest = max(patterns, key=lambda x: x.get('country_count', len(x['countries'])))
            
            # Moyenne de pays par pattern
            avg_countries = sum(p.get('country_count', len(p['countries'])) for p in patterns) / len(patterns)
            
            # Total occurrences
            total_occ = sum(p.get('total_occurrences', 0) for p in patterns)
            
            stats = {
                'total_patterns': len(patterns),
                'countries_involved': len(all_countries),
                'strongest_pattern': {
                    'pattern': strongest['pattern'],
                    'country_count': strongest.get('country_count', len(strongest['countries'])),
                    'countries': strongest['countries']
                },
                'average_countries_per_pattern': round(avg_countries, 2),
                'total_occurrences': total_occ,
                'analysis_period_days': days
            }
            
            return jsonify(stats), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur statistiques: {e}")
            return jsonify({
                'error': 'Erreur serveur',
                'details': str(e)
            }), 500
    
    # =========================================================================
    # ROUTE VUE WEB
    # =========================================================================
    
    @bp.route('/dashboard', methods=['GET'])
    def dashboard():
        """
        Page web du tableau de bord géo-narratif
        
        Returns:
            Template HTML
        """
        try:
            return render_template('geo_narrative_dashboard.html')
        except Exception as e:
            logger.error(f"❌ Erreur affichage dashboard: {e}")
            return f"Erreur: {str(e)}", 500

    # =======================================================================================   
    # route pour le carte des influences
    # =======================================================================================
    @bp.route('/influence-map', methods=['GET'])
    def get_influence_map():
        """Génère une carte d'influence narrative entre pays"""
        try:
            days = request.args.get('days', 7, type=int)
            
            if not geo_narrative_analyzer:
                return jsonify({
                    'success': False,
                    'error': 'GeoNarrativeAnalyzer non disponible'
                }), 503
            
            # Récupérer les patterns
            patterns = geo_narrative_analyzer.detect_transnational_patterns(
                days=days,
                min_countries=2
            )
            
            # Construire le réseau d'influence
            influence_network = {
                'nodes': [],
                'edges': [],
                'metadata': {
                    'total_patterns': len(patterns),
                    'countries_analyzed': len(set(p for pattern in patterns for p in pattern['countries'])),
                    'analysis_period': f'{days} jours'
                }
            }
            
            # Ajouter les pays comme nœuds
            countries = set()
            for pattern in patterns:
                countries.update(pattern['countries'])
            
            # Coordonnées des pays (simplifiées)
            country_coords = {
                'FR': [46.2276, 2.2137], 'DE': [51.1657, 10.4515], 
                'UK': [55.3781, -3.4360], 'US': [37.0902, -95.7129],
                'ES': [40.4637, -3.7492], 'IT': [41.8719, 12.5674],
                'CN': [35.8617, 104.1954], 'JP': [36.2048, 138.2529],
                'RU': [61.5240, 105.3188]
            }
            
            for country in countries:
                influence_network['nodes'].append({
                    'id': country,
                    'label': country,
                    'type': 'country',
                    'x': country_coords.get(country, [0, 0])[1],  # longitude
                    'y': country_coords.get(country, [0, 0])[0],  # latitude
                    'size': sum(1 for p in patterns if country in p['countries'])
                })
            
            # Ajouter les arêtes (connexions entre pays)
            for pattern in patterns:
                countries_list = pattern['countries']
                for i in range(len(countries_list)):
                    for j in range(i + 1, len(countries_list)):
                        influence_network['edges'].append({
                            'source': countries_list[i],
                            'target': countries_list[j],
                            'weight': pattern.get('strength', 1),
                            'label': pattern['pattern'][:30] + '...'
                        })
            
            return jsonify({
                'success': True,
                'influence_network': influence_network
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur génération carte d'influence: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # =========================================================================
    # ROUTE DE SANTÉ
    # =========================================================================
    
    @bp.route('/health', methods=['GET'])
    def health_check():
        """
        Vérification de santé du service
        
        Returns:
            JSON avec le statut du service
        """
        return jsonify({
            'status': 'ok',
            'service': 'geo_narrative_analyzer',
            'available': geo_narrative_analyzer is not None
        }), 200
    
    logger.info("✅ Blueprint geo_narrative créé avec succès")
    
    return bp


# =========================================================================
# FONCTION D'ENREGISTREMENT POUR app_factory.py
# =========================================================================

def register_geo_narrative_routes(app, db_manager, geo_narrative_analyzer):
    """
    Fonction helper pour enregistrer le blueprint dans l'app Flask
    
    Args:
        app: Instance Flask
        db_manager: Gestionnaire de base de données
        geo_narrative_analyzer: Instance de GeoNarrativeAnalyzer
    """
    try:
        with app.app_context():  # Ajout du contexte d'application
            bp = create_geo_narrative_blueprint(db_manager, geo_narrative_analyzer)
            app.register_blueprint(bp)
        
        logger.info("✅ Routes geo_narrative enregistrées")
        logger.info("📍 Routes disponibles:")
        logger.info("   GET  /api/geo-narrative/patterns")
        logger.info("   GET  /api/geo-narrative/patterns/<pattern_id>")
        logger.info("   GET  /api/geo-narrative/countries")
        logger.info("   POST /api/geo-narrative/export")
        logger.info("   GET  /api/geo-narrative/stats")
        logger.info("   GET  /api/geo-narrative/dashboard")
        logger.info("   GET  /api/geo-narrative/health")
        logger.info("   GET  /api/geo-narrative/influence-map")
        
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement routes geo_narrative: {e}")
        raise
