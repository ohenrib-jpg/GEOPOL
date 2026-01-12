# Flask/archiviste_db_fix.py
"""
Script de correction de la base de données pour Archiviste
Résout les problèmes de structure de tables et de colonnes manquantes
"""

import sqlite3
import logging
import json
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Thèmes par défaut pour Archiviste
DEFAULT_THEMES = [
    {
        'name': 'Géopolitique',
        'keywords': ['politique', 'international', 'diplomatie', 'relations', 'état', 'gouvernement', 'ambassade', 'traité'],
        'color': '#3B82F6',
        'description': 'Relations internationales et diplomatie',
        'category': 'politique'
    },
    {
        'name': 'Conflits',
        'keywords': ['guerre', 'conflit', 'tensions', 'armée', 'militaire', 'bataille', 'paix', 'négociations'],
        'color': '#EF4444',
        'description': 'Conflits armés et tensions militaires',
        'category': 'conflits'
    },
    {
        'name': 'Économie',
        'keywords': ['économie', 'commerce', 'finance', 'banque', 'marché', 'investissement', 'croissance', 'crise'],
        'color': '#10B981',
        'description': 'Économie mondiale et commerce international',
        'category': 'économie'
    },
    {
        'name': 'Technologie',
        'keywords': ['technologie', 'innovation', 'science', 'recherche', 'découverte', 'invention', 'digital', 'ia'],
        'color': '#8B5CF6',
        'description': 'Innovations technologiques et scientifiques',
        'category': 'technologie'
    },
    {
        'name': 'Culture',
        'keywords': ['culture', 'art', 'littérature', 'musique', 'cinéma', 'théâtre', 'éducation', 'tradition'],
        'color': '#F59E0B',
        'description': 'Culture, arts et éducation',
        'category': 'culture'
    }
]

def fix_archiviste_database(db_path: str = "rss_analyzer.db"):
    """Corrige la structure de la base de données pour Archiviste"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("[TOOL] Début de la correction de la structure Archiviste...")
        
        # === ÉTAPE 1: Vérifier la structure actuelle ===
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tables existantes: {existing_tables}")
        
        # === ÉTAPE 2: Créer les tables de base si nécessaire ===
        print("[MIGRATION] Création des tables de base...")
        _create_basic_tables(cursor, existing_tables)
        
        # === ÉTAPE 3: Corriger la table 'themes' ===
        if 'themes' in existing_tables:
            print("[MIGRATION] Correction de la table 'themes'...")
            _fix_themes_table(cursor)
        else:
            print("[NOTE] Création de la table 'themes'...")
            _create_themes_table(cursor)
        
        # === ÉTAPE 4: Créer les tables Archiviste spécifiques ===
        print("[MIGRATION] Création des tables Archiviste...")
        _create_archiviste_tables(cursor)
        
        # === ÉTAPE 5: Peupler les thèmes par défaut si nécessaire ===
        cursor.execute("SELECT COUNT(*) FROM themes")
        theme_count = cursor.fetchone()[0]
        
        if theme_count == 0:
            print("[MIGRATION] Ajout des thèmes par défaut...")
            _populate_default_themes(cursor)
        
        conn.commit()
        
        # === ÉTAPE 6: Vérification finale ===
        _verify_fix(cursor)
        
        print("[OK] Correction Archiviste terminée avec succès!")
        
    except Exception as e:
        print(f"[ERROR] Erreur lors de la correction: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def _create_basic_tables(cursor, existing_tables):
    """Crée les tables de base si elles n'existent pas"""
    
    basic_tables = {
        'themes': """
            CREATE TABLE IF NOT EXISTS themes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                keywords TEXT,
                color TEXT DEFAULT '#6366f1',
                description TEXT,
                active INTEGER DEFAULT 1,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'articles': """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                link TEXT UNIQUE,
                pub_date TIMESTAMP,
                sentiment_type TEXT,
                sentiment_score REAL,
                detailed_sentiment TEXT,
                roberta_score REAL,
                analysis_model TEXT,
                feed_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sentiment_confidence REAL DEFAULT 0.5,
                bayesian_confidence REAL,
                bayesian_evidence_count INTEGER DEFAULT 0,
                analyzed_at TIMESTAMP
            )
        """
    }
    
    for table_name, create_sql in basic_tables.items():
        if table_name not in existing_tables:
            print(f"   ➕ Création table '{table_name}'")
            cursor.execute(create_sql)

def _create_themes_table(cursor):
    """Crée la table themes avec la structure complète"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS themes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            keywords TEXT,
            color TEXT DEFAULT '#6366f1',
            description TEXT,
            active INTEGER DEFAULT 1,
            category TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   [OK] Table 'themes' créée")

