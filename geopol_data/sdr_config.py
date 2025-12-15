# Flask/geopol_data/sdr_config.py
"""
Configuration du module SDR
"""

import os
from typing import Dict, List, Tuple

# ============================================================================
# CONFIGURATION SERVEURS SDR
# ============================================================================

class SDRServersConfig:
    """Configuration des serveurs SDR publics"""
    
    # Temps d'attente (secondes)
    CONNECT_TIMEOUT = 10
    READ_TIMEOUT = 15
    
    # Nombre maximum de tentatives
    MAX_RETRIES = 2
    
    # Délai entre les requêtes (secondes)
    REQUEST_DELAY = 0.5
    
    # User-Agent
    USER_AGENT = "Mozilla/5.0 (compatible; GeopoliticalSDR/2.0; +http://github.com/geopol)"

class WebSDRServers:
    """Liste des serveurs WebSDR fiables"""
    
    # Serveurs hautement fiables
    PRIMARY_SERVERS = [
        {
            'name': 'University of Twente WebSDR',
            'url': 'http://websdr.ewi.utwente.nl:8901/',
            'type': 'websdr',
            'location': 'Netherlands',
            'frequency_range': (0, 30),  # MHz
            'reliability': 'high'
        }
    ]
    
    # Serveurs secondaires
    SECONDARY_SERVERS = [
        {
            'name': 'KiwiSDR Network',
            'url': 'https://kiwisdr.com/public/',
            'type': 'kiwisdr',
            'location': 'Global',
            'frequency_range': (0, 30),
            'reliability': 'medium'
        },
        {
            'name': 'WebSDR University of Halle',
            'url': 'http://websdr.ewi.utwente.nl:8901/',
            'type': 'websdr',
            'location': 'Germany',
            'frequency_range': (0, 30),
            'reliability': 'medium'
        }
    ]
    
    # Serveurs de secours
    FALLBACK_SERVERS = [
        {
            'name': 'WebSDR PA3WEG',
            'url': 'http://websdr.pa3weg.nl/',
            'type': 'websdr',
            'location': 'Netherlands',
            'frequency_range': (0, 30),
            'reliability': 'low'
        },
        {
            'name': 'SDR.hu Receiver List',
            'url': 'http://sdr.hu/',
            'type': 'directory',
            'location': 'Global',
            'frequency_range': (0, 30),
            'reliability': 'low'
        }
    ]
    
    @classmethod
    def get_all_servers(cls) -> List[Dict]:
        """Retourne tous les serveurs"""
        return cls.PRIMARY_SERVERS + cls.SECONDARY_SERVERS + cls.FALLBACK_SERVERS
    
    @classmethod
    def get_server_by_name(cls, name: str) -> Dict:
        """Trouve un serveur par son nom"""
        for server in cls.get_all_servers():
            if server['name'] == name:
                return server
        return {}

# ============================================================================
# FRÉQUENCES GÉOPOLITIQUES
# ============================================================================

class GeopoliticalFrequencies:
    """Fréquences géopolitiques critiques"""
    
    # Fréquences en kHz
    FREQUENCIES = {
        # Bandes de détresse
        'DISTRESS': [
            (2182, 'Détresse Maritime MF'),
            (156800, 'Détresse Maritime VHF'),
            (121500, 'Urgence Aviation VHF'),
            (243000, 'Urgence Aviation UHF'),
        ],
        
        # Communications militaires
        'MILITARY': [
            (4625, 'UVB-76 "The Buzzer" (RUS)'),
            (5800, 'The Pip (RUS)'),
            (8130, 'Air Flotte North (RUS)'),
            (8992, 'OTAN Military'),
            (11175, 'HFGCS US Military'),
            (15016, 'US Air Force'),
        ],
        
        # Diplomatie et gouvernement
        'DIPLOMATIC': [
            (5732, 'Diplomatic HF'),
            (6731, 'Diplomatic Traffic'),
            (15045, 'Diplomatic Comms'),
        ],
        
        # Broadcast international
        'BROADCAST': [
            (6000, 'BBC World Service'),
            (9410, 'Voice of America'),
            (11710, 'Radio China'),
            (15300, 'Radio France Int.'),
            (17705, 'Deutsche Welle'),
        ],
        
        # Stations de nombres
        'NUMBERS': [
            (9330, 'Cuban Numbers'),
            (13780, 'Lincolnshire Poacher'),
            (14787, 'Russian Numbers'),
        ],
        
        # Maritime
        'MARITIME': [
            (2187, 'Détresse Maritime DSC'),
            (4207, 'Trafic Maritime HF'),
            (6312, 'Maritime Comms'),
            (8414, 'Naval Communications'),
        ]
    }
    
    @classmethod
    def get_frequency_by_value(cls, freq_khz: int) -> Dict:
        """Trouve une fréquence par sa valeur"""
        for category, freqs in cls.FREQUENCIES.items():
            for freq, name in freqs:
                if freq == freq_khz:
                    return {
                        'frequency_khz': freq,
                        'name': name,
                        'category': category,
                        'description': f'Fréquence {category.lower()}'
                    }
        return None

