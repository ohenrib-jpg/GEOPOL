# Flask/real_financial_data.py
"""
Données financières RÉELLES avec yFinance
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import yfinance as yf
import pandas as pd

logger = logging.getLogger(__name__)

class RealFinancialData:
    """Récupère des données financières réelles"""
    
    def __init__(self, db_manager, symbols=None):
        self.db_manager = db_manager
        self.symbols = symbols or [
            '^GSPC', '^FTSE', '^GDAXI', '^FCHI', '^N225', '^HSI',
            'CL=F', 'GC=F', 'SI=F', 'NG=F',
            'BTC-USD', 'ETH-USD'
        ]
        
    def get_real_time_data(self) -> Dict[str, Any]:
        """Récupère les données en temps réel"""
        try:
            data = {}
            
            for symbol in self.symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='2d')
                    
                    if len(hist) >= 2:
                        current = hist['Close'].iloc[-1]
                        previous = hist['Close'].iloc[-2]
                        change_pct = ((current - previous) / previous) * 100
                        
                        data[symbol] = {
                            'current': float(current),
                            'change': float(change_pct),
                            'direction': 'up' if change_pct > 0 else 'down',
                            'volume': int(hist['Volume'].iloc[-1]),
                            'real_data': True,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    else:
                        data[symbol] = self._mock_financial_data(symbol)
                        
                except Exception as e:
                    logger.error(f"❌ Erreur symbole {symbol}: {e}")
                    data[symbol] = self._mock_financial_data(symbol)
            
            return {
                'success': True,
                'data': data,
                'market_status': self._get_market_status(),
                'real_data': any(d.get('real_data', False) for d in data.values()),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur données financières: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {},
                'real_data': False
            }
    
    def get_historical_data(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Données historiques"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f'{days}d')
            
            prices = []
            for date, row in hist.iterrows():
                prices.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
            return {
                'success': True,
                'symbol': symbol,
                'data': prices,
                'real_data': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur historique {symbol}: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }
    
    def _get_market_status(self) -> str:
        """Détermine le statut du marché"""
        try:
            # Vérifier les heures de marché US
            ny_time = datetime.utcnow() - timedelta(hours=5)
            hour = ny_time.hour
            
            if 9 <= hour <= 16:  # 9h-16h EST
                return 'open'
            else:
                return 'closed'
        except:
            return 'unknown'
    
    def _mock_financial_data(self, symbol: str) -> Dict[str, Any]:
        """Données simulées"""
        import random
        return {
            'current': random.uniform(100, 5000),
            'change': random.uniform(-5, 5),
            'direction': random.choice(['up', 'down']),
            'volume': random.randint(1000000, 50000000),
            'real_data': False,
            'note': 'Données simulées'
        }