def _fix_themes_table(cursor):
    """Corrige la structure de la table themes"""
    
    # Vérifier les colonnes existantes
    cursor.execute("PRAGMA table_info(themes)")
    theme_columns = {col[1]: col for col in cursor.fetchall()}
    print(f"   Colonnes actuelles: {list(theme_columns.keys())}")
    
    # Ajouter la colonne 'active' si manquante
    if 'active' not in theme_columns:
        print("   ➕ Ajout de la colonne 'active'")
        cursor.execute("ALTER TABLE themes ADD COLUMN active INTEGER DEFAULT 1")
    
    # Ajouter la colonne 'category' si manquante
    if 'category' not in theme_columns:
        print("   ➕ Ajout de la colonne 'category'")
        cursor.execute("ALTER TABLE themes ADD COLUMN category TEXT DEFAULT 'general'")
    
    # Vérifier si on a besoin de normaliser les IDs
    cursor.execute("SELECT id FROM themes LIMIT 1")
    sample_id = cursor.fetchone()
    
    if sample_id:
        id_value = sample_id[0]
        # Si l'ID n'est pas numérique, normaliser
        if isinstance(id_value, str) and not id_value.isdigit():
            print("   [MIGRATION] Conversion des IDs texte vers numérique...")
            _normalize_theme_ids(cursor)

