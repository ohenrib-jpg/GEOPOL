# Flask/weak_indicators/fallback_services.py
"""Services fallback pour WeakIndicators"""

import logging
from datetime import datetime
from typing import Dict, Any
import asyncio

logger = logging.getLogger(__name__)

class FallbackSDRService:
    """Service SDR fallback"""
    
    async def get_active_monitoring(self):
        """Données SDR fallback"""
        return {
            'active_monitors': [
                {
                    'id': 1,
                    'frequency': '14300 kHz',
                    'description': 'Fréquence diplomatique internationale',
                    'status': 'active',
                    'signal_strength': -65,
                    'last_activity': datetime.now().isoformat(),
                    'location': 'Europe'
                }
            ],
            'total_active': 1,
            'last_scan': datetime.now().isoformat(),
            'source': 'fallback'
        }

class FallbackTravelService:
    """Service voyage fallback"""
    
    async def get_country_risks(self):
        """Données voyage fallback"""
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

class FallbackFinancialService:
    """Service financier fallback"""
    
    async def get_market_data(self):
        """Données financières fallback"""
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