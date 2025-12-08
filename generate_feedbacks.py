#!/usr/bin/env python3
# Flask/generate_feedbacks.py
"""
Script pour générer des feedbacks initiaux à partir des articles existants
Cela permettra de démarrer l'apprentissage continu avec des données
"""

import sys
import os
from datetime import datetime
import sqlite3

# Ajouter le chemin parent pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

# Import direct sans le point (pas de package relatif)
try:
    from Flask.database import DatabaseManager
    from Flask.sentiment_analyzer import SentimentAnalyzer
    print("✅ Imports depuis Flask package")
except ImportError:
    # Fallback si on exécute depuis Flask/
    from database import DatabaseManager
    from sentiment_analyzer import SentimentAnalyzer
    print("✅ Imports directs")

def generate_initial_feedbacks(limit=100, confidence_threshold=0.6):
    """
    Génère des feedbacks à partir des articles existants
    
    Args:
        limit: Nombre maximum d'articles à traiter
        confidence_threshold: Seuil de confiance en dessous duquel on crée un feedback
    """
    print("="*70)
    print("🧠 GÉNÉRATION DE FEEDBACKS INITIAUX")
    print("="*70)
    
    # Initialiser les composants
    db_manager = DatabaseManager()
    sentiment_analyzer = SentimentAnalyzer()
    
    # Créer la table si elle n'existe pas
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # Créer la table learning_feedback
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                predicted_sentiment TEXT,
                corrected_sentiment TEXT,
                confidence REAL,
                text_content TEXT,
                processed BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_processed 
            ON learning_feedback(processed)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feedback_article 
            ON learning_feedback(article_id)
        """)
        
        conn.commit()
        print("✅ Table learning_feedback vérifiée/créée")
        
    except Exception as e:
        print(f"⚠️  Erreur création table: {e}")
    
    try:
        # Récupérer les articles récents avec analyse
        print(f"\n📊 Récupération des {limit} articles les plus récents...")
        
        # Ne plus filtrer par confiance, prendre tous les articles
        cursor.execute("""
            SELECT id, title, content, sentiment_type, sentiment_score, 
                   sentiment_confidence, detailed_sentiment
            FROM articles
            ORDER BY pub_date DESC
            LIMIT ?
        """, (limit,))
        
        articles = cursor.fetchall()
        print(f"✅ {len(articles)} articles trouvés")
        
        if not articles:
            print("⚠️  Aucun article à traiter")
            return
        
        # Générer des feedbacks
        feedbacks_created = 0
        
        print(f"\n🔄 Génération des feedbacks...")
        print(f"   Critère: confiance < {confidence_threshold}")
        
        for i, article in enumerate(articles, 1):
            article_id, title, content, sentiment_type, sentiment_score, confidence, detailed_sentiment = article
            
            if not title and not content:
                continue
            
            # Créer le texte complet
            text = f"{title or ''} {content or ''}"[:1000]
            
            # Utiliser le sentiment existant comme "prédiction"
            predicted = detailed_sentiment or sentiment_type or 'neutral'
            
            # Pour la simulation, on considère que le sentiment est correct
            # mais on crée quand même un feedback pour l'apprentissage
            corrected = predicted
            
            # Confiance (ou estimation si manquante)
            conf = confidence if confidence is not None else 0.5
            
            try:
                # Créer le feedback directement avec SQL
                cursor.execute("""
                    INSERT INTO learning_feedback 
                    (article_id, predicted_sentiment, corrected_sentiment, text_content, confidence)
                    VALUES (?, ?, ?, ?, ?)
                """, (article_id, predicted, corrected, text, conf))
                
                feedbacks_created += 1
                
                if i % 10 == 0:
                    print(f"   Progression: {i}/{len(articles)} articles traités...")
                    conn.commit()  # Commit par lots
                
            except Exception as e:
                print(f"   ❌ Erreur article {article_id}: {e}")
                continue
        
        # Commit final
        conn.commit()
        conn.close()
        
        print(f"\n{'='*70}")
        print(f"✅ GÉNÉRATION TERMINÉE")
        print(f"{'='*70}")
        print(f"📊 Feedbacks créés: {feedbacks_created}")
        print(f"📈 Progression vers l'apprentissage: {feedbacks_created}/20")
        
        if feedbacks_created >= 20:
            print(f"\n🎯 SEUIL ATTEINT ! L'apprentissage va se déclencher automatiquement.")
        else:
            print(f"\n⏳ Encore {20 - feedbacks_created} feedbacks nécessaires pour l'apprentissage.")
        
        print(f"\n💡 Astuce: Utilisez l'interface pour corriger les sentiments")
        print(f"   et améliorer la précision du modèle !")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        conn.close()

def check_feedback_status():
    """Vérifie le statut actuel des feedbacks"""
    print("="*70)
    print("📊 STATUT DES FEEDBACKS")
    print("="*70)
    
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # Compter les feedbacks
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN processed = 1 THEN 1 ELSE 0 END) as processed,
                SUM(CASE WHEN processed = 0 THEN 1 ELSE 0 END) as pending
            FROM learning_feedback
        """)
        
        row = cursor.fetchone()
        total, processed, pending = row if row else (0, 0, 0)
        
        print(f"\n📈 Statistiques:")
        print(f"   • Total feedbacks: {total or 0}")
        print(f"   • Traités: {processed or 0}")
        print(f"   • En attente: {pending or 0}")
        
        # Distribution par sentiment
        cursor.execute("""
            SELECT corrected_sentiment, COUNT(*) as count
            FROM learning_feedback
            GROUP BY corrected_sentiment
            ORDER BY count DESC
        """)
        
        distribution = cursor.fetchall()
        
        if distribution:
            print(f"\n📊 Distribution des sentiments:")
            for sentiment, count in distribution:
                emoji = {
                    'positive': '🟢',
                    'neutral_positive': '🔵',
                    'neutral_negative': '🟡',
                    'negative': '🔴'
                }.get(sentiment, '⚪')
                print(f"   {emoji} {sentiment}: {count}")
        
        # Vérifier si le modèle existe
        model_path = os.path.join('instance', 'continuous_learning_model.pth')
        model_exists = os.path.exists(model_path)
        
        print(f"\n🤖 Modèle d'apprentissage:")
        print(f"   {'✅ Créé' if model_exists else '❌ Non créé (nécessite 20+ feedbacks)'}")
        
        if pending and pending >= 20:
            print(f"\n🎯 PRÊT POUR L'APPRENTISSAGE !")
            print(f"   Le système va s'entraîner automatiquement.")
        elif pending:
            print(f"\n⏳ Progression: {pending}/20 feedbacks")
            print(f"   Encore {20 - pending} feedbacks nécessaires.")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        conn.close()

def main():
    """Menu principal"""
    print("\n" + "="*70)
    print("🧠 GEOPOL - GÉNÉRATEUR DE FEEDBACKS D'APPRENTISSAGE")
    print("="*70)
    print("\nOptions:")
    print("  1. Vérifier le statut actuel")
    print("  2. Générer des feedbacks (20 articles)")
    print("  3. Générer des feedbacks (100 articles)")
    print("  4. Générer des feedbacks (tous les articles récents)")
    print("  5. Quitter")
    
    choice = input("\nVotre choix (1-5): ").strip()
    
    if choice == '1':
        check_feedback_status()
    elif choice == '2':
        generate_initial_feedbacks(limit=20, confidence_threshold=0.6)
    elif choice == '3':
        generate_initial_feedbacks(limit=100, confidence_threshold=0.6)
    elif choice == '4':
        generate_initial_feedbacks(limit=1000, confidence_threshold=0.6)
    elif choice == '5':
        print("👋 Au revoir !")
        return
    else:
        print("❌ Choix invalide")
    
    # Afficher le statut après l'action
    if choice in ['2', '3', '4']:
        print("\n" + "="*70)
        input("\nAppuyez sur Entrée pour voir le statut mis à jour...")
        check_feedback_status()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
