/**
 * Archiviste v3.0 - Frontend Manager OPTIMISÉ ET COMPLET
 * Corrections: validation robuste, meilleure gestion erreurs, UX améliorée
 */

class ArchivisteV3Manager {
    constructor() {
        this.initialized = false;
        this.isAnalyzing = false;
        this.apiBaseUrl = window.location.origin;

        this.defaultPeriods = {
            '1945-1950': { name: 'Après-guerre et débuts de la Guerre froide', start: 1945, end: 1950 },
            '1950-1960': { name: 'Première phase de la Guerre froide', start: 1950, end: 1960 },
            '1960-1970': { name: 'Tensions nucléaires et révolutions sociales', start: 1960, end: 1970 },
            '1970-1980': { name: 'Détente, crises économiques', start: 1970, end: 1980 },
            '1980-1991': { name: 'Fin de la Guerre froide', start: 1980, end: 1991 },
            '1991-2000': { name: 'Post-Guerre froide et mondialisation', start: 1991, end: 2000 },
            '2000-2010': { name: 'Guerre contre le terrorisme et crise économique', start: 2000, end: 2010 },
            '2010-2019': { name: 'Réseaux sociaux, révolutions et multipolarité', start: 2010, end: 2019 },
            '2019-2022': { name: 'Pandémie de COVID-19', start: 2019, end: 2022 },
            '2022-2025': { name: 'Guerre en Ukraine et révolution de l\'IA', start: 2022, end: 2025 }
        };

        this.init();
    }

