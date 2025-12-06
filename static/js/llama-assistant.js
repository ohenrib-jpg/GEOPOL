// static/js/llama-assistant.js
class LlamaAssistant {
  constructor() {
    this.endpoint = "http://localhost:8080"; // endpoint llama.cpp
    this.enabled = true; // À gérer via les settings
    this.reportTemplates = {
      geopolitique: `
SYSTEM: Tu es GEOPOL, un expert en géopolitique. Analyse ce rapport.

RAPPORT GÉOPOLITIQUE - Template:
# Analyse Géopolitique

## 📊 Synthèse des Données
{data_summary}

## 🔍 Tendances Principales
- Tendances détectées
- Évolutions significatives
- Points de rupture

## 🌍 Contexte International
- Implications régionales
- Acteurs concernés
- Dynamiques de pouvoir

## 📈 Recommandations Stratégiques
- Actions prioritaires
- Scénarios probables
- Conseils opérationnels

## 🎯 Conclusion
Synthèse et perspectives

ANALYSE À EFFECTUER:
`,
      economique: `
SYSTEM: Tu es un analyste économique senior. Produis une analyse macroéconomique.

RAPPORT ÉCONOMIQUE - Template:
# Analyse Économique

## 📈 Indicateurs Clés
{data_summary}

## 💹 Tendances Marchés
- Dynamiques sectorielles
- Indicateurs financiers
- Perspectives de croissance

## 🏛️ Politiques Économiques
- Impacts des décisions
- Environnement réglementaire
- Recommandations politiques

## 🎯 Prévisions
- Scénarios à court/moyen terme
- Risques identifiés
- Opportunités
`
    };
  }

  async generateReport(reportType, dataContext, userPrompt = "") {
    if (!this.enabled) {
      throw new Error("Assistant Llama désactivé");
    }

    try {
      // Préparer les données pour l'analyse
      const dataSummary = await this.prepareDataSummary(dataContext);
      
      // Construire le prompt final
      const template = this.reportTemplates[reportType] || this.reportTemplates.geopolitique;
      const prompt = template.replace('{data_summary}', dataSummary) + userPrompt;

      console.log('🦙 Envoi à Llama:', prompt.substring(0, 200) + '...');

      // Appel à llama.cpp
      const analysis = await this.queryLlama(prompt);
      
      // Génération du PDF
      const pdfUrl = await this.generatePDF(analysis, reportType);
      
      return {
        success: true,
        analysis: analysis,
        pdfUrl: pdfUrl,
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      console.error('❌ Erreur génération rapport:', error);
      return {
        success: false,
        error: error.message,
        fallback: "Service Llama indisponible - Utilisez l'analyse standard"
      };
    }
  }

  async prepareDataSummary(dataContext) {
    // Récupérer les données statistiques pour l'IA
    const stats = await this.fetchAnalyticsData();
    
    return `
Articles analysés: ${stats.total_articles}
Période: ${stats.period}
Distribution des sentiments: 
- Positif: ${stats.sentiment.positive}
- Négatif: ${stats.sentiment.negative} 
- Neutre: ${stats.sentiment.neutral}

Thèmes principaux: ${stats.top_themes.join(', ')}

Contexte utilisateur: ${dataContext}
`;
  }

  async queryLlama(prompt) {
    const response = await fetch(`${this.endpoint}/v1/chat/completions`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': 'Bearer votre-cle-api' // Si nécessaire
      },
      body: JSON.stringify({
        model: "llama3.2-3b-Q4_K_M", // Votre modèle exact
        messages: [
          { 
            role: "system", 
            content: "Tu es un expert en analyses géopolitiques. Tes réponses doivent être structurées, factuelles et professionnelles." 
          },
          { role: "user", content: prompt }
        ],
        temperature: 0.5,
        max_tokens: 2000,
        stream: false
      }),
      timeout: 60000 // 60 secondes timeout
    });

    if (!response.ok) {
      throw new Error(`Llama.cpp error: ${response.status}`);
    }

    const data = await response.json();
    return data.choices[0]?.message?.content || "Aucune analyse générée";
  }

  async generatePDF(analysis, reportType) {
    // Utiliser une librairie côté serveur pour générer le PDF
    // Pour l'instant, retourner un faux URL
    return await this.callPDFGenerationAPI(analysis, reportType);
  }

  async callPDFGenerationAPI(content, reportType) {
    // Appel à votre route Flask pour générer le PDF
    const response = await fetch('/api/generate-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: content,
        title: `Rapport ${reportType}`,
        type: reportType
      })
    });
    
    const data = await response.json();
    return data.pdf_url;
  }

  async fetchAnalyticsData() {
    // Récupérer les données actuelles pour l'analyse
    const response = await fetch('/api/stats');
    const data = await response.json();
    
    return {
      total_articles: data.total_articles,
      period: '7 derniers jours',
      sentiment: data.sentiment_distribution,
      top_themes: Object.keys(data.theme_stats || {}).slice(0, 5)
    };
  }

  // Méthode pour tester la connexion
  async testConnection() {
    try {
      const response = await fetch(`${this.endpoint}/health`);
      return response.ok;
    } catch (error) {
      return false;
    }
  }
}

// Initialisation globale
window.LlamaAssistant = new LlamaAssistant();
console.log('✅ LlamaAssistant initialisé');