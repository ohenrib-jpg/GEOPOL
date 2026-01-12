"""
Configuration centrale du module economique GEOPOL Analytics
"""
import os
from typing import Dict

class EconomicConfig:
    """Configuration du module economique"""

    # Durees de cache par source de donnees (en heures)
    CACHE_DURATIONS = {
        'yfinance': 2,        # Donnees boursieres: 2h
        'eurostat': 24,       # Donnees macro UE: 24h
        'fred': 12,           # Donnees Fed US: 12h
        'akshare': 6,         # Donnees asiatiques: 6h
        'comtrade': 24,       # Balances commerciales: 24h
        'alpha_vantage': 4,   # Alpha Vantage: 4h
        'default': 12         # Par defaut: 12h
    }

    # Fallback en cas d'echec API (utiliser cache expire)
    USE_STALE_CACHE_ON_ERROR = True

    # Duree max du cache expire utilisable en fallback (en jours)
    MAX_STALE_CACHE_DAYS = 7

    # Limites de surveillance personnalisee
    MAX_WATCHLIST_INDICES = 8
    MAX_WATCHLIST_ETFS = 10
    MAX_CRYPTO_WATCHLIST = 3

    # Configuration du scheduler
    SCHEDULER_ENABLED = True
    DATA_REFRESH_INTERVAL_MINUTES = 120  # 2 heures
    ALERT_CHECK_INTERVAL_MINUTES = 15    # 15 minutes
    CACHE_CLEANUP_HOUR = 2               # 2h du matin
    CACHE_CLEANUP_AGE_DAYS = 30          # Supprimer donnees > 30 jours

    # Configuration des APIs
    API_KEYS = {
        'fred': os.getenv('FRED_API_KEY', ''),
        'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY', ''),
        'comtrade': os.getenv('COMTRADE_API_KEY', '')
    }

    # Retry logic pour appels API
    API_RETRY_ATTEMPTS = 3
    API_RETRY_BACKOFF = 2  # Backoff exponentiel (secondes)
    API_TIMEOUT = 30       # Timeout requetes (secondes)

    # Indicateurs France par defaut
    DEFAULT_FRANCE_INDICATORS = [
        {
            'name': 'PIB France',
            'source': 'eurostat',
            'dataset_code': 'namq_10_gdp',
            'unit': 'Md EUR'
        },
        {
            'name': 'Inflation France',
            'source': 'eurostat',
            'dataset_code': 'prc_hicp_midx',
            'unit': '%'
        },
        {
            'name': 'Chomage France',
            'source': 'eurostat',
            'dataset_code': 'une_rt_m',
            'unit': '%'
        },
        {
            'name': 'CAC 40',
            'source': 'yfinance',
            'symbol': '^FCHI',
            'unit': 'EUR'
        }
    ]

    # Indicateurs internationaux par defaut
    DEFAULT_INTERNATIONAL_INDICES = [
        {'symbol': '^GSPC', 'name': 'S&P 500', 'region': 'USA'},
        {'symbol': '^DJI', 'name': 'Dow Jones', 'region': 'USA'},
        {'symbol': '^IXIC', 'name': 'NASDAQ', 'region': 'USA'},
        {'symbol': '^GDAXI', 'name': 'DAX', 'region': 'Allemagne'},
        {'symbol': '^FTSE', 'name': 'FTSE 100', 'region': 'UK'},
        {'symbol': '^N225', 'name': 'Nikkei 225', 'region': 'Japon'},
        {'symbol': '000001.SS', 'name': 'Shanghai Composite', 'region': 'Chine'},
        {'symbol': '^HSI', 'name': 'Hang Seng', 'region': 'Hong Kong'}
    ]

    # ============================================================
    # INDICATEURS INTERNATIONAUX - Configuration complete
    # ============================================================

    # Categories d'indicateurs internationaux
    INTERNATIONAL_CATEGORIES = ['macro', 'forex', 'debt', 'commodities', 'indices', 'safe_haven', 'synthetic']

    # Indicateurs internationaux par categorie
    INTERNATIONAL_INDICATORS = {
        # Categorie 1: Stabilite Macro-Financiere
        'macro': [
            {'id': 'fed_rate', 'name': 'Taux Fed', 'source': 'fred', 'series': 'FEDFUNDS', 'unit': '%', 'category': 'macro'},
            {'id': 'us_yield_curve', 'name': 'Courbe des taux US (10Y-2Y)', 'source': 'fred', 'series': 'T10Y2Y', 'unit': '%', 'category': 'macro'},
            {'id': 'us_inflation', 'name': 'Inflation USA (CPI)', 'source': 'fred', 'series': 'CPIAUCSL', 'unit': '%', 'category': 'macro'},
            {'id': 'us_unemployment', 'name': 'Chomage USA', 'source': 'fred', 'series': 'UNRATE', 'unit': '%', 'category': 'macro'},
            {'id': 'us_gdp', 'name': 'PIB USA', 'source': 'fred', 'series': 'GDP', 'unit': 'Md USD', 'category': 'macro'},
            {'id': 'us_industrial', 'name': 'Production Industrielle USA', 'source': 'fred', 'series': 'INDPRO', 'unit': 'indice', 'category': 'macro'},
        ],

        # Categorie 2: Systemes Monetaires (Forex)
        'forex': [
            {'id': 'dxy', 'name': 'Dollar Index (DXY)', 'source': 'yfinance', 'symbol': 'DX-Y.NYB', 'unit': 'indice', 'category': 'forex'},
            {'id': 'eur_usd', 'name': 'EUR/USD', 'source': 'yfinance', 'symbol': 'EURUSD=X', 'unit': '', 'category': 'forex'},
            {'id': 'usd_cny', 'name': 'USD/CNY', 'source': 'yfinance', 'symbol': 'CNY=X', 'unit': '', 'category': 'forex'},
            {'id': 'usd_jpy', 'name': 'USD/JPY', 'source': 'yfinance', 'symbol': 'JPY=X', 'unit': '', 'category': 'forex'},
            {'id': 'gbp_usd', 'name': 'GBP/USD', 'source': 'yfinance', 'symbol': 'GBPUSD=X', 'unit': '', 'category': 'forex'},
            {'id': 'usd_chf', 'name': 'USD/CHF', 'source': 'yfinance', 'symbol': 'CHF=X', 'unit': '', 'category': 'forex'},
            {'id': 'usd_rub', 'name': 'USD/RUB', 'source': 'yfinance', 'symbol': 'RUB=X', 'unit': '', 'category': 'forex'},
            {'id': 'usd_try', 'name': 'USD/TRY', 'source': 'yfinance', 'symbol': 'TRY=X', 'unit': '', 'category': 'forex'},
            {'id': 'usd_brl', 'name': 'USD/BRL', 'source': 'yfinance', 'symbol': 'BRL=X', 'unit': '', 'category': 'forex'},
            {'id': 'usd_zar', 'name': 'USD/ZAR', 'source': 'yfinance', 'symbol': 'ZAR=X', 'unit': '', 'category': 'forex'},
        ],

        # Categorie 3: Dette Souveraine
        'debt': [
            {'id': 'us_10y', 'name': 'Taux US 10 ans', 'source': 'fred', 'series': 'DGS10', 'unit': '%', 'category': 'debt'},
            {'id': 'us_2y', 'name': 'Taux US 2 ans', 'source': 'fred', 'series': 'DGS2', 'unit': '%', 'category': 'debt'},
            {'id': 'de_10y', 'name': 'Bund Allemand 10 ans', 'source': 'yfinance', 'symbol': '^TNX', 'unit': '%', 'category': 'debt'},
            {'id': 'vix', 'name': 'VIX (Volatilite)', 'source': 'yfinance', 'symbol': '^VIX', 'unit': 'indice', 'category': 'debt'},
            {'id': 'emb', 'name': 'iShares Emergents Bonds', 'source': 'yfinance', 'symbol': 'EMB', 'unit': 'USD', 'category': 'debt'},
        ],

        # Categorie 4: Matieres Premieres Strategiques
        'commodities': [
            {'id': 'brent', 'name': 'Petrole Brent', 'source': 'yfinance', 'symbol': 'BZ=F', 'unit': 'USD/barrel', 'category': 'commodities'},
            {'id': 'wti', 'name': 'Petrole WTI', 'source': 'yfinance', 'symbol': 'CL=F', 'unit': 'USD/barrel', 'category': 'commodities'},
            {'id': 'gas_us', 'name': 'Gaz Naturel Henry Hub', 'source': 'yfinance', 'symbol': 'NG=F', 'unit': 'USD/MMBtu', 'category': 'commodities'},
            {'id': 'gold', 'name': 'Or', 'source': 'yfinance', 'symbol': 'GC=F', 'unit': 'USD/oz', 'category': 'commodities'},
            {'id': 'silver', 'name': 'Argent', 'source': 'yfinance', 'symbol': 'SI=F', 'unit': 'USD/oz', 'category': 'commodities'},
            {'id': 'copper', 'name': 'Cuivre', 'source': 'yfinance', 'symbol': 'HG=F', 'unit': 'USD/lb', 'category': 'commodities'},
            {'id': 'wheat', 'name': 'Ble', 'source': 'yfinance', 'symbol': 'ZW=F', 'unit': 'USD/bushel', 'category': 'commodities'},
            {'id': 'corn', 'name': 'Mais', 'source': 'yfinance', 'symbol': 'ZC=F', 'unit': 'USD/bushel', 'category': 'commodities'},
            {'id': 'lithium_etf', 'name': 'Lithium ETF', 'source': 'yfinance', 'symbol': 'LIT', 'unit': 'USD', 'category': 'commodities'},
            {'id': 'rare_earth_etf', 'name': 'Terres Rares ETF', 'source': 'yfinance', 'symbol': 'REMX', 'unit': 'USD', 'category': 'commodities'},
        ],

        # Categorie 5: Indices Boursiers Mondiaux
        'indices': [
            {'id': 'sp500', 'name': 'S&P 500', 'source': 'yfinance', 'symbol': '^GSPC', 'unit': 'points', 'category': 'indices'},
            {'id': 'nasdaq', 'name': 'NASDAQ Composite', 'source': 'yfinance', 'symbol': '^IXIC', 'unit': 'points', 'category': 'indices'},
            {'id': 'dow_jones', 'name': 'Dow Jones', 'source': 'yfinance', 'symbol': '^DJI', 'unit': 'points', 'category': 'indices'},
            {'id': 'msci_world', 'name': 'MSCI World ETF', 'source': 'yfinance', 'symbol': 'URTH', 'unit': 'USD', 'category': 'indices'},
            {'id': 'msci_em', 'name': 'MSCI Emerging Markets', 'source': 'yfinance', 'symbol': 'EEM', 'unit': 'USD', 'category': 'indices'},
            {'id': 'csi300', 'name': 'CSI 300 (Chine)', 'source': 'yfinance', 'symbol': '000300.SS', 'unit': 'points', 'category': 'indices'},
            {'id': 'nikkei', 'name': 'Nikkei 225', 'source': 'yfinance', 'symbol': '^N225', 'unit': 'points', 'category': 'indices'},
            {'id': 'eurostoxx', 'name': 'Euro Stoxx 50', 'source': 'yfinance', 'symbol': '^STOXX50E', 'unit': 'points', 'category': 'indices'},
            {'id': 'ftse', 'name': 'FTSE 100', 'source': 'yfinance', 'symbol': '^FTSE', 'unit': 'points', 'category': 'indices'},
            {'id': 'dax', 'name': 'DAX', 'source': 'yfinance', 'symbol': '^GDAXI', 'unit': 'points', 'category': 'indices'},
        ],

        # Categorie 6: Valeurs Refuges
        'safe_haven': [
            {'id': 'gold_safe', 'name': 'Or (Refuge)', 'source': 'yfinance', 'symbol': 'GC=F', 'unit': 'USD/oz', 'category': 'safe_haven'},
            {'id': 'bitcoin', 'name': 'Bitcoin', 'source': 'yfinance', 'symbol': 'BTC-USD', 'unit': 'USD', 'category': 'safe_haven'},
            {'id': 'chf', 'name': 'Franc Suisse (CHF/USD)', 'source': 'yfinance', 'symbol': 'CHF=X', 'unit': '', 'category': 'safe_haven'},
            {'id': 'jpy', 'name': 'Yen Japonais (JPY/USD)', 'source': 'yfinance', 'symbol': 'JPY=X', 'unit': '', 'category': 'safe_haven'},
            {'id': 'treasury_etf', 'name': 'US Treasury ETF', 'source': 'yfinance', 'symbol': 'TLT', 'unit': 'USD', 'category': 'safe_haven'},
        ],

        # Categorie 7: Indicateurs Synthetiques (Stress/Risque)
        'synthetic': [
            {'id': 'vix_stress', 'name': 'VIX (Stress Global)', 'source': 'yfinance', 'symbol': '^VIX', 'unit': 'indice', 'category': 'synthetic'},
            {'id': 'ted_spread', 'name': 'TED Spread', 'source': 'fred', 'series': 'TEDRATE', 'unit': '%', 'category': 'synthetic'},
            {'id': 'yield_curve', 'name': 'Courbe des taux (10Y-2Y)', 'source': 'fred', 'series': 'T10Y2Y', 'unit': '%', 'category': 'synthetic'},
            {'id': 'credit_spread', 'name': 'High Yield Spread', 'source': 'yfinance', 'symbol': 'HYG', 'unit': 'USD', 'category': 'synthetic'},
        ],
    }

    # Indicateurs par defaut pour les widgets internationaux
    DEFAULT_INTERNATIONAL_WIDGETS = ['vix', 'dxy', 'brent', 'gold', 'eur_usd', 'sp500']

    # Indicateurs pour le bandeau d'alerte rapide
    INTERNATIONAL_ALERT_INDICATORS = ['vix', 'dxy', 'brent', 'us_10y', 'gold']

    # Commodites strategiques
    STRATEGIC_COMMODITIES = [
        {'symbol': 'GC=F', 'name': 'Or', 'unit': 'USD/oz'},
        {'symbol': 'SI=F', 'name': 'Argent', 'unit': 'USD/oz'},
        {'symbol': 'PL=F', 'name': 'Platine', 'unit': 'USD/oz'},
        {'symbol': 'HG=F', 'name': 'Cuivre', 'unit': 'USD/lb'},
        {'symbol': 'NI=F', 'name': 'Nickel', 'unit': 'USD/lb'},
        {'symbol': 'CL=F', 'name': 'Petrole WTI', 'unit': 'USD/barrel'},
        {'symbol': 'BZ=F', 'name': 'Petrole Brent', 'unit': 'USD/barrel'},
        {'symbol': 'NG=F', 'name': 'Gaz naturel', 'unit': 'USD/MMBtu'}
    ]

    # Top cryptomonnaies disponibles
    TOP_CRYPTOCURRENCIES = [
        {'symbol': 'BTC-USD', 'name': 'Bitcoin'},
        {'symbol': 'ETH-USD', 'name': 'Ethereum'},
        {'symbol': 'BNB-USD', 'name': 'Binance Coin'},
        {'symbol': 'XRP-USD', 'name': 'Ripple'},
        {'symbol': 'ADA-USD', 'name': 'Cardano'},
        {'symbol': 'SOL-USD', 'name': 'Solana'},
        {'symbol': 'DOT-USD', 'name': 'Polkadot'},
        {'symbol': 'DOGE-USD', 'name': 'Dogecoin'},
        {'symbol': 'MATIC-USD', 'name': 'Polygon'},
        {'symbol': 'LTC-USD', 'name': 'Litecoin'}
    ]

    # Configuration export RAG
    RAG_EXPORT_CATEGORIES = [
        'france_indicators',
        'international_indicators',
        'financial_markets',
        'strategic_commodities',
        'cryptocurrencies',
        'watchlist_portfolio',
        'alert_events'
    ]

    RAG_FORMAT_VERSION = '1.0'

    @classmethod
    def get_cache_duration(cls, source: str) -> int:
        """Retourne la duree de cache pour une source donnee"""
        return cls.CACHE_DURATIONS.get(source, cls.CACHE_DURATIONS['default'])

    @classmethod
    def get_api_key(cls, api_name: str) -> str:
        """Retourne la cle API pour un service donne"""
        return cls.API_KEYS.get(api_name, '')

    @classmethod
    def validate_watchlist_limits(cls, watchlist_type: str, current_count: int) -> bool:
        """Verifie si on peut ajouter un element a la watchlist"""
        if watchlist_type == 'index':
            return current_count < cls.MAX_WATCHLIST_INDICES
        elif watchlist_type == 'etf':
            return current_count < cls.MAX_WATCHLIST_ETFS
        return False

    @classmethod
    def validate_crypto_limit(cls, current_count: int) -> bool:
        """Verifie si on peut ajouter une crypto"""
        return current_count < cls.MAX_CRYPTO_WATCHLIST
