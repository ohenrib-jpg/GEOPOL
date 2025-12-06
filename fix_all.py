#!/usr/bin/env python3
"""
Script de correction automatique COMPLÈTE
Résoudre tous les problèmes connus en une seule commande, non mais
"""

import os
import sys
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / 'rss_analyzer.db'

def print_header(title):
    """Affiche un en-tête formaté"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_database_exists():
    """Vérifie si la base de données existe"""
    if not DB_PATH.exists():
        print(f"❌ Base de données non trouvée: {DB_PATH}")
        print("\n💡 Solution: Lancez d'abord l'application:")
        print("   python run.py")
        return False
    
    print(f"✅ Base de données trouvée: {DB_PATH}")
    return True

def backup_database():
    """Crée une sauvegarde de la base de données"""
    backup_path = BASE_DIR / 'rss_analyzer.db.backup'
    
    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Sauvegarde créée: {backup_path}")
        return True
    except Exception as e:
        print(f"⚠️  Impossible de créer la sauvegarde: {e}")
        return False

def fix_database_structure():
    """Corrige la structure de la base de données"""
    print_header("🔧 CORRECTION DE LA BASE DE DONNÉES")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Supprimer la table migrations
        print("\n📋 Réinitialisation des migrations...")
        cursor.execute("DROP TABLE IF EXISTS migrations")
        print("✅ Table migrations réinitialisée")
        
        # 2. Vérifier les colonnes existantes
        cursor.execute("PRAGMA table_info(articles)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"\n📊 Colonnes existantes: {len(existing_columns)}")
        
        # 3. Ajouter les colonnes manquantes
        columns_to_add = {
            'bayesian_confidence': 'REAL DEFAULT 0.0',
            'bayesian_evidence_count': 'INTEGER DEFAULT 0',
            'original_sentiment_score': 'REAL',
            'analyzed_at': 'DATETIME'
        }
        
        print("\n➕ Ajout des colonnes manquantes:")
        added = 0
        for col_name, col_type in columns_to_add.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {col_name} {col_type}")
                    print(f"  ✅ {col_name}")
                    added += 1
                except sqlite3.OperationalError as e:
                    if "duplicate column" not in str(e).lower():
                        print(f"  ❌ {col_name}: {e}")
            else:
                print(f"  ⏭️  {col_name} (existe déjà)")
        
        # 4. Créer la table article_corroborations si elle n'existe pas
        print("\n📋 Vérification de la table article_corroborations...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS article_corroborations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                similar_article_id INTEGER NOT NULL,
                similarity_score REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                FOREIGN KEY (similar_article_id) REFERENCES articles(id) ON DELETE CASCADE,
                UNIQUE(article_id, similar_article_id)
            )
        """)
        print("✅ Table article_corroborations prête")
        
        # 5. Créer les index
        print("\n🔍 Création des index...")
        indices = [
            ("idx_corr_article", "article_corroborations", "article_id"),
            ("idx_corr_similar", "article_corroborations", "similar_article_id"),
            ("idx_articles_sentiment", "articles", "sentiment_type"),
        ]
        
        for idx_name, table, column in indices:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
                print(f"  ✅ {idx_name}")
            except Exception as e:
                print(f"  ⚠️  {idx_name}: {e}")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ Structure de la base de données corrigée")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def verify_structure():
    """Vérifie et affiche la structure finale"""
    print_header("🔍 VÉRIFICATION FINALE")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Compter les colonnes
        cursor.execute("PRAGMA table_info(articles)")
        columns = cursor.fetchall()
        print(f"\n📊 Table articles: {len(columns)} colonnes")
        
        # Vérifier les colonnes critiques
        critical_columns = ['bayesian_confidence', 'bayesian_evidence_count', 'analyzed_at']
        column_names = {col[1] for col in columns}
        
        print("\n✅ Colonnes critiques:")
        for col in critical_columns:
            status = "✅" if col in column_names else "❌"
            print(f"  {status} {col}")
        
        # Vérifier article_corroborations
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='article_corroborations'")
        if cursor.fetchone():
            print("\n✅ Table article_corroborations existe")
        else:
            print("\n❌ Table article_corroborations manquante")
        
        # Compter les articles
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        print(f"\n📰 {count} articles dans la base")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur vérification: {e}")
        return False
        
    finally:
        conn.close()

def check_files():
    """Vérifie que tous les fichiers nécessaires sont présents"""
    print_header("📁 VÉRIFICATION DES FICHIERS")
    
    required_files = {
        'Flask/bayesian_analyzer.py': 'Analyseur bayésien',
        'Flask/corroboration_engine.py': 'Moteur de corroboration',
        'Flask/database_migrations.py': 'Migrations',
        'Flask/routes_advanced.py': 'Routes avancées',
        'static/js/advanced-analysis.js': 'Interface JS',
    }
    
    all_present = True
    for filepath, description in required_files.items():
        full_path = BASE_DIR / filepath
        if full_path.exists():
            print(f"✅ {description}")
        else:
            print(f"❌ {description} manquant: {filepath}")
            all_present = False
    
    return all_present

def main():
    print("=" * 60)
    print("🔧 CORRECTION AUTOMATIQUE COMPLÈTE")
    print("=" * 60)
    print("\nCe script va :")
    print("  1. Vérifier la base de données")
    print("  2. Créer une sauvegarde")
    print("  3. Corriger la structure")
    print("  4. Vérifier les fichiers Python/JS")
    
    # Vérifier la base de données
    if not check_database_exists():
        sys.exit(1)
    
    # Demander confirmation
    response = input("\n⚠️  Continuer ? (oui/non): ").lower()
    if response not in ['oui', 'o', 'yes', 'y']:
        print("\n❌ Opération annulée")
        sys.exit(0)
    
    # Créer une sauvegarde
    backup_database()
    
    # Corriger la structure
    if not fix_database_structure():
        print("\n❌ Échec de la correction")
        sys.exit(1)
    
    # Vérifier la structure
    if not verify_structure():
        print("\n⚠️  Vérification incomplète")
    
    # Vérifier les fichiers
    if not check_files():
        print("\n⚠️  Certains fichiers sont manquants")
        print("   Consultez les artifacts de la conversation pour les créer")
    
    # Conclusion
    print("\n" + "=" * 60)
    print("✅ CORRECTION TERMINÉE")
    print("=" * 60)
    print("\n🚀 Prochaines étapes:")
    print("   1. Lancez l'application: python run.py")
    print("   2. Ouvrez http://localhost:5000")
    print("   3. Testez le bouton 'Analyse avancée'")
    print("\n📝 Si des erreurs persistent:")
    print("   - Consultez les logs de la console")
    print("   - Vérifiez la console du navigateur (F12)")
    print("   - Référez-vous au fichier CORRECTION_ERREURS.md")
    
    sys.exit(0)

if __name__ == "__main__":
    main()
