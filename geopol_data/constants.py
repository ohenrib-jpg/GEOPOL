# Flask/geopol_data/constants.py
"""
Constantes du module Geopol-Data
Codes pays, coordonnées GPS, indicateurs World Bank
"""

# ============================================================================
# COORDONNÉES GPS DES CAPITALES (pour Open-Meteo Phase 3)
# ============================================================================
# Format : 'ISO_A2': (latitude, longitude)

CAPITALS_GPS = {
    # Europe
    'FR': (48.8566, 2.3522),      # Paris
    'DE': (52.5200, 13.4050),     # Berlin
    'GB': (51.5074, -0.1278),     # Londres
    'IT': (41.9028, 12.4964),     # Rome
    'ES': (40.4168, -3.7038),     # Madrid
    'PL': (52.2297, 21.0122),     # Varsovie
    'NL': (52.3676, 4.9041),      # Amsterdam
    'BE': (50.8503, 4.3517),      # Bruxelles
    'SE': (59.3293, 18.0686),     # Stockholm
    'AT': (48.2082, 16.3738),     # Vienne
    
    # Amériques
    'US': (38.9072, -77.0369),    # Washington D.C.
    'CA': (45.4215, -75.6972),    # Ottawa
    'MX': (19.4326, -99.1332),    # Mexico
    'BR': (-15.8267, -47.9218),   # Brasilia
    'AR': (-34.6037, -58.3816),   # Buenos Aires
    'CL': (-33.4489, -70.6693),   # Santiago
    'CO': (4.7110, -74.0721),     # Bogotá
    
    # Asie
    'CN': (39.9042, 116.4074),    # Pékin
    'JP': (35.6762, 139.6503),    # Tokyo
    'IN': (28.6139, 77.2090),     # New Delhi
    'KR': (37.5665, 126.9780),    # Séoul
    'ID': (-6.2088, 106.8456),    # Jakarta
    'PK': (33.6844, 73.0479),     # Islamabad
    'BD': (23.8103, 90.4125),     # Dhaka
    'VN': (21.0285, 105.8542),    # Hanoï
    'TH': (13.7563, 100.5018),    # Bangkok
    'MY': (3.1390, 101.6869),     # Kuala Lumpur
    'PH': (14.5995, 120.9842),    # Manille
    'SA': (24.7136, 46.6753),     # Riyad
    'AE': (24.4539, 54.3773),     # Abu Dhabi
    'IL': (31.7683, 35.2137),     # Jérusalem
    'TR': (39.9334, 32.8597),     # Ankara
    'IR': (35.6892, 51.3890),     # Téhéran
    
    # Afrique
    'EG': (30.0444, 31.2357),     # Le Caire
    'ZA': (-25.7479, 28.2293),    # Pretoria
    'NG': (9.0765, 7.3986),       # Abuja
    'KE': (-1.2921, 36.8219),     # Nairobi
    'ET': (9.0320, 38.7469),      # Addis-Abeba
    'DZ': (36.7538, 3.0588),      # Alger
    'MA': (34.0209, -6.8416),     # Rabat
    'TN': (36.8065, 10.1815),     # Tunis
    'GH': (5.6037, -0.1870),      # Accra
    
    # Océanie
    'AU': (-35.2809, 149.1300),   # Canberra
    'NZ': (-41.2865, 174.7762),   # Wellington
    
    # Europe de l'Est & Russie
    'RU': (55.7558, 37.6173),     # Moscou
    'UA': (50.4501, 30.5234),     # Kiev
    'BY': (53.9045, 27.5615),     # Minsk
    'KZ': (51.1694, 71.4491),     # Astana
    
    # Moyen-Orient
    'IQ': (33.3128, 44.3615),     # Bagdad
    'SY': (33.5138, 36.2765),     # Damas
    'LB': (33.8886, 35.4955),     # Beyrouth
    'JO': (31.9454, 35.9284),     # Amman
    'YE': (15.5527, 48.5164),     # Sanaa
    
    # Amérique latine
    'PE': (-12.0464, -77.0428),   # Lima
    'VE': (10.4806, -66.9036),    # Caracas
    'EC': (-0.1807, -78.4678),    # Quito
    'BO': (-16.5000, -68.1500),   # La Paz
}

# ============================================================================
# INDICATEURS WORLD BANK
# ============================================================================
# Documentation complète : https://data.worldbank.org/indicator

