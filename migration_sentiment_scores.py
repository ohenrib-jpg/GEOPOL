#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migration_sentiment_scores.py - Migration pour rss_analyzer.db
Version spécifique pour la base de données existante de 110 Mo
"""

import time
from datetime import datetime
import logging
import os
import sys
import sqlite3

# Configuration du logging
logger = logging.getLogger(__name__)

def check_database_structure(db_path):
    """Vérifie et corrige la structure de la base de données"""
    print(f"🔍 Vérification de la structure de la base de données...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Vérifier si la table articles existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        if not cursor.fetchone():
            print("❌ Table 'articles' non trouvée. La base de données n'a pas la structure attendue.")
            return False
        
        # Vérifier les colonnes existantes
        cursor.execute("PRAGMA table_info(articles)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Colonnes existantes dans 'articles': {existing_columns}")
        
        # Colonnes requises pour la migration RoBERTa
        required_columns = [
            'sentiment_score',
            'detailed_sentiment', 
            'confidence',
            'analysis_model',
            'roberta_score'
        ]
        
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        if missing_columns:
            print(f"⚠️ Colonnes manquantes: {missing_columns}")
            print("🔄 Ajout des colonnes manquantes...")
            
            for column in missing_columns:
                if column == 'sentiment_score':
                    cursor.execute("ALTER TABLE articles ADD COLUMN sentiment_score REAL")
                elif column == 'detailed_sentiment':
                    cursor.execute("ALTER TABLE articles ADD COLUMN detailed_sentiment TEXT")
                elif column == 'confidence':
                    cursor.execute("ALTER TABLE articles ADD COLUMN confidence REAL DEFAULT 0.5")
                elif column == 'analysis_model':
                    cursor.execute("ALTER TABLE articles ADD COLUMN analysis_model TEXT DEFAULT 'traditional'")
                elif column == 'roberta_score':
                    cursor.execute("ALTER TABLE articles ADD COLUMN roberta_score REAL")
            
            conn.commit()
            print("✅ Colonnes manquantes ajoutées avec succès")
        else:
            print("✅ Toutes les colonnes requises sont présentes")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la structure: {e}")
        return False
    finally:
        conn.close()

def get_article_count(db_path):
    """Retourne le nombre d'articles dans la base"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM articles")
        count = cursor.fetchone()[0]
        return count
    except Exception as e:
        print(f"❌ Erreur lors du comptage des articles: {e}")
        return 0
    finally:
        conn.close()

