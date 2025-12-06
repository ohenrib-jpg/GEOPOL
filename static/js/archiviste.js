// static/js/archiviste.js - Interface Archiviste

class ArchivisteManager {
    static async showArchivistePanel() {
        const content = document.getElementById('themeManagerContent');
        const title = document.getElementById('modalTitle');

        if (!content || !title) return;

        title.textContent = '📚 Archiviste - Analyse Historique';

        content.innerHTML = `
            <div class="max-w-6xl mx-auto space-y-6">
                <!-- En-tête explicatif -->
                <div class="bg-gradient-to-r from-amber-50 to-orange-50 border-l-4 border-amber-500 p-4 rounded-lg">
                    <div class="flex items-start">
                        <div class="flex-shrink-0">
                            <i class="fas fa-archive text-amber-500 text-2xl"></i>
                        </div>
                        <div class="ml-3">
                            <h3 class="text-lg font-semibold text-gray-800">Analyse Historique depuis 1945</h3>
                            <p class="mt-2 text-sm text-gray-600">
                                Comparez les tendances émotionnelles et thématiques actuelles avec celles du passé.
                                Découvrez l'évolution des mentalités sur 80 ans d'histoire.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Actions principales -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div class="bg-white rounded-lg shadow-md p-4">
                        <h4 class="font-bold text-gray-800 mb-2">
                            <i class="fas fa-search text-amber-600 mr-2"></i>Analyse de Période
                        </h4>
                        <p class="text-sm text-gray-600 mb-3">Analyser une période historique spécifique</p>
                        <button onclick="ArchivisteManager.showPeriodAnalysis()" 
                                class="w-full bg-amber-600 text-white px-3 py-2 rounded hover:bg-amber-700 text-sm">
                            Lancer l'analyse
                        </button>
                    </div>

                    <div class="bg-white rounded-lg shadow-md p-4">
                        <h4 class="font-bold text-gray-800 mb-2">
                            <i class="fas fa-balance-scale text-orange-600 mr-2"></i>Comparaison Temporelle
                        </h4>
                        <p class="text-sm text-gray-600 mb-3">Comparer maintenant avec le passé</p>
                        <button onclick="ArchivisteManager.compareWithHistory()" 
                                class="w-full bg-orange-600 text-white px-3 py-2 rounded hover:bg-orange-700 text-sm">
                            Comparer maintenant
                        </button>
                    </div>

                    <div class="bg-white rounded-lg shadow-md p-4">
                        <h4 class="font-bold text-gray-800 mb-2">
                            <i class="fas fa-chart-line text-red-600 mr-2"></i>Évolution des Tendances
                        </h4>
                        <p class="text-sm text-gray-600 mb-3">Voir l'évolution des tendances</p>
                        <button onclick="ArchivisteManager.showTrendsEvolution()" 
                                class="w-full bg-red-600 text-white px-3 py-2 rounded hover:bg-red-700 text-sm">
                            Voir l'évolution
                        </button>
                    </div>
                </div>

                <!-- Résultats -->
                <div id="archivisteResults" class="space-y-4">
                    <div class="text-center py-8 text-gray-500">
                        <i class="fas fa-archive text-3xl mb-3"></i>
                        <p>Archiviste prêt</p>
                        <p class="text-sm mt-2">Choisissez une action pour commencer</p>
                    </div>
                </div>

                <!-- Informations sur Archive.org -->
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div class="flex items-center">
                        <i class="fas fa-info-circle text-blue-600 mr-3"></i>
                        <div>
                            <h5 class="font-semibold text-blue-800">Données Source</h5>
                            <p class="text-sm text-blue-600">
                                Les analyses sont basées sur les archives de 
                                <a href="https://archive.org" target="_blank" class="underline">Archive.org</a>
                                incluant journaux, magazines et livres depuis 1945.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        ModalManager.showModal('themeManagerModal');
        this.loadHistoricalAnalyses();
    }

    static async showPeriodAnalysis() {
        const content = document.getElementById('archivisteResults');
        content.innerHTML = `
            <div class="bg-white rounded-lg border p-6">
                <h4 class="font-bold text-gray-800 mb-4">
                    <i class="fas fa-search text-amber-600 mr-2"></i>
                    Analyse de Période Historique
                </h4>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Période historique</label>
                        <select id="historicalPeriod" class="w-full p-2 border border-gray-300 rounded-lg">
                            <option value="">Sélectionnez une période</option>
                        </select>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">Thème d'analyse (optionnel)</label>
                        <select id="analysisTheme" class="w-full p-2 border border-gray-300 rounded-lg">
                            <option value="">Tous les thèmes</option>
                        </select>
                    </div>
                </div>
                
                <div class="flex space-x-3">
                    <button onclick="ArchivisteManager.launchPeriodAnalysis()" 
                            id="launchAnalysisBtn"
                            class="bg-amber-600 text-white px-4 py-2 rounded hover:bg-amber-700">
                            Lancer l'analyse
                    </button>
                    <button onclick="ArchivisteManager.loadPeriodOptions()" 
                            class="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600">
                            Charger les options
                    </button>
                </div>
            </div>
        `;

        await this.loadPeriodOptions();
    }

    static async loadPeriodOptions() {
        try {
            const response = await fetch('/api/archiviste/periods');
            const data = await response.json();

            if (data.success) {
                const periodSelect = document.getElementById('historicalPeriod');
                const themeSelect = document.getElementById('analysisTheme');

                // Remplir les périodes
                periodSelect.innerHTML = '<option value="">Sélectionnez une période</option>';
                Object.entries(data.periods).forEach(([key, period]) => {
                    const option = document.createElement('option');
                    option.value = key;
                    option.textContent = `${period.name} (${period.start.slice(0,4)}-${period.end.slice(0,4)})`;
                    periodSelect.appendChild(option);
                });

                // Remplir les thèmes
                themeSelect.innerHTML = '<option value="">Tous les thèmes</option>';
                data.themes.forEach(theme => {
                    const option = document.createElement('option');
                    option.value = theme;
                    option.textContent = theme.charAt(0).toUpperCase() + theme.slice(1);
                    themeSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Erreur chargement options:', error);
        }
    }

    static async launchPeriodAnalysis() {
        const periodKey = document.getElementById('historicalPeriod').value;
        const theme = document.getElementById('analysisTheme').value;

        if (!periodKey) {
            alert('Veuillez sélectionner une période');
            return;
        }

        const btn = document.getElementById('launchAnalysisBtn');
        const resultsDiv = document.getElementById('archivisteResults');

        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyse en cours...';
        resultsDiv.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin text-amber-600 text-xl"></i></div>';

        try {
            const response = await fetch('/api/archiviste/analyze-period', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    period_key: periodKey,
                    theme: theme || null,
                    max_items: 50
                })
            });

            const data = await response.json();

            if (data.success) {
                this.displayPeriodAnalysis(data, resultsDiv);
            } else {
                this.showError(resultsDiv, data.error || 'Erreur lors de l\'analyse');
            }

        } catch (error) {
            this.showError(resultsDiv, 'Erreur réseau: ' + error.message);
        } finally {
            btn.disabled = false;
            btn.innerHTML = 'Lancer l\'analyse';
        }
    }

    static displayPeriodAnalysis(data, container) {
        const stats = data.statistics;
        const period = data.period;
        const items = data.top_items || [];

        const intensityClass = this.getIntensityClass(stats.emotional_intensity);
        const intensityIcon = this.getIntensityIcon(stats.emotional_intensity);

        let html = `
            <div class="bg-white rounded-lg border">
                <div class="p-4 border-b">
                    <h4 class="font-bold text-gray-800">
                        <i class="fas fa-archive text-amber-600 mr-2"></i>
                        Analyse de la ${period.name}
                    </h4>
                    <p class="text-sm text-gray-600">
                        ${period.start} à ${period.end} • ${data.items_analyzed} articles analysés
                    </p>
                </div>
                
                <div class="p-4 space-y-4">
                    <!-- Intensité émotionnelle -->
                    <div class="bg-gradient-to-r from-amber-50 to-orange-50 border-l-4 border-amber-500 p-4 rounded">
                        <div class="flex items-center justify-between">
                            <div>
                                <h5 class="font-bold text-lg text-gray-800">Intensité Émotionnelle</h5>
                                <p class="text-sm text-gray-600">${this.getIntensityDescription(stats.emotional_intensity)}</p>
                            </div>
                            <div class="text-right">
                                <div class="text-2xl font-bold ${intensityClass}">
                                    <i class="fas ${intensityIcon}"></i>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Statistiques de sentiment -->
                    <div class="grid grid-cols-3 gap-4">
                        <div class="bg-green-50 p-3 rounded text-center">
                            <div class="text-2xl font-bold text-green-600">${stats.sentiment_distribution.positive}</div>
                            <div class="text-sm text-green-600">Positifs (${stats.sentiment_distribution.positive_percent}%)</div>
                        </div>
                        <div class="bg-red-50 p-3 rounded text-center">
                            <div class="text-2xl font-bold text-red-600">${stats.sentiment_distribution.negative}</div>
                            <div class="text-sm text-red-600">Négatifs (${stats.sentiment_distribution.negative_percent}%)</div>
                        </div>
                        <div class="bg-gray-50 p-3 rounded text-center">
                            <div class="text-2xl font-bold text-gray-600">${stats.sentiment_distribution.neutral}</div>
                            <div class="text-sm text-gray-600">Neutres (${stats.sentiment_distribution.neutral_percent}%)</div>
                        </div>
                    </div>

                    <!-- Sentiment moyen -->
                    <div class="bg-blue-50 p-3 rounded">
                        <h6 class="font-semibold text-blue-800">Score de Sentiment Moyen</h6>
                        <p class="text-2xl font-bold text-blue-600">${stats.average_sentiment_score.toFixed(3)}</p>
                        <p class="text-sm text-blue-600">Échelle: -1 (très négatif) à +1 (très positif)</p>
                    </div>

                    <!-- Top thèmes -->
                    ${stats.top_themes && stats.top_themes.length > 0 ? `
                        <div class="bg-purple-50 p-3 rounded">
                            <h6 class="font-semibold text-purple-800 mb-2">Thèmes Principaux</h6>
                            <div class="space-y-1">
                                ${stats.top_themes.map((theme, index) => `
                                    <div class="flex justify-between text-sm">
                                        <span>${index + 1}. ${theme[0]}</span>
                                        <span class="text-purple-600">${theme[1]} articles</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Événements majeurs -->
                    ${stats.top_major_events && stats.top_major_events.length > 0 ? `
                        <div class="bg-yellow-50 p-3 rounded">
                            <h6 class="font-semibold text-yellow-800 mb-2">Événements Majeurs Détectés</h6>
                            <div class="flex flex-wrap gap-2">
                                ${stats.top_major_events.slice(0, 8).map(event => `
                                    <span class="text-xs px-2 py-1 bg-yellow-200 text-yellow-800 rounded">${event[0]}</span>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    static async compareWithHistory() {
        const resultsDiv = document.getElementById('archivisteResults');
        resultsDiv.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin text-orange-600 text-xl"></i></div>';

        try {
            // D'abord générer l'analyse actuelle
            const currentResponse = await fetch('/api/archiviste/current-analysis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ days: 30 })
            });

            const currentData = await currentResponse.json();

            if (!currentData.success) {
                throw new Error(currentData.error || 'Erreur génération analyse actuelle');
            }

            // Puis comparer avec l'historique
            const compareResponse = await fetch('/api/archiviste/compare-eras', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    current_analysis: currentData.current_analysis,
                    historical_periods: ['1990-2000', '2000-2010', '2010-2020', '2020-2025']
                })
            });

            const compareData = await compareResponse.json();

            if (compareData.success) {
                this.displayComparisonResults(compareData, resultsDiv);
            } else {
                this.showError(resultsDiv, compareData.error || 'Erreur lors de la comparaison');
            }

        } catch (error) {
            this.showError(resultsDiv, 'Erreur: ' + error.message);
        }
    }

    static displayComparisonResults(data, container) {
        const synthesis = data.synthesis;
        const comparisons = data.comparisons || [];

        const synthesisClass = this.getSynthesisClass(synthesis.dominant_evolution_pattern);
        const synthesisIcon = this.getSynthesisIcon(synthesis.dominant_evolution_pattern);

        let html = `
            <div class="bg-white rounded-lg border">
                <div class="p-4 border-b">
                    <h4 class="font-bold text-gray-800">
                        <i class="fas fa-balance-scale text-orange-600 mr-2"></i>
                        Comparaison Temporelle
                    </h4>
                    <p class="text-sm text-gray-600">
                        Comparaison avec ${synthesis.periods_analyzed} périodes historiques
                    </p>
                </div>
                
                <div class="p-4 space-y-4">
                    <!-- Synthèse principale -->
                    <div class="bg-gradient-to-r from-orange-50 to-red-50 border-l-4 border-orange-500 p-4 rounded">
                        <div class="flex items-center justify-between">
                            <div>
                                <h5 class="font-bold text-lg text-gray-800">Évolution Historique</h5>
                                <p class="text-sm text-gray-600">${synthesis.interpretation}</p>
                            </div>
                            <div class="text-right">
                                <div class="text-2xl font-bold ${synthesisClass}">
                                    <i class="fas ${synthesisIcon}"></i>
                                </div>
                                <div class="text-sm text-gray-500">Score: ${(synthesis.average_similarity_score * 100).toFixed(1)}%</div>
                            </div>
                        </div>
                    </div>

                    <!-- Métriques de comparaison -->
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-blue-50 p-3 rounded">
                            <h6 class="font-semibold text-blue-800">Score de Similarité</h6>
                            <p class="text-2xl font-bold text-blue-600">${(synthesis.average_similarity_score * 100).toFixed(1)}%</p>
                            <p class="text-sm text-blue-600">Résonance avec l'Histoire</p>
                        </div>
                        <div class="bg-green-50 p-3 rounded">
                            <h6 class="font-semibold text-green-800">Tendance Globale</h6>
                            <p class="text-xl font-bold text-green-600">${this.translateTrend(synthesis.overall_sentiment_trend)}</p>
                            <p class="text-sm text-green-600">Évolution du sentiment</p>
                        </div>
                    </div>

                    <!-- Comparaisons détaillées -->
                    <div class="space-y-3">
                        <h6 class="font-semibold text-gray-800">Comparaisons par Période</h6>
                        ${comparisons.map(comp => `
                            <div class="border border-gray-200 p-3 rounded">
                                <div class="flex justify-between items-start mb-2">
                                    <h6 class="font-medium text-gray-800">${comp.period_name}</h6>
                                    <span class="text-xs px-2 py-1 rounded ${this.getEvolutionClass(comp.evolution_type)}">
                                        ${this.translateEvolution(comp.evolution_type)}
                                    </span>
                                </div>
                                <div class="grid grid-cols-2 gap-2 text-sm">
                                    <div>
                                        <span class="text-gray-600">Différence sentiment:</span>
                                        <span class="font-medium">${comp.sentiment_comparison.difference > 0 ? '+' : ''}${comp.sentiment_comparison.difference.toFixed(3)}</span>
                                    </div>
                                    <div>
                                        <span class="text-gray-600">Similarité:</span>
                                        <span class="font-medium">${(comp.similarity_score * 100).toFixed(1)}%</span>
                                    </div>
                                </div>
                                <p class="text-xs text-gray-500 mt-1">${comp.sentiment_comparison.interpretation}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    static async showTrendsEvolution() {
        const resultsDiv = document.getElementById('archivisteResults');
        resultsDiv.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin text-red-600 text-xl"></i></div>';

        try {
            const response = await fetch('/api/archiviste/trends-evolution');
            const data = await response.json();

            if (data.success) {
                this.displayTrendsEvolution(data.trends, resultsDiv);
            } else {
                this.showError(resultsDiv, data.error || 'Erreur lors du chargement des tendances');
            }

        } catch (error) {
            this.showError(resultsDiv, 'Erreur réseau: ' + error.message);
        }
    }

    static displayTrendsEvolution(trends, container) {
        if (!trends || trends.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-chart-line text-3xl mb-3"></i>
                    <p>Aucune donnée d'évolution disponible</p>
                    <p class="text-sm mt-2">Effectuez d'abord des analyses historiques</p>
                </div>
            `;
            return;
        }

        // Trier par période
        trends.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

        const html = `
            <div class="bg-white rounded-lg border">
                <div class="p-4 border-b">
                    <h4 class="font-bold text-gray-800">
                        <i class="fas fa-chart-line text-red-600 mr-2"></i>
                        Évolution des Tendances
                    </h4>
                    <p class="text-sm text-gray-600">${trends.length} analyses historiques</p>
                </div>
                
                <div class="p-4">
                    <div class="space-y-4">
                        ${trends.map((trend, index) => `
                            <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                                <div class="flex-1">
                                    <h6 class="font-medium text-gray-800">${trend.period_name}</h6>
                                    <p class="text-sm text-gray-600">${trend.total_items} articles • Intensité: ${trend.emotional_intensity}</p>
                                </div>
                                <div class="text-right">
                                    <div class="text-lg font-bold ${this.getSentimentColor(trend.avg_sentiment_score)}">
                                        ${trend.avg_sentiment_score.toFixed(3)}
                                    </div>
                                    <div class="text-xs text-gray-500">${new Date(trend.created_at).toLocaleDateString()}</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    static async loadHistoricalAnalyses() {
        try {
            const response = await fetch('/api/archiviste/analyses-history?limit=5');
            const data = await response.json();

            if (data.success && data.analyses.length > 0) {
                console.log('📚 Analyses historiques chargées:', data.analyses.length);
            }
        } catch (error) {
            console.error('Erreur chargement analyses historiques:', error);
        }
    }

    // Utilitaires
    static getIntensityClass(intensity) {
        switch (intensity) {
            case 'highly_emotional': return 'text-red-600';
            case 'moderately_emotional': return 'text-orange-600';
            case 'slightly_emotional': return 'text-yellow-600';
            default: return 'text-gray-600';
        }
    }

    static getIntensityIcon(intensity) {
        switch (intensity) {
            case 'highly_emotional': return 'fa-exclamation-triangle';
            case 'moderately_emotional': return 'fa-fire';
            case 'slightly_emotional': return 'fa-heart';
            default: return 'fa-minus';
        }
    }

    static getIntensityDescription(intensity) {
        switch (intensity) {
            case 'highly_emotional': return 'Période très polarisée';
            case 'moderately_emotional': return 'Intensité émotionnelle modérée';
            case 'slightly_emotional': return 'Légèrement polarisée';
            default: return 'Neutre';
        }
    }

    static getSynthesisClass(pattern) {
        switch (pattern) {
            case 'major_shift': return 'text-red-600';
            case 'moderate_change': return 'text-orange-600';
            case 'intensity_change': return 'text-yellow-600';
            default: return 'text-green-600';
        }
    }

    static getSynthesisIcon(pattern) {
        switch (pattern) {
            case 'major_shift': return 'fa-exclamation-triangle';
            case 'moderate_change': return 'fa-arrows-alt';
            case 'intensity_change': return 'fa-adjust';
            default: return 'fa-check';
        }
    }

    static getEvolutionClass(type) {
        switch (type) {
            case 'major_shift': return 'bg-red-100 text-red-800';
            case 'moderate_change': return 'bg-orange-100 text-orange-800';
            case 'intensity_change': return 'bg-yellow-100 text-yellow-800';
            default: return 'bg-green-100 text-green-800';
        }
    }

    static getSentimentColor(score) {
        if (score > 0.1) return 'text-green-600';
        if (score < -0.1) return 'text-red-600';
        return 'text-gray-600';
    }

    static translateTrend(trend) {
        switch (trend) {
            case 'improving': return 'En amélioration';
            case 'declining': return 'En déclin';
            case 'mixed': return 'Mixte';
            case 'stable': return 'Stable';
            default: return 'Inconnu';
        }
    }

    static translateEvolution(evolution) {
        switch (evolution) {
            case 'major_shift': return 'Changement majeur';
            case 'moderate_change': return 'Changement modéré';
            case 'intensity_change': return 'Intensité';
            case 'stable': return 'Stable';
            default: return 'Inconnu';
        }
    }

    static showError(container, message) {
        container.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                <div class="flex items-center">
                    <i class="fas fa-exclamation-triangle text-red-600 mr-3"></i>
                    <div>
                        <p class="font-semibold text-red-800">Erreur</p>
                        <p class="text-sm text-red-600">${message}</p>
                    </div>
                </div>
            </div>
        `;
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    window.ArchivisteManager = ArchivisteManager;
    console.log('✅ ArchivisteManager initialisé');
});