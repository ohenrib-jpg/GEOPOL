"""
Service principal Archiviste v3.0 - VERSION CORRIGÉE
Utilise les MOTS-CLÉS DES THÈMES utilisateur pour la recherche
"""

import logging
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import Counter, defaultdict
import time
import os
import sys

logger = logging.getLogger(__name__)

class ArchivisteServiceImproved:
    """Service principal utilisant les thèmes définis par l'utilisateur"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Importer les dépendances
        try:
            from archive_client import ArchiveOrgClient
            self.archive_client = ArchiveOrgClient()
            logger.info("✅ ArchiveOrgClient initialisé")
        except ImportError as e:
            logger.error(f"❌ Erreur import ArchiveOrgClient: {e}")
            self.archive_client = None
        
        try:
            from archiviste_database import ArchivisteDatabase
            self.database = ArchivisteDatabase(db_manager)
            logger.info("✅ ArchivisteDatabase initialisé")
        except ImportError as e:
            logger.error(f"❌ Erreur import ArchivisteDatabase: {e}")
            self.database = None
        
        # Périodes historiques (contexte seulement)
        self.historical_periods = {
            '1945-1950': {'name': 'Après-guerre', 'start': 1945, 'end': 1950},
            '1950-1960': {'name': 'Guerre Froide début', 'start': 1950, 'end': 1960},
            '1960-1970': {'name': 'Tensions nucléaires', 'start': 1960, 'end': 1970},
            '1970-1980': {'name': 'Détente et crises', 'start': 1970, 'end': 1980},
            '1980-1991': {'name': 'Fin Guerre Froide', 'start': 1980, 'end': 1991},
            '1991-2000': {'name': 'Post-Guerre Froide', 'start': 1991, 'end': 2000},
            '2000-2010': {'name': 'Terrorisme et crise', 'start': 2000, 'end': 2010},
            '2010-2019': {'name': 'Numérique et instabilité', 'start': 2010, 'end': 2019},
            '2019-2022': {'name': 'Pandémie COVID-19', 'start': 2019, 'end': 2022},
            '2022-2025': {'name': 'Crises géopolitiques', 'start': 2022, 'end': 2025}
        }
        
        self._search_cache = {}
        self.session_stats = {'searches': 0, 'items_analyzed': 0, 'errors': 0}
        
    def get_available_periods(self) -> Dict[str, Dict[str, Any]]:
        """Retourne les périodes historiques"""
        return self.historical_periods
    
    def get_theme_keywords(self, theme_id: int) -> List[str]:
        """Récupère les mots-clés d'un thème depuis la base"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT keywords FROM themes WHERE id = ?", (theme_id,))
            row = cursor.fetchone()
            
            if not row or not row[0]:
                return []
            
            keywords_data = row[0]
            
            # Gestion flexible du format des mots-clés
            if isinstance(keywords_data, str):
                try:
                    # Essayer de parser comme JSON
                    keywords = json.loads(keywords_data)
                    if isinstance(keywords, list):
                        return keywords
                except:
                    # Sinon, split par virgules ou retours à la ligne
                    if ',' in keywords_data:
                        return [k.strip() for k in keywords_data.split(',') if k.strip()]
                    else:
                        return [k.strip() for k in keywords_data.split('\n') if k.strip()]
            
            elif isinstance(keywords_data, list):
                return keywords_data
                
            return []
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération mots-clés thème {theme_id}: {e}")
            return []
        finally:
            conn.close()

    def build_theme_based_query(self, theme_id: int, period_context: Dict = None) -> str:
        """Construit une requête basée sur les mots-clés du thème utilisateur"""
        # Récupérer les mots-clés du thème
        theme_keywords = self.get_theme_keywords(theme_id)
        
        if not theme_keywords:
            logger.warning(f"⚠️ Thème {theme_id} sans mots-clés, utilisation par défaut")
            theme_keywords = ['histoire', 'politique', 'conflit']
        
        logger.info(f"🔑 Mots-clés du thème {theme_id}: {len(theme_keywords)} trouvés")
        
        # Construction de la requête optimisée pour Archive.org
        query_parts = []
        
        # Utiliser les 3-5 premiers mots-clés du thème pour la recherche principale
        primary_keywords = theme_keywords[:5]
        
        # Ajouter des recherches spécifiques pour chaque mot-clé principal
        for keyword in primary_keywords:
            # Recherche dans le titre (plus pertinent)
            query_parts.append(f'title:"{keyword}"')
            # Recherche dans la description
            query_parts.append(f'description:"{keyword}"')
        
        # Ajouter les mots-clés restants comme recherche générale
        if len(theme_keywords) > 5:
            general_keywords = ' OR '.join([f'"{kw}"' for kw in theme_keywords[5:8]])
            query_parts.append(f'({general_keywords})')
        
        # Combiner toutes les parties avec OR
        final_query = ' OR '.join(query_parts)
        
        logger.info(f"🔍 Requête construite: {final_query[:100]}...")
        return final_query

    def analyze_period_with_theme(
        self, 
        period_key: str, 
        theme_id: int,
        max_items: int = 50
    ) -> Dict[str, Any]:
        """Analyse utilisant les MOTS-CLÉS DU THÈME UTILISATEUR"""
        try:
            # Validation de la période
            if period_key not in self.historical_periods:
                return {
                    'success': False,
                    'error': f'Période inconnue: {period_key}'
                }
            
            period = self.historical_periods[period_key]
            
            # Récupérer le thème avec son nom
            theme_info = self.get_theme_info(theme_id)
            if not theme_info:
                return {
                    'success': False,
                    'error': f'Thème {theme_id} non trouvé'
                }
            
            # CONSTRUCTION DE LA REQUÊTE BASÉE SUR LE THÈME
            search_query = self.build_theme_based_query(theme_id, period)
            
            # Recherche avec Archive.org
            start_year = period.get('start')
            end_year = period.get('end')
            
            archive_data = []
            if self.archive_client:
                archive_data = self.archive_client.search_press_articles(
                    query=search_query,
                    start_year=start_year,
                    end_year=end_year,
                    max_results=max_items
                )
            
            if not archive_data:
                return {
                    'success': False,
                    'error': f'Aucun article trouvé pour "{theme_info["name"]}" ({period["name"]})',
                    'search_query': search_query,
                    'period': period,
                    'theme': theme_info
                }
            
            # Traitement des résultats
            from historical_item import HistoricalItem
            items = []
            
            for data in archive_data:
                try:
                    item = HistoricalItem(data)
                    items.append(item)
                except Exception as e:
                    logger.warning(f"⚠️ Erreur création item: {e}")
                    continue
            
            # Génération des résultats
            key_items = self._identify_key_items(items, top_n=min(10, len(items)))
            insights = self._generate_insights(items, period, theme_info)
            
            result = {
                'success': True,
                'period': period,
                'theme': theme_info,
                'period_key': period_key,
                'theme_id': theme_id,
                'items_analyzed': len(items),
                'key_items': [item.to_dict() for item in key_items],
                'insights': insights,
                'search_query': search_query,
                'search_metadata': {
                    'query_used': search_query,
                    'theme_keywords_used': self.get_theme_keywords(theme_id)[:10],
                    'items_found': len(archive_data),
                    'period_constraint': f"{start_year}-{end_year}" if start_year and end_year else "Aucune"
                },
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Analyse réussie: {len(items)} items pour {theme_info['name']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse: {e}")
            return {
                'success': False,
                'error': f'Erreur analyse: {str(e)}'
            }

    def get_theme_info(self, theme_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un thème"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, name, color, description FROM themes WHERE id = ?", (theme_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return {
                'id': row[0],
                'name': row[1],
                'color': row[2] or '#6366f1',
                'description': row[3] or '',
                'keywords_count': len(self.get_theme_keywords(theme_id))
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération thème {theme_id}: {e}")
            return None
        finally:
            conn.close()

    def _identify_key_items(self, items: List, top_n: int = 10) -> List:
        """Identifie les items les plus pertinents"""
        if not items:
            return []
        
        # Trier par pertinence (downloads, puis titre significatif)
        items.sort(key=lambda x: (x.downloads or 0), reverse=True)
        return items[:top_n]

    def _generate_insights(self, items: List, period: Dict, theme: Dict) -> List[str]:
        """Génère des insights simples"""
        insights = []
        
        if items:
            insights.append(f"{len(items)} documents analysés")
            
            # Dates couvertes
            years = [item.year for item in items if item.year]
            if years:
                insights.append(f"Période couverte: {min(years)}-{max(years)}")
            
            # Sources variées
            sources = set(item.publisher or item.creator for item in items if item.publisher or item.creator)
            if sources:
                insights.append(f"{len(sources)} sources différentes")
        
        insights.append(f"Recherche basée sur {theme.get('keywords_count', 0)} mots-clés du thème")
        
        return insights

    def search_historical_items(self, query: str, period_key: str = None, 
                              theme_id: int = None, max_items: int = 50) -> Tuple[List, Dict]:
        """Recherche simplifiée"""
        try:
            if not self.archive_client:
                return [], {'error': 'Archive client non disponible'}
            
            period = self.historical_periods.get(period_key, {})
            start_year = period.get('start')
            end_year = period.get('end')
            
            archive_data = self.archive_client.search_press_articles(
                query=query,
                start_year=start_year,
                end_year=end_year,
                max_results=max_items
            )
            
            from historical_item import HistoricalItem
            items = [HistoricalItem(data) for data in archive_data]
            
            return items, {
                'items_found': len(archive_data),
                'query': query,
                'period_constraint': f"{start_year}-{end_year}" if start_year and end_year else "Aucune"
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche: {e}")
            return [], {'error': str(e)}

    def get_service_status(self) -> Dict[str, Any]:
        """Statut du service"""
        return {
            'status': 'active',
            'themes_available': True,
            'archive_client': self.archive_client is not None,
            'periods_count': len(self.historical_periods),
            'session_stats': self.session_stats
        }
