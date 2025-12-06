# Flask/create_database.py - CRÉATION COMPLÈTE DE LA BASE
import sqlite3
import os
import json
from datetime import datetime

def create_complete_database():
    """Crée la base de données complète avec toutes les tables"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'geopolitics.db')
    print(f"🗃️  Création de la base: {db_path}")
    
    # Supprimer l'ancienne base si elle existe
    if os.path.exists(db_path):
        print("📦 Suppression de l'ancienne base...")
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔨 Création des tables...")
        
        # 1. Table des thèmes
        cursor.execute("""
            CREATE TABLE themes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                keywords TEXT,
                color TEXT DEFAULT '#6366f1',
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Table 'themes' créée")
        
        # 2. Table des articles (COMPLÈTE avec RoBERTa)
        cursor.execute("""
            CREATE TABLE articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                link TEXT UNIQUE,
                pub_date DATETIME,
                feed_url TEXT,
                sentiment_score REAL,
                sentiment_type TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                -- Colonnes RoBERTa
                analysis_model TEXT DEFAULT 'traditional',
                sentiment_confidence REAL DEFAULT 0.5,
                roberta_score REAL,
                roberta_label TEXT,
                -- Colonnes avancées
                detailed_sentiment TEXT,
                bayesian_confidence REAL,
                bayesian_evidence_count INTEGER DEFAULT 0,
                analyzed_at DATETIME
            )
        """)
        print("✅ Table 'articles' créée avec colonnes RoBERTa")
        
        # 3. Table d'association articles-thèmes
        cursor.execute("""
            CREATE TABLE theme_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                theme_id TEXT,
                confidence REAL DEFAULT 0.5,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE
            )
        """)
        print("✅ Table 'theme_analyses' créée")
        
        # 4. Table des migrations
        cursor.execute("""
            CREATE TABLE migrations (
                name TEXT PRIMARY KEY,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Table 'migrations' créée")
        
        # 5. Table des corroborations
        cursor.execute("""
            CREATE TABLE article_corroborations (
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
        print("✅ Table 'article_corroborations' créée")
        
        # 6. Index pour performances
        indexes = [
            "CREATE INDEX idx_articles_pub_date ON articles(pub_date)",
            "CREATE INDEX idx_articles_feed_url ON articles(feed_url)",
            "CREATE INDEX idx_articles_sentiment ON articles(sentiment_type)",
            "CREATE INDEX idx_articles_analysis_model ON articles(analysis_model)",
            "CREATE INDEX idx_theme_analyses_article ON theme_analyses(article_id)",
            "CREATE INDEX idx_theme_analyses_theme ON theme_analyses(theme_id)",
            "CREATE INDEX idx_corr_article ON article_corroborations(article_id)",
            "CREATE INDEX idx_corr_similar ON article_corroborations(similar_article_id)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        print("✅ Index créés")
        
        # 7. Peupler avec les thèmes par défaut
        default_themes = {
            "technologie": {
                "keywords": ["ai", "intelligence artificielle", "chatgpt", "machine learning", "python", "programmation", "développement", "software", "hardware", "robot", "blockchain", "cloud", "cybersécurité"],
                "color": "#3B82F6"
            },
            "politique": {
                "keywords": ["gouvernement", "élection", "président", "ministre", "parlement", "loi", "réforme", "politique", "député", "sénateur", "vote", "assemblée"],
                "color": "#EF4444"
            },
            "économie": {
                "keywords": ["économie", "inflation", "croissance", "banque", "finance", "bourse", "investissement", "entreprise", "marché", "chômage", "emploi", "crise"],
                "color": "#10B981"
            },
            "santé": {
                "keywords": ["santé", "médecine", "hôpital", "vaccin", "maladie", "médecin", "patient", "recherche", "traitement", "épidémie", "virus", "médical"],
                "color": "#8B5CF6"
            },
            "environnement": {
                "keywords": ["environnement", "climat", "écologie", "réchauffement", "pollution", "énergie", "durable", "biodiversité", "transition", "carbone", "renouvelable"],
                "color": "#22C55E"
            }
        }
        
        for theme_id, theme_data in default_themes.items():
            cursor.execute(
                "INSERT INTO themes (id, name, keywords, color) VALUES (?, ?, ?, ?)",
                (
                    theme_id,
                    theme_id.capitalize(),
                    json.dumps(theme_data['keywords'], ensure_ascii=False),
                    theme_data['color'].replace('#', '')
                )
            )
        print("✅ Thèmes par défaut ajoutés")
        
        # 8. Ajouter des articles d'exemple avec RoBERTa
        sample_articles = [
            {
                "title": "Nouvelle avancée en intelligence artificielle",
                "content": "Les chercheurs ont fait une découverte révolutionnaire en IA qui pourrait changer notre quotidien.",
                "link": "https://example.com/ai-advancement",
                "pub_date": datetime.now().isoformat(),
                "feed_url": "https://example.com/tech",
                "sentiment_score": 0.8,
                "sentiment_type": "positive",
                "analysis_model": "roberta_tulpe",
                "sentiment_confidence": 0.9,
                "roberta_score": 0.8,
                "roberta_label": "positive",
                "detailed_sentiment": "positive"
            },
            {
                "title": "Crise économique en perspective",
                "content": "Les analystes prévoient une période difficile pour l'économie mondiale avec des défis majeurs.",
                "link": "https://example.com/economy-crisis", 
                "pub_date": datetime.now().isoformat(),
                "feed_url": "https://example.com/news",
                "sentiment_score": -0.6,
                "sentiment_type": "negative",
                "analysis_model": "roberta_tulpe", 
                "sentiment_confidence": 0.8,
                "roberta_score": -0.6,
                "roberta_label": "negative",
                "detailed_sentiment": "negative"
            }
        ]
        
        for article in sample_articles:
            cursor.execute("""
                INSERT INTO articles 
                (title, content, link, pub_date, feed_url, sentiment_score, sentiment_type, 
                 analysis_model, sentiment_confidence, roberta_score, roberta_label, detailed_sentiment)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article['title'], article['content'], article['link'], article['pub_date'],
                article['feed_url'], article['sentiment_score'], article['sentiment_type'],
                article['analysis_model'], article['sentiment_confidence'], article['roberta_score'],
                article['roberta_label'], article['detailed_sentiment']
            ))
        print("✅ Articles d'exemple ajoutés")
        
        conn.commit()
        
        # Vérification finale
        print("\n🎉 BASE DE DONNÉES CRÉÉE AVEC SUCCÈS!")
        _show_database_summary(cursor)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def _show_database_summary(cursor):
    """Affiche un résumé de la base"""
    try:
        cursor.execute("SELECT COUNT(*) FROM articles")
        articles_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM themes") 
        themes_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT analysis_model, COUNT(*) FROM articles GROUP BY analysis_model")
        models = cursor.fetchall()
        
        print(f"📊 RÉSUMÉ:")
        print(f"   📰 Articles: {articles_count}")
        print(f"   🏷️  Thèmes: {themes_count}")
        print(f"   🤖 Modèles d'analyse:")
        for model, count in models:
            print(f"      {model}: {count} articles")
            
    except Exception as e:
        print(f"📊 Erreur résumé: {e}")

if __name__ == "__main__":
    create_complete_database()