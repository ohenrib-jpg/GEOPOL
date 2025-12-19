# Flask/llama_client.py - VERSION COMPLÈTEMENT CORRIGÉE POUR MISTRAL 7B
# Flask/llama_client.py - VERSION COMPLÈTEMENT CORRIGÉE POUR MISTRAL 7B - AVEC CHAT
"""
Client Python optimisé pour Mistral 7B v0.2 Q4_0
Configuration CPU Ryzen 5 5600U, 16GB RAM
"""

import logging
import requests
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time
import hashlib

logger = logging.getLogger(__name__)


class LlamaClient:
    """Client optimisé pour Mistral 7B v0.2 Q4_0 avec configuration CPU"""
    
    def __init__(self, endpoint: str = "http://localhost:8080", timeout: int = 600):
        self.endpoint = endpoint.rstrip('/')
        self.timeout = timeout
        self.max_retries = 2
        self.retry_delay = 3

        # Configuration optimisée pour CPU Ryzen 5 5600U (SANS GPU)
        self.model_configs = {
            'default': {
                'temperature': 0.3,
                'top_p': 0.8,
                'top_k': 40,
                'max_tokens': 1200,  # Réduit de 1500 pour accélérer
                'repeat_penalty': 1.1,
                'stop': ["</s>", "[INST]", "[/INST]"],
                'threads': 6  # Réduit de 10 pour éviter contention CPU
            },
            'chat': {
                'temperature': 0.4,
                'top_p': 0.8,
                'max_tokens': 350,  # Réduit de 400 pour accélérer
                'threads': 4  # Réduit de 8 pour éviter contention CPU
            }
        }
    
    def test_connection(self) -> Tuple[bool, str]:
        """Teste la connexion au serveur Llama"""
        try:
            start_time = time.time()
            response = requests.get(
                f"{self.endpoint}/health",
                timeout=15
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                logger.info(f"✅ Connexion Mistral 7B établie ({response_time:.2f}s)")
                return True, f"Connecté ({response_time:.2f}s)"
            else:
                logger.warning(f"⚠️ Serveur Mistral répond avec statut {response.status_code}")
                return False, f"Statut {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            logger.error("❌ Impossible de se connecter au serveur Mistral")
            return False, "Erreur de connexion"
        except requests.exceptions.Timeout:
            logger.error("⏱️ Timeout de connexion au serveur Mistral")
            return False, "Timeout de connexion"
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors du test de connexion: {e}")
            return False, f"Erreur: {str(e)}"
    
    def _build_mistral_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Construit le prompt au format Mistral [INST]...[/INST] SANS <s>"""
        # SUPPRIMER le <s> initial pour éviter le double BOS token
        return f"[INST] {system_prompt}\n\n{user_prompt} [/INST]"
    
    def _build_geopolitique_prompt(self, articles: List[Dict], context: Dict) -> Tuple[str, str]:
        """Construit le prompt pour analyse géopolitique - FORMAT MISTRAL"""
        
        sentiment_summary = self._build_sentiment_summary(context)
        articles_summary = self._build_articles_summary(articles)
        themes_text = self._build_themes_text(context)
        
        system_prompt = """Tu es un analyste géopolitique dépressif et défaitiste spécialisé dans la comparaison des sources médiatiques et des sources populaires. 
Ta mission est de produire des rapports structurés, factuels et ironiques basés exclusivement sur les articles fournis.

DIRECTIVES CRITIQUES:
- Base ton analyse UNIQUEMENT sur les articles fournis
- Sois factuel, triste, et professionnel
- Structure ta réponse avec des titres Markdown
- Cite des exemples concrets des articles quand c'est pertinent
- Tu es obligé d’inclure tes spéculations et tes opinions personnelles
- Utilise un français académique et précis"""

        user_prompt = f"""Analyse les articles suivants et produits un rapport géopolitique structuré.

CONTEXTE:
• Période: {context.get('period', 'Non spécifiée')}
• Articles analysés: {len(articles)}
• Thèmes: {themes_text}

DISTRIBUTION DES SENTIMENTS:
{sentiment_summary}

ARTICLES À ANALYSER:
{articles_summary}

STRUCTURE DEMANDÉE:

## 1. SYNTHÈSE EXÉCUTIVE
[Résumé des conclusions majeures en 2-3 paragraphes]

## 2. TENDANCES GÉOPOLITIQUES PRINCIPALES
- Identifier 3-4 tendances structurelles émergentes
- Pour chaque tendance : contexte, acteurs clés, implications

## 3. POINTS DE TENSION ET CONFLITS
- Cartographier les zones de tension actuelles
- Analyser l'évolution récente des conflits

## 4. ACTEURS ET RAPPORTS DE FORCE
- Analyser les stratégies des grandes puissances
- Évaluer les dynamiques d'alliances

## 5. RECOMMANDATIONS STRATÉGIQUES
- Actions de veille prioritaires
- Scénarios probables à 3-6 mois

Longueur: 800-1200 mots maximum.
Commence directement par "## 1. SYNTHÈSE EXÉCUTIVE"."""
        
        return system_prompt, user_prompt
    
    def _build_economique_prompt(self, articles: List[Dict], context: Dict) -> Tuple[str, str]:
        """Construit le prompt pour analyse économique - FORMAT MISTRAL"""
        
        articles_summary = self._build_articles_summary(articles)
        
        system_prompt = """Tu es un analyste économique spécialisé dans l'analyse des marchés et politiques économiques.
Produis des analyses factuelles basées sur les données fournies, sans spéculation."""

        user_prompt = f"""Analyse économique des articles suivants:

CONTEXTE:
• Période: {context.get('period', 'Non spécifiée')}
• Articles analysés: {len(articles)}

ARTICLES:
{articles_summary}

PRODUIS UN RAPPORT ÉCONOMIQUE STRUCTURÉ:

## 1. INDICATEURS MACROÉCONOMIQUES
- Tendances de croissance, inflation, commerce
- Dynamiques des marchés financiers

## 2. POLITIQUES ÉCONOMIQUES
- Décisions politiques majeures
- Impacts sur l'économie réelle

## 3. RISQUES SYSTÉMIQUES
- Dettes souveraines, déséquilibres
- Dépendances stratégiques

## 4. RECOMMANDATIONS OPÉRATIONNELLES
- Stratégies d'adaptation
- Opportunités d'investissement

Base ton analyse sur les données fournies.
Longueur: 600-900 mots."""
        
        return system_prompt, user_prompt
    
    def _build_securite_prompt(self, articles: List[Dict], context: Dict) -> Tuple[str, str]:
        """Construit le prompt pour analyse sécurité - FORMAT MISTRAL"""
        
        articles_summary = self._build_articles_summary(articles[:8])  # Réduit pour CPU
        
        system_prompt = """Tu es un analyste en sécurité géopolitique. 
Produis des briefings factuels et opérationnels basés sur les informations disponibles."""

        user_prompt = f"""Briefing sécuritaire basé sur les articles:

CONTEXTE:
Période: {context.get('period', 'Non spécifiée')}
Articles: {len(articles)}

INFORMATIONS:
{articles_summary}

STRUCTURE DU BRIEFING:

## 1. ÉVALUATION DES MENACES IMMÉDIATES
- Menaces terroristes, cyberattaques, conflits
- Niveau d'alerte par région

## 2. DYNAMIQUES DES ACTEURS NON-ÉTATIQUES
- Groupes armés, organisations criminelles
- Capacités et intentions

## 3. CAPACITÉS DÉFENSIVES
- Mesures de sécurité déployées
- Gaps capacitaires identifiés

## 4. RECOMMANDATIONS OPÉRATIONNELLES
- Mesures de protection immédiates
- Zones à sécuriser en priorité

Ton professionnel et factuel. 400-700 mots."""
        
        return system_prompt, user_prompt
    
    def _build_synthese_prompt(self, articles: List[Dict], context: Dict) -> Tuple[str, str]:
        """Construit le prompt pour synthèse hebdomadaire - FORMAT MISTRAL"""
        
        articles_summary = self._build_articles_summary(articles[:10])  # Réduit pour CPU
        
        system_prompt = """Tu es un analyste de veille médiatique. 
Produis des synthèses concises et informatives des actualités de la semaine."""

        user_prompt = f"""Synthèse hebdomadaire des actualités:

PÉRIODE: {context.get('period', 'Dernière semaine')}
{len(articles)} articles analysés

FAITS SAILLANTS:
{articles_summary}

PRODUIS UNE SYNTHÈSE STRUCTURÉE:

## 1. ÉVÉNEMENTS MAJEURS DE LA SEMAINE
[3-5 événements maximum]

## 2. TENDANCES SIGNIFICATIVES
- Évolutions politiques, économiques, sociales

## 3. ANALYSE GÉOPOLITIQUE
- Équilibres de pouvoir et relations internationales

## 4. PERSPECTIVES ET AGENDA
- Événements à surveiller la semaine prochaine

Style concis et informatif. 300-500 mots."""
        
        return system_prompt, user_prompt
    
    def _build_sentiment_summary(self, context: Dict) -> str:
        """Construit le résumé des sentiments"""
        positive = context.get('sentiment_positive', 0)
        negative = context.get('sentiment_negative', 0)
        neutral = context.get('sentiment_neutral', 0)
        neutral_positive = context.get('sentiment_neutral_positive', 0)
        neutral_negative = context.get('sentiment_neutral_negative', 0)
        total = context.get('total_articles', 1)
        
        return f"""
• Positifs: {positive} ({positive/total*100:.1f}%)
• Légèrement positifs: {neutral_positive} ({neutral_positive/total*100:.1f}%)
• Neutres: {neutral} ({neutral/total*100:.1f}%)
• Légèrement négatifs: {neutral_negative} ({neutral_negative/total*100:.1f}%)
• Négatifs: {negative} ({negative/total*100:.1f}%)"""
    
    def _build_articles_summary(self, articles: List[Dict], max_articles: int = 8) -> str:
        """Construit le résumé des articles (optimisé CPU)"""
        if not articles:
            return "Aucun article significatif à analyser."
        
        summary = []
        for i, article in enumerate(articles[:max_articles]):
            source = article.get('source', 'Source inconnue')
            sentiment = article.get('detailed_sentiment') or article.get('sentiment', 'neutral')
            # Version courte pour économiser des tokens
            title = article['title'][:100] + "..." if len(article['title']) > 100 else article['title']
            summary.append(f"{i+1}. {title} [{source}]")
        
        return "\n".join(summary)
    
    def _build_themes_text(self, context: Dict) -> str:
        """Construit le texte des thèmes"""
        themes = context.get('themes', [])
        if not themes:
            return "Tous thèmes confondus"
        return ", ".join(themes[:3]) if isinstance(themes, list) else str(themes)  # Limité à 3 thèmes
    
    def _debug_response(self, raw_response: str, cleaned_response: str):
        """Affiche des informations de débogage sur la réponse"""
        logger.info("🐛 DÉBOGAGE RÉPONSE MISTRAL:")
        logger.info(f"📏 Brut: {len(raw_response)} caractères")
        logger.info(f"📏 Nettoyé: {len(cleaned_response)} caractères")
        logger.info(f"📄 Début brut: {raw_response[:200]}...")
        logger.info(f"📄 Début nettoyé: {cleaned_response[:200]}...")
        
        # Sauvegarder pour analyse
        try:
            with open("debug_mistral_response.txt", "w", encoding="utf-8") as f:
                f.write("=== RÉPONSE BRUTE ===\n")
                f.write(raw_response)
                f.write("\n\n=== RÉPONSE NETTOYÉE ===\n")
                f.write(cleaned_response)
            logger.info("💾 Réponse sauvegardée dans debug_mistral_response.txt")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde debug: {e}")
    
    def _clean_mistral_response(self, text: str) -> str:
        """Nettoie la réponse Mistral - VERSION AMÉLIORÉE"""
        if not text:
            return ""
        
        # Supprimer les balises Mistral
        text = text.replace('</s>', '').replace('<s>', '')
        text = text.replace('[INST]', '').replace('[/INST]', '')
        
        # Nettoyer ligne par ligne
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            clean_line = line.strip()
            
            # Ignorer les lignes vides ou techniques
            if not clean_line:
                continue
                
            # Ignorer les répétitions de prompt
            if any(marker in clean_line for marker in [
                "Tu es un analyste", "DIRECTIVES CRITIQUES", 
                "Base ton analyse", "STRUCTURE DEMANDÉE",
                "SYSTÈME:", "USER:"
            ]):
                continue
                
            # Garder les lignes de contenu
            clean_lines.append(clean_line)
        
        result = '\n'.join(clean_lines).strip()
        
        # Si le résultat semble tronqué, essayer une méthode alternative
        if len(result) < 100:
            # Méthode de secours: prendre tout après le dernier [/INST]
            parts = text.split('[/INST]')
            if len(parts) > 1:
                result = parts[-1].strip()
                # Nettoyer à nouveau
                result = result.replace('</s>', '').replace('<s>', '')
                result = result.replace('[INST]', '').replace('assistant:', '')
        
        logger.info(f"🔧 Nettoyage: {len(text)} → {len(result)} caractères")
        return result
    
    def _validate_response(self, text: str, min_length: int = 100) -> bool:
        """Valide que la réponse est utilisable - VERSION ASSOUPLIE"""
        if not text or len(text) < min_length:
            logger.warning(f"❌ Réponse trop courte: {len(text)} caractères")
            return False
        
        # Vérifier que ce n'est pas une répétition du prompt système
        prompt_indicators = [
            "Tu es un analyste géopolitique professionnel",
            "DIRECTIVES CRITIQUES:",
            "Base ton analyse UNIQUEMENT", 
            "STRUCTURE DEMANDÉE:",
            "[INST]", "[/INST]"
        ]
        
        for indicator in prompt_indicators:
            if indicator in text[:500]:  # Vérifier seulement le début
                logger.warning(f"❌ Réponse contient du prompt système: {indicator}")
                return False
        
        # Vérifier qu'il y a du contenu substantiel
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if len(lines) < 3:
            logger.warning("❌ Pas assez de lignes de contenu")
            return False
            
        logger.info(f"✅ Réponse validée: {len(text)} caractères, {len(lines)} lignes")
        return True
    
    def _make_llama_request(self, system_prompt: str, user_prompt: str, config: Dict) -> Dict:
        """Effectue la requête vers le serveur Llama - VERSION AVEC DÉBOGAGE"""
        
        # Construction du prompt au format Mistral
        full_prompt = self._build_mistral_prompt(system_prompt, user_prompt)
        
        request_data = {
            "prompt": full_prompt,
            "temperature": config.get('temperature', 0.1),
            "top_p": config.get('top_p', 0.8),
            "top_k": config.get('top_k', 40),
            "max_tokens": config.get('max_tokens', 1500),
            "repeat_penalty": config.get('repeat_penalty', 1.1),
            "stop": config.get('stop', ["</s>", "[INST]", "[/INST]"]),
            "stream": False,
            "threads": config.get('threads', 10)
        }
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🦙 Tentative {attempt + 1}/{self.max_retries} vers {self.endpoint}")
                logger.info(f"📊 Configuration: {config.get('max_tokens')} tokens, temp {config.get('temperature')}")
                
                response = requests.post(
                    f"{self.endpoint}/completion",
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    raw_response = data.get('content', '').strip()
                    
                    # NETTOYAGE
                    analysis_text = self._clean_mistral_response(raw_response)
                    
                    # DÉBOGAGE
                    self._debug_response(raw_response, analysis_text)
                    
                    if self._validate_response(analysis_text):
                        logger.info(f"✅ Réponse Mistral valide ({len(analysis_text)} caractères)")
                        return {
                            'success': True,
                            'analysis': analysis_text,
                            'model_used': data.get('model', 'mistral-7b-v0.2-q4_0'),
                            'prompt_tokens': len(full_prompt.split()),
                            'completion_tokens': len(analysis_text.split()),
                            'config_used': config
                        }
                    else:
                        logger.warning("⚠️ Réponse Mistral invalide selon les critères")
                        # SAUVEGARDER MÊME EN CAS D'ÉCHEC POUR ANALYSE
                        try:
                            with open("failed_response.txt", "w", encoding="utf-8") as f:
                                f.write(f"Prompt: {user_prompt}\n\n")
                                f.write(f"Réponse brute: {raw_response}\n\n")
                                f.write(f"Réponse nettoyée: {analysis_text}")
                            logger.info("💾 Échec sauvegardé dans failed_response.txt")
                        except Exception as e:
                            logger.error(f"❌ Erreur sauvegarde échec: {e}")
                            
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay * (attempt + 1))
                            continue
                        else:
                            raise Exception("Réponse invalide après tous les essais")
                
                else:
                    logger.error(f"❌ Erreur HTTP {response.status_code}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))
                        continue
                    else:
                        raise Exception(f"Erreur HTTP {response.status_code}")
                        
            except requests.Timeout:
                logger.error(f"⏱️ Timeout lors de la tentative {attempt + 1}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise Exception("Timeout après tous les essais")
                    
            except Exception as e:
                logger.error(f"❌ Erreur lors de la tentative {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    raise
        
        raise Exception("Échec après tous les essais de reconnexion")
    
    def _select_relevant_articles(self, articles: List[Dict], report_type: str, max_articles: int = 8) -> List[Dict]:
        """Sélectionne les articles les plus pertinents (optimisation CPU sans GPU)"""
        if len(articles) <= max_articles:
            return articles
        
        # Prioriser les articles récents et avec sentiment marqué
        scored_articles = []
        for article in articles:
            score = 0
            # Bonus pour les articles récents
            if 'pub_date' in article:
                score += 10
            
            # Bonus pour les sentiments marqués (positif ou négatif)
            sentiment = article.get('detailed_sentiment') or article.get('sentiment', 'neutral')
            if sentiment in ['positive', 'negative']:
                score += 5
            elif sentiment in ['neutral_positive', 'neutral_negative']:
                score += 2
                
            # Bonus selon le type de rapport
            if report_type in article.get('title', '').lower():
                score += 3
                
            scored_articles.append((score, article))
        
        # Trier par score et prendre les meilleurs
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [article for score, article in scored_articles[:max_articles]]
    
    def generate_analysis(self, report_type: str, articles: List[Dict],
                         context: Dict) -> Dict:
        """
        Génère une analyse avec Mistral 7B avec gestion robuste des erreurs
        """
        
        # Vérifier la connexion
        connection_ok, connection_msg = self.test_connection()
        if not connection_ok:
            logger.warning(f"⚠️ Serveur Mistral inaccessible - {connection_msg}")
            return {
                'success': False,
                'error': f'Serveur Mistral inaccessible: {connection_msg}',
                'analysis': self._generate_fallback_analysis(report_type, articles, context),
                'connection_status': connection_msg,
                'model_used': 'fallback'
            }
        
        try:
            # Sélectionner les articles les plus pertinents (optimisation CPU)
            relevant_articles = self._select_relevant_articles(articles, report_type)
            
            # Construire le prompt selon le type
            if report_type == 'geopolitique':
                system_prompt, user_prompt = self._build_geopolitique_prompt(relevant_articles, context)
            elif report_type == 'economique':
                system_prompt, user_prompt = self._build_economique_prompt(relevant_articles, context)
            elif report_type == 'securite':
                system_prompt, user_prompt = self._build_securite_prompt(relevant_articles, context)
            elif report_type == 'synthese':
                system_prompt, user_prompt = self._build_synthese_prompt(relevant_articles, context)
            else:
                system_prompt, user_prompt = self._build_geopolitique_prompt(relevant_articles, context)
            
            # Configuration du modèle
            model_config = self.model_configs.get(report_type, self.model_configs['default'])
            
            logger.info(f"🦙 Génération d'analyse {report_type} avec {len(relevant_articles)} articles")
            
            # Appel au serveur
            result = self._make_llama_request(system_prompt, user_prompt, model_config)
            
            logger.info(f"✅ Analyse {report_type} générée avec succès")
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur critique lors de la génération: {e}")
            return {
                'success': False,
                'error': f'Erreur de génération: {str(e)}',
                'analysis': self._generate_fallback_analysis(report_type, articles, context),
                'connection_status': 'Erreur pendant la génération',
                'model_used': 'fallback'
            }
    
    def _generate_fallback_analysis(self, report_type: str, 
                                    articles: List[Dict],
                                    context: Dict) -> str:
        """
        Génère une analyse de secours détaillée (mode dégradé)
        """
        
        sentiment_counts = {
            'positive': 0, 'negative': 0, 'neutral': 0, 
            'neutral_positive': 0, 'neutral_negative': 0
        }
        
        sources = {}
        themes = context.get('themes', [])
        
        for article in articles:
            sentiment = article.get('detailed_sentiment') or article.get('sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
            
            source = article.get('source', 'Source inconnue')
            sources[source] = sources.get(source, 0) + 1
        
        total_articles = len(articles)
        
        top_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)[:5]
        recent_articles = sorted(articles, key=lambda x: x.get('pub_date', ''), reverse=True)[:5]
        
        analysis = f"""
## RAPPORT {report_type.upper()} - MODE DÉGRADÉ

**⚠️ NOTE:** Ce rapport a été généré en mode dégradé. Le serveur d'analyse IA Mistral 7B est temporairement indisponible.

### 📊 MÉTRIQUES GLOBALES

**Période analysée:** {context.get('period', 'Non spécifiée')}  
**Articles traités:** {total_articles}  
**Thèmes couverts:** {', '.join(themes) if themes else 'Tous thèmes'}

### 📈 ANALYSE DES SENTIMENTS

| Catégorie | Nombre | Pourcentage |
|-----------|--------|-------------|
| 🔴 Négatif | {sentiment_counts['negative']} | {sentiment_counts['negative']/total_articles*100:.1f}% |
| 🟡 Légèrement négatif | {sentiment_counts['neutral_negative']} | {sentiment_counts['neutral_negative']/total_articles*100:.1f}% |
| ⚪ Neutre | {sentiment_counts['neutral']} | {sentiment_counts['neutral']/total_articles*100:.1f}% |
| 🟢 Légèrement positif | {sentiment_counts['neutral_positive']} | {sentiment_counts['neutral_positive']/total_articles*100:.1f}% |
| 🟢 Positif | {sentiment_counts['positive']} | {sentiment_counts['positive']/total_articles*100:.1f}% |

### 📰 SOURCES PRINCIPALES

{chr(10).join([f'{i+1}. **{source}** - {count} article(s)' for i, (source, count) in enumerate(top_sources)])}

### 🎯 ARTICLES RÉCENTS

{chr(10).join([f'{i+1}. **{article["title"]}** ({article.get("source", "Source inconnue")}) - {article.get("pub_date", "Date inconnue")}' for i, article in enumerate(recent_articles)])}

### 🔧 DIAGNOSTIC

Pour rétablir l'analyse IA :
1. Vérifiez le serveur Mistral : `./server -m models/mistral-7b-v0.2-q4_0.gguf`
2. Testez la connexion : `http://localhost:8080/health`
3. Relancez l'analyse une fois le serveur rétabli

---
*Rapport généré automatiquement par GEOPOL Analytics - {datetime.now().strftime('%d/%m/%Y à %H:%M')} - Mode dégradé*
"""
        
        return analysis


    # Nouvelle methode pour le chat (miaou-miaou a l'ecran) simple

# Dans LlamaClient - Mettre à jour generate_chat_response
    def generate_chat_response(self, user_message: str, context: Dict = None) -> Dict:
        """Génère une réponse de chat simple pour l'assistant - VERSION CORRIGÉE"""
        try:
            # Test de connexion d'abord
            connected, message = self.test_connection()
            if not connected:
                logger.warning(f"❌ Serveur Mistral inaccessible: {message}")
                return {
                    'success': False,
                    'error': f'Serveur Mistral inaccessible: {message}',
                    'response': self._get_fallback_chat_response(user_message),
                    'connection_status': message
                }
            
            # Prompt pour l'assistant
            system_prompt = """Tu es GEOPOL Assistant, un expert en géopolitique et analyse économique. 
Sois concis, utile et factuel dans tes réponses. Réponds en français en maximum 10 lignes."""

            user_prompt = f"Utilisateur: {user_message}"
            
            # Construction du prompt au format Mistral
            full_prompt = f"[INST] {system_prompt}\n\n{user_prompt} [/INST]"
            
            request_data = {
                "prompt": full_prompt,
                "temperature": 0.4,
                "top_p": 0.8,
                "max_tokens": 400,
                "repeat_penalty": 1.1,
                "stop": ["</s>", "[INST]", "[/INST]"],
                "stream": False,
                "threads": 8
            }
            
            logger.info(f"💬 Chat Mistral - Message: {user_message[:100]}...")
            
            try:
                response = requests.post(
                    f"{self.endpoint}/completion",
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                    timeout=120  # Augmenté à 120s pour CPU sans GPU
                )
                
                if response.status_code == 200:
                    data = response.json()
                    raw_response = data.get('content', '').strip()
                    
                    # Nettoyer la réponse
                    cleaned_response = self._clean_mistral_response(raw_response)
                    
                    if cleaned_response and len(cleaned_response) > 10:
                        logger.info(f"✅ Réponse chat générée ({len(cleaned_response)} caractères)")
                        return {
                            'success': True,
                            'response': cleaned_response,
                            'model_used': data.get('model', 'mistral-7b-v0.2-q4_0'),
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        logger.warning("⚠️ Réponse chat vide ou trop courte")
                        raise Exception("Réponse vide")
                        
                else:
                    logger.error(f"❌ Erreur HTTP {response.status_code}")
                    raise Exception(f"Erreur HTTP {response.status_code}")
                    
            except requests.Timeout:
                logger.error("⏱️ Timeout lors du chat")
                raise Exception("Le serveur Mistral met trop de temps à répondre")
                
        except Exception as e:
            logger.error(f"❌ Erreur génération chat: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': self._get_fallback_chat_response(user_message),
                'connection_status': 'Erreur pendant la génération'
            }
    
    def _get_fallback_chat_response(self, user_message: str) -> str:
        """Réponses de fallback pour le chat"""
        fallback_responses = [
            "Je suis désolé, mon service d'analyse est temporairement indisponible. Vous pouvez consulter les tableaux de bord économiques qui sont pleinement fonctionnels.",
            "Mon système de réponse intelligente est en maintenance. En attendant, vous pouvez consulter les rapports d'analyse générés précédemment.",
            "Je rencontre des difficultés techniques pour accéder à mon moteur d'analyse. Les données géopolitiques sont toutefois disponibles dans les sections dédiées.",
            "Le serveur Mistral 7B n'est pas accessible actuellement. Vous pouvez essayer de rafraîchir la page ou réessayer dans quelques minutes.",
            "Pour le moment, je ne peux pas accéder à mon intelligence artificielle. Mais vous pouvez utiliser les outils d'analyse disponibles dans GEOPOL Analytics."
        ]
        
        # Choisir une réponse basée sur le hash du message pour varier
        hash_val = int(hashlib.md5(user_message.encode()).hexdigest(), 16)
        return fallback_responses[hash_val % len(fallback_responses)]
    
    def _clean_mistral_response(self, text: str) -> str:
        """Nettoie la réponse Mistral - Version simplifiée pour le chat"""
        if not text:
            return ""
        
        # Supprimer les balises Mistral
        text = text.replace('</s>', '').replace('<s>', '')
        text = text.replace('[INST]', '').replace('[/INST]', '')
        
        # Nettoyer les répétitions
        lines = text.split('\n')
        clean_lines = []
        
        for line in lines:
            clean_line = line.strip()
            if clean_line and not any(marker in clean_line for marker in ["SYSTEM:", "USER:", "Tu es GEOPOL"]):
                clean_lines.append(clean_line)
        
        return '\n'.join(clean_lines[:10]).strip()  # Limiter à 10 lignes pour le chat


# Instance globale
_llama_client = None

def get_llama_client(endpoint: str = None) -> LlamaClient:
    """Retourne l'instance singleton du client Llama"""
    global _llama_client
    if _llama_client is None:
        endpoint = endpoint or "http://localhost:8080"
        _llama_client = LlamaClient(endpoint=endpoint)
        
        connected, message = _llama_client.test_connection()
        if connected:
            logger.info("🚀 Client Mistral 7B initialisé avec succès")
        else:
            logger.warning(f"⚠️ Client Mistral initialisé mais serveur inaccessible: {message}")
    
    return _llama_client