# Flask/llama_analyzer.py
"""
Module d'analyse géopolitique avec Llama 3.2 local
Génère des rapports structurés avec méthodologie professionnelle
"""

import requests
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class LlamaAnalyzer:
    """
    Analyseur géopolitique utilisant Llama 3.2 en local
    """
    
    def __init__(self, llama_endpoint: str = "http://localhost:8080"):
        self.llama_endpoint = llama_endpoint
        self.timeout = 300  # 5 minutes timeout
        
        # Templates de prompts professionnels
        self.report_templates = {
            'geopolitique': self._build_geopolitical_prompt,
            'economique': self._build_economic_prompt,
            'securite': self._build_security_prompt,
            'synthese': self._build_synthesis_prompt
        }
    
    def test_connection(self) -> bool:
        """Teste la connexion au serveur Llama"""
        try:
            response = requests.get(
                f"{self.llama_endpoint}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connexion Llama impossible: {e}")
            return False
    
    def _build_geopolitical_prompt(self, data_summary: str, articles_context: str) -> str:
        """Construit le prompt pour une analyse géopolitique"""
        return f"""Tu es GEOPOL, un expert senior en géopolitique et relations internationales. Tu dois produire un rapport d'analyse professionnel et structuré.

DONNÉES À ANALYSER:
{data_summary}

CONTEXTE DES ARTICLES:
{articles_context}

Génère un rapport structuré avec :
1. Introduction et contexte
2. Tendances principales (3-5 points)
3. Analyse par thème
4. Recommandations
5. Perspectives

Génère maintenant le rapport complet en HTML avec balises <h2>, <h3>, <p>, <ul>, <li>."""

    def _build_economic_prompt(self, data_summary: str, articles_context: str) -> str:
        """Construit le prompt pour une analyse économique"""
        return f"""Tu es un analyste économique senior. Produis un rapport d'analyse macroéconomique structuré.

DONNÉES ÉCONOMIQUES:
{data_summary}

CONTEXTE:
{articles_context}

STRUCTURE DU RAPPORT:

1. INTRODUCTION
   - Contexte économique global
   - Questions clés

2. MÉTHODOLOGIE
   - Sources et données
   - Approche analytique

3. RÉSUMÉ EXÉCUTIF
   - Indicateurs clés
   - Tendances principales
   - Alertes économiques

4. ANALYSE SECTORIELLE
   - Pour chaque secteur identifié:
     * Performance récente
     * Dynamiques de marché
     * Pressions réglementaires
     * Perspectives

5. PRÉVISIONS ET SCÉNARIOS
   - Scénario central
   - Scénarios alternatifs
   - Risques identifiés
   - Opportunités

6. CONCLUSION
   - Synthèse
   - Recommandations de politique économique

7. RÉFÉRENCES

Format HTML avec balises appropriées."""

    def _build_security_prompt(self, data_summary: str, articles_context: str) -> str:
        """Construit le prompt pour une analyse sécuritaire"""
        return f"""Tu es un expert en sécurité internationale. Produis une analyse des enjeux de sécurité.

DONNÉES:
{data_summary}

CONTEXTE:
{articles_context}

STRUCTURE:

1. INTRODUCTION
   - Panorama sécuritaire
   - Menaces émergentes

2. MÉTHODOLOGIE

3. RÉSUMÉ DES MENACES
   - Niveau de menace global
   - Zones de tension
   - Acteurs malveillants

4. ANALYSE PAR DOMAINE
   - Sécurité conventionnelle
   - Cybersécurité
   - Terrorisme
   - Criminalité organisée

5. ÉVOLUTION ET PRÉVISIONS
   - Tendances à surveiller
   - Scénarios de crise
   - Capacités de réponse

6. CONCLUSION ET RECOMMANDATIONS

7. RÉFÉRENCES

Format HTML."""

    def _build_synthesis_prompt(self, data_summary: str, articles_context: str) -> str:
        """Construit le prompt pour une synthèse hebdomadaire"""
        return f"""Tu es GEOPOL. Produis une synthèse hebdomadaire des événements géopolitiques.

DONNÉES:
{data_summary}

ARTICLES:
{articles_context}

STRUCTURE:

1. INTRODUCTION
   - Semaine du [dates]
   - Vue d'ensemble

2. MÉTHODOLOGIE

3. FAITS MARQUANTS
   - Top 5 des événements clés
   - Impact et signification

4. ANALYSE THÉMATIQUE
   - Évolutions par région/thème
   - Interconnexions

5. PERSPECTIVES
   - Événements à venir
   - Points de vigilance

6. CONCLUSION

7. RÉFÉRENCES

Format HTML."""

    def prepare_data_summary(self, articles: List[Dict], stats: Dict) -> str:
        """Prépare un résumé structuré des données pour le prompt"""
        
        total = len(articles)
        sentiments = stats.get('sentiment_distribution', {})
        themes = stats.get('themes', [])
        
        summary = f"""
📊 STATISTIQUES GLOBALES:
- Nombre d'articles analysés: {total}
- Période: {stats.get('date_from', 'N/A')} → {stats.get('date_to', 'N/A')}

😊 DISTRIBUTION DES SENTIMENTS:
- Positifs: {sentiments.get('positive', 0)} articles ({self._percentage(sentiments.get('positive', 0), total)}%)
- Négatifs: {sentiments.get('negative', 0)} articles ({self._percentage(sentiments.get('negative', 0), total)}%)
- Neutres: {sentiments.get('neutral', 0)} articles ({self._percentage(sentiments.get('neutral', 0), total)}%)

🏷️ THÈMES PRINCIPAUX:
{self._format_themes(themes)}

📍 SOURCES:
{stats.get('sources_count', 'N/A')} sources différentes analysées
"""
        return summary
    
    def prepare_articles_context(self, articles: List[Dict], max_articles: int = 20) -> str:
        """Prépare un contexte à partir des articles les plus pertinents"""
        
        # Trier par pertinence (date récente + sentiment fort)
        sorted_articles = sorted(
            articles,
            key=lambda x: (
                abs(x.get('sentiment_score', 0)),
                x.get('pub_date', '')
            ),
            reverse=True
        )[:max_articles]
        
        context = "ARTICLES CLÉS ANALYSÉS:\n\n"
        
        for i, article in enumerate(sorted_articles, 1):
            sentiment = article.get('sentiment_type', 'neutral')
            emoji = {'positive': '✅', 'negative': '⚠️', 'neutral': '➖'}.get(sentiment, '•')
            
            context += f"{emoji} Article #{i}: {article.get('title', 'Sans titre')}\n"
            context += f"   Source: {self._extract_domain(article.get('feed_url', 'N/A'))}\n"
            context += f"   Date: {article.get('pub_date', 'N/A')[:10]}\n"
            context += f"   Sentiment: {sentiment}\n"
            
            # Résumé du contenu (premiers mots)
            content = article.get('content', '')
            if content:
                context += f"   Résumé: {content[:200]}...\n"
            context += "\n"
        
        return context
    
    def generate_report(self, report_type: str, articles: List[Dict], 
                       stats: Dict) -> Dict[str, Any]:
        """
        Génère un rapport complet avec Llama
        
        Args:
            report_type: Type de rapport (geopolitique, economique, etc.)
            articles: Liste des articles
            stats: Statistiques globales
            
        Returns:
            Dict avec le rapport HTML et métadonnées
        """
        
        try:
            # Vérifier la connexion
            if not self.test_connection():
                return {
                    'success': False,
                    'error': 'Serveur Llama non accessible sur ' + self.llama_endpoint,
                    'fallback': True
                }
            
            logger.info(f"🦙 Génération rapport {report_type} avec {len(articles)} articles")
            
            # Préparer les données
            data_summary = self.prepare_data_summary(articles, stats)
            articles_context = self.prepare_articles_context(articles)
            
            # Construire le prompt
            prompt_builder = self.report_templates.get(
                report_type,
                self._build_geopolitical_prompt
            )
            prompt = prompt_builder(data_summary, articles_context)
            
            # Appel à Llama
            logger.info("📡 Envoi du prompt à Llama...")
            response = requests.post(
                f"{self.llama_endpoint}/v1/chat/completions",
                json={
                    "model": "llama3.2-3b-Q4_K_M",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Tu es GEOPOL, un expert en analyse géopolitique. Tu produis des rapports structurés, factuels et professionnels."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2500,
                    "stream": False
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"Erreur Llama HTTP {response.status_code}")
            
            result = response.json()
            analysis_html = result['choices'][0]['message']['content']
            
            # Nettoyer le HTML si nécessaire
            analysis_html = self._clean_html_output(analysis_html)
            
            logger.info("✅ Rapport généré avec succès")
            
            return {
                'success': True,
                'html_content': analysis_html,
                'model_used': 'Llama 3.2 3B Q4_K_M',
                'timestamp': datetime.now().isoformat(),
                'articles_count': len(articles),
                'report_type': report_type
            }
            
        except requests.Timeout:
            logger.error("⏱️ Timeout lors de l'appel à Llama")
            return {
                'success': False,
                'error': 'Le serveur Llama met trop de temps à répondre (>2 min)',
                'fallback': True
            }
        except Exception as e:
            logger.error(f"❌ Erreur génération rapport: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback': True
            }
    
    def _clean_html_output(self, html: str) -> str:
        """Nettoie la sortie HTML de Llama"""
        # Retirer les éventuels backticks markdown
        html = html.replace('```html', '').replace('```', '')
        
        # S'assurer que c'est bien du HTML
        if not html.strip().startswith('<'):
            # Convertir du texte brut en HTML simple
            lines = html.split('\n')
            html_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    if line.startswith('#'):
                        level = len(line) - len(line.lstrip('#'))
                        html_lines.append(f'<h{level}>{line.lstrip("# ")}</h{level}>')
                    else:
                        html_lines.append(f'<p>{line}</p>')
            html = '\n'.join(html_lines)
        
        return html.strip()
    
    # Méthodes utilitaires
    
    def _percentage(self, value: int, total: int) -> float:
        """Calcule un pourcentage"""
        return round((value / total * 100), 1) if total > 0 else 0
    
    def _format_themes(self, themes: List[str]) -> str:
        """Formate la liste des thèmes"""
        if not themes:
            return "- Aucun thème spécifique détecté"
        return '\n'.join(f"- {theme}" for theme in themes[:10])
    
    def _extract_domain(self, url: str) -> str:
        """Extrait le domaine d'une URL"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            return domain.replace('www.', '')
        except:
            return url
