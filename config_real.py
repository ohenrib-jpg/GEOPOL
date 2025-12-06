# Flask/config_real.py
"""
Configuration pour passer en mode RÉEL
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Mode réel vs développement
REAL_MODE = os.getenv('GEOPOL_REAL_MODE', 'false').lower() == 'true'

# Configuration SDR réelle
SDR_CONFIG = {
    'rtl_sdr_enabled': REAL_MODE and os.getenv('RTL_SDR_ENABLED', 'false') == 'true',
    'rtl_sdr_device_index': int(os.getenv('RTL_SDR_DEVICE_INDEX', '0')),
    'kiwisdr_api_key': os.getenv('KIWISDR_API_KEY', ''),
    'kiwisdr_servers': [
        'http://kiwisdr.com/',
        'http://websdr.org/'
    ],
    'sample_rate': int(os.getenv('SDR_SAMPLE_RATE', '2400000')),
    'gain': int(os.getenv('SDR_GAIN', '40'))
}

# Configuration API réelles
API_CONFIG = {
    'us_state_department': {
        'enabled': REAL_MODE,
        'api_key': os.getenv('US_STATE_DEPT_API_KEY', ''),
        'rate_limit': 10  # requêtes/minute
    },
    'yahoo_finance': {
        'enabled': REAL_MODE,
        'cache_duration': 300  # 5 minutes
    },
    'openfigi': {
        'enabled': REAL_MODE,
        'api_key': os.getenv('OPENFIGI_API_KEY', '')
    }
}

# Sources de données voyage réelles
TRAVEL_SOURCES = [
    {
        'name': 'US State Department',
        'url': 'https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.json',
        'enabled': REAL_MODE,
        'parser': 'json'
    },
    {
        'name': 'UK Foreign Office',
        'url': 'https://www.gov.uk/foreign-travel-advice',
        'enabled': REAL_MODE,
        'parser': 'html'
    },
    {
        'name': 'Canada Travel',
        'url': 'https://travel.gc.ca/travelling/advisories',
        'enabled': REAL_MODE,
        'parser': 'html'
    }
]

# Indices financiers à surveiller
FINANCIAL_SYMBOLS = [
    '^GSPC',  # S&P 500
    '^FTSE',  # FTSE 100
    '^GDAXI', # DAX
    '^FCHI',  # CAC 40
    '^N225',  # Nikkei 225
    '^HSI',   # Hang Seng
    'CL=F',   # Pétrole
    'GC=F',   # Or
    'SI=F',   # Argent
    'BTC-USD' # Bitcoin
]