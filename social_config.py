# social_config.py
"""
Configuration manuelle des instances Nitter et paramètres de scraping
"""

NITTER_INSTANCES = [
    'https://nitter.net',
    'https://nitter.it', 
    'https://nitter.privacydev.net',
    'https://nitter.poast.org',
    'https://nitter.tiekoetter.com',
    'https://nitter.fdn.fr',
    'https://nitter.nixnet.services',
    'https://nitter.1d4.us',
    'https://nitter.kavin.rocks',
    'https://nitter.unixfox.eu'
]

# Configuration du scraping
SCRAPING_CONFIG = {
    'timeout': 15,
    'max_retries': 3,
    'retry_delay': 2,
    'rate_limit_delay': 1,  # seconde entre les requêtes
    'user_agents': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ],
    'headers': {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
}

# Sources configurables
SOURCES_CONFIG = {
    'nitter_emotions': {
        'name': 'Nitter - Émotions',
        'type': 'nitter',
        'enabled': True,
        'config': {
            'query': 'anger OR sadness OR happiness OR fear OR joy OR "social media" OR "public opinion" -filter:replies',
            'limit': 30,
            'include_rts': False,
            'include_replies': False
        }
    },
    'nitter_geopolitics': {
        'name': 'Nitter - Géopolitique', 
        'type': 'nitter',
        'enabled': True,
        'config': {
            'query': 'geopolitics OR diplomacy OR "world news" OR international OR "foreign policy" OR war OR conflict -filter:replies',
            'limit': 30,
            'include_rts': False,
            'include_replies': False
        }
    }
}