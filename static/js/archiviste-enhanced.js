// static/js/archiviste-enhanced.js - VERSION AVEC ANALYSE COMPARATIVE
'use strict';

class EnhancedArchivisteManager {
    constructor() {
        this.initialized = false;
        this.periods = [];
        this.themes = [];
        this.isAnalyzing = false;
        this.init();
    }

    init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeComponents());
        } else {
            this.initializeComponents();
        }
    }

    initializeComponents() {
        if (this.initialized) return;
        this.setupEventListeners();
        this.loadInitialData();
        this.initialized = true;
    }

    setupEventListeners() {
        const analyzeBtn = document.getElementById('analyze-period-btn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.handleAnalyzeClick());
        }

        const periodSelect = document.getElementById('archiviste-period-select');
        const themeSelect = document.getElementById('archiviste-theme-select');

        if (periodSelect) {
            periodSelect.addEventListener('change', () => this.validateForm());
        }
        if (themeSelect) {
            themeSelect.addEventListener('change', () => this.validateForm());
        }
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadPeriods(),
                this.loadThemes(),
                this.loadStats()
            ]);
            this.validateForm();
        } catch (error) {
            console.error('Erreur chargement données initiales:', error);
        }
    }

    async loadPeriods() {
        try {
            const response = await this.apiCall('/archiviste/api/periods');
            if (response?.success && response.periods) {
                this.periods = Object.entries(response.periods).map(([key, period]) => ({
                    key,
                    ...period
                }));
                this.populatePeriodSelect();
                console.log('✅ Périodes chargées:', this.periods.length);
            }
        } catch (error) {
            console.warn('⚠️ Erreur chargement périodes:', error);
            this.loadPeriodsFallback();
        }
    }

    loadPeriodsFallback() {
        this.periods = [
            { key: '1945-1950', name: 'Après-guerre (1945-1950)' },
            { key: '1950-1960', name: 'Guerre froide débuts (1950-1960)' },
            { key: '1960-1970', name: 'Décolonisation (1960-1970)' },
            { key: '1970-1980', name: 'Détente (1970-1980)' },
            { key: '1980-1990', name: 'Fin guerre froide (1980-1990)' },
            { key: '1990-2000', name: 'Nouvel ordre mondial (1990-2000)' },
            { key: '2000-2010', name: 'Post-11/09 (2000-2010)' },
            { key: '2010-2020', name: 'Printemps arabes (2010-2020)' },
            { key: '2020-2025', name: 'Pandémie/IA (2020-2025)' }
        ];
        this.populatePeriodSelect();
    }

    populatePeriodSelect() {
        const select = document.getElementById('archiviste-period-select');
        if (!select) return;

        select.innerHTML = '<option value="">Sélectionnez une période...</option>';
        this.periods.forEach(period => {
            const option = document.createElement('option');
            option.value = period.key;
            option.textContent = period.name;
            select.appendChild(option);
        });
    }

    async loadThemes() {
        try {
            const response = await this.apiCall('/archiviste/api/themes');
            if (response?.success && response.themes) {
                this.themes = response.themes.map((theme, index) => {
                    let numericId;
                    if (typeof theme.id === 'number') {
                        numericId = theme.id;
                    } else if (typeof theme.id === 'string') {
                        const parsed = parseInt(theme.id);
                        numericId = isNaN(parsed) ? (index + 1) : parsed;
                    } else {
                        numericId = index + 1;
                    }

                    return {
                        id: numericId,
                        slug: theme.slug || theme.id,
                        name: theme.name,
                        keywords: theme.keywords || [],
                        description: theme.description || '',
                        color: theme.color || '#6366f1'
                    };
                });

                this.populateThemeSelect();
                console.log('✅ Thèmes chargés:', this.themes.length);
            }
        } catch (error) {
            console.warn('⚠️ Erreur chargement thèmes:', error);
            this.loadThemesFallback();
        }
    }

    loadThemesFallback() {
        this.themes = [
            { id: 1, name: 'Géopolitique', keywords: ['politique', 'international'] },
            { id: 2, name: 'Conflits', keywords: ['guerre', 'conflit'] },
            { id: 3, name: 'Économie', keywords: ['économie', 'commerce'] }
        ];
        this.populateThemeSelect();
    }

    populateThemeSelect() {
        const select = document.getElementById('archiviste-theme-select');
        if (!select) return;

        select.innerHTML = '<option value="">Sélectionnez un thème...</option>';
        this.themes.forEach(theme => {
            const option = document.createElement('option');
            option.value = theme.id;
            option.textContent = theme.name;
            select.appendChild(option);
        });
    }

    async loadStats() {
        try {
            const response = await this.apiCall('/archiviste/api/stats');
            if (response?.success) {
                this.displayStats(response.stats);
            }
        } catch (error) {
            console.warn('⚠️ Stats par défaut:', error);
        }
    }

    displayStats(stats) {
        const statsElement = document.getElementById('stats-content');
        if (!statsElement) return;

        statsElement.innerHTML = `
            <div class="grid grid-cols-2 gap-3">
                <div class="bg-blue-500/20 p-3 rounded-lg border border-blue-400/30">
                    <div class="text-xl font-bold text-blue-300">${stats.total_analyses || 0}</div>
                    <div class="text-sm text-blue-200">Analyses</div>
                </div>
                <div class="bg-green-500/20 p-3 rounded-lg border border-green-400/30">
                    <div class="text-xl font-bold text-green-300">${stats.total_archived_items || 0}</div>
                    <div class="text-sm text-green-200">Items archivés</div>
                </div>
            </div>
        `;
    }

    validateForm() {
        const period = document.getElementById('archiviste-period-select')?.value;
        const theme = document.getElementById('archiviste-theme-select')?.value;
        const analyzeBtn = document.getElementById('analyze-period-btn');

        if (analyzeBtn) {
            analyzeBtn.disabled = !(period && theme);
        }
    }

    handleAnalyzeClick() {
        if (this.isAnalyzing) return;

        const periodKey = document.getElementById('archiviste-period-select')?.value;
        const themeValue = document.getElementById('archiviste-theme-select')?.value;

        if (!periodKey || !themeValue) {
            this.displayError('Veuillez sélectionner une période et un thème');
            return;
        }

        const themeId = parseInt(themeValue);
        if (isNaN(themeId) || themeId <= 0) {
            this.displayError(`ID de thème invalide: ${themeValue}`);
            return;
        }

        this.analyzePeriod(periodKey, themeId);
    }

    async analyzePeriod(periodKey, themeId) {
        if (this.isAnalyzing) return;

        this.isAnalyzing = true;
        this.showLoading(true);

        try {
            const requestData = {
                period_key: periodKey,
                theme_id: themeId,
                max_items: 50
            };

            console.log('📤 Envoi requête analyse comparative:', requestData);

            const response = await this.apiCall('/archiviste/api/analyze-period', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            console.log('📥 Réponse reçue:', response);

            if (response && response.success) {
                this.displayComparativeResult(response);
            } else {
                this.displayError(response?.error || 'Erreur inconnue');
            }
        } catch (error) {
            console.error('❌ Erreur analyse:', error);
            this.displayError(`Erreur: ${error.message}`);
        } finally {
            this.isAnalyzing = false;
            this.showLoading(false);
        }
    }

    displayComparativeResult(result) {
        const resultsElement = document.getElementById('analysis-results');
        const contentElement = document.getElementById('results-content');

        if (!resultsElement || !contentElement) {
            console.error('❌ Éléments de résultats introuvables');
            return;
        }

        contentElement.innerHTML = this.generateComparativeHTML(result);
        resultsElement.classList.remove('hidden');
        resultsElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    generateComparativeHTML(result) {
        const historical = result.historical_sentiment || {};
        const current = result.current_sentiment || {};
        const comparison = result.comparative_analysis || {};

        return `
            <!-- En-tête succès -->
            <div class="bg-green-500/20 border border-green-400/30 rounded-xl p-6 mb-6">
                <h3 class="text-xl font-bold text-green-300 mb-2">✅ Analyse comparative réussie</h3>
                <p class="text-green-200 text-lg">${result.period?.name || 'Période'} - ${result.theme?.name || 'Thème'}</p>
                <p class="text-green-100">
                    ${result.historical_items_analyzed || 0} documents historiques analysés 
                    vs ${result.current_articles_count || 0} articles actuels
                </p>
            </div>

            <!-- Comparaison des sentiments -->
            <div class="bg-white/10 border border-white/20 rounded-xl p-6 mb-6">
                <h4 class="font-semibold text-white text-lg mb-4">📊 Comparaison des sentiments</h4>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Période historique -->
                    <div class="bg-blue-500/20 border border-blue-400/30 rounded-lg p-4">
                        <h5 class="font-semibold text-blue-300 mb-3">🕰️ Période historique</h5>
                        ${this.renderSentimentBars(historical)}
                    </div>

                    <!-- Période actuelle -->
                    <div class="bg-green-500/20 border border-green-400/30 rounded-lg p-4">
                        <h5 class="font-semibold text-green-300 mb-3">📅 Période actuelle</h5>
                        ${this.renderSentimentBars(current)}
                    </div>
                </div>

                <!-- Évolution -->
                <div class="mt-6 bg-purple-500/20 border border-purple-400/30 rounded-lg p-4">
                    <h5 class="font-semibold text-purple-300 mb-2">📈 Évolution</h5>
                    <p class="text-white">${comparison.interpretation || 'Pas de données'}</p>
                    <div class="grid grid-cols-3 gap-4 mt-4">
                        ${this.renderEvolutionMetric('Positif', comparison.positive_evolution)}
                        ${this.renderEvolutionMetric('Négatif', comparison.negative_evolution)}
                        ${this.renderEvolutionMetric('Neutre', comparison.neutral_evolution)}
                    </div>
                </div>
            </div>

            <!-- Changements narratifs -->
            ${this.renderNarrativeShifts(result.narrative_shifts)}

            <!-- Documents historiques principaux -->
            ${this.renderTopHistoricalItems(result.top_historical_items)}
        `;
    }

    renderSentimentBars(stats) {
        if (!stats || stats.total === 0) {
            return '<p class="text-gray-400 text-sm">Pas de données</p>';
        }

        const positive = (stats.positive_ratio * 100).toFixed(1);
        const negative = (stats.negative_ratio * 100).toFixed(1);
        const neutral = (stats.neutral_ratio * 100).toFixed(1);

        return `
            <div class="space-y-3">
                <div>
                    <div class="flex justify-between text-xs mb-1">
                        <span class="text-green-300">Positif</span>
                        <span class="text-green-200">${positive}%</span>
                    </div>
                    <div class="w-full bg-gray-700 rounded-full h-2">
                        <div class="bg-green-500 h-2 rounded-full" style="width: ${positive}%"></div>
                    </div>
                </div>
                <div>
                    <div class="flex justify-between text-xs mb-1">
                        <span class="text-red-300">Négatif</span>
                        <span class="text-red-200">${negative}%</span>
                    </div>
                    <div class="w-full bg-gray-700 rounded-full h-2">
                        <div class="bg-red-500 h-2 rounded-full" style="width: ${negative}%"></div>
                    </div>
                </div>
                <div>
                    <div class="flex justify-between text-xs mb-1">
                        <span class="text-gray-300">Neutre</span>
                        <span class="text-gray-200">${neutral}%</span>
                    </div>
                    <div class="w-full bg-gray-700 rounded-full h-2">
                        <div class="bg-gray-500 h-2 rounded-full" style="width: ${neutral}%"></div>
                    </div>
                </div>
                <div class="text-xs text-gray-400 mt-2">
                    Total: ${stats.total} documents
                </div>
            </div>
        `;
    }

    renderEvolutionMetric(label, value) {
        if (value === undefined || value === null) {
            return '';
        }

        const percent = (value * 100).toFixed(1);
        const isPositive = value > 0;
        const color = isPositive ? 'green' : (value < 0 ? 'red' : 'gray');
        const arrow = isPositive ? '↑' : (value < 0 ? '↓' : '→');

        return `
            <div class="text-center">
                <div class="text-${color}-300 text-2xl">${arrow}</div>
                <div class="text-${color}-200 font-semibold">${percent}%</div>
                <div class="text-gray-400 text-xs">${label}</div>
            </div>
        `;
    }

    renderNarrativeShifts(shifts) {
        if (!shifts) return '';

        return `
            <div class="bg-white/10 border border-white/20 rounded-xl p-6 mb-6">
                <h4 class="font-semibold text-white text-lg mb-4">🔄 Changements narratifs</h4>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div class="bg-orange-500/20 border border-orange-400/30 rounded-lg p-4">
                        <h5 class="font-semibold text-orange-300 mb-2">📈 Mots-clés émergents</h5>
                        ${this.renderKeywordList(shifts.emerging_keywords)}
                    </div>
                    
                    <div class="bg-gray-500/20 border border-gray-400/30 rounded-lg p-4">
                        <h5 class="font-semibold text-gray-300 mb-2">📉 Mots-clés en déclin</h5>
                        ${this.renderKeywordList(shifts.declining_keywords)}
                    </div>
                </div>
            </div>
        `;
    }

    renderKeywordList(keywords) {
        if (!keywords || keywords.length === 0) {
            return '<p class="text-sm text-gray-400">Aucun</p>';
        }

        return `
            <div class="flex flex-wrap gap-2">
                ${keywords.slice(0, 8).map(kw => 
                    `<span class="text-xs bg-white/10 px-2 py-1 rounded">${this.escapeHtml(kw)}</span>`
                ).join('')}
            </div>
        `;
    }

    renderTopHistoricalItems(items) {
        if (!items || items.length === 0) {
            return '';
        }

        return `
            <div class="bg-white/5 border border-white/10 rounded-xl p-4">
                <h4 class="font-semibold text-white mb-3">📚 Documents historiques principaux</h4>
                <div class="space-y-3">
                    ${items.slice(0, 5).map(item => `
                        <div class="bg-black/20 p-3 rounded-lg border border-white/10">
                            <h5 class="font-medium text-blue-300">${this.escapeHtml(item.title || 'Sans titre')}</h5>
                            <p class="text-sm text-gray-300 mt-1">
                                ${this.escapeHtml((item.text_extract || '').substring(0, 150))}...
                            </p>
                            <div class="flex justify-between text-xs text-gray-400 mt-2">
                                <span>Année: ${item.year || 'N/A'}</span>
                                <span>Pertinence: ${((item.theme_relevance || 0) * 100).toFixed(0)}%</span>
                                <span class="px-2 py-1 rounded ${this.getSentimentClass(item.sentiment_analysis?.sentiment_type)}">
                                    ${item.sentiment_analysis?.sentiment_type || 'neutre'}
                                </span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    getSentimentClass(sentiment) {
        switch (sentiment) {
            case 'positive': return 'bg-green-500/30 text-green-300';
            case 'negative': return 'bg-red-500/30 text-red-300';
            default: return 'bg-gray-500/30 text-gray-300';
        }
    }

    displayError(message) {
        const resultsElement = document.getElementById('analysis-results');
        const contentElement = document.getElementById('results-content');

        if (resultsElement && contentElement) {
            contentElement.innerHTML = `
                <div class="bg-red-500/20 border border-red-400/30 rounded-xl p-6">
                    <h3 class="text-xl font-bold text-red-300 mb-2">❌ Erreur</h3>
                    <p class="text-red-200">${this.escapeHtml(message)}</p>
                </div>
            `;
            resultsElement.classList.remove('hidden');
        }
    }

    showLoading(show) {
        const btn = document.getElementById('analyze-period-btn');
        if (btn) {
            if (show) {
                btn.innerHTML = `
                    <div class="flex items-center space-x-3">
                        <div class="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                        <span>Analyse comparative en cours...</span>
                    </div>
                `;
                btn.disabled = true;
            } else {
                btn.innerHTML = `
                    <span class="text-xl">🎯</span>
                    <span class="text-lg">Lancer l'Analyse Historique</span>
                `;
                this.validateForm();
            }
        }
    }

    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        };

        const config = { ...defaultOptions, ...options };
        const response = await fetch(endpoint, config);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        return await response.json();
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static getInstance() {
        if (!window._enhancedArchivisteInstance) {
            window._enhancedArchivisteInstance = new EnhancedArchivisteManager();
        }
        return window._enhancedArchivisteInstance;
    }

    static loadPeriods() {
        return this.getInstance().loadPeriods();
    }

    static loadThemes() {
        return this.getInstance().loadThemes();
    }

    static loadStats() {
        return this.getInstance().loadStats();
    }
}

// Initialisation automatique
(() => {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            window.EnhancedArchivisteManager = EnhancedArchivisteManager;
            EnhancedArchivisteManager.getInstance();
            console.log('✅ EnhancedArchivisteManager avec analyse comparative initialisé');
        });
    } else {
        window.EnhancedArchivisteManager = EnhancedArchivisteManager;
        EnhancedArchivisteManager.getInstance();
        console.log('✅ EnhancedArchivisteManager avec analyse comparative initialisé');
    }
})();