    init() {
        console.log('🚀 ArchivisteV3Manager - Démarrage...');
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeComponents());
        } else {
            this.initializeComponents();
        }
    }

    initializeComponents() {
        if (this.initialized) return;
        console.log('🔧 Initialisation des composants...');
        this.setupEventListeners();
        this.loadInitialData();
        this.initialized = true;
        console.log('✅ ArchivisteV3Manager complètement initialisé');
    }

    setupEventListeners() {
        console.log('🔗 Configuration des écouteurs...');
        const analyzeBtn = document.getElementById('analyze-period-btn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.handlePeriodAnalysis());
            console.log('✅ Bouton analyse configuré');
        }

        const periodSelect = document.getElementById('period-select');
        const themeSelect = document.getElementById('theme-select');

        if (periodSelect) {
            periodSelect.addEventListener('change', () => {
                console.log('📅 Période changée:', periodSelect.value);
                this.validateAnalysisForm();
            });
        }

        if (themeSelect) {
            themeSelect.addEventListener('change', () => {
                const selectedOption = themeSelect.options[themeSelect.selectedIndex];
                console.log('🏷️ Thème changé:', themeSelect.value, selectedOption?.textContent);
                this.validateAnalysisForm();
            });
        }

        console.log('✅ Tous les écouteurs configurés');
    }

    async loadInitialData() {
        console.log('📥 Début chargement données initiales');
        try {
            const periodsResponse = await this.apiCall('/archiviste-v3/api/periods');
            if (periodsResponse?.success) {
                this.populatePeriodSelect(periodsResponse.periods);
            } else {
                this.populatePeriodSelect(this.defaultPeriods);
            }

            const themesResponse = await this.apiCall('/api/themes');
            if (themesResponse?.themes) {
                this.populateThemeSelect(themesResponse.themes);
            } else {
                console.warn('⚠️ Impossible de charger les thèmes');
            }

            this.validateAnalysisForm();
            setTimeout(() => this.loadAnalysesHistory(), 1500);
            console.log('✅ Données initiales chargées');
        } catch (error) {
            console.error('❌ Erreur chargement données:', error);
            this.loadAllDefaultData();
        }
    }

    populatePeriodSelect(periods) {
        const select = document.getElementById('period-select');
        if (!select) return;

        const currentValue = select.value;
        select.innerHTML = '<option value="">Sélectionnez une période historique...</option>';
        let periodCount = 0;

        if (Array.isArray(periods)) {
            periods.forEach((period, index) => {
                const key = period.key || period.id || index.toString();
                const name = period.name || period.label || `Période ${index + 1}`;
                const start = period.start || period.start_year;
                const end = period.end || period.end_year;
                this.addPeriodOption(select, key, name, start, end);
                periodCount++;
            });
        } else if (typeof periods === 'object' && periods !== null) {
            Object.entries(periods).forEach(([key, period]) => {
                const name = period.name || period.label || key.replace(/_/g, ' ').toUpperCase();
                const start = period.start || period.start_year;
                const end = period.end || period.end_year;
                this.addPeriodOption(select, key, name, start, end);
                periodCount++;
            });
        }

        if (currentValue) {
            const optionExists = Array.from(select.options).some(opt => opt.value === currentValue);
            if (optionExists) select.value = currentValue;
        }

        console.log(`✅ ${periodCount} périodes chargées`);
    }

    addPeriodOption(select, key, name, start, end) {
        const option = document.createElement('option');
        option.value = key;
        let displayText = name;
        if (start && end) {
            displayText += ` (${start} - ${end})`;
        } else if (start) {
            displayText += ` (dès ${start})`;
        }
        option.textContent = displayText;
        option.title = `${name} - Période historique`;
        if (start && end) {
            option.dataset.start = start;
            option.dataset.end = end;
        }
        select.appendChild(option);
    }

    populateThemeSelect(themes) {
        const select = document.getElementById('theme-select');
        if (!select) return;

        const currentValue = select.value;
        select.innerHTML = '<option value="">Sélectionnez un thème d\'analyse...</option>';
        let themeCount = 0;

        if (Array.isArray(themes)) {
            themes.forEach(theme => {
                const id = theme.id || theme._id;
                const name = theme.name || theme.label || theme.title || `Thème ${id}`;
                const keywordsCount = theme.keywords_count || (theme.keywords ? theme.keywords.length : 0);

                const option = document.createElement('option');
                option.value = id;
                option.textContent = `${name} (${keywordsCount} mots-clés)`;
                option.dataset.themeName = name;

                if (theme.description) option.title = theme.description;
                if (theme.keywords) option.dataset.keywords = JSON.stringify(theme.keywords.slice(0, 5));

                select.appendChild(option);
                themeCount++;
            });
        }

        if (currentValue && Array.from(select.options).some(opt => opt.value === currentValue)) {
            select.value = currentValue;
        }

        console.log(`✅ ${themeCount} thèmes chargés`);
    }

    validateAnalysisForm() {
        const periodSelect = document.getElementById('period-select');
        const themeSelect = document.getElementById('theme-select');
        const analyzeBtn = document.getElementById('analyze-period-btn');

        if (!periodSelect || !themeSelect || !analyzeBtn) return;

        const isPeriodSelected = periodSelect.value && periodSelect.value !== '';
        const isThemeSelected = themeSelect.value && themeSelect.value !== '';
        const isValid = isPeriodSelected && isThemeSelected;

        analyzeBtn.disabled = !isValid;

        if (isValid) {
            analyzeBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            analyzeBtn.classList.add('opacity-100', 'cursor-pointer', 'hover:shadow-lg');
        } else {
            analyzeBtn.classList.add('opacity-50', 'cursor-not-allowed');
            analyzeBtn.classList.remove('opacity-100', 'hover:shadow-lg');
        }

        console.log(`📋 Formulaire: ${isValid ? 'PRÊT' : 'INCOMPLET'}`);
    }

    async handlePeriodAnalysis() {
        if (this.isAnalyzing) {
            this.showToast('Une analyse est déjà en cours', 'warning');
            return;
        }

        const periodKey = document.getElementById('period-select').value;
        const themeId = document.getElementById('theme-select').value;
        const maxItems = parseInt(document.getElementById('max-items')?.value || '50');

        const periodSelect = document.getElementById('period-select');
        const themeSelect = document.getElementById('theme-select');

        const periodOption = periodSelect.options[periodSelect.selectedIndex];
        const themeOption = themeSelect.options[themeSelect.selectedIndex];

        const periodDisplayName = periodOption.textContent.split('(')[0].trim();
        const themeDisplayName = themeOption.textContent.split('(')[0].trim();

        console.log(`🎯 Analyse: ${periodDisplayName} (${periodKey}) + ${themeDisplayName} (ID: ${themeId})`);

        if (!periodKey || !themeId) {
            this.displayError('Sélectionnez une période et un thème');
            return;
        }

        if (isNaN(parseInt(themeId))) {
            console.error('❌ theme_id invalide:', themeId);
            this.displayError(`Thème invalide: ${themeId}. Veuillez recharger la page.`);
            return;
        }

        this.isAnalyzing = true;
        this.showAnalysisLoading(true);

        try {
            const payload = {
                period_key: periodKey,
                theme_id: parseInt(themeId),
                max_items: maxItems
            };

            console.log('📤 Envoi payload:', payload);

            const response = await this.apiCall('/archiviste-v3/api/analyze-period', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            console.log('📊 Réponse analyse:', response);

            if (response?.success) {
                this.displayAnalysisResults(response);
                this.showToast('Analyse terminée avec succès', 'success');
                setTimeout(() => this.loadAnalysesHistory(), 1000);
            } else {
                const errorMsg = response?.error || 'Erreur inconnue';
                if (errorMsg.includes('Aucun document') || response?.items_analyzed === 0) {
                    this.displayNoResultsMessage(periodDisplayName, themeDisplayName, response);
                } else {
                    this.displayError(errorMsg);
                }
            }
        } catch (error) {
            console.error('❌ Erreur analyse:', error);
            this.displayError(`Erreur technique: ${error.message}`);
        } finally {
            this.isAnalyzing = false;
            this.showAnalysisLoading(false);
        }
    }

    displayAnalysisResults(result) {
        const resultsDiv = document.getElementById('analysis-results');
        const contentDiv = document.getElementById('analysis-content');

        if (!resultsDiv || !contentDiv) {
            console.error('❌ Conteneurs résultats non trouvés');
            return;
        }

        const html = this.generateResultsHTML(result);
        contentDiv.innerHTML = html;
        resultsDiv.classList.remove('hidden');

        setTimeout(() => {
            resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);

        console.log('✅ Résultats affichés');
    }

    generateResultsHTML(result) {
        const periodName = result.period?.name || 'Période';
        const themeName = result.theme?.name || 'Thème';
        const itemsCount = result.items_analyzed || 0;
        const keyItems = result.key_items || [];
        const searchMetadata = result.search_metadata || {};
        const insights = result.insights || [];

        let html = `
            <div class="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-300 rounded-xl p-6 mb-6 shadow-lg">
                <div class="flex items-center justify-between">
                    <div>
                        <h3 class="text-2xl font-bold text-green-800 mb-2 flex items-center">
                            <span class="text-3xl mr-2">✅</span>
                            Analyse réussie
                        </h3>
                        <p class="text-green-700 font-medium">${periodName} - ${themeName}</p>
                        <p class="text-green-600 text-sm mt-1">${itemsCount} documents analysés</p>
                        ${searchMetadata.duration_seconds ? `
                            <p class="text-green-500 text-xs mt-1">⏱️ Durée: ${searchMetadata.duration_seconds}s</p>
                        ` : ''}
                    </div>
                    <div class="text-right">
                        <div class="text-4xl font-bold text-green-700">${keyItems.length}</div>
                        <div class="text-green-600 text-sm">documents clés</div>
                    </div>
                </div>
                
                ${searchMetadata.theme_keywords ? `
                    <div class="mt-4 p-4 bg-white rounded-lg border border-green-200">
                        <p class="text-green-800 text-sm font-medium mb-2">
                            🔑 Mots-clés de recherche:
                        </p>
                        <div class="flex flex-wrap gap-2">
                            ${searchMetadata.theme_keywords.slice(0, 15).map(kw => `
                                <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                                    ${this.escapeHtml(kw)}
                                </span>
                            `).join('')}
                        </div>
                        ${searchMetadata.theme_keywords.length > 15 ? `
                            <p class="text-green-600 text-xs mt-2">+ ${searchMetadata.theme_keywords.length - 15} autres</p>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
        `;

        if (insights.length > 0) {
            html += `
                <div class="bg-gradient-to-r from-purple-50 to-indigo-50 border-2 border-purple-300 rounded-xl p-6 mb-6 shadow-lg">
                    <h4 class="text-xl font-bold text-purple-800 mb-4 flex items-center">
                        <span class="text-2xl mr-2">💡</span>
                        Insights de l'analyse
                    </h4>
                    <div class="space-y-3">
                        ${insights.map(insight => `
                            <div class="flex items-start bg-white p-3 rounded-lg border border-purple-200">
                                <span class="text-purple-500 mr-3 text-lg">▸</span>
                                <span class="text-purple-700 font-medium">${this.escapeHtml(insight)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        if (keyItems.length > 0) {
            html += `
                <div class="bg-white border-2 border-blue-200 rounded-xl p-6 mb-6 shadow-lg">
                    <h4 class="text-xl font-bold text-gray-800 mb-5 flex items-center">
                        <span class="text-2xl mr-2">⭐</span>
                        Documents clés (${keyItems.length})
                    </h4>
                    <div class="space-y-4">
            `;

            keyItems.forEach((item, index) => {
                const title = this.escapeHtml(item.title || `Document ${index + 1}`);
                const description = this.escapeHtml(item.description || 'Aucune description');
                const sourceUrl = item.source_url || `https://archive.org/details/${item.identifier}`;
                const date = item.date || item.year || 'Date inconnue';
                const relevance = Math.round((item.geopolitical_relevance || 0.5) * 100);
                const entities = item.entities || [];

                html += `
                    <div class="border-2 border-gray-200 rounded-lg p-5 hover:border-blue-400 hover:shadow-md transition-all">
                        <div class="flex justify-between items-start mb-3">
                            <h5 class="font-bold text-gray-800 text-lg flex-1 pr-4">${title}</h5>
                            <span class="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-bold rounded-full whitespace-nowrap">
                                ${relevance}% pertinent
                            </span>
                        </div>
                        
                        <p class="text-gray-600 mb-4 leading-relaxed">${description.substring(0, 250)}${description.length > 250 ? '...' : ''}</p>
                        
                        ${entities.length > 0 ? `
                            <div class="mb-4">
                                <p class="text-xs text-gray-500 mb-2 font-medium">🏷️ Entités détectées:</p>
                                <div class="flex flex-wrap gap-2">
                                    ${entities.slice(0, 8).map(e => `
                                        <span class="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs">
                                            ${this.escapeHtml(e.text)}
                                        </span>
                                    `).join('')}
                                    ${entities.length > 8 ? `
                                        <span class="px-2 py-1 bg-gray-200 text-gray-600 rounded text-xs">
                                            +${entities.length - 8}
                                        </span>
                                    ` : ''}
                                </div>
                            </div>
                        ` : ''}
                        
                        <div class="flex justify-between items-center pt-3 border-t border-gray-200">
                            <div class="text-sm text-gray-500 flex items-center gap-3">
                                <span>📅 ${date}</span>
                                <span>🌐 ${item.language || 'FR'}</span>
                                ${item.downloads ? `<span>⬇️ ${item.downloads}</span>` : ''}
                            </div>
                            
                            <a href="${sourceUrl}" 
                               target="_blank" 
                               rel="noopener noreferrer"
                               class="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white text-sm font-medium rounded-lg transition-all shadow-md hover:shadow-lg">
                                🔗 Voir sur Archive.org
                            </a>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="bg-yellow-50 border border-yellow-200 rounded-xl p-6 text-center">
                    <div class="text-4xl mb-3">📭</div>
                    <p class="text-yellow-800 font-medium">Aucun document clé trouvé</p>
                    <p class="text-yellow-600 text-sm mt-2">Essayez d'élargir vos critères de recherche</p>
                </div>
            `;
        }

        return html;
    }

    displayNoResultsMessage(periodName, themeName, originalResponse) {
        const resultsDiv = document.getElementById('analysis-results');
        const contentDiv = document.getElementById('analysis-content');

        if (!resultsDiv || !contentDiv) return;

        const cacheInfo = originalResponse?.cache_metadata || {};

        contentDiv.innerHTML = `
            <div class="bg-gradient-to-r from-yellow-50 to-amber-50 border-2 border-yellow-300 rounded-xl p-8 mb-6 shadow-lg">
                <div class="flex items-start">
                    <div class="text-5xl mr-4">🔍</div>
                    <div class="flex-1">
                        <h3 class="text-2xl font-bold text-yellow-800 mb-3">
                            Aucun document trouvé
                        </h3>
                        <p class="text-yellow-700 mb-2 text-lg">
                            La recherche pour <strong>"${periodName}"</strong> avec le thème 
                            <strong>"${themeName}"</strong> n'a retourné aucun résultat.
                        </p>
                        
                        ${cacheInfo.from_cache > 0 ? `
                            <p class="text-yellow-600 text-sm mt-3">
                                📂 ${cacheInfo.from_cache} documents en cache, mais aucun nouveau trouvé.
                            </p>
                        ` : ''}
                        
                        <div class="mt-4 p-4 bg-white rounded-lg border border-yellow-200">
                            <p class="text-yellow-700 font-medium mb-2">
                                Causes possibles :
                            </p>
                            <ul class="text-yellow-600 text-sm ml-4 space-y-1 list-disc">
                                <li>Période trop spécifique ou récente</li>
                                <li>Mots-clés trop restrictifs</li>
                                <li>Documents non indexés dans Archive.org</li>
                                <li>Combinaison période/thème peu documentée</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="bg-white border-2 border-gray-200 rounded-xl p-6 shadow-lg">
                <h4 class="font-bold text-gray-800 mb-5 text-xl flex items-center">
                    <span class="text-2xl mr-2">💡</span>
                    Suggestions d'amélioration
                </h4>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <h5 class="font-semibold text-blue-800 mb-3 flex items-center">
                            <span class="mr-2">🎯</span>
                            Stratégies de recherche
                        </h5>
                        <ul class="text-blue-700 space-y-2 text-sm">
                            <li>• Élargir la période temporelle</li>
                            <li>• Choisir un thème plus général</li>
                            <li>• Ajouter des synonymes aux mots-clés</li>
                            <li>• Vérifier l'orthographe</li>
                        </ul>
                    </div>
                    
                    <div class="p-4 bg-green-50 rounded-lg border border-green-200">
                        <h5 class="font-semibold text-green-800 mb-3 flex items-center">
                            <span class="mr-2">⚡</span>
                            Actions rapides
                        </h5>
                        <div class="space-y-2">
                            <button onclick="window.location.reload()" 
                                    class="w-full text-left p-3 bg-white hover:bg-green-100 rounded-lg transition-colors border border-green-200 font-medium text-green-800">
                                🔄 Réessayer avec d'autres paramètres
                            </button>
                            <button onclick="document.getElementById('period-select').focus()" 
                                    class="w-full text-left p-3 bg-white hover:bg-green-100 rounded-lg transition-colors border border-green-200 font-medium text-green-800">
                                📅 Changer la période
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        resultsDiv.classList.remove('hidden');
        resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    showAnalysisLoading(show) {
        const btn = document.getElementById('analyze-period-btn');
        if (!btn) return;

        if (show) {
            btn.innerHTML = `
                <div class="flex items-center justify-center space-x-3">
                    <div class="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                    <span class="font-medium">Analyse en cours...</span>
                </div>
            `;
            btn.disabled = true;
            btn.classList.add('opacity-75', 'cursor-wait');
        } else {
            btn.innerHTML = `
                <div class="flex items-center justify-center space-x-2">
                    <span class="text-xl">▶️</span>
                    <span class="font-semibold">Lancer l'Analyse</span>
                </div>
            `;
            btn.classList.remove('opacity-75', 'cursor-wait');
            this.validateAnalysisForm();
        }
    }

    async loadAnalysesHistory() {
        try {
            console.log('📜 Chargement historique...');
            const response = await this.apiCall('/archiviste-v3/api/analyses-history');

            if (response?.success) {
                this.displayAnalysesHistory(response.analyses || []);
            }
        } catch (error) {
            console.warn('⚠️ Erreur historique:', error);
        }
    }

    displayAnalysesHistory(analyses) {
        const container = document.getElementById('analyses-history');
        if (!container) return;

        if (!analyses || analyses.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8">
                    <div class="text-4xl mb-3">⏱️</div>
                    <p class="text-gray-500 font-medium">Aucune analyse précédente</p>
                    <p class="text-sm text-gray-400 mt-1">Effectuez votre première analyse</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="mb-4">
                <h5 class="font-bold text-gray-700 mb-3 text-lg flex items-center">
                    <span class="mr-2">📋</span>
                    Historique des analyses
                </h5>
            </div>
            <div class="space-y-3 max-h-96 overflow-y-auto">
                ${analyses.slice(0, 15).map((analysis, index) => `
                    <div class="flex items-center justify-between p-4 bg-gradient-to-r from-gray-50 to-slate-50 hover:from-gray-100 hover:to-slate-100 rounded-lg border border-gray-200 transition-all hover:shadow-md">
                        <div class="flex items-center flex-1">
                            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-purple-400 to-indigo-500 text-white flex items-center justify-center font-bold text-sm mr-4 shadow-md">
                                ${index + 1}
                            </div>
                            <div class="flex-1">
                                <div class="font-semibold text-gray-800">
                                    ${this.escapeHtml(analysis.theme_name || analysis.period_name || 'Analyse')}
                                </div>
                                <div class="text-xs text-gray-500 mt-1 flex items-center gap-2">
                                    ${analysis.period_name ? `<span>📅 ${analysis.period_name}</span>` : ''}
                                    ${analysis.created_at ? `<span>• ${new Date(analysis.created_at).toLocaleDateString('fr-FR')}</span>` : ''}
                                    ${analysis.duration ? `<span>• ⏱️ ${analysis.duration.toFixed(1)}s</span>` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="text-right ml-4">
                            <div class="text-lg font-bold text-gray-700">${analysis.items_analyzed || 0}</div>
                            <div class="text-xs text-gray-500">documents</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async apiCall(endpoint, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        };

        const config = { ...defaultOptions, ...options };
        const url = endpoint.startsWith('http') ? endpoint : `${this.apiBaseUrl}${endpoint}`;

        console.log(`📡 API ${config.method}: ${url}`);

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                let errorDetails = '';
                try {
                    const errorBody = await response.json();
                    errorDetails = errorBody.error || JSON.stringify(errorBody);
                } catch {
                    errorDetails = await response.text();
                }

                console.error(`❌ Erreur HTTP ${response.status}:`, errorDetails);
                throw new Error(`HTTP ${response.status}: ${errorDetails}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`❌ API error: ${url}`, error);
            throw error;
        }
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showToast(message, type = 'info') {
        const colors = {
            error: 'bg-red-500',
            success: 'bg-green-500',
            warning: 'bg-yellow-500',
            info: 'bg-blue-500'
        };

        const icons = {
            error: '❌',
            success: '✅',
            warning: '⚠️',
            info: 'ℹ️'
        };

        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-xl text-white font-medium ${colors[type] || colors.info} flex items-center gap-2`;
        toast.innerHTML = `
            <span class="text-xl">${icons[type] || icons.info}</span>
            <span>${message}</span>
        `;
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'transform 0.3s ease-in-out';

        document.body.appendChild(toast);

        setTimeout(() => toast.style.transform = 'translateX(0)', 10);

        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }

    displayError(message) {
        console.error('❌ Erreur affichée:', message);
        this.showToast(message, 'error');

        const resultsDiv = document.getElementById('analysis-results');
        const contentDiv = document.getElementById('analysis-content');

        if (resultsDiv && contentDiv) {
            contentDiv.innerHTML = `
                <div class="bg-red-50 border-2 border-red-300 rounded-xl p-6 text-center">
                    <div class="text-5xl mb-4">⚠️</div>
                    <h3 class="text-xl font-bold text-red-800 mb-2">Erreur</h3>
                    <p class="text-red-700">${this.escapeHtml(message)}</p>
                    <button onclick="window.location.reload()" 
                            class="mt-4 px-6 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors">
                        🔄 Recharger la page
                    </button>
                </div>
            `;
            resultsDiv.classList.remove('hidden');
        }
    }

    loadAllDefaultData() {
        console.log('🔄 Chargement données par défaut...');
        this.populatePeriodSelect(this.defaultPeriods);
        this.validateAnalysisForm();
    }
}

// Initialisation globale
(() => {
    console.log('🌐 Archiviste v3.0 - Initialisation globale');

    const initManager = () => {
        console.log('👨‍💼 Création ArchivisteManager...');
        window.archivisteManager = new ArchivisteV3Manager();
        console.log('✅ ArchivisteManager prêt');
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initManager);
    } else {
        initManager();
    }
})();