def migrate_existing_articles(db_path, batch_size=100, max_articles=None):
    """
    Migre les articles existants pour ajouter les scores de sentiment détaillés
    """
    # Import des modules ici pour éviter les problèmes de chemin
    from database import DatabaseManager
    from sentiment_analyzer import SentimentAnalyzer
    
    db_manager = DatabaseManager(db_path)
    sentiment_analyzer = SentimentAnalyzer()
    
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    stats = {
        'total': 0,
        'migrated': 0,
        'errors': 0,
        'skipped': 0,
        'start_time': datetime.now(),
        'categories': {
            'positive': 0,
            'neutral_positive': 0,
            'neutral_negative': 0,
            'negative': 0
        }
    }
    
    try:
        # 1️⃣ Compter le nombre total d'articles
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        stats['total'] = total_articles
        
        if max_articles:
            total_to_migrate = min(total_articles, max_articles)
        else:
            total_to_migrate = total_articles
        
        print(f"\n{'='*70}")
        print(f"🚀 MIGRATION DES SCORES DE SENTIMENT")
        print(f"{'='*70}")
        print(f"📊 Articles à migrer: {total_to_migrate:,}")
        print(f"📦 Taille des lots: {batch_size}")
        print(f"⏰ Début: {stats['start_time'].strftime('%H:%M:%S')}")
        print(f"{'='*70}\n")
        
        if total_to_migrate == 0:
            print("⚠️ Aucun article à migrer")
            return stats
        
        # 2️⃣ Migration par lots
        offset = 0
        batch_num = 1
        
        while offset < total_to_migrate:
            batch_start = time.time()
            
            # Récupérer un lot d'articles
            limit_clause = f"LIMIT {batch_size} OFFSET {offset}"
            if max_articles:
                remaining = max_articles - offset
                if remaining <= 0:
                    break
                limit_clause = f"LIMIT {min(batch_size, remaining)} OFFSET {offset}"
            
            cursor.execute(f"""
                SELECT id, title, content, sentiment_type, created_at
                FROM articles 
                ORDER BY created_at DESC
                {limit_clause}
            """)
            
            articles = cursor.fetchall()
            
            if not articles:
                break
            
            # Traiter chaque article du lot
            batch_migrated = 0
            batch_errors = 0
            
            for article_id, title, content, current_sentiment, created_at in articles:
                try:
                    if not title and not content:
                        stats['skipped'] += 1
                        continue
                    
                    # Analyser le sentiment avec RoBERTa amélioré
                    sentiment_result = sentiment_analyzer.analyze_article(title or "", content or "")
                    
                    # Mettre à jour l'article
                    cursor.execute("""
                        UPDATE articles 
                        SET sentiment_score = ?,
                            detailed_sentiment = ?,
                            confidence = ?,
                            analysis_model = ?,
                            roberta_score = ?
                        WHERE id = ?
                    """, (
                        sentiment_result['score'],
                        sentiment_result['type'],
                        sentiment_result['confidence'],
                        sentiment_result['model'],
                        sentiment_result.get('score', 0.0),
                        article_id
                    ))
                    
                    # Mettre à jour les statistiques
                    batch_migrated += 1
                    stats['migrated'] += 1
                    stats['categories'][sentiment_result['type']] = stats['categories'].get(sentiment_result['type'], 0) + 1
                    
                except Exception as e:
                    batch_errors += 1
                    stats['errors'] += 1
                    print(f"  ❌ Erreur article {article_id}: {str(e)[:100]}")
                    continue
            
            # Commit du lot
            conn.commit()
            
            # Afficher la progression
            batch_time = time.time() - batch_start
            offset += len(articles)
            progress = (offset / total_to_migrate) * 100 if total_to_migrate > 0 else 100
            articles_per_sec = batch_migrated / batch_time if batch_time > 0 else 0
            
            print(f"📦 Lot {batch_num:3d} | "
                  f"✅ {batch_migrated:3d}/{len(articles)} | "
                  f"❌ {batch_errors:2d} | "
                  f"⏱️  {batch_time:.1f}s | "
                  f"📊 {progress:5.1f}% | "
                  f"⚡ {articles_per_sec:.1f}/s")
            
            batch_num += 1
        
        # 3️⃣ Afficher le résumé final
        end_time = datetime.now()
        duration = (end_time - stats['start_time']).total_seconds()
        
        print(f"\n{'='*70}")
        print(f"🎉 MIGRATION TERMINÉE")
        print(f"{'='*70}")
        print(f"✅ Articles migrés: {stats['migrated']:,}/{stats['total']:,}")
        print(f"❌ Erreurs: {stats['errors']:,}")
        print(f"⏭️  Ignorés: {stats['skipped']:,}")
        print(f"⏱️  Durée totale: {duration/60:.1f} minutes")
        print(f"⚡ Vitesse moyenne: {stats['migrated']/duration:.1f} articles/s")
        print(f"\n📊 DISTRIBUTION DES SENTIMENTS:")
        for category in ['positive', 'neutral_positive', 'neutral_negative', 'negative']:
            count = stats['categories'].get(category, 0)
            percentage = (count / stats['migrated'] * 100) if stats['migrated'] > 0 else 0
            emoji = {'positive': '🟢', 'neutral_positive': '🔵', 'neutral_negative': '🟡', 'negative': '🔴'}.get(category, '⚪')
            print(f"  {emoji} {category:20s}: {count:,} ({percentage:.1f}%)")
        print(f"{'='*70}\n")
        
        return stats
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        raise
    finally:
        conn.close()

