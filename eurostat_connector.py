# Flask/eurostat_connector.py
"""
Connecteur Eurostat amélioré avec sources multiples et cache intelligent
Sources : API Eurostat, World Bank, Data.gouv.fr, OCDE
"""

import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import time
import os
import json
import re
from urllib.parse import urlencode
import xml.etree.ElementTree as ET
import sqlite3

logger = logging.getLogger(__name__)

class SQLiteCache:
    """Cache SQLite pour stocker les données API avec TTL"""

    def __init__(self, db_path: str = 'instance/cache/eurostat_cache.db'):
        """Initialise le cache SQLite"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialise la base de données avec la table cache"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_cache (
                    key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ttl INTEGER DEFAULT 86400
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON api_cache(timestamp)')
            conn.commit()

    def get(self, key: str) -> Optional[Dict]:
        """Récupère des données du cache si non expirées"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    'SELECT data, timestamp, ttl FROM api_cache WHERE key = ?',
                    (key,)
                )
                row = cursor.fetchone()

                if row:
                    # Vérifier si le cache est expiré
                    timestamp = datetime.fromisoformat(row['timestamp'])
                    age = datetime.now() - timestamp
                    if age.total_seconds() < row['ttl']:
                        # Cache valide
                        return json.loads(row['data'])
                    else:
                        # Cache expiré, supprimer
                        conn.execute('DELETE FROM api_cache WHERE key = ?', (key,))
                        conn.commit()
                        logger.debug(f"Cache expiré supprimé: {key}")
                return None
        except Exception as e:
            logger.error(f"Erreur lecture cache SQLite: {e}")
            return None

    def set(self, key: str, data: Dict, ttl: int = 86400):
        """Stocke des données dans le cache avec TTL (secondes)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                data_json = json.dumps(data)
                conn.execute(
                    'INSERT OR REPLACE INTO api_cache (key, data, ttl) VALUES (?, ?, ?)',
                    (key, data_json, ttl)
                )
                conn.commit()
                logger.debug(f"Données mises en cache: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Erreur écriture cache SQLite: {e}")

    def clean_expired(self):
        """Nettoie les entrées expirées du cache"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                deleted = conn.execute(
                    'DELETE FROM api_cache WHERE timestamp < datetime("now", "-" || ttl || " seconds")'
                ).rowcount
                if deleted > 0:
                    logger.info(f"Cache nettoyé: {deleted} entrées expirées supprimées")
                conn.commit()
        except Exception as e:
            logger.error(f"Erreur nettoyage cache SQLite: {e}")

# Imports
import requests

# Import des autres connecteurs pour fallback
try:
    try:
        from .geopol_data.connectors.world_bank import WorldBankConnector
    except ImportError:
        from geopol_data.connectors.world_bank import WorldBankConnector
    WORLD_BANK_AVAILABLE = True
except ImportError:
    logger.warning("[WARN] World Bank Connector non disponible")
    WORLD_BANK_AVAILABLE = False

try:
    try:
        from .oecd_connector import OECDConnector
    except ImportError:
        from oecd_connector import OECDConnector
    OECD_AVAILABLE = True
except ImportError:
    logger.warning("[WARN] OECD Connector non disponible")
    OECD_AVAILABLE = False

try:
    try:
        from .comtrade_connector import ComtradeConnector
    except ImportError:
        from comtrade_connector import ComtradeConnector
    COMTRADE_AVAILABLE = True
except ImportError:
    logger.warning("[WARN] Comtrade Connector non disponible")
    COMTRADE_AVAILABLE = False

@dataclass
class EurostatDataset:
    """Définition d'un dataset Eurostat"""
    code: str
    name: str
    description: str
    category: str
    frequency: str
    unit: str
    last_update: str
    url: str


