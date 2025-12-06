# geo/Flask/travel_advisor.py
import logging
import requests
from datetime import datetime
from typing import Dict, List
import json

logger = logging.getLogger(__name__)

class TravelAdvisor:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.sources = {
            'US': 'https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.html',
            'UK': 'https://www.gov.uk/foreign-travel-advice',
            'AU': 'https://www.smartraveller.gov.au/',
            'EU': 'https://eeas.europa.eu/headquarters/eeas/travel-risk-assessments_en'
        }
        self.selected_countries = ['US', 'UK', 'AU', 'EU']  # Pays sélectionnés
        
    async def fetch_advisories(self) -> Dict:
        """Récupère les avis de voyage des sources sélectionnées"""
        advisories = {}
        
        for country in self.selected_countries:
            try:
                # Simulation de récupération (en production: scraping/API)
                advisories[country] = await self._get_country_advisory(country)
            except Exception as e:
                logger.error(f"Erreur récupération {country}: {e}")
                advisories[country] = {'level': 1, 'message': 'Données non disponibles'}
        
        # Vérifier les changements et générer des alertes
        alerts = await self._check_for_alerts(advisories)
        
        return {
            'advisories': advisories,
            'alerts': alerts,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _get_country_advisory(self, country: str) -> Dict:
        """Récupère l'avis pour un pays spécifique (simulation)"""
        import random
        levels = {
            1: "Exercer des précautions normales",
            2: "Exercer une prudence accrue",
            3: "Réenvisager le voyage",
            4: "Ne pas voyager"
        }
        
        level = random.randint(1, 4)
        return {
            'level': level,
            'message': levels[level],
            'last_updated': datetime.utcnow().isoformat()
        }
    
    async def _check_for_alerts(self, advisories: Dict) -> List[Dict]:
        """Vérifie les changements d'avis et génère des alertes"""
        alerts = []
        conn = self.db_manager.get_connection()
        cur = conn.cursor()
        
        for country, advisory in advisories.items():
            # Récupérer l'avis précédent
            cur.execute("""
                SELECT level FROM travel_advisories 
                WHERE country = ? ORDER BY timestamp DESC LIMIT 1
            """, (country,))
            
            prev_level = cur.fetchone()
            if prev_level and prev_level[0] != advisory['level']:
                # Changement détecté
                alerts.append({
                    'country': country,
                    'previous_level': prev_level[0],
                    'new_level': advisory['level'],
                    'message': f"Changement d'alerte: {prev_level[0]} → {advisory['level']}",
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            # Sauvegarder le nouvel avis
            cur.execute("""
                INSERT INTO travel_advisories (country, level, message)
                VALUES (?, ?, ?)
            """, (country, advisory['level'], advisory['message']))
        
        conn.commit()
        conn.close()
        return alerts

# Initialisation de la base de données
def init_travel_database(db_manager):
    conn = db_manager.get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS travel_advisories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT NOT NULL,
            level INTEGER NOT NULL,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_travel_country_time ON travel_advisories(country, timestamp)")
    
    conn.commit()
    conn.close()
