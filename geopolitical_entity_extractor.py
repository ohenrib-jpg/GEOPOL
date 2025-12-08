# Flask/geopolitical_entity_extractor.py - Extraction d'entités géopolitiques
import spacy
import logging
from typing import List, Dict, Any, Set
from collections import Counter
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class GeopoliticalEntityExtractor:
    """
    Extracteur d'entités géopolitiques utilisant SpaCy
    Identifie : pays, villes, organisations, personnalités, événements
    """
    
    # Catégories d'entités géopolitiques
    ENTITY_CATEGORIES = {
        'GPE': 'location',      # Pays, villes, états
        'LOC': 'location',      # Lieux géographiques
        'ORG': 'organization',  # Organisations, gouvernements
        'PERSON': 'person',     # Personnalités
        'EVENT': 'event',       # Événements
        'NORP': 'group'         # Nationalités, groupes religieux/politiques
    }
    
    # Liste étendue de pays et régions (pour enrichissement)
    KNOWN_COUNTRIES = {
        'france', 'états-unis', 'usa', 'chine', 'russie', 'inde', 'japon',
        'allemagne', 'royaume-uni', 'italie', 'espagne', 'canada', 'mexique',
        'brésil', 'argentine', 'australie', 'corée du sud', 'iran', 'irak',
        'syrie', 'israël', 'palestine', 'égypte', 'arabie saoudite', 'turquie',
        'ukraine', 'pologne', 'suède', 'norvège', 'finlande', 'belgique',
        'pays-bas', 'suisse', 'autriche', 'portugal', 'grèce', 'hongrie'
    }
    
    # Organisations internationales importantes
    KNOWN_ORGANIZATIONS = {
        'onu', 'otan', 'union européenne', 'ue', 'omc', 'fmi', 'banque mondiale',
        'oms', 'unesco', 'opep', 'g7', 'g20', 'brics', 'asean', 'osce',
        'conseil de sécurité', 'parlement européen', 'commission européenne'
    }
    
    def __init__(self, model_name: str = "fr_core_news_lg"):
        """
        Initialise l'extracteur avec le modèle SpaCy français
        
        Args:
            model_name: Nom du modèle SpaCy à utiliser
        """
        self.model_name = model_name
        self.nlp = None
        self._load_model()
    
    def _load_model(self):
        """Charge le modèle SpaCy"""
        try:
            self.nlp = spacy.load(self.model_name)
            logger.info(f"✅ Modèle SpaCy '{self.model_name}' chargé avec succès")
        except OSError:
            logger.error(f"❌ Modèle '{self.model_name}' non trouvé")
            logger.info("📥 Installation du modèle...")
            try:
                import subprocess
                subprocess.run(
                    ["python", "-m", "spacy", "download", self.model_name],
                    check=True
                )
                self.nlp = spacy.load(self.model_name)
                logger.info(f"✅ Modèle '{self.model_name}' installé et chargé")
            except Exception as e:
                logger.error(f"❌ Impossible d'installer le modèle: {e}")
                raise
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extrait toutes les entités géopolitiques d'un texte
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dictionnaire contenant les entités par catégorie
        """
        if not text or not self.nlp:
            return self._empty_result()
        
        try:
            doc = self.nlp(text)
            
            entities = {
                'locations': [],
                'organizations': [],
                'persons': [],
                'events': [],
                'groups': [],
                'all_entities': []
            }
            
            seen_entities = set()
            
            for ent in doc.ents:
                entity_text = ent.text.strip()
                entity_lower = entity_text.lower()
                
                # Éviter les doublons
                if entity_lower in seen_entities:
                    continue
                seen_entities.add(entity_lower)
                
                entity_data = {
                    'text': entity_text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                }
                
                # Catégoriser selon le type SpaCy
                category = self.ENTITY_CATEGORIES.get(ent.label_, 'other')
                
                if category == 'location':
                    entities['locations'].append(entity_data)
                elif category == 'organization':
                    entities['organizations'].append(entity_data)
                elif category == 'person':
                    entities['persons'].append(entity_data)
                elif category == 'event':
                    entities['events'].append(entity_data)
                elif category == 'group':
                    entities['groups'].append(entity_data)
                
                entities['all_entities'].append(entity_data)
            
            # Enrichir avec détection personnalisée
            self._enrich_with_known_entities(text, entities)
            
            return entities
            
        except Exception as e:
            logger.error(f"❌ Erreur extraction entités: {e}")
            return self._empty_result()
    
    def _enrich_with_known_entities(self, text: str, entities: Dict[str, Any]):
        """
        Enrichit la détection avec des listes prédéfinies
        """
        text_lower = text.lower()
        
        # Détecter pays connus
        for country in self.KNOWN_COUNTRIES:
            if country in text_lower:
                # Vérifier si déjà détecté
                if not any(e['text'].lower() == country for e in entities['locations']):
                    entities['locations'].append({
                        'text': country.title(),
                        'label': 'GPE',
                        'start': -1,
                        'end': -1,
                        'source': 'enrichment'
                    })
        
        # Détecter organisations connues
        for org in self.KNOWN_ORGANIZATIONS:
            if org in text_lower:
                if not any(e['text'].lower() == org for e in entities['organizations']):
                    entities['organizations'].append({
                        'text': org.upper() if len(org) <= 4 else org.title(),
                        'label': 'ORG',
                        'start': -1,
                        'end': -1,
                        'source': 'enrichment'
                    })
    
    def _empty_result(self) -> Dict[str, Any]:
        """Retourne un résultat vide"""
        return {
            'locations': [],
            'organizations': [],
            'persons': [],
            'events': [],
            'groups': [],
            'all_entities': []
        }
    
    def extract_with_context(self, text: str, context_window: int = 50) -> Dict[str, Any]:
        """
        Extrait les entités avec leur contexte
        
        Args:
            text: Texte à analyser
            context_window: Nombre de caractères de contexte autour de l'entité
            
        Returns:
            Entités avec contexte
        """
        entities = self.extract_entities(text)
        
        # Ajouter le contexte pour chaque entité
        for category in ['locations', 'organizations', 'persons', 'events', 'groups']:
            for entity in entities[category]:
                if entity.get('start', -1) >= 0:
                    start = max(0, entity['start'] - context_window)
                    end = min(len(text), entity['end'] + context_window)
                    entity['context'] = text[start:end]
        
        return entities
    
    def get_most_frequent_entities(self, text: str, top_n: int = 10) -> Dict[str, List[tuple]]:
        """
        Retourne les entités les plus fréquentes par catégorie
        
        Args:
            text: Texte à analyser
            top_n: Nombre d'entités à retourner par catégorie
            
        Returns:
            Dictionnaire des entités les plus fréquentes avec leur compte
        """
        entities = self.extract_entities(text)
        
        result = {}
        
        for category in ['locations', 'organizations', 'persons', 'groups']:
            entity_texts = [e['text'] for e in entities[category]]
            counter = Counter(entity_texts)
            result[category] = counter.most_common(top_n)
        
        return result
    
    def analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyse un article complet et extrait toutes les informations
        
        Args:
            article: Dictionnaire contenant 'title' et 'content'
            
        Returns:
            Analyse complète avec entités et statistiques
        """
        title = article.get('title', '')
        content = article.get('content', '')
        full_text = f"{title}. {content}"
        
        # Extraction des entités
        entities = self.extract_entities(full_text)
        
        # Statistiques
        stats = {
            'total_entities': len(entities['all_entities']),
            'locations_count': len(entities['locations']),
            'organizations_count': len(entities['organizations']),
            'persons_count': len(entities['persons']),
            'events_count': len(entities['events']),
            'groups_count': len(entities['groups'])
        }
        
        # Entités les plus fréquentes
        frequent = self.get_most_frequent_entities(full_text, top_n=5)
        
        return {
            'entities': entities,
            'statistics': stats,
            'frequent_entities': frequent,
            'analyzed_at': datetime.now().isoformat()
        }
    
    def extract_geopolitical_network(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyse un ensemble d'articles pour créer un réseau d'entités géopolitiques
        
        Args:
            articles: Liste d'articles à analyser
            
        Returns:
            Réseau d'entités avec relations et statistiques globales
        """
        all_locations = []
        all_organizations = []
        all_persons = []
        location_org_pairs = []
        
        for article in articles:
            analysis = self.analyze_article(article)
            entities = analysis['entities']
            
            # Collecter toutes les entités
            all_locations.extend([e['text'] for e in entities['locations']])
            all_organizations.extend([e['text'] for e in entities['organizations']])
            all_persons.extend([e['text'] for e in entities['persons']])
            
            # Créer des paires location-organisation (co-occurrence)
            for loc in entities['locations']:
                for org in entities['organizations']:
                    location_org_pairs.append((loc['text'], org['text']))
        
        # Calculer les fréquences
        location_freq = Counter(all_locations)
        org_freq = Counter(all_organizations)
        person_freq = Counter(all_persons)
        pair_freq = Counter(location_org_pairs)
        
        return {
            'top_locations': location_freq.most_common(20),
            'top_organizations': org_freq.most_common(20),
            'top_persons': person_freq.most_common(20),
            'top_relations': pair_freq.most_common(20),
            'total_articles_analyzed': len(articles),
            'network_density': len(pair_freq) / max(len(location_freq) * len(org_freq), 1)
        }
    
    def format_for_display(self, entities: Dict[str, Any]) -> str:
        """
        Formate les entités pour affichage lisible
        
        Args:
            entities: Résultat de extract_entities()
            
        Returns:
            Chaîne formatée
        """
        output = []
        
        if entities['locations']:
            output.append("🌍 LIEUX:")
            for e in entities['locations'][:10]:
                output.append(f"  • {e['text']}")
        
        if entities['organizations']:
            output.append("\n🏛️ ORGANISATIONS:")
            for e in entities['organizations'][:10]:
                output.append(f"  • {e['text']}")
        
        if entities['persons']:
            output.append("\n👤 PERSONNALITÉS:")
            for e in entities['persons'][:10]:
                output.append(f"  • {e['text']}")
        
        if entities['groups']:
            output.append("\n👥 GROUPES:")
            for e in entities['groups'][:10]:
                output.append(f"  • {e['text']}")
        
        return "\n".join(output) if output else "Aucune entité détectée"
    
    def export_to_json(self, entities: Dict[str, Any], filepath: str):
        """
        Exporte les entités en JSON
        
        Args:
            entities: Résultat de extract_entities()
            filepath: Chemin du fichier de sortie
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(entities, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Entités exportées vers {filepath}")
        except Exception as e:
            logger.error(f"❌ Erreur export JSON: {e}")