def verify_migration(db_path):
    """
    Vérifie que la migration s'est bien passée
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Articles avec nouveau format
        cursor.execute("SELECT COUNT(*) FROM articles WHERE detailed_sentiment IS NOT NULL")
        migrated_count = cursor.fetchone()[0]
        
        # Articles sans scores détaillés
        cursor.execute("SELECT COUNT(*) FROM articles WHERE detailed_sentiment IS NULL")
        remaining_count = cursor.fetchone()[0]
        
        # Distribution par catégorie
        cursor.execute("SELECT detailed_sentiment, COUNT(*) FROM articles WHERE detailed_sentiment IS NOT NULL GROUP BY detailed_sentiment")
        distribution = dict(cursor.fetchall())
        
        # Stats supplémentaires
        cursor.execute("SELECT COUNT(*) FROM articles")
        total_articles = cursor.fetchone()[0]
        
        print(f"\n{'='*70}")
        print(f"🔍 VÉRIFICATION DE LA MIGRATION")
        print(f"{'='*70}")
        print(f"📊 Total articles dans la base: {total_articles:,}")
        print(f"✅ Articles migrés: {migrated_count:,}")
        print(f"⏳ Articles restants: {remaining_count:,}")
        print(f"\n📊 Distribution des sentiments migrés:")
        
        if distribution:
            for category, count in distribution.items():
                emoji = {'positive': '🟢', 'neutral_positive': '🔵', 'neutral_negative': '🟡', 'negative': '🔴'}.get(category, '⚪')
                percentage = (count / migrated_count * 100) if migrated_count > 0 else 0
                print(f"  {emoji} {category:20s}: {count:,} ({percentage:.1f}%)")
        else:
            print("  Aucune donnée de sentiment trouvée")
            
        print(f"{'='*70}\n")
        
        return {
            'migrated': migrated_count,
            'remaining': remaining_count,
            'distribution': distribution,
            'total_articles': total_articles
        }
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return {'migrated': 0, 'remaining': 0, 'distribution': {}}
    finally:
        conn.close()

def main():
    """Fonction principale"""
    # Vérifier que la base de données existe
    db_path = 'rss_analyzer.db'
    if not os.path.exists(db_path):
        print(f"❌ La base de données {db_path} n'a pas été trouvée à la racine.")
        print("ℹ️  Assurez-vous que le fichier est dans le même répertoire que ce script.")
        return
    
    # Ajouter le répertoire parent au path pour les imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)
    
    try:
        # Vérifier la structure de la base
        if not check_database_structure(db_path):
            print("❌ La structure de la base de données est incompatible. Migration annulée.")
            return
        
        # Obtenir le nombre d'articles
        article_count = get_article_count(db_path)
        print(f"📊 Nombre d'articles dans la base: {article_count:,}")
        
        if article_count == 0:
            print("❌ Aucun article à migrer. Migration annulée.")
            return
        
        # Menu interactif
        print("\n📋 Options disponibles:")
        print("  1. Migrer tous les articles")
        print("  2. Migrer les premiers articles (test)")
        print("  3. Vérifier la migration")
        print("  4. Afficher les infos de la base")
        
        choice = input("\nVotre choix (1-4): ").strip()
        
        if choice == '1':
            migrate_existing_articles(db_path)
            verify_migration(db_path)
            
        elif choice == '2':
            test_count = min(100, article_count)  # Tester avec 100 articles ou moins
            migrate_existing_articles(db_path, max_articles=test_count)
            verify_migration(db_path)
            
        elif choice == '3':
            verify_migration(db_path)
            
        elif choice == '4':
            # Afficher les infos de la base
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM articles")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE sentiment_type IS NOT NULL")
            with_sentiment = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE detailed_sentiment IS NOT NULL")
            with_detailed = cursor.fetchone()[0]
            
            print(f"\n📊 INFORMATIONS BASE DE DONNÉES:")
            print(f"   Chemin: {db_path}")
            print(f"   Total articles: {total:,}")
            print(f"   Avec sentiment_type: {with_sentiment:,}")
            print(f"   Avec detailed_sentiment: {with_detailed:,}")
            
            # Structure de la table
            cursor.execute("PRAGMA table_info(articles)")
            columns = cursor.fetchall()
            print(f"\n🏗️  STRUCTURE TABLE articles:")
            for col in columns:
                print(f"   {col[1]} ({col[2]})")
            
            conn.close()
            
        else:
            print("❌ Choix invalide")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