# ============================================================================
# CONFIGURATION ANALYSE
# ============================================================================

class SDRMetricsConfig:
    """Configuration des métriques SDR"""
    
    # Seuils d'anomalie
    ANOMALY_THRESHOLDS = {
        'CRITICAL': 80,    # Rouge
        'HIGH_RISK': 60,   # Orange
        'WARNING': 40,     # Jaune
        'STABLE': 20,      # Vert clair
        'OPTIMAL': 0       # Vert
    }
    
    # Seuils de puissance (dB)
    POWER_THRESHOLDS = {
        'STRONG': -60,     # Signal fort
        'GOOD': -70,       # Signal bon
        'WEAK': -80,       # Signal faible
        'NOISE': -90       # Bruit
    }
    
    # Durées (minutes)
    SCAN_INTERVAL = 5      # Intervalle entre scans
    CACHE_TTL = 60         # Durée de vie du cache
    HISTORY_HOURS = 24     # Historique à conserver
    
    # Paramètres d'analyse
    PEAK_DETECTION_THRESHOLD = 0.15  # Seuil détection pics
    BANDWIDTH_DEFAULT = 5            # Bandwidth par défaut (kHz)

# ============================================================================
# CONFIGURATION ZONES GÉOPOLITIQUES
# ============================================================================

class GeopoliticalZones:
    """Configuration des zones géopolitiques"""
    
    # Format: [lat_min, lon_min, lat_max, lon_max]
    ZONES = {
        'NATO_EUROPE': {
            'name': 'OTAN Europe',
            'coordinates': [(35, -10), (35, 30), (70, 30), (70, -10)],
            'center': (52.5, 10),
            'countries': ['FR', 'DE', 'GB', 'IT', 'ES', 'PL', 'NL', 'BE', 'SE'],
            'alliances': ['NATO', 'EU']
        },
        'NATO_NA': {
            'name': 'OTAN Amérique du Nord',
            'coordinates': [(25, -130), (25, -60), (70, -60), (70, -130)],
            'center': (45, -95),
            'countries': ['US', 'CA'],
            'alliances': ['NATO', 'NORAD']
        },
        'BRICS_CORE': {
            'name': 'BRICS Noyau',
            'coordinates': [(-35, -80), (-35, 150), (60, 150), (60, -80)],
            'center': (30, 60),
            'countries': ['BR', 'RU', 'IN', 'CN', 'ZA'],
            'alliances': ['BRICS', 'SCO']
        },
        'MIDDLE_EAST': {
            'name': 'Moyen-Orient',
            'coordinates': [(12, 30), (12, 60), (40, 60), (40, 30)],
            'center': (30, 45),
            'countries': ['SA', 'IR', 'IQ', 'SY', 'IL', 'AE', 'QA'],
            'alliances': ['OPEC', 'GCC']
        },
        'ASIA_PACIFIC': {
            'name': 'Asie-Pacifique',
            'coordinates': [(-50, 90), (-50, 180), (50, 180), (50, 90)],
            'center': (0, 135),
            'countries': ['JP', 'KR', 'AU', 'ID', 'VN', 'PH', 'MY'],
            'alliances': ['ASEAN', 'APEC']
        }
    }
    
    @classmethod
    def get_zone_by_country(cls, country_code: str) -> str:
        """Trouve la zone d'un pays"""
        for zone_id, zone in cls.ZONES.items():
            if country_code in zone['countries']:
                return zone_id
        return 'GLOBAL'

# ============================================================================
# UTILITAIRES
# ============================================================================

def get_sdr_mode() -> str:
    """Détermine le mode SDR"""
    real_mode = os.getenv('GEOPOL_REAL_MODE', 'false').lower() == 'true'
    return 'RÉEL' if real_mode else 'SIMULATION'

def get_available_frequencies(limit_per_category: int = 3) -> List[Dict]:
    """Retourne les fréquences disponibles"""
    frequencies = []
    
    for category, freqs in GeopoliticalFrequencies.FREQUENCIES.items():
        for i, (freq, name) in enumerate(freqs):
            if i < limit_per_category:
                frequencies.append({
                    'frequency_khz': freq,
                    'name': name,
                    'category': category,
                    'priority': len(freqs) - i
                })
    
    return sorted(frequencies, key=lambda x: x['priority'], reverse=True)

# ============================================================================
# EXPORT CONFIG
# ============================================================================

SDR_CONFIG = {
    'servers': SDRServersConfig,
    'frequencies': GeopoliticalFrequencies,
    'metrics': SDRMetricsConfig,
    'zones': GeopoliticalZones,
    'mode': get_sdr_mode()
}