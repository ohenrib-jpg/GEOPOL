# Flask/geopol_data/config.py
"""
Configuration du module Geopol-Data
Gestion des paramètres via variables d'environnement ou valeurs par défaut
"""

import os
from pathlib import Path
from datetime import timedelta

# ============================================================================
# CHEMINS DE FICHIERS
# ============================================================================

# Dossier racine du projet
BASE_DIR = Path(__file__).parent.parent.parent
FLASK_DIR = BASE_DIR / 'Flask'
STATIC_DIR = BASE_DIR / 'static'
TEMPLATES_DIR = BASE_DIR / 'templates'

# Dossier de données
DATA_DIR = STATIC_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Fichiers GeoJSON
GEOJSON_FILE = DATA_DIR / 'countries.geojson'
SIMPLIFIED_GEOJSON_FILE = DATA_DIR / 'countries_simplified.geojson'

# ============================================================================
# CONFIGURATION CACHE
# ============================================================================

class CacheConfig:
    """Configuration du cache en mémoire"""
    
    # Durée de validité du cache (en heures)
    TTL_HOURS = int(os.getenv('GEOPOL_CACHE_TTL_HOURS', 24))
    
    # Durée en timedelta
    TTL = timedelta(hours=TTL_HOURS)
    
    # Taille maximale du cache (nombre de pays)
    MAX_SIZE = int(os.getenv('GEOPOL_CACHE_MAX_SIZE', 200))
    
    # Activer/désactiver le cache
    ENABLED = os.getenv('GEOPOL_CACHE_ENABLED', 'true').lower() == 'true'

# ============================================================================
# CONFIGURATION APIs
# ============================================================================

class WorldBankConfig:
    """Configuration World Bank API"""
    
    # URL de base
    BASE_URL = os.getenv(
        'WORLD_BANK_BASE_URL',
        'https://api.worldbank.org/v2'
    )
    
    # Timeout requêtes (en secondes)
    TIMEOUT = int(os.getenv('WORLD_BANK_TIMEOUT', 15))
    
    # Nombre de tentatives (retry)
    MAX_RETRIES = int(os.getenv('WORLD_BANK_MAX_RETRIES', 3))
    
    # Format de réponse
    FORMAT = 'json'
    
    # Paramètres par défaut
    DEFAULT_PARAMS = {
        'format': FORMAT,
        'per_page': 500,  # Maximum d'enregistrements par requête
        # Supprimé 'date': 'MRV:1' - non supporté par tous les endpoints
    }

class OpenMeteoConfig:
    """Configuration Open-Meteo API (Phase 3)"""
    
    # URL de base
    BASE_URL = os.getenv(
        'OPEN_METEO_BASE_URL',
        'https://air-quality-api.open-meteo.com/v1'
    )
    
    # Timeout requêtes
    TIMEOUT = int(os.getenv('OPEN_METEO_TIMEOUT', 10))
    
    # Paramètres par défaut pour qualité de l'air
    DEFAULT_PARAMS = {
        'hourly': 'pm2_5',
        'forecast_days': 1,
    }

class NaturalEarthConfig:
    """Configuration Natural Earth Data"""
    
    # URL du GeoJSON
    URL = os.getenv(
        'NATURAL_EARTH_URL',
        'https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.geojson'
    )
    
    # Niveau de simplification (plus élevé = moins de détails)
    # 0.01 = simplification légère, 0.1 = simplification agressive
    SIMPLIFICATION_TOLERANCE = float(os.getenv('GEOJSON_SIMPLIFICATION', 0.01))
    
    # Activer la simplification
    SIMPLIFY = os.getenv('GEOJSON_SIMPLIFY', 'true').lower() == 'true'

# ============================================================================
# CONFIGURATION LOGGING
# ============================================================================

class LoggingConfig:
    """Configuration des logs"""
    
    # Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LEVEL = os.getenv('GEOPOL_LOG_LEVEL', 'INFO')
    
    # Format des logs
    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Fichier de log (optionnel)
    FILE = os.getenv('GEOPOL_LOG_FILE', None)
    
    # Activer les logs console
    CONSOLE = os.getenv('GEOPOL_LOG_CONSOLE', 'true').lower() == 'true'

