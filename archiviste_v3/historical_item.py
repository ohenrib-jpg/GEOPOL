"""
Modèle pour les items historiques avec SpaCy
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class HistoricalItem:
    """Item historique avec analyse SpaCy intégrée"""
    
    def __init__(self, archive_data: Dict[str, Any]):
        self.identifier = archive_data.get('identifier', '')
        self.title = archive_data.get('title', '')
        self.description = archive_data.get('description', '')
        self.date = archive_data.get('date', '')
        self.year = archive_data.get('year', 0)
        self.language = archive_data.get('language', '')
        self.creator = archive_data.get('creator', '')
        self.publisher = archive_data.get('publisher', '')
        self.subject = archive_data.get('subject', [])
        self.downloads = archive_data.get('downloads', 0)
        
        # Construire l'URL source
        if self.identifier:
            self.source_url = f"https://archive.org/details/{self.identifier}"
        else:
            self.source_url = ''
        
        # Contenu extrait
        self.content = self._extract_content(archive_data)
        
        # Analyse SpaCy (sera remplie plus tard)
        self.entities = []
        self.embedding = None
        self.themes = []
        self.geopolitical_relevance = 0.0
        self.processed_at = None
        
        # Métadonnées
        self.created_at = datetime.now()
    
    def _extract_content(self, archive_data: Dict[str, Any]) -> str:
        """Extrait le contenu textuel des métadonnées"""
        text_parts = []
        
        if self.title:
            text_parts.append(str(self.title))
        
        if self.description:
            desc = self.description
            if isinstance(desc, list):
                text_parts.extend([str(d) for d in desc])
            else:
                text_parts.append(str(desc))
        
        if self.subject:
            if isinstance(self.subject, list):
                text_parts.extend([str(s) for s in self.subject])
            else:
                text_parts.append(str(self.subject))
        
        if self.creator:
            text_parts.append(str(self.creator))
        
        if self.publisher:
            text_parts.append(str(self.publisher))
        
        return ' '.join(text_parts)
    
    def analyze_with_spacy(self, nlp_model) -> bool:
        """
        Analyse l'item avec SpaCy
        
        Args:
            nlp_model: Modèle SpaCy chargé
            
        Returns:
            bool: Succès de l'analyse
        """
        try:
            if not nlp_model or not self.content:
                return False
            
            # Analyse SpaCy
            doc = nlp_model(self.content[:1000000])  # Limite de caractères
            
            # Extraction des entités
            self.entities = []
            for ent in doc.ents:
                if ent.label_ in ['GPE', 'LOC', 'ORG', 'PERSON', 'EVENT']:
                    self.entities.append({
                        'text': ent.text,
                        'label': ent.label_,
                        'start': ent.start_char,
                        'end': ent.end_char
                    })
            
            # Création de l'embedding
            if doc.has_vector:
                self.embedding = doc.vector.tolist()
            
            # Pertinence géopolitique simple
            geopolitical_labels = ['GPE', 'LOC', 'ORG']
            geopolitical_count = len([e for e in self.entities if e['label'] in geopolitical_labels])
            self.geopolitical_relevance = min(geopolitical_count / 10.0, 1.0)
            
            # Extraire des thèmes simples basés sur les entités
            if self.entities:
                entity_types = {}
                for entity in self.entities:
                    label = entity['label']
                    entity_types[label] = entity_types.get(label, 0) + 1
                
                self.themes = []
                for label, count in entity_types.items():
                    if count >= 2:  # Seuil minimal
                        self.themes.append({
                            'name': label.lower(),
                            'count': count,
                            'type': 'entity_based'
                        })
            
            self.processed_at = datetime.now()
            
            logger.debug(f"✅ Analyse SpaCy: {self.identifier} - {len(self.entities)} entités")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse SpaCy {self.identifier}: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour stockage JSON"""
        return {
            'identifier': self.identifier,
            'title': self.title,
            'description': self.description,
            'date': self.date,
            'year': self.year,
            'language': self.language,
            'creator': self.creator,
            'publisher': self.publisher,
            'subject': self.subject,
            'downloads': self.downloads,
            'source_url': self.source_url,
            'content': self.content[:1000] + '...' if len(self.content) > 1000 else self.content,
            'entities': self.entities,
            'themes': self.themes,
            'geopolitical_relevance': self.geopolitical_relevance,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoricalItem':
        """Crée une instance depuis un dictionnaire"""
        archive_data = {
            'identifier': data.get('identifier', ''),
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'date': data.get('date', ''),
            'year': data.get('year', 0),
            'language': data.get('language', ''),
            'creator': data.get('creator', ''),
            'publisher': data.get('publisher', ''),
            'subject': data.get('subject', []),
            'downloads': data.get('downloads', 0)
        }
        
        item = cls(archive_data)
        
        # Restaurer les champs analysés
        item.entities = data.get('entities', [])
        item.themes = data.get('themes', [])
        item.geopolitical_relevance = data.get('geopolitical_relevance', 0.0)
        
        if data.get('processed_at'):
            from datetime import datetime
            item.processed_at = datetime.fromisoformat(data['processed_at'])
        
        return item
    
    def __str__(self) -> str:
        return f"HistoricalItem({self.identifier}, {self.year}, {len(self.entities)} entités)"