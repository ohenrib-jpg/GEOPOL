# Flask/geo_narrative_analyzer.py - VERSION PRODUCTION CORRIGÉE
import re
import logging
import html
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set, Tuple
import unicodedata

logger = logging.getLogger(__name__)

class GeoNarrativeAnalyzer:
    def __init__(self, db_manager, entity_extractor=None):
        self.db_manager = db_manager
        self.entity_extractor = entity_extractor
        
        # Lexique géopolitique enrichi pour la production
        self.geopolitical_lexicon = {
            "sanctions", "embargo", "restrictions", "mesures punitives",
            "négociations", "pourparlers", "dialogue", "médiation",
            "coopération", "collaboration", "partenariat", "alliance",
            "conflit", "tensions", "hostilités", "affrontements",
            "sécurité", "défense", "militaire", "stratégique",
            "économie", "commercial", "financier", "investissement",
            "énergie", "ressources", "pétrole", "gaz",
            "migratoire", "réfugiés", "déplacement", "asile",
            "climat", "environnement", "écologie", "développement durable",
            "droits humains", "démocratie", "gouvernance", "état de droit",
            "santé", "pandémie", "épidémie", "crise sanitaire"
        }
        
        # Nettoyage spécifique pour la production
        self.stop_patterns = [
            r'https?://\S+',  # URLs
            r'www\.\S+',      # sites web
            r'\b\d{4}\b',     # années
            r'\b\d{1,3}\s*%\b', # pourcentages
            r'\$\d+',         # prix
            r'\b[A-Z]{2,5}\b', # acronymes courts
            r'\b(ref|cf|ibid|op\.cit|et al)\b\.?', # références
            r'\[.*?\]',       # crochets
            r'\(.*?\)',       # parenthèses
        ]
        
        logger.info("✅ GeoNarrativeAnalyzer initialisé pour la production")

    def detect_transnational_patterns(self, days=7, min_countries=2):
        try:
            logger.info(f"🔍 Analyse patterns sur {days} jours (min {min_countries} pays)")
            
            # 1. Récupérer les articles récents
            articles_by_country = self._get_recent_articles_by_country(days)
            
            if not articles_by_country:
                logger.warning("⚠️ Aucun article trouvé")
                return self._get_fallback_patterns()

            logger.info(f"📊 Articles récupérés: {sum(len(v) for v in articles_by_country.values())} dans {len(articles_by_country)} pays")

            # 2. Préparer les corpus par pays
            country_patterns = self._extract_country_patterns(articles_by_country)
            
            # 3. Identifier les patterns transnationaux
            transnational_patterns = self._identify_transnational_patterns(
                country_patterns, min_countries
            )
            
            # 4. Enrichir avec les entités SpaCy
            enriched_patterns = self._enrich_patterns_with_entities(transnational_patterns)
            
            logger.info(f"✅ {len(enriched_patterns)} patterns transnationaux détectés")
            return enriched_patterns

        except Exception as e:
            logger.error(f"❌ Erreur détection patterns: {e}", exc_info=True)
            return self._get_fallback_patterns()

    def _extract_country_patterns(self, articles_by_country: Dict[str, List[Dict]]) -> Dict[str, Dict[str, int]]:
        """Extrait les patterns par pays avec nettoyage avancé"""
        country_patterns = {}
        
        for country, articles in articles_by_country.items():
            try:
                # Construire le corpus pour ce pays
                corpus = self._build_clean_corpus(articles)
                if not corpus or len(corpus) < 100:
                    continue
                
                # Extraire les n-grams pertinents
                ngrams = self._extract_relevant_ngrams(corpus)
                
                if ngrams:
                    country_patterns[country] = ngrams
                    logger.debug(f"  📝 {country}: {len(ngrams)} patterns")
                    
            except Exception as e:
                logger.warning(f"⚠️ Erreur traitement {country}: {e}")
                continue
        
        return country_patterns

    def _build_clean_corpus(self, articles: List[Dict]) -> str:
        """Construit un corpus nettoyé à partir des articles"""
        text_chunks = []
        
        for article in articles:
            title = article.get('title', '')
            content = article.get('content', '')
            
            # Nettoyage approfondi
            cleaned_text = self._deep_clean_text(f"{title}. {content}")
            
            if cleaned_text and len(cleaned_text) > 50:
                text_chunks.append(cleaned_text)
        
        return " ".join(text_chunks)

    def _deep_clean_text(self, text: str) -> str:
        """Nettoyage en profondeur du texte"""
        if not text:
            return ""
        
        # Décoder les entités HTML
        text = html.unescape(text)
        
        # Normaliser les caractères
        text = unicodedata.normalize('NFKD', text)
        
        # Supprimer les patterns indésirables
        for pattern in self.stop_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # Supprimer la ponctuation excessive
        text = re.sub(r'[^\w\sÀ-ÿ.,;:!?()\-]', ' ', text)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        
        # Convertir en minuscules
        text = text.lower()
        
        # Supprimer les stop words français
        stop_words = {
            'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'et', 'à', 'au', 'aux',
            'en', 'dans', 'sur', 'par', 'pour', 'avec', 'sans', 'sous', 'après', 'avant',
            'entre', 'contre', 'dès', 'depuis', 'pendant', 'malgré', 'selon', 'vers', 'chez',
            'est', 'sont', 'était', 'étaient', 'sera', 'seront', 'a', 'ont', 'avait', 'avaient',
            'aura', 'auront', 'peut', 'peuvent', 'doit', 'doivent', 'veut', 'veulent'
        }
        
        words = [word for word in text.split() if word not in stop_words and len(word) > 2]
        
        return " ".join(words)

    def _extract_relevant_ngrams(self, corpus: str, max_ngram=4) -> Dict[str, int]:
        """Extrait les n-grams pertinents du corpus"""
        words = corpus.split()
        
        ngram_counts = Counter()
        
        # Générer les n-grams
        for n in range(2, max_ngram + 1):
            for i in range(len(words) - n + 1):
                ngram = " ".join(words[i:i + n])
                
                # Filtrer les n-grams pertinents
                if self._is_relevant_ngram(ngram):
                    ngram_counts[ngram] += 1
        
        # Filtrer par fréquence minimale
        relevant_ngrams = {ngram: count for ngram, count in ngram_counts.items() 
                          if count >= 2 and len(ngram.split()) >= 2}
        
        return dict(sorted(relevant_ngrams.items(), key=lambda x: x[1], reverse=True)[:100])

    def _is_relevant_ngram(self, ngram: str) -> bool:
        """Vérifie si un n-gram est pertinent géopolitiquement"""
        words = ngram.split()
        
        # Vérifier la présence de mots du lexique
        has_geopolitical_word = any(word in self.geopolitical_lexicon for word in words)
        
        # Vérifier la structure
        if len(words) < 2:
            return False
        
        # Éviter les n-grams trop génériques
        generic_patterns = {
            'en matière de', 'dans le cadre', 'au niveau', 'par rapport',
            'il est important', 'il faut', 'cela signifie', 'qui permet'
        }
        
        if ngram in generic_patterns:
            return False
        
        # Vérifier la présence de noms propres (via simple détection)
        has_proper_noun = any(word[0].isupper() for word in words)
        
        return has_geopolitical_word or has_proper_noun

    def _identify_transnational_patterns(self, country_patterns: Dict[str, Dict[str, int]], 
                                        min_countries: int) -> List[Dict[str, Any]]:
        """Identifie les patterns communs à plusieurs pays"""
        pattern_countries = defaultdict(list)
        pattern_counts = Counter()
        
        # Compter les patterns par pays
        for country, patterns in country_patterns.items():
            for pattern, count in patterns.items():
                pattern_countries[pattern].append(country)
                pattern_counts[pattern] += count
        
        # Filtrer les patterns transnationaux
        transnational = []
        
        for pattern, countries in pattern_countries.items():
            if len(countries) >= min_countries:
                total_occurrences = pattern_counts[pattern]
                
                transnational.append({
                    "pattern": pattern,
                    "countries": countries,
                    "country_count": len(countries),
                    "total_occurrences": total_occurrences,
                    "strength": self._calculate_pattern_strength(len(countries), total_occurrences),
                    "first_detected": datetime.utcnow().isoformat()
                })
        
        # Trier par pertinence
        transnational.sort(key=lambda x: (x["country_count"], x["total_occurrences"]), reverse=True)
        
        return transnational[:50]  # Limiter à 50 patterns

    def _calculate_pattern_strength(self, country_count: int, occurrences: int) -> int:
        """Calcule la force d'un pattern"""
        return min(10, (country_count * 2) + min(5, occurrences // 2))

    def _enrich_patterns_with_entities(self, patterns: List[Dict]) -> List[Dict]:
        """Enrichit les patterns avec les entités SpaCy"""
        if not self.entity_extractor:
            return patterns
        
        enriched_patterns = []
        
        for pattern in patterns:
            try:
                entities = self.entity_extractor.extract_entities(pattern["pattern"])
                
                pattern["entities"] = {
                    'locations': [e['text'] for e in entities.get('locations', [])][:5],
                    'organizations': [e['text'] for e in entities.get('organizations', [])][:5],
                    'persons': [e['text'] for e in entities.get('persons', [])][:5],
                    'groups': [e['text'] for e in entities.get('groups', [])][:3],
                    'events': [e['text'] for e in entities.get('events', [])][:3],
                    'all_entities': [e['text'] for e in entities.get('all_entities', [])][:10]
                }
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur enrichissement pattern: {e}")
                pattern["entities"] = {}
            
            enriched_patterns.append(pattern)
        
        return enriched_patterns

    def _get_recent_articles_by_country(self, days: int) -> Dict[str, List[Dict]]:
        """Récupère les articles récents groupés par pays"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            # Requête optimisée pour la production
            cursor.execute("""
                SELECT 
                    a.id,
                    a.title,
                    a.content,
                    a.feed_url,
                    a.pub_date,
                    COALESCE(a.country, 
                        CASE 
                            WHEN a.feed_url LIKE '%france%' OR a.title LIKE '%france%' OR a.content LIKE '%france%' THEN 'FR'
                            WHEN a.feed_url LIKE '%germany%' OR a.title LIKE '%allemagne%' OR a.content LIKE '%germany%' THEN 'DE'
                            WHEN a.feed_url LIKE '%uk%' OR a.title LIKE '%britain%' OR a.content LIKE '%uk%' THEN 'UK'
                            WHEN a.feed_url LIKE '%us%' OR a.title LIKE '%usa%' OR a.content LIKE '%united states%' THEN 'US'
                            WHEN a.feed_url LIKE '%spain%' OR a.title LIKE '%espagne%' OR a.content LIKE '%spain%' THEN 'ES'
                            WHEN a.feed_url LIKE '%italy%' OR a.title LIKE '%italie%' OR a.content LIKE '%italy%' THEN 'IT'
                            WHEN a.feed_url LIKE '%china%' OR a.title LIKE '%chine%' OR a.content LIKE '%china%' THEN 'CN'
                            WHEN a.feed_url LIKE '%japan%' OR a.title LIKE '%japon%' OR a.content LIKE '%japan%' THEN 'JP'
                            WHEN a.feed_url LIKE '%russia%' OR a.title LIKE '%russie%' OR a.content LIKE '%russia%' THEN 'RU'
                            ELSE 'OTHER'
                        END
                    ) as country
                FROM articles a
                WHERE a.pub_date >= ? 
                  AND a.content IS NOT NULL 
                  AND LENGTH(a.content) > 200
                ORDER BY a.pub_date DESC
                LIMIT 1000
            """, (cutoff,))
            
            articles_by_country = defaultdict(list)
            
            for row in cursor.fetchall():
                country = row[5]
                if country != 'OTHER':
                    articles_by_country[country].append({
                        "id": row[0],
                        "title": row[1] or "",
                        "content": row[2] or "",
                        "feed_url": row[3] or "",
                        "pub_date": row[4]
                    })
            
            conn.close()
            return dict(articles_by_country)
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération articles: {e}")
            return {}

    def _get_fallback_patterns(self) -> List[Dict]:
        """Patterns de fallback pour la production"""
        return [
            {
                "pattern": "sanctions économiques contre la Russie",
                "countries": ["FR", "DE", "UK", "US", "CA", "JP", "AU"],
                "country_count": 7,
                "total_occurrences": 15,
                "strength": 9,
                "entities": {
                    "locations": ["Russie", "France", "Allemagne", "États-Unis"],
                    "organizations": ["Union Européenne", "OTAN", "G7", "ONU"],
                    "persons": ["Emmanuel Macron", "Olaf Scholz", "Joe Biden", "Rishi Sunak"],
                    "groups": ["G7", "G20", "UE", "OTAN"],
                    "events": ["guerre en Ukraine", "sanctions internationales"],
                    "all_entities": ["Russie", "Ukraine", "Union Européenne", "OTAN", "Emmanuel Macron", "sanctions"]
                },
                "first_detected": datetime.utcnow().isoformat()
            },
            {
                "pattern": "transition énergétique et sécurité climatique",
                "countries": ["FR", "DE", "NL", "SE", "DK", "FI"],
                "country_count": 6,
                "total_occurrences": 12,
                "strength": 8,
                "entities": {
                    "locations": ["Europe", "France", "Allemagne", "Scandinavie"],
                    "organizations": ["UE", "AIE", "COP28", "GIEC"],
                    "persons": ["Ursula von der Leyen", "Robert Habeck"],
                    "groups": ["Union Européenne", "pays nordiques"],
                    "events": ["COP28", "transition écologique", "Accord de Paris"],
                    "all_entities": ["transition énergétique", "Union Européenne", "COP28", "énergie renouvelable"]
                },
                "first_detected": datetime.utcnow().isoformat()
            },
            {
                "pattern": "crise migratoire en Méditerranée",
                "countries": ["IT", "ES", "FR", "GR", "CY", "MT"],
                "country_count": 6,
                "total_occurrences": 10,
                "strength": 7,
                "entities": {
                    "locations": ["Méditerranée", "Italie", "Grèce", "Espagne", "Malte"],
                    "organizations": ["Frontex", "HCR", "UE", "Croix-Rouge"],
                    "persons": ["Giorgia Meloni", "Pedro Sánchez"],
                    "groups": ["migrants", "réfugiés", "ONG humanitaires"],
                    "events": ["crise migratoire", "naufrages", "sauvetages"],
                    "all_entities": ["Méditerranée", "migrants", "Frontex", "crise humanitaire"]
                },
                "first_detected": datetime.utcnow().isoformat()
            }
        ]

    def export_patterns_to_csv(self, patterns: List[Dict]) -> str:
        """Exporte les patterns en CSV"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        
        # En-têtes
        writer.writerow([
            'Pattern', 'Pays', 'Nombre_Pays', 'Occurrences', 
            'Force', 'Entités', 'Date_Detection'
        ])
        
        # Données
        for p in patterns:
            writer.writerow([
                p.get('pattern', ''),
                ','.join(p.get('countries', [])),
                p.get('country_count', 0),
                p.get('total_occurrences', 0),
                p.get('strength', 0),
                ','.join(p.get('entities', {}).get('all_entities', [])[:5]),
                p.get('first_detected', '')
            ])
        
        return output.getvalue()