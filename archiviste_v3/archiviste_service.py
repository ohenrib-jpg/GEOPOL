"""
ArchivisteServiceImproved - VERSION AVEC GALLICA FONCTIONNEL
"""

import logging
import json
import time
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

class ArchivisteServiceImproved:
    """Service complet avec Archive.org + Gallica + support futurs sources"""
    
    def __init__(self, db_manager, sentiment_analyzer=None, gallica_client=None, wayback_client=None):
        self.db_manager = db_manager
        self.sentiment_analyzer = sentiment_analyzer
        self.gallica_client = gallica_client
        self.wayback_client = wayback_client  # 🆕 Wayback Machine
        
        print("\n" + "="*70)
        print("🚀 ARCHIVISTE v3.2 - INITIALISATION")
        print("="*70)
        
        # Clients
        try:
            from archive_client import ArchiveOrgClient
            self.archive_client = ArchiveOrgClient()
            print("✅ Archive.org client initialisé")
        except ImportError as e:
            print(f"❌ Archive.org client: {e}")
            self.archive_client = None
        
        # Vérifier Gallica
        if self.gallica_client:
            try:
                if self.gallica_client.test_connection():
                    print("✅ Gallica BnF client initialisé et testé")
                else:
                    print("⚠️ Gallica client créé mais connexion échouée")
            except Exception as e:
                print(f"⚠️ Gallica test échoué: {e}")
        else:
            print("ℹ️ Gallica client non fourni")
        
        # 🆕 Vérifier Wayback Machine
        if self.wayback_client:
            try:
                if self.wayback_client.test_connection():
                    print("✅ Wayback Machine client initialisé et testé")
                else:
                    print("⚠️ Wayback client créé mais connexion échouée")
            except Exception as e:
                print(f"⚠️ Wayback test échoué: {e}")
        else:
            print("ℹ️ Wayback client non fourni")
        
        # Base de données
        try:
            from archiviste_database import ArchivisteDatabase
            self.database = ArchivisteDatabase(db_manager)
            print("✅ Database Archiviste initialisée")
        except ImportError as e:
            print(f"❌ Database: {e}")
            self.database = None
        
        # Périodes historiques
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
        
        self.session_stats = {
            'searches': 0, 
            'items_analyzed': 0,
            'errors': 0,
            'archive_org_searches': 0,
            'gallica_searches': 0,
            'wayback_searches': 0  # 🆕 Wayback Machine
        }
        
        # Récapitulatif
        sources_available = []
        if self.archive_client:
            sources_available.append("Archive.org")
        if self.gallica_client:
            sources_available.append("Gallica BnF")
        if self.wayback_client:  # 🆕
            sources_available.append("Wayback Machine")
        
        print(f"\n📚 Sources disponibles: {', '.join(sources_available) if sources_available else 'Aucune'}")
        print("="*70 + "\n")
    
    def get_theme_info(self, theme_id: int) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un thème"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, color, description 
                FROM themes 
                WHERE id = ?
            """, (theme_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'color': row[2] or '#6366f1',
                    'description': row[3] or ''
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur thème {theme_id}: {e}")
            return None
    
    def get_theme_by_name(self, theme_name: str) -> Optional[Dict[str, Any]]:
        """Récupère un thème par son nom"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, color, description 
                FROM themes 
                WHERE LOWER(name) = LOWER(?)
            """, (theme_name,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'color': row[2] or '#6366f1',
                    'description': row[3] or ''
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur thème par nom {theme_name}: {e}")
            return None
    
    def get_theme_keywords(self, theme_id: int) -> List[str]:
        """Récupère les mots-clés d'un thème"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT keywords FROM themes WHERE id = ?", (theme_id,))
            row = cursor.fetchone()
            conn.close()
            
            if not row or not row[0]:
                return []
            
            keywords_data = row[0]
            keywords = []
            
            if isinstance(keywords_data, list):
                keywords = [str(k).strip() for k in keywords_data if k]
            elif isinstance(keywords_data, str):
                try:
                    parsed = json.loads(keywords_data)
                    if isinstance(parsed, list):
                        keywords = [str(k).strip() for k in parsed if k]
                    else:
                        keywords = [k.strip() for k in keywords_data.split(',') if k.strip()]
                except:
                    keywords = [k.strip() for k in keywords_data.split(',') if k.strip()]
            
            return keywords
            
        except Exception as e:
            logger.error(f"❌ Erreur mots-clés thème {theme_id}: {e}")
            return ['histoire', 'géopolitique']
    
    def analyze_period_with_theme(self, period_key: str, theme_id: int, max_items: int = 50):
        """Analyse principale avec sources multiples (Archive.org + Gallica)"""
        start_time = time.time()
        
        try:
            # Vérification période
            if period_key not in self.historical_periods:
                return {'success': False, 'error': f'Période inconnue: {period_key}'}
            
            period = self.historical_periods[period_key]
            
            # Vérification thème
            if isinstance(theme_id, str) and not theme_id.isdigit():
                theme_info = self.get_theme_by_name(theme_id)
                if not theme_info:
                    return {'success': False, 'error': f'Thème invalide: {theme_id}'}
                theme_id = theme_info['id']
            else:
                theme_info = self.get_theme_info(int(theme_id))
                if not theme_info:
                    return {'success': False, 'error': f'Thème {theme_id} non trouvé'}
            
            print(f"\n🎯 ANALYSE: {theme_info['name']} ({period['name']})")
            print(f"   Période: {period['start']}-{period['end']}")
            
            # Mots-clés
            keywords = self.get_theme_keywords(theme_id)
            search_query = ' OR '.join([f'"{kw}"' for kw in keywords[:5]])
            print(f"🔑 Mots-clés: {keywords[:5]}")
            
            # RÉCUPÉRATION DES SOURCES
            print(f"\n🔍 Lancement des recherches...")
            all_items = []
            source_stats = {}
            
            # 1. Archive.org
            if self.archive_client:
                print("1️⃣ Interrogation Archive.org...")
                try:
                    archive_items = self.archive_client.search_french_press(
                        query=search_query,
                        start_year=period['start'],
                        end_year=period['end'],
                        max_results=max_items // 2
                    )
                    source_stats['archive.org'] = len(archive_items)
                    all_items.extend([{**item, 'source': 'archive.org'} for item in archive_items])
                    print(f"   ✅ {len(archive_items)} résultats Archive.org")
                except Exception as e:
                    logger.error(f"   ❌ Erreur Archive.org: {e}")
                    source_stats['archive.org'] = 0
            
            # 2. Gallica (si disponible)
            if self.gallica_client:
                print("2️⃣ Interrogation Gallica BnF...")
                try:
                    # Déterminer le type de document selon la période
                    doc_type = 'press' if period['end'] <= 1954 else 'monograph'
                    
                    gallica_items = self.gallica_client.search(
                        query=search_query,
                        start_year=period['start'],
                        end_year=period['end'],
                        max_results=max_items // 3,
                        doc_type=doc_type
                    )
                    source_stats['gallica'] = len(gallica_items)
                    all_items.extend([{**item, 'source': 'gallica'} for item in gallica_items])
                    print(f"   ✅ {len(gallica_items)} résultats Gallica")
                    
                    self.session_stats['gallica_searches'] += 1
                except Exception as e:
                    logger.error(f"   ❌ Erreur Gallica: {e}")
                    source_stats['gallica'] = 0
            
            # 🆕 3. Wayback Machine (si disponible)
            if self.wayback_client:
                print("3️⃣ Interrogation Wayback Machine...")
                try:
                    # Adapter la stratégie selon la période
                    if period['end'] < 1996:
                        # Wayback n'existait pas avant 1996
                        print("   ⚠️ Période antérieure à 1996 - Wayback non applicable")
                        wayback_items = []
                    elif period['start'] < 2000:
                        # Peu de sites avant 2000
                        print("   📡 Période 1996-2000 - Recherche ciblée")
                        wayback_items = self.wayback_client.search(
                            query=search_query,
                            start_year=max(period['start'], 1996),
                            end_year=period['end'],
                            max_results=max_items // 4,
                            sites=['lemonde.fr', 'liberation.fr']
                        )
                    else:
                        # Après 2000: recherche complète
                        print("   📡 Période post-2000 - Recherche complète")
                        wayback_items = self.wayback_client.search(
                            query=search_query,
                            start_year=period['start'],
                            end_year=period['end'],
                            max_results=max_items // 3
                        )
                    
                    source_stats['wayback'] = len(wayback_items)
                    all_items.extend([{**item, 'source': 'wayback'} for item in wayback_items])
                    print(f"   ✅ {len(wayback_items)} archives web Wayback")
                    
                    self.session_stats['wayback_searches'] += 1
                    
                except Exception as e:
                    logger.error(f"   ❌ Erreur Wayback: {e}")
                    source_stats['wayback'] = 0
            
            total_items = len(all_items)
            print(f"\n📊 FUSION: {total_items} items totaux")
            for source, count in source_stats.items():
                print(f"   • {source}: {count}")
            
            if total_items == 0:
                return {
                    'success': True,
                    'period': {'key': period_key, 'name': period['name']},
                    'theme': theme_info,
                    'items_analyzed': 0,
                    'key_items': [],
                    'insights': ['❌ Aucun document trouvé pour cette période et ce thème'],
                    'search_metadata': {'keywords': keywords},
                    'sources_used': list(source_stats.keys()),
                    'source_stats': source_stats
                }
            
            # Items clés (tri par pertinence)
            key_items = self._rank_items(all_items, keywords)[:min(10, len(all_items))]
            
            # Insights
            insights = self._generate_insights(all_items, theme_info, period, source_stats)
            
            # Sauvegarde session
            search_duration = time.time() - start_time
            if self.database:
                try:
                    self.database.save_search_session(
                        period_key=period_key,
                        theme_id=theme_id,
                        search_query=search_query,
                        total_found=total_items,
                        new_added=0,
                        cached_used=0,
                        duration=search_duration
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Erreur sauvegarde session: {e}")
            
            # Mise à jour stats
            self.session_stats['searches'] += 1
            self.session_stats['items_analyzed'] += total_items
            if 'archive.org' in source_stats:
                self.session_stats['archive_org_searches'] += 1
            
            result = {
                'success': True,
                'period': {'key': period_key, 'name': period['name']},
                'theme': theme_info,
                'items_analyzed': total_items,
                'key_items': key_items,
                'insights': insights,
                'search_metadata': {
                    'keywords': keywords,
                    'duration': round(search_duration, 2),
                    'sources_used': list(source_stats.keys())
                },
                'source_stats': source_stats,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"\n✅ Analyse réussie en {search_duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse: {e}", exc_info=True)
            self.session_stats['errors'] += 1
            return {'success': False, 'error': str(e)}
    
    def _rank_items(self, items: List[Dict], keywords: List[str]) -> List[Dict]:
        """Trie les items par pertinence avec bonus source"""
        scored = []
        for item in items:
            score = 0.0
            
            # Bonus par source
            source = item.get('source', 'unknown')
            if source == 'gallica':
                score += 0.3  # Gallica = source premium
            elif source == 'archive.org':
                score += 0.2
            
            # Score de mots-clés
            content = f"{item.get('title', '')} {item.get('description', '')}".lower()
            keyword_matches = sum(1 for kw in keywords if kw.lower() in content)
            score += min(keyword_matches / max(len(keywords), 1), 1.0) * 0.5
            
            # Score de qualité
            if 'quality_score' in item:
                score += item['quality_score'] * 0.2
            
            scored.append((item, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored]
    
    def _generate_insights(
        self, 
        items: List[Dict], 
        theme_info: Dict, 
        period: Dict, 
        source_stats: Dict
    ) -> List[str]:
        """Génère des insights sur l'analyse"""
        insights = []
        
        insights.append(f"📊 {len(items)} documents analysés")
        
        # Sources utilisées
        if source_stats:
            sources_str = ', '.join([f"{s} ({c})" for s, c in source_stats.items()])
            insights.append(f"🔍 Sources: {sources_str}")
        
        # Répartition par source
        source_counts = {}
        for item in items:
            source = item.get('source', 'inconnu')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        for source, count in source_counts.items():
            pct = round(count / len(items) * 100, 1)
            insights.append(f"   • {source}: {count} documents ({pct}%)")
        
        # Années couvertes
        years = [item.get('year', 0) for item in items if item.get('year')]
        if years:
            min_year = min(years)
            max_year = max(years)
            if min_year != max_year:
                insights.append(f"📅 Couverture: {min_year}-{max_year}")
            else:
                insights.append(f"📅 Année: {min_year}")
        
        # Qualité globale
        quality_scores = [item.get('quality_score', 0.5) for item in items]
        avg_quality = sum(quality_scores) / len(quality_scores)
        insights.append(f"⭐ Qualité moyenne: {avg_quality:.1%}")
        
        return insights
    
    # Méthodes utilitaires
    def get_available_periods(self):
        return self.historical_periods
    
    def get_service_status(self):
        return {
            'status': 'active',
            'sources': {
                'archive.org': self.archive_client is not None,
                'gallica': self.gallica_client is not None
            },
            'session_stats': self.session_stats
        }
    
    def get_search_history(self, limit=20):
        if self.database:
            return self.database.get_search_history(limit)
        return []