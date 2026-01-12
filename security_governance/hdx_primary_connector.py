"""
Connecteur principal UN OCHA HDX (Humanitarian Data Exchange)
Source principale de données conflits/humanitaires - sans authentification
Étend le connecteur de base avec des fonctionnalités avancées
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from .ocha_hdx_connector import OchaHdxConnector

logger = logging.getLogger(__name__)


class HDXPrimaryConnector(OchaHdxConnector):
    """
    Connecteur HDX principal avec fonctionnalités avancées
    Pour analyse géopolitique et monitoring des conflits
    """

    # Catégories de crises avec mots-clés associés
    CRISIS_CATEGORIES = {
        'armed_conflict': ['conflict', 'war', 'violence', 'battle', 'armed', 'combat'],
        'displacement': ['displacement', 'refugees', 'idp', 'migration', 'fleeing'],
        'humanitarian': ['humanitarian', 'aid', 'relief', 'assistance', 'response'],
        'food_security': ['food', 'famine', 'nutrition', 'hunger', 'malnutrition'],
        'health': ['health', 'disease', 'covid', 'epidemic', 'outbreak', 'hospital'],
        'natural_disaster': ['disaster', 'earthquake', 'flood', 'drought', 'cyclone'],
        'climate': ['climate', 'environment', 'temperature', 'rainfall', 'weather'],
        'education': ['education', 'school', 'students', 'learning'],
        'protection': ['protection', 'rights', 'violence', 'abuse', 'exploitation']
    }

    # Régions prioritaires pour monitoring géopolitique
    PRIORITY_REGIONS = [
        'Ukraine', 'Gaza', 'Sudan', 'Syria', 'Yemen', 'Afghanistan',
        'Myanmar', 'Ethiopia', 'Democratic Republic of Congo', 'Somalia',
        'Haiti', 'Venezuela', 'Mali', 'Niger', 'Burkina Faso'
    ]

    def __init__(self):
        """Initialise le connecteur HDX principal"""
        super().__init__()
        self.cache = {}
        self.cache_ttl = 3600  # 1 heure de cache

    def get_crisis_indicators(self, country: str = None) -> Dict[str, Any]:
        """
        Récupère des indicateurs de crise pour un pays ou globalement

        Args:
            country: Nom du pays (optionnel)

        Returns:
            Dict avec indicateurs structurés
        """
        try:
            if country:
                result = self.get_country_data(country)
                if not result.get('success'):
                    return result

                datasets = result.get('datasets', [])
                categories = result.get('by_category', {})
            else:
                result = self.get_summary()
                if not result.get('success'):
                    return result

                # Récupérer datasets des crises récentes
                crisis_result = self.get_crisis_data()
                datasets = crisis_result.get('datasets', []) if crisis_result.get('success') else []
                categories = {}

            # Calculer les indicateurs
            indicators = {
                'total_datasets': len(datasets),
                'crisis_severity': self._calculate_crisis_severity(datasets),
                'humanitarian_needs': self._calculate_humanitarian_needs(datasets),
                'temporal_trend': self._analyze_temporal_trend(datasets),
                'geographic_coverage': self._analyze_geographic_coverage(datasets),
                'data_freshness': self._calculate_data_freshness(datasets)
            }

            # Ajouter des métriques par catégorie
            if categories:
                indicators['category_distribution'] = {
                    cat: len(items) for cat, items in categories.items()
                }

            logger.info(f"[OK] Crisis indicators calculated: {len(datasets)} datasets")

            return {
                'success': True,
                'country': country,
                'indicators': indicators,
                'timestamp': datetime.now().isoformat(),
                'source': 'UN OCHA HDX'
            }

        except Exception as e:
            logger.error(f"[ERROR] Crisis indicators error: {e}")
            return {
                'success': False,
                'error': str(e),
                'country': country
            }

    def get_conflict_events(self, days: int = 30, limit: int = 100) -> Dict[str, Any]:
        """
        Récupère les événements de conflit récents (similaire à ACLED)

        Args:
            days: Nombre de jours à couvrir
            limit: Nombre maximum de datasets à analyser

        Returns:
            List d'événements de conflit structurés
        """
        try:
            # Rechercher datasets de conflits
            result = self.search_datasets(
                query='conflict OR violence OR war OR armed',
                limit=limit
            )

            if not result.get('success'):
                return result

            datasets = result.get('datasets', [])

            # Filtrer par date récente
            recent_datasets = []
            cutoff_date = datetime.now() - timedelta(days=days)

            for ds in datasets:
                ds_date = ds.get('dataset_date')
                updated = ds.get('updated')

                # Essayer de parser la date
                date_str = ds_date or updated
                if date_str:
                    try:
                        ds_datetime = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        if ds_datetime >= cutoff_date:
                            recent_datasets.append(ds)
                    except:
                        # Si parsing échoue, inclure quand même
                        recent_datasets.append(ds)
                else:
                    # Pas de date, inclure par défaut
                    recent_datasets.append(ds)

            # Structurer comme événements ACLED
            events = []
            for ds in recent_datasets[:50]:  # Limiter à 50 événements
                event = {
                    'id': ds.get('id'),
                    'title': ds.get('title'),
                    'description': ds.get('notes', '')[:200],
                    'dataset_date': ds.get('dataset_date'),
                    'updated': ds.get('updated'),
                    'organization': ds.get('organization'),
                    'tags': ds.get('tags', []),
                    'url': ds.get('url'),
                    'type': self._classify_event_type(ds),
                    'country': self._extract_country(ds),
                    'location': self._extract_location(ds),
                    'severity': self._estimate_severity(ds)
                }
                events.append(event)

            logger.info(f"[OK] Conflict events: {len(events)} events from {len(recent_datasets)} datasets")

            return {
                'success': True,
                'events_count': len(events),
                'events': events,
                'period_days': days,
                'timestamp': datetime.now().isoformat(),
                'source': 'UN OCHA HDX'
            }

        except Exception as e:
            logger.error(f"[ERROR] Conflict events error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_priority_regions_status(self) -> Dict[str, Any]:
        """
        Récupère le statut des régions prioritaires
        """
        try:
            regions_status = {}

            for region in self.PRIORITY_REGIONS[:10]:  # Limiter à 10 pour performance
                result = self.get_country_data(region)

                if result.get('success'):
                    datasets = result.get('datasets', [])
                    categories = result.get('categories', {})

                    # Calculer un score de crise
                    crisis_score = 0
                    if 'conflict' in categories:
                        crisis_score += categories['conflict'] * 3
                    if 'displacement' in categories:
                        crisis_score += categories['displacement'] * 2
                    if 'food_security' in categories:
                        crisis_score += categories['food_security'] * 2

                    # Déterminer le statut
                    if crisis_score > 20:
                        status = 'critical'
                    elif crisis_score > 10:
                        status = 'high'
                    elif crisis_score > 5:
                        status = 'medium'
                    else:
                        status = 'low'

                    regions_status[region] = {
                        'datasets_count': len(datasets),
                        'crisis_score': crisis_score,
                        'status': status,
                        'categories': categories,
                        'latest_update': datasets[0].get('updated') if datasets else None
                    }

            logger.info(f"[OK] Priority regions status: {len(regions_status)} regions")

            return {
                'success': True,
                'regions': regions_status,
                'timestamp': datetime.now().isoformat(),
                'source': 'UN OCHA HDX'
            }

        except Exception as e:
            logger.error(f"[ERROR] Priority regions error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_humanitarian_access_map(self) -> Dict[str, Any]:
        """
        Génère une carte d'accès humanitaire par pays
        """
        try:
            # Récupérer données d'accès humanitaire
            result = self.get_humanitarian_access()

            if not result.get('success'):
                return result

            datasets = result.get('datasets', [])

            # Analyser par pays
            country_access = {}
            for ds in datasets:
                country = self._extract_country(ds)
                if country:
                    if country not in country_access:
                        country_access[country] = {
                            'datasets': [],
                            'constraints': []
                        }
                    country_access[country]['datasets'].append(ds)

                    # Extraire les contraintes mentionnées
                    constraints = self._extract_access_constraints(ds)
                    country_access[country]['constraints'].extend(constraints)

            logger.info(f"[OK] Humanitarian access map: {len(country_access)} countries")

            return {
                'success': True,
                'country_access': country_access,
                'total_datasets': len(datasets),
                'timestamp': datetime.now().isoformat(),
                'source': 'UN OCHA HDX'
            }

        except Exception as e:
            logger.error(f"[ERROR] Humanitarian access map error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_daily_briefing(self) -> Dict[str, Any]:
        """
        Génère un briefing quotidien des crises mondiales
        """
        try:
            # Récupérer données récentes
            conflict_events = self.get_conflict_events(days=1, limit=20)
            priority_regions = self.get_priority_regions_status()
            humanitarian_access = self.get_humanitarian_access()

            # Compiler le briefing
            briefing = {
                'date': datetime.now().isoformat(),
                'conflict_events': conflict_events.get('events_count', 0) if conflict_events.get('success') else 0,
                'priority_regions': priority_regions.get('regions', {}) if priority_regions.get('success') else {},
                'humanitarian_access': humanitarian_access.get('datasets_count', 0) if humanitarian_access.get('success') else 0,
                'key_updates': []
            }

            # Ajouter les mises à jour clés
            if conflict_events.get('success'):
                events = conflict_events.get('events', [])[:5]
                for event in events:
                    briefing['key_updates'].append({
                        'type': 'conflict',
                        'title': event.get('title'),
                        'country': event.get('country'),
                        'severity': event.get('severity')
                    })

            logger.info(f"[OK] Daily briefing generated")

            return {
                'success': True,
                'briefing': briefing,
                'timestamp': datetime.now().isoformat(),
                'source': 'UN OCHA HDX'
            }

        except Exception as e:
            logger.error(f"[ERROR] Daily briefing error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    # ========== MÉTHODES D'ASSISTANCE PRIVÉES ==========

    def _calculate_crisis_severity(self, datasets: List[Dict]) -> str:
        """Calcule la sévérité globale d'une crise"""
        if not datasets:
            return 'low'

        # Analyse basique basée sur les tags
        severity_keywords = {
            'critical': ['emergency', 'catastrophe', 'crisis', 'war', 'conflict'],
            'high': ['severe', 'major', 'disaster', 'violence', 'attack'],
            'medium': ['moderate', 'escalation', 'tension', 'protest'],
            'low': ['monitoring', 'alert', 'watch', 'situation']
        }

        severity_scores = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

        for ds in datasets:
            text = ' '.join(ds.get('tags', [])).lower() + ' ' + ds.get('title', '').lower()
            for severity, keywords in severity_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        severity_scores[severity] += 1
                        break

        # Retourner la sévérité dominante
        return max(severity_scores.items(), key=lambda x: x[1])[0]

    def _calculate_humanitarian_needs(self, datasets: List[Dict]) -> Dict[str, int]:
        """Calcule les besoins humanitaires par catégorie"""
        needs = {
            'food': 0,
            'shelter': 0,
            'health': 0,
            'protection': 0,
            'water': 0,
            'education': 0
        }

        for ds in datasets:
            text = ' '.join(ds.get('tags', [])).lower() + ' ' + ds.get('title', '').lower()

            if any(word in text for word in ['food', 'nutrition', 'hunger']):
                needs['food'] += 1
            if any(word in text for word in ['shelter', 'housing', 'camp']):
                needs['shelter'] += 1
            if any(word in text for word in ['health', 'medical', 'hospital']):
                needs['health'] += 1
            if any(word in text for word in ['protection', 'rights', 'violence']):
                needs['protection'] += 1
            if any(word in text for word in ['water', 'sanitation', 'watsan']):
                needs['water'] += 1
            if any(word in text for word in ['education', 'school', 'learning']):
                needs['education'] += 1

        return needs

    def _analyze_temporal_trend(self, datasets: List[Dict]) -> str:
        """Analyse la tendance temporelle"""
        if len(datasets) < 2:
            return 'stable'

        # Trier par date
        dated_datasets = []
        for ds in datasets:
            date_str = ds.get('updated') or ds.get('dataset_date')
            if date_str:
                try:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    dated_datasets.append((date, ds))
                except:
                    pass

        if len(dated_datasets) < 2:
            return 'stable'

        # Vérifier si augmentation récente
        dated_datasets.sort(key=lambda x: x[0])
        recent_count = len([d for d in dated_datasets if d[0] > datetime.now() - timedelta(days=7)])
        older_count = len(dated_datasets) - recent_count

        if recent_count > older_count * 0.5:  # Plus de 50% des datasets sont récents
            return 'increasing'
        elif recent_count < older_count * 0.2:  # Moins de 20% récents
            return 'decreasing'
        else:
            return 'stable'

    def _analyze_geographic_coverage(self, datasets: List[Dict]) -> List[str]:
        """Extrait la couverture géographique"""
        countries = set()
        for ds in datasets:
            country = self._extract_country(ds)
            if country:
                countries.add(country)
        return list(countries)[:10]  # Limiter à 10 pays

    def _calculate_data_freshness(self, datasets: List[Dict]) -> str:
        """Calcule la fraîcheur des données"""
        if not datasets:
            return 'old'

        latest_date = None
        for ds in datasets:
            date_str = ds.get('updated') or ds.get('dataset_date')
            if date_str:
                try:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    if latest_date is None or date > latest_date:
                        latest_date = date
                except:
                    pass

        if not latest_date:
            return 'unknown'

        days_diff = (datetime.now() - latest_date).days

        if days_diff < 1:
            return 'very_fresh'
        elif days_diff < 7:
            return 'fresh'
        elif days_diff < 30:
            return 'recent'
        else:
            return 'old'

    def _classify_event_type(self, dataset: Dict) -> str:
        """Classifie le type d'événement"""
        text = ' '.join(dataset.get('tags', [])).lower() + ' ' + dataset.get('title', '').lower()

        for category, keywords in self.CRISIS_CATEGORIES.items():
            if any(keyword in text for keyword in keywords):
                return category

        return 'other'

    def _extract_country(self, dataset: Dict) -> Optional[str]:
        """Extrait le pays d'un dataset"""
        # Chercher dans les tags
        tags = dataset.get('tags', [])
        for tag in tags:
            if len(tag) > 2 and tag[0].isupper():  # Nom de pays probable
                # Liste de pays courants
                common_countries = self.PRIORITY_REGIONS
                for country in common_countries:
                    if country.lower() in tag.lower():
                        return country

        # Chercher dans le titre
        title = dataset.get('title', '').lower()
        for country in self.PRIORITY_REGIONS:
            if country.lower() in title:
                return country

        return None

    def _extract_location(self, dataset: Dict) -> Optional[str]:
        """Extrait la localisation spécifique"""
        title = dataset.get('title', '')
        # Extraire la partie après le dernier tiret ou deux-points
        if ' - ' in title:
            return title.split(' - ')[-1].strip()
        elif ': ' in title:
            return title.split(': ')[-1].strip()
        return None

    def _estimate_severity(self, dataset: Dict) -> str:
        """Estime la sévérité d'un événement"""
        text = ' '.join(dataset.get('tags', [])).lower() + ' ' + dataset.get('title', '').lower()

        if any(word in text for word in ['emergency', 'crisis', 'catastrophe', 'war']):
            return 'high'
        elif any(word in text for word in ['severe', 'major', 'violence', 'attack']):
            return 'medium'
        elif any(word in text for word in ['alert', 'warning', 'tension']):
            return 'low'
        else:
            return 'unknown'

    def _extract_access_constraints(self, dataset: Dict) -> List[str]:
        """Extrait les contraintes d'accès humanitaire"""
        constraints = []
        text = ' '.join(dataset.get('tags', [])).lower() + ' ' + dataset.get('title', '').lower()

        constraint_keywords = {
            'restrictions': ['restriction', 'limit', 'constraint', 'block'],
            'insecurity': ['insecurity', 'violence', 'attack', 'threat'],
            'bureaucracy': ['bureaucracy', 'permit', 'authorization', 'paperwork'],
            'logistics': ['logistics', 'transport', 'accessibility', 'remote']
        }

        for constraint_type, keywords in constraint_keywords.items():
            if any(keyword in text for keyword in keywords):
                constraints.append(constraint_type)

        return constraints


def get_hdx_primary_connector() -> HDXPrimaryConnector:
    """Factory pour obtenir le connecteur HDX principal"""
    return HDXPrimaryConnector()


__all__ = ['HDXPrimaryConnector', 'get_hdx_primary_connector']