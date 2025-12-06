// static/js/feeds.js - Gestion adaptative des flux RSS (background progressif)

class FeedManager {
    static defaultFeeds = [
        'https://feeds.bbci.co.uk/news/rss.xml',
        'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
        'https://feeds.lemonde.fr/c/205/f/3050/index.rss',
        'https://www.lefigaro.fr/rss/figaro_actualites.xml',
        'https://www.liberation.fr/arc/outboundfeeds/rss-all/',
        'https://www.francetvinfo.fr/titres.rss',
        'https://www.20minutes.fr/feeds/rss-une.xml'
    ];

    // Configuration adaptative
    static processingState = {
        isRunning: false,
        isPaused: false,
        currentBatch: 0,
        totalBatches: 0,
        processedFeeds: 0,
        totalFeeds: 0,
        newArticles: 0,
        totalArticles: 0,
        errors: [],
        startTime: null
    };

    static AUTO_REFRESH_INTERVAL = 30000; // 30 secondes
    static refreshTimer = null;
    static initialized = false;

    static init() {
        if (this.initialized) {
            console.log('⚠️ FeedManager déjà initialisé');
            return;
        }

        try {
            this.setupEventListeners();
            this.loadSavedFeeds();
            this.initProgressTracking();
            this.startAutoRefresh();
            this.initialized = true;
            console.log('✅ FeedManager adaptatif initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
        }
    }

    static initProgressTracking() {
        try {
            const resultDiv = document.getElementById('updateResult');
            if (resultDiv && !document.getElementById('feedProgressBar')) {
                const progressHTML = `
                    <div id="feedProgressBar" class="hidden mb-4">
                        <div class="flex justify-between text-sm mb-1">
                            <span id="progressLabel">Préparation...</span>
                            <span id="progressCount">0/0</span>
                        </div>
                        <div class="w-full bg-gray-200 rounded-full h-2.5 overflow-hidden">
                            <div id="progressBarFill" class="bg-blue-600 h-2.5 transition-all duration-500 ease-out" style="width: 0%"></div>
                        </div>
                        <div class="flex justify-between mt-2 text-xs text-gray-600">
                            <span id="progressSpeed">Vitesse: --</span>
                            <span id="progressETA">Temps restant: --</span>
                        </div>
                        <div class="flex space-x-2 mt-3">
                            <button id="pauseResumeBtn" onclick="FeedManager.togglePause()" 
                                    class="hidden px-3 py-1 bg-yellow-500 text-white rounded text-xs hover:bg-yellow-600">
                                <i class="fas fa-pause mr-1"></i>Pause
                            </button>
                            <button id="stopBtn" onclick="FeedManager.stopProcessing()" 
                                    class="hidden px-3 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600">
                                <i class="fas fa-stop mr-1"></i>Arrêter
                            </button>
                        </div>
                    </div>
                `;
                resultDiv.insertAdjacentHTML('beforebegin', progressHTML);
            }
        } catch (error) {
            console.warn('⚠️ Impossible de créer la barre de progression:', error);
        }
    }

    static setupEventListeners() {
        const scrapeBtn = document.getElementById('scrapeFeedsBtn');
        if (scrapeBtn) {
            scrapeBtn.addEventListener('click', () => this.startScraping());
        }

        const updateBtn = document.getElementById('updateFeedsBtn');
        if (updateBtn) {
            updateBtn.addEventListener('click', () => this.startScraping());
        }

        const loadDefaultBtn = document.getElementById('loadDefaultFeedsBtn');
        if (loadDefaultBtn) {
            loadDefaultBtn.addEventListener('click', () => this.loadDefaultFeeds());
        }

        const feedsTextarea = document.getElementById('feedUrls');
        if (feedsTextarea) {
            feedsTextarea.addEventListener('blur', () => this.saveFeeds());
        }
    }

    static loadSavedFeeds() {
        try {
            const savedFeeds = localStorage.getItem('savedFeeds');
            const feedsTextarea = document.getElementById('feedUrls');

            if (feedsTextarea) {
                if (savedFeeds && savedFeeds.trim().length > 0) {
                    feedsTextarea.value = savedFeeds;
                    console.log('✅ Flux sauvegardés chargés');
                } else {
                    this.loadDefaultFeeds();
                }
            }
        } catch (error) {
            console.error('❌ Erreur chargement flux:', error);
            this.loadDefaultFeeds();
        }
    }

    static saveFeeds() {
        try {
            const feedsTextarea = document.getElementById('feedUrls');
            if (feedsTextarea && feedsTextarea.value.trim()) {
                localStorage.setItem('savedFeeds', feedsTextarea.value);
            }
        } catch (error) {
            console.error('❌ Erreur sauvegarde flux:', error);
        }
    }

    static loadDefaultFeeds() {
        try {
            const feedsTextarea = document.getElementById('feedUrls');
            if (feedsTextarea) {
                feedsTextarea.value = this.defaultFeeds.join('\n');
                this.showResult('✓ Flux par défaut chargés', 'success');
                this.saveFeeds();
            }
        } catch (error) {
            console.error('❌ Erreur chargement flux par défaut:', error);
        }
    }

    static async startScraping() {
        const feedUrls = this.getFeedUrls();
        
        if (feedUrls.length === 0) {
            this.showResult('⚠ Veuillez entrer au moins un flux RSS', 'error');
            return;
        }

        if (this.processingState.isRunning) {
            this.showResult('⚠ Une analyse est déjà en cours', 'error');
            return;
        }

        this.saveFeeds();
        await this.processAdaptive(feedUrls);
    }

    /**
     * 🎯 Traitement adaptatif en arrière-plan
     * Délègue la vitesse à RoBERTa et TextBlob
     */
    static async processAdaptive(feedUrls) {
        // Réinitialiser l'état
        this.processingState = {
            isRunning: true,
            isPaused: false,
            currentBatch: 0,
            totalBatches: feedUrls.length,
            processedFeeds: 0,
            totalFeeds: feedUrls.length,
            newArticles: 0,
            totalArticles: 0,
            errors: [],
            startTime: Date.now()
        };

        console.log(`🚀 Démarrage analyse adaptative: ${feedUrls.length} flux`);

        this.setButtonsState(false);
        this.showProgressBar(true);
        this.showControlButtons(true);

        // Traiter flux par flux (séquentiel pour adapter la vitesse)
        for (let i = 0; i < feedUrls.length; i++) {
            // Vérifier pause/arrêt
            if (!this.processingState.isRunning) {
                console.log('🛑 Traitement arrêté par l\'utilisateur');
                break;
            }

            while (this.processingState.isPaused) {
                await this.sleep(500);
            }

            const feedUrl = feedUrls[i];
            const feedName = this.extractDomainName(feedUrl);

            this.updateProgress(
                i,
                feedUrls.length,
                `📡 Analyse: ${feedName}...`
            );

            try {
                console.log(`[${i + 1}/${feedUrls.length}] Traitement: ${feedName}`);
                
                // ⭐ Laisser le serveur (RoBERTa) gérer le timing
                const result = await this.processSingleFeedNoTimeout(feedUrl);

                if (result.success) {
                    this.processingState.totalArticles += result.total_articles || 0;
                    this.processingState.newArticles += result.new_articles || 0;
                    console.log(`✅ ${feedName}: ${result.new_articles} nouveaux / ${result.total_articles} total`);
                } else {
                    this.processingState.errors.push(`${feedName}: ${result.error}`);
                    console.warn(`⚠️ ${feedName}: ${result.error}`);
                }

            } catch (error) {
                this.processingState.errors.push(`${feedName}: ${error.message}`);
                console.error(`❌ ${feedName}: ${error.message}`);
            }

            this.processingState.processedFeeds++;

            // Mise à jour progressive de l'UI
            this.updateProgressStats();

            // 🔄 Rafraîchir les données tous les 5 flux
            if (this.processingState.newArticles > 0 && (i + 1) % 5 === 0) {
                console.log('🔄 Rafraîchissement intermédiaire des données...');
                this.refreshDisplayedData().catch(e => console.warn('⚠️ Erreur refresh:', e));
            }
        }

        // Traitement terminé
        this.processingState.isRunning = false;
        this.setButtonsState(true);
        this.showProgressBar(false);
        this.showControlButtons(false);

        console.log(`✅ Analyse terminée: ${this.processingState.newArticles} nouveaux articles`);

        this.displayFinalResults();

        // Rafraîchissement final
        if (this.processingState.newArticles > 0) {
            await this.sleep(1000);
            await this.refreshDisplayedData();
        }
    }

    /**
     * 🎯 Traitement SANS timeout - délégué à RoBERTa
     */
    static async processSingleFeedNoTimeout(feedUrl) {
        try {
            const response = await fetch('/api/update-feeds', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ feeds: [feedUrl] })
            });