def _normalize_theme_ids(cursor):
    """Normalise les IDs de thèmes pour qu'ils soient numériques"""
    try:
        # Créer une table temporaire avec IDs numériques
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS themes_temp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                keywords TEXT,
                color TEXT DEFAULT '#6366f1',
                description TEXT,
                active INTEGER DEFAULT 1,
                category TEXT DEFAULT 'general',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Copier les données depuis l'ancienne table
        cursor.execute("""
            SELECT name, keywords, color, description, active, category, created_at
            FROM themes
            ORDER BY name
        """)
        
        themes_data = cursor.fetchall()
        
        for i, theme in enumerate(themes_data, 1):
            cursor.execute("""
                INSERT INTO themes_temp 
                (id, name, keywords, color, description, active, category, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (i, theme[0], theme[1], theme[2], theme[3], 
                  theme[4] if len(theme) > 4 else 1, 
                  theme[5] if len(theme) > 5 else 'general', 
                  theme[6] if len(theme) > 6 else None))
        
        # Remplacer l'ancienne table
        cursor.execute("DROP TABLE themes")
        cursor.execute("ALTER TABLE themes_temp RENAME TO themes")
        
        print(f"   [OK] {len(themes_data)} thèmes normalisés avec IDs numériques")
        
    except Exception as e:
        print(f"   [WARN] Erreur normalisation IDs: {e}")
        # Annuler les changements de cette étape
        cursor.execute("DROP TABLE IF EXISTS themes_temp")
        raise

def _create_archiviste_tables(cursor):
    """Crée les tables spécifiques à Archiviste"""
    
    archiviste_tables = {
        'archiviste_items': """
            CREATE TABLE IF NOT EXISTS archiviste_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identifier TEXT UNIQUE NOT NULL,
                title TEXT,
                date TEXT,
                year INTEGER,
                collection TEXT,
                description TEXT,
                language TEXT,
                creator TEXT,
                publisher TEXT,
                subject TEXT,
                mediatype TEXT,
                downloads INTEGER DEFAULT 0,
                full_text TEXT,
                text_quality_score INTEGER DEFAULT 0,
                geopolitical_relevance_score INTEGER DEFAULT 0,
                themes_detected TEXT,
                sentiment_score REAL DEFAULT 0.0,
                entities_extracted TEXT,
                fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_analyzed_at DATETIME,
                analysis_version INTEGER DEFAULT 1
            )
        """,
        
        'archiviste_period_analyses': """
            CREATE TABLE IF NOT EXISTS archiviste_period_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period_key TEXT NOT NULL,
                period_name TEXT,
                theme_id INTEGER,
                total_items INTEGER DEFAULT 0,
                items_analyzed INTEGER DEFAULT 0,
                sentiment_evolution TEXT,
                theme_evolution TEXT,
                dominant_narratives TEXT,
                geopolitical_shifts TEXT,
                key_events TEXT,
                confidence_score REAL DEFAULT 0.0,
                analysis_summary TEXT,
                raw_data TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'archiviste_theme_mappings': """
            CREATE TABLE IF NOT EXISTS archiviste_theme_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_identifier TEXT NOT NULL,
                theme_id INTEGER NOT NULL,
                theme_name TEXT NOT NULL,
                relevance_score REAL DEFAULT 0.0,
                confidence REAL DEFAULT 0.0,
                matched_keywords TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_identifier) REFERENCES archiviste_items(identifier)
            )
        """
    }
    
    for table_name, create_sql in archiviste_tables.items():
        try:
            cursor.execute(create_sql)
            print(f"   [OK] Table '{table_name}' créée/vérifiée")
        except Exception as e:
            print(f"   [WARN] Erreur création table {table_name}: {e}")
    
    # Créer les index
    archiviste_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_archiviste_items_year ON archiviste_items(year)",
        "CREATE INDEX IF NOT EXISTS idx_archiviste_items_theme ON archiviste_items(themes_detected)",
        "CREATE INDEX IF NOT EXISTS idx_archiviste_mappings_theme ON archiviste_theme_mappings(theme_id)",
        "CREATE INDEX IF NOT EXISTS idx_archiviste_period_key ON archiviste_period_analyses(period_key)",
        "CREATE INDEX IF NOT EXISTS idx_archiviste_mappings_item ON archiviste_theme_mappings(item_identifier)"
    ]
    
    for index_sql in archiviste_indexes:
        try:
            cursor.execute(index_sql)
        except Exception as e:
            print(f"   [WARN] Erreur création index: {e}")

