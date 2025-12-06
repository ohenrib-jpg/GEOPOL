# Flask/economic_indicators.py
"""
Module de gestion des indicateurs économiques internationaux
Collecte de données depuis yFinance, Banque Mondiale, et OpenSanctions
"""

import sqlite3
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
import logging

logger = logging.getLogger(__name__)


class EconomicIndicatorsManager:
    """Gestionnaire principal des indicateurs économiques"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.wb_base_url = "https://api.worldbank.org/v2"
        self.opensanctions_url = "https://data.opensanctions.org/datasets/latest/default/targets.nested.json"
        
        # Initialiser les tables
        self._init_database()
        
    def _init_database(self):
        """Initialise les tables pour les indicateurs économiques"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        # Table pour les données financières (yFinance)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            indicator_type TEXT NOT NULL,
            value REAL,
            currency TEXT,
            timestamp TEXT NOT NULL,
            source TEXT DEFAULT 'yfinance',
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, indicator_type, timestamp)
        )
        ''')
        
        # Table pour les données Banque Mondiale
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS world_bank_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT NOT NULL,
            country_name TEXT,
            indicator_code TEXT NOT NULL,
            indicator_name TEXT,
            year INTEGER NOT NULL,
            value REAL,
            last_updated TEXT,
            source TEXT DEFAULT 'worldbank',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country_code, indicator_code, year)
        )
        ''')
        
        # Table pour les sanctions internationales
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS international_sanctions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id TEXT UNIQUE NOT NULL,
            entity_name TEXT NOT NULL,
            entity_type TEXT,
            country TEXT,
            sanctions_list TEXT,
            reason TEXT,
            start_date TEXT,
            data_json TEXT,
            last_updated TEXT,
            source TEXT DEFAULT 'opensanctions',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Table pour l'historique des séries temporelles
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS indicator_time_series (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            indicator_key TEXT NOT NULL,
            indicator_type TEXT NOT NULL,
            date TEXT NOT NULL,
            value REAL,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(indicator_key, indicator_type, date)
        )
        ''')
        
        # Index pour améliorer les performances
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_financial_symbol ON financial_indicators(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wb_country ON world_bank_indicators(country_code)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sanctions_country ON international_sanctions(country)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timeseries_key ON indicator_time_series(indicator_key)')
        
        conn.commit()
        conn.close()
        logger.info("✅ Tables indicateurs économiques initialisées")
    
    # ==========================================
    # YFINANCE - INDICATEURS FINANCIERS
    # ==========================================
    
    def fetch_financial_data(self, symbols: List[str], period: str = "1mo") -> Dict:
        """
        Récupère les données financières via yFinance
        
        Args:
            symbols: Liste des symboles (ex: ['SPY', 'GLD', 'USDCNY=X'])
            period: Période ('1d', '5d', '1mo', '3mo', '6mo', '1y')
        """
        results = {}
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                info = ticker.info
                
                if not hist.empty:
                    latest = hist.iloc[-1]
                    
                    results[symbol] = {
                        'current_price': float(latest['Close']),
                        'open': float(latest['Open']),
                        'high': float(latest['High']),
                        'low': float(latest['Low']),
                        'volume': int(latest['Volume']),
                        'timestamp': latest.name.isoformat(),
                        'currency': info.get('currency', 'USD'),
                        'name': info.get('longName', symbol),
                        'change_percent': self._calculate_change(hist)
                    }
                    
                    # Sauvegarder en base
                    self._save_financial_indicator(symbol, results[symbol])
                    
                    logger.info(f"✅ Données récupérées pour {symbol}")
                else:
                    logger.warning(f"⚠️ Pas de données pour {symbol}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur yFinance pour {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        return results
    
    def _calculate_change(self, hist) -> float:
        """Calcule le pourcentage de variation"""
        if len(hist) < 2:
            return 0.0
        first_close = hist.iloc[0]['Close']
        last_close = hist.iloc[-1]['Close']
        return ((last_close - first_close) / first_close) * 100
    
    def _save_financial_indicator(self, symbol: str, data: Dict):
        """Sauvegarde un indicateur financier"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT OR REPLACE INTO financial_indicators 
            (symbol, indicator_type, value, currency, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                symbol,
                'price',
                data['current_price'],
                data['currency'],
                data['timestamp'],
                json.dumps(data)
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde {symbol}: {e}")
        finally:
            conn.close()
    
    # ==========================================
    # BANQUE MONDIALE - INDICATEURS MACRO
    # ==========================================
    
    def fetch_world_bank_data(self, country_codes: List[str], indicator_code: str, 
                              years: int = 5) -> Dict:
        """
        Récupère des données de la Banque Mondiale
        
        Args:
            country_codes: Liste de codes pays ISO ('CN', 'US', 'BR', etc.)
            indicator_code: Code indicateur (ex: 'NY.GDP.MKTP.CD' pour PIB)
            years: Nombre d'années à récupérer
        """
        results = {}
        
        current_year = datetime.now().year
        date_range = f"{current_year - years}:{current_year}"
        
        for country in country_codes:
            try:
                url = f"{self.wb_base_url}/country/{country}/indicator/{indicator_code}"
                params = {
                    'format': 'json',
                    'date': date_range,
                    'per_page': 100
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if len(data) > 1 and data[1]:
                    country_data = []
                    
                    for entry in data[1]:
                        if entry['value'] is not None:
                            country_data.append({
                                'year': entry['date'],
                                'value': entry['value'],
                                'country_name': entry['country']['value'],
                                'indicator_name': entry['indicator']['value']
                            })
                            
                            # Sauvegarder en base
                            self._save_wb_indicator(country, entry, indicator_code)
                    
                    results[country] = country_data
                    logger.info(f"✅ Données Banque Mondiale pour {country}")
                else:
                    results[country] = []
                    logger.warning(f"⚠️ Pas de données WB pour {country}")
                    
            except Exception as e:
                logger.error(f"❌ Erreur Banque Mondiale {country}: {e}")
                results[country] = {'error': str(e)}
        
        return results
    
    def _save_wb_indicator(self, country_code: str, entry: Dict, indicator_code: str):
        """Sauvegarde un indicateur Banque Mondiale"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT OR REPLACE INTO world_bank_indicators 
            (country_code, country_name, indicator_code, indicator_name, year, value, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                country_code,
                entry['country']['value'],
                indicator_code,
                entry['indicator']['value'],
                int(entry['date']),
                entry['value'],
                datetime.now().isoformat()
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde WB {country_code}: {e}")
        finally:
            conn.close()
    
    # ==========================================
    # OPENSANCTIONS - SANCTIONS INTERNATIONALES
    # ==========================================
    
    def fetch_sanctions_data(self, countries: Optional[List[str]] = None) -> Dict:
        """
        Récupère les données de sanctions depuis OpenSanctions
        
        Args:
            countries: Liste de pays à filtrer (optionnel)
        """
        try:
            logger.info("📡 Récupération des sanctions OpenSanctions...")
            response = requests.get(self.opensanctions_url, timeout=30)
            response.raise_for_status()
            
            all_sanctions = response.json()
            filtered_sanctions = []
            
            for entity in all_sanctions:
                # Filtrer par pays si spécifié
                if countries:
                    entity_countries = self._extract_countries(entity)
                    if not any(c in entity_countries for c in countries):
                        continue
                
                sanction_data = {
                    'id': entity.get('id', ''),
                    'name': self._extract_name(entity),
                    'type': entity.get('schema', 'Unknown'),
                    'countries': self._extract_countries(entity),
                    'sanctions': self._extract_sanctions_info(entity),
                    'reason': entity.get('properties', {}).get('reason', [''])[0] if entity.get('properties', {}).get('reason') else '',
                    'start_date': self._extract_date(entity)
                }
                
                filtered_sanctions.append(sanction_data)
                
                # Sauvegarder en base
                self._save_sanction(sanction_data, entity)
            
            logger.info(f"✅ {len(filtered_sanctions)} sanctions récupérées")
            
            return {
                'total': len(filtered_sanctions),
                'sanctions': filtered_sanctions,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur OpenSanctions: {e}")
            return {'error': str(e), 'sanctions': []}
    
    def _extract_name(self, entity: Dict) -> str:
        """Extrait le nom d'une entité"""
        props = entity.get('properties', {})
        if 'name' in props and props['name']:
            return props['name'][0]
        return entity.get('id', 'Unknown')
    
    def _extract_countries(self, entity: Dict) -> List[str]:
        """Extrait les pays associés"""
        props = entity.get('properties', {})
        countries = []
        
        for field in ['country', 'nationality', 'jurisdiction']:
            if field in props and props[field]:
                countries.extend(props[field])
        
        return list(set(countries))
    
    def _extract_sanctions_info(self, entity: Dict) -> List[str]:
        """Extrait les informations de sanctions"""
        props = entity.get('properties', {})
        topics = props.get('topics', [])
        return topics if topics else ['Unknown']
    
    def _extract_date(self, entity: Dict) -> Optional[str]:
        """Extrait la date de début"""
        props = entity.get('properties', {})
        if 'startDate' in props and props['startDate']:
            return props['startDate'][0]
        return None
    
    def _save_sanction(self, sanction_data: Dict, raw_entity: Dict):
        """Sauvegarde une sanction"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT OR REPLACE INTO international_sanctions 
            (entity_id, entity_name, entity_type, country, sanctions_list, reason, start_date, data_json, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                sanction_data['id'],
                sanction_data['name'],
                sanction_data['type'],
                ','.join(sanction_data['countries']),
                ','.join(sanction_data['sanctions']),
                sanction_data['reason'],
                sanction_data['start_date'],
                json.dumps(raw_entity),
                datetime.now().isoformat()
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde sanction: {e}")
        finally:
            conn.close()
    
    # ==========================================
    # SÉRIES TEMPORELLES
    # ==========================================
    
    def save_time_series(self, indicator_key: str, indicator_type: str, 
                        date: str, value: float, metadata: Optional[Dict] = None):
        """Sauvegarde un point de série temporelle"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT OR REPLACE INTO indicator_time_series 
            (indicator_key, indicator_type, date, value, metadata)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                indicator_key,
                indicator_type,
                date,
                value,
                json.dumps(metadata) if metadata else None
            ))
            conn.commit()
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde série temporelle: {e}")
        finally:
            conn.close()
    
    def get_time_series(self, indicator_key: str, indicator_type: str, 
                       days: int = 30) -> List[Dict]:
        """Récupère une série temporelle"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
        SELECT date, value, metadata FROM indicator_time_series
        WHERE indicator_key = ? AND indicator_type = ? AND date >= ?
        ORDER BY date ASC
        ''', (indicator_key, indicator_type, cutoff_date))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'date': row[0],
                'value': row[1],
                'metadata': json.loads(row[2]) if row[2] else {}
            }
            for row in rows
        ]
    
    # ==========================================
    # RÉCUPÉRATION DE DONNÉES
    # ==========================================
    
    def get_latest_financial_indicators(self, limit: int = 50) -> List[Dict]:
        """Récupère les derniers indicateurs financiers"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT symbol, indicator_type, value, currency, timestamp, metadata
        FROM financial_indicators
        ORDER BY created_at DESC
        LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'symbol': row[0],
                'type': row[1],
                'value': row[2],
                'currency': row[3],
                'timestamp': row[4],
                'metadata': json.loads(row[5]) if row[5] else {}
            }
            for row in rows
        ]
    
    def get_wb_indicators_by_country(self, country_code: str, limit: int = 20) -> List[Dict]:
        """Récupère les indicateurs Banque Mondiale pour un pays"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT country_name, indicator_code, indicator_name, year, value
        FROM world_bank_indicators
        WHERE country_code = ?
        ORDER BY year DESC, indicator_code ASC
        LIMIT ?
        ''', (country_code, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'country': row[0],
                'indicator_code': row[1],
                'indicator_name': row[2],
                'year': row[3],
                'value': row[4]
            }
            for row in rows
        ]
    
    def get_sanctions_summary(self) -> Dict:
        """Récupère un résumé des sanctions"""
        conn = sqlite3.connect(self.db_manager.db_path)
        cursor = conn.cursor()
        
        # Total des sanctions
        cursor.execute('SELECT COUNT(*) FROM international_sanctions')
        total = cursor.fetchone()[0]
        
        # Par pays
        cursor.execute('''
        SELECT country, COUNT(*) as count
        FROM international_sanctions
        WHERE country != ''
        GROUP BY country
        ORDER BY count DESC
        LIMIT 10
        ''')
        by_country = [{'country': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        # Par type
        cursor.execute('''
        SELECT entity_type, COUNT(*) as count
        FROM international_sanctions
        GROUP BY entity_type
        ORDER BY count DESC
        LIMIT 5
        ''')
        by_type = [{'type': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        conn.close()
        
        return {
            'total': total,
            'by_country': by_country,
            'by_type': by_type
        }
    
    # ==========================================
    # INDICATEURS PRÉDÉFINIS
    # ==========================================
    
    def get_major_indices(self) -> Dict:
        """Récupère les principaux indices mondiaux"""
        symbols = [
            '^GSPC',  # S&P 500
            '^DJI',   # Dow Jones
            '^IXIC',  # NASDAQ
            '^FTSE',  # FTSE 100
            '^GDAXI', # DAX
            '000001.SS',  # Shanghai Composite
            '^HSI',   # Hang Seng
            '^N225'   # Nikkei 225
        ]
        return self.fetch_financial_data(symbols, period='5d')
    
    def get_commodities(self) -> Dict:
        """Récupère les prix des matières premières"""
        symbols = [
            'GC=F',   # Or
            'SI=F',   # Argent
            'CL=F',   # Pétrole WTI
            'BZ=F',   # Pétrole Brent
            'NG=F',   # Gaz naturel
        ]
        return self.fetch_financial_data(symbols, period='1mo')
    
    def get_currencies(self) -> Dict:
        """Récupère les taux de change"""
        symbols = [
            'EURUSD=X',
            'GBPUSD=X',
            'JPYUSD=X',
            'CNYUSD=X',
            'RUBUSD=X'
        ]
        return self.fetch_financial_data(symbols, period='1mo')
    
    def get_brics_indicators(self) -> Dict:
        """Récupère les indicateurs des pays BRICS"""
        countries = ['BR', 'RU', 'IN', 'CN', 'ZA']  # Brésil, Russie, Inde, Chine, Afrique du Sud
        
        # PIB
        gdp_data = self.fetch_world_bank_data(countries, 'NY.GDP.MKTP.CD', years=5)
        
        # Inflation
        inflation_data = self.fetch_world_bank_data(countries, 'FP.CPI.TOTL.ZG', years=5)
        
        return {
            'gdp': gdp_data,
            'inflation': inflation_data
        }
