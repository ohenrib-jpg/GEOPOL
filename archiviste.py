# Flask/archiviste.py - VERSION OPTIMISÉE v2.2
"""
Module Archiviste - Analyse historique via Archive.org
Avec throttling, cache et gestion d'erreurs robuste
"""

import requests
import logging
import json
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from functools import lru_cache
from .database import DatabaseManager
from .sentiment_analyzer import SentimentAnalyzer
from .theme_analyzer import ThemeAnalyzer

logger = logging.getLogger(__name__)

class Archiviste:
    """
    Archiviste pour l'analyse historique avec rate limiting
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.sentiment_analyzer = SentimentAnalyzer()
        self.theme_analyzer = ThemeAnalyzer(db_manager)
        
        # Rate limiting pour Archive.org
        self.last_request_time = 0
        self.min_request_interval = 2.0  # 2 secondes entre requêtes
        self.max_retries = 3
        self.request_timeout = 30
        
        # Configuration Archive.org
        self.archive_base_url = "https://archive.org/advancedsearch.php"
        
        # Cache des résultats (expire après 1 heure)
        self._cache = {}
        self._cache_expiry = {}
        self.cache_duration = 3600  # 1 heure
        
        # Collections d'archives
        self.collections = [
            {
                'id': 'newspapers',
                'name': 'Archive.org Newspapers',
                'type': 'newspapers',
                'description': 'Collection de journaux historiques'
            },
            {
                'id': 'mags',
                'name': 'Archive.org Magazines',
                'type': 'magazines',
                'description': 'Collection de magazines'
            }
        ]
        
        # Périodes historiques
        self.historical_periods = {
            '1945-1950': {'start': '1945-01-01', 'end': '1950-12-31', 'name': 'Post-guerre'},
            '1950-1960': {'start': '1950-01-01', 'end': '1960-12-31', 'name': 'Guerre froide'},
            '1960-1970': {'start': '1960-01-01', 'end': '1970-12-31', 'name': 'Décolonisation'},
            '1970-1980': {'start': '1970-01-01', 'end': '1980-12-31', 'name': 'Détente'},
            '1980-1990': {'start': '1980-01-01', 'end': '1990-12-31', 'name': 'Tensions'},
            '1990-2000': {'start': '1990-01-01', 'end': '2000-12-31', 'name': 'Nouvel ordre'},
            '2000-2010': {'start': '2000-01-01', 'end': '2010-12-31', 'name': 'Post-11 septembre'},
            '2010-2020': {'start': '2010-01-01', 'end': '2020-12-31', 'name': 'Digitalisation'},
            '2020-2025': {'start': '2020-01-01', 'end': '2025-12-31', 'name': 'Pandémie/IA'}
        }
        
        # Thèmes géopolitiques
        self.historical_themes = {
            'guerre': ['guerre', 'war', 'conflit', 'conflict', 'bataille', 'battle'],
            'diplomatie': ['diplomatie', 'diplomacy', 'négociation', 'negotiation', 'traité', 'treaty'],
            'economie': ['économie', 'economy', 'économique', 'economic', 'marché', 'market'],
            'politique': ['politique', 'politics', 'élection', 'election', 'gouvernement', 'government']
        }
    
    def _throttle_request(self):
        """Applique un délai entre requêtes pour respecter le rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            sleep_time = self.min_request_interval - elapsed
            logger.debug(f"⏳ Throttling: pause de {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _get_cache_key(self, query: str, collection: str, start_date: str, end_date: str) -> str:
        """Génère une clé de cache unique"""
        return f"{collection}:{query}:{start_date}:{end_date}"
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Vérifie si le cache est encore valide"""
        if cache_key not in self._cache_expiry:
            return False
        return time.time() < self._cache_expiry[cache_key]
    
    def search_archive_collection(self, query: str, collection: str = 'newspapers', 
                                start_date: str = None, end_date: str = None,
                                limit: int = 50) -> List[Dict[str, Any]]:
        """
        Recherche dans Archive.org avec cache et rate limiting
        """
        # Vérifier le cache
        cache_key = self._get_cache_key(query, collection, start_date or '', end_date or '')
        if self._is_cache_valid(cache_key):
            logger.info(f"📦 Cache hit pour: {cache_key}")
            return self._cache[cache_key]
        
        # Throttling avant la requête
        self._throttle_request()
        
        # Construction de la requête
        search_query = f'collection:({collection})'
        if query:
            search_query += f' AND (text:"{query}" OR title:"{query}")'
        if start_date and end_date:
            search_query += f' AND date:[{start_date} TO {end_date}]'
        
        params = {
            'q': search_query,
            'fl[]': ['identifier', 'title', 'date', 'description', 'creator', 'subject'],
            'rows': limit,
            'output': 'json',
            'page': 1,
            'sort[]': 'downloads desc'
        }
        
        logger.info(f"🔍 Archive.org: {search_query[:100]}...")
        
        # Tentatives avec retry
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    self.archive_base_url, 
                    params=params, 
                    timeout=self.request_timeout,
                    headers={'User-Agent': 'GEOPOL-Research/2.2'}
                )
                response.raise_for_status()
                
                data = response.json()
                items = data.get('response', {}).get('docs', [])
                
                # Mise en cache
                self._cache[cache_key] = items
                self._cache_expiry[cache_key] = time.time() + self.cache_duration
                
                logger.info(f"✅ Archive.org: {len(items)} items trouvés")
                return items
                
            except requests.Timeout:
                logger.warning(f"⏱️ Timeout tentative {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Backoff exponentiel
            except requests.RequestException as e:
                logger.error(f"❌ Erreur Archive.org (tentative {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"❌ Erreur inattendue: {e}")
                break
        
        logger.error("❌ Échec après toutes les tentatives")
        return []
    
    def extract_text_from_archive(self, item: Dict[str, Any]) -> str:
        """
        Extrait le texte d'un item avec gestion d'erreurs robuste
        """
        try:
            identifier = item.get('identifier')
            if not identifier:
                return ""
            
            # Fallback sur métadonnées
            description = item.get('description', '')
            title = item.get('title', '')
            subject = ' '.join(item.get('subject', [])) if isinstance(item.get('subject'), list) else ''
            
            combined_text = f"{title} {description} {subject}".strip()
            return combined_text[:5000]  # Limite de sécurité
            
        except Exception as e:
            logger.debug(f"Erreur extraction texte: {e}")
            return item.get('title', '') or item.get('description', '')
    
    def analyze_historical_content(self, text: str, year: int) -> Dict[str, Any]:
        """
        Analyse le contenu historique avec gestion d'erreurs
        """
        if not text or len(text) < 50:
            return self._get_default_analysis(year)
        
        try:
            # Analyse de sentiment
            sentiment = self.sentiment_analyzer.analyze_sentiment(text)
            
            # Analyse thématique
            themes = self.theme_analyzer.analyze_article(text, text[:100])
            
            # Détection d'événements majeurs
            major_events = self.detect_major_events(text, year)
            
            return {
                'sentiment_score': sentiment.get('score', 0.0),
                'sentiment_type': sentiment.get('type', 'neutral'),
                'sentiment_confidence': sentiment.get('confidence', 0.0),
                'themes': themes,
                'major_events': major_events,
                'word_count': len(text.split()),
                'year': year
            }
            
        except Exception as e:
            logger.debug(f"Erreur analyse contenu: {e}")
            return self._get_default_analysis(year)
    
    def _get_default_analysis(self, year: int) -> Dict[str, Any]:
        """Retourne une analyse par défaut en cas d'erreur"""
        return {
            'sentiment_score': 0.0,
            'sentiment_type': 'neutral',
            'sentiment_confidence': 0.0,
            'themes': {},
            'major_events': [],
            'word_count': 0,
            'year': year
        }
    
    def detect_major_events(self, text: str, year: int) -> List[str]:
        """
        Détecte les événements majeurs mentionnés
        """
        events = []
        text_lower = text.lower()
        
        # Mapping événements par année (extrait simplifié)
        major_events_map = {
            1945: ['hiroshima', 'nagasaki', 'nations unies'],
            1961: ['mur de berlin', 'kennedy'],
            1989: ['chute mur berlin', 'tiananmen'],
            2001: ['11 septembre', 'world trade center'],
            # ... ajouter plus d'événements selon besoins
        }
        
        if year in major_events_map:
            for event in major_events_map[year]:
                if event in text_lower:
                    events.append(event)
        
        return events[:5]
    
    def analyze_historical_period(self, period_key: str, theme: str = None, 
                                max_items: int = 100) -> Dict[str, Any]:
        """
        Analyse une période historique avec optimisations
        """
        try:
            if period_key not in self.historical_periods:
                return {
                    'success': False,
                    'error': f'Période inconnue: {period_key}',
                    'available_periods': list(self.historical_periods.keys())
                }
            
            period = self.historical_periods[period_key]
            start_date = period['start']
            end_date = period['end']
            
            logger.info(f"📚 Analyse: {period['name']} ({start_date} à {end_date})")
            
            # Construction de la requête
            if theme and theme in self.historical_themes:
                keywords = ' OR '.join(self.historical_themes[theme][:5])  # Limite mots-clés
                search_query = f'({keywords})'
            else:
                search_query = 'geopolitics OR international OR history'
            
            # Recherche dans les archives
            items = self.search_archive_collection(
                query=search_query,
                collection='newspapers',
                start_date=start_date,
                end_date=end_date,
                limit=max_items
            )
            
            if not items:
                return {
                    'success': False,
                    'error': f'Aucun contenu trouvé pour {period_key}',
                    'period': period,
                    'theme': theme
                }
            
            # Analyse du contenu
            analyzed_items = []
            for i, item in enumerate(items[:max_items]):
                try:
                    text = self.extract_text_from_archive(item)
                    if text:
                        year = int(start_date[:4])
                        analysis = self.analyze_historical_content(text, year)
                        enriched_item = {
                            **item,
                            **analysis,
                            'period': period['name']
                        }
                        analyzed_items.append(enriched_item)
                except Exception as e:
                    logger.debug(f"Erreur item {i}: {e}")
                    continue
            
            if not analyzed_items:
                return {
                    'success': False,
                    'error': 'Impossible d\'analyser les items récupérés',
                    'period': period
                }
            
            # Statistiques
            period_stats = self._calculate_period_statistics(analyzed_items, period_key)
            main_trends = self._extract_main_trends(analyzed_items, theme)
            
            result = {
                'success': True,
                'period': period,
                'theme': theme,
                'items_analyzed': len(analyzed_items),
                'statistics': period_stats,
                'main_trends': main_trends,
                'top_items': analyzed_items[:10]
            }
            
            # Sauvegarde
            self._save_historical_analysis(result)
            
            logger.info(f"✅ Analyse complète: {len(analyzed_items)} items pour {period['name']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse période: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_period_statistics(self, items: List[Dict], period_key: str) -> Dict[str, Any]:
        """
        Calcule les statistiques d'une période avec validation
        """
        if not items:
            return {}
        
        sentiment_dist = {'positive': 0, 'negative': 0, 'neutral': 0}
        total_sentiment_score = 0
        total_confidence = 0
        theme_counts = {}
        all_major_events = []
        
        for item in items:
            sentiment_type = item.get('sentiment_type', 'neutral')
            sentiment_dist[sentiment_type] = sentiment_dist.get(sentiment_type, 0) + 1
            
            total_sentiment_score += item.get('sentiment_score', 0)
            total_confidence += item.get('sentiment_confidence', 0)
            
            for theme_id in item.get('themes', {}):
                theme_counts[theme_id] = theme_counts.get(theme_id, 0) + 1
            
            all_major_events.extend(item.get('major_events', []))
        
        avg_sentiment = total_sentiment_score / len(items)
        avg_confidence = total_confidence / len(items) if items else 0
        
        top_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        event_freq = {}
        for event in all_major_events:
            event_freq[event] = event_freq.get(event, 0) + 1
        
        top_events = sorted(event_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'total_items': len(items),
            'period_key': period_key,
            'sentiment_distribution': {
                'positive': sentiment_dist['positive'],
                'negative': sentiment_dist['negative'],
                'neutral': sentiment_dist['neutral'],
                'positive_percent': round(sentiment_dist['positive'] / len(items) * 100, 1),
                'negative_percent': round(sentiment_dist['negative'] / len(items) * 100, 1),
                'neutral_percent': round(sentiment_dist['neutral'] / len(items) * 100, 1)
            },
            'average_sentiment_score': round(avg_sentiment, 4),
            'average_confidence': round(avg_confidence, 4),
            'top_themes': top_themes,
            'top_major_events': top_events,
            'emotional_intensity': self._calculate_emotional_intensity(sentiment_dist, avg_sentiment)
        }
    
    def _calculate_emotional_intensity(self, sentiment_dist: Dict, avg_score: float) -> str:
        """Calcule l'intensité émotionnelle"""
        total = sum(sentiment_dist.values())
        if total == 0:
            return "neutral"
        
        emotional_ratio = (sentiment_dist['positive'] + sentiment_dist['negative']) / total
        score_magnitude = abs(avg_score)
        
        if emotional_ratio > 0.7 and score_magnitude > 0.3:
            return "highly_emotional"
        elif emotional_ratio > 0.5 and score_magnitude > 0.2:
            return "moderately_emotional"
        elif emotional_ratio > 0.3 and score_magnitude > 0.1:
            return "slightly_emotional"
        else:
            return "neutral"
    
    def _extract_main_trends(self, items: List[Dict], theme: str = None) -> List[Dict[str, Any]]:
        """Extrait les tendances principales"""
        trends = []
        
        content_types = {}
        languages = {}
        
        for item in items:
            item_type = item.get('type', 'unknown')
            content_types[item_type] = content_types.get(item_type, 0) + 1
            
            language = item.get('language', 'unknown')
            languages[language] = languages.get(language, 0) + 1
        
        if content_types:
            dominant_type = max(content_types.items(), key=lambda x: x[1])
            trends.append({
                'type': 'content_type',
                'description': f"Contenu principalement {dominant_type[0]}",
                'value': dominant_type[1],
                'percentage': round(dominant_type[1] / len(items) * 100, 1)
            })
        
        return trends
    
    def _save_historical_analysis(self, analysis: Dict[str, Any]):
        """Sauvegarde l'analyse historique"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS historical_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_key TEXT,
                    period_name TEXT,
                    theme TEXT,
                    total_items INTEGER,
                    avg_sentiment_score REAL,
                    emotional_intensity TEXT,
                    top_themes TEXT,
                    top_events TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                INSERT INTO historical_analyses 
                (period_key, period_name, theme, total_items, avg_sentiment_score, 
                 emotional_intensity, top_themes, top_events)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                analysis['period'].get('key', ''),
                analysis['period'].get('name', ''),
                analysis.get('theme', ''),
                analysis.get('items_analyzed', 0),
                analysis.get('statistics', {}).get('average_sentiment_score', 0),
                analysis.get('statistics', {}).get('emotional_intensity', ''),
                str(analysis.get('statistics', {}).get('top_themes', [])),
                str(analysis.get('statistics', {}).get('top_major_events', []))
            ))
            
            conn.commit()
            logger.debug("💾 Analyse historique sauvegardée")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def compare_current_vs_historical(self, current_analysis: Dict, 
                                     historical_periods: List[str] = None) -> Dict[str, Any]:
        """Compare l'analyse actuelle avec les périodes historiques"""
        try:
            if historical_periods is None:
                historical_periods = ['1990-2000', '2000-2010', '2010-2020', '2020-2025']
            
            comparisons = []
            
            for period_key in historical_periods:
                historical = self.analyze_historical_period(period_key)
                
                if not historical.get('success'):
                    continue
                
                comparison = self._compare_periods(current_analysis, historical, period_key)
                comparisons.append(comparison)
            
            synthesis = self._synthesize_comparisons(comparisons)
            
            return {
                'success': True,
                'current_analysis': current_analysis,
                'comparisons': comparisons,
                'synthesis': synthesis,
                'historical_periods_analyzed': len(comparisons)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur comparaison: {e}")
            return {'success': False, 'error': str(e)}
    
    def _compare_periods(self, current: Dict, historical: Dict, period_key: str) -> Dict[str, Any]:
        """Compare deux périodes"""
        try:
            current_stats = current.get('statistics', {})
            historical_stats = historical.get('statistics', {})
            
            current_sentiment = current_stats.get('average_sentiment_score', 0)
            historical_sentiment = historical_stats.get('average_sentiment_score', 0)
            sentiment_diff = current_sentiment - historical_sentiment
            
            evolution_type = self._classify_evolution(
                sentiment_diff,
                current_stats.get('emotional_intensity', 'neutral'),
                historical_stats.get('emotional_intensity', 'neutral')
            )
            
            return {
                'period_key': period_key,
                'period_name': historical_stats.get('period_key', period_key),
                'sentiment_comparison': {
                    'current': current_sentiment,
                    'historical': historical_sentiment,
                    'difference': round(sentiment_diff, 4),
                    'interpretation': self._interpret_sentiment_change(sentiment_diff)
                },
                'evolution_type': evolution_type,
                'similarity_score': self._calculate_similarity_score(current_stats, historical_stats)
            }
            
        except Exception as e:
            logger.error(f"Erreur comparaison: {e}")
            return {'period_key': period_key, 'error': str(e)}
    
    def _classify_evolution(self, sentiment_diff: float, current_intensity: str, 
                          historical_intensity: str) -> str:
        """Classifie le type d'évolution"""
        if abs(sentiment_diff) > 0.3:
            return "major_shift"
        elif abs(sentiment_diff) > 0.15:
            return "moderate_change"
        elif current_intensity != historical_intensity:
            return "intensity_change"
        else:
            return "stable"
    
    def _interpret_sentiment_change(self, sentiment_diff: float) -> str:
        """Interprète le changement de sentiment"""
        if sentiment_diff > 0.3:
            return "Sentiment notablement plus positif"
        elif sentiment_diff > 0.15:
            return "Sentiment légèrement plus positif"
        elif sentiment_diff < -0.3:
            return "Sentiment notablement plus négatif"
        elif sentiment_diff < -0.15:
            return "Sentiment légèrement plus négatif"
        else:
            return "Sentiment similaire"
    
    def _calculate_similarity_score(self, current_stats: Dict, historical_stats: Dict) -> float:
        """Calcule un score de similarité"""
        try:
            current_dist = current_stats.get('sentiment_distribution', {})
            historical_dist = historical_stats.get('sentiment_distribution', {})
            
            sentiment_diff = (
                abs(current_dist.get('positive_percent', 0) - historical_dist.get('positive_percent', 0)) +
                abs(current_dist.get('negative_percent', 0) - historical_dist.get('negative_percent', 0)) +
                abs(current_dist.get('neutral_percent', 0) - historical_dist.get('neutral_percent', 0))
            ) / 3
            
            similarity_score = 1 - (sentiment_diff / 100)
            return round(max(0, min(1, similarity_score)), 3)
            
        except Exception as e:
            logger.debug(f"Erreur calcul similarité: {e}")
            return 0.0
    
    def _synthesize_comparisons(self, comparisons: List[Dict]) -> Dict[str, Any]:
        """Synthétise les comparaisons multiples"""
        if not comparisons:
            return {}
        
        evolution_counts = {}
        total_similarity = 0
        
        for comp in comparisons:
            evolution_type = comp.get('evolution_type', 'unknown')
            evolution_counts[evolution_type] = evolution_counts.get(evolution_type, 0) + 1
            total_similarity += comp.get('similarity_score', 0)
        
        dominant_evolution = max(evolution_counts.items(), key=lambda x: x[1])[0] if evolution_counts else 'unknown'
        avg_similarity = total_similarity / len(comparisons) if comparisons else 0
        
        return {
            'dominant_evolution_pattern': dominant_evolution,
            'average_similarity_score': round(avg_similarity, 3),
            'evolution_distribution': evolution_counts,
            'periods_analyzed': len(comparisons),
            'interpretation': f"Analyse comparative sur {len(comparisons)} périodes historiques"
        }


# Instance globale
_archiviste = None

def get_archiviste(db_manager: DatabaseManager) -> Archiviste:
    """Retourne l'instance singleton de l'archiviste"""
    global _archiviste
    if _archiviste is None:
        _archiviste = Archiviste(db_manager)
        logger.info("✅ Archiviste initialisé avec throttling et cache")
    return _archiviste
