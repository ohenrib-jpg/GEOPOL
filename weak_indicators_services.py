# Flask/weak_indicators_services.py
"""
Service principal des indicateurs faibles - RÉEL uniquement
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
import asyncio

logger = logging.getLogger(__name__)


class WeakIndicatorsService:
    """
    Service unifié pour les indicateurs faibles
    Utilise uniquement des sources réelles
    """
    
    def __init__(self, db_manager, real_mode=False, real_sdr_monitor=None, 
                 real_financial_data=None, real_travel_data=None):
        self.db_manager = db_manager
        self.real_mode = real_mode
        self.real_sdr_monitor = real_sdr_monitor
        self.real_financial_data = real_financial_data
        self.real_travel_data = real_travel_data
        
        # Initialiser les services réels
        self._init_services()
        
        logger.info(f"✅ WeakIndicatorsService initialisé (mode {'RÉEL' if real_mode else 'SIMULATION'})")
    
    def _init_services(self):
        """Initialise les services réels"""
        if self.real_mode and self.real_sdr_monitor:
            self.sdr_service = self.real_sdr_monitor
            logger.info("✅ Service SDR réel initialisé")
        else:
            try:
                from .geo_web_sdr import GeoWebSDR
                self.sdr_service = GeoWebSDR(self.db_manager)
                logger.info("✅ Service WebSDR initialisé")
            except Exception as e:
                logger.error(f"❌ Erreur initialisation WebSDR: {e}")
                self.sdr_service = None
        
        if self.real_mode and self.real_travel_data:
            self.travel_service = self.real_travel_data
            logger.info("✅ Service voyage réel initialisé")
        else:
            try:
                from .real_travel_advisories_service import RealTravelAdvisoriesService
                self.travel_service = RealTravelAdvisoriesService(self.db_manager)
                logger.info("✅ Service voyage initialisé")
            except Exception as e:
                logger.error(f"❌ Erreur initialisation voyage: {e}")
                self.travel_service = None
        
        if self.real_mode and self.real_financial_data:
            self.financial_service = self.real_financial_data
            logger.info("✅ Service financier réel initialisé")
        else:
            try:
                from .real_financial_service import RealFinancialService
                self.financial_service = RealFinancialService(self.db_manager)
                logger.info("✅ Service financier initialisé")
            except Exception as e:
                logger.error(f"❌ Erreur initialisation financier: {e}")
                self.financial_service = None
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        try:
        # Exécuter en parallèle
            tasks = []
        
            if self.sdr_service:
            # CORRECTION : Utilisez la bonne méthode
                if hasattr(self.sdr_service, 'monitor_all_geopolitical'):
                    tasks.append(self.sdr_service.monitor_all_geopolitical())
                elif hasattr(self.sdr_service, 'monitor_all_geopolitical_frequencies'):
                    tasks.append(self.sdr_service.monitor_all_geopolitical_frequencies())
                else:
                    tasks.append({'error': 'Service SDR: méthode non disponible'})
            else:
                tasks.append({'error': 'Service WebSDR non disponible'})
            
                if self.travel_service:
                    travel_data = self.travel_service.get_country_risk_levels()
                    tasks.append(travel_data)
                else:
                    tasks.append({'error': 'Service voyage non disponible'})
            
            if self.financial_service:
                financial_data = self.financial_service.update_all_market_data()
                tasks.append(financial_data)
            else:
                tasks.append({'error': 'Service financier non disponible'})
            
            # Exécuter
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Organiser les résultats
            sdr_data, travel_data, financial_data = results
            
            return {
                'success': True,
                'data': {
                    'sdr': sdr_data if not isinstance(sdr_data, Exception) else {'error': str(sdr_data)},
                    'travel': travel_data if not isinstance(travel_data, Exception) else {'error': str(travel_data)},
                    'financial': financial_data if not isinstance(financial_data, Exception) else {'error': str(financial_data)}
                },
                'services_available': {
                    'sdr': self.sdr_service is not None,
                    'travel': self.travel_service is not None,
                    'financial': self.financial_service is not None
                },
                'timestamp': datetime.utcnow().isoformat(),
                'real_data': self.real_mode
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur get_dashboard_data: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'real_data': self.real_mode
            }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Statut des services"""
        return {
            'sdr': {
                'available': self.sdr_service is not None,
                'mode': 'real' if self.real_mode and self.real_sdr_monitor else 'simulated',
                'last_scan': 'N/A' if not self.sdr_service else 'Prêt'
            },
            'travel': {
                'available': self.travel_service is not None,
                'mode': 'real' if self.real_mode and self.real_travel_data else 'simulated',
                'last_scan': 'N/A' if not self.travel_service else 'Prêt'
            },
            'financial': {
                'available': self.financial_service is not None,
                'mode': 'real' if self.real_mode and self.real_financial_data else 'simulated',
                'last_scan': 'N/A' if not self.financial_service else 'Prêt'
            },
            'timestamp': datetime.utcnow().isoformat(),
            'overall_mode': 'REAL' if self.real_mode else 'SIMULATION'
        }