#!/usr/bin/env python3
"""
Script pour réinitialiser les migrations et recréer les colonnes manquantes
"""

import sqlite3
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'rss_analyzer.db')

def reset_migrations():
    """Réinitialise la table des migrations"""
    print("🔄 Réinitialisation des migrations...")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Base de données non trouvée: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Supprimer la table migrations
        cursor.execute("DROP TABLE IF EXISTS migrations")
        print("✅ Table migrations supprimée")
        
        # Ajouter les colonnes manquantes si elles n'existent pas
        print("\n📊 Vérification des colonnes...")
        
        # Récupérer la structure actuelle de la table articles
        cursor.execute("PRAGMA table_info(articles)")
        columns = {row[1] for row in cursor.fetchall()}
        print(f"Colonnes existantes: {columns}")
        
        # Colonnes à ajouter
        columns_to_add = {
            'bayesian_confidence': 'REAL DEFAULT 0.0',
            'bayesian_evidence_count': 'INTEGER DEFAULT 0',
            'original_sentiment_score': 'REAL',
            'analyzed_at': 'DATETIME'
        }
        
        for col_name, col_type in columns_to_add.items():
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_name} {col_type}")
                    print(f"✅ Colonne ajoutée: {col_name}")
                except sqlite3.OperationalError as e:
                    if "duplicate column" in str(e).lower():
                        print(f"⏭️  Colonne {col_name} existe déjà")
                    else:
                        raise
            else:
                print(f"⏭️  Colonne {col_name} existe déjà")
        
        conn.commit()
        print("\n✅ Réinitialisation terminée avec succès")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def verify_structure():
    """Vérifie la structure de la base de données"""
    print("\n🔍 Vérification de la structure...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Vérifier la table articles
        cursor.execute("PRAGMA table_info(articles)")
        print("\n📋 Structure de la table 'articles':")
        for row in cursor.fetchall():
            print(f"  - {row[1]} ({row[2]})")
        
        # Vérifier la table article_corroborations
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='article_corroborations'")
        if cursor.fetchone():
            print("\n✅ Table 'article_corroborations' existe")
        else:
            print("\n⚠️  Table 'article_corroborations' manquante")
            
    finally:
        conn.close()

def main():
    print("=" * 60)
    print("🔧 RÉINITIALISATION DES MIGRATIONS")
    print("=" * 60)
    
    if not os.path.exists(DB_PATH):
        print(f"\n❌ Base de données non trouvée: {DB_PATH}")
        print("\n💡 Lancez d'abord l'application avec: python run.py")
        sys.exit(1)
    
    # Demander confirmation
    print(f"\n📁 Base de données: {DB_PATH}")
    response = input("\n⚠️  Voulez-vous réinitialiser les migrations ? (oui/non): ")
    
    if response.lower() not in ['oui', 'o', 'yes', 'y']:
        print("\n❌ Opération annulée")
        sys.exit(0)
    
    # Réinitialiser
    success = reset_migrations()
    
    if success:
        verify_structure()
        
        print("\n" + "=" * 60)
        print("✅ MIGRATION RÉUSSIE")
        print("=" * 60)
        print("\n🚀 Prochaines étapes:")
        print("   1. Redémarrez l'application: python run.py")
        print("   2. Les migrations seront réappliquées automatiquement")
        print("   3. Testez le bouton 'Analyse avancée'")
        
        sys.exit(0)
    else:
        print("\n❌ Échec de la réinitialisation")
        sys.exit(1)

if __name__ == "__main__":
    main()
