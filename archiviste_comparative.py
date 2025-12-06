# Flask/archiviste_comparative.py
"""
Module Archiviste amélioré avec analyse comparative réelle des sentiments
Utilise l'API Archive.org pour récupérer et analyser des documents historiques
"""

import logging
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import Counter
import re

logger = logging.getLogger(__name__)


class ArchiveOrgClient:
    """Client pour interagir avec l'API Archive.org"""
    
    BASE_URL = "https://archive.org"
    SEARCH_URL = f"{BASE_URL}/advancedsearch.php"
    METADATA_URL = f"{BASE_URL}/metadata"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GeoPolAnalyzer/1.0 (Educational Research)'
        })
    
    def search_by_period_and_keywords(
        self, 
        keywords: List[str], 
        start_year: int, 
        end_year: int,
        collections: List[str] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Recherche dans Archive.org par période et mots-clés
        
        Args:
            keywords: Liste de mots-clés du thème
            start_year: Année de début
            end_year: Année de fin
            collections: Collections spécifiques (newspapers, texts, etc.)
            max_results: Nombre max de résultats
        
        Returns:
            Liste de documents avec métadonnées enrichies
        """
        try:
            # Construire la requête de recherche
            keyword_query = ' OR '.join([f'"{kw}"' for kw in keywords[:5]])
            
            # Collections par défaut pour contenus textuels
            if not collections:
                collections = ['texts', 'opensource', 'gutenberg']
            
            collection_query = ' OR '.join([f'collection:{c}' for c in collections])
            
            # Requête complète
            query = f"({keyword_query}) AND ({collection_query}) AND year:[{start_year} TO {end_year}]"
            
            params = {
                'q': query,
                'fl': 'identifier,title,description,date,year,creator,subject,downloads,language',
                'rows': max_results,
                'output': 'json',
                'sort': 'downloads desc'  # Prioriser les documents populaires
            }
            
            logger.info(f"🔍 Recherche Archive.org: {keyword_query} ({start_year}-{end_year})")
            
            response = self.session.get(self.SEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            docs = data.get('response', {}).get('docs', [])
            
            logger.info(f"✅ {len(docs)} documents trouvés sur Archive.org")
            
            return docs
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche Archive.org: {e}")
            return []
    
    def get_item_metadata(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Récupère les métadonnées complètes d'un item"""
        try:
            url = f"{self.METADATA_URL}/{identifier}"
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ Erreur métadonnées {identifier}: {e}")
            return None
    
    def extract_text_content(self, item: Dict[str, Any]) -> str:
        """
        Extrait le contenu textuel disponible d'un item
        (métadonnées uniquement pour limiter la charge)
        """
        text_parts = []
        
        # Titre
        if item.get('title'):
            text_parts.append(str(item['title']))
        
        # Description (souvent riche en contenu)
        if item.get('description'):
            desc = item['description']
            if isinstance(desc, list):
                text_parts.extend([str(d) for d in desc])
            else:
                text_parts.append(str(desc))
        
        # Sujets/thématiques
        if item.get('subject'):
            subjects = item['subject']
            if isinstance(subjects, list):
                text_parts.extend([str(s) for s in subjects])
            else:
                text_parts.append(str(subjects))
        
        # Créateur (peut contenir des infos contextuelles)
        if item.get('creator'):
            text_parts.append(str(item['creator']))
        
        return ' '.join(text_parts)


class ComparativeSentimentAnalyzer:
    """
    Analyseur de sentiments adapté pour l'analyse historique comparative
    Utilise le même modèle RoBERTa mais en mode allégé
    """
    
    def __init__(self, sentiment_analyzer):
        """
        Args:
            sentiment_analyzer: Instance du SentimentAnalyzer principal
        """
        self.sentiment_analyzer = sentiment_analyzer
        self.cache = {}  # Cache simple pour éviter réanalyses
    
    def analyze_historical_text(self, text: str, item_id: str = None) -> Dict[str, Any]:
        """
        Analyse le sentiment d'un texte historique
        Version allégée pour traiter plus de documents
        """
        if not text or len(text.strip()) < 20:
            return {
                'sentiment_type': 'neutral',
                'sentiment_score': 0.0,
                'confidence': 0.0,
                'processed': False
            }
        
        # Vérifier le cache
        cache_key = f"{item_id}_{hash(text[:500])}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Tronquer le texte pour performances (garder début et fin)
            if len(text) > 1000:
                text = text[:700] + " [...] " + text[-300:]
            
            # Utiliser l'analyseur principal
            result = self.sentiment_analyzer.analyze_sentiment(text)
            
            analysis = {
                'sentiment_type': result.get('sentiment_type', 'neutral'),
                'sentiment_score': result.get('sentiment_score', 0.0),
                'confidence': result.get('roberta_score', 0.5),
                'processed': True
            }
            
            # Mettre en cache
            self.cache[cache_key] = analysis
            
            return analysis
            
        except Exception as e:
            logger.debug(f"Erreur analyse historique: {e}")
            return {
                'sentiment_type': 'neutral',
                'sentiment_score': 0.0,
                'confidence': 0.0,
                'processed': False,
                'error': str(e)
            }
    
    def batch_analyze_items(
        self, 
        items: List[Dict[str, Any]], 
        theme_keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Analyse par lot des items historiques
        Optimisé pour traiter plusieurs documents rapidement
        """
        analyzed_items = []
        
        for i, item in enumerate(items):
            # Log de progression tous les 10 items
            if i % 10 == 0:
                logger.info(f"📊 Analyse {i}/{len(items)} items...")
            
            # Extraire le texte
            text = self._extract_text_from_item(item)
            
            # Calculer la pertinence thématique
            relevance = self._calculate_theme_relevance(text, theme_keywords)
            
            # Ne garder que les items pertinents (seuil bas)
            if relevance < 0.05:  # Au moins 5% de mots-clés présents
                continue
            
            # Analyser le sentiment
            sentiment = self.analyze_historical_text(
                text, 
                item_id=item.get('identifier')
            )
            
            # Enrichir l'item
            analyzed_item = {
                **item,
                'text_extract': text[:500],  # Extrait pour référence
                'word_count': len(text.split()),
                'theme_relevance': relevance,
                'sentiment_analysis': sentiment,
                'matched_keywords': self._find_matching_keywords(text, theme_keywords)
            }
            
            analyzed_items.append(analyzed_item)
        
        logger.info(f"✅ {len(analyzed_items)} items analysés et pertinents")
        
        return analyzed_items
    
    def _extract_text_from_item(self, item: Dict[str, Any]) -> str:
        """Extrait le texte d'un item Archive.org"""
        text_parts = []
        
        for field in ['title', 'description', 'subject', 'creator']:
            value = item.get(field)
            if value:
                if isinstance(value, list):
                    text_parts.extend([str(v) for v in value])
                else:
                    text_parts.append(str(value))
        
        return ' '.join(text_parts)
    
    def _calculate_theme_relevance(self, text: str, keywords: List[str]) -> float:
        """Calcule la pertinence d'un texte par rapport aux mots-clés"""
        if not text or not keywords:
            return 0.0
        
        text_lower = text.lower()
        matches = sum(1 for kw in keywords if kw.lower() in text_lower)
        
        return matches / len(keywords)
    
    def _find_matching_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Trouve les mots-clés présents dans le texte"""
        text_lower = text.lower()
        return [kw for kw in keywords if kw.lower() in text_lower]


class ComparativeArchiviste:
    """
    Archiviste avec capacités d'analyse comparative réelle
    """
    
    def __init__(self, db_manager, sentiment_analyzer):
        self.db_manager = db_manager
        self.archive_client = ArchiveOrgClient()
        self.comparative_analyzer = ComparativeSentimentAnalyzer(sentiment_analyzer)
        
        # Périodes historiques
        self.historical_periods = {
            '1945-1950': {'start': 1945, 'end': 1950, 'name': 'Après-guerre (1945-1950)'},
            '1950-1960': {'start': 1950, 'end': 1960, 'name': 'Guerre froide débuts (1950-1960)'},
            '1960-1970': {'start': 1960, 'end': 1970, 'name': 'Décolonisation (1960-1970)'},
            '1970-1980': {'start': 1970, 'end': 1980, 'name': 'Détente (1970-1980)'},
            '1980-1990': {'start': 1980, 'end': 1990, 'name': 'Fin guerre froide (1980-1990)'},
            '1990-2000': {'start': 1990, 'end': 2000, 'name': 'Nouvel ordre mondial (1990-2000)'},
            '2000-2010': {'start': 2000, 'end': 2010, 'name': 'Post-11/09 (2000-2010)'},
            '2010-2020': {'start': 2010, 'end': 2020, 'name': 'Printemps arabes/Crise (2010-2020)'},
            '2020-2025': {'start': 2020, 'end': 2025, 'name': 'Pandémie/IA (2020-2025)'}
        }
    
    def analyze_period_with_theme(
        self, 
        period_key: str, 
        theme_id: int,
        max_items: int = 50
    ) -> Dict[str, Any]:
        """
        Analyse comparative d'une période historique avec un thème
        VRAIE recherche et analyse sur Archive.org
        """
        try:
            logger.info(f"🎯 Analyse comparative: période {period_key}, thème {theme_id}")
            
            # Valider la période
            if period_key not in self.historical_periods:
                return {
                    'success': False,
                    'error': f'Période inconnue: {period_key}'
                }
            
            period = self.historical_periods[period_key]
            
            # Récupérer le thème avec mots-clés
            theme = self._get_theme_by_id(theme_id)
            if not theme:
                return {
                    'success': False,
                    'error': f'Thème {theme_id} non trouvé'
                }
            
            logger.info(f"📚 Thème: {theme['name']} ({len(theme['keywords'])} mots-clés)")
            
            # 1. RECHERCHER sur Archive.org
            historical_items = self.archive_client.search_by_period_and_keywords(
                keywords=theme['keywords'],
                start_year=period['start'],
                end_year=period['end'],
                max_results=max_items
            )
            
            if not historical_items:
                return {
                    'success': False,
                    'error': f'Aucun document trouvé sur Archive.org pour cette période/thème',
                    'period': period,
                    'theme': theme
                }
            
            # 2. ANALYSER les sentiments des documents historiques
            analyzed_items = self.comparative_analyzer.batch_analyze_items(
                historical_items,
                theme['keywords']
            )
            
            if not analyzed_items:
                return {
                    'success': False,
                    'error': 'Aucun document pertinent après analyse',
                    'total_found': len(historical_items)
                }
            
            # 3. RÉCUPÉRER les articles actuels pour comparaison
            current_articles = self._get_current_articles_by_theme(theme_id, limit=50)
            
            # 4. CALCULER les statistiques comparatives
            historical_stats = self._calculate_sentiment_statistics(analyzed_items, 'historical')
            current_stats = self._calculate_sentiment_statistics(current_articles, 'current')
            
            # 5. COMPARER les tendances
            comparison = self._compare_sentiment_trends(historical_stats, current_stats)
            
            # 6. IDENTIFIER les changements narratifs
            narrative_shifts = self._identify_narrative_shifts(
                analyzed_items, 
                current_articles,
                theme
            )
            
            result = {
                'success': True,
                'period': period,
                'theme': theme,
                'historical_items_found': len(historical_items),
                'historical_items_analyzed': len(analyzed_items),
                'current_articles_count': len(current_articles),
                'historical_sentiment': historical_stats,
                'current_sentiment': current_stats,
                'comparative_analysis': comparison,
                'narrative_shifts': narrative_shifts,
                'top_historical_items': analyzed_items[:10],
                'timestamp': datetime.now().isoformat()
            }
            
            # Sauvegarder l'analyse
            self._save_comparative_analysis(result)
            
            logger.info(f"✅ Analyse comparative terminée: {len(analyzed_items)} items historiques vs {len(current_articles)} actuels")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse comparative: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Erreur: {str(e)}'
            }
    
    def _get_theme_by_id(self, theme_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un thème depuis la base de données"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, name, keywords, description, color
                FROM themes
                WHERE id = ?
            """, (theme_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            keywords = []
            if row[2]:
                try:
                    keywords = json.loads(row[2])
                except:
                    keywords = [k.strip() for k in str(row[2]).split(',') if k.strip()]
            
            return {
                'id': row[0],
                'name': row[1],
                'keywords': keywords,
                'description': row[3] or '',
                'color': row[4] or '#6366f1'
            }
            
        finally:
            conn.close()
    
    def _get_current_articles_by_theme(self, theme_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les articles actuels pour un thème"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT a.id, a.title, a.content, a.pub_date,
                       a.sentiment_type, a.sentiment_score, a.sentiment_confidence
                FROM articles a
                JOIN theme_analyses ta ON a.id = ta.article_id
                WHERE ta.theme_id = ?
                AND a.pub_date >= DATE('now', '-30 days')
                ORDER BY a.pub_date DESC
                LIMIT ?
            """, (theme_id, limit))
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'sentiment_type': row[4],
                    'sentiment_score': row[5],
                    'confidence': row[6] or 0.5
                })
            
            return articles
            
        finally:
            conn.close()
    
    def _calculate_sentiment_statistics(
        self, 
        items: List[Dict[str, Any]], 
        source_type: str
    ) -> Dict[str, Any]:
        """Calcule les statistiques de sentiment pour un ensemble d'items"""
        
        if not items:
            return {
                'total': 0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0,
                'neutral_ratio': 0.0,
                'average_score': 0.0,
                'average_confidence': 0.0
            }
        
        sentiments = []
        scores = []
        confidences = []
        
        for item in items:
            if source_type == 'historical':
                sent_data = item.get('sentiment_analysis', {})
                sentiment = sent_data.get('sentiment_type', 'neutral')
                score = sent_data.get('sentiment_score', 0.0)
                confidence = sent_data.get('confidence', 0.0)
            else:  # current
                sentiment = item.get('sentiment_type', 'neutral')
                score = item.get('sentiment_score', 0.0)
                confidence = item.get('confidence', 0.5)
            
            sentiments.append(sentiment)
            scores.append(score)
            confidences.append(confidence)
        
        sentiment_counts = Counter(sentiments)
        total = len(sentiments)
        
        return {
            'total': total,
            'positive_count': sentiment_counts.get('positive', 0),
            'negative_count': sentiment_counts.get('negative', 0),
            'neutral_count': sentiment_counts.get('neutral', 0),
            'positive_ratio': sentiment_counts.get('positive', 0) / total,
            'negative_ratio': sentiment_counts.get('negative', 0) / total,
            'neutral_ratio': sentiment_counts.get('neutral', 0) / total,
            'average_score': sum(scores) / len(scores) if scores else 0.0,
            'average_confidence': sum(confidences) / len(confidences) if confidences else 0.0
        }
    
    def _compare_sentiment_trends(
        self, 
        historical: Dict[str, Any], 
        current: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare les tendances de sentiment entre périodes"""
        
        return {
            'positive_evolution': current['positive_ratio'] - historical['positive_ratio'],
            'negative_evolution': current['negative_ratio'] - historical['negative_ratio'],
            'neutral_evolution': current['neutral_ratio'] - historical['neutral_ratio'],
            'score_evolution': current['average_score'] - historical['average_score'],
            'interpretation': self._interpret_sentiment_evolution(historical, current)
        }
    
    def _interpret_sentiment_evolution(
        self, 
        historical: Dict[str, Any], 
        current: Dict[str, Any]
    ) -> str:
        """Génère une interprétation textuelle de l'évolution"""
        
        pos_change = current['positive_ratio'] - historical['positive_ratio']
        neg_change = current['negative_ratio'] - historical['negative_ratio']
        
        if abs(pos_change) < 0.1 and abs(neg_change) < 0.1:
            return "Sentiment relativement stable entre la période historique et aujourd'hui"
        
        if pos_change > 0.15:
            return "Forte augmentation du sentiment positif par rapport à la période historique"
        elif pos_change > 0.05:
            return "Légère amélioration du sentiment positif"
        
        if neg_change > 0.15:
            return "Forte augmentation du sentiment négatif par rapport à la période historique"
        elif neg_change > 0.05:
            return "Légère augmentation du sentiment négatif"
        
        return "Évolution mixte des sentiments"
    
    def _identify_narrative_shifts(
        self,
        historical_items: List[Dict[str, Any]],
        current_articles: List[Dict[str, Any]],
        theme: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identifie les changements dans les récits dominants"""
        
        # Mots-clés les plus fréquents historiquement
        historical_keywords = []
        for item in historical_items:
            historical_keywords.extend(item.get('matched_keywords', []))
        
        hist_keyword_freq = Counter(historical_keywords)
        
        # Mots-clés actuels (à partir des articles)
        current_keywords = []
        for article in current_articles:
            content = (article.get('title', '') + ' ' + article.get('content', '')).lower()
            for kw in theme['keywords']:
                if kw.lower() in content:
                    current_keywords.append(kw)
        
        curr_keyword_freq = Counter(current_keywords)
        
        return {
            'historical_dominant_keywords': hist_keyword_freq.most_common(10),
            'current_dominant_keywords': curr_keyword_freq.most_common(10),
            'emerging_keywords': [kw for kw, _ in curr_keyword_freq.most_common(10) 
                                 if kw not in hist_keyword_freq],
            'declining_keywords': [kw for kw, _ in hist_keyword_freq.most_common(10)
                                  if kw not in curr_keyword_freq]
        }
    
    def _save_comparative_analysis(self, analysis: Dict[str, Any]):
        """Sauvegarde l'analyse comparative dans la base"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO archiviste_period_analyses
                (period_key, period_name, theme_id, total_items, items_analyzed,
                 analysis_summary, raw_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                analysis['period']['start'],  # Utiliser start comme clé
                analysis['period']['name'],
                analysis['theme']['id'],
                analysis.get('historical_items_found', 0),
                analysis.get('historical_items_analyzed', 0),
                json.dumps(analysis['comparative_analysis'], ensure_ascii=False),
                json.dumps(analysis, ensure_ascii=False)
            ))
            
            conn.commit()
            logger.info("✅ Analyse comparative sauvegardée")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde analyse: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_available_themes(self) -> List[Dict[str, Any]]:
        """Retourne tous les thèmes disponibles"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, name, keywords, description, color
                FROM themes
                WHERE active = 1 OR active IS NULL
                ORDER BY name
            """)
            
            themes = []
            for row in cursor.fetchall():
                keywords = []
                if row[2]:
                    try:
                        keywords = json.loads(row[2])
                    except:
                        keywords = [k.strip() for k in str(row[2]).split(',') if k.strip()]
                
                themes.append({
                    'id': row[0],
                    'name': row[1],
                    'keywords': keywords,
                    'description': row[3] or '',
                    'color': row[4] or '#6366f1'
                })
            
            return themes
            
        finally:
            conn.close()
