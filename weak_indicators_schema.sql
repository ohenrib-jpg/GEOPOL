-- Flask/weak_indicators_schema.sql
-- Schéma complet pour les indicateurs faibles

-- ============================================
-- TABLES AVIS AUX VOYAGEURS
-- ============================================

CREATE TABLE IF NOT EXISTS travel_advisories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_code TEXT NOT NULL,
    country_name TEXT,
    risk_level INTEGER NOT NULL DEFAULT 1,  -- 1=Normal, 2=Caution, 3=Reconsider, 4=DoNotTravel
    source TEXT NOT NULL,  -- 'us_state_department', 'uk_foreign_office', 'canada_travel'
    summary TEXT,
    details TEXT,  -- JSON avec infos complémentaires
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(country_code, source)
);

CREATE INDEX IF NOT EXISTS idx_travel_country ON travel_advisories(country_code);
CREATE INDEX IF NOT EXISTS idx_travel_risk ON travel_advisories(risk_level);
CREATE INDEX IF NOT EXISTS idx_travel_updated ON travel_advisories(last_updated);

-- Historique des changements de niveau
CREATE TABLE IF NOT EXISTS travel_advisories_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    country_code TEXT NOT NULL,
    source TEXT NOT NULL,
    previous_risk_level INTEGER,
    new_risk_level INTEGER,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(country_code) REFERENCES travel_advisories(country_code)
);

-- ============================================
-- TABLES KIWISDR / SDR
-- ============================================

-- Serveurs KiwiSDR actifs
CREATE TABLE IF NOT EXISTS kiwisdr_servers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    location TEXT,
    users INTEGER DEFAULT 0,
    users_max INTEGER DEFAULT 4,
    status TEXT DEFAULT 'online',  -- 'online', 'offline', 'full'
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table pour stocker les résultats d'analyse détaillés
CREATE TABLE IF NOT EXISTS sdr_spectrum_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    frequency_id INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_peaks INTEGER NOT NULL,
    significant_emissions INTEGER NOT NULL,
    peaks_data TEXT,  -- JSON des pics détectés
    analysis_parameters TEXT,
    server_used TEXT,
    FOREIGN KEY(frequency_id) REFERENCES kiwisdr_monitored_frequencies(id)
);

-- Fréquences surveillées
CREATE TABLE IF NOT EXISTS kiwisdr_monitored_frequencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    frequency_khz INTEGER NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,  -- 'military', 'diplomatic', 'maritime', 'aviation', 'broadcast'
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activité quotidienne par fréquence
CREATE TABLE IF NOT EXISTS kiwisdr_frequency_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    frequency_id INTEGER NOT NULL,
    date DATE NOT NULL,
    emission_count INTEGER DEFAULT 0,
    peak_strength REAL DEFAULT 0.0,
    observation_duration INTEGER DEFAULT 0,  -- en secondes
    notes TEXT,
    observer TEXT DEFAULT 'user',
    FOREIGN KEY(frequency_id) REFERENCES kiwisdr_monitored_frequencies(id),
    UNIQUE(frequency_id, date)
);

CREATE INDEX IF NOT EXISTS idx_freq_activity_date ON kiwisdr_frequency_activity(date);
CREATE INDEX IF NOT EXISTS idx_freq_activity_freq ON kiwisdr_frequency_activity(frequency_id);

-- Historique du nombre de serveurs actifs
CREATE TABLE IF NOT EXISTS kiwisdr_server_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_servers INTEGER NOT NULL,
    online_servers INTEGER NOT NULL,
    full_servers INTEGER NOT NULL,
    snapshot_data TEXT  -- JSON avec détails
);

-- ============================================
-- TABLES DONNÉES MACRO-ÉCONOMIQUES
-- ============================================

-- Cache des données boursières
CREATE TABLE IF NOT EXISTS stock_data_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    name TEXT,
    asset_type TEXT,  -- 'index', 'commodity', 'crypto', 'etf'
    current_price REAL,
    change_percent REAL,
    change_direction TEXT,  -- 'up', 'down', 'stable'
    country TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_json TEXT,  -- JSON avec données complètes
    UNIQUE(symbol)
);

CREATE INDEX IF NOT EXISTS idx_stock_symbol ON stock_data_cache(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_updated ON stock_data_cache(last_updated);

-- Historique des prix (pour graphiques)
CREATE TABLE IF NOT EXISTS stock_price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    close_price REAL,
    volume BIGINT,
    UNIQUE(symbol, date)
);

-- ============================================
-- TABLES FLUX SDR (Générique)
-- ============================================

-- Flux SDR configurés
CREATE TABLE IF NOT EXISTS sdr_streams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT,
    frequency_khz INTEGER DEFAULT 0,
    type TEXT DEFAULT 'rtlsdr',  -- 'rtlsdr', 'websdr', 'kiwisdr', 'manual'
    description TEXT,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Activité quotidienne des flux SDR
CREATE TABLE IF NOT EXISTS sdr_daily_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stream_id INTEGER NOT NULL,
    date DATE NOT NULL,
    activity_count INTEGER DEFAULT 0,
    FOREIGN KEY(stream_id) REFERENCES sdr_streams(id),
    UNIQUE(stream_id, date)
);

-- ============================================
-- TABLES MONITORING AUTOMATIQUE
-- ============================================

-- Sessions de monitoring en cours
CREATE TABLE IF NOT EXISTS weak_indicators_monitoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitoring_id TEXT UNIQUE,
    frequency_khz INTEGER NOT NULL,
    emissions_count INTEGER DEFAULT 0,
    activity_level TEXT,  -- 'none', 'low', 'medium', 'high', 'very_high'
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_data TEXT  -- JSON
);

-- Patterns détectés
CREATE TABLE IF NOT EXISTS weak_indicators_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    frequency_khz INTEGER NOT NULL,
    pattern_type TEXT,
    confidence REAL,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT  -- JSON
);

-- ============================================
-- VUES PRATIQUES
-- ============================================

-- Vue agrégée des avis aux voyageurs par pays
CREATE VIEW IF NOT EXISTS v_travel_advisories_summary AS
SELECT 
    country_code,
    MAX(country_name) as country_name,
    MAX(risk_level) as max_risk_level,
    GROUP_CONCAT(source) as sources,
    MAX(last_updated) as last_updated
FROM travel_advisories
GROUP BY country_code;

-- Vue des fréquences les plus actives
CREATE VIEW IF NOT EXISTS v_top_active_frequencies AS
SELECT 
    f.id,
    f.frequency_khz,
    f.name,
    f.category,
    SUM(a.emission_count) as total_emissions,
    AVG(a.emission_count) as avg_emissions,
    MAX(a.date) as last_activity
FROM kiwisdr_monitored_frequencies f
LEFT JOIN kiwisdr_frequency_activity a ON f.id = a.frequency_id
WHERE f.active = 1
GROUP BY f.id
ORDER BY total_emissions DESC;

-- Vue des stocks avec variations significatives
CREATE VIEW IF NOT EXISTS v_significant_stock_moves AS
SELECT 
    symbol,
    name,
    asset_type,
    current_price,
    change_percent,
    change_direction,
    country
FROM stock_data_cache
WHERE ABS(change_percent) > 2.0  -- Variations > 2%
ORDER BY ABS(change_percent) DESC;
