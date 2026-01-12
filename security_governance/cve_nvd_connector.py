"""
Connecteur CVE/NVD (National Vulnerability Database)
Source: https://services.nvd.nist.gov/rest/json/cves/2.0
API publique sans authentification requise
Limite: 5 requêtes par 30 secondes par IP

Données disponibles:
- Vulnérabilités CVE récentes
- Scores CVSS
- Informations de sévérité
- Références
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import time

logger = logging.getLogger(__name__)


class CVENVDConnector:
    """
    Connecteur pour l'API NVD CVE
    Récupère les vulnérabilités récentes
    """

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    # Types de sévérité
    SEVERITY_LEVELS = {
        'CRITICAL': (9.0, 10.0),
        'HIGH': (7.0, 8.9),
        'MEDIUM': (4.0, 6.9),
        'LOW': (0.0, 3.9)
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0 (+https://github.com/geopol)',
            'Accept': 'application/json'
        })
        self.last_request_time = 0
        self.min_request_interval = 6  # 6 secondes entre requêtes (5/30s)

    def _rate_limit(self):
        """Respecte les limites de rate limiting de l'API NVD"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.info(f"[RATE LIMIT] Attente {sleep_time:.1f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def get_recent_cves(self, days: int = 7, limit: int = 20) -> Dict[str, Any]:
        """
        Récupère les CVE récentes
        Args:
            days: Nombre de jours en arrière
            limit: Nombre max de CVE
        Returns:
            Dict avec résultats
        """
        try:
            self._rate_limit()

            # Calculer date de début
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%dT00:00:00.000')

            # Paramètres de recherche
            end_date = datetime.now().strftime('%Y-%m-%dT23:59:59.999')
            params = {
                'pubStartDate': start_date,
                'pubEndDate': end_date,
                'resultsPerPage': min(limit, 100),  # Max 100 par requête
                'startIndex': 0
            }

            logger.info(f"[NVD] Récupération CVE depuis {start_date}")

            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Formater les résultats
            cves = self._format_cves(data.get('vulnerabilities', []))

            # Statistiques
            stats = self._calculate_stats(cves)

            logger.info(f"[OK] {len(cves)} CVE récentes récupérées")

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'NVD CVE Database',
                'total_results': data.get('totalResults', 0),
                'cves': cves,
                'statistics': stats,
                'query': {
                    'days': days,
                    'limit': limit,
                    'start_date': start_date
                }
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR] Erreur requête NVD: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"[ERROR] Erreur inattendue NVD: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_critical_cves(self, days: int = 30, limit: int = 10) -> Dict[str, Any]:
        """
        Récupère uniquement les CVE critiques
        """
        try:
            result = self.get_recent_cves(days=days, limit=100)  # Plus pour filtrer

            if not result['success']:
                return result

            # Filtrer CVE critiques
            critical_cves = [
                cve for cve in result['cves']
                if cve.get('severity_level') == 'CRITICAL'
            ][:limit]

            logger.info(f"[OK] {len(critical_cves)} CVE critiques trouvées")

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'NVD CVE Database',
                'critical_cves': critical_cves,
                'count': len(critical_cves),
                'total_scanned': len(result['cves']),
                'query': {
                    'days': days,
                    'limit': limit
                }
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur critical CVE: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_cve_by_id(self, cve_id: str) -> Dict[str, Any]:
        """
        Récupère une CVE spécifique
        """
        try:
            self._rate_limit()

            url = f"{self.BASE_URL}?cveId={cve_id}"

            logger.info(f"[NVD] Récupération CVE {cve_id}")

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()

            if not data.get('vulnerabilities'):
                return {
                    'success': False,
                    'error': f'CVE {cve_id} non trouvée',
                    'timestamp': datetime.now().isoformat()
                }

            cve_data = self._format_cves(data['vulnerabilities'])[0]

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'NVD CVE Database',
                'cve': cve_data
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur CVE {cve_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _format_cves(self, vulnerabilities: List[Dict]) -> List[Dict[str, Any]]:
        """Formate les vulnérabilités au format GEOPOL"""
        formatted = []

        for vuln in vulnerabilities:
            try:
                cve = vuln.get('cve', {})

                # Informations de base
                cve_id = cve.get('id', '')

                # Métriques CVSS v3 (prioritaire) ou v2
                metrics = cve.get('metrics', {})
                cvss_data = None
                base_score = 0.0
                severity = 'UNKNOWN'

                if 'cvssMetricV31' in metrics and metrics['cvssMetricV31']:
                    cvss_data = metrics['cvssMetricV31'][0]['cvssData']
                    base_score = cvss_data.get('baseScore', 0.0)
                    severity = metrics['cvssMetricV31'][0].get('cvssData', {}).get('baseSeverity', 'UNKNOWN')
                elif 'cvssMetricV30' in metrics and metrics['cvssMetricV30']:
                    cvss_data = metrics['cvssMetricV30'][0]['cvssData']
                    base_score = cvss_data.get('baseScore', 0.0)
                    severity = metrics['cvssMetricV30'][0].get('cvssData', {}).get('baseSeverity', 'UNKNOWN')
                elif 'cvssMetricV2' in metrics and metrics['cvssMetricV2']:
                    cvss_data = metrics['cvssMetricV2'][0]['cvssData']
                    base_score = cvss_data.get('baseScore', 0.0)
                    severity = self._cvss2_severity(base_score)

                # Déterminer niveau de sévérité
                severity_level = self._determine_severity_level(base_score)

                # Descriptions
                descriptions = cve.get('descriptions', [])
                description_en = next(
                    (desc['value'] for desc in descriptions if desc['lang'] == 'en'),
                    'No description available'
                )

                # Références
                references = cve.get('references', [])
                reference_urls = [ref['url'] for ref in references[:3]]  # Top 3

                # Configuration CPE (produits affectés)
                configurations = cve.get('configurations', [])
                affected_products = self._extract_affected_products(configurations)

                # Date de publication
                published = cve.get('published', '')
                if published:
                    published_date = published.split('T')[0]
                else:
                    published_date = 'Unknown'

                formatted.append({
                    'cve_id': cve_id,
                    'description': description_en[:500],  # Limite longueur
                    'severity_score': round(base_score, 1),
                    'severity': severity,
                    'severity_level': severity_level,
                    'published_date': published_date,
                    'last_modified': cve.get('lastModified', '').split('T')[0],
                    'affected_products': affected_products[:5],  # Top 5
                    'reference_urls': reference_urls,
                    'attack_vector': cvss_data.get('attackVector', 'UNKNOWN') if cvss_data else 'UNKNOWN',
                    'attack_complexity': cvss_data.get('attackComplexity', 'UNKNOWN') if cvss_data else 'UNKNOWN',
                    'privileges_required': cvss_data.get('privilegesRequired', 'UNKNOWN') if cvss_data else 'UNKNOWN',
                    'user_interaction': cvss_data.get('userInteraction', 'UNKNOWN') if cvss_data else 'UNKNOWN',
                    'scope': cvss_data.get('scope', 'UNKNOWN') if cvss_data else 'UNKNOWN',
                    'confidentiality_impact': cvss_data.get('confidentialityImpact', 'UNKNOWN') if cvss_data else 'UNKNOWN',
                    'integrity_impact': cvss_data.get('integrityImpact', 'UNKNOWN') if cvss_data else 'UNKNOWN',
                    'availability_impact': cvss_data.get('availabilityImpact', 'UNKNOWN') if cvss_data else 'UNKNOWN',
                    'base_score': round(base_score, 1),
                    'exploitability_score': cvss_data.get('exploitabilityScore', 0.0) if cvss_data else 0.0,
                    'impact_score': cvss_data.get('impactScore', 0.0) if cvss_data else 0.0,
                    'timestamp': datetime.now().isoformat()
                })

            except Exception as e:
                logger.warning(f"[WARN] Erreur format CVE: {e}")
                continue

        return formatted

    def _extract_affected_products(self, configurations: List[Dict]) -> List[str]:
        """Extrait la liste des produits affectés"""
        products = set()

        for config in configurations:
            nodes = config.get('nodes', [])
            for node in nodes:
                cpe_matches = node.get('cpeMatch', [])
                for cpe_match in cpe_matches:
                    cpe_uri = cpe_match.get('criteria', '')
                    # Extraire le nom du produit du CPE URI
                    # Format: cpe:2.3:a:microsoft:windows:10.0:*:*:*:*:*:*:*
                    parts = cpe_uri.split(':')
                    if len(parts) >= 5:
                        vendor = parts[3]
                        product = parts[4]
                        if vendor and product:
                            products.add(f"{vendor}/{product}")

        return list(products)

    def _determine_severity_level(self, score: float) -> str:
        """Détermine le niveau de sévérité basé sur le score CVSS"""
        if score >= 9.0:
            return 'CRITICAL'
        elif score >= 7.0:
            return 'HIGH'
        elif score >= 4.0:
            return 'MEDIUM'
        elif score > 0.0:
            return 'LOW'
        else:
            return 'UNKNOWN'

    def _cvss2_severity(self, score: float) -> str:
        """Convertit score CVSS v2 en sévérité textuelle"""
        if score >= 7.0:
            return 'HIGH'
        elif score >= 4.0:
            return 'MEDIUM'
        elif score > 0.0:
            return 'LOW'
        else:
            return 'UNKNOWN'

    def _calculate_stats(self, cves: List[Dict]) -> Dict[str, Any]:
        """Calcule les statistiques sur les CVE"""
        if not cves:
            return {
                'total': 0,
                'by_severity': {},
                'average_score': 0.0
            }

        by_severity = {
            'CRITICAL': 0,
            'HIGH': 0,
            'MEDIUM': 0,
            'LOW': 0,
            'UNKNOWN': 0
        }

        total_score = 0.0

        for cve in cves:
            severity = cve.get('severity_level', 'UNKNOWN')
            by_severity[severity] = by_severity.get(severity, 0) + 1
            total_score += cve.get('severity_score', 0.0)

        return {
            'total': len(cves),
            'by_severity': by_severity,
            'average_score': round(total_score / len(cves), 2) if cves else 0.0,
            'critical_percentage': round(by_severity['CRITICAL'] / len(cves) * 100, 1) if cves else 0.0
        }


def get_cve_nvd_connector() -> CVENVDConnector:
    """Factory pour obtenir le connecteur CVE/NVD"""
    return CVENVDConnector()


__all__ = ['CVENVDConnector', 'get_cve_nvd_connector']