# Flask/routes_geo_entity_integrated.py - Routes API pour l'intégration complète

from flask import Blueprint, jsonify, request, Response
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def create_integrated_blueprint(
    db_manager,
    geo_narrative_analyzer,
    entity_extractor,
    entity_db_manager,
    geo_entity_integration
):
    """
    Crée le Blueprint pour les routes intégrées geo-narrative + entities
    
    Args:
        db_manager: Gestionnaire de base de données
        geo_narrative_analyzer: Instance GeoNarrativeAnalyzer
        entity_extractor: Instance GeopoliticalEntityExtractor
        entity_db_manager: Instance EntityDatabaseManager
        geo_entity_integration: Instance GeoEntityIntegration
    
    Returns:
        Blueprint Flask configuré
    """
    
    bp = Blueprint('geo_entity_integrated', __name__, url_prefix='/api/geo-entity')
    
    # =========================================================================
    # ROUTES D'ANALYSE ENRICHIE
    # =========================================================================
    
    @bp.route('/patterns-enriched', methods=['GET'])
    def get_enriched_patterns():
        """
        Récupère les patterns transnationaux enrichis avec entités géopolitiques
        
        Query params:
            - days: Nombre de jours (défaut: 7)
            - min_countries: Nombre minimum de pays (défaut: 2)
        
        Returns:
            JSON avec patterns enrichis
        """
        try:
            days = request.args.get('days', 7, type=int)
            min_countries = request.args.get('min_countries', 2, type=int)
            
            logger.info(f"🔍 Requête patterns enrichis: days={days}, min_countries={min_countries}")
            
            patterns = geo_entity_integration.analyze_patterns_with_entities(
                days=days,
                min_countries=min_countries
            )
            
            return jsonify({
                'success': True,
                'count': len(patterns),
                'patterns': patterns
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur patterns enrichis: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/comprehensive-analysis', methods=['GET'])
    def get_comprehensive_analysis():
        """
        Analyse complète : patterns + réseau d'entités + statistiques
        
        Query params:
            - days: Nombre de jours (défaut: 7)
        
        Returns:
            JSON avec rapport complet
        """
        try:
            days = request.args.get('days', 7, type=int)
            
            logger.info(f"🔎 Analyse complète sur {days} jours")
            
            report = geo_entity_integration.analyze_articles_comprehensive(days=days)
            
            return jsonify({
                'success': True,
                'report': report
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse complète: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =========================================================================
    # RECHERCHE ET FILTRAGE
    # =========================================================================
    
    @bp.route('/patterns/by-entity', methods=['GET'])
    def find_patterns_by_entity():
        """
        Trouve tous les patterns mentionnant une entité spécifique
        
        Query params:
            - entity: Nom de l'entité (requis)
            - type: Type d'entité (optionnel: location, organization, person)
            - days: Nombre de jours (défaut: 7)
        
        Returns:
            JSON avec patterns correspondants
        """
        try:
            entity_name = request.args.get('entity')
            entity_type = request.args.get('type', None)
            days = request.args.get('days', 7, type=int)
            
            if not entity_name:
                return jsonify({
                    'success': False,
                    'error': 'Paramètre "entity" requis'
                }), 400
            
            logger.info(f"🔍 Recherche patterns pour entité: {entity_name}")
            
            patterns = geo_entity_integration.find_patterns_by_entity(
                entity_name=entity_name,
                entity_type=entity_type,
                days=days
            )
            
            return jsonify({
                'success': True,
                'entity': entity_name,
                'entity_type': entity_type,
                'count': len(patterns),
                'patterns': patterns
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche par entité: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/entity/timeline', methods=['GET'])
    def get_entity_timeline():
        """
        Chronologie d'apparition d'une entité
        
        Query params:
            - entity: Nom de l'entité (requis)
            - days: Nombre de jours (défaut: 30)
        
        Returns:
            JSON avec timeline
        """
        try:
            entity_name = request.args.get('entity')
            days = request.args.get('days', 30, type=int)
            
            if not entity_name:
                return jsonify({
                    'success': False,
                    'error': 'Paramètre "entity" requis'
                }), 400
            
            logger.info(f"📅 Timeline pour: {entity_name}")
            
            timeline = geo_entity_integration.get_entity_timeline(
                entity_name=entity_name,
                days=days
            )
            
            return jsonify({
                'success': True,
                'timeline': timeline
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur timeline: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =========================================================================
    # VISUALISATION DES RELATIONS
    # =========================================================================
    
    @bp.route('/entity-relations', methods=['GET'])
    def get_entity_relations():
        """
        Graphe de relations entre entités (co-occurrences)
        
        Query params:
            - days: Nombre de jours (défaut: 7)
        
        Returns:
            JSON avec graphe de relations (format D3.js/vis.js)
        """
        try:
            days = request.args.get('days', 7, type=int)
            
            logger.info(f"🕸️ Extraction relations sur {days} jours")
            
            graph = geo_entity_integration.get_entity_relations(days=days)
            
            return jsonify({
                'success': True,
                'graph': graph
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur relations: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =========================================================================
    # EXPORT ET RAPPORTS
    # =========================================================================
    
    @bp.route('/report', methods=['GET', 'POST'])
    def generate_report():
        """
        Génère un rapport complet
        
        Query/Body params:
            - days: Nombre de jours (défaut: 7)
            - format: 'json' ou 'markdown' (défaut: json)
        
        Returns:
            Rapport formaté
        """
        try:
            if request.method == 'POST':
                data = request.get_json() or {}
                days = data.get('days', 7)
                report_format = data.get('format', 'json')
            else:
                days = request.args.get('days', 7, type=int)
                report_format = request.args.get('format', 'json')
            
            logger.info(f"📄 Génération rapport: {days} jours, format: {report_format}")
            
            report = geo_entity_integration.generate_comprehensive_report(
                days=days,
                format=report_format
            )
            
            if report_format == 'json':
                return Response(
                    report,
                    mimetype='application/json',
                    headers={
                        'Content-Disposition': f'attachment; filename=geo_report_{days}days.json'
                    }
                )
            elif report_format == 'markdown':
                return Response(
                    report,
                    mimetype='text/markdown',
                    headers={
                        'Content-Disposition': f'attachment; filename=geo_report_{days}days.md'
                    }
                )
            else:
                return jsonify({
                    'success': False,
                    'error': 'Format non supporté. Utilisez json ou markdown'
                }), 400
            
        except Exception as e:
            logger.error(f"❌ Erreur génération rapport: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =========================================================================
    # STATISTIQUES AVANCÉES
    # =========================================================================
    
    @bp.route('/stats/patterns', methods=['GET'])
    def get_pattern_statistics():
        """
        Statistiques détaillées sur les patterns
        
        Query params:
            - days: Nombre de jours (défaut: 7)
        
        Returns:
            JSON avec statistiques
        """
        try:
            days = request.args.get('days', 7, type=int)
            
            patterns = geo_entity_integration.analyze_patterns_with_entities(
                days=days,
                min_countries=2
            )
            
            # Calculer des statistiques
            if not patterns:
                return jsonify({
                    'success': True,
                    'stats': {
                        'total_patterns': 0,
                        'avg_countries_per_pattern': 0,
                        'avg_entities_per_pattern': 0,
                        'most_common_entity_types': {}
                    }
                }), 200
            
            avg_countries = sum(p.get('country_count', 0) for p in patterns) / len(patterns)
            avg_entities = sum(p.get('entity_richness_score', 0) for p in patterns) / len(patterns)
            
            # Compter les types d'entités
            entity_type_counts = {
                'locations': 0,
                'organizations': 0,
                'persons': 0,
                'groups': 0,
                'events': 0
            }
            
            for pattern in patterns:
                counts = pattern.get('entity_counts', {})
                for entity_type, count in counts.items():
                    entity_type_counts[entity_type] += count
            
            stats = {
                'total_patterns': len(patterns),
                'avg_countries_per_pattern': round(avg_countries, 2),
                'avg_entities_per_pattern': round(avg_entities, 2),
                'entity_type_distribution': entity_type_counts,
                'richest_pattern': max(patterns, key=lambda p: p.get('entity_richness_score', 0)),
                'most_transnational_pattern': max(patterns, key=lambda p: p.get('country_count', 0))
            }
            
            return jsonify({
                'success': True,
                'stats': stats
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur statistiques: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/stats/entities', methods=['GET'])
    def get_entity_statistics():
        """
        Statistiques sur les entités détectées
        
        Query params:
            - days: Nombre de jours (défaut: 7)
        
        Returns:
            JSON avec statistiques sur les entités
        """
        try:
            days = request.args.get('days', 7, type=int)
            
            analysis = geo_entity_integration.analyze_articles_comprehensive(days=days)
            entity_network = analysis.get('entity_network', {})
            
            stats = {
                'top_locations': entity_network.get('top_locations', [])[:10],
                'top_organizations': entity_network.get('top_organizations', [])[:10],
                'top_persons': entity_network.get('top_persons', [])[:10],
                'network_density': entity_network.get('network_density', 0),
                'total_articles_analyzed': entity_network.get('total_articles_analyzed', 0)
            }
            
            return jsonify({
                'success': True,
                'stats': stats
            }), 200
            
        except Exception as e:
            logger.error(f"❌ Erreur statistiques entités: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # =========================================================================
    # SANTÉ ET DEBUG
    # =========================================================================
    
    @bp.route('/health', methods=['GET'])
    def health_check():
        """Vérification santé du service intégré"""
        return jsonify({
            'status': 'ok',
            'service': 'geo_entity_integrated',
            'components': {
                'geo_narrative_analyzer': geo_narrative_analyzer is not None,
                'entity_extractor': entity_extractor is not None,
                'entity_db_manager': entity_db_manager is not None,
                'integration': geo_entity_integration is not None
            }
        }), 200
    
    logger.info("✅ Blueprint geo_entity_integrated créé")
    
    return bp


# =========================================================================
# FONCTION D'ENREGISTREMENT
# =========================================================================

def register_integrated_routes(
    app,
    db_manager,
    geo_narrative_analyzer,
    entity_extractor,
    entity_db_manager,
    geo_entity_integration
):
    """
    Enregistre le blueprint dans l'app Flask
    
    Args:
        app: Instance Flask
        db_manager: Gestionnaire BDD
        geo_narrative_analyzer: Analyseur geo-narrative
        entity_extractor: Extracteur d'entités
        entity_db_manager: Gestionnaire BDD entités
        geo_entity_integration: Intégrateur
    """
    try:
        bp = create_integrated_blueprint(
            db_manager,
            geo_narrative_analyzer,
            entity_extractor,
            entity_db_manager,
            geo_entity_integration
        )
        
        app.register_blueprint(bp)
        
        logger.info("✅ Routes intégrées geo-entity enregistrées")
        logger.info("📍 Routes disponibles:")
        logger.info("   GET  /api/geo-entity/patterns-enriched")
        logger.info("   GET  /api/geo-entity/comprehensive-analysis")
        logger.info("   GET  /api/geo-entity/patterns/by-entity")
        logger.info("   GET  /api/geo-entity/entity/timeline")
        logger.info("   GET  /api/geo-entity/entity-relations")
        logger.info("   GET  /api/geo-entity/report")
        logger.info("   GET  /api/geo-entity/stats/patterns")
        logger.info("   GET  /api/geo-entity/stats/entities")
        logger.info("   GET  /api/geo-entity/health")
        
    except Exception as e:
        logger.error(f"❌ Erreur enregistrement routes intégrées: {e}")
        raise