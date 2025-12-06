# Flask/geo_narrative_analyzer.py - VERSION AMÉLIORÉE

from collections import defaultdict
from datetime import datetime
import re
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class GeoNarrativeAnalyzer:
    """
    Analyseur de narratifs géopolitiques transnationaux.
    Détecte les patterns verbaux communs entre différents pays.
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.verb_patterns_cache = {}
        
        # Verbes français courants pour l'analyse géopolitique
        self.geopolitical_verbs = {
            # Verbes de déclaration
            'déclarer', 'affirmer', 'annoncer', 'préciser', 'souligner',
            'confirmer', 'nier', 'réfuter', 'contester', 'démentir',
            
            # Verbes d'action politique
            'décider', 'voter', 'adopter', 'rejeter', 'approuver',
            'sanctionner', 'interdire', 'autoriser', 'suspendre',
            
            # Verbes de relation internationale
            'négocier', 'coopérer', 's\'allier', 'rompre', 'tensions',
            'accuser', 'critiquer', 'condamner', 'soutenir', 'défendre',
            
            # Verbes d'état/être
            'être', 'avoir', 'devenir', 'rester', 'sembler', 'paraître',
            
            # Formes conjuguées fréquentes
            'est', 'sont', 'a', 'ont', 'fait', 'font', 'dit', 'disent',
            'va', 'vont', 'peut', 'peuvent', 'doit', 'doivent'
        }
    
    # =========================================================================
    # MÉTHODE PRINCIPALE
    # =========================================================================
    
    def detect_transnational_patterns(self, days=7, min_countries=2):
        """
        Détecte les patterns verbaux transnationaux sur une période donnée.
        
        Args:
            days: Nombre de jours à analyser (défaut: 7)
            min_countries: Nombre minimum de pays partageant un pattern (défaut: 2)
            
        Returns:
            Liste de dictionnaires contenant les patterns détectés
        """
        try:
            logger.info(f"🔍 Analyse de patterns transnationaux sur {days} jours...")
            
            # Récupérer les articles groupés par pays
            articles = self._get_recent_articles_by_country(days)
            
            if not articles:
                logger.warning("⚠️ Aucun article trouvé pour l'analyse")
                return []
            
            logger.info(f"📊 {len(articles)} pays détectés: {list(articles.keys())}")
            
            # Analyser les patterns
            patterns = self._analyze_verb_patterns(articles, min_countries)
            
            logger.info(f"✅ {len(patterns)} patterns transnationaux détectés")
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ Erreur détection patterns: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    # =========================================================================
    # ANALYSE DES PATTERNS VERBAUX
    # =========================================================================
    
    def _analyze_verb_patterns(self, articles_by_country: Dict[str, List], min_countries: int) -> List[Dict]:
        """
        Cœur algorithmique - Analyse les cooccurrences verbales entre pays
        
        Args:
            articles_by_country: Dict {pays: [articles]}
            min_countries: Nombre minimum de pays pour considérer un pattern
            
        Returns:
            Liste de patterns transnationaux
        """
        # 1. Extraire les patterns par pays
        country_patterns = {}
        for country, articles in articles_by_country.items():
            logger.info(f"  📝 Analyse de {len(articles)} articles pour {country}")
            verb_patterns = self._extract_verb_patterns(articles)
            country_patterns[country] = verb_patterns
            logger.info(f"     → {len(verb_patterns)} patterns uniques détectés")
        
        # 2. Détecter les patterns communs
        common_patterns = self._find_common_patterns(country_patterns)
        
        # 3. Filtrer et formater les résultats
        transnational_patterns = []
        for pattern, countries_list in common_patterns.items():
            if len(countries_list) >= min_countries:
                # Calculer la force du pattern
                total_occurrences = sum(
                    country_patterns[country].get(pattern, 0) 
                    for country in countries_list
                )
                
                transnational_patterns.append({
                    'pattern': pattern,
                    'countries': countries_list,
                    'country_count': len(countries_list),
                    'total_occurrences': total_occurrences,
                    'strength': len(countries_list),
                    'first_detected': datetime.now().isoformat(),
                    'avg_occurrences': total_occurrences / len(countries_list)
                })
        
        # Trier par force décroissante
        transnational_patterns.sort(key=lambda x: (x['country_count'], x['total_occurrences']), reverse=True)
        
        return transnational_patterns
    
    def _extract_verb_patterns(self, articles: List[Dict]) -> Dict[str, int]:
        """
        Extrait les patterns verbe + contexte des articles d'un pays
        
        Args:
            articles: Liste d'articles du pays
            
        Returns:
            Dict {pattern: nombre_occurrences}
        """
        patterns = defaultdict(int)
        
        for article in articles:
            try:
                # Combiner titre et contenu
                title = article.get('title', '')
                content = article.get('content', '')
                text = f"{title}. {content}"
                
                # Découper en phrases
                sentences = self._split_sentences(text)
                
                # Analyser chaque phrase
                for sentence in sentences:
                    if not sentence.strip():
                        continue
                        
                    # Extraire les verbes
                    verbs = self._extract_verbs(sentence)
                    
                    # Créer des patterns pour chaque verbe
                    for verb in verbs:
                        pattern = self._build_pattern(verb, sentence)
                        if pattern and len(pattern.split()) >= 3:  # Minimum 3 mots
                            patterns[pattern] += 1
                            
            except Exception as e:
                logger.debug(f"Erreur traitement article: {e}")
                continue
        
        return dict(patterns)
    
    def _extract_verbs(self, sentence: str) -> List[str]:
        """
        Extrait les verbes d'une phrase (version améliorée)
        
        Args:
            sentence: Phrase à analyser
            
        Returns:
            Liste de verbes détectés
        """
        verbs = []
        
        # Nettoyer et tokeniser
        sentence_lower = sentence.lower()
        words = re.findall(r'\b[\wéèêàâùûîôçœ]+\b', sentence_lower)
        
        for word in words:
            if word in self.geopolitical_verbs:
                verbs.append(word)
        
        return verbs
    
    def _build_pattern(self, verb: str, sentence: str) -> str:
        """
        Construit un pattern à partir d'un verbe et de son contexte
        
        Args:
            verb: Verbe central
            sentence: Phrase complète
            
        Returns:
            Pattern contextualisé (ou None)
        """
        # Tokeniser la phrase
        words = re.findall(r'\b[\wéèêàâùûîôçœ]+\b', sentence.lower())
        
        if verb not in words:
            return None
        
        # Trouver l'index du verbe
        try:
            verb_index = words.index(verb)
        except ValueError:
            return None
        
        # Extraire le contexte (2 mots avant, 2 mots après)
        start = max(0, verb_index - 2)
        end = min(len(words), verb_index + 3)
        
        context_words = words[start:end]
        
        # Filtrer les mots vides non pertinents
        stop_words = {'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'à', 'au', 'aux'}
        filtered_words = [w for w in context_words if w not in stop_words or w == verb]
        
        if len(filtered_words) < 2:
            return None
        
        return " ".join(filtered_words)
    
    def _find_common_patterns(self, country_patterns: Dict[str, Dict[str, int]]) -> Dict[str, List[str]]:
        """
        Trouve les patterns communs à plusieurs pays
        
        Args:
            country_patterns: Dict {pays: {pattern: count}}
            
        Returns:
            Dict {pattern: [liste_pays]}
        """
        pattern_countries = defaultdict(list)
        
        for country, patterns in country_patterns.items():
            for pattern in patterns.keys():
                pattern_countries[pattern].append(country)
        
        return dict(pattern_countries)
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Découpe un texte en phrases
        
        Args:
            text: Texte à découper
            
        Returns:
            Liste de phrases
        """
        # Remplacer les abréviations courantes pour éviter les faux positifs
        text = text.replace('M.', 'M§')
        text = text.replace('Mme.', 'Mme§')
        text = text.replace('Dr.', 'Dr§')
        text = text.replace('etc.', 'etc§')
        
        # Découper sur les ponctuations fortes
        sentences = re.split(r'[.!?]+', text)
        
        # Restaurer les abréviations
        sentences = [s.replace('§', '.').strip() for s in sentences if s.strip()]
        
        return sentences
    
    # =========================================================================
    # RÉCUPÉRATION DES DONNÉES
    # =========================================================================
    
    def _get_recent_articles_by_country(self, days: int) -> Dict[str, List[Dict]]:
        """
        Récupère les articles groupés par pays
        
        Args:
            days: Nombre de jours à récupérer
            
        Returns:
            Dict {pays: [articles]}
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Requête améliorée avec détection de pays plus robuste
            cursor.execute("""
                SELECT 
                    a.id, 
                    a.title, 
                    a.content, 
                    a.feed_url, 
                    a.pub_date,
                    CASE 
                        WHEN a.feed_url LIKE '%france%' OR a.feed_url LIKE '%fr.%' OR a.feed_url LIKE '%.fr/%' THEN 'FR'
                        WHEN a.feed_url LIKE '%germany%' OR a.feed_url LIKE '%de.%' OR a.feed_url LIKE '%.de/%' THEN 'DE'
                        WHEN a.feed_url LIKE '%uk.%' OR a.feed_url LIKE '%.uk/%' OR a.feed_url LIKE '%britain%' THEN 'UK'
                        WHEN a.feed_url LIKE '%us.%' OR a.feed_url LIKE '%.us/%' OR a.feed_url LIKE '%usa%' THEN 'US'
                        WHEN a.feed_url LIKE '%spain%' OR a.feed_url LIKE '%es.%' OR a.feed_url LIKE '%.es/%' THEN 'ES'
                        WHEN a.feed_url LIKE '%italy%' OR a.feed_url LIKE '%it.%' OR a.feed_url LIKE '%.it/%' THEN 'IT'
                        ELSE 'OTHER'
                    END as country
                FROM articles a
                WHERE a.pub_date >= datetime('now', '-' || ? || ' days')
                    AND a.content IS NOT NULL
                    AND LENGTH(a.content) > 100
                ORDER BY country, a.pub_date DESC
            """, (days,))
            
            articles_by_country = defaultdict(list)
            
            for row in cursor.fetchall():
                country = row[5]
                
                # Ignorer les articles "OTHER" si peu nombreux
                if country == 'OTHER':
                    continue
                
                articles_by_country[country].append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'feed_url': row[3],
                    'pub_date': row[4],
                    'country': country
                })
            
            conn.close()
            
            return dict(articles_by_country)
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération articles: {e}")
            return {}
    
    # =========================================================================
    # MÉTHODES UTILITAIRES SUPPLÉMENTAIRES
    # =========================================================================
    
    def get_pattern_details(self, pattern: str, days: int = 7) -> Dict[str, Any]:
        """
        Obtient les détails d'un pattern spécifique
        
        Args:
            pattern: Pattern à analyser
            days: Période d'analyse
            
        Returns:
            Détails du pattern avec exemples d'articles
        """
        try:
            articles_by_country = self._get_recent_articles_by_country(days)
            
            result = {
                'pattern': pattern,
                'countries': [],
                'examples': []
            }
            
            for country, articles in articles_by_country.items():
                for article in articles:
                    text = f"{article['title']} {article['content']}".lower()
                    if pattern.lower() in text:
                        result['countries'].append(country)
                        result['examples'].append({
                            'country': country,
                            'title': article['title'],
                            'pub_date': article['pub_date'],
                            'article_id': article['id']
                        })
            
            # Dédupliquer les pays
            result['countries'] = list(set(result['countries']))
            result['country_count'] = len(result['countries'])
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération détails pattern: {e}")
            return {'error': str(e)}
    
    def export_patterns_json(self, patterns: List[Dict], filepath: str = None) -> str:
        """
        Exporte les patterns en JSON
        
        Args:
            patterns: Liste de patterns à exporter
            filepath: Chemin du fichier (optionnel)
            
        Returns:
            JSON string ou chemin du fichier
        """
        import json
        
        json_data = json.dumps(patterns, ensure_ascii=False, indent=2)
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(json_data)
                logger.info(f"✅ Patterns exportés vers {filepath}")
                return filepath
            except Exception as e:
                logger.error(f"❌ Erreur export: {e}")
                return json_data
        
        return json_data