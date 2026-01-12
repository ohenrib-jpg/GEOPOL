"""
Connecteur Transparency International CPI (Corruption Perceptions Index)
Source: https://www.transparency.org/en/cpi
Données publiques: https://www.transparency.org/en/cpi/2023
Format: CSV disponible via API ou téléchargement direct
Pas d'authentification requise pour les données publiques
"""
import requests
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import csv
from io import StringIO

logger = logging.getLogger(__name__)

# Import du cache intelligent
try:
    from .security_cache import cached_connector_method
    CACHE_ENABLED = True
    logger.debug(f"[CPI] Cache intelligent activé: CACHE_ENABLED={CACHE_ENABLED}")
except ImportError as e:
    CACHE_ENABLED = False
    cached_connector_method = lambda source: lambda func: func  # Décorateur factice
    logger.warning(f"[CPI] Cache intelligent désactivé: {e}")


class TransparencyCPIConnector:
    """
    Connecteur pour les données CPI de Transparency International
    Indice de perception de la corruption (score 0-100)
    """

    # URLs des données CPI (mises à jour janvier 2026)
    # Note: Transparency International ne fournit pas d'API publique
    # Les données sont disponibles en téléchargement via le site web
    CPI_URLS = {
        '2024': {
            'main_page': 'https://www.transparency.org/en/cpi/2024',
            'media_kit': 'https://www.transparency.org/en/cpi/2024/media-kit',
            'description': 'CPI 2024 published February 2025'
        },
        '2023': {
            'main_page': 'https://www.transparency.org/en/cpi/2023',
            'description': 'CPI 2023'
        }
    }

    # URLs alternatives - sources communautaires (CSV)
    # PRIORITÉ: GitHub raw est le plus fiable, DataHub a des problèmes 404
    ALT_URLS = {
        'github_csv': 'https://raw.githubusercontent.com/datasets/corruption-perceptions-index/master/data/cpi.csv',
        'github_csv_alt': 'https://raw.githubusercontent.com/vincentarelbundock/Rdatasets/master/csv/datasets/corruption.csv',
        'ourworldindata': 'https://raw.githubusercontent.com/owid/owid-datasets/master/datasets/Corruption%20Perception%20Index%20-%20Transparency%20International/Corruption%20Perception%20Index%20-%20Transparency%20International.csv'
    }

    # Configuration de timeout et retry
    DEFAULT_TIMEOUT = 60  # Plus long pour téléchargement Excel
    MAX_RETRIES = 3
    RETRY_DELAY = 2

    def __init__(self, timeout: int = None, max_retries: int = None):
        """
        Args:
            timeout: Timeout en secondes pour les requêtes (défaut: 60)
            max_retries: Nombre maximum de tentatives (défaut: 3)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0 (+https://github.com/geopol)',
            'Accept': 'text/csv,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries or self.MAX_RETRIES
        self.circuit_breaker = {'failures': 0, 'last_failure': None, 'open': False}
        # Cache géré par security_cache.py
        self.data_cache = {}
        self.cache_timestamp = None
        self.cache_duration = 86400  # 24 heures (données annuelles)

    def _check_circuit_breaker(self) -> bool:
        """Vérifie si le circuit breaker est ouvert"""
        if not self.circuit_breaker['open']:
            return True

        # Circuit ouvert: vérifier si on peut réessayer (après 60 secondes)
        if self.circuit_breaker['last_failure']:
            elapsed = (datetime.now() - self.circuit_breaker['last_failure']).total_seconds()
            if elapsed > 60:
                logger.info("[CPI] Circuit breaker: tentative de récupération")
                self.circuit_breaker['open'] = False
                self.circuit_breaker['failures'] = 0
                return True

        logger.warning("[CPI] Circuit breaker ouvert - requête bloquée")
        return False

    def _record_failure(self):
        """Enregistre un échec pour le circuit breaker"""
        self.circuit_breaker['failures'] += 1
        self.circuit_breaker['last_failure'] = datetime.now()
        if self.circuit_breaker['failures'] >= 3:
            self.circuit_breaker['open'] = True
            logger.error("[CPI] Circuit breaker ouvert après 3 échecs")

    def _record_success(self):
        """Enregistre un succès - réinitialise le circuit breaker"""
        if self.circuit_breaker['failures'] > 0:
            logger.info("[CPI] Circuit breaker: récupération réussie")
        self.circuit_breaker['failures'] = 0
        self.circuit_breaker['open'] = False

    @cached_connector_method('transparency_cpi')
    def get_cpi_data(self, year: int = None) -> Dict[str, Any]:
        """
        Récupère les données CPI pour une année spécifique
        Args:
            year: Année (2020-2023). Si None, dernière année disponible
        Returns:
            Dict avec résultats
        """
        if year is None:
            year = max(int(y) for y in self.CPI_URLS.keys())

        try:
            # Vérifier cache
            cache_key = f"cpi_{year}"
            if cache_key in self.data_cache and self.cache_timestamp:
                cache_age = (datetime.now() - self.cache_timestamp).total_seconds()
                if cache_age < self.cache_duration:
                    logger.info(f"[CPI] Données en cache ({cache_age:.0f}s)")
                    return self.data_cache[cache_key]

            # Essayer différentes sources
            data = self._fetch_cpi_from_sources(year)

            if not data:
                return {
                    'success': False,
                    'error': 'Données CPI indisponibles',
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Transparency International CPI data currently unavailable'
                }

            # Formater les résultats
            formatted_data = self._format_cpi_data(data, year)

            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'Transparency International CPI',
                'year': year,
                'total_countries': len(formatted_data),
                'data': formatted_data,
                'statistics': self._calculate_cpi_stats(formatted_data),
                'metadata': {
                    'description': 'Corruption Perceptions Index (0-100, higher = less corrupt)',
                    'source_url': f'https://www.transparency.org/en/cpi/{year}',
                    'update_frequency': 'Annual'
                }
            }

            # Mettre en cache
            self.data_cache[cache_key] = result
            self.cache_timestamp = datetime.now()

            logger.info(f"[OK] {len(formatted_data)} pays CPI {year} récupérés")
            return result

        except Exception as e:
            logger.error(f"[ERROR] Erreur CPI {year}: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'message': 'Erreur récupération données CPI'
            }

    def _fetch_cpi_from_sources(self, year: int) -> List[Dict]:
        """
        Essaie différentes sources pour les données CPI
        Avec fallback sur les années précédentes si nécessaire
        """
        sources = [
            self._fetch_cpi_csv_public,
            self._fetch_cpi_excel_public,
            self._fetch_cpi_api  # Hypothétique
        ]

        # Essayer d'abord l'année demandée, puis les années précédentes
        years_to_try = [year, year - 1, year - 2, year - 3]

        for try_year in years_to_try:
            for source_func in sources:
                try:
                    data = source_func(try_year)
                    if data and len(data) > 1:  # Au moins 2 pays
                        logger.info(f"[CPI] Données récupérées via {source_func.__name__} pour {try_year}")
                        return data
                except Exception as e:
                    logger.warning(f"[CPI] Échec source {source_func.__name__} pour {try_year}: {e}")
                    continue

        # Dernier recours: récupérer toutes les données disponibles (sans filtre d'année)
        logger.info("[CPI] Tentative sans filtre d'année...")
        try:
            data = self._fetch_cpi_csv_all_years()
            if data:
                logger.info(f"[CPI] {len(data)} entrées récupérées (toutes années)")
                return data
        except Exception as e:
            logger.warning(f"[CPI] Échec récupération toutes années: {e}")

        return []

    def _fetch_cpi_csv_all_years(self) -> List[Dict]:
        """
        Récupère toutes les données CPI disponibles (sans filtre d'année)
        Retourne les données de l'année la plus récente
        """
        urls_to_try = [
            ('GitHub Raw', self.ALT_URLS['github_csv']),
            ('GitHub Alt', self.ALT_URLS.get('github_csv_alt', '')),
            ('Our World in Data', self.ALT_URLS.get('ourworldindata', ''))
        ]
        urls_to_try = [(name, url) for name, url in urls_to_try if url]

        for source_name, csv_url in urls_to_try:
            try:
                logger.info(f"[CPI CSV] Téléchargement toutes données depuis {source_name}")
                response = self.session.get(csv_url, timeout=self.timeout)
                response.raise_for_status()

                csv_data = StringIO(response.text)
                reader = csv.DictReader(csv_data)

                # Récupérer toutes les données
                all_data = []
                years_found = set()
                for row in reader:
                    try:
                        clean_row = {k.strip(): v.strip() if v else '' for k, v in row.items()}
                        row_year = clean_row.get('Year', clean_row.get('year', ''))
                        if row_year:
                            years_found.add(int(row_year))
                        all_data.append(clean_row)
                    except Exception:
                        continue

                if not all_data:
                    continue

                # Si on a trouvé des années, filtrer sur la plus récente
                if years_found:
                    most_recent_year = max(years_found)
                    recent_data = [d for d in all_data
                                   if d.get('Year', d.get('year', '')) == str(most_recent_year)]
                    if recent_data:
                        logger.info(f"[CPI CSV] Année la plus récente: {most_recent_year}, {len(recent_data)} pays")
                        return recent_data

                # Sinon retourner toutes les données
                logger.info(f"[CPI CSV] {len(all_data)} entrées récupérées")
                return all_data

            except Exception as e:
                logger.warning(f"[CPI CSV] Erreur {source_name}: {e}")
                continue

        return []

    def _fetch_cpi_csv_public(self, year: int) -> List[Dict]:
        """
        Tente de récupérer les données CSV depuis les sources communautaires
        GitHub est prioritaire car DataHub a des problèmes 404
        """
        # Ordre de priorité: GitHub first (plus fiable)
        urls_to_try = [
            ('GitHub Raw', self.ALT_URLS['github_csv']),
            ('GitHub Alt', self.ALT_URLS.get('github_csv_alt', '')),
            ('Our World in Data', self.ALT_URLS.get('ourworldindata', ''))
        ]
        # Filtrer les URLs vides
        urls_to_try = [(name, url) for name, url in urls_to_try if url]

        for source_name, csv_url in urls_to_try:
            if not self._check_circuit_breaker():
                logger.warning(f"[CPI CSV] Circuit breaker ouvert - skip {source_name}")
                continue

            try:
                logger.info(f"[CPI CSV] Téléchargement depuis {source_name}: {csv_url}")
                response = self.session.get(csv_url, timeout=self.timeout)
                response.raise_for_status()

                # Lire CSV
                csv_data = StringIO(response.text)
                reader = csv.DictReader(csv_data)

                data = []
                for row in reader:
                    try:
                        # Nettoyer les noms de colonnes
                        clean_row = {k.strip(): v.strip() if v else '' for k, v in row.items()}

                        # Filtrer par année si spécifiée
                        row_year = clean_row.get('Year', clean_row.get('year', ''))
                        if row_year and int(row_year) == year:
                            data.append(clean_row)
                        elif not row_year:  # Données sans année (prendre toutes)
                            data.append(clean_row)

                    except Exception as e:
                        logger.debug(f"[CPI CSV] Erreur parsing ligne: {e}")
                        continue

                if data:
                    logger.info(f"[CPI CSV] {len(data)} lignes récupérées depuis {source_name}")
                    self._record_success()
                    return data
                else:
                    logger.warning(f"[CPI CSV] Aucune donnée pour {year} dans {source_name}")

            except requests.exceptions.RequestException as e:
                logger.warning(f"[CPI CSV] Erreur requête {source_name}: {e}")
                self._record_failure()
                continue
            except Exception as e:
                logger.warning(f"[CPI CSV] Erreur inattendue {source_name}: {e}")
                self._record_failure()
                continue

        logger.error(f"[CPI CSV] Échec de toutes les sources CSV")
        return []

    def _fetch_cpi_excel_public(self, year: int) -> List[Dict]:
        """
        Tente de récupérer les données Excel publiques
        Nécessite pandas pour lire Excel
        """
        try:
            import pandas as pd

            excel_url = self.CPI_URLS.get(str(year))
            if not excel_url:
                logger.warning(f"[CPI Excel] URL non trouvée pour {year}")
                return []

            logger.info(f"[CPI Excel] Téléchargement {excel_url}")
            response = self.session.get(excel_url, timeout=60)
            response.raise_for_status()

            # Lire Excel avec pandas
            import io
            excel_data = io.BytesIO(response.content)

            # Essayer différentes feuilles
            sheets_to_try = ['CPI Score', 'CPI 2023', 'Data', 'Sheet1']
            df = None

            for sheet in sheets_to_try:
                try:
                    df = pd.read_excel(excel_data, sheet_name=sheet)
                    logger.info(f"[CPI Excel] Feuille '{sheet}' lue avec succès")
                    break
                except Exception as e:
                    logger.debug(f"[CPI Excel] Échec feuille '{sheet}': {e}")
                    continue

            if df is None or df.empty:
                logger.warning("[CPI Excel] Aucune feuille valide trouvée")
                return []

            # Convertir en liste de dicts
            data = df.to_dict('records')
            logger.info(f"[CPI Excel] {len(data)} lignes converties")

            return data

        except ImportError:
            logger.warning("[CPI Excel] pandas non installé, skip Excel source")
            return []
        except Exception as e:
            logger.warning(f"[CPI Excel] Erreur: {e}")
            return []

    def _fetch_cpi_api(self, year: int) -> List[Dict]:
        """
        Tente d'utiliser l'API Transparency International (hypothétique)
        """
        # Cette méthode est hypothétique - l'API publique peut ne pas exister
        try:
            api_url = self.ALT_URLS['api']
            params = {'year': year}

            logger.info(f"[CPI API] Appel {api_url}")
            response = self.session.get(api_url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            return data.get('results', [])

        except Exception as e:
            logger.debug(f"[CPI API] Échec (normal si API non disponible): {e}")
            return []

    def _format_cpi_data(self, raw_data: List[Dict], year: int) -> List[Dict[str, Any]]:
        """
        Formate les données CPI au format GEOPOL standardisé
        """
        formatted = []

        for item in raw_data:
            try:
                # Extraire informations selon différents formats possibles
                country, score, rank = self._extract_cpi_fields(item)

                if not country or score is None:
                    continue

                # Assurer les types
                try:
                    score_float = float(score)
                    rank_int = int(rank) if rank else 0
                except (ValueError, TypeError):
                    continue

                # Valider plage score
                if not (0 <= score_float <= 100):
                    continue

                formatted.append({
                    'country': country,
                    'country_code': self._get_country_code(country),
                    'cpi_score': score_float,
                    'global_rank': rank_int,
                    'year': year,
                    'trend': self._estimate_trend(country, score_float, year),
                    'region': self._get_region(country),
                    'source': 'Transparency International CPI',
                    'data_quality': 'official' if score_float > 0 else 'estimated'
                })

            except Exception as e:
                logger.debug(f"[CPI] Erreur format item: {e}")
                continue

        # Trier par score décroissant
        formatted.sort(key=lambda x: x['cpi_score'], reverse=True)

        # Ajuster les rangs (après tri)
        for i, item in enumerate(formatted):
            item['global_rank'] = i + 1

        return formatted

    def _extract_cpi_fields(self, item: Dict) -> tuple:
        """
        Extrait pays, score et rang selon différents formats de données
        """
        # Essayer différents noms de colonnes
        country_keys = ['Country', 'country', 'Country/Territory', 'Jurisdiction']
        score_keys = ['CPI Score', 'Score', 'cpi_score', 'CPI']
        rank_keys = ['Rank', 'rank', 'Global Rank', 'Position']

        country = None
        score = None
        rank = None

        for key in country_keys:
            if key in item and item[key]:
                country = str(item[key]).strip()
                break

        for key in score_keys:
            if key in item and item[key]:
                score = item[key]
                break

        for key in rank_keys:
            if key in item and item[key]:
                rank = item[key]
                break

        return country, score, rank

    def _get_country_code(self, country_name: str) -> str:
        """
        Convertit nom de pays en code ISO (simplifié)
        """
        country_mapping = {
            'Denmark': 'DNK', 'Finland': 'FIN', 'New Zealand': 'NZL',
            'Norway': 'NOR', 'Singapore': 'SGP', 'Sweden': 'SWE',
            'Switzerland': 'CHE', 'Netherlands': 'NLD', 'Germany': 'DEU',
            'Luxembourg': 'LUX', 'United Kingdom': 'GBR', 'Australia': 'AUS',
            'Canada': 'CAN', 'United States': 'USA', 'France': 'FRA',
            'Japan': 'JPN', 'South Korea': 'KOR', 'Italy': 'ITA',
            'Spain': 'ESP', 'Portugal': 'PRT', 'Poland': 'POL'
        }
        return country_mapping.get(country_name, '')

    def _get_region(self, country_name: str) -> str:
        """
        Détermine la région d'un pays
        """
        region_mapping = {
            # Europe
            'Denmark': 'Europe', 'Finland': 'Europe', 'Norway': 'Europe',
            'Sweden': 'Europe', 'Switzerland': 'Europe', 'Netherlands': 'Europe',
            'Germany': 'Europe', 'Luxembourg': 'Europe', 'United Kingdom': 'Europe',
            'France': 'Europe', 'Italy': 'Europe', 'Spain': 'Europe',
            'Portugal': 'Europe', 'Poland': 'Europe',
            # Amériques
            'United States': 'Americas', 'Canada': 'Americas',
            # Asie/Pacifique
            'New Zealand': 'Asia Pacific', 'Singapore': 'Asia Pacific',
            'Australia': 'Asia Pacific', 'Japan': 'Asia Pacific',
            'South Korea': 'Asia Pacific'
        }
        return region_mapping.get(country_name, 'Unknown')

    def _estimate_trend(self, country: str, current_score: float, year: int) -> str:
        """
        Estime la tendance (simplifié - faute de données historiques)
        """
        # En production, comparer avec l'année précédente
        return 'Stable'

    def _calculate_cpi_stats(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Calcule les statistiques sur les données CPI
        """
        if not data:
            return {'total': 0, 'average_score': 0, 'by_region': {}}

        scores = [item['cpi_score'] for item in data]
        by_region = {}

        for item in data:
            region = item['region']
            by_region[region] = by_region.get(region, 0) + 1

        return {
            'total': len(data),
            'average_score': round(sum(scores) / len(scores), 1),
            'min_score': min(scores),
            'max_score': max(scores),
            'by_region': by_region,
            'top_10_avg': round(sum(scores[:10]) / min(10, len(scores)), 1) if scores else 0,
            'bottom_10_avg': round(sum(scores[-10:]) / min(10, len(scores)), 1) if scores else 0
        }

    @cached_connector_method('transparency_cpi')
    def get_cpi_ranking(self, limit: int = 20) -> Dict[str, Any]:
        """
        Récupère le classement CPI (top pays)
        """
        result = self.get_cpi_data()
        if not result['success']:
            return result

        data = result['data'][:limit]

        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'source': 'Transparency International CPI',
            'ranking': data,
            'limit': limit
        }

    @cached_connector_method('transparency_cpi')
    def get_country_cpi(self, country_name: str) -> Dict[str, Any]:
        """
        Récupère les données CPI pour un pays spécifique
        """
        result = self.get_cpi_data()
        if not result['success']:
            return result

        for item in result['data']:
            if item['country'].lower() == country_name.lower():
                return {
                    'success': True,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'Transparency International CPI',
                    'country_data': item
                }

        return {
            'success': False,
            'error': f'Pays {country_name} non trouvé dans les données CPI',
            'timestamp': datetime.now().isoformat()
        }


def get_transparency_cpi_connector() -> TransparencyCPIConnector:
    """Factory pour obtenir le connecteur CPI"""
    return TransparencyCPIConnector()


__all__ = ['TransparencyCPIConnector', 'get_transparency_cpi_connector']