            if (!response.ok) {
                return {
                    success: false,
                    error: `HTTP ${response.status}`
                };
            }

            const data = await response.json();

            if (data.results) {
                return {
                    success: true,
                    total_articles: data.results.total_articles || 0,
                    new_articles: data.results.new_articles || 0
                };
            } else if (data.error) {
                return {
                    success: false,
                    error: data.error
                };
            } else {
                return {
                    success: false,
                    error: 'Réponse invalide'
                };
            }
        } catch (error) {
            return {
                success: false,
                error: error.message || 'Erreur réseau'
            };
        }
    }

    static togglePause() {
        this.processingState.isPaused = !this.processingState.isPaused;
        
        const btn = document.getElementById('pauseResumeBtn');
        if (btn) {
            if (this.processingState.isPaused) {
                btn.innerHTML = '<i class="fas fa-play mr-1"></i>Reprendre';
                btn.classList.replace('bg-yellow-500', 'bg-green-500');
                btn.classList.replace('hover:bg-yellow-600', 'hover:bg-green-600');
                console.log('⏸️ Analyse en pause');
            } else {
                btn.innerHTML = '<i class="fas fa-pause mr-1"></i>Pause';
                btn.classList.replace('bg-green-500', 'bg-yellow-500');
                btn.classList.replace('hover:bg-green-600', 'hover:bg-yellow-600');
                console.log('▶️ Analyse reprise');
            }
        }
    }

    static stopProcessing() {
        if (confirm('Voulez-vous vraiment arrêter l\'analyse en cours ?')) {
            this.processingState.isRunning = false;
            console.log('🛑 Arrêt demandé par l\'utilisateur');
        }
    }

    static updateProgressStats() {
        const state = this.processingState;
        const elapsed = (Date.now() - state.startTime) / 1000; // secondes
        
        // Calcul vitesse moyenne
        const avgSpeed = state.processedFeeds / elapsed; // flux/seconde
        const remaining = state.totalFeeds - state.processedFeeds;
        const eta = remaining / avgSpeed; // secondes

        // Mise à jour affichage
        const speedEl = document.getElementById('progressSpeed');
        const etaEl = document.getElementById('progressETA');

        if (speedEl) {
            speedEl.textContent = `Vitesse: ${avgSpeed.toFixed(2)} flux/s`;
        }

        if (etaEl && !isNaN(eta) && eta < 3600) {
            const minutes = Math.floor(eta / 60);
            const seconds = Math.floor(eta % 60);
            etaEl.textContent = `Temps restant: ${minutes}m ${seconds}s`;
        }

        // Mise à jour compteurs principaux
        this.updateProgress(
            state.processedFeeds,
            state.totalFeeds,
            `📊 ${state.newArticles} nouveaux articles trouvés`
        );
    }

    static displayFinalResults() {
        const state = this.processingState;
        const resultDiv = document.getElementById('updateResult');
        if (!resultDiv) return;

        const duration = ((Date.now() - state.startTime) / 1000).toFixed(1);

        let resultHTML = '';

        if (state.newArticles > 0) {
            resultHTML = `
                <div class="text-green-600 bg-green-50 border border-green-200 rounded-lg p-4">
                    <div class="flex items-center mb-2">
                        <i class="fas fa-check-circle text-xl mr-2"></i>
                        <span class="font-medium text-lg">✓ Analyse terminée avec succès!</span>
                    </div>
                    <div class="grid grid-cols-2 gap-3 text-sm mt-3">
                        <div class="bg-white p-2 rounded">
                            <p class="text-gray-600">Nouveaux articles</p>
                            <p class="text-2xl font-bold text-green-700">${state.newArticles}</p>
                        </div>
                        <div class="bg-white p-2 rounded">
                            <p class="text-gray-600">Total traités</p>
                            <p class="text-2xl font-bold">${state.totalArticles}</p>
                        </div>
                        <div class="bg-white p-2 rounded">
                            <p class="text-gray-600">Flux réussis</p>
                            <p class="text-xl font-bold">${state.processedFeeds - state.errors.length}/${state.processedFeeds}</p>
                        </div>
                        <div class="bg-white p-2 rounded">
                            <p class="text-gray-600">Durée</p>
                            <p class="text-xl font-bold">${duration}s</p>
                        </div>
                    </div>
                </div>
            `;
        } else if (state.processedFeeds > state.errors.length) {
            resultHTML = `
                <div class="text-blue-600 bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div class="flex items-center mb-2">
                        <i class="fas fa-info-circle text-xl mr-2"></i>
                        <span class="font-medium text-lg">ℹ Analyse terminée</span>
                    </div>
                    <p class="text-sm mt-2">Aucun nouvel article (${state.totalArticles} déjà en base)</p>
                    <p class="text-sm">${state.processedFeeds} flux analysés en ${duration}s</p>
                </div>
            `;
        } else {
            resultHTML = `
                <div class="text-orange-600 bg-orange-50 border border-orange-200 rounded-lg p-4">
                    <div class="flex items-center mb-2">
                        <i class="fas fa-exclamation-triangle text-xl mr-2"></i>
                        <span class="font-medium text-lg">⚠ Tous les flux ont échoué</span>
                    </div>
                    <p class="text-sm mt-2">Vérifiez votre connexion et les URLs</p>
                </div>
            `;
        }

        // Erreurs
        if (state.errors.length > 0) {
            resultHTML += `
                <div class="mt-3 text-orange-600 bg-orange-50 border border-orange-200 rounded-lg p-4">
                    <details class="cursor-pointer">
                        <summary class="font-medium">⚠ ${state.errors.length} flux en erreur</summary>
                        <div class="mt-2 text-xs space-y-1 max-h-40 overflow-y-auto">
                            ${state.errors.slice(0, 10).map(e => `<p>• ${this.escapeHtml(e)}</p>`).join('')}
                            ${state.errors.length > 10 ? `<p class="italic">... et ${state.errors.length - 10} autres</p>` : ''}
                        </div>
                    </details>
                </div>
            `;
        }

        resultDiv.innerHTML = resultHTML;
    }

    static updateProgress(current, total, label) {
        try {
            const progressLabel = document.getElementById('progressLabel');
            const progressCount = document.getElementById('progressCount');
            const progressBarFill = document.getElementById('progressBarFill');

            if (progressLabel) progressLabel.textContent = label;
            if (progressCount) progressCount.textContent = `${current}/${total}`;
            if (progressBarFill) {
                const percentage = total > 0 ? Math.round((current / total) * 100) : 0;
                progressBarFill.style.width = `${percentage}%`;
            }
        } catch (error) {
            console.warn('⚠️ Erreur mise à jour progression:', error);
        }
    }

    static showProgressBar(show) {
        try {
            const progressBar = document.getElementById('feedProgressBar');
            if (progressBar) {
                progressBar.classList.toggle('hidden', !show);
            }
        } catch (error) {
            console.warn('⚠️ Erreur affichage barre:', error);
        }
    }

    static showControlButtons(show) {
        try {
            const pauseBtn = document.getElementById('pauseResumeBtn');
            const stopBtn = document.getElementById('stopBtn');
            
            if (pauseBtn) pauseBtn.classList.toggle('hidden', !show);
            if (stopBtn) stopBtn.classList.toggle('hidden', !show);
        } catch (error) {
            console.warn('⚠️ Erreur affichage boutons contrôle:', error);
        }
    }

    static setButtonsState(enabled) {
        try {
            const scrapeBtn = document.getElementById('scrapeFeedsBtn');
            const updateBtn = document.getElementById('updateFeedsBtn');

            if (scrapeBtn) {
                scrapeBtn.disabled = !enabled;
                scrapeBtn.innerHTML = enabled
                    ? '<i class="fas fa-play mr-2"></i>Lancer l\'analyse'
                    : '<i class="fas fa-spinner fa-spin mr-2"></i>Analyse en cours...';
            }

            if (updateBtn) {
                updateBtn.disabled = !enabled;
                updateBtn.innerHTML = enabled
                    ? '<i class="fas fa-sync-alt mr-2"></i>Mettre à jour'
                    : '<i class="fas fa-spinner fa-spin mr-2"></i>En cours...';
            }
        } catch (error) {
            console.warn('⚠️ Erreur mise à jour boutons:', error);
        }
    }

    /**
     * 🔄 Rafraîchissement automatique toutes les 30 secondes
     */
    static startAutoRefresh() {
        // Effacer l'ancien timer si existant
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }

        console.log('🔄 Auto-refresh activé (30s)');

        this.refreshTimer = setInterval(() => {
            // Ne pas rafraîchir pendant une analyse
            if (!this.processingState.isRunning) {
                console.log('🔄 Rafraîchissement automatique...');
                this.refreshDisplayedData().catch(e => 
                    console.warn('⚠️ Erreur auto-refresh:', e)
                );
            }
        }, this.AUTO_REFRESH_INTERVAL);
    }

    static stopAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
            console.log('🛑 Auto-refresh arrêté');
        }
    }

    static async refreshDisplayedData() {
        try {
            const promises = [];

            // Dashboard
            if (typeof DashboardManager !== 'undefined' && DashboardManager.loadDashboardData) {
                promises.push(
                    DashboardManager.loadDashboardData().catch(e => {
                        console.warn('⚠️ Erreur refresh dashboard:', e);
                        return null;
                    })
                );
            }

            // Articles
            if (typeof ArticleManager !== 'undefined' && ArticleManager.loadRecentArticles) {
                promises.push(
                    ArticleManager.loadRecentArticles().catch(e => {
                        console.warn('⚠️ Erreur refresh articles:', e);
                        return null;
                    })
                );
            }

            // Stats rapides
            promises.push(
                this.loadQuickStats().catch(e => {
                    console.warn('⚠️ Erreur refresh stats:', e);
                    return null;
                })
            );

            await Promise.allSettled(promises);
            console.log('✅ Données rafraîchies');
        } catch (error) {
            console.error('❌ Erreur rafraîchissement:', error);
        }
    }

    static async loadQuickStats() {
        const elements = {
            totalArticles: document.getElementById('totalArticles'),
            positiveArticles: document.getElementById('positiveArticles'),
            totalThemes: document.getElementById('totalThemes')
        };

        if (!elements.totalArticles && !elements.positiveArticles && !elements.totalThemes) {
            return;
        }

        try {
            const response = await fetch('/api/stats');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();

            if (elements.totalArticles) {
                this.animateCounter(elements.totalArticles, data.total_articles || 0);
            }
            if (elements.positiveArticles) {
                this.animateCounter(elements.positiveArticles, data.sentiment_distribution?.positive || 0);
            }
            if (elements.totalThemes) {
                this.animateCounter(elements.totalThemes, Object.keys(data.theme_stats || {}).length);
            }
        } catch (error) {
            console.error('❌ Erreur stats:', error);
            Object.values(elements).forEach(el => {
                if (el) el.textContent = '0';
            });
        }
    }

    static animateCounter(element, targetValue) {
        try {
            const currentValue = parseInt(element.textContent) || 0;
            if (currentValue === targetValue) return;

            const duration = 600;
            const steps = 20;
            const increment = (targetValue - currentValue) / steps;
            let step = 0;

            const timer = setInterval(() => {
                step++;
                element.textContent = Math.round(currentValue + (increment * step));
                if (step >= steps) {
                    element.textContent = targetValue;
                    clearInterval(timer);
                }
            }, duration / steps);
        } catch (error) {
            element.textContent = targetValue;
        }
    }

    static getFeedUrls() {
        try {
            const feedsTextarea = document.getElementById('feedUrls');
            if (!feedsTextarea) return [];

            return feedsTextarea.value
                .split('\n')
                .map(url => url.trim())
                .filter(url => url.length > 0)
                .filter(url => this.isValidUrl(url))
                .filter((url, i, self) => self.indexOf(url) === i);
        } catch (error) {
            console.error('❌ Erreur récupération URLs:', error);
            return [];
        }
    }

    static isValidUrl(string) {
        try {
            const url = new URL(string);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch {
            return false;
        }
    }

    static showResult(message, type = 'info') {
        const resultDiv = document.getElementById('updateResult');
        if (!resultDiv) return;

        const config = {
            success: { color: 'text-green-600 bg-green-50 border-green-200', icon: 'check-circle' },
            error: { color: 'text-red-600 bg-red-50 border-red-200', icon: 'exclamation-triangle' },
            info: { color: 'text-blue-600 bg-blue-50 border-blue-200', icon: 'info-circle' }
        };

        const { color, icon } = config[type] || config.info;

        resultDiv.innerHTML = `
            <div class="${color} border rounded-lg p-3 flex items-center">
                <i class="fas fa-${icon} text-lg mr-2"></i>
                <span>${message}</span>
            </div>
        `;
    }

    static extractDomainName(url) {
        try {
            return new URL(url).hostname.replace('www.', '');
        } catch {
            return url.substring(0, 30) + '...';
        }
    }

    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    window.FeedManager = FeedManager;
    FeedManager.init();
});

// Nettoyage avant fermeture
window.addEventListener('beforeunload', function() {
    if (FeedManager.refreshTimer) {
        FeedManager.stopAutoRefresh();
    }
});