WORLD_BANK_INDICATORS = {
    # Économie
    'gdp': 'NY.GDP.MKTP.CD',              # PIB (USD courants)
    'gdp_per_capita': 'NY.GDP.PCAP.CD',   # PIB par habitant
    'gdp_growth': 'NY.GDP.MKTP.KD.ZG',    # Croissance PIB (%)
    'inflation': 'FP.CPI.TOTL.ZG',        # Inflation (%)
    'debt': 'GC.DOD.TOTL.GD.ZS',          # Dette publique (% PIB)
    
    # Démographie
    'population': 'SP.POP.TOTL',          # Population totale
    'urban_population': 'SP.URB.TOTL.IN.ZS',  # Urbanisation (%)
    'fertility': 'SP.DYN.TFRT.IN',        # Taux de fertilité
    'life_expectancy': 'SP.DYN.LE00.IN',  # Espérance de vie
    
    # Travail
    'unemployment': 'SL.UEM.TOTL.ZS',     # Chômage (%)
    'labor_force': 'SL.TLF.TOTL.IN',      # Force de travail
    
    # Militaire & Sécurité
    'military_spending': 'MS.MIL.XPND.GD.ZS',  # Dépenses militaires (% PIB)
    'military_spending_usd': 'MS.MIL.XPND.CD', # Dépenses militaires (USD)
    
    # Environnement
    'pm25': 'EN.ATM.PM25.MC.M3',          # PM2.5 moyen (µg/m³)
    'co2': 'EN.ATM.CO2E.PC',              # Émissions CO2 (tonnes/hab)
    'forest': 'AG.LND.FRST.ZS',           # Forêts (% territoire)
    'renewable_energy': 'EG.FEC.RNEW.ZS', # Énergies renouvelables (%)
    
    # Énergie
    'energy_imports': 'EG.IMP.CONS.ZS',   # Imports énergétiques (% conso)
    'electricity_access': 'EG.ELC.ACCS.ZS',  # Accès électricité (%)
    
    # Éducation & Développement
    'school_enrollment': 'SE.SEC.ENRR',   # Scolarisation secondaire (%)
    'internet_users': 'IT.NET.USER.ZS',   # Utilisateurs internet (%)
}

# ============================================================================
# INDICATEURS CORE (PHASE 1)
# ============================================================================
# Les 6 indicateurs prioritaires pour démarrer

CORE_INDICATORS = [
    'NY.GDP.MKTP.CD',        # PIB
    'NY.GDP.PCAP.CD',        # PIB/habitant
    'SP.POP.TOTL',           # Population
    'MS.MIL.XPND.GD.ZS',     # Dépenses militaires (% PIB)
    'SL.UEM.TOTL.ZS',        # Chômage
    'EN.ATM.PM25.MC.M3',     # Pollution PM2.5
]

# ============================================================================
# CODES PAYS ISO (les plus importants géopolitiquement)
# ============================================================================

PRIORITY_COUNTRIES = [
    # G7
    'US', 'CA', 'GB', 'FR', 'DE', 'IT', 'JP',
    
    # BRICS+
    'BR', 'RU', 'IN', 'CN', 'ZA', 
    'SA', 'IR', 'EG', 'ET', 'AE',
    
    # Europe stratégique
    'ES', 'PL', 'NL', 'BE', 'SE', 'AT', 'UA',
    
    # Asie-Pacifique
    'KR', 'ID', 'PK', 'BD', 'VN', 'TH', 'MY', 'PH', 'AU',
    
    # Moyen-Orient
    'TR', 'IL', 'IQ', 'SY', 'LB', 'JO', 'YE',
    
    # Afrique
    'NG', 'KE', 'DZ', 'MA', 'TN', 'GH',
    
    # Amérique latine
    'MX', 'AR', 'CL', 'CO', 'PE', 'VE', 'EC', 'BO',
]

# ============================================================================
# CONFIGURATION CACHE
# ============================================================================

CACHE_TTL_HOURS = 24  # Durée validité cache World Bank (données changent peu)
API_TIMEOUT_SECONDS = 15  # Timeout requêtes HTTP

# ============================================================================
# URLS DES APIs
# ============================================================================

WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2"
OPEN_METEO_BASE_URL = "https://air-quality-api.open-meteo.com/v1"
NATURAL_EARTH_URL = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.geojson"

# ============================================================================
# MAPPING NOMS DE PAYS
# ============================================================================
# Pour gérer les différences de noms entre World Bank et Natural Earth

COUNTRY_NAME_MAPPING = {
    'United States': 'United States of America',
    'Russia': 'Russian Federation',
    'South Korea': 'Republic of Korea',
    'North Korea': "Democratic People's Republic of Korea",
    'UK': 'United Kingdom',
    'Czech Republic': 'Czechia',
}
