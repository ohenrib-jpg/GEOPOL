# Flask/fix_database.py
import sqlite3
import os

def fix_database():
    """Corrige la base de données en ajoutant les colonnes manquantes"""
    
    # Chemin vers la base de données
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'rss_analyzer.db')
    
    if not os.path.exists(db_path):
        print("❌ Base de données non trouvée")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔧 Correction de la base de données...")
        
        # Vérifier les colonnes existantes
        cursor.execute("PRAGMA table_info(articles)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Colonnes existantes: {existing_columns}")
        
        # Colonnes à ajouter
        required_columns = [
            ('detailed_sentiment', 'TEXT'),
            ('roberta_score', 'REAL'),
            ('analysis_model', 'TEXT'),
            ('sentiment_confidence', 'REAL DEFAULT 0.5'),
            ('bayesian_confidence', 'REAL'),
            ('bayesian_evidence_count', 'INTEGER DEFAULT 0'),
            ('analyzed_at', 'TIMESTAMP')
        ]
        
        # Ajouter les colonnes manquantes
        for column_name, column_type in required_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Colonne ajoutée: {column_name}")
                except Exception as e:
                    print(f"⚠️ Erreur sur {column_name}: {e}")
            else:
                print(f"✅ Colonne déjà présente: {column_name}")
        
        # Mettre à jour les articles existants
        cursor.execute("""
            UPDATE articles 
            SET analysis_model = 'traditional',
                sentiment_confidence = 0.7
            WHERE analysis_model IS NULL
        """)
        print(f"✅ {cursor.rowcount} articles mis à jour")
        
        # Créer les index manquants
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_articles_detailed_sentiment ON articles(detailed_sentiment)",
            "CREATE INDEX IF NOT EXISTS idx_articles_analysis_model ON articles(analysis_model)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"✅ Index créé")
            except Exception as e:
                print(f"⚠️ Erreur index: {e}")
        
        conn.commit()
        print("🎉 Base de données corrigée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database()
