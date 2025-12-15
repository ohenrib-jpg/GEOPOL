# Flask/geopol_data/connectors/sdr_spectrum_service.py (corrigé)
"""
Service d'analyse spectrale SDR - Version corrigée des imports
"""

import logging
import requests
import os
import numpy as np
import time
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class SDRSpectrumService:
    """
    Service d'analyse spectrale passive via WebSDR
    """
    
    # Serveurs WebSDR publics testés
    WEBSDR_SERVERS = [
        {
            'name': 'University of Twente WebSDR',
            'url': 'http://websdr.ewi.utwente.nl:8901/',
            'type': 'websdr',
            'location': 'Netherlands',
            'status': 'unknown'
        },
        {
            'name': 'KiwiSDR Network',
            'url': 'https://kiwisdr.com/public/',
            'type': 'kiwisdr',
            'location': 'Global',
            'status': 'unknown'
        }
    ]
    
    # Fréquences géopolitiques critiques (kHz)
    GEOPOLITICAL_FREQUENCIES = {
        'emergency': [
            {'freq': 2182, 'name': 'Détresse Maritime MF', 'baseline_peaks': 3},
            {'freq': 121500, 'name': 'Urgence Aviation VHF', 'baseline_peaks': 5}
        ],
        'military': [
            {'freq': 4625, 'name': 'UVB-76 "The Buzzer"', 'baseline_peaks': 8},
            {'freq': 11175, 'name': 'HFGCS US Military', 'baseline_peaks': 12}
        ],
        'broadcast': [
            {'freq': 6000, 'name': 'BBC World Service', 'baseline_peaks': 15},
            {'freq': 9410, 'name': 'Voice of America', 'baseline_peaks': 10}
        ]
    }
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.active_servers = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GeopoliticalSDR/2.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        self.timeout = 15
        self.cache = {}
        self.cache_ttl = 60
        
        # Mode réel ou simulation
        self.real_mode = os.getenv('GEOPOL_REAL_MODE', 'false').lower() == 'true'
        
        self._init_database()
        logger.info(f"✅ SDRSpectrumService initialisé - Mode: {'RÉEL' if self.real_mode else 'SIMULATION'}")
    
    def _init_database(self):
        """Initialise les tables SDR - VERSION SIMPLIFIÉE"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            # Table des scans spectraux
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sdr_spectrum_scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    frequency_khz INTEGER NOT NULL,
                    category TEXT,
                    peak_count INTEGER DEFAULT 0,
                    power_db REAL,
                    signal_type TEXT,
                    server_name TEXT,
                    baseline_deviation REAL,
                    anomaly_detected BOOLEAN DEFAULT 0,
                    real_data BOOLEAN DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des serveurs
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sdr_websdr_servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT UNIQUE,
                    location TEXT,
                    status TEXT DEFAULT 'unknown',
                    last_check DATETIME
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("✅ Tables SDR initialisées")
            
        except Exception as e:
            logger.error(f"❌ Erreur init BDD: {e}")
    
    def discover_active_servers(self) -> List[Dict]:
        """Découvre les serveurs WebSDR actifs"""
        if not self.real_mode:
            # Mode simulation
            self.active_servers = [{
                'name': 'Simulated WebSDR',
                'url': 'http://simulated.websdr.local/',
                'type': 'websdr',
                'location': 'Simulation',
                'status': 'active'
            }]
            return self.active_servers
        
        active_servers = []
        
        for server in self.WEBSDR_SERVERS:
            try:
                response = self.session.get(server['url'], timeout=10, verify=False)
                if response.status_code == 200:
                    server_info = server.copy()
                    server_info['status'] = 'active'
                    server_info['last_check'] = datetime.utcnow().isoformat()
                    active_servers.append(server_info)
                    logger.info(f"✅ Serveur {server['name']} actif")
                else:
                    logger.warning(f"⚠️ {server['name']}: HTTP {response.status_code}")
            except Exception as e:
                logger.warning(f"🔌 {server['name']} inaccessible: {e}")
        
        self.active_servers = active_servers
        logger.info(f"📡 {len(active_servers)} serveurs SDR actifs")
        return active_servers
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Données pour le dashboard SDR"""
        # Générer des données simulées
        frequencies_ui = []
        
        for category, freq_list in self.GEOPOLITICAL_FREQUENCIES.items():
            for freq_info in freq_list:
                peak_count = random.randint(1, 20)
                power_db = round(-70 + random.random() * 30, 1)
                
                frequencies_ui.append({
                    'frequency_khz': freq_info['freq'],
                    'name': freq_info['name'],
                    'category': category,
                    'baseline_peaks': freq_info['baseline_peaks'],
                    'status': 'active' if power_db > -60 else 'inactive',
                    'peak_count': peak_count,
                    'power_db': power_db,
                    'last_scan': datetime.utcnow().isoformat(),
                    'anomaly': random.random() > 0.8
                })
        
        return {
            'success': True,
            'stats': {
                'total_frequencies': len(frequencies_ui),
                'total_scans': random.randint(50, 200),
                'anomalies_count': random.randint(0, 5),
                'real_data_ratio': 0.0,
                'active_servers': len(self.active_servers)
            },
            'frequencies': frequencies_ui,
            'recent_scans': [],
            'anomalies': [],
            'real_data': False,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def scan_frequency(self, frequency_khz: int, category: str = 'custom') -> Dict[str, Any]:
        """Scanne une fréquence spécifique"""
        # Simulation simple
        baseline = random.randint(3, 15)
        peaks = baseline + random.randint(-2, 5)
        power_db = round(-70 + random.random() * 25, 1)
        anomaly = random.random() > 0.85
        
        result = {
            'success': True,
            'frequency_khz': frequency_khz,
            'peak_count': peaks,
            'power_db': power_db,
            'signal_type': self._classify_signal(peaks, power_db),
            'signal_present': power_db > -80,
            'baseline_peaks': baseline,
            'anomaly_detected': anomaly,
            'servers_used': 0,
            'real_data': False,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Sauvegarder en BDD
        self._save_scan_result(result, frequency_khz, category)
        
        return result
    
    def _classify_signal(self, peaks: int, power_db: float) -> str:
        """Classifie le type de signal"""
        if power_db < -90:
            return 'noise'
        elif peaks == 0:
            return 'carrier'
        elif peaks == 1:
            return 'cw'
        elif 2 <= peaks <= 5:
            return 'ssb'
        elif 6 <= peaks <= 15:
            return 'digital'
        else:
            return 'broadcast'
    
    def _save_scan_result(self, scan: Dict, frequency_khz: int, category: str):
        """Sauvegarde un résultat de scan"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO sdr_spectrum_scans 
                (frequency_khz, category, peak_count, power_db, signal_type, real_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                frequency_khz,
                category,
                scan['peak_count'],
                scan['power_db'],
                scan['signal_type'],
                scan['real_data']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde scan: {e}")
    
    def get_test_spectrum(self) -> Dict[str, Any]:
        """Génère un spectre de test"""
        frequencies = np.linspace(0, 30, 1000)
        powers = -90 + 20 * np.random.randn(1000)
        
        # Ajouter des pics aux fréquences géopolitiques
        for category, freq_list in self.GEOPOLITICAL_FREQUENCIES.items():
            for freq_info in freq_list:
                freq_mhz = freq_info['freq'] / 1000.0
                if freq_mhz <= 30:
                    idx = np.argmin(np.abs(frequencies - freq_mhz))
                    if 0 <= idx < len(powers):
                        sigma = 0.05
                        gaussian = 30 * np.exp(-((frequencies - freq_mhz) ** 2) / (2 * sigma ** 2))
                        powers += gaussian
        
        return {
            'success': True,
            'frequencies_mhz': frequencies.tolist(),
            'powers': powers.tolist(),
            'timestamp': datetime.utcnow().isoformat()
        }

# Version asynchrone pour compatibilité
class AsyncSDRSpectrumService(SDRSpectrumService):
    """Version asynchrone du service SDR"""
    
    async def scan_critical_frequencies(self):
        """Scanne les fréquences critiques (asynchrone)"""
        results = {}
        
        for category, frequencies in self.GEOPOLITICAL_FREQUENCIES.items():
            category_results = []
            
            for freq_info in frequencies:
                scan_result = self.scan_frequency(freq_info['freq'], category)
                scan_result['name'] = freq_info['name']
                category_results.append(scan_result)
            
            if category_results:
                results[category] = category_results
        
        return {
            'success': True,
            'results': results,
            'stats': {
                'total_scans': sum(len(r) for r in results.values()),
                'active_servers': len(self.active_servers)
            },
            'timestamp': datetime.utcnow().isoformat()
        }