# Geo/Flask/continuous_learning.py
"""
Système de Deep Learning Passif pour l'Amélioration Continue
Intégration avec l'architecture Flask existante
"""

import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import time

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np

from .database import DatabaseManager
from .sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)

class FeedbackDataset(Dataset):
    """Dataset pour l'apprentissage continu avec feedback utilisateur"""
    
    def __init__(self, feedback_data: List[Dict], sentiment_analyzer: SentimentAnalyzer):
        self.feedback_data = feedback_data
        self.sentiment_analyzer = sentiment_analyzer
        self.label_mapping = {
            'positive': 0,
            'neutral_positive': 1,
            'neutral_negative': 2,
            'negative': 3
        }
        
    def __len__(self):
        return len(self.feedback_data)
    
    def __getitem__(self, idx):
        item = self.feedback_data[idx]
        
        # Extraire les features à partir du texte
        text = f"{item.get('title', '')} {item.get('content', '')}"
        sentiment_result = self.sentiment_analyzer.analyze_sentiment_with_score(text)
        
        # Features vector
        features = [
            sentiment_result['score'],  # Score de sentiment
            sentiment_result['confidence'],  # Confiance
            len(text.split()),  # Longueur du texte
            len([w for w in text.split() if len(w) > 5]),  # Mots longs
        ]
        
        # Convertir en tensor
        features_tensor = torch.FloatTensor(features)
        label_tensor = torch.LongTensor([self.label_mapping.get(item['corrected_sentiment'], 1)])
        
        return features_tensor, label_tensor

class ContinuousLearningModel(nn.Module):
    """Modèle simple de deep learning pour l'apprentissage continu"""
    
    def __init__(self, input_size: int = 4, hidden_size: int = 64, num_classes: int = 4):
        super(ContinuousLearningModel, self).__init__()
        
        self.network = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size // 2, num_classes)
        )
        
    def forward(self, x):
        return self.network(x)

