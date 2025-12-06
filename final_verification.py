# Flask/final_verification.py - VÉRIFICATION FINALE
import sqlite3
import os
from sentiment_analyzer import SentimentAnalyzer
import time

def final_verification():
    print("🎯 VÉRIFICATION FINALE COMPLÈTE")
    print("=" * 60)
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'geopolitics.db')
    
    # 1. Vérification base de données
    print("🗃️  BASE DE DONNÉES:")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tables existantes
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"   Tables: {', '.join(tables)}")
    
    # Colonnes articles
    cursor.execute("PRAGMA table_info(articles)")
    columns = [col[1] for col in cursor.fetchall()]
    
    critical_columns = ['analysis_model', 'sentiment_confidence', 'roberta_score', 'roberta_label']
    print("   Colonnes critiques:")
    for col in critical_columns:
        status = "✅" if col in columns else "❌"
        print(f"      {status} {col}")
    
    # Données
    cursor.execute("SELECT COUNT(*) FROM articles")
    articles_count = cursor.fetchone()[0]
    print(f"   📰 Articles: {articles_count}")
    
    cursor.execute("SELECT analysis_model, COUNT(*) FROM articles GROUP BY analysis_model")
    print("   🤖 Modèles utilisés:")
    for model, count in cursor.fetchall():
        print(f"      {model}: {count} articles")
    
    conn.close()
    
    # 2. Vérification RoBERTa Tulpe
    print("\n🤖 ROERTA TULPE:")
    analyzer = SentimentAnalyzer()
    time.sleep(2)
    
    test_cases = [
        ("IA révolutionnaire", "L'intelligence artificielle fait des progrès extraordinaires et va transformer notre société de façon spectaculaire!"),
        ("Crise majeure", "La situation économique est catastrophique avec une inflation horrible et un chômage en hausse désastreuse."),
        ("Innovation positive", "Cette nouvelle technologie est vraiment utile et efficace pour résoudre les problèmes environnementaux.")
    ]
    
    for name, text in test_cases:
        result = analyzer.analyze_sentiment_with_score(text)
        print(f"   🔍 {name}:")
        print(f"      Type: {result['type']}")
        print(f"      Score: {result['score']:.3f}")
        print(f"      Modèle: {result['model']}")
    
    print("\n" + "=" * 60)
    print("🚀 SYSTÈME PRÊT!")
    print("   Vous pouvez maintenant redémarrer l'application Flask")

if __name__ == "__main__":
    final_verification()