# Flask/real_financial_service.py
"""
Service financier RÉEL avec yFinance - Sans fallback
"""

import logging
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class RealFinancialService:
    """
    Service de données financières réelles
    Utilise yFinance pour indices, commodities, crypto
    """
    
    # Indices géopolitiques majeurs
    GEOPOLITICAL_INDICES = {
        '^GSPC': {'name': 'S&P 500', 'country': 'USA', 'type': 'index'},
        '^FTSE': {'name': 'FTSE 100', 'country': 'UK', 'type': 'index'},
        '^GDAXI': {'name': 'DAX', 'country': 'Germany', 'type': 'index'},
        '^FCHI': {'name': 'CAC 40', 'country': 'France', 'type': 'index'},
        '^N225': {'name': 'Nikkei 225', 'country': 'Japan', 'type': 'index'},
        '^HSI': {'name': 'Hang Seng', 'country': 'Hong Kong', 'type': 'index'},
    }
    
    # Commodités stratégiques
    STRATEGIC_COMMODITIES = {
        'CL=F': {'name': 'Pétrole Brut', 'unit': 'USD/barrel', 'type': 'commodity'},
        'GC=F': {'name': 'Or', 'unit': 'USD/oz', 'type': 'commodity'},
        'SI=F': {'name': 'Argent', 'unit': 'USD/oz', 'type': 'commodity'},
        'NG=F': {'name': 'Gaz Naturel', 'unit': 'USD/MMBtu', 'type': 'commodity'},
        'ZC=F': {'name': 'Maïs', 'unit': 'USD/bushel', 'type': 'commodity'},
        'ZW=F': {'name': 'Blé', 'unit': 'USD/bushel', 'type': 'commodity'},
    }
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._init_financial_database()
    
    def _init_financial_database(self):
        """Initialise les tables financières"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS financial_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    name TEXT,
                    asset_type TEXT,
                    current_price REAL,
                    previous_price REAL,
                    change_percent REAL,
                    change_direction TEXT,
                    volume BIGINT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    real_data BOOLEAN DEFAULT 1,
                    UNIQUE(symbol, timestamp)
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS financial_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    alert_type TEXT,
                    price_change REAL,
                    threshold REAL,
                    description TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("✅ Tables financières initialisées")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation BDD financière: {e}")
            raise
    
    def update_all_market_data(self) -> Dict:
        """
        Met à jour toutes les données de marché
        Retourne uniquement des données réelles
        """
        try:
            logger.info("📈 Mise à jour données de marché...")
            
            results = {
                'indices': {},
                'commodities': {},
                'market_status': self._get_market_status(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Récupérer les indices
            for symbol, info in self.GEOPOLITICAL_INDICES.items():
                try:
                    data = self._get_symbol_data(symbol)
                    if data:
                        results['indices'][symbol] = data
                        self._save_financial_data(data)
                except Exception as e:
                    logger.error(f"❌ Erreur indice {symbol}: {e}")
            
            # Récupérer les commodités
            for symbol, info in self.STRATEGIC_COMMODITIES.items():
                try:
                    data = self._get_symbol_data(symbol)
                    if data:
                        results['commodities'][symbol] = data
                        self._save_financial_data(data)
                except Exception as e:
                    logger.error(f"❌ Erreur commodité {symbol}: {e}")
            
            # Analyser les tendances
            results['analysis'] = self._analyze_market_trends(results)
            
            logger.info(f"✅ {len(results['indices'])} indices et {len(results['commodities'])} commodités récupérés")
            
            return {
                'success': True,
                'data': results,
                'real_data': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour marché: {e}")
            return {
                'success': False,
                'error': str(e),
                'real_data': False
            }
    
    def _get_symbol_data(self, symbol: str) -> Optional[Dict]:
        """
        Récupère les données pour un symbole
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Données historiques (5 jours)
            hist = ticker.history(period='5d')
            
            if len(hist) < 2:
                logger.warning(f"⚠️ Données insuffisantes pour {symbol}")
                return None
            
            current_price = float(hist['Close'].iloc[-1])
            previous_price = float(hist['Close'].iloc[-2])
            change_percent = ((current_price - previous_price) / previous_price) * 100
            
            # Informations supplémentaires
            info = ticker.info
            volume = info.get('volume', hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0)
            
            data = {
                'symbol': symbol,
                'name': info.get('shortName', info.get('longName', symbol)),
                'asset_type': info.get('quoteType', 'unknown'),
                'current_price': round(current_price, 2),
                'previous_price': round(previous_price, 2),
                'change_percent': round(change_percent, 2),
                'change_direction': 'up' if change_percent > 0 else 'down',
                'volume': int(volume),
                'currency': info.get('currency', 'USD'),
                'timestamp': datetime.utcnow().isoformat(),
                'real_data': True,
                'source': 'yfinance'
            }
            
            # Générer une alerte si mouvement important
            if abs(change_percent) > 3:
                self._generate_financial_alert(symbol, change_percent, current_price)
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Erreur symbole {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, days: int = 30) -> Dict:
        """
        Récupère les données historiques
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f'{days}d')
            
            data_points = []
            for date, row in hist.iterrows():
                data_points.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
            return {
                'success': True,
                'symbol': symbol,
                'data': data_points,
                'period_days': days,
                'real_data': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur historique {symbol}: {e}")
            return {
                'success': False,
                'error': str(e),
                'real_data': False
            }
    
    def _analyze_market_trends(self, market_data: Dict) -> Dict:
        """
        Analyse les tendances du marché
        """
        try:
            all_changes = []
            
            # Collecter tous les changements
            for category in ['indices', 'commodities']:
                for symbol, data in market_data.get(category, {}).items():
                    if isinstance(data, dict) and 'change_percent' in data:
                        all_changes.append(data['change_percent'])
            
            if not all_changes:
                return {'trend': 'unknown', 'confidence': 0}
            
            # Calculer la tendance
            avg_change = sum(all_changes) / len(all_changes)
            positive_count = sum(1 for c in all_changes if c > 0)
            positive_ratio = positive_count / len(all_changes)
            
            if avg_change > 1 and positive_ratio > 0.6:
                trend = 'bullish'
            elif avg_change < -1 and positive_ratio < 0.4:
                trend = 'bearish'
            else:
                trend = 'neutral'
            
            return {
                'trend': trend,
                'average_change': round(avg_change, 2),
                'positive_ratio': round(positive_ratio, 2),
                'assets_analyzed': len(all_changes)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse tendances: {e}")
            return {'trend': 'error', 'error': str(e)}
    
    def _get_market_status(self) -> str:
        """
        Détermine le statut du marché (ouvert/fermé)
        """
        try:
            ny_time = datetime.utcnow() - timedelta(hours=5)  # UTC-5 pour New York
            hour = ny_time.hour
            weekday = ny_time.weekday()  # 0 = lundi, 6 = dimanche
            
            # Horaires de marché US
            if weekday < 5:  # Lundi à vendredi
                if 9 <= hour <= 16:  # 9h-16h EST
                    return 'open'
            
            return 'closed'
            
        except:
            return 'unknown'
    
    def _save_financial_data(self, data: Dict):
        """Sauvegarde les données financières"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO financial_data 
                (symbol, name, asset_type, current_price, previous_price, 
                 change_percent, change_direction, volume, real_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                data['symbol'],
                data['name'],
                data['asset_type'],
                data['current_price'],
                data['previous_price'],
                data['change_percent'],
                data['change_direction'],
                data['volume']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde données financières: {e}")
    
    def _generate_financial_alert(self, symbol: str, change_percent: float, price: float):
        """Génère une alerte financière"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            alert_type = 'SIGNIFICANT_RISE' if change_percent > 0 else 'SIGNIFICANT_DROP'
            
            cur.execute("""
                INSERT INTO financial_alerts 
                (symbol, alert_type, price_change, threshold, description)
                VALUES (?, ?, ?, 3, ?)
            """, (
                symbol,
                alert_type,
                round(change_percent, 2),
                f"{symbol}: Changement de {change_percent:.2f}% à {price:.2f}"
            ))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"📈 Alerte {alert_type} pour {symbol}: {change_percent:.2f}%")
            
        except Exception as e:
            logger.error(f"❌ Erreur génération alerte financière: {e}")