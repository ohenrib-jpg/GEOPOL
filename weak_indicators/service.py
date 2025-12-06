# Flask/weak_indicators/service.py
"""Service principal unifié des indicateurs faibles - VERSION CORRIGÉE"""

import logging
from datetime import datetime
from typing import Dict, Any, List
import asyncio

logger = logging.getLogger(__name__)

class WeakIndicatorsService:
    """Service principal unifié des indicateurs faibles"""
    
    def __init__(self, db_manager=None, config=None):
        """Constructeur corrigé acceptant db_manager et config"""
        self.db_manager = db_manager
        self.config = config or {}
        self.real_mode = self.config.get('real_mode', False)
        
        # Initialiser les services
        self.sdr_service = None
        self.travel_service = None
        self.financial_service = None
        
        self._init_services()
    
    def _init_services(self):
        """Initialisation des services adaptés depuis tes fichiers existants"""
        try:
            # Service SDR (à créer ou utiliser existant)
            from .realtime.sdr_monitor import SDRMonitor
            self.sdr_service = SDRMonitor(self.db_manager, self.real_mode)
            
            # Service Voyage adapté depuis tes fichiers
            from .realtime.travel_service import TravelAdvisoryService
            self.travel_service = TravelAdvisoryService(self.db_manager)
            
            # Service Financier adapté depuis tes fichiers
            from .realtime.financial_service import FinancialDataService
            self.financial_service = FinancialDataService(self.db_manager)
            
            logger.info("✅ Services adaptés initialisés depuis fichiers existants")
            
        except ImportError as e:
            logger.error(f"❌ Erreur import services: {e}")
            # Créer des services fallback
            self._create_fallback_services()
        except Exception as e:
            logger.error(f"❌ Erreur initialisation services adaptés: {e}")
            # Les services seront None, mais l'application continuera
    
    def _create_fallback_services(self):
        """Crée des services fallback si les vrais services ne peuvent pas être chargés"""
        from .fallback_services import (
            FallbackSDRService,
            FallbackTravelService,
            FallbackFinancialService
        )
        self.sdr_service = FallbackSDRService()
        self.travel_service = FallbackTravelService()
        self.financial_service = FallbackFinancialService()
        logger.info("✅ Services fallback initialisés")
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Endpoint principal - Données consolidées"""
        try:
            # Collecte parallèle des données
            tasks = {}
            
            if self.sdr_service:
                tasks['sdr'] = self.sdr_service.get_active_monitoring()
            else:
                tasks['sdr'] = self._get_fallback_sdr_data()
            
            if self.travel_service:
                tasks['travel'] = self.travel_service.get_country_risks()
            else:
                tasks['travel'] = self._get_fallback_travel_data()
                
            if self.financial_service:
                tasks['financial'] = self.financial_service.get_market_data()
            else:
                tasks['financial'] = self._get_fallback_financial_data()
            
            # Exécution parallèle
            results = {}
            for key, task in tasks.items():
                if asyncio.iscoroutine(task):
                    results[key] = await task
                else:
                    results[key] = task
            
            return {
                'success': True,
                'data': results,
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'real_mode': self.real_mode,
                    'services_available': {
                        'sdr': self.sdr_service is not None,
                        'travel': self.travel_service is not None,
                        'financial': self.financial_service is not None
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur get_dashboard_data: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': self._get_fallback_all_data(),
                'metadata': {'timestamp': datetime.now().isoformat(), 'real_mode': False}
            }
    
    # Méthodes fallback simplifiées
    def _get_fallback_sdr_data(self):
        return {
            'active_monitors': [
                {'frequency': '14300 kHz', 'status': 'active', 'signal_strength': -65},
                {'frequency': '2182 kHz', 'status': 'active', 'signal_strength': -72}
            ],
            'total_monitors': 2,
            'last_scan': datetime.now().isoformat(),
            'source': 'fallback'
        }
    
    def _get_fallback_travel_data(self):
        return {
            'countries': [
                {'code': 'FR', 'name': 'France', 'risk_level': 1, 'advice': 'Normal'},
                {'code': 'UA', 'name': 'Ukraine', 'risk_level': 4, 'advice': 'Avoid all travel'}
            ],
            'last_update': datetime.now().isoformat(),
            'source': 'fallback'
        }
    
    def _get_fallback_financial_data(self):
        return {
            'indices': {
                'CAC40': {'value': 7345.67, 'change': +1.2},
                'S&P500': {'value': 5123.45, 'change': +0.8}
            },
            'last_update': datetime.now().isoformat(),
            'source': 'fallback'
        }
    
    def _get_fallback_all_data(self):
        """Données fallback complètes"""
        return {
            'sdr': self._get_fallback_sdr_data(),
            'travel': self._get_fallback_travel_data(),
            'financial': self._get_fallback_financial_data()
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Statut simplifié des services"""
        return {
            'status': 'operational',
            'services': {
                'sdr': {'available': self.sdr_service is not None, 'mode': 'real' if self.real_mode else 'simulated'},
                'travel': {'available': self.travel_service is not None},
                'financial': {'available': self.financial_service is not None}
            },
            'timestamp': datetime.now().isoformat()
        }