# ============================================================================
# CONFIGURATION INDICATEURS
# ============================================================================

class IndicatorsConfig:
    """Configuration des indicateurs géopolitiques"""
    
    # Indicateurs à récupérer par défaut
    # (voir constants.py pour la liste complète)
    DEFAULT_INDICATORS = os.getenv(
        'GEOPOL_DEFAULT_INDICATORS',
        'NY.GDP.MKTP.CD,NY.GDP.PCAP.CD,SP.POP.TOTL,MS.MIL.XPND.GD.ZS,SL.UEM.TOTL.ZS,EN.ATM.PM25.MC.M3'
    ).split(',')
    
    # Nombre minimum d'indicateurs requis pour valider un pays
    MIN_INDICATORS = int(os.getenv('GEOPOL_MIN_INDICATORS', 3))

# ============================================================================
# CONFIGURATION GÉNÉRALE
# ============================================================================

class Config:
    """Configuration globale du module"""
    
    # Mode debug
    DEBUG = os.getenv('GEOPOL_DEBUG', 'false').lower() == 'true'
    
    # Mode développement
    DEVELOPMENT = os.getenv('FLASK_ENV', 'production') == 'development'
    
    # Sous-configurations
    cache = CacheConfig
    world_bank = WorldBankConfig
    open_meteo = OpenMeteoConfig
    natural_earth = NaturalEarthConfig
    logging = LoggingConfig
    indicators = IndicatorsConfig
    
    @classmethod
    def print_config(cls):
        """Affiche la configuration actuelle (pour debug)"""
        print("=" * 70)
        print("CONFIGURATION GEOPOL-DATA")
        print("=" * 70)
        print(f"Mode Debug: {cls.DEBUG}")
        print(f"Mode Développement: {cls.DEVELOPMENT}")
        print(f"\nCache:")
        print(f"  - Activé: {cls.cache.ENABLED}")
        print(f"  - TTL: {cls.cache.TTL_HOURS}h")
        print(f"  - Taille max: {cls.cache.MAX_SIZE} pays")
        print(f"\nWorld Bank API:")
        print(f"  - URL: {cls.world_bank.BASE_URL}")
        print(f"  - Timeout: {cls.world_bank.TIMEOUT}s")
        print(f"  - Retries: {cls.world_bank.MAX_RETRIES}")
        print(f"\nIndicateurs par défaut:")
        for indicator in cls.indicators.DEFAULT_INDICATORS:
            print(f"  - {indicator}")
        print(f"\nLogging:")
        print(f"  - Niveau: {cls.logging.LEVEL}")
        print(f"  - Console: {cls.logging.CONSOLE}")
        print(f"  - Fichier: {cls.logging.FILE or 'Désactivé'}")
        print("=" * 70)

# ============================================================================
# VALIDATION DE LA CONFIGURATION
# ============================================================================

def validate_config():
    """Valide la configuration au démarrage"""
    errors = []
    
    # Vérifier que le dossier data existe
    if not DATA_DIR.exists():
        errors.append(f"Dossier data manquant: {DATA_DIR}")
    
    # Vérifier les valeurs de configuration
    if CacheConfig.TTL_HOURS < 1:
        errors.append("Cache TTL doit être >= 1 heure")
    
    if CacheConfig.MAX_SIZE < 10:
        errors.append("Cache MAX_SIZE doit être >= 10")
    
    if WorldBankConfig.TIMEOUT < 5:
        errors.append("World Bank timeout doit être >= 5 secondes")
    
    # Afficher les erreurs
    if errors:
        print("⚠️ ERREURS DE CONFIGURATION:")
        for error in errors:
            print(f"  - {error}")
        raise ValueError("Configuration invalide")
    
    return True

# ============================================================================
# INITIALISATION
# ============================================================================

# Valider la config au chargement du module
if __name__ != '__main__':
    try:
        validate_config()
    except ValueError as e:
        print(f"❌ Erreur configuration: {e}")