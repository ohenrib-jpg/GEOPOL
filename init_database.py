#!/usr/bin/env python3
# init_database.py - Initialisation complète de la base de données

import sqlite3
import os
import json
from datetime import datetime

def init_database():
    """Initialise ou réinitialise la base de données"""
    
    # Créer le dossier instance s'il n'existe pas
    instance_dir = 'instance'
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"✅ Dossier '{instance_dir}' créé")
    
    db_path = os.path.join(instance_dir, 'geopol.db')
    
    print("🔧 INITIALISATION DE LA BASE DE DONNÉES")
    print("=" * 70)
    print(f"📁 Chemin: {db_path}")
    
    # Vérifier si la base existe
    db_exists = os.path.exists(db_path)
    if db_exists:
        print(f"⚠️  Base de données existante trouvée")
        response = input("Voulez-vous la réinitialiser ? (O/n): ").strip().lower()
        if response not in ['o', 'oui', 'y', 'yes', '']:
            print("❌ Opération annulée")
            return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("\n1️⃣ Création de la table articles...")
        cursor.execute("""
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
                analyzed_at TIMESTAMP,
                harmonized INTEGER DEFAULT 0,
                cluster_size INTEGER DEFAULT 1,
                analysis_metadata TEXT
            )
        """)
        print("   ✅ Table articles créée")
        
        print("\n2️⃣ Création de la table themes...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS themes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                keywords TEXT NOT NULL,
                color TEXT DEFAULT '#6366f1',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ Table themes créée")
        
        print("\n3️⃣ Création de la table theme_analyses...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS theme_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                theme_id TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles (id),
                FOREIGN KEY (theme_id) REFERENCES themes (id)
            )
        """)
        print("   ✅ Table theme_analyses créée")
        
        print("\n4️⃣ Création des index...")
        
        # Index pour articles
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(pub_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_sentiment ON articles(sentiment_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_detailed_sentiment ON articles(detailed_sentiment)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_analysis_model ON articles(analysis_model)")
        print("   ✅ Index articles créés")
        
        # Index pour theme_analyses
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_theme_analyses_confidence ON theme_analyses(confidence)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_theme_analyses_article ON theme_analyses(article_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_theme_analyses_theme ON theme_analyses(theme_id)")
        print("   ✅ Index theme_analyses créés")
        
        print("\n5️⃣ Création de thèmes par défaut...")
        
        default_themes = [
            {
                'id': 'geopolitique',
                'name': 'Géopolitique',
                'keywords': json.dumps(['guerre', 'conflit', 'diplomatie', 'sanctions', 'alliance', 'tension'], ensure_ascii=False),
                'color': '#FF6B6B',
                'description': 'Événements et analyses géopolitiques internationaux'
            },
            {
                'id': 'economie',
                'name': 'Économie',
                'keywords': json.dumps(['économie', 'croissance', 'inflation', 'marché', 'bourse', 'finance'], ensure_ascii=False),
                'color': '#4ECDC4',
                'description': 'Actualités économiques et financières'
            },
            {
                'id': 'technologie',
                'name': 'Technologie',
                'keywords': json.dumps(['technologie', 'innovation', 'numérique', 'intelligence artificielle', 'cybersécurité'], ensure_ascii=False),
                'color': '#45B7D1',
                'description': 'Technologies et innovations'
            },
            {
                'id': 'environnement',
                'name': 'Environnement',
                'keywords': json.dumps(['climat', 'environnement', 'écologie', 'pollution', 'biodiversité', 'énergie'], ensure_ascii=False),
                'color': '#96CEB4',
                'description': 'Environnement et changement climatique'
            },
            {
                'id': 'societe',
                'name': 'Société',
                'keywords': json.dumps(['société', 'social', 'culture', 'éducation', 'santé'], ensure_ascii=False),
                'color': '#FFEAA7',
                'description': 'Questions de société et culture'
            },
            {
                'id': 'politique_france',
                'name': 'Politique France',
                'keywords': json.dumps(['france', 'paris', 'gouvernement', 'assemblée', 'élection', 'réforme'], ensure_ascii=False),
                'color': '#6C5CE7',
                'description': 'Politique française'
            },
            {
                'id': 'international',
                'name': 'International',
                'keywords': json.dumps(['international', 'mondial', 'onu', 'union européenne', 'otan'], ensure_ascii=False),
                'color': '#A29BFE',
                'description': 'Relations internationales'
            },
            {
                'id': 'defense',
                'name': 'Défense & Sécurité',
                'keywords': json.dumps(['défense', 'armée', 'militaire', 'sécurité', 'terrorisme'], ensure_ascii=False),
                'color': '#FD79A8',
                'description': 'Défense nationale et sécurité'
            },
            {
                'id': 'energie',
                'name': 'Énergie',
                'keywords': json.dumps(['énergie', 'pétrole', 'gaz', 'nucléaire', 'renouvelable', 'électricité'], ensure_ascii=False),
                'color': '#FDCB6E',
                'description': 'Énergie et ressources'
            }
        ]
        
        for theme in default_themes:
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO themes (id, name, keywords, color, description)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    theme['id'],
                    theme['name'],
                    theme['keywords'],
                    theme['color'],
                    theme['description']
                ))
                print(f"   ✅ Thème créé: {theme['name']}")
            except Exception as e:
                print(f"   ⚠️  Erreur création {theme['id']}: {e}")
        
        print("\n6️⃣ Création des tables avancées...")
        
        # Tables pour corroboration
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS article_corroborations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                similar_article_id INTEGER,
                similarity_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles (id),
                FOREIGN KEY (similar_article_id) REFERENCES articles (id)
            )
        """)
        print("   ✅ Table article_corroborations créée")
        
        # Tables pour thèmes avancés
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS theme_keywords_weighted (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                category TEXT DEFAULT 'primary',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE,
                UNIQUE(theme_id, keyword)
            )
        """)
        print("   ✅ Table theme_keywords_weighted créée")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS theme_synonyms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme_id TEXT NOT NULL,
                original_word TEXT NOT NULL,
                synonym TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE
            )
        """)
        print("   ✅ Table theme_synonyms créée")
        
        conn.commit()
        
        print("\n7️⃣ Vérification finale...")
        
        # Vérifier les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"   Tables créées: {len(tables)}")
        for table in sorted(tables):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"      - {table}: {count} enregistrement(s)")
        
        print("\n8️⃣ Test d'insertion de thème...")
        test_theme = {
            'id': 'test_init',
            'name': 'Test Initialisation',
            'keywords': json.dumps(['test', 'init', 'validation']),
            'color': '#00FF00',
            'description': 'Thème de test'
        }
        
        cursor.execute("""
            INSERT INTO themes (id, name, keywords, color, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            test_theme['id'],
            test_theme['name'],
            test_theme['keywords'],
            test_theme['color'],
            test_theme['description']
        ))
        conn.commit()
        print("   ✅ Insertion test réussie")
        
        # Vérifier
        cursor.execute("SELECT * FROM themes WHERE id = ?", (test_theme['id'],))
        result = cursor.fetchone()
        if result:
            print(f"   ✅ Thème test récupéré: {result[1]}")
            keywords = json.loads(result[2])
            print(f"   ✅ Keywords parsés: {keywords}")
        
        # Supprimer le test
        cursor.execute("DELETE FROM themes WHERE id = ?", (test_theme['id'],))
        conn.commit()
        print("   ✅ Thème test nettoyé")
        
        print("\n" + "=" * 70)
        print("✅ Base de données initialisée avec succès !")
        print(f"📊 {len(default_themes)} thèmes par défaut créés")
        print("\n💡 Vous pouvez maintenant:")
        print("   1. Démarrer le serveur Flask")
        print("   2. Accéder à l'interface web")
        print("   3. Créer, modifier et supprimer des thèmes")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Script d'initialisation de la base de données GEOPOL\n")
    
    if init_database():
        print("\n✅ Tout est prêt !")
    else:
        print("\n❌ L'initialisation a échoué.")
