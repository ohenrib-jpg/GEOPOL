"""
Connecteur AlienVault OTX (Open Threat Exchange)
Source: https://otx.alienvault.com/
API: https://otx.alienvault.com/api
Documentation: https://otx.alienvault.com/api

Données disponibles:
- Indicateurs de compromission (IOCs)
- Pulses (collections de menaces)
- Malware
- IPs malveillantes
- Domaines malveillants
- CVEs
- Groupes APT
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

# Import du cache intelligent
try:
    from .security_cache import cached_connector_method
    CACHE_ENABLED = True
    logger.debug(f"[OTX] Cache intelligent activé: CACHE_ENABLED={CACHE_ENABLED}")
except ImportError as e:
    CACHE_ENABLED = False
    cached_connector_method = lambda source: lambda func: func  # Décorateur factice
    logger.warning(f"[OTX] Cache intelligent désactivé: {e}")


class AlienVaultOTXConnector:
    """
    Connecteur pour l'API AlienVault OTX (Open Threat Exchange)
    Récupère les indicateurs de menaces cyber (IOCs, pulses, malware, etc.)
    """

    BASE_URL = "https://otx.alienvault.com/api/v1"

    # Endpoints principaux
    ENDPOINTS = {
        'pulses_subscribed': '/pulses/subscribed',
        'pulses_activity': '/pulses/activity',
        'search_pulses': '/search/pulses',
        'indicators_ipv4': '/indicators/IPv4',
        'indicators_domain': '/indicators/domain',
        'indicators_hostname': '/indicators/hostname',
        'indicators_file': '/indicators/file',
        'indicators_url': '/indicators/URL',
        'indicators_cve': '/indicators/cve',
        'user_me': '/user/me',
        'user_pulses': '/users/me/pulses'
    }

    # Types d'indicateurs OTX
    INDICATOR_TYPES = {
        'IPv4': 'Adresse IP v4',
        'IPv6': 'Adresse IP v6',
        'domain': 'Domaine',
        'hostname': 'Nom d\'hôte',
        'email': 'Email',
        'URL': 'URL',
        'URI': 'URI',
        'FileHash-MD5': 'Hash MD5',
        'FileHash-SHA1': 'Hash SHA1',
        'FileHash-SHA256': 'Hash SHA256',
        'CIDR': 'Bloc CIDR',
        'FilePath': 'Chemin fichier',
        'Mutex': 'Mutex',
        'CVE': 'CVE'
    }

    # Configuration de timeout et retry
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self, api_key: str = None, timeout: int = None, max_retries: int = None):
        """
        Args:
            api_key: Clé API OTX (ou via env ALIENVAULT_OTX_API_KEY)
            timeout: Timeout en secondes pour les requêtes (défaut: 30)
            max_retries: Nombre maximum de tentatives (défaut: 3)
        """
        self.api_key = api_key or os.getenv('ALIENVAULT_OTX_API_KEY')

        if not self.api_key:
            logger.warning("[OTX] Clé API non configurée - fonctionnalités limitées")

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0 (+https://github.com/geopol)',
            'Accept': 'application/json'
        })

        if self.api_key:
            self.session.headers['X-OTX-API-KEY'] = self.api_key

        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries or self.MAX_RETRIES
        self.circuit_breaker = {'failures': 0, 'last_failure': None, 'open': False}

    def _check_circuit_breaker(self) -> bool:
        """Vérifie si le circuit breaker est ouvert"""
        if not self.circuit_breaker['open']:
            return True

        if self.circuit_breaker['last_failure']:
            elapsed = (datetime.now() - self.circuit_breaker['last_failure']).total_seconds()
            if elapsed > 60:
                logger.info("[OTX] Circuit breaker: tentative de récupération")
                self.circuit_breaker['open'] = False
                self.circuit_breaker['failures'] = 0
                return True

        logger.warning("[OTX] Circuit breaker ouvert - requête bloquée")
        return False

    def _record_failure(self):
        """Enregistre un échec pour le circuit breaker"""
        self.circuit_breaker['failures'] += 1
        self.circuit_breaker['last_failure'] = datetime.now()
        if self.circuit_breaker['failures'] >= 3:
            self.circuit_breaker['open'] = True
            logger.error("[OTX] Circuit breaker ouvert après 3 échecs")

    def _record_success(self):
        """Enregistre un succès - réinitialise le circuit breaker"""
        if self.circuit_breaker['failures'] > 0:
            logger.info("[OTX] Circuit breaker: récupération réussie")
        self.circuit_breaker['failures'] = 0
        self.circuit_breaker['open'] = False

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Effectue une requête à l'API OTX avec gestion d'erreurs
        """
        if not self._check_circuit_breaker():
            return {
                'success': False,
                'error': 'Circuit breaker ouvert - service temporairement indisponible'
            }

        url = f"{self.BASE_URL}{endpoint}"
        last_error = None

        for attempt in range(self.max_retries):
            try:
                logger.info(f"[OTX] Requête {endpoint} (tentative {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()

                data = response.json()
                self._record_success()
                return {'success': True, 'data': data}

            except requests.exceptions.Timeout as e:
                last_error = f"Timeout après {self.timeout}s: {e}"
                logger.warning(f"[OTX] Timeout {endpoint} (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except requests.exceptions.ConnectionError as e:
                last_error = f"Erreur de connexion: {e}"
                logger.warning(f"[OTX] Erreur connexion {endpoint} (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except requests.exceptions.HTTPError as e:
                if response.status_code == 403:
                    last_error = "Clé API invalide ou expirée"
                    logger.error("[OTX] Erreur 403 - Clé API invalide")
                    break
                elif response.status_code < 500:
                    last_error = f"Erreur HTTP {response.status_code}: {e}"
                    logger.error(f"[OTX] Erreur HTTP {response.status_code}")
                    break
                last_error = f"Erreur serveur {response.status_code}: {e}"
                logger.warning(f"[OTX] Erreur serveur {endpoint} (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except Exception as e:
                last_error = f"Erreur inattendue: {e}"
                logger.error(f"[OTX] Erreur inattendue {endpoint}: {e}")
                break

        self._record_failure()
        logger.error(f"[OTX] Échec après {self.max_retries} tentatives: {last_error}")
        return {'success': False, 'error': last_error}

    @cached_connector_method('alienvault_otx')
    def get_subscribed_pulses(self, limit: int = 50, days: int = 7) -> Dict[str, Any]:
        """
        Récupère les pulses auxquels l'utilisateur est abonné
        Args:
            limit: Nombre max de pulses
            days: Pulses modifiées dans les X derniers jours
        Returns:
            Dict avec les pulses
        """
        try:
            modified_since = (datetime.now() - timedelta(days=days)).isoformat()

            params = {
                'limit': limit,
                'modified_since': modified_since
            }

            result = self._make_request(self.ENDPOINTS['pulses_subscribed'], params)

            if not result['success']:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'timestamp': datetime.now().isoformat(),
                    'pulses': []
                }

            pulses = result['data'].get('results', [])
            formatted_pulses = self._format_pulses(pulses)

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'AlienVault OTX',
                'total_pulses': len(formatted_pulses),
                'pulses': formatted_pulses,
                'query': {'limit': limit, 'days': days}
            }

        except Exception as e:
            logger.error(f"[OTX] Erreur get_subscribed_pulses: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'pulses': []
            }

    @cached_connector_method('alienvault_otx')
    def search_pulses(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """
        Recherche dans les pulses publiques
        Args:
            query: Terme de recherche (ex: 'ransomware', 'APT29', 'Ukraine')
            limit: Nombre max de résultats
        Returns:
            Dict avec les pulses trouvées
        """
        try:
            params = {
                'q': query,
                'limit': limit
            }

            result = self._make_request(self.ENDPOINTS['search_pulses'], params)

            if not result['success']:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'timestamp': datetime.now().isoformat(),
                    'pulses': []
                }

            pulses = result['data'].get('results', [])
            formatted_pulses = self._format_pulses(pulses)

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'AlienVault OTX Search',
                'query': query,
                'total_results': len(formatted_pulses),
                'pulses': formatted_pulses
            }

        except Exception as e:
            logger.error(f"[OTX] Erreur search_pulses: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'pulses': []
            }

    @cached_connector_method('alienvault_otx')
    def get_indicator_details(self, indicator_type: str, indicator: str) -> Dict[str, Any]:
        """
        Récupère les détails d'un indicateur spécifique
        Args:
            indicator_type: Type d'indicateur ('IPv4', 'domain', 'hostname', 'file', 'URL', 'cve')
            indicator: Valeur de l'indicateur
        Returns:
            Dict avec les détails
        """
        try:
            # Mapper le type vers l'endpoint
            type_to_endpoint = {
                'ipv4': 'indicators_ipv4',
                'ip': 'indicators_ipv4',
                'domain': 'indicators_domain',
                'hostname': 'indicators_hostname',
                'file': 'indicators_file',
                'hash': 'indicators_file',
                'url': 'indicators_url',
                'cve': 'indicators_cve'
            }

            endpoint_key = type_to_endpoint.get(indicator_type.lower())
            if not endpoint_key:
                return {
                    'success': False,
                    'error': f"Type d'indicateur non supporté: {indicator_type}",
                    'timestamp': datetime.now().isoformat()
                }

            endpoint = f"{self.ENDPOINTS[endpoint_key]}/{indicator}/general"
            result = self._make_request(endpoint)

            if not result['success']:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'timestamp': datetime.now().isoformat()
                }

            data = result['data']

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'AlienVault OTX',
                'indicator_type': indicator_type,
                'indicator': indicator,
                'details': {
                    'pulse_count': data.get('pulse_info', {}).get('count', 0),
                    'reputation': data.get('reputation', 0),
                    'country': data.get('country_name', 'Unknown'),
                    'country_code': data.get('country_code', ''),
                    'asn': data.get('asn', ''),
                    'validation': data.get('validation', []),
                    'related_pulses': data.get('pulse_info', {}).get('pulses', [])[:5],
                    'malware_samples': len(data.get('malware', {}).get('data', [])),
                    'sections': list(data.get('sections', []))
                },
                'raw_data': data
            }

        except Exception as e:
            logger.error(f"[OTX] Erreur get_indicator_details: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @cached_connector_method('alienvault_otx')
    def get_recent_threats(self, days: int = 7, limit: int = 50) -> Dict[str, Any]:
        """
        Récupère les menaces récentes (pulses publiques récentes)
        Args:
            days: Nombre de jours en arrière
            limit: Nombre max de menaces
        Returns:
            Dict avec les menaces récentes
        """
        try:
            # Rechercher des termes de menaces courants
            threat_terms = ['malware', 'ransomware', 'apt', 'phishing', 'exploit']
            all_threats = []

            for term in threat_terms[:3]:  # Limiter pour éviter trop de requêtes
                result = self.search_pulses(term, limit=limit // 3)
                if result.get('success'):
                    all_threats.extend(result.get('pulses', []))

            # Dédupliquer par ID
            seen_ids = set()
            unique_threats = []
            for threat in all_threats:
                threat_id = threat.get('id')
                if threat_id and threat_id not in seen_ids:
                    seen_ids.add(threat_id)
                    unique_threats.append(threat)

            # Trier par date de modification
            unique_threats.sort(
                key=lambda x: x.get('modified', ''),
                reverse=True
            )

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'AlienVault OTX',
                'total_threats': len(unique_threats[:limit]),
                'threats': unique_threats[:limit],
                'query': {'days': days, 'limit': limit}
            }

        except Exception as e:
            logger.error(f"[OTX] Erreur get_recent_threats: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'threats': []
            }

    @cached_connector_method('alienvault_otx')
    def get_threat_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé des menaces (statistiques agrégées)
        Returns:
            Dict avec statistiques de menaces
        """
        try:
            # Récupérer les pulses récentes
            pulses_result = self.get_subscribed_pulses(limit=100, days=30)

            if not pulses_result.get('success'):
                # Fallback sur recherche publique
                pulses_result = self.search_pulses('threat', limit=50)

            pulses = pulses_result.get('pulses', [])

            # Agréger les statistiques
            by_adversary = {}
            by_targeted_country = {}
            by_malware_family = {}
            total_indicators = 0

            for pulse in pulses:
                # Compter indicateurs
                total_indicators += pulse.get('indicator_count', 0)

                # Groupes adversaires
                adversary = pulse.get('adversary', 'Unknown')
                if adversary and adversary != 'Unknown':
                    by_adversary[adversary] = by_adversary.get(adversary, 0) + 1

                # Pays ciblés
                for country in pulse.get('targeted_countries', []):
                    by_targeted_country[country] = by_targeted_country.get(country, 0) + 1

                # Familles de malware
                for family in pulse.get('malware_families', []):
                    by_malware_family[family] = by_malware_family.get(family, 0) + 1

            # Trier et limiter
            top_adversaries = sorted(by_adversary.items(), key=lambda x: x[1], reverse=True)[:10]
            top_countries = sorted(by_targeted_country.items(), key=lambda x: x[1], reverse=True)[:10]
            top_malware = sorted(by_malware_family.items(), key=lambda x: x[1], reverse=True)[:10]

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'AlienVault OTX',
                'summary': {
                    'total_pulses': len(pulses),
                    'total_indicators': total_indicators,
                    'top_adversaries': [{'name': k, 'count': v} for k, v in top_adversaries],
                    'top_targeted_countries': [{'country': k, 'count': v} for k, v in top_countries],
                    'top_malware_families': [{'family': k, 'count': v} for k, v in top_malware],
                    'avg_indicators_per_pulse': round(total_indicators / len(pulses), 1) if pulses else 0
                }
            }

        except Exception as e:
            logger.error(f"[OTX] Erreur get_threat_summary: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @cached_connector_method('alienvault_otx')
    def check_ioc(self, ioc: str, ioc_type: str = 'auto') -> Dict[str, Any]:
        """
        Vérifie si un IOC (Indicator of Compromise) est connu
        Args:
            ioc: L'indicateur à vérifier (IP, domaine, hash, etc.)
            ioc_type: Type d'IOC ('auto' pour détection automatique)
        Returns:
            Dict avec le statut de l'IOC
        """
        try:
            # Détection automatique du type si 'auto'
            if ioc_type == 'auto':
                ioc_type = self._detect_ioc_type(ioc)

            if not ioc_type:
                return {
                    'success': False,
                    'error': f"Impossible de déterminer le type de l'IOC: {ioc}",
                    'timestamp': datetime.now().isoformat()
                }

            # Récupérer les détails
            result = self.get_indicator_details(ioc_type, ioc)

            if not result['success']:
                return result

            details = result.get('details', {})

            # Déterminer le niveau de risque
            pulse_count = details.get('pulse_count', 0)
            reputation = details.get('reputation', 0)

            if pulse_count >= 10 or reputation >= 50:
                risk_level = 'high'
            elif pulse_count >= 3 or reputation >= 20:
                risk_level = 'medium'
            elif pulse_count >= 1:
                risk_level = 'low'
            else:
                risk_level = 'unknown'

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'AlienVault OTX',
                'ioc': ioc,
                'ioc_type': ioc_type,
                'is_known_threat': pulse_count > 0,
                'risk_level': risk_level,
                'pulse_count': pulse_count,
                'reputation_score': reputation,
                'country': details.get('country', 'Unknown'),
                'details': details
            }

        except Exception as e:
            logger.error(f"[OTX] Erreur check_ioc: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _detect_ioc_type(self, ioc: str) -> Optional[str]:
        """Détecte automatiquement le type d'IOC"""
        import re

        ioc = ioc.strip()

        # IPv4
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ipv4_pattern, ioc):
            return 'ipv4'

        # Hash (MD5, SHA1, SHA256)
        if re.match(r'^[a-fA-F0-9]{32}$', ioc):
            return 'file'  # MD5
        if re.match(r'^[a-fA-F0-9]{40}$', ioc):
            return 'file'  # SHA1
        if re.match(r'^[a-fA-F0-9]{64}$', ioc):
            return 'file'  # SHA256

        # CVE
        if re.match(r'^CVE-\d{4}-\d+$', ioc, re.IGNORECASE):
            return 'cve'

        # URL
        if ioc.startswith(('http://', 'https://')):
            return 'url'

        # Domain (simple check)
        if '.' in ioc and not ioc.startswith(('http://', 'https://')) and not re.match(ipv4_pattern, ioc):
            return 'domain'

        return None

    def _format_pulses(self, pulses: List[Dict]) -> List[Dict[str, Any]]:
        """Formate les pulses OTX au format GEOPOL"""
        formatted = []

        for pulse in pulses:
            try:
                formatted.append({
                    'id': pulse.get('id'),
                    'name': pulse.get('name', ''),
                    'description': pulse.get('description', '')[:500] if pulse.get('description') else '',
                    'author_name': pulse.get('author_name', 'Unknown'),
                    'created': pulse.get('created'),
                    'modified': pulse.get('modified'),
                    'indicator_count': pulse.get('indicator_count', 0),
                    'adversary': pulse.get('adversary', ''),
                    'targeted_countries': pulse.get('targeted_countries', []),
                    'malware_families': pulse.get('malware_families', []),
                    'attack_ids': pulse.get('attack_ids', []),
                    'industries': pulse.get('industries', []),
                    'tlp': pulse.get('tlp', 'white'),
                    'tags': pulse.get('tags', [])[:10],
                    'references': pulse.get('references', [])[:5],
                    'source': 'AlienVault OTX'
                })

            except Exception as e:
                logger.warning(f"[OTX] Erreur format pulse: {e}")
                continue

        return formatted

    def verify_api_key(self) -> Dict[str, Any]:
        """
        Vérifie si la clé API est valide
        Returns:
            Dict avec le statut de la clé
        """
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'valid': False,
                    'error': 'Aucune clé API configurée',
                    'timestamp': datetime.now().isoformat()
                }

            result = self._make_request(self.ENDPOINTS['user_me'])

            if result['success']:
                user_data = result['data']
                return {
                    'success': True,
                    'valid': True,
                    'username': user_data.get('username'),
                    'member_since': user_data.get('member_since'),
                    'pulse_count': user_data.get('pulse_count', 0),
                    'subscriber_count': user_data.get('subscriber_count', 0),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'valid': False,
                    'error': result.get('error', 'Vérification échouée'),
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"[OTX] Erreur verify_api_key: {e}")
            return {
                'success': False,
                'valid': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


def get_alienvault_otx_connector(api_key: str = None) -> AlienVaultOTXConnector:
    """Factory pour obtenir le connecteur AlienVault OTX"""
    return AlienVaultOTXConnector(api_key=api_key)


__all__ = ['AlienVaultOTXConnector', 'get_alienvault_otx_connector']