class ContinuousLearningEngine:
    """Moteur d'apprentissage continu passif"""
    
    def __init__(self, db_manager: DatabaseManager, sentiment_analyzer: SentimentAnalyzer):
        self.db_manager = db_manager
        self.sentiment_analyzer = sentiment_analyzer
        self.model = ContinuousLearningModel()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=1e-4)
        self.criterion = nn.CrossEntropyLoss()
        self.feedback_buffer = []
        self.min_feedback_threshold = 20
        self.learning_rate = 1e-5  # Très faible pour fine-tuning
        self.model_path = os.path.join('instance', 'continuous_learning_model.pth')
        
        # Créer la table de feedback si elle n'existe pas
        self._create_feedback_table()
        
        # Charger le modèle existant
        self._load_model()
        
    def _create_feedback_table(self):
        """Créer la table de feedback dans la base de données"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
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
            
            # Index pour performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_processed 
                ON learning_feedback(processed)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_article 
                ON learning_feedback(article_id)
            """)
            
            conn.commit()
            logger.info("✅ Table learning_feedback créée")
            
        except Exception as e:
            logger.error(f"❌ Erreur création table feedback: {e}")
        finally:
            conn.close()
    
    def collect_feedback(self, article_id: int, predicted_sentiment: str, 
                        corrected_sentiment: str, text_content: str, confidence: float = 0.5):
        """Collecter le feedback utilisateur"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO learning_feedback 
                (article_id, predicted_sentiment, corrected_sentiment, text_content, confidence)
                VALUES (?, ?, ?, ?, ?)
            """, (article_id, predicted_sentiment, corrected_sentiment, text_content, confidence))
            
            conn.commit()
            logger.info(f"✅ Feedback collecté pour article {article_id}")
            
            # Vérifier si on doit déclencher l'apprentissage
            self._check_and_trigger_learning()
            
        except Exception as e:
            logger.error(f"❌ Erreur collecte feedback: {e}")
        finally:
            conn.close()
    
    def _check_and_trigger_learning(self):
        """Vérifier si on doit déclencher l'apprentissage"""
        unprocessed_count = self._get_unprocessed_feedback_count()
        
        if unprocessed_count >= self.min_feedback_threshold:
            logger.info(f"🎯 {unprocessed_count} feedbacks non traités - Déclenchement apprentissage")
            self._trigger_learning()
    
    def _get_unprocessed_feedback_count(self) -> int:
        """Obtenir le nombre de feedbacks non traités"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM learning_feedback 
                WHERE processed = FALSE
            """)
            return cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"❌ Erreur comptage feedbacks: {e}")
            return 0
        finally:
            conn.close()
    
    def _get_unprocessed_feedback(self) -> List[Dict]:
        """Obtenir les feedbacks non traités"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, article_id, predicted_sentiment, corrected_sentiment, 
                       text_content, confidence
                FROM learning_feedback 
                WHERE processed = FALSE
                ORDER BY created_at ASC
            """)
            
            feedbacks = []
            for row in cursor.fetchall():
                feedbacks.append({
                    'id': row[0],
                    'article_id': row[1],
                    'predicted_sentiment': row[2],
                    'corrected_sentiment': row[3],
                    'text_content': row[4],
                    'confidence': row[5]
                })
            
            return feedbacks
        except Exception as e:
            logger.error(f"❌ Erreur récupération feedbacks: {e}")
            return []
        finally:
            conn.close()
    
    def _trigger_learning(self):
        """Déclencher l'apprentissage avec les feedbacks"""
        feedback_data = self._get_unprocessed_feedback()
        
        if not feedback_data:
            return
        
        logger.info(f"🚀 Début apprentissage avec {len(feedback_data)} feedbacks")
        
        try:
            # Créer le dataset
            dataset = FeedbackDataset(feedback_data, self.sentiment_analyzer)
            dataloader = DataLoader(dataset, batch_size=8, shuffle=True)
            
            # Fine-tuning avec learning rate très faible
            optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)
            
            self.model.train()
            total_loss = 0
            batch_count = 0
            
            for batch_features, batch_labels in dataloader:
                optimizer.zero_grad()
                
                outputs = self.model(batch_features)
                loss = self.criterion(outputs, batch_labels.squeeze())
                
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
                batch_count += 1
            
            avg_loss = total_loss / batch_count if batch_count > 0 else 0
            logger.info(f"✅ Apprentissage terminé - Loss moyen: {avg_loss:.4f}")
            
            # Sauvegarder le modèle
            self._save_model()
            
            # Marquer les feedbacks comme traités
            self._mark_feedbacks_as_processed([f['id'] for f in feedback_data])
            
        except Exception as e:
            logger.error(f"❌ Erreur apprentissage: {e}")
    
    def _mark_feedbacks_as_processed(self, feedback_ids: List[int]):
        """Marquer les feedbacks comme traités"""
        if not feedback_ids:
            return
            
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            placeholders = ','.join('?' * len(feedback_ids))
            cursor.execute(f"""
                UPDATE learning_feedback 
                SET processed = TRUE 
                WHERE id IN ({placeholders})
            """, feedback_ids)
            
            conn.commit()
            logger.info(f"✅ {len(feedback_ids)} feedbacks marqués comme traités")
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour feedbacks: {e}")
        finally:
            conn.close()
    
    def _save_model(self):
        """Sauvegarder le modèle"""
        try:
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'timestamp': datetime.now().isoformat()
            }, self.model_path)
            logger.info("✅ Modèle sauvegardé")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde modèle: {e}")
    
    def _load_model(self):
        """Charger le modèle existant"""
        try:
            if os.path.exists(self.model_path):
                checkpoint = torch.load(self.model_path)
                self.model.load_state_dict(checkpoint['model_state_dict'])
                self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                logger.info("✅ Modèle chargé")
            else:
                logger.info("🆕 Nouveau modèle créé")
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {e}")
    
    def predict_sentiment(self, text: str) -> Dict[str, Any]:
        """Prédiction avec le modèle continu"""
        try:
            # Analyse avec sentiment analyzer existant
            base_result = self.sentiment_analyzer.analyze_sentiment_with_score(text)
            
            # Features pour le modèle continu
            features = [
                base_result['score'],
                base_result['confidence'],
                len(text.split()),
                len([w for w in text.split() if len(w) > 5])
            ]
            
            # Prédiction avec modèle continu
            features_tensor = torch.FloatTensor(features).unsqueeze(0)
            self.model.eval()
            
            with torch.no_grad():
                outputs = self.model(features_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                predicted_class = torch.argmax(probabilities, dim=1).item()
                
                # Mapping inverse
                class_mapping = {
                    0: 'positive',
                    1: 'neutral_positive', 
                    2: 'neutral_negative',
                    3: 'negative'
                }
                
                continuous_prediction = class_mapping[predicted_class]
                confidence = probabilities[0][predicted_class].item()
                
                # Fusion des résultats
                final_sentiment = continuous_prediction if confidence > 0.7 else base_result['type']
                
                return {
                    'sentiment': final_sentiment,
                    'confidence': max(confidence, base_result['confidence']),
                    'base_sentiment': base_result['type'],
                    'continuous_model_used': True
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur prédiction continue: {e}")
            # Fallback sur analyseur classique
            return self.sentiment_analyzer.analyze_sentiment_with_score(text)

class PassiveLearningScheduler:
    """Planificateur d'apprentissage passif"""
    
    def __init__(self, learning_engine: ContinuousLearningEngine):
        self.learning_engine = learning_engine
        self.running = False
        self.thread = None
        
    def start(self):
        """Démarrer le planificateur"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.thread.start()
            logger.info("✅ Planificateur d'apprentissage passif démarré")
    
    def stop(self):
        """Arrêter le planificateur"""
        self.running = False
        if self.thread:
            self.thread.join()
        logger.info("🛑 Planificateur d'apprentissage passif arrêté")
    
    def _scheduler_loop(self):
        """Boucle principale du planificateur"""
        while self.running:
            try:
                # Vérifier les feedbacks toutes les 30 minutes
                self.learning_engine._check_and_trigger_learning()
                
                # Attendre 30 minutes
                for _ in range(30 * 60):  # 30 minutes * 60 secondes
                    if not self.running:
                        return
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ Erreur planificateur: {e}")
                time.sleep(60)  # Attendre 1 minute en cas d'erreur

# Singleton pour l'engine d'apprentissage
_learning_engine = None
_scheduler = None

def get_learning_engine(db_manager: DatabaseManager, sentiment_analyzer: SentimentAnalyzer) -> ContinuousLearningEngine:
    """Obtenir l'instance singleton du learning engine"""
    global _learning_engine
    
    if _learning_engine is None:
        _learning_engine = ContinuousLearningEngine(db_manager, sentiment_analyzer)
    
    return _learning_engine

def start_passive_learning(db_manager: DatabaseManager, sentiment_analyzer: SentimentAnalyzer):
    """Démarrer l'apprentissage passif"""
    global _scheduler
    
    learning_engine = get_learning_engine(db_manager, sentiment_analyzer)
    _scheduler = PassiveLearningScheduler(learning_engine)
    _scheduler.start()
    
    return learning_engine

def stop_passive_learning():
    """Arrêter l'apprentissage passif"""
    global _scheduler
    
    if _scheduler:
        _scheduler.stop()
        _scheduler = None
