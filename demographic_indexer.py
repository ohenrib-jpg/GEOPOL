"""
Demographic Data Indexer pour RAG Pipeline
Indexe les données socio-démographiques pour l'accès par l'IA locale

Convertit les indicateurs démographiques (OECD, Eurostat, World Bank, INSEE)
en documents structurés pour le système RAG.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DemographicDocument:
    """Document démographique pour le RAG"""
    country_code: str
    country_name: str
    indicator_id: str
    indicator_name: str
    value: float
    year: int
    source: str
    category: str
    unit: str = ""
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DemographicIndexer:
    """
    Indexe les données démographiques pour le RAG Pipeline
    Convertit les données de la DB en Documents searchable
    """

    def __init__(self, db_manager, cache_dir: str = None):
        """
        Args:
            db_manager: Database manager pour accéder aux données
            cache_dir: Répertoire pour le cache des documents indexés
        """
        self.db_manager = db_manager
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), 'demographic_cache')
        os.makedirs(self.cache_dir, exist_ok=True)

        # Mapping des indicateurs pour des noms lisibles
        self.indicator_names = {
            # OECD
            'oecd_population': 'Population totale',
            'oecd_health': 'Indicateurs de santé',
            'oecd_education': 'Niveau d\'éducation',
            'oecd_labour': 'Marché du travail',
            'oecd_inequality': 'Inégalités sociales',
            'oecd_wellbeing': 'Bien-être social',
            'oecd_migration': 'Flux migratoires',
            'oecd_family': 'Structures familiales',

            # Eurostat
            'demo_pjan': 'Population par âge et sexe',
            'demo_gind': 'Indicateurs démographiques',
            'demo_r_d2jan': 'Densité de population',
            'demo_find': 'Taux de fécondité',
            'demo_magec': 'Âge moyen de la maternité',

            # World Bank
            'SP.POP.TOTL': 'Population totale',
            'SP.POP.GROW': 'Croissance démographique',
            'SP.DYN.LE00.IN': 'Espérance de vie à la naissance',
            'SP.DYN.TFRT.IN': 'Taux de fécondité',
            'SP.URB.TOTL.IN.ZS': 'Population urbaine (%)',
            'NY.GDP.PCAP.CD': 'PIB par habitant',

            # INSEE
            'insee_population': 'Population INSEE',
            'insee_natalite': 'Taux de natalité',
            'insee_mortalite': 'Taux de mortalité',

            # Autres indicateurs courants
            'NY.GDP.MKTP.CD': 'PIB (valeur nominale, USD)',
            'NY.GDP.MKTP.KD.ZG': 'Croissance du PIB (%)',
            'SL.UEM.TOTL.ZS': 'Taux de chômage (% de la main-d\'œuvre)',
            'SI.POV.GINI': 'Coefficient de Gini (inégalité)',
            'SP.DYN.LE00.IN': 'Espérance de vie à la naissance (années)',
            'SP.DYN.TFRT.IN': 'Taux de fécondité (naissances par femme)',
            'SP.URB.TOTL.IN.ZS': 'Population urbaine (% du total)',
            'nama_10_gdp': 'PIB et composantes (Eurostat)',
            'une_rt_a': 'Taux de chômage (Eurostat)',
            'hlth_rs_prshp': 'Personnel de santé (Eurostat)',
            'educ_uoe_enra': 'Inscriptions dans l\'éducation (Eurostat)',
            'ICP': 'Parité de pouvoir d\'achat',
            'EXR': 'Taux de change',
            'SE.XPD.TOTL.GD.ZS': 'Dépenses éducation (% PIB)',
            'SE.PRM.NENR': 'Taux de scolarisation primaire',
            'SH.MED.PHYS.ZS': 'Médecins pour 1000 habitants',
        }

        # Mapping des catégories pour le contexte
        self.category_descriptions = {
            'population': 'Statistiques de population et démographie',
            'health': 'Indicateurs de santé publique',
            'education': 'Niveau d\'éducation et formation',
            'social': 'Indicateurs sociaux et bien-être',
            'economic': 'Indicateurs économiques liés à la démographie',
            'migration': 'Flux migratoires et mobilité',
            'fertility': 'Natalité et fécondité',
            'mortality': 'Mortalité et espérance de vie'
        }

        logger.info(f"[OK] DemographicIndexer initialisé (cache: {self.cache_dir})")

    def index_all_data(self) -> Dict[str, int]:
        """
        Indexe toutes les données démographiques disponibles

        Returns:
            Stats sur l'indexation (nombre de documents par source)
        """
        logger.info("[DATA] Indexation de toutes les données démographiques...")

        stats = {
            'total': 0,
            'by_source': {},
            'by_category': {},
            'by_country': {}
        }

        try:
            # Récupérer toutes les données démographiques
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Query pour récupérer tous les indicateurs
            cursor.execute("""
                SELECT
                    country_code,
                    country_name,
                    indicator_id,
                    value,
                    year,
                    source,
                    category,
                    unit
                FROM demographic_data
                WHERE value IS NOT NULL
                ORDER BY country_code, indicator_id, year DESC
            """)

            rows = cursor.fetchall()
            logger.info(f"📦 {len(rows)} enregistrements récupérés de la base de données")

            # Convertir en documents
            documents = []
            for row in rows:
                doc = DemographicDocument(
                    country_code=row[0],
                    country_name=row[1] or self._get_country_name(row[0]),
                    indicator_id=row[2],
                    indicator_name=self.indicator_names.get(row[2], row[2]),
                    value=float(row[3]),
                    year=int(row[4]),
                    source=row[5],
                    category=row[6] or 'other',
                    unit=row[7] or ''
                )
                documents.append(doc)

                # Stats
                stats['by_source'][doc.source] = stats['by_source'].get(doc.source, 0) + 1
                stats['by_category'][doc.category] = stats['by_category'].get(doc.category, 0) + 1
                stats['by_country'][doc.country_code] = stats['by_country'].get(doc.country_code, 0) + 1

            stats['total'] = len(documents)

            # Sauvegarder les documents dans le cache
            self._save_to_cache(documents)

            logger.info(f"[OK] Indexation terminée: {stats['total']} documents")
            logger.info(f"   Par source: {stats['by_source']}")
            logger.info(f"   Par catégorie: {stats['by_category']}")

            return stats

        except Exception as e:
            logger.error(f"[ERROR] Erreur indexation: {e}", exc_info=True)
            return stats

    def search_documents(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Recherche dans les documents indexés

        Args:
            query: Requête de recherche (mots-clés, pays, indicateurs)
            limit: Nombre maximum de résultats

        Returns:
            Liste de documents formatés pour le RAG
        """
        logger.info(f"[SEARCH] Recherche démographique: '{query}'")

        # Charger les documents du cache
        documents = self._load_from_cache()

        if not documents:
            logger.warning("[WARN] Aucun document en cache, indexation nécessaire")
            self.index_all_data()
            documents = self._load_from_cache()

        # Filtrage par mots-clés
        query_lower = query.lower()
        keywords = self._extract_keywords(query)

        matched_docs = []
        for doc in documents:
            score = 0

            # Construire le texte searchable
            searchable_text = f"{doc.country_name} {doc.country_code} {doc.indicator_name} {doc.indicator_id} {doc.category} {doc.source}".lower()

            # Simple keyword matching
            for keyword in keywords:
                if keyword in searchable_text:
                    score += 2

            # Query complète dans le texte
            if query_lower in searchable_text:
                score += 3

            # Bonus pour les données récentes
            if doc.year >= 2020:
                score += 1

            if score > 0:
                matched_docs.append((score, doc))

        # Trier par score décroissant
        matched_docs.sort(key=lambda x: x[0], reverse=True)

        # Convertir en format RAG Document
        rag_documents = []
        for score, doc in matched_docs[:limit]:
            rag_doc = self._to_rag_document(doc, score)
            rag_documents.append(rag_doc)

        logger.info(f"[OK] {len(rag_documents)} documents trouvés")
        return rag_documents

    def get_country_summary(self, country_code: str) -> Dict:
        """
        Génère un résumé complet pour un pays

        Args:
            country_code: Code ISO du pays (FR, DE, etc.)

        Returns:
            Résumé structuré avec tous les indicateurs disponibles
        """
        logger.info(f"[DATA] Résumé démographique pour {country_code}")

        documents = self._load_from_cache()

        # Filtrer par pays
        country_docs = [doc for doc in documents if doc.country_code.upper() == country_code.upper()]

        if not country_docs:
            return {
                'country_code': country_code,
                'country_name': self._get_country_name(country_code),
                'error': 'Aucune donnée disponible pour ce pays'
            }

        # Organiser par catégorie
        by_category = {}
        latest_year = 0

        for doc in country_docs:
            if doc.category not in by_category:
                by_category[doc.category] = []
            by_category[doc.category].append(doc)
            latest_year = max(latest_year, doc.year)

        # Récupérer les indicateurs les plus récents par catégorie
        summary = {
            'country_code': country_code,
            'country_name': country_docs[0].country_name,
            'latest_year': latest_year,
            'categories': {},
            'total_indicators': len(country_docs)
        }

        for category, docs in by_category.items():
            # Prendre l'indicateur le plus récent de chaque type
            latest_by_indicator = {}
            for doc in docs:
                if doc.indicator_id not in latest_by_indicator or doc.year > latest_by_indicator[doc.indicator_id].year:
                    latest_by_indicator[doc.indicator_id] = doc

            summary['categories'][category] = {
                'description': self.category_descriptions.get(category, category),
                'indicators': [
                    {
                        'name': doc.indicator_name,
                        'value': doc.value,
                        'year': doc.year,
                        'unit': doc.unit,
                        'source': doc.source
                    }
                    for doc in latest_by_indicator.values()
                ]
            }

        return summary

    def _to_rag_document(self, demo_doc: DemographicDocument, relevance_score: float = 0.0) -> Dict:
        """
        Convertit un DemographicDocument en format RAG Document

        Args:
            demo_doc: Document démographique
            relevance_score: Score de pertinence pour le tri

        Returns:
            Dict compatible avec rag_pipeline.Document
        """
        # Formater le contenu de manière lisible
        content = f"""
{demo_doc.indicator_name} ({demo_doc.indicator_id})
Pays: {demo_doc.country_name} ({demo_doc.country_code})
Valeur: {demo_doc.value:,.2f} {demo_doc.unit}
Année: {demo_doc.year}
Source: {demo_doc.source.upper()}
Catégorie: {self.category_descriptions.get(demo_doc.category, demo_doc.category)}
        """.strip()

        title = f"{demo_doc.country_name} - {demo_doc.indicator_name} ({demo_doc.year})"

        return {
            'content': content,
            'title': title,
            'source': f"demographic_{demo_doc.source}",
            'url': None,
            'timestamp': datetime.now().isoformat(),
            'relevance_score': relevance_score,
            'source_type': 'demographic',
            'metadata': {
                'country_code': demo_doc.country_code,
                'country_name': demo_doc.country_name,
                'indicator_id': demo_doc.indicator_id,
                'value': demo_doc.value,
                'year': demo_doc.year,
                'category': demo_doc.category,
                'source': demo_doc.source
            }
        }

    def _save_to_cache(self, documents: List[DemographicDocument]):
        """Sauvegarde les documents dans le cache"""
        cache_file = os.path.join(self.cache_dir, 'demographic_index.json')

        try:
            # Convertir en dict pour JSON
            docs_dict = []
            for doc in documents:
                docs_dict.append({
                    'country_code': doc.country_code,
                    'country_name': doc.country_name,
                    'indicator_id': doc.indicator_id,
                    'indicator_name': doc.indicator_name,
                    'value': doc.value,
                    'year': doc.year,
                    'source': doc.source,
                    'category': doc.category,
                    'unit': doc.unit,
                    'metadata': doc.metadata
                })

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'total': len(docs_dict),
                    'documents': docs_dict
                }, f, ensure_ascii=False, indent=2)

            logger.info(f"💾 Cache sauvegardé: {len(docs_dict)} documents")

        except Exception as e:
            logger.error(f"[ERROR] Erreur sauvegarde cache: {e}")

    def _load_from_cache(self) -> List[DemographicDocument]:
        """Charge les documents depuis le cache"""
        cache_file = os.path.join(self.cache_dir, 'demographic_index.json')

        if not os.path.exists(cache_file):
            return []

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            documents = []
            for doc_dict in data.get('documents', []):
                doc = DemographicDocument(
                    country_code=doc_dict['country_code'],
                    country_name=doc_dict['country_name'],
                    indicator_id=doc_dict['indicator_id'],
                    indicator_name=doc_dict['indicator_name'],
                    value=doc_dict['value'],
                    year=doc_dict['year'],
                    source=doc_dict['source'],
                    category=doc_dict['category'],
                    unit=doc_dict.get('unit', ''),
                    metadata=doc_dict.get('metadata', {})
                )
                documents.append(doc)

            logger.info(f"📦 Cache chargé: {len(documents)} documents")
            return documents

        except Exception as e:
            logger.error(f"[ERROR] Erreur chargement cache: {e}")
            return []

    def _extract_keywords(self, query: str) -> List[str]:
        """Extrait les mots-clés de la requête"""
        import re

        query = re.sub(r'[^\w\s]', '', query.lower())
        words = query.split()

        # Stopwords français
        stopwords = {
            'le', 'la', 'les', 'de', 'des', 'du', 'et', 'en', 'un', 'une',
            'à', 'au', 'aux', 'dans', 'sur', 'par', 'pour', 'avec', 'sans'
        }

        keywords = [word for word in words if len(word) > 2 and word not in stopwords]
        return keywords

    def _get_country_name(self, country_code: str) -> str:
        """Récupère le nom complet d'un pays depuis son code"""
        country_names = {
            'FR': 'France',
            'DE': 'Allemagne',
            'IT': 'Italie',
            'ES': 'Espagne',
            'GB': 'Royaume-Uni',
            'US': 'États-Unis',
            'CN': 'Chine',
            'JP': 'Japon',
            'BE': 'Belgique',
            'NL': 'Pays-Bas',
            'SE': 'Suède',
            'DK': 'Danemark',
            'NO': 'Norvège',
            'FI': 'Finlande',
            'PL': 'Pologne',
            'PT': 'Portugal',
            'GR': 'Grèce',
            'AT': 'Autriche',
            'CH': 'Suisse',
            'IE': 'Irlande'
        }
        return country_names.get(country_code.upper(), country_code)


# Fonction factory
def create_demographic_indexer(db_manager, cache_dir: str = None):
    """Crée une instance du DemographicIndexer"""
    return DemographicIndexer(db_manager=db_manager, cache_dir=cache_dir)
