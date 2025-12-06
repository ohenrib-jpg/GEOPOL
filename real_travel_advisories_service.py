# Flask/real_travel_advisories_service.py
"""
Service d'avis aux voyageurs RÉELS - Sans fallback
Sources publiques officielles
"""

import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class RealTravelAdvisoriesService:
    """
    Service de récupération d'avis aux voyageurs
    Sources: US State Department, UK FCDO, Canada Travel
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (GeoPolMonitor/1.0) Contact: ohenri.b@gmail.com',
            'Accept': 'application/json, text/html',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'
        })
    
    def scan_all_sources(self) -> Dict[str, Any]:
        """
        Scanne toutes les sources d'avis
        Retourne uniquement des données réelles
        """
        results = {
            'sources_scanned': [],
            'total_advisories': 0,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # 1. US State Department
        us_result = self._scan_us_state_department()
        results['us_state_department'] = us_result
        results['sources_scanned'].append('us_state_department')
        
        # 2. UK Foreign Office
        uk_result = self._scan_uk_foreign_office()
        results['uk_foreign_office'] = uk_result
        results['sources_scanned'].append('uk_foreign_office')
        
        # 3. Canada Travel
        ca_result = self._scan_canada_travel()
        results['canada_travel'] = ca_result
        results['sources_scanned'].append('canada_travel')
        
        # Calculer total
        total = us_result.get('count', 0) + uk_result.get('count', 0) + ca_result.get('count', 0)
        results['total_advisories'] = total
        
        return results
    
    # ... (reste du code identique)
