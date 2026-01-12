"""
Connecteur World Bank - Control of Corruption
Source: https://api.worldbank.org/v2
API publique sans authentification requise

Indicateurs:
- CC.EST: Control of Corruption Estimate (governance indicator)
- Score: -2.5 (weak) à +2.5 (strong)

Alternative au CPI de Transparency International
Données disponibles depuis 1996, mises à jour annuellement
"""

import requests
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

# Import du cache intelligent
try:
    from .security_cache import cached_connector_method
    CACHE_ENABLED = True
    logger.debug(f"[WORLD BANK] Cache intelligent activé: CACHE_ENABLED={CACHE_ENABLED}")
except ImportError as e:
    CACHE_ENABLED = False
    cached_connector_method = lambda source: lambda func: func  # Décorateur factice
    logger.warning(f"[WORLD BANK] Cache intelligent désactivé: {e}")


class WorldBankCorruptionConnector:
    """
    Connecteur pour les données de corruption de la Banque Mondiale
    Utilise l'indicateur CC.EST (Control of Corruption Estimate)
    """

    BASE_URL = "https://api.worldbank.org/v2"
    INDICATOR = "CC.EST"  # Control of Corruption Estimate
    FORMAT = "json"  # json ou xml

    # Configuration de timeout et retry
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # secondes

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
        self.country_cache = {}
        self.cache_timestamp = None

    def _check_circuit_breaker(self) -> bool:
        """Vérifie si le circuit breaker est ouvert"""
        if not self.circuit_breaker['open']:
            return True

        # Circuit ouvert: vérifier si on peut réessayer (après 60 secondes)
        if self.circuit_breaker['last_failure']:
            elapsed = (datetime.now() - self.circuit_breaker['last_failure']).total_seconds()
            if elapsed > 60:
                logger.info("[WORLD BANK] Circuit breaker: tentative de récupération")
                self.circuit_breaker['open'] = False
                self.circuit_breaker['failures'] = 0
                return True

        logger.warning("[WORLD BANK] Circuit breaker ouvert - requête bloquée")
        return False

    def _record_failure(self):
        """Enregistre un échec pour le circuit breaker"""
        self.circuit_breaker['failures'] += 1
        self.circuit_breaker['last_failure'] = datetime.now()
        if self.circuit_breaker['failures'] >= 3:
            self.circuit_breaker['open'] = True
            logger.error("[WORLD BANK] Circuit breaker ouvert après 3 échecs")

    def _record_success(self):
        """Enregistre un succès - réinitialise le circuit breaker"""
        if self.circuit_breaker['failures'] > 0:
            logger.info("[WORLD BANK] Circuit breaker: récupération réussie")
        self.circuit_breaker['failures'] = 0
        self.circuit_breaker['open'] = False

    def _make_request(self, url: str, params: Dict = None) -> Dict[str, Any]:
        """
        Effectue une requête avec gestion d'erreurs, retry et circuit breaker
        """
        # Vérifier le circuit breaker
        if not self._check_circuit_breaker():
            return {
                'success': False,
                'error': 'Circuit breaker ouvert - service temporairement indisponible'
            }

        last_error = None

        # Retry logic
        for attempt in range(self.max_retries):
            try:
                logger.info(f"[WORLD BANK] Requête {url} (tentative {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()

                data = response.json()
                self._record_success()
                return {'success': True, 'data': data}

            except requests.exceptions.Timeout as e:
                last_error = f"Timeout après {self.timeout}s: {e}"
                logger.warning(f"[WORLD BANK] Timeout (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except requests.exceptions.ConnectionError as e:
                last_error = f"Erreur de connexion: {e}"
                logger.warning(f"[WORLD BANK] Erreur connexion (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except requests.exceptions.HTTPError as e:
                # Ne pas retry sur 4xx (erreur client)
                if response.status_code < 500:
                    last_error = f"Erreur HTTP {response.status_code}: {e}"
                    logger.error(f"[WORLD BANK] Erreur HTTP {response.status_code} - pas de retry")
                    break
                last_error = f"Erreur serveur {response.status_code}: {e}"
                logger.warning(f"[WORLD BANK] Erreur serveur (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except json.JSONDecodeError as e:
                last_error = f"Réponse JSON invalide: {e}"
                logger.error(f"[WORLD BANK] Erreur JSON: {e}")
                break

            except Exception as e:
                last_error = f"Erreur inattendue: {e}"
                logger.error(f"[WORLD BANK] Erreur inattendue: {e}")
                break

        # Toutes les tentatives ont échoué
        self._record_failure()
        logger.error(f"[WORLD BANK] Échec après {self.max_retries} tentatives: {last_error}")
        return {'success': False, 'error': last_error}

    @cached_connector_method('worldbank_corruption')
    def get_corruption_data(self, year: int = 2022, limit: int = 50) -> Dict[str, Any]:
        """
        Récupère les données de corruption pour une année spécifique
        Args:
            year: Année des données (1996-2023)
            limit: Nombre max de pays
        Returns:
            Dict avec résultats
        """
        try:
            # URL API World Bank
            url = f"{self.BASE_URL}/country/all/indicator/{self.INDICATOR}"
            params = {
                'format': self.FORMAT,
                'date': year,
                'per_page': min(limit, 1000),  # Max 1000
                'page': 1
            }

            logger.info(f"[WORLD BANK] Récupération données corruption {year}")

            # Utiliser la méthode avec retry et circuit breaker
            result = self._make_request(url, params)

            if not result.get('success'):
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'timestamp': datetime.now().isoformat()
                }

            data = result['data']

            # Vérifier le format de réponse World Bank
            # Format attendu: [metadata, [data_items]] ou juste [data_items]
            if not data:
                logger.warning("[WORLD BANK] Réponse vide")
                return {
                    'success': False,
                    'error': 'Réponse vide de World Bank API',
                    'timestamp': datetime.now().isoformat()
                }

            # Gérer différents formats de réponse
            if isinstance(data, list) and len(data) >= 2:
                # Format standard: [metadata, data]
                metadata = data[0] if isinstance(data[0], dict) else {'total': 0}
                indicators_data = data[1] if len(data) > 1 else []
            elif isinstance(data, list) and len(data) == 1:
                # Format alternatif: [data] sans métadonnées
                metadata = {'total': len(data[0]) if isinstance(data[0], list) else 1}
                indicators_data = data[0] if isinstance(data[0], list) else data
            elif isinstance(data, dict):
                # Format dict direct
                metadata = {'total': data.get('total', 0)}
                indicators_data = data.get('data', []) or data.get('indicators', [])
            else:
                logger.warning(f"[WORLD BANK] Format inattendu: {type(data)}")
                return {
                    'success': False,
                    'error': f'Format de réponse invalide: {type(data)}',
                    'timestamp': datetime.now().isoformat()
                }

            # Vérifier que indicators_data est une liste
            if not isinstance(indicators_data, list):
                indicators_data = [indicators_data] if indicators_data else []

            # Filtrer les entrées None
            indicators_data = [item for item in indicators_data if item is not None]

            if not indicators_data:
                logger.warning(f"[WORLD BANK] Aucune donnée pour l'année {year}")
                return {
                    'success': False,
                    'error': f'Aucune donnée disponible pour {year}',
                    'timestamp': datetime.now().isoformat()
                }

            logger.info(f"[OK] {len(indicators_data)} pays récupérés")

            # Formater les données
            corruption_data = self._format_corruption_data(indicators_data, year)

            # Statistiques
            stats = self._calculate_statistics(corruption_data)

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'World Bank Governance Indicators (CC.EST)',
                'year': year,
                'total_countries': metadata.get('total', 0),
                'corruption_data': corruption_data,
                'statistics': stats,
                'indicator': {
                    'code': self.INDICATOR,
                    'name': 'Control of Corruption Estimate',
                    'description': 'Measures perceptions of corruption, ranging from -2.5 (weak) to +2.5 (strong) governance',
                    'scale': 'Score de -2.5 (faible contrôle) à +2.5 (fort contrôle)'
                }
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR] Erreur requête World Bank: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"[ERROR] Erreur traitement World Bank: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @cached_connector_method('worldbank_corruption')
    def get_latest_data(self, limit: int = 50) -> Dict[str, Any]:
        """
        Récupère les données les plus récentes disponibles
        """
        try:
            # D'abord trouver l'année la plus récente
            current_year = datetime.now().year - 1  # Données avec 1 an de décalage
            year_to_try = current_year

            # Essayer les années récentes jusqu'à trouver des données
            for attempt_year in range(current_year, 2018, -1):  # Remonter jusqu'à 2018
                test_result = self.get_corruption_data(year=attempt_year, limit=10)
                if test_result.get('success') and test_result.get('total_countries', 0) > 0:
                    year_to_try = attempt_year
                    break

            logger.info(f"[WORLD BANK] Utilisation données {year_to_try} (plus récentes disponibles)")

            # Récupérer les données pour cette année
            return self.get_corruption_data(year=year_to_try, limit=limit)

        except Exception as e:
            logger.error(f"[ERROR] Erreur latest data: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @cached_connector_method('worldbank_corruption')
    def get_top_and_bottom(self, year: int = 2022, count: int = 10) -> Dict[str, Any]:
        """
        Récupère les meilleurs et pires pays
        """
        try:
            result = self.get_corruption_data(year=year, limit=200)  # Plus pour trier

            if not result.get('success'):
                return result

            data = result.get('corruption_data', [])

            # Trier par score (du meilleur au pire)
            sorted_data = sorted(data, key=lambda x: x['score'], reverse=True)

            # Meilleurs pays (hauts scores = moins de corruption)
            top_countries = sorted_data[:count]

            # Pires pays (bas scores = plus de corruption)
            bottom_countries = sorted_data[-count:]

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'World Bank Governance Indicators (CC.EST)',
                'year': year,
                'top_countries': top_countries,
                'bottom_countries': bottom_countries,
                'statistics': {
                    'top_average': round(sum(c['score'] for c in top_countries) / len(top_countries), 2),
                    'bottom_average': round(sum(c['score'] for c in bottom_countries) / len(bottom_countries), 2),
                    'global_average': result.get('statistics', {}).get('average_score', 0)
                }
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur top/bottom: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @cached_connector_method('worldbank_corruption')
    def get_country_trend(self, country_code: str, years: int = 10) -> Dict[str, Any]:
        """
        Récupère la tendance d'un pays sur plusieurs années
        """
        try:
            current_year = datetime.now().year - 1
            start_year = current_year - years + 1

            url = f"{self.BASE_URL}/country/{country_code}/indicator/{self.INDICATOR}"
            params = {
                'format': self.FORMAT,
                'date': f"{start_year}:{current_year}",
                'per_page': years * 2
            }

            logger.info(f"[WORLD BANK] Tendance pour {country_code} {start_year}-{current_year}")

            # Utiliser la méthode avec retry et circuit breaker
            result = self._make_request(url, params)

            if not result.get('success'):
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'timestamp': datetime.now().isoformat()
                }

            data = result['data']

            if len(data) < 2:
                return {
                    'success': False,
                    'error': 'Données non disponibles',
                    'timestamp': datetime.now().isoformat()
                }

            indicators_data = data[1]

            # Formater la tendance
            trend_data = []
            for item in indicators_data:
                if item.get('value') is not None:
                    trend_data.append({
                        'year': int(item.get('date')),
                        'score': round(float(item.get('value')), 3),
                        'percentile': item.get('decimal', 0)
                    })

            # Trier par année
            trend_data.sort(key=lambda x: x['year'])

            # Calculer changement
            if len(trend_data) >= 2:
                first_score = trend_data[0]['score']
                last_score = trend_data[-1]['score']
                score_change = last_score - first_score
                percent_change = (score_change / abs(first_score)) * 100 if first_score != 0 else 0
            else:
                score_change = 0
                percent_change = 0

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'World Bank Governance Indicators (CC.EST)',
                'country_code': country_code.upper(),
                'country_name': self._get_country_name(country_code),
                'trend_data': trend_data,
                'statistics': {
                    'data_points': len(trend_data),
                    'first_year': trend_data[0]['year'] if trend_data else None,
                    'last_year': trend_data[-1]['year'] if trend_data else None,
                    'score_change': round(score_change, 3),
                    'percent_change': round(percent_change, 1),
                    'current_score': trend_data[-1]['score'] if trend_data else None,
                    'trend': 'Amélioration' if score_change > 0 else 'Détérioration' if score_change < 0 else 'Stable'
                }
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur tendance pays: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _format_corruption_data(self, indicators_data: List[Dict], year: int) -> List[Dict[str, Any]]:
        """Formate les données de corruption au format GEOPOL"""
        formatted = []

        for item in indicators_data:
            try:
                country = item.get('country', {})
                value = item.get('value')

                if value is None:
                    continue

                score = float(value)

                # Convertir score World Bank (-2.5 à +2.5) en score lisible 0-100
                # -2.5 = 0, 0 = 50, +2.5 = 100
                readable_score = ((score + 2.5) / 5.0) * 100
                readable_score = max(0, min(100, readable_score))  # Clamp 0-100

                # Déterminer niveau de corruption
                corruption_level = self._determine_corruption_level(score)

                formatted.append({
                    'country_code': country.get('id', '').upper(),
                    'country_name': country.get('value', ''),
                    'year': year,
                    'score': round(score, 3),  # Score original (-2.5 à +2.5)
                    'readable_score': round(readable_score, 1),  # Score 0-100
                    'corruption_level': corruption_level,
                    'percentile': item.get('decimal', 0),
                    'source': 'World Bank CC.EST',
                    'interpretation': self._get_interpretation(score),
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.warning(f"[WARN] Erreur format données: {e}")
                continue

        return formatted

    def _determine_corruption_level(self, score: float) -> str:
        """Détermine le niveau de corruption basé sur le score"""
        if score >= 1.5:
            return 'Very Low'  # Très faible corruption
        elif score >= 0.5:
            return 'Low'  # Faible corruption
        elif score >= -0.5:
            return 'Moderate'  # Corruption modérée
        elif score >= -1.5:
            return 'High'  # Forte corruption
        else:
            return 'Very High'  # Très forte corruption

    def _get_interpretation(self, score: float) -> str:
        """Retourne une interprétation du score"""
        if score >= 1.5:
            return 'Governance forte, corruption très faible'
        elif score >= 0.5:
            return 'Bon contrôle de la corruption'
        elif score >= -0.5:
            return 'Contrôle modéré de la corruption'
        elif score >= -1.5:
            return 'Contrôle faible de la corruption'
        else:
            return 'Contrôle très faible de la corruption'

    def _calculate_statistics(self, data: List[Dict]) -> Dict[str, Any]:
        """Calcule les statistiques sur les données"""
        if not data:
            return {
                'average_score': 0,
                'min_score': 0,
                'max_score': 0,
                'count': 0
            }

        scores = [item['score'] for item in data]
        readable_scores = [item['readable_score'] for item in data]

        # Compter par niveau
        levels = {}
        for item in data:
            level = item['corruption_level']
            levels[level] = levels.get(level, 0) + 1

        return {
            'average_score': round(sum(scores) / len(scores), 3),
            'average_readable_score': round(sum(readable_scores) / len(readable_scores), 1),
            'min_score': round(min(scores), 3),
            'max_score': round(max(scores), 3),
            'min_readable_score': round(min(readable_scores), 1),
            'max_readable_score': round(max(readable_scores), 1),
            'count': len(data),
            'by_level': levels,
            'countries_very_low': levels.get('Very Low', 0),
            'countries_very_high': levels.get('Very High', 0)
        }

    def _get_country_name(self, country_code: str) -> str:
        """Obtient le nom du pays depuis le cache ou l'API"""
        if country_code in self.country_cache:
            return self.country_cache[country_code]

        try:
            url = f"{self.BASE_URL}/country/{country_code}"
            params = {'format': 'json'}

            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1 and data[1]:
                    country_name = data[1][0].get('name', country_code)
                    self.country_cache[country_code] = country_name
                    return country_name
        except:
            pass

        return country_code


def get_worldbank_corruption_connector() -> WorldBankCorruptionConnector:
    """Factory pour obtenir le connecteur World Bank Corruption"""
    return WorldBankCorruptionConnector()


__all__ = ['WorldBankCorruptionConnector', 'get_worldbank_corruption_connector']