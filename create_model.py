# create_model.py
from Flask.database import DatabaseManager
from Flask.sentiment_analyzer import SentimentAnalyzer
from Flask.continuous_learning import get_learning_engine

db = DatabaseManager()
sentiment = SentimentAnalyzer()
engine = get_learning_engine(db, sentiment)

# Forcer la création du modèle
engine._check_and_trigger_learning()

print("✅ Vérification apprentissage lancée")