import logging
import threading
from typing import Dict, Any, List, Tuple
import numpy as np

# Importations conditionnelles
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("⚠️ TextBlob non disponible")

try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("⚠️ NLTK non disponible")

try:
    from transformers import pipeline
    ROBERTA_AVAILABLE = True
    print("✅ Transformers disponible - RoBERTa activable")
except ImportError:
    ROBERTA_AVAILABLE = False
    print("⚠️ Transformers non disponible")

logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    def __init__(self):
        self.sia = None
        self.roberta_pipeline = None
        
        # 🎯 LEXIQUE GÉOPOLITIQUE AMÉLIORÉ - PLUS NUANCÉ
        self.geopolitical_modifiers = {
            # Termes négatifs (impact réduit)
            'conflit': -0.25, 'guerre': -0.4, 'invasion': -0.5,
            'sanction': -0.3, 'embargo': -0.3, 'crise': -0.25,
            'tension': -0.2, 'menace': -0.25, 'attaque': -0.4,
            'bombardement': -0.5, 'victime': -0.3, 'destruction': -0.4,
            'réfugié': -0.25, 'famine': -0.4, 'répression': -0.3,
            'violence': -0.3, 'instabilité': -0.2, 'protestation': -0.15,
            
            # Termes positifs (impact augmenté)
            'accord': 0.5, 'paix': 0.6, 'coopération': 0.5,
            'diplomatie': 0.4, 'négociation': 0.4, 'traité': 0.5,
            'alliance': 0.5, 'stabilité': 0.4, 'développement': 0.4,
            'croissance': 0.4, 'investissement': 0.4, 'partenariat': 0.5,
            'progrès': 0.4, 'solution': 0.3, 'entente': 0.3,
            'réconciliation': 0.5, 'détente': 0.4, 'compromis': 0.3,
            
            # Termes neutres mais souvent positifs en contexte
            'élection': 0.1, 'sommet': 0.2, 'réunion': 0.15,
            'déclaration': 0.1, 'annonce': 0.1, 'visite': 0.2,
            'dialogue': 0.3, 'consultation': 0.2, 'forum': 0.15
        }
        
        # 📊 SEUILS RECALIBRÉS - PLUS PERMISSIFS POUR LE POSITIF
        self.thresholds = {
            'positive': 0.15,           # Seuil abaissé pour capturer plus de positif
            'neutral_positive': 0.02,   # Zone tampon élargie
            'neutral_negative': -0.02,  # Zone neutre réduite
            'negative': -0.15           # Seuil relevé pour réduire faux négatifs
        }
        
        self._initialize_nltk()
        self._initialize_roberta()
    
    def _initialize_nltk(self):
        """Initialise NLTK en arrière-plan"""
        if not NLTK_AVAILABLE:
            return
            
        def download_nltk_data():
            try:
                nltk.data.find('vader_lexicon')
                logger.info("✅ VADER lexicon déjà disponible")
            except LookupError:
                logger.info("📥 Téléchargement de VADER lexicon...")
                nltk.download('vader_lexicon', quiet=True)
                logger.info("✅ VADER lexicon téléchargé")
            
            self.sia = SentimentIntensityAnalyzer()
        
        thread = threading.Thread(target=download_nltk_data)
        thread.daemon = True
        thread.start()
    
    def _initialize_roberta(self):
        """Initialise RoBERTa en arrière-plan"""
        if not ROBERTA_AVAILABLE:
            print("⚠️ RoBERTa non disponible - mode fallback activé")
            return
            
        def load_roberta():
            try:
                print("🤖 Chargement de RoBERTa...")
                # Utilisation d'un modèle plus adapté au contexte général
                self.roberta_pipeline = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    truncation=True,
                    max_length=512,
                    device=-1,  # CPU
                    top_k=None  # Obtenir tous les scores
                )
                print("✅ RoBERTa chargé avec succès !")
            except Exception as e:
                print(f"❌ Erreur chargement RoBERTa: {e}")
                # Fallback vers un modèle plus simple
                try:
                    self.roberta_pipeline = pipeline(
                        "sentiment-analysis",
                        model="siebert/sentiment-roberta-large-english",
                        device=-1
                    )
                    print("✅ Fallback RoBERTa chargé")
                except Exception as e2:
                    print(f"❌ Erreur fallback RoBERTa: {e2}")
                    self.roberta_pipeline = None
        
        load_roberta()
    
    def _apply_geopolitical_context(self, text: str, base_score: float) -> float:
        """
        🎯 Ajuste le score en fonction du contexte géopolitique - VERSION AMÉLIORÉE
        """
        text_lower = text.lower()
        adjustment = 0.0
        matches = 0
        
        for term, modifier in self.geopolitical_modifiers.items():
            # Recherche plus robuste avec word boundaries
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text_lower):
                adjustment += modifier
                matches += 1
                logger.debug(f"🔍 Terme géo trouvé: '{term}' -> {modifier}")
        
        # Moyenne des ajustements trouvés
        if matches > 0:
            adjustment = adjustment / matches
            # Mélange avec pondération réduite pour le contexte (80% base, 20% contexte)
            adjusted_score = (base_score * 0.8) + (adjustment * 0.2)
            logger.debug(f"🎯 Ajustement géo: {base_score:.3f} → {adjusted_score:.3f} ({matches} termes)")
            return min(max(adjusted_score, -1.0), 1.0)  # Clamping
        
        return base_score
    
    def _smooth_score(self, score: float) -> float:
        """
        📊 Lissage moins agressif pour préserver les nuances
        """
        # Réduction de la compression
        smoothed = np.tanh(score * 1.2)  # Facteur augmenté pour moins compresser
        return float(smoothed)
    
    def _categorize_sentiment(self, score: float, confidence: float) -> str:
        """
        🏷️ Catégorisation plus nuancée avec biais positif
        """
        # Si confiance faible, tendre vers le neutre positif
        if confidence < 0.4:
            return 'neutral_positive' if score >= -0.1 else 'neutral_negative'
        
        # Biais positif pour les scores proches de zéro
        if score > 0:
            # Renforcement du positif
            if score >= self.thresholds['positive']:
                return 'positive'
            elif score >= self.thresholds['neutral_positive']:
                return 'neutral_positive'
            else:
                # Scores légèrement positifs mais sous le seuil -> neutre positif
                return 'neutral_positive'
        else:
            if score <= self.thresholds['negative']:
                return 'negative'
            elif score <= self.thresholds['neutral_negative']:
                return 'neutral_negative'
            else:
                # Scores légèrement négatifs mais au-dessus du seuil -> neutre négatif
                return 'neutral_negative'
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """
        Extraire les phrases clés pour une analyse plus précise
        """
        # Découpage simple en phrases
        sentences = re.split(r'[.!?]+', text)
        key_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Phrases significatives
                # Vérifier la présence de termes importants
                important_terms = ['accord', 'paix', 'coopération', 'conflit', 'crise', 'négociation']
                if any(term in sentence.lower() for term in important_terms):
                    key_sentences.append(sentence)
        
        return key_sentences
    
    def analyze_sentiment_with_score(self, text: str) -> Dict[str, Any]:
        """
        ⭐ Analyse principale avec améliorations significatives
        """
        if not text or len(text.strip()) < 10:
            return {
                'score': 0.05,  # Léger biais positif pour contenu vide
                'type': 'neutral_positive',
                'confidence': 0.0,
                'model': 'none'
            }
        
        # PRIORITÉ 1 : RoBERTa avec améliorations
        if self.roberta_pipeline:
            try:
                # Utiliser les phrases clés si possible
                key_phrases = self._extract_key_phrases(text)
                analysis_text = ' '.join(key_phrases) if key_phrases else text[:800]
                
                result = self.roberta_pipeline(analysis_text)[0]
                
                # Traitement amélioré des résultats RoBERTa
                if isinstance(result, list):
                    # Modèle retournant multiple scores
                    scores_dict = {item['label']: item['score'] for item in result}
                    positive_score = scores_dict.get('positive', scores_dict.get('POS', 0))
                    negative_score = scores_dict.get('negative', scores_dict.get('NEG', 0))
                    neutral_score = scores_dict.get('neutral', scores_dict.get('NEU', 0))
                    
                    # Calcul du score brut normalisé
                    raw_score = positive_score - negative_score
                    raw_confidence = max(positive_score, negative_score, neutral_score)
                    
                else:
                    # Modèle simple
                    label = result['label'].lower()
                    raw_confidence = result['score']
                    
                    if 'positive' in label:
                        raw_score = raw_confidence
                    elif 'negative' in label:
                        raw_score = -raw_confidence
                    else:
                        raw_score = 0.0
                
                # 🎯 APPLICATION DU CONTEXTE GÉOPOLITIQUE AMÉLIORÉ
                geo_adjusted_score = self._apply_geopolitical_context(text, raw_score)
                
                # 📊 LISSAGE AMÉLIORÉ
                smoothed_score = self._smooth_score(geo_adjusted_score)
                
                # 🏷️ CATÉGORISATION INTELLIGENTE
                sentiment_type = self._categorize_sentiment(smoothed_score, raw_confidence)
                
                # Post-processing : éviter les neutres négatifs pour scores légèrement positifs
                if sentiment_type == 'neutral_negative' and smoothed_score > -0.01:
                    sentiment_type = 'neutral_positive'
                
                result = {
                    'score': smoothed_score,
                    'type': sentiment_type,
                    'confidence': raw_confidence,
                    'model': 'roberta_enhanced',
                    'raw_score': raw_score,
                    'geo_adjusted': geo_adjusted_score,
                    'key_phrases_used': len(key_phrases) > 0
                }
                
                logger.debug(f"📊 Analyse RoBERTa: {raw_score:.3f} -> {smoothed_score:.3f} -> {sentiment_type}")
                return result
                
            except Exception as e:
                logger.error(f"Erreur RoBERTa: {e}")
                # Fallback systématique en cas d'erreur
        
        # FALLBACK : Méthode traditionnelle améliorée
        return self._analyze_traditional_enhanced(text)
    
    def _analyze_traditional_enhanced(self, text: str) -> Dict[str, Any]:
        """
        📚 Analyse traditionnelle avec améliorations significatives
        """
        try:
            scores = []
            confidences = []
            
            # TextBlob avec pondération
            if TEXTBLOB_AVAILABLE:
                blob = TextBlob(text)
                tb_score = blob.sentiment.polarity
                tb_confidence = blob.sentiment.subjectivity  # Subjectivité comme proxy de confiance
                scores.append(tb_score)
                confidences.append(tb_confidence)
            
            # VADER avec analyse détaillée
            if self.sia:
                vader_scores = self.sia.polarity_scores(text)
                vader_score = vader_scores['compound']
                vader_confidence = 1.0 - abs(vader_scores['neu'] - 0.5)  # Confiance basée sur neutralité
                scores.append(vader_score)
                confidences.append(vader_confidence)
            
            # Moyenne pondérée par confiance
            if scores:
                total_confidence = sum(confidences)
                if total_confidence > 0:
                    raw_score = sum(s * c for s, c in zip(scores, confidences)) / total_confidence
                    avg_confidence = total_confidence / len(confidences)
                else:
                    raw_score = sum(scores) / len(scores)
                    avg_confidence = 0.5
            else:
                raw_score = 0.0
                avg_confidence = 0.0
            
            # 🎯 Contexte géopolitique
            geo_adjusted = self._apply_geopolitical_context(text, raw_score)
            
            # 📊 Lissage
            smoothed = self._smooth_score(geo_adjusted)
            
            # 🏷️ Catégorisation avec biais positif
            sentiment_type = self._categorize_sentiment(smoothed, avg_confidence)
            
            return {
                'score': smoothed,
                'type': sentiment_type,
                'confidence': avg_confidence,
                'model': 'traditional_enhanced',
                'raw_score': raw_score,
                'geo_adjusted': geo_adjusted
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse traditionnelle: {e}")
            # Fallback ultra simple
            return {
                'score': 0.05,  # Léger biais positif
                'type': 'neutral_positive',
                'confidence': 0.1,
                'model': 'error_fallback'
            }
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Méthode de compatibilité"""
        return self.analyze_sentiment_with_score(text)
    
    def analyze_article(self, title: str, content: str) -> Dict[str, Any]:
        """
        📰 Analyse d'article avec pondération optimisée
        """
        # Le titre a plus d'importance (70/30) pour la géopolitique
        title_analysis = self.analyze_sentiment_with_score(title)
        content_analysis = self.analyze_sentiment_with_score(content[:1500])  # Contenu limité
        
        # Score combiné avec pondération titre renforcée
        combined_score = (title_analysis['score'] * 0.7) + (content_analysis['score'] * 0.3)
        combined_confidence = (title_analysis['confidence'] * 0.7) + (content_analysis['confidence'] * 0.3)
        
        # Recatégorisation avec vérification de cohérence
        sentiment_type = self._categorize_sentiment(combined_score, combined_confidence)
        
        # Vérification de cohérence entre titre et contenu
        title_type = title_analysis['type']
        content_type = content_analysis['type']
        
        # Si conflit majeur, favoriser le titre
        if (title_type in ['positive', 'neutral_positive'] and 
            content_type in ['negative', 'neutral_negative']):
            logger.debug(f"⚠️ Conflit détecté: titre={title_type}, contenu={content_type} -> priorité titre")
            # Ajuster légèrement vers le titre
            combined_score = (combined_score * 0.3) + (title_analysis['score'] * 0.7)
            sentiment_type = self._categorize_sentiment(combined_score, combined_confidence)
        
        return {
            'score': combined_score,
            'type': sentiment_type,
            'confidence': combined_confidence,
            'model': title_analysis['model'],
            'title_score': title_analysis['score'],
            'content_score': content_analysis['score'],
            'title_sentiment': title_type,
            'content_sentiment': content_type
        }
    
    def get_detailed_sentiment_category(self, result: Dict[str, Any]) -> Tuple[str, float]:
        """
        Méthode utilitaire pour la migration
        """
        return result['type'], result['confidence']
    
    def get_sentiment_explanation(self, result: Dict[str, Any]) -> str:
        """
        💬 Génère une explication textuelle du sentiment
        """
        score = result['score']
        sentiment = result['type']
        confidence = result['confidence']
        
        explanations = {
            'positive': f"Sentiment clairement positif (score: {score:.2f}, confiance: {confidence:.0%})",
            'neutral_positive': f"Tendance positive (score: {score:.2f}, confiance: {confidence:.0%})",
            'neutral_negative': f"Tendance négative (score: {score:.2f}, confiance: {confidence:.0%})",
            'negative': f"Sentiment clairement négatif (score: {score:.2f}, confiance: {confidence:.0%})"
        }
        
        return explanations.get(sentiment, "Sentiment indéterminé")

# Ajout de l'import manquant
import re
