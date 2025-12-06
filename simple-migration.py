# Flask/simple_migration.py - MIGRATION SIMPLE
import sqlite3
import os

def simple_migration():
    """Migration simple - juste les colonnes manquantes"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'geopolitics.db')
    print(f"🔄 Migration simple: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Liste des colonnes à ajouter
        columns_to_add = [
            "analysis_model TEXT DEFAULT 'traditional'",
            "sentiment_confidence REAL DEFAULT 0.5",
            "roberta_score REAL", 
            "roberta_label TEXT"
        ]
        
        # Ajouter chaque colonne
        for col_def in columns_to_add:
            col_name = col_def.split()[0]
            try:
                cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_def}")
                print(f"✅ {col_name}")
            except Exception as e:
                if "duplicate" in str(e).lower():
                    print(f"✅ {col_name} (déjà présente)")
                else:
                    print(f"⚠️ {col_name}: {e}")
        
        conn.commit()
        print("🎉 Migration terminée!")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    simple_migration()