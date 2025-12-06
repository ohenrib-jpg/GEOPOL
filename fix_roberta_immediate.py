# Flask/fix_roberta_immediate.py - CORRECTION URGENTE
import sqlite3
import os
import sys

def fix_roberta_immediate():
    """Correction urgente pour RoBERTa"""
    
    # Chemin de la base
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'geopolitics.db')
    print(f"🔧 Correction de: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ Base de données non trouvée!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔍 Analyse de la structure...")
        
        # 1. Vérifier les colonnes existantes
        cursor.execute("PRAGMA table_info(articles)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"📋 Colonnes actuelles: {columns}")
        
        # 2. Ajouter les colonnes manquantes pour RoBERTa
        missing_columns = [
            ('analysis_model', 'TEXT DEFAULT "traditional"'),
            ('sentiment_confidence', 'REAL DEFAULT 0.5'),
            ('roberta_score', 'REAL'),
            ('roberta_label', 'TEXT')
        ]
        
        added_count = 0
        for col_name, col_type in missing_columns:
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_name} {col_type}")
                    print(f"✅ AJOUTÉE: {col_name}")
                    added_count += 1
                except Exception as e:
                    print(f"❌ Erreur {col_name}: {e}")
            else:
                print(f"✅ DÉJÀ PRÉSENTE: {col_name}")
        
        # 3. Mettre à jour les articles existants
        if 'analysis_model' in columns:
            cursor.execute("""
                UPDATE articles 
                SET analysis_model = 'traditional'
                WHERE analysis_model IS NULL
            """)
            print(f"✅ {cursor.rowcount} articles mis à jour")
        
        conn.commit()
        
        # 4. Vérification finale
        cursor.execute("PRAGMA table_info(articles)")
        final_columns = [col[1] for col in cursor.fetchall()]
        print(f"\n🎉 STRUCTURE FINALE: {len(final_columns)} colonnes")
        
        # Vérifier RoBERTa
        test_roberta()
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        conn.rollback()
    finally:
        conn.close()

def test_roberta():
    """Teste RoBERTa"""
    print("\n🤖 TEST ROERTA...")
    try:
        from sentiment_analyzer import SentimentAnalyzer
        import time
        
        analyzer = SentimentAnalyzer()
        print("⏳ Attente du chargement de RoBERTa...")
        time.sleep(5)
        
        test_texts = [
            "This is absolutely fantastic and wonderful!",
            "This is terrible and awful.",
            "The situation is normal and stable."
        ]
        
        for i, text in enumerate(test_texts, 1):
            result = analyzer.analyze_sentiment_with_score(text)
            print(f"🧪 Test {i}: {result['model']} -> {result['type']} (score: {result['score']:.3f})")
        
        print("✅ Test RoBERTa terminé!")
        
    except Exception as e:
        print(f"❌ Erreur test RoBERTa: {e}")

if __name__ == "__main__":
    fix_roberta_immediate()