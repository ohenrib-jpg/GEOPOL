"""
Connecteur UCDP (Uppsala Conflict Data Program) - Données de conflits armés
Source: https://ucdp.uu.se/
API: https://ucdpapi.uu.se/
Données disponibles: Conflits armés, victimes, acteurs, localisations
Alternative open source à ACLED, maintenue par Université d'Uppsala
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import csv
from io import StringIO

logger = logging.getLogger(__name__)

# Import du cache intelligent
try:
    from .security_cache import cached_connector_method
    CACHE_ENABLED = True
    logger.debug(f"[UCDP] Cache intelligent activé: CACHE_ENABLED={CACHE_ENABLED}")
except ImportError as e:
    CACHE_ENABLED = False
    cached_connector_method = lambda source: lambda func: func  # Décorateur factice
    logger.warning(f"[UCDP] Cache intelligent désactivé: {e}")


class UCDPConnector:
    """
    Connecteur pour l'API UCDP (Uppsala Conflict Data Program)
    Données de conflits armés avec victimes géolocalisées
    """

    # API UCDP endpoints (public API)
    # Documentation: https://ucdp.uu.se/apidocs/
    # Note: L'API UCDP utilise maintenant des versions différentes par endpoint
    BASE_URL = "https://ucdpapi.pcr.uu.se/api"

    # Versions par dataset (mises à jour janvier 2026)
    # GED (Georeferenced Event Dataset): version 24.1
    # UCDP/PRIO Armed Conflict Dataset: version 24.1
    GED_VERSION = "24.1"
    ACD_VERSION = "24.1"

    # Endpoints principaux avec versions correctes
    ENDPOINTS = {
        'conflicts': f"/ucdpprioconflict/{ACD_VERSION}",
        'events': f"/gedevents/{GED_VERSION}",
        'dyadic': f"/dyadic/{ACD_VERSION}",
        'nonstate': f"/nonstate/{ACD_VERSION}",
        'onesided': f"/onesided/{ACD_VERSION}",
        'battledeaths': f"/battledeaths/{ACD_VERSION}",
        # Nouveau endpoint candidate (données préliminaires)
        'candidate': "/candidate/gedevents"
    }

    # Configuration de timeout et retry
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # secondes

    # Types de conflits UCDP
    CONFLICT_TYPES = {
        1: 'Extra-state conflict',
        2: 'Interstate conflict',
        3: 'Internal conflict',
        4: 'Internationalized internal conflict'
    }

    def __init__(self, timeout: int = None, max_retries: int = None):
        """
        Args:
            timeout: Timeout en secondes pour les requêtes (défaut: 30)
            max_retries: Nombre maximum de tentatives (défaut: 3)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0 (+https://github.com/geopol)',
            'Accept': 'application/json'
        })
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries or self.MAX_RETRIES
        self.circuit_breaker = {'failures': 0, 'last_failure': None, 'open': False}
        # Cache géré par security_cache.py (cache intelligent externe)
        # self.data_cache = {}  # Ancien cache interne non utilisé

    def _check_circuit_breaker(self) -> bool:
        """
        Vérifie si le circuit breaker est ouvert
        Returns:
            True si la requête peut continuer, False si circuit ouvert
        """
        if not self.circuit_breaker['open']:
            return True

        # Circuit ouvert: vérifier si on peut réessayer (après 60 secondes)
        if self.circuit_breaker['last_failure']:
            elapsed = (datetime.now() - self.circuit_breaker['last_failure']).total_seconds()
            if elapsed > 60:  # Réessayer après 1 minute
                logger.info("[UCDP] Circuit breaker: tentative de récupération")
                self.circuit_breaker['open'] = False
                self.circuit_breaker['failures'] = 0
                return True

        logger.warning("[UCDP] Circuit breaker ouvert - requête bloquée")
        return False

    def _record_failure(self):
        """Enregistre un échec pour le circuit breaker"""
        self.circuit_breaker['failures'] += 1
        self.circuit_breaker['last_failure'] = datetime.now()

        # Ouvrir le circuit après 3 échecs consécutifs
        if self.circuit_breaker['failures'] >= 3:
            self.circuit_breaker['open'] = True
            logger.error("[UCDP] Circuit breaker ouvert après 3 échecs")

    def _record_success(self):
        """Enregistre un succès - réinitialise le circuit breaker"""
        if self.circuit_breaker['failures'] > 0:
            logger.info("[UCDP] Circuit breaker: récupération réussie")
        self.circuit_breaker['failures'] = 0
        self.circuit_breaker['open'] = False

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Effectue une requête à l'API UCDP avec gestion d'erreurs, retry et circuit breaker
        """
        # Vérifier le circuit breaker
        if not self._check_circuit_breaker():
            return {
                'success': False,
                'error': 'Circuit breaker ouvert - service temporairement indisponible'
            }

        # Construire l'URL - BASE_URL inclut déjà /api
        url = f"{self.BASE_URL}{endpoint}"

        # Nettoyer les paramètres (UCDP n'accepte pas certains formats)
        if params:
            # UCDP utilise des formats de date différents selon l'endpoint
            clean_params = {}
            for key, value in params.items():
                if value is not None:
                    clean_params[key] = value
            params = clean_params
        last_error = None

        # Retry logic
        for attempt in range(self.max_retries):
            try:
                logger.info(f"[UCDP] Requête {endpoint} (tentative {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()

                data = response.json()
                self._record_success()
                return {'success': True, 'data': data}

            except requests.exceptions.Timeout as e:
                last_error = f"Timeout après {self.timeout}s: {e}"
                logger.warning(f"[UCDP] Timeout {endpoint} (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except requests.exceptions.ConnectionError as e:
                last_error = f"Erreur de connexion: {e}"
                logger.warning(f"[UCDP] Erreur connexion {endpoint} (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except requests.exceptions.HTTPError as e:
                # Ne pas retry sur 4xx (erreur client)
                if response.status_code < 500:
                    last_error = f"Erreur HTTP {response.status_code}: {e}"
                    logger.error(f"[UCDP] Erreur HTTP {response.status_code} - pas de retry")
                    break
                last_error = f"Erreur serveur {response.status_code}: {e}"
                logger.warning(f"[UCDP] Erreur serveur {endpoint} (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except json.JSONDecodeError as e:
                last_error = f"Réponse JSON invalide: {e}"
                logger.error(f"[UCDP] Erreur JSON {endpoint}: {e}")
                break  # Ne pas retry sur erreur JSON

            except Exception as e:
                last_error = f"Erreur inattendue: {e}"
                logger.error(f"[UCDP] Erreur inattendue {endpoint}: {e}")
                break

        # Toutes les tentatives ont échoué
        self._record_failure()
        logger.error(f"[UCDP] Échec après {self.max_retries} tentatives: {last_error}")
        return {'success': False, 'error': last_error}

    @cached_connector_method('ucdp')
    def get_recent_conflicts(self, days: int = 30, limit: int = 50) -> Dict[str, Any]:
        """
        Récupère les conflits récents avec victimes.
        L'API UCDP GED retourne les données chronologiquement depuis 2002,
        donc nous récupérons les dernières pages pour avoir les données récentes.
        """
        try:
            # Étape 1: Récupérer le nombre total de pages
            params = {'pagesize': min(limit, 100)}
            logger.info(f"[UCDP] Récupération des conflits récents (limit={limit})")

            result = self._make_request(self.ENDPOINTS['events'], params)

            if not result['success']:
                logger.warning("[UCDP] API indisponible, tentative CSV public...")
                return self._get_public_csv_data(days, limit)

            raw_data = result.get('data', {})
            total_pages = raw_data.get('TotalPages', 0)
            total_count = raw_data.get('TotalCount', 0)

            if total_pages == 0:
                logger.warning("[UCDP] Aucune donnée disponible")
                return self._get_fallback_data()

            # Étape 2: Récupérer les dernières pages (données les plus récentes)
            # Les données UCDP sont ordonnées chronologiquement, les plus récentes sont à la fin
            pages_to_fetch = min(3, total_pages)  # Récupérer les 3 dernières pages max
            all_events = []

            for page_offset in range(pages_to_fetch):
                page_num = total_pages - page_offset - 1
                if page_num < 0:
                    break

                params = {
                    'pagesize': min(limit, 100),
                    'page': page_num
                }

                page_result = self._make_request(self.ENDPOINTS['events'], params)
                if page_result.get('success'):
                    page_data = page_result.get('data', {})
                    events = page_data.get('Result', [])
                    if events:
                        all_events.extend(events)
                        logger.info(f"[UCDP] Page {page_num}: {len(events)} événements")

                if len(all_events) >= limit:
                    break

            # Limiter et formater
            all_events = all_events[:limit]
            formatted_events = self._format_events(all_events)

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'UCDP GED API',
                'total_events': len(formatted_events),
                'total_available': total_count,
                'events': formatted_events,
                'statistics': self._calculate_conflict_stats(formatted_events),
                'query': {'days': days, 'limit': limit}
            }

        except Exception as e:
            logger.error(f"[UCDP] Erreur get_recent_conflicts: {e}")
            return self._get_fallback_data()

    def _get_fallback_data(self) -> Dict[str, Any]:
        """Retourne des données de fallback en cas d'erreur"""
        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'source': 'Fallback',
            'total_events': 0,
            'events': [],
            'statistics': {'total': 0, 'by_country': {}, 'by_type': {}, 'total_fatalities': 0},
            'message': 'Données UCDP temporairement indisponibles'
        }

    @cached_connector_method('ucdp')
    def get_conflict_summary(self, year: int = None) -> Dict[str, Any]:
        """
        Récupère un résumé des conflits pour une année
        """
        if year is None:
            year = datetime.now().year - 1  # Dernière année complète

        try:
            params = {'year': year}
            result = self._make_request(self.ENDPOINTS['conflicts'], params)

            if not result['success']:
                return {
                    'success': False,
                    'error': result['error'],
                    'timestamp': datetime.now().isoformat()
                }

            conflicts = result['data'].get('conflicts', [])

            summary = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'UCDP Conflict API',
                'year': year,
                'total_conflicts': len(conflicts),
                'conflicts_by_type': self._count_conflicts_by_type(conflicts),
                'conflicts_by_region': self._count_conflicts_by_region(conflicts),
                'total_fatalities': sum(c.get('best_fatality_estimate', 0) for c in conflicts),
                'active_conflicts': [c for c in conflicts if c.get('ongoing', False)]
            }

            return summary

        except Exception as e:
            logger.error(f"[UCDP] Erreur get_conflict_summary: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _format_events(self, events: List[Dict]) -> List[Dict[str, Any]]:
        """Formate les événements UCDP au format GEOPOL"""
        formatted = []

        for event in events:
            try:
                # Informations de base
                event_id = event.get('id', '')
                date_start = event.get('date_start', '')
                date_end = event.get('date_end', '')

                # Localisation
                location = event.get('location', '')
                country = event.get('country', '')
                latitude = event.get('latitude')
                longitude = event.get('longitude')

                # Type et acteurs
                event_type = event.get('type_of_violence', '')
                actor1 = event.get('actor1', '')
                actor2 = event.get('actor2', '')

                # Victimes
                fatalities = event.get('best_fatality_estimate', 0)

                # Source
                source = event.get('source', 'UCDP')

                formatted.append({
                    'id': event_id,
                    'date': date_start[:10] if date_start else 'Unknown',
                    'country': country,
                    'location': location,
                    'latitude': latitude,
                    'longitude': longitude,
                    'event_type': self._translate_event_type(event_type),
                    'actors': f"{actor1} vs {actor2}" if actor1 and actor2 else actor1 or actor2 or 'Unknown',
                    'fatalities': fatalities,
                    'source': source,
                    'ucdp_data': True,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.warning(f"[UCDP] Erreur format événement: {e}")
                continue

        return formatted

    def _translate_event_type(self, event_type_code: str) -> str:
        """Traduit le type d'événement UCDP"""
        type_mapping = {
            '1': 'State-based conflict',
            '2': 'Non-state conflict',
            '3': 'One-sided violence'
        }
        return type_mapping.get(event_type_code, event_type_code)

    def _calculate_conflict_stats(self, events: List[Dict]) -> Dict[str, Any]:
        """Calcule les statistiques sur les conflits"""
        if not events:
            return {'total': 0, 'by_country': {}, 'by_type': {}, 'total_fatalities': 0}

        by_country = {}
        by_type = {}
        total_fatalities = 0

        for event in events:
            country = event.get('country', 'Unknown')
            event_type = event.get('event_type', 'Unknown')
            fatalities = event.get('fatalities', 0)

            by_country[country] = by_country.get(country, 0) + 1
            by_type[event_type] = by_type.get(event_type, 0) + 1
            total_fatalities += fatalities

        return {
            'total': len(events),
            'by_country': dict(sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:10]),
            'by_type': by_type,
            'total_fatalities': total_fatalities,
            'avg_fatalities': round(total_fatalities / len(events), 2) if events else 0
        }

    def _count_conflicts_by_type(self, conflicts: List[Dict]) -> Dict[str, int]:
        """Compte les conflits par type"""
        counts = {}
        for conflict in conflicts:
            conflict_type = conflict.get('type_of_conflict', 0)
            type_name = self.CONFLICT_TYPES.get(conflict_type, f'Type {conflict_type}')
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts

    def _count_conflicts_by_region(self, conflicts: List[Dict]) -> Dict[str, int]:
        """Compte les conflits par région"""
        region_mapping = {
            'Africa': ['Sub-Saharan Africa', 'North Africa'],
            'Asia': ['South Asia', 'Southeast Asia', 'East Asia', 'Central Asia'],
            'Middle East': ['Middle East'],
            'Europe': ['Europe'],
            'Americas': ['North America', 'South America', 'Central America']
        }

        counts = {region: 0 for region in region_mapping.keys()}

        for conflict in conflicts:
            region_name = conflict.get('region', '')
            for region, subregions in region_mapping.items():
                if region_name in subregions:
                    counts[region] += 1
                    break
            else:
                counts['Other'] = counts.get('Other', 0) + 1

        return counts

    def _get_public_csv_data(self, days: int, limit: int) -> Dict[str, Any]:
        """
        Tente de récupérer des données depuis les CSV publics UCDP
        Dernier recours si API indisponible
        """
        try:
            # URL des données publiques GED (dernière version)
            csv_url = "https://ucdp.uu.se/downloads/ged/ged231.csv"

            logger.info(f"[UCDP CSV] Téléchargement {csv_url}")
            response = requests.get(csv_url, timeout=60)
            response.raise_for_status()

            # Lire CSV
            csv_data = StringIO(response.text)
            reader = csv.DictReader(csv_data)

            events = []
            for row in reader:
                try:
                    event_date = row.get('date_start', '')
                    if not event_date:
                        continue

                    # Filtrer par date (approximatif)
                    event_year = int(event_date[:4]) if len(event_date) >= 4 else 0
                    current_year = datetime.now().year

                    if current_year - event_year <= 1:  # Dernière année
                        events.append(row)

                    if len(events) >= limit:
                        break

                except Exception as e:
                    logger.warning(f"[UCDP CSV] Erreur ligne: {e}")
                    continue

            formatted_events = self._format_events(events)

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'UCDP Public CSV (GED)',
                'total_events': len(events),
                'events': formatted_events,
                'statistics': self._calculate_conflict_stats(formatted_events),
                'query': {'days': days, 'limit': limit},
                'note': 'Données CSV publiques (dernière année disponible)'
            }

        except Exception as e:
            logger.error(f"[UCDP CSV] Erreur: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'message': 'API UCDP et CSV public indisponibles'
            }


def get_ucdp_connector() -> UCDPConnector:
    """Factory pour obtenir le connecteur UCDP"""
    return UCDPConnector()


__all__ = ['UCDPConnector', 'get_ucdp_connector']