// static/js/advanced-analysis.js - Analyse avancée (IA + Cartographie Narrative)

class AdvancedAnalysisManager {
    static async showAnalysisPanel() {
        const content = document.getElementById('themeManagerContent');
        const title = document.getElementById('modalTitle');

        if (!content || !title) return;

        title.textContent = '🔬 Analyse Avancée';

        // Appliquer la correction MAJ 28/11 
        content.className = 'p-6 overflow-y-auto flex-1 modal-form-container';

        content.innerHTML = `
        <div class="max-w-6xl mx-auto space-y-6 modal-form-container">
                <!-- En-tête explicatif -->
                <div class="bg-gradient-to-r from-purple-50 to-blue-50 border-l-4 border-purple-500 p-4 rounded-lg">
                    <div class="flex items-start">
                        <div class="flex-shrink-0">
                            <i class="fas fa-info-circle text-purple-500 text-2xl"></i>
                        </div>
                        <div class="ml-3">
                            <h3 class="text-lg font-semibold text-gray-800">Analyse Avancée Automatisée</h3>
                            <p class="mt-2 text-sm text-gray-600">
                                Les outils d'analyse avancée sont désormais intégrés au traitement automatique des articles.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- CADRE EXPLICATIF - Analyse automatique -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Analyse Bayésienne Automatique -->
                    <div class="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg shadow-md p-6 border-2 border-indigo-200">
                        <div class="flex items-center mb-4">
                            <div class="bg-indigo-500 p-3 rounded-full mr-4">
                                <i class="fas fa-brain text-white text-2xl"></i>
                            </div>
                            <h3 class="text-xl font-bold text-gray-800">
                                Analyse Bayésienne
                            </h3>
                        </div>
                        <div class="space-y-3">
                            <div class="bg-white bg-opacity-70 rounded-lg p-4">
                                <div class="flex items-start">
                                    <i class="fas fa-check-circle text-green-500 mt-1 mr-3"></i>
                                    <div>
                                        <p class="font-semibold text-gray-800 text-sm">Traitement Automatique</p>
                                        <p class="text-gray-600 text-xs mt-1">
                                            Effectuée automatiquement par RoBERTa lors de l'analyse des articles
                                        </p>
                                    </div>
                                </div>
                            </div>
                            <div class="bg-white bg-opacity-70 rounded-lg p-4">
                                <div class="flex items-start">
                                    <i class="fas fa-layer-group text-blue-500 mt-1 mr-3"></i>
                                    <div>
                                        <p class="font-semibold text-gray-800 text-sm">Traitement par Lots</p>
                                        <p class="text-gray-600 text-xs mt-1">
                                            Les articles sont analysés par paquets de 5 pour optimiser la précision
                                        </p>
                                    </div>
                                </div>
                            </div>
                            <div class="bg-white bg-opacity-70 rounded-lg p-4">
                                <div class="flex items-start">
                                    <i class="fas fa-chart-line text-purple-500 mt-1 mr-3"></i>
                                    <div>
                                        <p class="font-semibold text-gray-800 text-sm">Score de Confiance</p>
                                        <p class="text-gray-600 text-xs mt-1">
                                            Calcul automatique de la confiance bayésienne pour chaque sentiment
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Corroboration Automatique -->
                    <div class="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg shadow-md p-6 border-2 border-blue-200">
                        <div class="flex items-center mb-4">
                            <div class="bg-blue-500 p-3 rounded-full mr-4">
                                <i class="fas fa-network-wired text-white text-2xl"></i>
                            </div>
                            <h3 class="text-xl font-bold text-gray-800">
                                Corroboration
                            </h3>
                        </div>
                        <div class="space-y-3">
                            <div class="bg-white bg-opacity-70 rounded-lg p-4">
                                <div class="flex items-start">
                                    <i class="fas fa-check-circle text-green-500 mt-1 mr-3"></i>
                                    <div>
                                        <p class="font-semibold text-gray-800 text-sm">Détection Automatique</p>
                                        <p class="text-gray-600 text-xs mt-1">
                                            Identification automatique des articles similaires et corroborants
                                        </p>
                                    </div>
                                </div>
                            </div>
                            <div class="bg-white bg-opacity-70 rounded-lg p-4">
                                <div class="flex items-start">
                                    <i class="fas fa-link text-cyan-500 mt-1 mr-3"></i>
                                    <div>
                                        <p class="font-semibold text-gray-800 text-sm">Relations Thématiques</p>
                                        <p class="text-gray-600 text-xs mt-1">
                                            Calcul de similarité et identification des liens narratifs
                                        </p>
                                    </div>
                                </div>
                            </div>
                            <div class="bg-white bg-opacity-70 rounded-lg p-4">
                                <div class="flex items-start">
                                    <i class="fas fa-database text-blue-500 mt-1 mr-3"></i>
                                    <div>
                                        <p class="font-semibold text-gray-800 text-sm">Stockage Intégré</p>
                                        <p class="text-gray-600 text-xs mt-1">
                                            Les résultats sont sauvegardés automatiquement dans la base de données
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Note technique -->
                <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div class="flex items-start">
                        <i class="fas fa-lightbulb text-yellow-500 text-xl mr-3 mt-1"></i>
                        <div>
                            <p class="font-semibold text-gray-800 text-sm mb-2">💡 Information Technique</p>
                            <p class="text-gray-600 text-xs leading-relaxed">
                                L'analyse bayésienne et la corroboration sont désormais des processus intégrés au pipeline 
                                de traitement RoBERTa. Elles s'exécutent automatiquement lors de l'import des flux RSS, 
                                garantissant une analyse complète et cohérente de tous les articles sans intervention manuelle.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- CARTOGRAPHIE NARRATIVE - Section mise en évidence -->

    <div class="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl shadow-2xl p-8 text-white transform hover:scale-[1.02] transition-transform duration-300">
        <div class="flex items-center justify-between mb-6">
            <div class="flex items-center space-x-4">
                <div class="bg-white bg-opacity-20 p-4 rounded-full backdrop-blur-sm">
                    <i class="fas fa-globe-europe text-4xl"></i>
                </div>
                <div>
                    <h3 class="text-2xl font-bold mb-2">
                        🌍 Cartographie Narrative
                    </h3>
                    <p class="text-blue-100 text-sm">
                        Visualisation géopolitique avancée des narratifs transnationaux
                    </p>
                </div>
            </div>
            <div class="bg-yellow-400 text-yellow-900 px-3 py-1 rounded-full text-xs font-bold">
                OPÉRATIONNEL
            </div>
        </div>

        <p class="text-blue-50 mb-6 leading-relaxed">
            Explorez les interconnexions narratives entre les articles,
            analysez les tendances géopolitiques et découvrez les relations
            thématiques dans un environnement cartographique interactif.
        </p>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div class="bg-white bg-opacity-10 rounded-lg p-4 backdrop-blur-sm">
                <i class="fas fa-project-diagram text-2xl mb-2"></i>
                <p class="text-sm font-semibold">Graphes Relationnels</p>
            </div>
            <div class="bg-white bg-opacity-10 rounded-lg p-4 backdrop-blur-sm">
                <i class="fas fa-map-marked-alt text-2xl mb-2"></i>
                <p class="text-sm font-semibold">Visualisation Spatiale</p>
            </div>
            <div class="bg-white bg-opacity-10 rounded-lg p-4 backdrop-blur-sm">
                <i class="fas fa-brain text-2xl mb-2"></i>
                <p class="text-sm font-semibold">Analyse Sémantique</p>
            </div>
        </div>

        <button onclick="GeoNarrativeManager.showCartographieNarrative()"
                class="w-full bg-white text-indigo-700 px-8 py-4 rounded-lg font-bold text-lg hover:bg-blue-50 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1 flex items-center justify-center space-x-3">
            <i class="fas fa-rocket text-xl"></i>
            <span>Lancer la Cartographie Narrative</span>
            <i class="fas fa-arrow-right"></i>
        </button>
    </div>

                <!-- SECTION IA LOCALE POUR RAPPORTS -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h3 class="text-xl font-bold text-gray-800 mb-4">
                        <i class="fas fa-robot text-orange-500 mr-2"></i>
                        Analyse IA Locale (Llama 3.2)
                    </h3>
                    <p class="text-gray-600 mb-4 text-sm">
                        Génération de rapports d'analyse géopolitique avec l'IA locale
                    </p>
                    
                    <div class="space-y-4">
                        <!-- Sélection du type de rapport -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                Type de rapport
                            </label>
                            <select id="reportType" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500">
                                <option value="geopolitique">Analyse Géopolitique</option>
                                <option value="economique">Analyse Économique</option>
                                <option value="securite">Analyse Sécurité</option>
                                <option value="synthese">Synthèse Hebdomadaire</option>
                            </select>
                        </div>

                        <!-- Période d'analyse -->
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    Date de début
                                </label>
                                <input type="date" id="startDate" class="w-full p-2 border border-gray-300 rounded-lg">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">
                                    Date de fin
                                </label>
                                <input type="date" id="endDate" class="w-full p-2 border border-gray-300 rounded-lg">
                            </div>
                        </div>

                        <!-- Thèmes à inclure -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">
                                Thèmes à analyser
                            </label>
                            <div id="themeSelection" class="space-y-2 max-h-32 overflow-y-auto border border-gray-300 rounded-lg p-3">
                                <!-- Les thèmes seront chargés dynamiquement -->
                                <div class="text-center text-gray-500 py-4">
                                    <i class="fas fa-spinner fa-spin mr-2"></i>
                                    Chargement des thèmes...
                                </div>
                            </div>
                        </div>

                        <!-- Options avancées -->
                        <div class="bg-gray-50 p-4 rounded-lg">
                            <label class="flex items-center">
                                <input type="checkbox" id="includeSentiment" checked class="rounded border-gray-300 text-orange-600 focus:ring-orange-500">
                                <span class="ml-2 text-sm text-gray-700">Inclure l'analyse des sentiments</span>
                            </label>
                            <label class="flex items-center mt-2">
                                <input type="checkbox" id="includeSources" checked class="rounded border-gray-300 text-orange-600 focus:ring-orange-500">
                                <span class="ml-2 text-sm text-gray-700">Inclure les sources</span>
                            </label>
                            <label class="flex items-center mt-2">
                                <input type="checkbox" id="generatePDF" checked class="rounded border-gray-300 text-orange-600 focus:ring-orange-500">
                                <span class="ml-2 text-sm text-gray-700">Générer un PDF</span>
                            </label>
                        </div>

                        <!-- Bouton de génération -->
                        <button onclick="AdvancedAnalysisManager.generateIAReport()"
                                id="generateReportBtn"
                                class="w-full bg-blue-600 text-red px-4 py-3 rounded-lg hover:bg-blue-700 transition duration-200 font-semibold">
                            <i class="fas fa-magic mr-2"></i>Générer le rapport IA
                        </button>

                        <!-- Résultats de l'IA -->
                        <div id="iaReportResult" class="mt-4"></div>
                    </div>
                </div>

                <!-- Historique des analyses -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h3 class="text-xl font-bold text-gray-800 mb-4">
                        <i class="fas fa-history text-gray-600 mr-2"></i>
                        Articles avec analyse avancée
                    </h3>
                    <div id="analyzedArticlesList" class="space-y-3">
                        <div class="text-center py-4 text-gray-500">
                            <i class="fas fa-spinner fa-spin text-xl mb-2"></i>
                            <p>Chargement...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        ModalManager.showModal('themeManagerModal');
        this.loadAnalyzedArticles();
        this.loadThemesForIA();
    }

    static async loadThemesForIA() {
        const container = document.getElementById('themeSelection');
        if (!container) return;

        try {
            const response = await fetch('/api/themes');
            const data = await response.json();

            if (data.themes && data.themes.length > 0) {
                container.innerHTML = data.themes.map(theme => `
                    <label class="flex items-center">
                        <input type="checkbox" value="${theme.id}" checked 
                               class="theme-checkbox rounded border-gray-300 text-orange-600 focus:ring-orange-500">
                        <span class="ml-2 text-sm text-gray-700">${theme.name}</span>
                    </label>
                `).join('');
            } else {
                container.innerHTML = '<p class="text-gray-500 text-sm">Aucun thème disponible</p>';
            }
        } catch (error) {
            container.innerHTML = '<p class="text-red-500 text-sm">Erreur de chargement des thèmes</p>';
        }
    }

    static async generateIAReport() {
        const btn = document.getElementById('generateReportBtn');
        const resultDiv = document.getElementById('iaReportResult');

        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Génération en cours...';
        resultDiv.innerHTML = '<div class="text-blue-600 text-sm">📄 L\'IA analyse les articles et génère le rapport...</div>';

        try {
            const reportType = document.getElementById('reportType').value;
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            const includeSentiment = document.getElementById('includeSentiment').checked;
            const includeSources = document.getElementById('includeSources').checked;
            const generatePDF = document.getElementById('generatePDF').checked;

            const selectedThemes = Array.from(document.querySelectorAll('.theme-checkbox:checked'))
                .map(cb => cb.value);

            const requestData = {
                report_type: reportType,
                start_date: startDate,
                end_date: endDate,
                themes: selectedThemes,
                include_sentiment: includeSentiment,
                include_sources: includeSources,
                generate_pdf: generatePDF
            };

            const response = await fetch('/api/generate-ia-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            const data = await response.json();

            if (data.success) {
                this.displayIAReportResults(data, resultDiv, generatePDF);
            } else {
                resultDiv.innerHTML = `
                    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                        <p class="text-red-800 font-semibold">❌ Erreur lors de la génération</p>
                        <p class="text-red-600 text-sm mt-1">${data.error || 'Erreur inconnue'}</p>
                    </div>
                `;
            }

        } catch (error) {
            resultDiv.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                    <p class="text-red-800 font-semibold">❌ Erreur réseau</p>
                    <p class="text-red-600 text-sm mt-1">${error.message}</p>
                </div>
            `;
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-magic mr-2"></i>Générer le rapport IA';
        }
    }

    static displayIAReportResults(data, container, generatePDF) {
        let pdfSection = '';

        if (generatePDF && data.analysis_html) {
            // Échapper le HTML pour le passer en paramètre JS de manière sécurisée
            const safeHtml = data.analysis_html
                .replace(/\\/g, '\\\\')  // Échapper les backslashes
                .replace(/`/g, '\\`')    // Échapper les backticks
                .replace(/\$/g, '\\$')   // Échapper les dollars
                .replace(/'/g, "\\'")    // Échapper les apostrophes
                .replace(/"/g, '\\"');   // Échapper les guillemets

            pdfSection = `
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 class="font-semibold text-blue-800 mb-2">📄 Générer le PDF</h4>
            <p class="text-blue-600 text-sm mb-3">Cliquez pour générer et télécharger le rapport PDF.</p>
            <button id="pdfGenerateBtn" 
                    class="inline-flex items-center bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition duration-200">
                <i class="fas fa-download mr-2"></i>Générer le PDF
            </button>
        </div>
        `;
        }

        container.innerHTML = `
        <div class="space-y-4">
            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                <p class="text-green-800 font-semibold">✅ Rapport généré avec succès !</p>
            </div>
            
            <div class="bg-white border border-gray-200 rounded-lg p-4">
                <h4 class="font-semibold text-gray-800 mb-3">📋 Résumé du rapport</h4>
                <div class="space-y-2 text-sm">
                    <p><strong>Type:</strong> ${data.report_type}</p>
                    <p><strong>Articles analysés:</strong> ${data.articles_analyzed}</p>
                    <p><strong>Thèmes couverts:</strong> ${data.themes_covered?.join(', ') || 'Tous'}</p>
                    <p><strong>Période:</strong> ${data.period}</p>
                    ${data.llama_status ? `
                        <p><strong>Mode:</strong> 
                            <span class="px-2 py-1 rounded text-xs ${data.llama_status.success ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                                ${data.llama_status.mode}
                            </span>
                        </p>
                    ` : ''}
                </div>
            </div>

            <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 class="font-semibold text-gray-800 mb-3">🧠 Analyse IA</h4>
                <div class="prose prose-sm max-w-none" id="analysisContent">
                    ${data.analysis_html || '<p class="text-gray-600">Aucune analyse disponible</p>'}
                </div>
            </div>

            ${pdfSection}
        </div>
    `;

        // Attacher l'événement au bouton PDF après injection du HTML
        if (generatePDF && data.analysis_html) {
            setTimeout(() => {
                const pdfBtn = document.getElementById('pdfGenerateBtn');
                if (pdfBtn) {
                    pdfBtn.addEventListener('click', () => {
                        AdvancedAnalysisManager.generatePDFFromAnalysis(data.report_type, data.analysis_html);
                    });
                }
            }, 100);
        }
    }

    static async generatePDFFromAnalysis(reportType, htmlContent) {
        try {
            const response = await fetch('/api/generate-pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    html_content: htmlContent,
                    title: `Rapport ${reportType}`,
                    type: reportType
                })
            });

            if (response.ok) {
                // Télécharger le PDF
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `rapport_${reportType}_${new Date().toISOString().slice(0, 10)}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            } else {
                const errorData = await response.json();
                alert('Erreur lors de la génération du PDF: ' + (errorData.error || 'Erreur inconnue'));
            }
        } catch (error) {
            console.error('Erreur génération PDF:', error);
            alert('Erreur lors de la génération du PDF: ' + error.message);
        }
    }

    static async loadAnalyzedArticles() {
        const container = document.getElementById('analyzedArticlesList');
        if (!container) return;

        try {
            const response = await fetch('/api/analyzed-articles?limit=30');
            const articles = await response.json();

            if (articles && articles.length > 0) {
                container.innerHTML = articles.map(article => `
                    <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 hover:bg-gray-100 transition-colors">
                        <div class="flex justify-between items-start mb-2">
                            <h4 class="font-semibold text-gray-800 text-sm flex-1">${article.title}</h4>
                            <span class="text-xs text-gray-500 ml-2">${new Date(article.pub_date).toLocaleDateString('fr-FR')}</span>
                        </div>
                        <p class="text-gray-600 text-xs mb-3">${article.content}</p>
                        <div class="flex items-center justify-between text-xs">
                            <div class="flex items-center space-x-3">
                                <span class="px-2 py-1 rounded ${this.getSentimentBadge(article.sentiment_type)}">
                                    ${article.sentiment_type || 'neutral'}
                                </span>
                                ${article.bayesian_confidence ? `
                                    <span class="text-purple-600">
                                        <i class="fas fa-brain mr-1"></i>
                                        Confiance: ${(article.bayesian_confidence * 100).toFixed(1)}%
                                    </span>
                                ` : ''}
                                ${article.corroboration_count > 0 ? `
                                    <span class="text-blue-600">
                                        <i class="fas fa-link mr-1"></i>
                                        ${article.corroboration_count} corroboration(s)
                                    </span>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `).join('');
            } else {
                container.innerHTML = `
                    <div class="text-center py-8 text-gray-500">
                        <i class="fas fa-inbox text-3xl mb-3"></i>
                        <p>Aucun article analysé pour le moment</p>
                        <p class="text-xs mt-2">Les articles seront affichés ici après analyse</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Erreur chargement articles analysés:', error);
            container.innerHTML = `
                <div class="text-center py-8 text-red-500">
                    <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                    <p>Erreur lors du chargement</p>
                </div>
            `;
        }
    }

    static getSentimentBadge(sentiment) {
        switch (sentiment) {
            case 'positive': return 'bg-green-100 text-green-800';
            case 'negative': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }

    static showAlert(container, message, type = 'info') {
        const colors = {
            success: 'green',
            error: 'red',
            info: 'blue'
        };
        const color = colors[type] || 'blue';

        container.innerHTML = `
            <div class="mt-3 bg-${color}-50 border border-${color}-200 rounded-lg p-3 text-sm">
                <p class="text-${color}-800">${message}</p>
            </div>
        `;
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    window.AdvancedAnalysisManager = AdvancedAnalysisManager;
    console.log('✅ AdvancedAnalysisManager initialisé avec Cartographie Narrative');
});