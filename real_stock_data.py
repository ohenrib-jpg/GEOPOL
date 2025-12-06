# Flask/real_stock_data.py
"""
Module pour les données boursières réelles dans weak indicators
"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class RealStockData:
    """Gestionnaire des données boursières réelles pour weak indicators"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.yfinance = None
        self._init_yfinance()
    
    def _init_yfinance(self):
        """Initialise le connecteur yfinance"""
        try:
            from .yfinance_connector import YFinanceConnector
            self.yfinance = YFinanceConnector()
            logger.info("✅ RealStockData initialisé avec yfinance")
        except ImportError as e:
            logger.error(f"❌ Erreur initialisation yfinance: {e}")
            self.yfinance = None
    
    def get_geopolitical_indices(self) -> Dict[str, Any]:
        """Récupère les indices géopolitiques importants"""
        if not self.yfinance:
            return self._get_fallback_data()
        
        try:
            # Indices principaux pour surveillance géopolitique
            geopolitical_symbols = [
                '^GSPC',  # S&P 500 (États-Unis)
                '^FTSE',  # FTSE 100 (Royaume-Uni) 
                '^GDAXI', # DAX (Allemagne)
                '^FCHI',  # CAC 40 (France)
                '^N225',  # Nikkei 225 (Japon)
                '^HSI',   # Hang Seng (Hong Kong)
            ]
            
            results = {}
            for symbol in geopolitical_symbols:
                try:
                    data = self.yfinance.get_index_data(symbol)
                    if data.get('success'):
                        results[symbol] = data
                    else:
                        results[symbol] = self._create_fallback_entry(symbol, data.get('error', 'Unknown error'))
                except Exception as e:
                    logger.error(f"❌ Erreur indice {symbol}: {e}")
                    results[symbol] = self._create_fallback_entry(symbol, str(e))
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur get_geopolitical_indices: {e}")
            return self._get_fallback_data()
    
    def get_commodity_prices(self) -> Dict[str, Any]:
        """Récupère les prix des matières premières stratégiques"""
        if not self.yfinance:
            return self._get_fallback_commodities()
        
        try:
            commodities_data = self.yfinance.get_commodity_prices()
            
            # Filtrer les commodités importantes pour la géopolitique
            strategic_commodities = {
                'CL=F': 'Pétrole Brut',
                'GC=F': 'Or',
                'SI=F': 'Argent', 
                'NG=F': 'Gaz Naturel',
                'ZC=F': 'Maïs',
                'ZW=F': 'Blé'
            }
            
            results = {}
            for symbol, name in strategic_commodities.items():
                data = commodities_data.get(symbol, {})
                if data:
                    results[symbol] = data
                else:
                    results[symbol] = self._create_fallback_commodity(symbol, name)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur commodity prices: {e}")
            return self._get_fallback_commodities()
    
    def get_crypto_prices(self) -> Dict[str, Any]:
        """Récupère les prix des cryptomonnaies"""
        if not self.yfinance:
            return self._get_fallback_cryptos()
        
        try:
            cryptos_data = self.yfinance.get_crypto_prices()
            
            # Cryptos importantes
            major_cryptos = {
                'BTC-USD': 'Bitcoin',
                'ETH-USD': 'Ethereum',
                'USDT-USD': 'Tether'
            }
            
            results = {}
            for symbol, name in major_cryptos.items():
                data = cryptos_data.get(symbol, {})
                if data:
                    results[symbol] = data
                else:
                    results[symbol] = self._create_fallback_crypto(symbol, name)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur crypto prices: {e}")
            return self._get_fallback_cryptos()
    
    def _create_fallback_entry(self, symbol: str, error: str) -> Dict[str, Any]:
        """Crée une entrée de secours pour un indice"""
        symbol_names = {
            '^GSPC': 'S&P 500',
            '^FTSE': 'FTSE 100', 
            '^GDAXI': 'DAX',
            '^FCHI': 'CAC 40',
            '^N225': 'Nikkei 225',
            '^HSI': 'Hang Seng'
        }
        
        return {
            'success': False,
            'symbol': symbol,
            'name': symbol_names.get(symbol, symbol),
            'current_price': 0,
            'change_percent': 0,
            'change_direction': 'stable',
            'country': 'Global',
            'type': 'index',
            'timestamp': datetime.now().isoformat(),
            'error': error
        }
    
    def _create_fallback_commodity(self, symbol: str, name: str) -> Dict[str, Any]:
        """Crée une entrée de secours pour une commodité"""
        return {
            'success': False,
            'symbol': symbol,
            'name': name,
            'current_price': 0,
            'change_percent': 0,
            'change_direction': 'stable',
            'unit': 'USD',
            'type': 'commodity',
            'timestamp': datetime.now().isoformat(),
            'error': 'Données non disponibles'
        }
    
    def _create_fallback_crypto(self, symbol: str, name: str) -> Dict[str, Any]:
        """Crée une entrée de secours pour une crypto"""
        return {
            'success': False,
            'symbol': symbol,
            'name': name,
            'current_price': 0,
            'change_percent': 0,
            'change_direction': 'stable',
            'type': 'crypto',
            'timestamp': datetime.now().isoformat(),
            'error': 'Données non disponibles'
        }
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Données de secours complètes"""
        return {
            '^GSPC': self._create_fallback_entry('^GSPC', 'Service indisponible'),
            '^FTSE': self._create_fallback_entry('^FTSE', 'Service indisponible'),
            '^GDAXI': self._create_fallback_entry('^GDAXI', 'Service indisponible'),
            '^FCHI': self._create_fallback_entry('^FCHI', 'Service indisponible')
        }
    
    def _get_fallback_commodities(self) -> Dict[str, Any]:
        """Commodités de secours"""
        return {
            'CL=F': self._create_fallback_commodity('CL=F', 'Pétrole Brut'),
            'GC=F': self._create_fallback_commodity('GC=F', 'Or')
        }
    
    def _get_fallback_cryptos(self) -> Dict[str, Any]:
        """Cryptos de secours"""
        return {
            'BTC-USD': self._create_fallback_crypto('BTC-USD', 'Bitcoin'),
            'ETH-USD': self._create_fallback_crypto('ETH-USD', 'Ethereum')
        }