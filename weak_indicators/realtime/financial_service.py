# Flask/weak_indicators/realtime/financial_service.py

import logging
import yfinance as yf
from datetime import datetime
from typing import Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class FinancialDataService:
    """Service des données financières - Adapté depuis financial_watcher.py"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Matières premières stratégiques (conservées de ton fichier)
        self.strategic_commodities = {
            'XAU': 'Or',
            'XAG': 'Argent',
            'CL': 'Pétrole brut', 
            'NG': 'Gaz naturel',
            'HG': 'Cuivre'
        }
        
        # Indices géopolitiques importants (étendus)
        self.geopolitical_indices = {
            '^GSPC': {'name': 'S&P 500', 'country': 'États-Unis'},
            '^FTSE': {'name': 'FTSE 100', 'country': 'Royaume-Uni'},
            '^GDAXI': {'name': 'DAX', 'country': 'Allemagne'},
            '^FCHI': {'name': 'CAC 40', 'country': 'France'},
            '^N225': {'name': 'Nikkei 225', 'country': 'Japon'},
            '^HSI': {'name': 'Hang Seng', 'country': 'Hong Kong'}
        }
    
    async def get_market_data(self) -> Dict[str, Any]:
        """Récupère les données de marché - Interface standardisée"""
        try:
            # Utiliser ton code existant mais avec interface async
            commodities_data = await self.monitor_strategic_commodities()
            indices_data = await self.get_geopolitical_indices()
            
            return {
                'commodities': commodities_data,
                'indices': indices_data,
                'last_update': datetime.now().isoformat(),
                'source': 'yfinance'
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur données financières: {e}")
            return self._get_fallback_data()
    
    async def monitor_strategic_commodities(self) -> Dict:
        """Surveillance des matières premières - Ton code existant adapté"""
        results = {}
        
        for symbol, name in self.strategic_commodities.items():
            try:
                # Adapter les symboles pour yfinance
                if symbol in ['XAU', 'XAG']:
                    ticker_symbol = f"{symbol}=X"  # Forex
                else:
                    ticker_symbol = f"{symbol}F"   # Futures
                
                ticker = yf.Ticker(ticker_symbol)
                hist = ticker.history(period="5d")
                
                if len(hist) >= 2:
                    current = float(hist['Close'].iloc[-1])
                    previous = float(hist['Close'].iloc[-2])
                    change_pct = ((current - previous) / previous) * 100
                    
                    # Détecter anomalies (seuil à 5%) - conservé de ton code
                    anomaly = abs(change_pct) > 5.0
                    
                    results[symbol] = {
                        'name': name,
                        'current_price': round(current, 2),
                        'change_percent': round(change_pct, 2),
                        'anomaly': anomaly,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Sauvegarder si anomalie - ton code existant
                    if anomaly:
                        await self._save_anomaly(symbol, name, current, change_pct)
                        
            except Exception as e:
                logger.error(f"❌ Erreur surveillance {symbol}: {e}")
                results[symbol] = {'error': str(e), 'name': name}
        
        return results
    
    async def get_geopolitical_indices(self) -> Dict[str, Any]:
        """Récupère les indices géopolitiques - Nouvelle méthode"""
        results = {}
        
        for symbol, info in self.geopolitical_indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")
                
                if len(hist) >= 2:
                    current_price = float(hist['Close'].iloc[-1])
                    previous_price = float(hist['Close'].iloc[-2])
                    change_percent = ((current_price - previous_price) / previous_price) * 100
                    
                    results[symbol] = {
                        'name': info['name'],
                        'current_price': round(current_price, 2),
                        'change_percent': round(change_percent, 2),
                        'trend': 'up' if change_percent > 0 else 'down',
                        'country': info['country']
                    }
                else:
                    results[symbol] = {'error': 'Données insuffisantes', 'name': info['name']}
                    
            except Exception as e:
                logger.error(f"❌ Erreur indice {symbol}: {e}")
                results[symbol] = {'error': str(e), 'name': info['name']}
        
        return results
    
    async def _save_anomaly(self, symbol: str, name: str, price: float, change: float):
        """Sauvegarde les anomalies financières - Ton code existant"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            # Vérifier/Créer la table comme dans ton code
            cur.execute("""
                CREATE TABLE IF NOT EXISTS financial_anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    change_percent REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cur.execute("""
                INSERT INTO financial_anomalies (symbol, name, price, change_percent)
                VALUES (?, ?, ?, ?)
            """, (symbol, name, price, change))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde anomalie: {e}")
    
    def _get_fallback_data(self):
        """Données de fallback en cas d'erreur"""
        return {
            'commodities': {
                'XAU': {
                    'name': 'Or',
                    'current_price': 1832.50,
                    'change_percent': 0.8,
                    'anomaly': False,
                    'fallback': True
                }
            },
            'indices': {
                '^FCHI': {
                    'name': 'CAC 40',
                    'current_price': 7345.67,
                    'change_percent': 1.2,
                    'trend': 'up',
                    'country': 'France',
                    'fallback': True
                }
            },
            'last_update': datetime.now().isoformat(),
            'source': 'fallback'
        }

# Fonction d'initialisation conservée
def init_financial_database(db_manager):
    """Initialisation DB - Ton code existant"""
    conn = db_manager.get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS financial_anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            change_percent REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_financial_time ON financial_anomalies(timestamp)")
    
    conn.commit()
    conn.close()
