# Flask/geo_entity_integration.py - Intégration Geo-Narrative + Entity Extractor

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class GeoEntityIntegration:
    """
    Orchestrateur combinant l'analyse géo-narrative avec l'extraction d'entités.
    Permet d'enrichir les patterns transnationaux avec des entités géopolitiques.
    """
    
    def __init__(self, geo_narrative_analyzer, entity_extractor, entity_db_manager):
        """
        Initialise l'intégrateur
        
        Args:
            geo_narrative_analyzer: Instance de GeoNarrativeAnalyzer
            entity_extractor: Instance de GeopoliticalEntityExtractor
            entity_db_manager: Instance de EntityDatabaseManager
        """
        self.geo_analyzer = geo_narrative_analyzer
        self.entity_extractor = entity_extractor
        self.entity_db = entity_db_manager
        
        logger.info("✅ GeoEntityIntegration initialisé")
    
    # =========================================================================
    # MÉTHODE PRINCIPALE - ANALYSE ENRICHIE
    # =========================================================================
    
    def analyze_patterns_with_entities(self, days: int = 7, min_countries: int = 2) -> List[Dict[str, Any]]:
        """
        Analyse les patterns transnationaux ET extrait les entités associées
        
        Args:
            days: Période d'analyse en jours
            min_countries: Nombre minimum de pays pour considérer un pattern
            
        Returns:
            Liste de patterns enrichis avec entités géopolitiques
        """
        try:
            logger.info(f"🔍 Analyse enrichie: {days} jours, min {min_countries} pays")
            
            # 1. Détecter les patterns transnationaux
            patterns = self.geo_analyzer.detect_transnational_patterns(
                days=days, 
                min_countries=min_countries
            )
            
            if not patterns:
                logger.warning("⚠️ Aucun pattern détecté")
                return []
            
            logger.info(f"📊 {len(patterns)} patterns détectés, enrichissement en cours...")
            
            # 2. Enrichir chaque pattern avec des entités
            enriched_patterns = []
            for pattern in patterns:
                enriched = self._enrich_pattern_with_entities(pattern)
                enriched_patterns.append(enriched)
            
            # 3. Calculer des statistiques globales
            enriched_patterns = self._add_global_statistics(enriched_patterns)
            
            logger.info(f"✅ {len(enriched_patterns)} patterns enrichis")
            
            return enriched_patterns
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse enrichie: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _enrich_pattern_with_entities(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrichit un pattern avec les entités géopolitiques extraites
        
        Args:
            pattern: Pattern brut de geo_narrative_analyzer
            
        Returns:
            Pattern enrichi avec entités
        """
        try:
            pattern_text = pattern['pattern']
            
            # Extraire les entités du pattern
            entities = self.entity_extractor.extract_entities(pattern_text)
            
            # Enrichir le pattern
            pattern['entities'] = {
                'locations': entities.get('locations', []),
                'organizations': entities.get('organizations', []),
                'persons': entities.get('persons', []),
                'groups': entities.get('groups', []),
                'events': entities.get('events', [])
            }
            
            # Compter les entités
            pattern['entity_counts'] = {
                'locations': len(entities.get('locations', [])),
                'organizations': len(entities.get('organizations', [])),
                'persons': len(entities.get('persons', [])),
                'groups': len(entities.get('groups', [])),
                'events': len(entities.get('events', []))
            }
            
            # Calculer un score de "richesse" du pattern
            total_entities = sum(pattern['entity_counts'].values())
            pattern['entity_richness_score'] = total_entities
            
            return pattern
            
        except Exception as e:
            logger.error(f"❌ Erreur enrichissement pattern: {e}")
            # Retourner le pattern original en cas d'erreur
            pattern['entities'] = {}
            pattern['entity_counts'] = {}
            pattern['entity_richness_score'] = 0
            return pattern
    
    def _add_global_statistics(self, patterns: List[Dict]) -> List[Dict]:
        """
        Ajoute des statistiques globales sur les entités
        
        Args:
            patterns: Liste de patterns enrichis
            
        Returns:
            Patterns avec statistiques ajoutées
        """
        # Compter toutes les entités
        all_locations = []
        all_organizations = []
        all_persons = []
        
        for pattern in patterns:
            entities = pattern.get('entities', {})
            all_locations.extend([e['text'] for e in entities.get('locations', [])])
            all_organizations.extend([e['text'] for e in entities.get('organizations', [])])
            all_persons.extend([e['text'] for e in entities.get('persons', [])])
        
        # Calculer les entités les plus fréquentes
        location_freq = Counter(all_locations)
        org_freq = Counter(all_organizations)
        person_freq = Counter(all_persons)
        
        # Ajouter aux métadonnées de chaque pattern
        for pattern in patterns:
            pattern['global_context'] = {
                'top_locations': location_freq.most_common(5),
                'top_organizations': org_freq.most_common(5),
                'top_persons': person_freq.most_common(5)
            }
        
        return patterns
    
    # =========================================================================
    # ANALYSE PAR ARTICLES
    # =========================================================================
    
    def analyze_articles_comprehensive(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyse complète : patterns + entités pour tous les articles
        
        Args:
            days: Période d'analyse
            
        Returns:
            Rapport complet avec patterns et réseau d'entités
        """
        try:
            logger.info(f"🔎 Analyse complète sur {days} jours...")
            
            # 1. Récupérer les articles
            articles_by_country = self.geo_analyzer._get_recent_articles_by_country(days)
            
            all_articles = []
            for country, articles in articles_by_country.items():
                all_articles.extend(articles)
            
            logger.info(f"📚 {len(all_articles)} articles à analyser")
            
            # 2. Analyser les patterns
            patterns = self.analyze_patterns_with_entities(days=days, min_countries=2)
            
            # 3. Créer le réseau d'entités global
            entity_network = self.entity_extractor.extract_geopolitical_network(all_articles)
            
            # 4. Sauvegarder les entités en base de données
            self._save_entities_to_db(all_articles)
            
            # 5. Compiler le rapport
            report = {
                'analysis_date': datetime.now().isoformat(),
                'period_days': days,
                'summary': {
                    'total_articles': len(all_articles),
                    'countries_analyzed': len(articles_by_country),
                    'patterns_detected': len(patterns),
                    'unique_locations': len(entity_network['top_locations']),
                    'unique_organizations': len(entity_network['top_organizations']),
                    'unique_persons': len(entity_network['top_persons'])
                },
                'patterns': patterns,
                'entity_network': entity_network,
                'articles_by_country': {
                    country: len(articles) 
                    for country, articles in articles_by_country.items()
                }
            }
            
            logger.info("✅ Analyse complète terminée")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse complète: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _save_entities_to_db(self, articles: List[Dict]) -> None:
        """
        Sauvegarde les entités extraites en base de données
        
        Args:
            articles: Liste d'articles à traiter
        """
        try:
            saved_count = 0
            
            for article in articles:
                # Extraire les entités
                analysis = self.entity_extractor.analyze_article(article)
                entities = analysis['entities']
                
                # Sauvegarder pour chaque catégorie
                article_id = article.get('id')
                if not article_id:
                    continue
                
                # Locations
                for entity in entities.get('locations', []):
                    self.entity_db.save_entity(
                        article_id=article_id,
                        entity_text=entity['text'],
                        entity_type='location',
                        entity_label=entity.get('label', 'GPE'),
                        context=entity.get('context', '')
                    )
                
                # Organizations
                for entity in entities.get('organizations', []):
                    self.entity_db.save_entity(
                        article_id=article_id,
                        entity_text=entity['text'],
                        entity_type='organization',
                        entity_label=entity.get('label', 'ORG'),
                        context=entity.get('context', '')
                    )
                
                # Persons
                for entity in entities.get('persons', []):
                    self.entity_db.save_entity(
                        article_id=article_id,
                        entity_text=entity['text'],
                        entity_type='person',
                        entity_label=entity.get('label', 'PERSON'),
                        context=entity.get('context', '')
                    )
                
                saved_count += 1
            
            logger.info(f"💾 Entités sauvegardées pour {saved_count} articles")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde entités: {e}")
    
    # =========================================================================
    # RECHERCHE ET FILTRAGE
    # =========================================================================
    
    def find_patterns_by_entity(
        self, 
        entity_name: str, 
        entity_type: Optional[str] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Trouve tous les patterns mentionnant une entité spécifique
        
        Args:
            entity_name: Nom de l'entité (ex: "France", "ONU", "Macron")
            entity_type: Type d'entité (optionnel: location, organization, person)
            days: Période d'analyse
            
        Returns:
            Liste de patterns contenant cette entité
        """
        try:
            # Analyser avec entités
            patterns = self.analyze_patterns_with_entities(days=days)
            
            # Filtrer les patterns contenant l'entité
            matching_patterns = []
            
            for pattern in patterns:
                entities = pattern.get('entities', {})
                
                # Chercher dans toutes les catégories ou une catégorie spécifique
                categories = [entity_type] if entity_type else entities.keys()
                
                for category in categories:
                    entity_list = entities.get(category, [])
                    for entity in entity_list:
                        if entity_name.lower() in entity['text'].lower():
                            matching_patterns.append(pattern)
                            break
            
            logger.info(f"🔍 {len(matching_patterns)} patterns trouvés pour '{entity_name}'")
            
            return matching_patterns
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche par entité: {e}")
            return []
    
    def get_entity_timeline(
        self, 
        entity_name: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Chronologie d'apparition d'une entité dans les patterns
        
        Args:
            entity_name: Nom de l'entité
            days: Période d'analyse
            
        Returns:
            Timeline avec patterns et dates
        """
        try:
            # Récupérer les entités de la BDD
            entities = self.entity_db.get_entities_by_text(entity_name)
            
            # Grouper par date
            timeline = defaultdict(list)
            
            for entity in entities:
                date = entity.get('created_at', '').split('T')[0]  # Extraire juste la date
                timeline[date].append({
                    'article_id': entity.get('article_id'),
                    'context': entity.get('context', '')[:100] + '...',
                    'type': entity.get('entity_type')
                })
            
            # Convertir en liste triée
            sorted_timeline = [
                {
                    'date': date,
                    'occurrences': len(items),
                    'examples': items[:3]  # Limiter à 3 exemples par jour
                }
                for date, items in sorted(timeline.items())
            ]
            
            return {
                'entity': entity_name,
                'total_occurrences': sum(len(items) for items in timeline.values()),
                'days_analyzed': days,
                'timeline': sorted_timeline
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur timeline entité: {e}")
            return {}
    
    # =========================================================================
    # VISUALISATION DES RELATIONS
    # =========================================================================
    
    def get_entity_relations(
        self, 
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Extrait les relations entre entités (co-occurrences)
        
        Args:
            days: Période d'analyse
            
        Returns:
            Graphe de relations entre entités
        """
        try:
            # Analyser les articles
            articles_by_country = self.geo_analyzer._get_recent_articles_by_country(days)
            all_articles = []
            for articles in articles_by_country.values():
                all_articles.extend(articles)
            
            # Créer le graphe de relations
            relations = []
            
            for article in all_articles:
                # Extraire les entités de l'article
                analysis = self.entity_extractor.analyze_article(article)
                entities = analysis['entities']
                
                # Créer des relations entre locations et organizations
                locations = [e['text'] for e in entities.get('locations', [])]
                organizations = [e['text'] for e in entities.get('organizations', [])]
                persons = [e['text'] for e in entities.get('persons', [])]
                
                # Relations location-organization
                for loc in locations:
                    for org in organizations:
                        relations.append({
                            'source': loc,
                            'target': org,
                            'type': 'location-organization',
                            'article_id': article.get('id')
                        })
                
                # Relations organization-person
                for org in organizations:
                    for person in persons:
                        relations.append({
                            'source': org,
                            'target': person,
                            'type': 'organization-person',
                            'article_id': article.get('id')
                        })
            
            # Compter les relations
            relation_counts = Counter(
                (r['source'], r['target'], r['type']) 
                for r in relations
            )
            
            # Formater pour visualisation (format D3.js/vis.js)
            nodes = set()
            for relation in relations:
                nodes.add(relation['source'])
                nodes.add(relation['target'])
            
            graph = {
                'nodes': [{'id': node, 'label': node} for node in nodes],
                'edges': [
                    {
                        'source': source,
                        'target': target,
                        'weight': count,
                        'type': rel_type
                    }
                    for (source, target, rel_type), count in relation_counts.most_common(50)
                ],
                'metadata': {
                    'total_nodes': len(nodes),
                    'total_edges': len(relation_counts),
                    'analysis_date': datetime.now().isoformat(),
                    'period_days': days
                }
            }
            
            return graph
            
        except Exception as e:
            logger.error(f"❌ Erreur relations entités: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    # =========================================================================
    # EXPORT ET RAPPORTS
    # =========================================================================
    
    def generate_comprehensive_report(
        self, 
        days: int = 7,
        format: str = 'json'
    ) -> str:
        """
        Génère un rapport complet combinant patterns et entités
        
        Args:
            days: Période d'analyse
            format: Format de sortie ('json' ou 'markdown')
            
        Returns:
            Rapport formaté
        """
        try:
            # Analyse complète
            analysis = self.analyze_articles_comprehensive(days=days)
            
            if format == 'json':
                import json
                return json.dumps(analysis, ensure_ascii=False, indent=2)
            
            elif format == 'markdown':
                # Générer un rapport Markdown
                md = f"# 🌍 Rapport Géopolitique\n\n"
                md += f"**Date:** {analysis['analysis_date']}\n"
                md += f"**Période:** {days} jours\n\n"
                
                md += "## 📊 Résumé\n\n"
                summary = analysis['summary']
                md += f"- Articles analysés: **{summary['total_articles']}**\n"
                md += f"- Pays: **{summary['countries_analyzed']}**\n"
                md += f"- Patterns détectés: **{summary['patterns_detected']}**\n"
                md += f"- Lieux uniques: **{summary['unique_locations']}**\n"
                md += f"- Organisations uniques: **{summary['unique_organizations']}**\n"
                md += f"- Personnalités uniques: **{summary['unique_persons']}**\n\n"
                
                md += "## 🔍 Top Patterns Transnationaux\n\n"
                for i, pattern in enumerate(analysis['patterns'][:10], 1):
                    md += f"### {i}. \"{pattern['pattern']}\"\n\n"
                    md += f"- Pays: {', '.join(pattern['countries'])}\n"
                    md += f"- Occurrences: {pattern.get('total_occurrences', 0)}\n"
                    
                    # Entités associées
                    entities = pattern.get('entities', {})
                    if entities.get('locations'):
                        locs = [e['text'] for e in entities['locations'][:3]]
                        md += f"- Lieux: {', '.join(locs)}\n"
                    if entities.get('organizations'):
                        orgs = [e['text'] for e in entities['organizations'][:3]]
                        md += f"- Organisations: {', '.join(orgs)}\n"
                    
                    md += "\n"
                
                return md
            
            else:
                return "Format non supporté"
            
        except Exception as e:
            logger.error(f"❌ Erreur génération rapport: {e}")
            return f"Erreur: {str(e)}"
