# Flask/fix_migration_immediate.py - CORRECTION URGENTE
import sqlite3
import os

def fix_database_immediate():
    """Correction immédiate de la base de données"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'geopolitics.db')
    print(f"🔧 Correction de la base: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Ajouter les colonnes manquantes pour RoBERTa
        missing_columns = [
            'analysis_model',
            'sentiment_confidence', 
            'roberta_score',
            'roberta_label'
        ]
        
        cursor.execute("PRAGMA table_info(articles)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Colonnes existantes: {existing_columns}")
        
        for column in missing_columns:
            if column not in existing_columns:
                if column == 'analysis_model':
                    cursor.execute("ALTER TABLE articles ADD COLUMN analysis_model TEXT DEFAULT 'traditional'")
                elif column == 'sentiment_confidence':
                    cursor.execute("ALTER TABLE articles ADD COLUMN sentiment_confidence REAL DEFAULT 0.5")
                elif column == 'roberta_score':
                    cursor.execute("ALTER TABLE articles ADD COLUMN roberta_score REAL")
                elif column == 'roberta_label':
                    cursor.execute("ALTER TABLE articles ADD COLUMN roberta_label TEXT")
                print(f"✅ Colonne ajoutée: {column}")
        
        # 2. Mettre à jour les articles existants
        cursor.execute("""
            UPDATE articles 
            SET analysis_model = 'traditional',
                sentiment_confidence = 0.7
            WHERE analysis_model IS NULL
        """)
        print(f"✅ {cursor.rowcount} articles mis à jour")
        
        conn.commit()
        
        # 3. Vérification finale
        cursor.execute("PRAGMA table_info(articles)")
        final_columns = [col[1] for col in cursor.fetchall()]
        print(f"🎉 Colonnes finales: {final_columns}")
        
        # Vérifier RoBERTa
        test_roberta_status(cursor)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        conn.rollback()
    finally:
        conn.close()

def test_roberta_status(cursor):
    """Teste le statut de RoBERTa"""
    print("\n🔍 Test RoBERTa en cours...")
    
    # Vérifier si RoBERTa est disponible
    try:
        from sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        
        # Attendre un peu que RoBERTa se charge
        import time
        print("⏳ Chargement de RoBERTa...")
        time.sleep(3)
        
        # Test avec un texte simple
        test_text = "This is absolutely fantastic and wonderful!"
        result = analyzer.analyze_sentiment_with_score(test_text)
        
        print(f"🧪 Test RoBERTa: '{test_text}'")
        print(f"   Modèle: {result['model']}")
        print(f"   Score: {result['score']}")
        print(f"   Type: {result['type']}")
        print(f"   Confiance: {result['confidence']}")
        
        if result['model'] == 'roberta':
            print("🎉 RoBERTa est OPÉRATIONNEL!")
        else:
            print("⚠️ RoBERTa non disponible, utilisation du mode traditionnel")
            
    except Exception as e:
        print(f"❌ Erreur test RoBERTa: {e}")

if __name__ == "__main__":
    fix_database_immediate()