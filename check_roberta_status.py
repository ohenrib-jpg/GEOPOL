# Flask/check_roberta_status.py - VERSION CORRIGÉE
import sqlite3
import os
import time
import sys

# Ajouter le chemin parent pour les imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def check_roberta_status(db_path):
    """Vérifie le statut de RoBERTa et de la base de données"""
    print("🔍 Vérification complète du système...")
    
    # 1. Vérifier la base de données
    print("\n📊 VÉRIFICATION BASE DE DONNÉES:")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Colonnes existantes
    cursor.execute("PRAGMA table_info(articles)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"✅ Colonnes articles: {len(columns)} colonnes")
    
    # Vérifier les colonnes critiques
    critical_columns = ['analysis_model', 'detailed_sentiment', 'sentiment_confidence']
    for col in critical_columns:
        if col in columns:
            print(f"   ✅ {col}: PRÉSENTE")
        else:
            print(f"   ❌ {col}: MANQUANTE")
    
    # Compter les articles
    cursor.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]
    print(f"✅ Total articles: {total_articles}")
    
    # Vérifier si analysis_model existe avant de l'utiliser
    if 'analysis_model' in columns:
        cursor.execute("SELECT analysis_model, COUNT(*) FROM articles GROUP BY analysis_model")
        stats = cursor.fetchall()
        print("📊 Articles par modèle:")
        for model, count in stats:
            print(f"   {model}: {count} articles")
    else:
        print("❌ analysis_model: colonne non disponible")
    
    conn.close()
    
    # 2. Vérifier RoBERTa
    print("\n🤖 VÉRIFICATION ROERTA:")
    try:
        from sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        
        # Attendre que RoBERTa se charge
        print("⏳ Chargement de RoBERTa (attente 5 secondes)...")
        time.sleep(5)
        
        # Test avec plusieurs textes
        test_cases = [
            "This is absolutely fantastic and wonderful!",
            "This is terrible and awful.",
            "The weather is normal today."
        ]
        
        for i, text in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}: '{text}'")
            result = analyzer.analyze_sentiment_with_score(text)
            print(f"   📊 Modèle: {result['model']}")
            print(f"   🎯 Type: {result['type']}")
            print(f"   🔢 Score: {result['score']:.3f}")
            print(f"   💪 Confiance: {result['confidence']:.3f}")
            
            if 'roberta' in result.get('model', ''):
                print("   ✅ RoBERTa actif!")
            else:
                print("   ⚠️ Mode traditionnel")
    
    except Exception as e:
        print(f"❌ Erreur RoBERTa: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*50)
    print("🎉 VÉRIFICATION TERMINÉE")

if __name__ == "__main__":
    # Chemin vers la base de données
    from config import DB_PATH
    check_roberta_status(DB_PATH)