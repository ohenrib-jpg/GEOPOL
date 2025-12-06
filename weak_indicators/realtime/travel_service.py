# Flask/weak_indicators/realtime/travel_service.py

import logging
from datetime import datetime
from typing import Dict, Any, List
import asyncio

logger = logging.getLogger(__name__)

class TravelAdvisoryService:
    """Service des avis de voyage - Fusion de tes services existants"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Essayer d'utiliser le service réel en premier
        self.real_service = None
        try:
            from ...travel_advisories_service import TravelAdvisoriesService
            self.real_service = TravelAdvisoriesService
            logger.info("✅ Service réel Travel Advisories disponible")
        except ImportError as e:
            logger.info(f"ℹ️ Service réel non disponible: {e}")
    
    async def get_country_risks(self) -> Dict[str, Any]:
        """Récupère les niveaux de risque par pays - Interface standardisée"""
        try:
            # Priorité au service réel
            if self.real_service and self.db_manager:
                countries = self.real_service.get_country_risk_levels(self.db_manager)
                return {
                    'countries': countries,
                    'total_countries': len(countries),
                    'last_update': datetime.now().isoformat(),
                    'source': 'real'
                }
            
            # Fallback au service simulé (ton code travel_advisor.py)
            return await self._get_simulated_data()
            
        except Exception as e:
            logger.error(f"❌ Erreur service voyage: {e}")
            return await self._get_simulated_data()
    
    async def _get_simulated_data(self) -> Dict[str, Any]:
        """Données simulées - Adapté de ton travel_advisor.py"""
        try:
            # Utiliser la logique de ton code existant
            advisories = {}
            
            # Pays surveillés de ton code
            selected_countries = ['US', 'UK', 'AU', 'EU', 'FR', 'CN', 'RU', 'UA']
            
            for country in selected_countries:
                try:
                    advisories[country] = await self._get_country_advisory(country)
                except Exception as e:
                    logger.error(f"Erreur pays {country}: {e}")
                    advisories[country] = {
                        'level': 1, 
                        'message': 'Données non disponibles',
                        'last_updated': datetime.now().isoformat()
                    }
            
            # Vérifier les changements comme dans ton code
            alerts = await self._check_for_alerts(advisories)
            
            # Convertir au format standard
            countries_list = []
            for country_code, advisory in advisories.items():
                countries_list.append({
                    'country_code': country_code,
                    'country_name': self._get_country_name(country_code),
                    'risk_level': advisory['level'],
                    'advice': advisory['message'],
                    'last_updated': advisory['last_updated'],
                    'sources': ['simulated']
                })
            
            return {
                'countries': countries_list,
                'alerts': alerts,
                'total_countries': len(countries_list),
                'last_update': datetime.now().isoformat(),
                'source': 'simulated'
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur données simulées: {e}")
            return self._get_fallback_data()
    
    async def _get_country_advisory(self, country: str) -> Dict:
        """Récupère l'avis pour un pays - Ton code existant adapté"""
        import random
        levels = {
            1: "Exercer des précautions normales",
            2: "Exercer une prudence accrue", 
            3: "Réenvisager le voyage",
            4: "Ne pas voyager"
        }
        
        # Logique de risque basée sur le pays
        risk_levels = {
            'UA': 4, 'RU': 3, 'CN': 2, 'FR': 1, 'US': 1, 'UK': 1, 'AU': 1, 'EU': 1
        }
        
        level = risk_levels.get(country, random.randint(1, 2))
        
        return {
            'level': level,
            'message': levels[level],
            'last_updated': datetime.now().isoformat()
        }
    
    async def _check_for_alerts(self, advisories: Dict) -> List[Dict]:
        """Vérifie les changements d'avis - Ton code existant adapté"""
        alerts = []
        
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            # Créer table si nécessaire
            cur.execute("""
                CREATE TABLE IF NOT EXISTS travel_advisories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    country TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    message TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            for country, advisory in advisories.items():
                # Récupérer l'avis précédent
                cur.execute("""
                    SELECT level FROM travel_advisories 
                    WHERE country = ? ORDER BY timestamp DESC LIMIT 1
                """, (country,))
                
                prev_level_result = cur.fetchone()
                prev_level = prev_level_result[0] if prev_level_result else None
                
                if prev_level and prev_level != advisory['level']:
                    # Changement détecté
                    alerts.append({
                        'country': country,
                        'previous_level': prev_level,
                        'new_level': advisory['level'],
                        'message': f"Changement d'alerte: {prev_level} → {advisory['level']}",
                        'timestamp': datetime.now().isoformat()
                    })
                
                # Sauvegarder le nouvel avis
                cur.execute("""
                    INSERT INTO travel_advisories (country, level, message)
                    VALUES (?, ?, ?)
                """, (country, advisory['level'], advisory['message']))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification alertes: {e}")
        
        return alerts
    
    def _get_country_name(self, country_code: str) -> str:
        """Convertit code pays en nom"""
        country_names = {
            'US': 'États-Unis', 'UK': 'Royaume-Uni', 'AU': 'Australie',
            'EU': 'Union Européenne', 'FR': 'France', 'CN': 'Chine',
            'RU': 'Russie', 'UA': 'Ukraine'
        }
        return country_names.get(country_code, country_code)
    
    def _get_fallback_data(self):
        """Données de fallback minimales"""
        return {
            'countries': [
                {
                    'country_code': 'FR',
                    'country_name': 'France',
                    'risk_level': 1,
                    'advice': 'Précautions normales',
                    'last_updated': datetime.now().isoformat(),
                    'sources': ['fallback']
                }
            ],
            'alerts': [],
            'total_countries': 1,
            'last_update': datetime.now().isoformat(),
            'source': 'fallback'
        }
    
    async def scan_advisories(self) -> Dict[str, Any]:
        """Lance un scan des avis - Interface pour les scans manuels"""
        try:
            if self.real_service and self.db_manager:
                results = self.real_service.scan_advisories(self.db_manager)
                return {
                    'success': True,
                    'results': results,
                    'source': 'real'
                }
            else:
                # Scan simulé
                return {
                    'success': True,
                    'results': {
                        'us_state_department': {'success': True, 'advisories_processed': 3},
                        'uk_foreign_office': {'success': True, 'advisories_processed': 2},
                        'canada_travel': {'success': True, 'advisories_processed': 2},
                        'total_countries': 7
                    },
                    'source': 'simulated',
                    'note': 'Scan simulé - service réel non disponible'
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur scan advisories: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': 'error'
            }

# Fonctions d'initialisation conservées
def init_travel_database(db_manager):
    """Initialisation DB - Ton code existant"""
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