def _populate_default_themes(cursor):
    """Ajoute les thèmes par défaut pour Archiviste"""
    
    for i, theme_data in enumerate(DEFAULT_THEMES, 1):
        cursor.execute("""
            INSERT INTO themes (id, name, keywords, color, description, category, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            i,  # ID numérique
            theme_data['name'],
            json.dumps(theme_data['keywords'], ensure_ascii=False),
            theme_data['color'],
            theme_data['description'],
            theme_data['category'],
            1  # active
        ))
    
    print(f"   [OK] {len(DEFAULT_THEMES)} thèmes par défaut ajoutés")

def _verify_fix(cursor):
    """Vérifie que la correction a fonctionné"""
    print("\n[SEARCH] Vérification de la correction...")
    
    # Vérifier les tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    required_tables = ['themes', 'archiviste_items', 'archiviste_theme_mappings']
    for table in required_tables:
        if table in tables:
            print(f"   [OK] Table '{table}' présente")
        else:
            print(f"   [ERROR] Table '{table}' MANQUANTE")
    
    # Vérifier les thèmes
    cursor.execute("SELECT COUNT(*) FROM themes")
    theme_count = cursor.fetchone()[0]
    print(f"   [DATA] Thèmes dans la base: {theme_count}")
    
    # Vérifier la structure des thèmes
    cursor.execute("PRAGMA table_info(themes)")
    theme_columns = [col[1] for col in cursor.fetchall()]
    required_columns = ['id', 'name', 'keywords', 'active']
    
    for col in required_columns:
        if col in theme_columns:
            print(f"   [OK] Colonne '{col}' présente dans themes")
        else:
            print(f"   [ERROR] Colonne '{col}' MANQUANTE dans themes")
    
    # Vérifier les IDs numériques
    cursor.execute("SELECT id FROM themes LIMIT 5")
    sample_ids = [row[0] for row in cursor.fetchall()]
    all_numeric = all(isinstance(id_val, int) or (isinstance(id_val, str) and str(id_val).isdigit()) for id_val in sample_ids)
    
    if all_numeric:
        print("   [OK] IDs de thèmes numériques")
    else:
        print("   [WARN] IDs de thèmes non-numériques détectés")

def get_database_status(db_path: str = "rss_analyzer.db") -> Dict[str, Any]:
    """Retourne le statut de la base de données Archiviste"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        status = {
            'themes_table': False,
            'archiviste_tables': {},
            'theme_count': 0,
            'item_count': 0,
            'issues': []
        }
        
        # Vérifier la table themes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='themes'")
        status['themes_table'] = bool(cursor.fetchone())
        
        # Compter les thèmes
        if status['themes_table']:
            cursor.execute("SELECT COUNT(*) FROM themes")
            status['theme_count'] = cursor.fetchone()[0]
        
        # Vérifier les tables Archiviste
        archiviste_tables = ['archiviste_items', 'archiviste_theme_mappings', 'archiviste_period_analyses']
        for table in archiviste_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            status['archiviste_tables'][table] = bool(cursor.fetchone())
            
            if status['archiviste_tables'][table]:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count_result = cursor.fetchone()
                status[f'{table}_count'] = count_result[0] if count_result else 0
        
        # Vérifier les colonnes de themes
        if status['themes_table']:
            cursor.execute("PRAGMA table_info(themes)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'active' not in columns:
                status['issues'].append("Colonne 'active' manquante dans themes")
            
            # Vérifier les IDs
            cursor.execute("SELECT id FROM themes LIMIT 1")
            sample = cursor.fetchone()
            if sample and not isinstance(sample[0], int) and not (isinstance(sample[0], str) and sample[0].isdigit()):
                status['issues'].append("IDs de thèmes non-numériques détectés")
        
        return status
        
    finally:
        conn.close()

# Utilisation simple
if __name__ == "__main__":
    print("[TOOL] Correcteur de base de données Archiviste")
    print("=" * 50)
    
    try:
        # Afficher le statut avant
        print("[DATA] Statut avant correction:")
        status_before = get_database_status()
        print(f"   - Table themes: {'[OK]' if status_before['themes_table'] else '[ERROR]'}")
        print(f"   - Nombre de thèmes: {status_before['theme_count']}")
        
        for table, exists in status_before['archiviste_tables'].items():
            print(f"   - Table {table}: {'[OK]' if exists else '[ERROR]'}")
        
        if status_before['issues']:
            print("   - Problèmes détectés:")
            for issue in status_before['issues']:
                print(f"     • {issue}")
        
        # Exécuter la correction
        print("\n[MIGRATION] Exécution de la correction...")
        fix_archiviste_database()
        
        # Afficher le statut après
        print("\n[DATA] Statut après correction:")
        status_after = get_database_status()
        print(f"   - Table themes: {'[OK]' if status_after['themes_table'] else '[ERROR]'}")
        print(f"   - Nombre de thèmes: {status_after['theme_count']}")
        
        for table, exists in status_after['archiviste_tables'].items():
            print(f"   - Table {table}: {'[OK]' if exists else '[ERROR]'}")
        
        if not status_after['issues']:
            print("   [OK] Aucun problème détecté")
        else:
            print("   - Problèmes restants:")
            for issue in status_after['issues']:
                print(f"     • {issue}")
                
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")