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
        
        self._init_database()

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
            
            logger.info("[OK] Tables démographiques initialisées")
        except Exception as e:
            logger.error(f"Erreur init DB démographique: {e}")

    # ============================================================
    # EUROSTAT API
    # ============================================================
    
    def fetch_eurostat_data(self, dataset_code: str, filters: Dict = None) -> List[Dict]:
        """
        Récupère des données Eurostat
        Ex: demo_pjan (population), nama_10_gdp (PIB)
        """
        try:
            base_url = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
            url = f"{base_url}/{dataset_code}"
            
            params = {
                'format': 'JSON',
                'lang': 'EN'
            }
            
            if filters:
                params.update(filters)
            
            logger.info(f"[DATA] Eurostat: {dataset_code}")
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_eurostat_response(data, dataset_code)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur Eurostat {dataset_code}: {e}")
            return []
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
            geo_dim = dimensions.get('geo', {}).get('category', {}).get('label', {})
            time_dim = dimensions.get('time', {}).get('category', {}).get('label', {})
            
            # Parcourir les valeurs
            for key, value in values.items():
                if value is None:
                    continue
                
                # Décoder la clé (format: "index_geo_time")
                parts = key.split('_') if '_' in key else [key]
                
                if len(parts) >= 2:
                    geo_code = parts[-2] if len(parts) > 2 else parts[0]
                    year_str = parts[-1]
                    
                    try:
                        year = int(year_str)
                        country_name = geo_dim.get(geo_code, geo_code)
                        
                        results.append({
                            'indicator_id': dataset_code,
                            'country_code': geo_code,
                            'country_name': country_name,
                            'value': float(value),
                            'year': year,
                            'source': 'eurostat',
                            'unit': data.get('extension', {}).get('datasetId', '')
                        })
                    except (ValueError, TypeError):
                        continue
            
            logger.info(f"[OK] Eurostat: {len(results)} entrées parsées")
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
        try:
            base_url = "https://data-api.ecb.europa.eu/service/data"
            url = f"{base_url}/{flow_ref}"
            
            if key:
                url += f"/{key}"
            
            params = {
                'format': 'jsondata',
                'detail': 'dataonly'
            }
            
            logger.info(f"[BANK] BCE: {flow_ref}")
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_ecb_response(data, flow_ref)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur BCE {flow_ref}: {e}")
            return []
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
            dimensions = structure.get('dimensions', {}).get('series', [])
            
            # Récupérer les observations
            if 'series' in dataset:
                for series_key, series_data in dataset['series'].items():
                    observations = series_data.get('observations', {})
                    
                    for time_idx, obs_list in observations.items():
                        value = obs_list[0] if obs_list else None
                        
                        if value is not None:
                            results.append({
                                'indicator_id': flow_ref,
                                'country_code': 'EU',
                                'country_name': 'Zone Euro',
                                'value': float(value),
                                'year': 2024,  # À améliorer avec le parsing du temps
                                'source': 'ecb',
                                'unit': 'index'
                            })
            
            logger.info(f"[OK] BCE: {len(results)} entrées parsées")
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
        try:
            if countries is None:
                countries = ['all']
            
            country_str = ';'.join(countries)
            url = f"https://api.worldbank.org/v2/country/{country_str}/indicator/{indicator}"
            
            params = {
                'format': 'json',
                'per_page': 1000,
                'date': '2010:2024'
            }
            
            logger.info(f"[GLOBAL] World Bank: {indicator}")
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_worldbank_response(data, indicator)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur World Bank {indicator}: {e}")
            return []
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
                    'unit': record.get('unit', '')
                })
            
            logger.info(f"[OK] World Bank: {len(results)} entrées parsées")
            return results
            
        except Exception as e:
            logger.error(f"Erreur parse World Bank: {e}")
            return results

    # ============================================================
    # STOCKAGE ET RÉCUPÉRATION
    # ============================================================
    
    def store_indicators(self, indicators: List[Dict]) -> int:
        """Stocke les indicateurs en base de données"""
        stored = 0
        
        for ind in indicators:
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
        
        logger.info(f"[DATA] Collecte terminée: {stored} indicateurs stockés")
        
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
