# Flask/yfinance_connector.py
"""
Connecteur yFinance pour données financières
"""

import logging
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class YFinanceConnector:
    """Connecteur pour yFinance"""
    
    # Indices surveillés
    TRACKED_INDICES = {
        '^FCHI': {'name': 'CAC 40', 'country': 'France', 'region': 'Europe'},
        '^GDAXI': {'name': 'DAX', 'country': 'Allemagne', 'region': 'Europe'},
        '^FTSE': {'name': 'FTSE 100', 'country': 'Royaume-Uni', 'region': 'Europe'},
        '^GSPC': {'name': 'S&P 500', 'country': 'États-Unis', 'region': 'Amérique'},
        '^DJI': {'name': 'Dow Jones', 'country': 'États-Unis', 'region': 'Amérique'},
        '^IXIC': {'name': 'NASDAQ', 'country': 'États-Unis', 'region': 'Amérique'},
        '^N225': {'name': 'Nikkei 225', 'country': 'Japon', 'region': 'Asie'}
    }
    
    def __init__(self):
        logger.info("✅ Connecteur yFinance initialisé")
    
    def get_index_data(self, symbol: str) -> Dict[str, Any]:
        """Récupère les données d'un indice"""
        try:
            if symbol not in self.TRACKED_INDICES:
                return {'success': False, 'error': f'Symbole {symbol} non supporté'}
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            
            if len(hist) >= 2:
                current_price = float(hist['Close'].iloc[-1])
                previous_price = float(hist['Close'].iloc[-2])
                change_percent = ((current_price - previous_price) / previous_price) * 100
                
                return {
                    'success': True,
                    'symbol': symbol,
                    'name': self.TRACKED_INDICES[symbol]['name'],
                    'current_price': round(current_price, 2),
                    'change_percent': round(change_percent, 2),
                    'trend': 'up' if change_percent > 0 else 'down',
                    'timestamp': datetime.now().isoformat(),
                    'source': 'Yahoo Finance',
                    'country': self.TRACKED_INDICES[symbol]['country'],
                    'region': self.TRACKED_INDICES[symbol]['region']
                }
            
            return {'success': False, 'error': 'Données insuffisantes'}
            
        except Exception as e:
            logger.error(f"❌ Erreur yFinance {symbol}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_all_indices(self) -> Dict[str, Any]:
        """Récupère tous les indices"""
        results = {}
        success_count = 0
        
        for symbol, info in self.TRACKED_INDICES.items():
            data = self.get_index_data(symbol)
            if data['success']:
                results[symbol] = data
                success_count += 1
        
        return {
            'success': success_count > 0,
            'indices': results,
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'total': len(self.TRACKED_INDICES),
                'successful': success_count,
                'failed': len(self.TRACKED_INDICES) - success_count
            }
        }
    
    def get_historical_data(self, symbol: str, period: str = '6mo') -> Dict[str, Any]:
        """Données historiques"""
        try:
            if symbol not in self.TRACKED_INDICES:
                return {'success': False, 'error': f'Symbole {symbol} non supporté'}
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            
            if hist.empty:
                return {'success': False, 'error': 'Aucune donnée historique disponible'}
            
            data = []
            for date, row in hist.iterrows():
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'close': round(row['Close'], 2),
                    'volume': int(row['Volume']),
                    'high': round(row['High'], 2),
                    'low': round(row['Low'], 2)
                })
            
            return {
                'success': True,
                'symbol': symbol,
                'name': self.TRACKED_INDICES[symbol]['name'],
                'period': period,
                'data': data,
                'records': len(data)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur historique {symbol}: {e}")
            return {'success': False, 'error': str(e)}