class EurostatAPIClient:
    """Client principal pour l'API Eurostat JSON-stat 2.0"""
    
    BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
    METADATA_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0"
    
    # Datasets clés avec leurs dimensions
    KEY_DATASETS = {
        'gdp': {
            'code': 'namq_10_gdp',
            'name': 'GDP and main components',
            'dimensions': {
                'unit': ['CP_MEUR', 'CLV10_MEUR', 'CLV_PCH_PRE'],
                's_adj': ['SCA', 'NSA'],
                'na_item': ['B1GQ', 'B1G'],
                'geo': ['FR', 'DE', 'IT', 'ES', 'EU27_2020']
            }
        },
        'inflation': {
            'code': 'prc_hicp_midx',
            'name': 'HICP - monthly data',
            'dimensions': {
                'unit': ['I15', 'RCH_A'],
                'coicop': ['CP00', 'FOOD', 'ENERGY'],
                'geo': ['FR', 'DE', 'IT', 'ES', 'EU27_2020']
            }
        },
        'unemployment': {
            'code': 'une_rt_m',
            'name': 'Unemployment rate',
            'dimensions': {
                's_adj': ['SA', 'NSA'],
                'age': ['TOTAL', 'Y15-24', 'Y25-74'],
                'sex': ['T', 'M', 'F'],
                'geo': ['FR', 'DE', 'IT', 'ES', 'EU27_2020']
            }
        },
        'trade': {
            'code': 'ext_lt_intratrd',
            'name': 'Intra and Extra-EU trade by Member State and by product group',
            'dimensions': {
                'freq': ['A'],  # Annual
                'indic_et': ['PC_TOT_IMP', 'PC_TOT_EXP', 'MIO_BAL_VAL'],  # Import share, export share, balance value
                'sitc06': ['TOTAL', 'SITC0_1', 'SITC2_4', 'SITC3', 'SITC5', 'SITC6_8', 'SITC7', 'SITC9'],
                'partner': ['EU27_2020', 'EXT_EU27_2020', 'WORLD'],
                'geo': ['FR', 'DE', 'IT', 'ES', 'EU27_2020'],
                'time': []  # Will be filled automatically
            }
        },
        'gini': {
            'code': 'ilc_di12',
            'name': 'Gini coefficient',
            'dimensions': {
                'unit': ['PC'],
                'indic_il': ['GINI'],
                'geo': ['FR', 'DE', 'IT', 'ES', 'EU27_2020']
            }
        }
    }
    
    def __init__(self, cache_dir: str = 'instance/cache/eurostat', use_sqlite_cache: bool = True):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'EconomicDashboard/2.0 (educational)',
            'Accept': 'application/json',
            'Accept-Language': 'en,fr;q=0.9'
        })

        # Cache SQLite (recommandé pour performances et historique)
        self.sqlite_cache = None
        if use_sqlite_cache:
            try:
                self.sqlite_cache = SQLiteCache(os.path.join(cache_dir, 'eurostat_cache.db'))
                logger.info("[OK] Cache SQLite initialisé")
            except Exception as e:
                logger.warning(f"[WARN] Impossible d'initialiser le cache SQLite: {e}")
                self.sqlite_cache = None

        # Cache en mémoire pour les métadonnées
        self.dataset_cache = {}
        self.last_refresh = {}

        logger.info("[OK] Eurostat API Client initialisé")
    
    def get_dataset_info(self, dataset_code: str) -> Optional[Dict]:
        """Récupère les métadonnées d'un dataset"""
        cache_key = f"meta_{dataset_code}"
        ttl_seconds = 604800  # 7 jours en secondes

        # 1. Essayer le cache SQLite (si activé)
        if self.sqlite_cache:
            cached_data = self.sqlite_cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"[CACHE SQLITE] Métadonnées récupérées du cache: {dataset_code}")
                return cached_data

        # 2. Fallback: cache fichier JSON (compatibilité)
        cache_file = os.path.join(self.cache_dir, f"meta_{dataset_code}.json")
        if os.path.exists(cache_file):
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if cache_age.days < 7:  # Cache 7 jours pour les métadonnées
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        logger.debug(f"[CACHE FICHIER] Métadonnées récupérées du cache: {dataset_code}")
                        # Mettre aussi dans le cache SQLite si disponible
                        if self.sqlite_cache and data:
                            self.sqlite_cache.set(cache_key, data, ttl_seconds)
                        return data
                except:
                    pass

        # 3. Récupération depuis l'API
        try:
            url = f"{self.METADATA_URL}/metadata/{dataset_code}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Sauvegarder en cache SQLite (prioritaire)
                if self.sqlite_cache:
                    self.sqlite_cache.set(cache_key, data, ttl_seconds)

                # Sauvegarder aussi en cache fichier (compatibilité)
                try:
                    with open(cache_file, 'w') as f:
                        json.dump(data, f)
                except Exception as e:
                    logger.warning(f"Erreur sauvegarde cache fichier métadonnées: {e}")

                return data
        except Exception as e:
            logger.error(f"Erreur métadonnées {dataset_code}: {e}")

        return None
    
    def get_data(self, dataset_code: str, params: Dict = None) -> Optional[Dict]:
        """
        Récupère les données d'un dataset avec paramètres

        Args:
            dataset_code: Code du dataset Eurostat
            params: Paramètres de filtre (geo, time, unit, etc.)
        """
        cache_key = self._generate_cache_key(dataset_code, params)

        # 1. Essayer le cache SQLite (si activé)
        if self.sqlite_cache:
            cached_data = self.sqlite_cache.get(cache_key)
            if cached_data is not None:
                logger.debug(f"[CACHE SQLITE] Données récupérées du cache: {dataset_code}")
                return cached_data

        # 2. Fallback: cache fichier JSON (compatibilité)
        cache_file = os.path.join(self.cache_dir, f"data_{cache_key}.json")
        if os.path.exists(cache_file):
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if cache_age < timedelta(hours=24):
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                        logger.debug(f"[CACHE FICHIER] Données récupérées du cache: {dataset_code}")
                        # Mettre aussi dans le cache SQLite si disponible
                        if self.sqlite_cache and data:
                            self.sqlite_cache.set(cache_key, data)
                        return data
                except:
                    pass

        # 3. Récupération depuis l'API
        try:
            url = f"{self.BASE_URL}/{dataset_code}"
            default_params = {
                'format': 'JSON',
                'lang': 'EN',
                'lastTimePeriod': 20  # 20 dernières périodes
            }

            if params:
                default_params.update(params)

            logger.debug(f"[API] Requête Eurostat: {dataset_code} avec {default_params}")

            response = self.session.get(url, params=default_params, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # Vérifier que les données sont valides
                if self._validate_eurostat_data(data):
                    # Sauvegarder en cache SQLite (prioritaire)
                    if self.sqlite_cache:
                        self.sqlite_cache.set(cache_key, data)

                    # Sauvegarder aussi en cache fichier (compatibilité)
                    try:
                        with open(cache_file, 'w') as f:
                            json.dump(data, f)
                    except Exception as e:
                        logger.warning(f"Erreur sauvegarde cache fichier: {e}")

                    return data
                else:
                    logger.warning(f"Données invalides pour {dataset_code}")
            else:
                logger.warning(f"Statut {response.status_code} pour {dataset_code}")

        except Exception as e:
            logger.error(f"Erreur récupération {dataset_code}: {e}")

        return None
    
    def _generate_cache_key(self, dataset_code: str, params: Dict) -> str:
        """Génère une clé de cache unique"""
        if not params:
            return dataset_code
        
        # Trier les paramètres pour une clé cohérente
        sorted_params = sorted(params.items())
        param_str = '_'.join(f"{k}_{v}" for k, v in sorted_params)
        
        # Limiter la longueur et remplacer les caractères spéciaux
        param_str = re.sub(r'[^\w]', '_', param_str)[:100]
        
        return f"{dataset_code}_{param_str}"
    
    def _validate_eurostat_data(self, data: Dict) -> bool:
        """Valide les données Eurostat"""
        try:
            # Vérifier la structure de base
            if not isinstance(data, dict):
                return False
            
            # Vérifier la présence de valeurs
            if 'value' not in data:
                return False
            
            # Vérifier qu'il y a au moins une valeur
            values = data.get('value', {})
            if not values:
                return False
            
            # Vérifier les dimensions
            dimensions = data.get('dimension', {})
            if not dimensions:
                return False
            
            # Vérifier la dimension temps
            time_dim = dimensions.get('time', {})
            if not time_dim:
                return False
            
            return True
            
        except Exception:
            return False
    
    def parse_time_series(self, data: Dict, value_key: str = 'value') -> List[Dict]:
        """Parse les données Eurostat en séries temporelles"""
        try:
            values = data.get(value_key, {})
            dimensions = data.get('dimension', {})
            
            # Obtenir la dimension temps
            time_dim = dimensions.get('time', {})
            time_categories = time_dim.get('category', {}).get('index', {})
            
            if not values or not time_categories:
                return []
            
            # Créer un mapping index -> période
            time_mapping = {}
            for period, idx in time_categories.items():
                time_mapping[str(idx)] = period
            
            # Collecter les valeurs
            series = []
            for idx_str, value in values.items():
                period = time_mapping.get(idx_str)
                if period and value is not None:
                    try:
                        series.append({
                            'period': period,
                            'value': float(value),
                            'index': idx_str
                        })
                    except (ValueError, TypeError):
                        continue
            
            # Trier par période
            series.sort(key=lambda x: self._parse_period(x['period']))
            
            return series
            
        except Exception as e:
            logger.error(f"Erreur parsing time series: {e}")
            return []
    
    def _parse_period(self, period_str: str) -> datetime:
        """Convertit une période Eurostat en datetime"""
        try:
            # Formats: 2024, 2024-Q1, 2024M01, 2024W01
            if 'Q' in period_str:
                year, quarter = period_str.split('-')
                month = (int(quarter[1]) - 1) * 3 + 1
                return datetime(int(year), month, 1)
            elif 'M' in period_str:
                year, month = period_str.split('M')
                return datetime(int(year), int(month), 1)
            elif 'W' in period_str:
                year, week = period_str.split('W')
                # Approximation: première journée de la semaine
                return datetime(int(year), 1, 1) + timedelta(weeks=int(week)-1)
            else:
                # Année seule
                return datetime(int(period_str), 1, 1)
        except:
            return datetime.min
    
    def get_latest_value(self, dataset_code: str, params: Dict = None) -> Optional[Dict]:
        """Récupère la dernière valeur d'un dataset"""
        data = self.get_data(dataset_code, params)
        
        if not data:
            return None
        
        series = self.parse_time_series(data)
        if not series:
            return None
        
        # Dernière valeur (la plus récente)
        latest = series[-1]
        
        # Valeur précédente si disponible
        previous = series[-2] if len(series) > 1 else latest
        
        return {
            'value': latest['value'],
            'period': latest['period'],
            'previous_value': previous['value'],
            'previous_period': previous['period'],
            'change': latest['value'] - previous['value'],
            'change_percent': ((latest['value'] - previous['value']) / previous['value'] * 100 
                              if previous['value'] != 0 else 0),
            'series_length': len(series)
        }

class EurostatHybridConnector:
    """
    Connecteur hybride Eurostat avec sources multiples et fallback
    """
    
    def __init__(self):
        self.eurostat_client = EurostatAPIClient()
        
        # Initialiser les connecteurs de fallback
        self.fallback_clients = {}
        
        if WORLD_BANK_AVAILABLE:
            try:
                self.fallback_clients['world_bank'] = WorldBankConnector()
                logger.info("[OK] World Bank fallback disponible")
            except:
                pass
        
        if OECD_AVAILABLE:
            try:
                self.fallback_clients['oecd'] = OECDConnector()
                logger.info("[OK] OECD fallback disponible")
            except:
                pass
        
        # Configuration des indicateurs
        self.indicators_config = self._load_indicators_config()

        # Client COMTRADE pour données détaillées par code CN
        self.comtrade_client = None
        if COMTRADE_AVAILABLE:
            try:
                # Charger la clé API depuis les variables d'environnement
                comtrade_api_key = os.getenv('COMTRADE_API_KEY')
                self.comtrade_client = ComtradeConnector(api_key=comtrade_api_key)
                logger.info("[OK] Comtrade client initialisé pour données détaillées")
            except Exception as e:
                logger.warning(f"[WARN] Impossible d'initialiser Comtrade client: {e}")

        logger.info(f"[OK] Eurostat Hybrid Connector initialisé avec {len(self.fallback_clients)} fallbacks")
    
    def _load_indicators_config(self) -> Dict:
        """Charge la configuration des indicateurs"""
        return {
            'gdp': {
                'eurostat': {
                    'dataset': 'namq_10_gdp',
                    'params': {'geo': 'FR', 'unit': 'CLV_PCH_PRE', 's_adj': 'SCA', 'na_item': 'B1GQ'}
                },
                'world_bank': {'indicator': 'NY.GDP.MKTP.KD.ZG', 'country': 'FR'},
                'oecd': {'dataset': 'QNA', 'subject': 'GDP', 'measure': 'CQRSA'}
            },
            'inflation': {
                'eurostat': {
                    'dataset': 'prc_hicp_midx',
                    'params': {'geo': 'FR', 'coicop': 'CP00', 'unit': 'RCH_A'}
                },
                'world_bank': {'indicator': 'FP.CPI.TOTL.ZG', 'country': 'FR'},
                'oecd': {'dataset': 'CPI', 'subject': 'TOT', 'measure': 'GY'}
            },
            'unemployment': {
                'eurostat': {
                    'dataset': 'une_rt_m',
                    'params': {'geo': 'FR', 's_adj': 'SA', 'age': 'TOTAL', 'sex': 'T'}
                },
                'world_bank': {'indicator': 'SL.UEM.TOTL.ZS', 'country': 'FR'},
                'oecd': {'dataset': 'LFS', 'subject': 'UNR', 'measure': 'PC_LF'}
            },
            'trade_balance': {
                'eurostat': {
                    'dataset': 'ext_lt_intratrd',
                    'params': {'geo': 'FR', 'partner': 'WORLD', 'indic_et': 'MIO_BAL_VAL', 'sitc06': 'TOTAL', 'freq': 'A'}
                },
                'world_bank': {'indicator': 'NE.RSB.GNFS.CD', 'country': 'FR'},
                'oecd': {'dataset': 'EO', 'subject': 'TB', 'measure': 'PC_GDP'}
            },
            'gini': {
                'eurostat': {
                    'dataset': 'ilc_di12',
                    'params': {'geo': 'FR', 'indic_il': 'GINI', 'unit': 'PC'}
                },
                'world_bank': {'indicator': 'SI.POV.GINI', 'country': 'FR'},
                'oecd': {'dataset': 'IDD', 'subject': 'GINI', 'measure': 'A'}
            }
        }
    
    def get_indicator(self, indicator_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Récupère un indicateur avec stratégie de fallback
        """
        if indicator_id not in self.indicators_config:
            return {
                'success': False,
                'error': f'Indicateur {indicator_id} inconnu',
                'indicator_id': indicator_id
            }
        
        config = self.indicators_config[indicator_id]
        
        # Essayer Eurostat en premier
        logger.info(f"[DATA] Récupération {indicator_id} depuis Eurostat...")

        # Logique spéciale pour la balance commerciale (calcul EXP - IMP si nécessaire)
        if indicator_id == 'trade_balance':
            eurostat_data = self._get_trade_balance_from_eurostat(config.get('eurostat'))
        else:
            eurostat_data = self._get_from_eurostat(config.get('eurostat'))

        if eurostat_data and self._validate_indicator_data(eurostat_data):
            logger.info(f"[OK] {indicator_id} récupéré depuis Eurostat")
            return self._format_response(eurostat_data, 'eurostat', indicator_id)
        
        # Fallback 1: World Bank
        if 'world_bank' in config and 'world_bank' in self.fallback_clients:
            logger.info(f"[MIGRATION] Fallback {indicator_id} depuis World Bank...")
            wb_data = self._get_from_worldbank(config['world_bank'])
            if wb_data and self._validate_indicator_data(wb_data):
                logger.info(f"[OK] {indicator_id} récupéré depuis World Bank")
                return self._format_response(wb_data, 'world_bank', indicator_id)
        
        # Fallback 2: OECD
        if 'oecd' in config and 'oecd' in self.fallback_clients:
            logger.info(f"[MIGRATION] Fallback {indicator_id} depuis OECD...")
            oecd_data = self._get_from_oecd(config['oecd'])
            if oecd_data and self._validate_indicator_data(oecd_data):
                logger.info(f"[OK] {indicator_id} récupéré depuis OECD")
                return self._format_response(oecd_data, 'oecd', indicator_id)
        
        # Fallback final: données de référence
        logger.warning(f"[WARN] Toutes les sources échouées pour {indicator_id}, utilisation fallback")
        return self._get_fallback_data(indicator_id)
    
    def _get_from_eurostat(self, config: Dict) -> Optional[Dict]:
        """Récupère depuis Eurostat"""
        if not config:
            return None
        
        try:
            dataset = config['dataset']
            params = config.get('params', {})
            
            data = self.eurostat_client.get_data(dataset, params)
            if not data:
                return None
            
            latest = self.eurostat_client.get_latest_value(dataset, params)
            if not latest:
                return None
            
            # Récupérer les métadonnées
            metadata = self.eurostat_client.get_dataset_info(dataset)
            
            return {
                'value': latest['value'],
                'period': latest['period'],
                'previous_value': latest['previous_value'],
                'previous_period': latest['previous_period'],
                'change': latest['change'],
                'change_percent': latest['change_percent'],
                'metadata': metadata,
                'raw_data': data,
                'series': self.eurostat_client.parse_time_series(data)
            }
            
        except Exception as e:
            logger.error(f"Erreur Eurostat: {e}")
            return None

    def _get_trade_balance_from_eurostat(self, config: Dict) -> Optional[Dict]:
        """
        Récupère la balance commerciale depuis Eurostat avec fallback calculé
        Si MIO_BAL_VAL n'est pas disponible, calcule EXP - IMP
        """
        if not config:
            return None

        try:
            dataset = config['dataset']
            params = config.get('params', {}).copy()

            # 1. Essayer MIO_BAL_VAL (balance commerciale directe)
            logger.info("[TRADE] Essai balance commerciale MIO_BAL_VAL...")
            data = self.eurostat_client.get_data(dataset, params)
            latest = self.eurostat_client.get_latest_value(dataset, params) if data else None

            if latest:
                logger.info("[OK] Balance commerciale récupérée via MIO_BAL_VAL")
                metadata = self.eurostat_client.get_dataset_info(dataset)
                return {
                    'value': latest['value'],
                    'period': latest['period'],
                    'previous_value': latest['previous_value'],
                    'previous_period': latest['previous_period'],
                    'change': latest['change'],
                    'change_percent': latest['change_percent'],
                    'metadata': metadata,
                    'raw_data': data,
                    'series': self.eurostat_client.parse_time_series(data),
                    'calculation_method': 'direct_MIO_BAL_VAL'
                }

            # 2. Fallback: calculer EXP - IMP
            logger.info("[TRADE] Fallback: calcul EXP - IMP via MIO_EXP_VAL et MIO_IMP_VAL...")

            # Récupérer exports
            params_exp = params.copy()
            params_exp['indic_et'] = 'MIO_EXP_VAL'
            data_exp = self.eurostat_client.get_data(dataset, params_exp)
            latest_exp = self.eurostat_client.get_latest_value(dataset, params_exp) if data_exp else None

            # Récupérer imports
            params_imp = params.copy()
            params_imp['indic_et'] = 'MIO_IMP_VAL'
            data_imp = self.eurostat_client.get_data(dataset, params_imp)
            latest_imp = self.eurostat_client.get_latest_value(dataset, params_imp) if data_imp else None

            if latest_exp and latest_imp:
                # Vérifier que les périodes correspondent
                if latest_exp['period'] == latest_imp['period']:
                    trade_balance = latest_exp['value'] - latest_imp['value']
                    # Pour le change, utiliser les valeurs précédentes si disponibles
                    prev_exp = latest_exp.get('previous_value', latest_exp['value'])
                    prev_imp = latest_imp.get('previous_value', latest_imp['value'])
                    prev_balance = prev_exp - prev_imp
                    change = trade_balance - prev_balance
                    change_percent = (change / prev_balance * 100) if prev_balance != 0 else 0

                    logger.info(f"[OK] Balance commerciale calculée: {trade_balance:.1f} (EXP={latest_exp['value']:.1f}, IMP={latest_imp['value']:.1f})")

                    metadata = self.eurostat_client.get_dataset_info(dataset)
                    return {
                        'value': trade_balance,
                        'period': latest_exp['period'],
                        'previous_value': prev_balance,
                        'previous_period': latest_exp.get('previous_period', latest_exp['period']),
                        'change': change,
                        'change_percent': change_percent,
                        'metadata': metadata,
                        'raw_data': {'exports': data_exp, 'imports': data_imp},
                        'series': [],  # Pas de série historique pour le calcul
                        'calculation_method': 'calculated_EXP_minus_IMP',
                        'components': {
                            'exports': latest_exp['value'],
                            'imports': latest_imp['value'],
                            'exports_period': latest_exp['period'],
                            'imports_period': latest_imp['period']
                        }
                    }
                else:
                    logger.warning(f"[WARN] Périodes incohérentes: EXP={latest_exp['period']}, IMP={latest_imp['period']}")

            # 3. Si un seul des deux est disponible, utiliser celui-là avec signe opposé pour l'autre
            elif latest_exp or latest_imp:
                available = latest_exp if latest_exp else latest_imp
                component_type = 'exports' if latest_exp else 'imports'
                sign = 1 if latest_exp else -1  # Si seulement exports, balance = exports (pas d'imports). Si seulement imports, balance = -imports
                trade_balance = available['value'] * sign

                logger.warning(f"[WARN] Seulement {component_type} disponible, balance estimée: {trade_balance:.1f}")

                metadata = self.eurostat_client.get_dataset_info(dataset)
                return {
                    'value': trade_balance,
                    'period': available['period'],
                    'previous_value': available.get('previous_value', trade_balance),
                    'previous_period': available.get('previous_period', available['period']),
                    'change': available.get('change', 0),
                    'change_percent': available.get('change_percent', 0),
                    'metadata': metadata,
                    'raw_data': data_exp if latest_exp else data_imp,
                    'series': [],
                    'calculation_method': f'estimated_from_{component_type}',
                    'note': f'Seulement les {component_type} disponibles'
                }

            # 4. Aucune donnée disponible
            logger.warning("[WARN] Aucune donnée EXP/IMP disponible pour calcul balance commerciale")
            return None

        except Exception as e:
            logger.error(f"Erreur calcul balance commerciale: {e}")
            return None

    def _get_from_worldbank(self, config: Dict) -> Optional[Dict]:
        """Récupère depuis World Bank"""
        if 'world_bank' not in self.fallback_clients:
            return None
        
        try:
            client = self.fallback_clients['world_bank']
            indicator = config['indicator']
            country = config['country']
            
            # Implémentation dépend de votre client World Bank
            # Ceci est un exemple générique
            data = client.get_indicator(indicator, country)
            
            if data and 'values' in data and len(data['values']) >= 2:
                values = data['values']
                values.sort(key=lambda x: x.get('year', 0), reverse=True)
                
                latest = values[0]
                previous = values[1] if len(values) > 1 else latest
                
                return {
                    'value': latest.get('value', 0),
                    'period': str(latest.get('year', '')),
                    'previous_value': previous.get('value', 0),
                    'previous_period': str(previous.get('year', '')),
                    'change': latest.get('value', 0) - previous.get('value', 0),
                    'change_percent': ((latest.get('value', 0) - previous.get('value', 0)) / 
                                      previous.get('value', 0) * 100 if previous.get('value', 0) != 0 else 0),
                    'source': 'World Bank',
                    'raw_data': data
                }
                
        except Exception as e:
            logger.error(f"Erreur World Bank: {e}")
        
        return None
    
    def _get_from_oecd(self, config: Dict) -> Optional[Dict]:
        """Récupère depuis OECD"""
        if 'oecd' not in self.fallback_clients:
            return None
        
        try:
            client = self.fallback_clients['oecd']
            dataset = config['dataset']
            subject = config['subject']
            measure = config.get('measure', '')
            
            # Implémentation dépend de votre client OECD
            data = client.get_data(dataset, subject, measure, country='FRA')
            
            if data and 'series' in data and data['series']:
                series = data['series'][0]
                observations = series.get('observations', [])
                
                if len(observations) >= 2:
                    observations.sort(key=lambda x: x.get('period', ''), reverse=True)
                    
                    latest = observations[0]
                    previous = observations[1]
                    
                    return {
                        'value': latest.get('value', 0),
                        'period': latest.get('period', ''),
                        'previous_value': previous.get('value', 0),
                        'previous_period': previous.get('period', ''),
                        'change': latest.get('value', 0) - previous.get('value', 0),
                        'change_percent': ((latest.get('value', 0) - previous.get('value', 0)) / 
                                          previous.get('value', 0) * 100 if previous.get('value', 0) != 0 else 0),
                        'source': 'OECD',
                        'raw_data': data
                    }
                    
        except Exception as e:
            logger.error(f"Erreur OECD: {e}")
        
        return None
    
    def _validate_indicator_data(self, data: Dict) -> bool:
        """Valide les données d'un indicateur"""
        try:
            # Vérifications de base
            if not data:
                return False
            
            # Vérifier la présence des champs requis
            required = ['value', 'period']
            for field in required:
                if field not in data:
                    return False
            
            # Vérifier que la valeur est numérique
            value = data['value']
            if not isinstance(value, (int, float)):
                return False
            
            # Vérifier les plages raisonnables selon le type d'indicateur
            # (Ces plages sont approximatives)
            if 'inflation' in str(data.get('source', '')):
                if not (-10 <= value <= 50):  # Inflation entre -10% et 50%
                    return False
            elif 'unemployment' in str(data.get('source', '')):
                if not (0 <= value <= 30):  # Chômage entre 0% et 30%
                    return False
            elif 'gdp' in str(data.get('source', '')):
                if not (-20 <= value <= 20):  # Croissance PIB entre -20% et +20%
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _format_response(self, data: Dict, source: str, indicator_id: str) -> Dict[str, Any]:
        """Formate la réponse standardisée"""
        # Noms des indicateurs
        indicator_names = {
            'gdp': 'Croissance du PIB',
            'inflation': 'Inflation (IPCH)',
            'unemployment': 'Taux de chômage',
            'trade_balance': 'Balance commerciale',
            'gini': 'Indice GINI (inégalités)'
        }
        
        # Unités par indicateur
        indicator_units = {
            'gdp': '%',
            'inflation': '%',
            'unemployment': '%',
            'trade_balance': 'Millions €',
            'gini': 'Points (0-100)'
        }
        
        # Descriptions
        descriptions = {
            'gdp': 'Variation trimestrielle du PIB en volume',
            'inflation': 'Indice des prix à la consommation harmonisé',
            'unemployment': 'Taux de chômage désaisonnalisé',
            'trade_balance': 'Balance commerciale (exportations - importations)',
            'gini': 'Coefficient de Gini mesurant les inégalités de revenus'
        }
        
        # Catégories
        categories = {
            'gdp': 'macroeconomic',
            'inflation': 'prices',
            'unemployment': 'employment',
            'trade_balance': 'trade',
            'gini': 'inequality'
        }
        
        # Fiabilité par source
        reliability = {
            'eurostat': 'official',
            'world_bank': 'official',
            'oecd': 'official',
            'fallback': 'estimated'
        }
        
        name = indicator_names.get(indicator_id, indicator_id)
        unit = indicator_units.get(indicator_id, '')
        description = descriptions.get(indicator_id, '')
        category = categories.get(indicator_id, 'other')
        
        response = {
            'success': True,
            'indicator_id': indicator_id,
            'indicator_name': name,
            'value': round(data['value'], 3),
            'unit': unit,
            'period': data['period'],
            'source': source.upper(),
            'description': description,
            'category': category,
            'reliability': reliability.get(source, 'unknown'),
            'last_update': datetime.now().isoformat(),
            'metadata': {
                'raw_value': data['value'],
                'raw_period': data['period']
            }
        }
        
        # Ajouter les données comparatives si disponibles
        if 'previous_value' in data:
            response['previous_value'] = round(data['previous_value'], 3)
            response['previous_period'] = data['previous_period']
            response['change'] = round(data.get('change', 0), 3)
            response['change_percent'] = round(data.get('change_percent', 0), 2)
        
        # Ajouter les séries historiques si disponibles
        if 'series' in data and data['series']:
            # Limiter à 10 points maximum
            historical = data['series'][-10:] if len(data['series']) > 10 else data['series']
            response['historical'] = [
                {
                    'period': item['period'],
                    'value': round(item['value'], 3)
                }
                for item in historical
            ]
        
        # Ajouter des métadonnées supplémentaires
        if 'metadata' in data:
            response['dataset_info'] = data['metadata']
        
        return response
    
    def _get_fallback_data(self, indicator_id: str) -> Dict[str, Any]:
        """Données de secours avec valeurs réalistes"""
        fallbacks = {
            'gdp': {
                'value': 0.2,
                'period': '2024-Q3',
                'previous_value': 0.3,
                'previous_period': '2024-Q2',
                'change': -0.1,
                'change_percent': -33.3
            },
            'inflation': {
                'value': 2.3,
                'period': '2024-10',
                'previous_value': 2.2,
                'previous_period': '2024-09',
                'change': 0.1,
                'change_percent': 4.5
            },
            'unemployment': {
                'value': 7.4,
                'period': '2024-09',
                'previous_value': 7.5,
                'previous_period': '2024-08',
                'change': -0.1,
                'change_percent': -1.3
            },
            'trade_balance': {
                'value': -4500,
                'period': '2024-08',
                'previous_value': -4200,
                'previous_period': '2024-07',
                'change': -300,
                'change_percent': 7.1
            },
            'gini': {
                'value': 29.4,
                'period': '2023',
                'previous_value': 29.1,
                'previous_period': '2022',
                'change': 0.3,
                'change_percent': 1.0
            }
        }
        
        fb = fallbacks.get(indicator_id, {
            'value': 0,
            'period': '2024',
            'previous_value': 0,
            'previous_period': '2023',
            'change': 0,
            'change_percent': 0
        })
        
        return self._format_response(fb, 'fallback', indicator_id)
    
    def get_multiple_indicators(self, indicator_ids: List[str]) -> Dict[str, Any]:
        """Récupère plusieurs indicateurs en une fois"""
        results = {}
        
        for indicator_id in indicator_ids:
            logger.info(f"Récupération de {indicator_id}...")
            result = self.get_indicator(indicator_id)
            results[indicator_id] = result
            time.sleep(0.5)  # Respect des rate limits
        
        # Statistiques
        successful = sum(1 for r in results.values() if r.get('success'))
        
        return {
            'success': successful > 0,
            'indicators': results,
            'summary': {
                'total': len(indicator_ids),
                'successful': successful,
                'failed': len(indicator_ids) - successful,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    def search_datasets(self, keyword: str = None) -> List[Dict]:
        """Recherche des datasets Eurostat"""
        try:
            # URL pour la recherche (exemple, peut nécessiter adaptation)
            search_url = "https://ec.europa.eu/eurostat/api/dissemination/catalogue"
            
            params = {'format': 'JSON', 'lang': 'EN'}
            if keyword:
                params['search'] = keyword
            
            response = requests.get(search_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                datasets = []
                for item in data.get('datasets', [])[:20]:  # Limiter à 20 résultats
                    datasets.append({
                        'code': item.get('code', ''),
                        'name': item.get('name', ''),
                        'description': item.get('description', ''),
                        'last_update': item.get('lastUpdate', ''),
                        'url': item.get('url', '')
                    })
                
                return datasets
                
        except Exception as e:
            logger.error(f"Erreur recherche datasets: {e}")
        
        return []
    
    def get_trade_by_product(self, product_code: str, region: str = 'FR') -> Dict[str, Any]:
        """
        Récupère les données de commerce pour un produit spécifique
        
        Args:
            product_code: Code produit (CN, SITC, etc.)
            region: Code région (FR, DE, etc.)
        """
        # Essayer différents datasets et paramètres
        datasets_to_try = [
            {
                'dataset': 'ext_lt_intratrd',
                'params': {
                    'geo': region,
                    'partner': 'WORLD',
                    'indic_et': 'TRD_VAL',
                    'stk_flow': ['IMP', 'EXP']
                }
            },
            {
                'dataset': 'ds-045409',
                'params': {
                    'geo': region,
                    'partner': 'TOTAL',
                    'product': product_code,
                    'indic_et': 'TRD_VAL'
                }
            }
        ]
        
        for dataset_config in datasets_to_try:
            try:
                dataset = dataset_config['dataset']
                base_params = dataset_config['params']
                
                # Récupérer imports
                import_params = base_params.copy()
                if isinstance(import_params['stk_flow'], list):
                    import_params['stk_flow'] = 'IMP'
                
                import_data = self.eurostat_client.get_data(dataset, import_params)
                
                # Récupérer exports
                export_params = base_params.copy()
                if isinstance(export_params['stk_flow'], list):
                    export_params['stk_flow'] = 'EXP'
                
                export_data = self.eurostat_client.get_data(dataset, export_params)
                
                if import_data and export_data:
                    imports = self.eurostat_client.get_latest_value(dataset, import_params)
                    exports = self.eurostat_client.get_latest_value(dataset, export_params)
                    
                    if imports and exports:
                        return {
                            'success': True,
                            'product_code': product_code,
                            'region': region,
                            'imports': imports['value'],
                            'exports': exports['value'],
                            'trade_balance': exports['value'] - imports['value'],
                            'import_period': imports['period'],
                            'export_period': exports['period'],
                            'source': 'Eurostat',
                            'dataset': dataset
                        }
                        
            except Exception as e:
                logger.debug(f"Dataset {dataset_config['dataset']} échoué: {e}")
                continue
        
        # Fallback
        logger.warning(f"Pas de données commerce pour {product_code}, utilisation fallback")
        return {
            'success': True,
            'product_code': product_code,
            'region': region,
            'imports': 1000,
            'exports': 800,
            'trade_balance': -200,
            'import_period': '2024',
            'export_period': '2024',
            'source': 'Fallback',
            'note': 'Données estimées - source API indisponible'
        }

    def get_trade_by_cn(self, cn_code: str, region: str = 'EU27', year: int = 2023, skip_comtrade: bool = False) -> Dict[str, Any]:
        """
        Récupère les données de commerce pour un code CN (Combined Nomenclature)
        Utilise UN Comtrade API pour des données réelles, fallback vers Eurostat si indisponible

        Args:
            cn_code: Code CN à 2-8 chiffres
            region: Code région (EU27, FR, DE, etc.)
            year: Année
            skip_comtrade: Si True, saute l'appel COMTRADE (pour éviter boucle infinie)

        Returns:
            Dict avec imports/exports (données réelles) ou fallback
        """
        logger.info(f"[DATA] Récupération commerce pour CN {cn_code}, région {region}, année {year}")

        # 1. Essayer UN Comtrade (données réelles, officielles) SAUF si skip_comtrade=True
        if self.comtrade_client and not skip_comtrade:
            try:
                logger.info(f"[COMTRADE] Appel API pour CN {cn_code}...")
                comtrade_result = self.comtrade_client.get_trade_by_cn(cn_code, region, year)

                if comtrade_result and comtrade_result.get('success'):
                    logger.info(f"[OK] Données COMTRADE réelles obtenues pour CN {cn_code}")
                    # Format compatible avec l'interface Eurostat
                    return {
                        'success': True,
                        'product_code': cn_code,
                        'cn_code': cn_code,
                        'region': region,
                        'year': year,
                        'imports': comtrade_result.get('imports', 0),
                        'exports': comtrade_result.get('exports', 0),
                        'trade_balance': comtrade_result.get('trade_balance', 0),
                        'import_period': f"{year}-12-31",
                        'export_period': f"{year}-12-31",
                        'source': 'UN Comtrade',
                        'note': 'Données officielles Nations Unies',
                        'data_source': comtrade_result.get('data_source', {}),
                        'dependency_ratio': comtrade_result.get('dependency_ratio', 0),
                        'unit': comtrade_result.get('unit', 'Millions USD')
                    }
                else:
                    logger.warning(f"[WARN] COMTRADE retourné aucun résultat pour CN {cn_code}")
            except Exception as e:
                logger.error(f"[ERROR] Erreur COMTRADE pour CN {cn_code}: {e}")

        # 2. Fallback: essayer Eurostat (peut retourner des estimations)
        logger.info(f"[FALLBACK] Essai Eurostat pour CN {cn_code}...")
        try:
            # Convertir région EU27 vers EU27_2020 si nécessaire
            eurostat_region = region
            if region.upper() == 'EU27':
                eurostat_region = 'EU27_2020'

            # Utiliser get_trade_by_product (qui peut retourner des données Eurostat ou fallback)
            eurostat_result = self.get_trade_by_product(product_code=cn_code, region=eurostat_region)

            # Ajouter l'année demandée
            eurostat_result['requested_year'] = year
            eurostat_result['cn_code'] = cn_code

            logger.info(f"[OK] Données Eurostat/fallback obtenues pour CN {cn_code}")
            return eurostat_result

        except Exception as e:
            logger.error(f"[ERROR] Erreur Eurostat fallback: {e}")

            # 3. Fallback final: données de référence
            logger.warning(f"[FALLBACK] Utilisation données de référence pour CN {cn_code}")
            return {
                'success': True,
                'product_code': cn_code,
                'cn_code': cn_code,
                'region': region,
                'year': year,
                'imports': 1000,
                'exports': 800,
                'trade_balance': -200,
                'import_period': f"{year}-12-31",
                'export_period': f"{year}-12-31",
                'source': 'Données de référence',
                'note': 'API Eurostat et COMTRADE indisponibles - valeurs estimées',
                'data_source': {
                    'type': 'estimated',
                    'confidence': 'low',
                    'note': 'Données estimées en attendant connexion API'
                },
                'dependency_ratio': 55.6,
                'unit': 'Millions USD estimés'
            }

# Interface simplifiée pour compatibilité
class EurostatConnector(EurostatHybridConnector):
    """
    Alias pour compatibilité avec le code existant
    """
    pass

# Exemple d'utilisation
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("🧪 TEST EUROSTAT HYBRID CONNECTOR")
    print("="*60)
    
    connector = EurostatHybridConnector()
    
    # Test indicateurs clés
    indicators = ['gdp', 'inflation', 'unemployment', 'gini']
    
    print("\n[DATA] TEST INDICATEURS CLÉS:")
    print("-"*40)
    
    for indicator in indicators:
        print(f"\n[SEARCH] {indicator.upper()}...")
        data = connector.get_indicator(indicator)
        
        if data.get('success'):
            print(f"[OK] {data['indicator_name']}: {data['value']} {data['unit']}")
            print(f"   Période: {data['period']}")
            print(f"   Source: {data['source']} ({data['reliability']})")
            
            if 'change_percent' in data:
                change_sign = '+' if data['change'] > 0 else ''
                print(f"   Variation: {change_sign}{data['change_percent']}%")
            
            if 'historical' in data:
                print(f"   Historique: {len(data['historical'])} points")
        else:
            print(f"[ERROR] Échec")
    
    # Test recherche datasets
    print("\n[SEARCH] RECHERCHE DATASETS 'trade':")
    print("-"*40)
    
    datasets = connector.search_datasets('trade')
    for i, ds in enumerate(datasets[:3], 1):
        print(f"{i}. {ds['code']}: {ds['name']}")
    
    print(f"\n[TARGET] {len(datasets)} datasets trouvés")