# Flask/demographic_module.py
"""
Module de collecte et gestion des données démographiques et socio-économiques
Sources: Eurostat, BCE, Banque Mondiale
"""

import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass, asdict
import time

logger = logging.getLogger(__name__)


@dataclass
class DemographicIndicator:
    """Structure pour un indicateur démographique"""
    indicator_id: str
    country_code: str
    country_name: str
    value: float
    year: int
    source: str  # 'eurostat', 'ecb', 'worldbank'
    category: str  # 'population', 'economy', 'social', 'health', 'education'
    unit: str
    last_update: str


class DemographicDataService:
    """Service de collecte de données démographiques multi-sources"""

    # Mapping des indicateurs vers leurs catégories
    INDICATOR_CATEGORIES = {
        # Population
        'demo_pjan': 'population',
        'demo_gind': 'population',
        'SP.POP.TOTL': 'population',
        'SP.POP.GROW': 'population',
        'SP.URB.TOTL': 'population',

        # Économie
        'nama_10_gdp': 'economy',
        'NY.GDP.MKTP.CD': 'economy',
        'NY.GDP.PCAP.CD': 'economy',
        'NY.GDP.MKTP.KD.ZG': 'economy',
        'ICP': 'economy',
        'EXR': 'economy',

        # Social
        'une_rt_a': 'social',
        'SL.UEM.TOTL.ZS': 'social',
        'SI.POV.GINI': 'social',

        # Santé
        'hlth_rs_prshp': 'health',
        'SH.MED.PHYS.ZS': 'health',
        'SP.DYN.LE00.IN': 'health',

        # Éducation
        'educ_uoe_enra': 'education',
        'SE.XPD.TOTL.GD.ZS': 'education',
        'SE.PRM.NENR': 'education',
    }

    def __init__(self, db_manager):
        self.db = db_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0',
            'Accept': 'application/json'
        })

        # Cache en mémoire (5 minutes)
        self._cache = {}
        self._cache_duration = 300
        self._cache_timestamps = {}

        self._init_database()

    def _get_category(self, indicator_id: str) -> str:
        """Détermine la catégorie d'un indicateur"""
        return self.INDICATOR_CATEGORIES.get(indicator_id, 'unknown')

    def _fetch_with_retry(self, url: str, params: Dict = None, max_retries: int = 3) -> Optional[requests.Response]:
        """Effectue une requête HTTP avec retry en cas d'erreur"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=15)
                response.raise_for_status()
                return response
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout (tentative {attempt + 1}/{max_retries}): {url}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limit atteint (tentative {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(5 * (attempt + 1))
                elif e.response.status_code >= 500:
                    logger.warning(f"Erreur serveur {e.response.status_code} (tentative {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        time.sleep(3 ** attempt)
                else:
                    raise
            except requests.exceptions.RequestException as e:
                logger.warning(f"Erreur requête (tentative {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
        return None

    def _init_database(self):
        """Initialise les tables pour stocker les données démographiques"""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS demographic_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    indicator_id TEXT NOT NULL,
                    country_code TEXT NOT NULL,
                    country_name TEXT,
                    value REAL,
                    year INTEGER,
                    source TEXT,
                    category TEXT,
                    unit TEXT,
                    metadata TEXT,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(indicator_id, country_code, year, source)
                )
            """)

            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_demographic_country
                ON demographic_data(country_code, year)
            """)

            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_demographic_indicator
                ON demographic_data(indicator_id, year)
            """)

            logger.info("✅ Tables démographiques initialisées")
        except Exception as e:
            logger.error(f"Erreur init DB démographique: {e}")

    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Récupère une valeur du cache si elle est encore valide"""
        if cache_key in self._cache:
            timestamp = self._cache_timestamps.get(cache_key, 0)
            if time.time() - timestamp < self._cache_duration:
                logger.debug(f"Cache hit: {cache_key}")
                return self._cache[cache_key]
            else:
                # Cache expiré
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]
        return None

    def _set_cache(self, cache_key: str, value: Any):
        """Stocke une valeur dans le cache"""
        self._cache[cache_key] = value
        self._cache_timestamps[cache_key] = time.time()
        logger.debug(f"Cache set: {cache_key}")

    # ============================================================
    # EUROSTAT API
    # ============================================================
    
    def fetch_eurostat_data(self, dataset_code: str, filters: Dict = None) -> List[Dict]:
        """
        Récupère des données Eurostat
        Ex: demo_pjan (population), nama_10_gdp (PIB)
        """
        # Vérifier le cache
        cache_key = f"eurostat_{dataset_code}_{json.dumps(filters, sort_keys=True) if filters else ''}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            base_url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
            url = f"{base_url}/{dataset_code}"

            params = {
                'format': 'JSON',
                'lang': 'EN'
            }

            if filters:
                params.update(filters)

            logger.info(f"📊 Eurostat: {dataset_code}")
            response = self._fetch_with_retry(url, params=params)

            if response is None:
                logger.error(f"Échec après retries: Eurostat {dataset_code}")
                return []

            data = response.json()
            results = self._parse_eurostat_response(data, dataset_code)

            # Mettre en cache
            self._set_cache(cache_key, results)
            return results

        except Exception as e:
            logger.error(f"Erreur parsing Eurostat: {e}")
            return []

    def _parse_eurostat_response(self, data: Dict, dataset_code: str) -> List[Dict]:
        """Parse la réponse complexe d'Eurostat"""
        results = []

        try:
            # Structure Eurostat: data.value contient les valeurs
            if 'value' not in data or 'dimension' not in data:
                return results

            values = data['value']
            dimensions = data['dimension']

            # Récupérer les dimensions (pays, temps)
            geo_dim = dimensions.get('geo', {}).get('category', {}).get('index', [])
            time_dim = dimensions.get('time', {}).get('category', {}).get('index', [])
            geo_labels = dimensions.get('geo', {}).get('category', {}).get('label', {})
            time_labels = dimensions.get('time', {}).get('category', {}).get('label', {})

            # Récupérer les tailles des dimensions
            dim_sizes = data.get('size', [])
            if not dim_sizes:
                return results

            # Parcourir les valeurs
            for idx_str, value in values.items():
                if value is None:
                    continue

                try:
                    idx = int(idx_str)

                    # Calculer les indices multidimensionnels
                    # Format: index = geo_idx * time_size + time_idx (pour 2D)
                    if len(dim_sizes) >= 2:
                        time_size = dim_sizes[-1]
                        geo_idx = idx // time_size
                        time_idx = idx % time_size

                        # Récupérer les codes à partir des indices
                        geo_codes = list(geo_labels.keys())
                        time_codes = list(time_labels.keys())

                        if geo_idx < len(geo_codes) and time_idx < len(time_codes):
                            geo_code = geo_codes[geo_idx]
                            time_code = time_codes[time_idx]
                            country_name = geo_labels.get(geo_code, geo_code)

                            # Parser l'année
                            year = int(time_code) if time_code.isdigit() else int(time_code[:4])

                            results.append({
                                'indicator_id': dataset_code,
                                'country_code': geo_code,
                                'country_name': country_name,
                                'value': float(value),
                                'year': year,
                                'source': 'eurostat',
                                'category': self._get_category(dataset_code),
                                'unit': data.get('extension', {}).get('datasetId', '')
                            })
                except (ValueError, TypeError, IndexError) as e:
                    continue

            logger.info(f"✅ Eurostat: {len(results)} entrées parsées")
            return results

        except Exception as e:
            logger.error(f"Erreur parse Eurostat: {e}")
            return results

    # ============================================================
    # BCE (European Central Bank) API
    # ============================================================
    
    def fetch_ecb_data(self, flow_ref: str, key: str = None) -> List[Dict]:
        """
        Récupère des données BCE
        Ex: EXR (taux de change), ICP (inflation)
        """
        # Vérifier le cache
        cache_key = f"ecb_{flow_ref}_{key or ''}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            base_url = "https://data-api.ecb.europa.eu/service/data"
            url = f"{base_url}/{flow_ref}"

            if key:
                url += f"/{key}"

            params = {
                'format': 'jsondata',
                'detail': 'dataonly'
            }

            logger.info(f"🏦 BCE: {flow_ref}")
            response = self._fetch_with_retry(url, params=params)

            if response is None:
                logger.error(f"Échec après retries: BCE {flow_ref}")
                return []

            data = response.json()
            results = self._parse_ecb_response(data, flow_ref)

            # Mettre en cache
            self._set_cache(cache_key, results)
            return results

        except Exception as e:
            logger.error(f"Erreur parsing BCE: {e}")
            return []

    def _parse_ecb_response(self, data: Dict, flow_ref: str) -> List[Dict]:
        """Parse la réponse BCE (format SDMX-JSON)"""
        results = []

        try:
            if 'dataSets' not in data or not data['dataSets']:
                return results

            dataset = data['dataSets'][0]
            structure = data.get('structure', {})
            dimensions = structure.get('dimensions', {})

            # Récupérer la dimension temporelle
            obs_dimensions = dimensions.get('observation', [])
            time_values = []
            for dim in obs_dimensions:
                if dim.get('id') == 'TIME_PERIOD':
                    time_values = [v.get('id') for v in dim.get('values', [])]
                    break

            # Récupérer les observations
            if 'series' in dataset:
                for series_key, series_data in dataset['series'].items():
                    observations = series_data.get('observations', {})

                    for time_idx_str, obs_list in observations.items():
                        value = obs_list[0] if obs_list else None

                        if value is not None:
                            try:
                                time_idx = int(time_idx_str)
                                # Extraire l'année de la période temporelle
                                if time_idx < len(time_values):
                                    time_period = time_values[time_idx]
                                    # Format BCE: YYYY, YYYY-MM, YYYY-QX, etc.
                                    year = int(time_period.split('-')[0]) if '-' in time_period else int(time_period[:4])
                                else:
                                    year = datetime.now().year

                                results.append({
                                    'indicator_id': flow_ref,
                                    'country_code': 'EU',
                                    'country_name': 'Zone Euro',
                                    'value': float(value),
                                    'year': year,
                                    'source': 'ecb',
                                    'category': self._get_category(flow_ref),
                                    'unit': 'index'
                                })
                            except (ValueError, IndexError):
                                continue

            logger.info(f"✅ BCE: {len(results)} entrées parsées")
            return results

        except Exception as e:
            logger.error(f"Erreur parse BCE: {e}")
            return results

    # ============================================================
    # BANQUE MONDIALE API
    # ============================================================
    
    def fetch_worldbank_data(self, indicator: str, countries: List[str] = None) -> List[Dict]:
        """
        Récupère des données Banque Mondiale
        Ex: SP.POP.TOTL (population), NY.GDP.MKTP.CD (PIB)
        """
        # Vérifier le cache
        if countries is None:
            countries = ['all']
        cache_key = f"worldbank_{indicator}_{';'.join(sorted(countries))}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        try:
            country_str = ';'.join(countries)
            url = f"https://api.worldbank.org/v2/country/{country_str}/indicator/{indicator}"

            params = {
                'format': 'json',
                'per_page': 1000,
                'date': '2010:2024'
            }

            logger.info(f"🌍 World Bank: {indicator}")
            response = self._fetch_with_retry(url, params=params)

            if response is None:
                logger.error(f"Échec après retries: World Bank {indicator}")
                return []

            data = response.json()
            results = self._parse_worldbank_response(data, indicator)

            # Mettre en cache
            self._set_cache(cache_key, results)
            return results

        except Exception as e:
            logger.error(f"Erreur parsing World Bank: {e}")
            return []

    def _parse_worldbank_response(self, data: List, indicator: str) -> List[Dict]:
        """Parse la réponse Banque Mondiale"""
        results = []
        
        try:
            if len(data) < 2:
                return results
            
            records = data[1]  # Les données sont dans le 2e élément
            
            for record in records:
                if record.get('value') is None:
                    continue
                
                country_info = record.get('country', {})
                
                results.append({
                    'indicator_id': indicator,
                    'country_code': record.get('countryiso3code', ''),
                    'country_name': country_info.get('value', ''),
                    'value': float(record['value']),
                    'year': int(record.get('date', 0)),
                    'source': 'worldbank',
                    'category': self._get_category(indicator),
                    'unit': record.get('unit', '')
                })
            
            logger.info(f"✅ World Bank: {len(results)} entrées parsées")
            return results
            
        except Exception as e:
            logger.error(f"Erreur parse World Bank: {e}")
            return results

    # ============================================================
    # STOCKAGE ET RÉCUPÉRATION
    # ============================================================
    
    def _validate_indicator(self, ind: Dict) -> bool:
        """Valide un indicateur avant stockage"""
        required_fields = ['indicator_id', 'country_code', 'value', 'year', 'source']

        # Vérifier les champs requis
        for field in required_fields:
            if field not in ind or ind[field] is None:
                logger.warning(f"Indicateur invalide - champ manquant: {field}")
                return False

        # Vérifier les types
        try:
            float(ind['value'])
            int(ind['year'])
        except (ValueError, TypeError):
            logger.warning(f"Indicateur invalide - types incorrects: {ind}")
            return False

        # Vérifier l'année
        current_year = datetime.now().year
        if ind['year'] < 1900 or ind['year'] > current_year + 1:
            logger.warning(f"Indicateur invalide - année hors limites: {ind['year']}")
            return False

        return True

    def store_indicators(self, indicators: List[Dict]) -> int:
        """Stocke les indicateurs en base de données"""
        stored = 0

        for ind in indicators:
            # Valider l'indicateur
            if not self._validate_indicator(ind):
                continue

            try:
                self.db.execute_query("""
                    INSERT OR REPLACE INTO demographic_data
                    (indicator_id, country_code, country_name, value, year,
                     source, category, unit, metadata, last_update)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    ind.get('indicator_id'),
                    ind.get('country_code'),
                    ind.get('country_name'),
                    ind.get('value'),
                    ind.get('year'),
                    ind.get('source'),
                    ind.get('category', 'unknown'),
                    ind.get('unit'),
                    json.dumps(ind.get('metadata', {}))
                ))
                stored += 1
            except Exception as e:
                logger.error(f"Erreur stockage indicateur: {e}")

        return stored

    def get_country_data(self, country_code: str, year: int = None) -> Dict[str, Any]:
        """Récupère toutes les données d'un pays"""
        query = """
            SELECT indicator_id, value, year, source, category, unit
            FROM demographic_data
            WHERE country_code = ?
        """
        params = [country_code]
        
        if year:
            query += " AND year = ?"
            params.append(year)
        else:
            query += " ORDER BY year DESC"
        
        results = self.db.execute_query(query, params)
        
        # Organiser par catégorie
        data_by_category = {}
        for row in results:
            category = row[4]
            if category not in data_by_category:
                data_by_category[category] = []
            
            data_by_category[category].append({
                'indicator': row[0],
                'value': row[1],
                'year': row[2],
                'source': row[3],
                'unit': row[5]
            })
        
        return data_by_category

    def get_indicator_comparison(self, indicator_id: str, countries: List[str], 
                                  start_year: int = None) -> Dict:
        """Compare un indicateur entre plusieurs pays"""
        query = """
            SELECT country_code, country_name, year, value, unit
            FROM demographic_data
            WHERE indicator_id = ?
            AND country_code IN ({})
        """.format(','.join('?' * len(countries)))
        
        params = [indicator_id] + countries
        
        if start_year:
            query += " AND year >= ?"
            params.append(start_year)
        
        query += " ORDER BY year DESC, country_code"
        
        results = self.db.execute_query(query, params)
        
        # Organiser par pays
        comparison = {}
        for row in results:
            country = row[0]
            if country not in comparison:
                comparison[country] = {
                    'name': row[1],
                    'data': []
                }
            
            comparison[country]['data'].append({
                'year': row[2],
                'value': row[3],
                'unit': row[4]
            })
        
        return comparison

    # ============================================================
    # COLLECTIONS PRÉDÉFINIES
    # ============================================================
    
    def collect_essential_indicators(self, countries: List[str] = None) -> Dict:
        """Collecte les indicateurs essentiels pour analyse"""
        
        all_data = []
        stats = {
            'eurostat': 0,
            'ecb': 0,
            'worldbank': 0,
            'total': 0
        }
        
        # 1. Population (Eurostat)
        pop_data = self.fetch_eurostat_data('demo_pjan')
        all_data.extend(pop_data)
        stats['eurostat'] += len(pop_data)
        
        # 2. PIB (World Bank)
        gdp_data = self.fetch_worldbank_data('NY.GDP.MKTP.CD', countries)
        all_data.extend(gdp_data)
        stats['worldbank'] += len(gdp_data)
        
        # 3. Inflation (BCE)
        inflation_data = self.fetch_ecb_data('ICP')
        all_data.extend(inflation_data)
        stats['ecb'] += len(inflation_data)
        
        # Stocker
        stored = self.store_indicators(all_data)
        stats['total'] = stored
        
        logger.info(f"📊 Collecte terminée: {stored} indicateurs stockés")
        
        return {
            'success': True,
            'stats': stats,
            'indicators_count': len(all_data)
        }

    def get_available_countries(self) -> List[Dict]:
        """Liste des pays disponibles dans la base"""
        results = self.db.execute_query("""
            SELECT DISTINCT country_code, country_name, 
                   COUNT(*) as indicator_count,
                   MAX(year) as latest_year
            FROM demographic_data
            WHERE country_code IS NOT NULL
            GROUP BY country_code, country_name
            ORDER BY country_name
        """)
        
        return [
            {
                'code': row[0],
                'name': row[1],
                'indicators': row[2],
                'latest_year': row[3]
            }
            for row in results
        ]

    def get_available_indicators(self) -> List[Dict]:
        """Liste des indicateurs disponibles"""
        results = self.db.execute_query("""
            SELECT DISTINCT indicator_id, source, category,
                   COUNT(DISTINCT country_code) as country_count,
                   MAX(year) as latest_year
            FROM demographic_data
            GROUP BY indicator_id, source, category
            ORDER BY category, indicator_id
        """)
        
        return [
            {
                'id': row[0],
                'source': row[1],
                'category': row[2],
                'countries': row[3],
                'latest_year': row[4]
            }
            for row in results
        ]
