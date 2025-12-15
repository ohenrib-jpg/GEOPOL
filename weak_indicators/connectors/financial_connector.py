# Flask/weak_indicators/connectors/financial_connector.py
"""Connecteur pour les données financières"""

import logging
import yfinance as yf
from typing import List
from datetime import datetime
from ..models import FinancialInstrument

logger = logging.getLogger(__name__)

class FinancialConnector:
    """Connecteur pour les données financières"""
    
    def __init__(self):
        # Indices géopolitiques
        self.indices = {
            '^GSPC': {'name': 'S&P 500', 'country': 'USA'},
            '^FTSE': {'name': 'FTSE 100', 'country': 'UK'},
            '^GDAXI': {'name': 'DAX', 'country': 'Germany'},
            '^FCHI': {'name': 'CAC 40', 'country': 'France'},
            '^N225': {'name': 'Nikkei 225', 'country': 'Japan'},
            '^HSI': {'name': 'Hang Seng', 'country': 'Hong Kong'}
        }
        
        # Matières premières stratégiques
        self.commodities = {
            'CL=F': {'name': 'Crude Oil', 'type': 'commodity'},
            'GC=F': {'name': 'Gold', 'type': 'commodity'},
            'SI=F': {'name': 'Silver', 'type': 'commodity'},
            'NG=F': {'name': 'Natural Gas', 'type': 'commodity'}
        }
        
        # Cryptomonnaies
        self.crypto = {
            'BTC-USD': {'name': 'Bitcoin', 'type': 'crypto'},
            'ETH-USD': {'name': 'Ethereum', 'type': 'crypto'}
        }
    
    def fetch_all_data(self) -> List[FinancialInstrument]:
        """Récupère toutes les données financières"""
        instruments = []
        
        # Indices
        for symbol, info in self.indices.items():
            try:
                data = self._fetch_symbol(symbol, info['name'], 'index')
                if data:
                    instruments.append(data)
            except Exception as e:
                logger.error(f"Erreur index {symbol}: {e}")
        
        # Commodities
        for symbol, info in self.commodities.items():
            try:
                data = self._fetch_symbol(symbol, info['name'], info['type'])
                if data:
                    instruments.append(data)
            except Exception as e:
                logger.error(f"Erreur commodity {symbol}: {e}")
        
        # Crypto
        for symbol, info in self.crypto.items():
            try:
                data = self._fetch_symbol(symbol, info['name'], info['type'])
                if data:
                    instruments.append(data)
            except Exception as e:
                logger.error(f"Erreur crypto {symbol}: {e}")
        
        return instruments
    
    def _fetch_symbol(self, symbol: str, name: str, category: str) -> FinancialInstrument:
        """Récupère les données pour un symbole"""
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="2d")
        
        if len(hist) >= 2:
            current_price = float(hist['Close'].iloc[-1])
            previous_price = float(hist['Close'].iloc[-2])
            change_percent = ((current_price - previous_price) / previous_price) * 100
            
            return FinancialInstrument(
                symbol=symbol,
                name=name,
                current_price=round(current_price, 2),
                change_percent=round(change_percent, 2),
                volume=int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else None,
                timestamp=datetime.utcnow(),
                source='yfinance',
                category=category
            )
        
        return None
