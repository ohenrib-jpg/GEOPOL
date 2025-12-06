# geo/Flask/financial_watcher.py
import logging
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List
import json

logger = logging.getLogger(__name__)

class FinancialWatcher:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        # Matières premières stratégiques
        self.strategic_commodities = {
            'XAU': 'Or',  # ^XAU en Yahoo Finance
            'XAG': 'Argent',
            'CL': 'Pétrole brut',
            'NG': 'Gaz naturel',
            'HG': 'Cuivre'
        }
        
    async def monitor_strategic_commodities(self) -> Dict:
        """Surveillance des matières premières stratégiques"""
        results = {}
        
        for symbol, name in self.strategic_commodities.items():
            try:
                ticker = yf.Ticker(f"{symbol}=X")  # Symboles forex
                hist = ticker.history(period="5d")
                
                if len(hist) >= 2:
                    current = float(hist['Close'].iloc[-1])
                    previous = float(hist['Close'].iloc[-2])
                    change_pct = ((current - previous) / previous) * 100
                    
                    # Détecter anomalies (seuil à 5%)
                    anomaly = abs(change_pct) > 5.0
                    
                    results[symbol] = {
                        'name': name,
                        'current_price': round(current, 2),
                        'change_percent': round(change_pct, 2),
                        'anomaly': anomaly,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    
                    # Sauvegarder si anomalie
                    if anomaly:
                        await self._save_anomaly(symbol, name, current, change_pct)
                        
            except Exception as e:
                logger.error(f"Erreur surveillance {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        return results
    
    async def _save_anomaly(self, symbol: str, name: str, price: float, change: float):
        """Sauvegarde les anomalies financières"""
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO financial_anomalies (symbol, name, price, change_percent)
            VALUES (?, ?, ?, ?)
        """, (symbol, name, price, change))
        
        conn.commit()
        conn.close()

# Initialisation de la base de données
def init_financial_database(db_manager):
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
