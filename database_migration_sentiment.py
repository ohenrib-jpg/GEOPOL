# Flask/database_migration_sentiment.py
import sqlite3
import logging

logger = logging.getLogger(__name__)

def migrate_sentiment_columns(db_path):
    """Migration pour les colonnes de sentiment RoBERTa"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔧 Migration des colonnes de sentiment RoBERTa...")
        
        # Vérifier la structure actuelle
        cursor.execute("PRAGMA table_info(articles)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Colonnes existantes: {existing_columns}")
        
        # Colonnes à ajouter pour RoBERTa
        sentiment_columns = [
            ('analysis_model', 'TEXT DEFAULT "traditional"'),
            ('sentiment_confidence', 'REAL DEFAULT 0.5'),
            ('roberta_score', 'REAL'),
            ('roberta_label', 'TEXT')
        ]
        
        for column_name, column_type in sentiment_columns:
            if column_name not in existing_columns:
                print(f"➕ Ajout de la colonne {column_name}...")
                try:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Colonne {column_name} ajoutée")
                except Exception as e:
                    print(f"⚠️ Erreur sur {column_name}: {e}")
        
        # Mettre à jour les articles existants
        print("🔄 Mise à jour des articles existants...")
        
        cursor.execute("""
            UPDATE articles 
            SET analysis_model = 'traditional',
                sentiment_confidence = 0.7
            WHERE analysis_model IS NULL
        """)
        
        updated_count = cursor.rowcount
        print(f"✅ {updated_count} articles mis à jour avec le modèle traditionnel")
        
        conn.commit()
        print("🎉 Migration RoBERTa terminée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur migration RoBERTa: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()