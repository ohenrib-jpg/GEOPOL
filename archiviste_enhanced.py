# Flask/archiviste_enhanced.py
import logging
from typing import List, Dict, Any
from .archiviste_database import ArchivisteDatabase  # [OK] Import relatif corrigé

logger = logging.getLogger(__name__)

class EnhancedArchiviste:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.archiviste_db = ArchivisteDatabase(db_manager)
        
        # Périodes historiques étendues
        self.historical_periods = {
            '1945-1950': {'start': '1945-01-01', 'end': '1950-12-31', 'name': 'Après-guerre (1945-1950)'},
            '1950-1960': {'start': '1950-01-01', 'end': '1960-12-31', 'name': 'Guerre froide débuts (1950-1960)'},
            '1960-1970': {'start': '1960-01-01', 'end': '1970-12-31', 'name': 'Décolonisation (1960-1970)'},
            '1970-1980': {'start': '1970-01-01', 'end': '1980-12-31', 'name': 'Détente (1970-1980)'},
            '1980-1990': {'start': '1980-01-01', 'end': '1990-12-31', 'name': 'Fin guerre froide (1980-1990)'},
            '1990-2000': {'start': '1990-01-01', 'end': '2000-12-31', 'name': 'Nouvel ordre mondial (1990-2000)'},
            '2000-2010': {'start': '2000-01-01', 'end': '2010-12-31', 'name': 'Post-11/09 (2000-2010)'},
            '2010-2020': {'start': '2010-01-01', 'end': '2020-12-31', 'name': 'Printemps arabes/Crise (2010-2020)'},
            '2020-2025': {'start': '2020-01-01', 'end': '2025-12-31', 'name': 'Pandémie/IA (2020-2025)'}
        }
    
    def get_available_themes(self) -> List[Dict[str, Any]]:
        """Récupère tous les thèmes disponibles avec statistiques"""
        try:
            themes = self.archiviste_db.get_user_themes_with_keywords()
            logger.info(f"[DATA] {len(themes)} thèmes disponibles")
            return themes
        except Exception as e:
            logger.error(f"[ERROR] Erreur get_available_themes: {e}")
            return []

    def analyze_period_with_theme(self, period_key: str, theme_id: int, max_items: int = 100) -> Dict[str, Any]:
        """Analyse une période historique avec un thème spécifique"""
        try:
            logger.info(f"[TARGET] Début analyse période {period_key} avec thème ID {theme_id}")
            
            if period_key not in self.historical_periods:
                return {
                    'success': False,
                    'error': f'Période inconnue: {period_key}'
                }
            
            period = self.historical_periods[period_key]
            start_year = int(period['start'][:4])
            end_year = int(period['end'][:4])
            
            # Récupérer le thème
            themes = self.get_available_themes()
            theme = next((t for t in themes if t['id'] == theme_id), None)
            
            if not theme:
                available_ids = [t['id'] for t in themes]
                return {
                    'success': False,
                    'error': f'Thème ID {theme_id} inconnu. Thèmes disponibles: {available_ids}',
                    'available_themes': [{'id': t['id'], 'name': t['name']} for t in themes]
                }
            
            logger.info(f"[TARGET] Analyse période {period['name']} avec thème: {theme['name']} (ID: {theme_id})")
            
            # Recherche avec les mots-clés du thème
            if not theme.get('keywords'):
                return {
                    'success': False,
                    'error': f'Le thème "{theme["name"]}" n\'a pas de mots-clés définis'
                }
            
            # Utiliser les mots-clés pour la recherche
            query = ' OR '.join(theme['keywords'][:5])
            
            # Simulation de recherche pour le moment
            simulated_items = self.search_archive_simulation(query, start_year, end_year, max_items)
            
            if not simulated_items:
                return {
                    'success': False,
                    'error': f'Aucun contenu trouvé pour {period["name"]} avec le thème {theme["name"]}',
                    'period': period,
                    'theme': theme,
                    'query_used': query
                }
            
            # Analyser les items
            analyzed_items = []
            for item in simulated_items:
                try:
                    text = self._extract_text_from_item(item)
                    
                    if len(text) < 20:
                        continue
                    
                    analyzed_item = {
                        **item,
                        'text_extract': text[:500],
                        'word_count': len(text.split())
                    }
                    
                    analyzed_items.append(analyzed_item)
                    
                except Exception as e:
                    logger.debug(f"Erreur analyse item: {e}")
                    continue
            
            # Calculer les statistiques
            stats = self._calculate_enhanced_statistics(analyzed_items, period_key, theme)
            
            result = {
                'success': True,
                'period': period,
                'theme': theme,
                'items_analyzed': len(analyzed_items),
                'statistics': stats,
                'top_items': analyzed_items[:10],
                'theme_coverage': self._calculate_theme_coverage(analyzed_items, theme),
                'query_used': query
            }
            
            logger.info(f"[OK] Analyse terminée: {len(analyzed_items)} items analysés")
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] Erreur analyze_period_with_theme: {e}")
            return {
                'success': False,
                'error': f'Erreur lors de l\'analyse: {str(e)}'
            }

    def search_archive_simulation(self, query: str, start_year: int, end_year: int, max_items: int = 50) -> List[Dict[str, Any]]:
        """Simulation de recherche Archive.org pour les tests"""
        logger.info(f"[SEARCH] Simulation recherche: {query} ({start_year}-{end_year})")
        
        # Données simulées réalistes
        simulated_items = []
        for i in range(min(15, max_items)):
            year = start_year + (i * 2) % (end_year - start_year + 1)
            simulated_items.append({
                'identifier': f'sim-item-{year}-{i}',
                'title': f'Document {year} sur {query.split(" OR ")[0] if " OR " in query else query}',
                'description': f'Description historique concernant {query} pendant la période {year}',
                'year': year,
                'collection': ['newspapers', 'historical-documents'],
                'subject': [query.split(" OR ")[0], 'histoire', 'archives'],
                'creator': 'Various Historical Sources',
                'downloads': 150 + i * 15
            })
        
        return simulated_items
    
    def _extract_text_from_item(self, item_data: Dict[str, Any]) -> str:
        """Extrait le texte d'un item Archive.org"""
        text_parts = []
        
        if item_data.get('title'):
            text_parts.append(item_data['title'])
        
        if item_data.get('description'):
            desc = item_data['description']
            if isinstance(desc, list):
                text_parts.extend(desc)
            else:
                text_parts.append(str(desc))
        
        if item_data.get('subject'):
            subjects = item_data['subject']
            if isinstance(subjects, list):
                text_parts.extend(subjects)
            else:
                text_parts.append(str(subjects))
        
        if item_data.get('creator'):
            text_parts.append(str(item_data['creator']))
        
        return ' '.join(text_parts)
    
    def _calculate_enhanced_statistics(self, items: List[Dict], period_key: str, theme: Dict) -> Dict[str, Any]:
        """Calcule des statistiques avancées avec focus sur le thème"""
        if not items:
            return {}
        
        # Mots-clés les plus fréquents dans ce contexte
        all_keywords = []
        for item in items:
            text = item.get('text_extract', '').lower()
            for keyword in theme['keywords']:
                if keyword.lower() in text:
                    all_keywords.append(keyword)
        
        from collections import Counter
        keyword_freq = Counter(all_keywords)
        
        return {
            'period_key': period_key,
            'theme_id': theme['id'],
            'total_items': len(items),
            'relevance_metrics': {
                'average_relevance': 0.65,  # Simulation
                'high_relevance_items': len([i for i in items if len(i.get('text_extract', '')) > 100]),
                'medium_relevance_items': len([i for i in items if 50 <= len(i.get('text_extract', '')) <= 100]),
                'low_relevance_items': len([i for i in items if len(i.get('text_extract', '')) < 50])
            },
            'keyword_frequency': keyword_freq.most_common(10),
            'temporal_distribution': self._calculate_temporal_distribution(items),
            'source_distribution': self._calculate_source_distribution(items)
        }
    
    def _calculate_theme_coverage(self, items: List[Dict], theme: Dict) -> Dict[str, Any]:
        """Calcule la couverture thématique"""
        total_keywords = len(theme['keywords'])
        covered_keywords = set()
        
        for item in items:
            text = item.get('text_extract', '').lower()
            for keyword in theme['keywords']:
                if keyword.lower() in text:
                    covered_keywords.add(keyword)
        
        coverage_percent = (len(covered_keywords) / total_keywords * 100) if total_keywords > 0 else 0
        
        return {
            'total_keywords': total_keywords,
            'covered_keywords': len(covered_keywords),
            'coverage_percent': round(coverage_percent, 1),
            'missing_keywords': [k for k in theme['keywords'] if k not in covered_keywords],
            'well_covered_keywords': list(covered_keywords)
        }
    
    def _calculate_temporal_distribution(self, items: List[Dict]) -> Dict[str, int]:
        """Calcule la distribution temporelle des items"""
        year_counts = {}
        for item in items:
            year = item.get('year')
            if year:
                year_counts[year] = year_counts.get(year, 0) + 1
        
        return dict(sorted(year_counts.items()))
    
    def _calculate_source_distribution(self, items: List[Dict]) -> Dict[str, int]:
        """Calcule la distribution par source/collection"""
        collection_counts = {}
        for item in items:
            collections = item.get('collection', [])
            if isinstance(collections, list):
                for collection in collections:
                    collection_counts[collection] = collection_counts.get(collection, 0) + 1
            elif collections:
                collection_counts[collections] = collection_counts.get(collections, 0) + 1
        
        return dict(sorted(collection_counts.items(), key=lambda x: x[1], reverse=True))
