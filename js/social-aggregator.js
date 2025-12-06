// static/js/social-aggregator.js - VERSION COMPLÈTE

class SocialAggregatorManager {
    static async showSocialPanel() {
        const content = document.getElementById('themeManagerContent');
        const title = document.getElementById('modalTitle');

        if (!content || !title) {
            console.error('❌ Éléments modal non trouvés');
            return;
        }

        title.textContent = '🌐 Réseaux Sociaux';

        content.innerHTML = `
            <div class="max-w-6xl mx-auto space-y-6">
                <!-- En-tête explicatif -->
                <div class="bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-blue-500 p-4 rounded-lg">
                    <div class="flex items-start">
                        <div class="flex-shrink-0">
                            <i class="fas fa-network-wired text-blue-500 text-2xl"></i>
                        </div>
                        <div class="ml-3">
                            <h3 class="text-lg font-semibold text-gray-800">Agrégation de Réseaux Sociaux</h3>
                            <p class="mt-2 text-sm text-gray-600">
                                Analyse des tendances émotionnelles et géopolitiques sur les réseaux sociaux,
                                avec comparaison aux médias traditionnels.
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Actions rapides -->
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div class="bg-white rounded-lg shadow-md p-4">
                        <h4 class="font-bold text-gray-800 mb-2">
                            <i class="fas fa-download text-blue-600 mr-2"></i>Récupération
                        </h4>
                        <p class="text-sm text-gray-600 mb-3">Récupérer les derniers posts</p>
                        <button onclick="SocialAggregatorManager.fetchRecentPosts()" 
                                id="fetchPostsBtn"
                                class="w-full bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700 text-sm">
                            Récupérer les posts
                        </button>
                    </div>

                    <div class="bg-white rounded-lg shadow-md p-4">
                        <h4 class="font-bold text-gray-800 mb-2">
                            <i class="fas fa-chart-line text-green-600 mr-2"></i>Top Thèmes
                        </h4>
                        <p class="text-sm text-gray-600 mb-3">Les 5 thèmes émotionnels du jour</p>
                        <button onclick="SocialAggregatorManager.loadTopThemes()" 
                                class="w-full bg-green-600 text-white px-3 py-2 rounded hover:bg-green-700 text-sm">
                            Voir les top thèmes
                        </button>
                    </div>

                    <div class="bg-white rounded-lg shadow-md p-4">
                        <h4 class="font-bold text-gray-800 mb-2">
                            <i class="fas fa-balance-scale text-purple-600 mr-2"></i>Comparaison
                        </h4>
                        <p class="text-sm text-gray-600 mb-3">RSS vs Réseaux Sociaux</p>
                        <button onclick="SocialAggregatorManager.compareWithRSS()" 
                                class="w-full bg-purple-600 text-white px-3 py-2 rounded hover:bg-purple-700 text-sm">
                            Comparer maintenant
                        </button>
                    </div>

                    <div class="bg-white rounded-lg shadow-md p-4">
                        <h4 class="font-bold text-gray-800 mb-2">
                            <i class="fas fa-cog text-gray-600 mr-2"></i>Configuration
                        </h4>
                        <p class="text-sm text-gray-600 mb-3">Gérer les instances Nitter</p>
                        <button onclick="InstanceManager.showInstancePanel()" 
                                class="w-full bg-gray-600 text-white px-3 py-2 rounded hover:bg-gray-700 text-sm">
                            Gérer les instances
                        </button>
                    </div>
                </div>

                <!-- Résultats -->
                <div id="socialResults" class="space-y-4">
                    <div class="text-center py-8 text-gray-500">
                        <i class="fas fa-share-alt text-3xl mb-3"></i>
                        <p>Interface prête</p>
                        <p class="text-sm mt-2">Utilisez les boutons ci-dessus pour commencer</p>
                    </div>
                </div>

                <!-- Statistiques en temps réel -->
                <div class="bg-white rounded-lg shadow-md p-4">
                    <h4 class="font-bold text-gray-800 mb-4">
                        <i class="fas fa-chart-bar text-indigo-600 mr-2"></i>Statistiques en temps réel
                    </h4>
                    <div id="realTimeStats" class="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-blue-600" id="modalTotalPosts">0</div>
                            <div class="text-sm text-gray-600">Posts totaux</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-green-600" id="modalPositivePosts">0</div>
                            <div class="text-sm text-gray-600">Sentiment +</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-red-600" id="modalNegativePosts">0</div>
                            <div class="text-sm text-gray-600">Sentiment -</div>
                        </div>
                        <div class="text-center">
                            <div class="text-2xl font-bold text-purple-600" id="modalFactorZ">0.00</div>
                            <div class="text-sm text-gray-600">Facteur Z</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        ModalManager.showModal('themeManagerModal');
        this.loadStatistics();
    }

    static async fetchRecentPosts(buttonElement = null) {
        // Déterminer le container en fonction du contexte
        let resultsDiv;
        if (window.location.pathname === '/social') {
            resultsDiv = document.getElementById('recent-posts-result');
        } else {
            resultsDiv = document.getElementById('socialResults');
        }

        const btn = buttonElement || document.getElementById('fetchPostsBtn');

        if (!resultsDiv) {
            console.error('❌ Element de résultats non trouvé');
            return;
        }

        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Récupération...';
        }

        resultsDiv.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin text-blue-600 text-xl"></i><p class="mt-2 text-gray-600">Récupération en cours...</p></div>';

        try {
            const response = await fetch('/api/social/fetch-posts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ days: 1 })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                this.displayFetchResults(data, resultsDiv);
                this.loadStatistics();
            } else {
                this.showError(resultsDiv, data.error || 'Erreur lors de la récupération');
            }

        } catch (error) {
            console.error('❌ Erreur fetchRecentPosts:', error);
            this.showError(resultsDiv, 'Erreur réseau: ' + error.message);
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = window.location.pathname === '/social' ?
                    '<i class="fas fa-download mr-2"></i>Récupérer' :
                    'Récupérer les posts';
            }
        }
    }

    static displayFetchResults(data, container) {
        if (!container) {
            console.error('❌ Container non défini dans displayFetchResults');
            return;
        }

        const posts = data.posts || [];

        let html = `
            <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <div class="flex items-center mb-2">
                    <i class="fas fa-check-circle text-green-600 mr-2"></i>
                    <span class="font-semibold text-green-800">Récupération réussie</span>
                </div>
                <div class="text-sm text-green-700">
                    <p>📊 ${data.posts_count || 0} posts trouvés</p>
                    <p>💾 ${data.saved_count || 0} posts sauvegardés</p>
                </div>
            </div>
        `;

        if (posts.length > 0) {
            html += `
                <div class="bg-white rounded-lg border">
                    <div class="p-4 border-b">
                        <h4 class="font-semibold text-gray-800">Derniers posts récupérés</h4>
                    </div>
                    <div class="max-h-96 overflow-y-auto">
                        ${posts.map(post => this.getPostTemplate(post)).join('')}
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="text-center py-8 text-gray-500 bg-white rounded-lg border">
                    <i class="fas fa-inbox text-3xl mb-3"></i>
                    <p>Aucun post récupéré</p>
                    <p class="text-sm mt-2">Vérifiez la connexion aux réseaux sociaux</p>
                </div>
            `;
        }

        container.innerHTML = html;
    }

    static getPostTemplate(post) {
        const sentimentType = post.sentiment_type || 'neutral';
        const sentimentClass = this.getSentimentClass(sentimentType);
        const sentimentIcon = this.getSentimentIcon(sentimentType);
        const title = post.title || 'Sans titre';
        const content = post.content || '';
        const source = post.source || 'Inconnu';
        const pubDate = post.pub_date || new Date().toISOString();

        return `
            <div class="border-b border-gray-200 p-4 hover:bg-gray-50">
                <div class="flex justify-between items-start mb-2">
                    <h5 class="font-medium text-gray-800 flex-1">${this.escapeHtml(title)}</h5>
                    <span class="text-xs text-gray-500 whitespace-nowrap ml-2">
                        ${this.formatDate(pubDate)}
                    </span>
                </div>
                <p class="text-sm text-gray-600 mb-2">${this.escapeHtml(content.substring(0, 150))}...</p>
                <div class="flex justify-between items-center">
                    <div class="flex items-center space-x-2">
                        <span class="text-xs px-2 py-1 rounded ${sentimentClass}">
                            <i class="fas ${sentimentIcon} mr-1"></i>
                            ${sentimentType}
                        </span>
                        <span class="text-xs text-gray-500">${source}</span>
                    </div>
                    ${post.link ? `
                        <a href="${post.link}" target="_blank" 
                           class="text-blue-600 hover:text-blue-800 text-sm">
                            <i class="fas fa-external-link-alt"></i>
                        </a>
                    ` : ''}
                </div>
            </div>
        `;
    }

    static async loadTopThemes() {
        let resultsDiv;
        if (window.location.pathname === '/social') {
            resultsDiv = document.getElementById('top-themes-result');
        } else {
            resultsDiv = document.getElementById('socialResults');
        }

        if (!resultsDiv) {
            console.error('❌ Element de résultats non trouvé');
            return;
        }

        resultsDiv.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin text-blue-600 text-xl"></i><p class="mt-2 text-gray-600">Chargement des thèmes...</p></div>';

        try {
            const response = await fetch('/api/social/top-themes?days=1');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                this.displayTopThemes(data.themes, resultsDiv);
            } else {
                this.showError(resultsDiv, data.error || 'Erreur lors du chargement des thèmes');
            }

        } catch (error) {
            console.error('❌ Erreur loadTopThemes:', error);
            this.showError(resultsDiv, 'Erreur réseau: ' + error.message);
        }
    }

    static displayTopThemes(themes, container) {
        if (!container) {
            console.error('❌ Container non défini dans displayTopThemes');
            return;
        }

        if (!themes || themes.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500 bg-white rounded-lg border">
                    <i class="fas fa-chart-pie text-3xl mb-3"></i>
                    <p>Aucun thème émotionnel détecté</p>
                </div>
            `;
            return;
        }

        const html = `
            <div class="bg-white rounded-lg border">
                <div class="p-4 border-b">
                    <h4 class="font-semibold text-gray-800">Top 5 Thèmes Émotionnels du Jour</h4>
                </div>
                <div class="p-4">
                    ${themes.map((theme, index) => `
                        <div class="flex items-center justify-between p-3 border border-gray-200 rounded-lg mb-2 hover:bg-gray-50">
                            <div class="flex items-center space-x-3">
                                <div class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                    <span class="text-blue-600 font-bold text-sm">${index + 1}</span>
                                </div>
                                <div>
                                    <h5 class="font-medium text-gray-800 capitalize">${theme.theme || 'Inconnu'}</h5>
                                    <p class="text-sm text-gray-600">${theme.posts_count || 0} posts • Score: ${theme.score || 0}</p>
                                </div>
                            </div>
                            <div class="text-right">
                                <div class="text-lg font-bold text-purple-600">${(theme.final_score || 0).toFixed(1)}</div>
                                <div class="text-xs text-gray-500">Engagement total</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    static async compareWithRSS() {
        let resultsDiv;
        if (window.location.pathname === '/social') {
            resultsDiv = document.getElementById('comparison-result');
        } else {
            resultsDiv = document.getElementById('socialResults');
        }

        if (!resultsDiv) {
            console.error('❌ Element de résultats non trouvé');
            return;
        }

        resultsDiv.innerHTML = '<div class="text-center py-4"><i class="fas fa-spinner fa-spin text-purple-600 text-xl"></i><p class="mt-2 text-gray-600">Comparaison en cours...</p></div>';

        try {
            const response = await fetch('/api/social/compare', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ days: 1 })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success) {
                this.displayComparisonResults(data, resultsDiv);
            } else {
                this.showError(resultsDiv, data.error || 'Erreur lors de la comparaison');
            }

        } catch (error) {
            console.error('❌ Erreur compareWithRSS:', error);
            this.showError(resultsDiv, 'Erreur réseau: ' + error.message);
        }
    }

    static displayComparisonResults(data, container) {
        if (!container) {
            console.error('❌ Container non défini dans displayComparisonResults');
            return;
        }

        const summary = data.summary || {};
        const factorZ = summary.factor_z || 0;
        const comparison = data.comparison || {};

        const interpretationColor = this.getInterpretationColor(factorZ);
        const interpretationIcon = this.getInterpretationIcon(factorZ);

        const html = `
            <div class="bg-white rounded-lg border">
                <div class="p-4 border-b">
                    <h4 class="font-semibold text-gray-800">
                        <i class="fas fa-balance-scale text-purple-600 mr-2"></i>
                        Comparaison RSS vs Réseaux Sociaux
                    </h4>
                </div>
                <div class="p-4 space-y-4">
                    <!-- Facteur Z principal -->
                    <div class="bg-gradient-to-r from-purple-50 to-blue-50 border-l-4 border-purple-500 p-4 rounded">
                        <div class="flex items-center justify-between">
                            <div>
                                <h5 class="font-bold text-lg text-gray-800">Facteur Z: ${factorZ.toFixed(3)}</h5>
                                <p class="text-sm text-gray-600">${summary.interpretation || 'Aucune interprétation disponible'}</p>
                            </div>
                            <div class="text-right">
                                <div class="text-2xl font-bold ${interpretationColor}">
                                    <i class="fas ${interpretationIcon}"></i>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Métriques détaillées -->
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-blue-50 p-3 rounded">
                            <h6 class="font-semibold text-blue-800">Médias Traditionnels (RSS)</h6>
                            <p class="text-2xl font-bold text-blue-600">${(summary.rss_sentiment || 0).toFixed(3)}</p>
                            <p class="text-sm text-blue-600">Sentiment moyen</p>
                        </div>
                        <div class="bg-green-50 p-3 rounded">
                            <h6 class="font-semibold text-green-800">Réseaux Sociaux</h6>
                            <p class="text-2xl font-bold text-green-600">${(summary.social_sentiment || 0).toFixed(3)}</p>
                            <p class="text-sm text-green-600">Sentiment moyen</p>
                        </div>
                    </div>

                    <!-- Divergence -->
                    <div class="bg-gray-50 p-3 rounded">
                        <h6 class="font-semibold text-gray-800">Analyse de Divergence</h6>
                        <p class="text-lg font-bold text-gray-600">Écart absolu: ${(summary.divergence || 0).toFixed(3)}</p>
                        <p class="text-sm text-gray-600">Plus l'écart est élevé, plus la dissonance médiatique est importante</p>
                    </div>

                    <!-- Recommandations -->
                    ${comparison.recommendations ? `
                        <div class="bg-yellow-50 border border-yellow-200 p-3 rounded">
                            <h6 class="font-semibold text-yellow-800 mb-2">Recommandations</h6>
                            ${comparison.recommendations.map(rec => `
                                <div class="mb-2">
                                    <span class="text-xs px-2 py-1 rounded ${this.getRecommendationClass(rec.level)}">${rec.level}</span>
                                    <p class="text-sm text-gray-700 mt-1">${rec.message}</p>
                                    <p class="text-xs text-gray-600">${rec.action}</p>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    static async loadStatistics() {
        try {
            const response = await fetch('/api/social/statistics?days=7');

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.updateStatsDisplay(data.statistics);
                }
            }
        } catch (error) {
            console.error('❌ Erreur chargement stats:', error);
        }

        try {
            const response = await fetch('/api/social/comparison-history?limit=1');

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.history && data.history.length > 0) {
                    const latestFactorZ = data.history[0].factor_z;
                    const factorZElement = document.getElementById('factorZ');
                    const modalFactorZ = document.getElementById('modalFactorZ');

                    if (factorZElement) {
                        factorZElement.textContent = (latestFactorZ || 0).toFixed(2);
                    }
                    if (modalFactorZ) {
                        modalFactorZ.textContent = (latestFactorZ || 0).toFixed(2);
                    }
                }
            }
        } catch (error) {
            console.error('❌ Erreur chargement factor Z:', error);
        }
    }

    static updateStatsDisplay(stats) {
        if (!stats) return;

        const elements = {
            'totalPosts': stats.total_posts || 0,
            'positivePosts': stats.sentiment_distribution?.positive || 0,
            'negativePosts': stats.sentiment_distribution?.negative || 0,
            'modalTotalPosts': stats.total_posts || 0,
            'modalPositivePosts': stats.sentiment_distribution?.positive || 0,
            'modalNegativePosts': stats.sentiment_distribution?.negative || 0
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
    }

    // Utilitaires
    static getSentimentClass(sentiment) {
        switch (sentiment) {
            case 'positive': return 'bg-green-100 text-green-800';
            case 'negative': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }

    static getSentimentIcon(sentiment) {
        switch (sentiment) {
            case 'positive': return 'fa-smile';
            case 'negative': return 'fa-frown';
            default: return 'fa-meh';
        }
    }

    static getInterpretationColor(factorZ) {
        if (Math.abs(factorZ) > 2.5) return 'text-red-600';
        if (Math.abs(factorZ) > 1.5) return 'text-orange-600';
        if (Math.abs(factorZ) > 0.5) return 'text-yellow-600';
        return 'text-green-600';
    }

    static getInterpretationIcon(factorZ) {
        if (Math.abs(factorZ) > 2.5) return 'fa-exclamation-triangle';
        if (Math.abs(factorZ) > 1.5) return 'fa-warning';
        if (Math.abs(factorZ) > 0.5) return 'fa-info-circle';
        return 'fa-check-circle';
    }

    static getRecommendationClass(level) {
        switch (level) {
            case 'critical': return 'bg-red-100 text-red-800';
            case 'warning': return 'bg-yellow-100 text-yellow-800';
            case 'success': return 'bg-green-100 text-green-800';
            default: return 'bg-blue-100 text-blue-800';
        }
    }

    static formatDate(dateString) {
        if (!dateString) return 'Date inconnue';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('fr-FR', {
                day: 'numeric',
                month: 'short',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch (e) {
            return 'Date invalide';
        }
    }

    static escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    static showError(container, message) {
        if (!container) {
            console.error('❌ Container non défini pour afficher l\'erreur:', message);
            return;
        }

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
    window.SocialAggregatorManager = SocialAggregatorManager;
    console.log('✅ SocialAggregatorManager initialisé');

    // Charger les statistiques automatiquement sur la page sociale
    if (window.location.pathname === '/social' || window.location.pathname.includes('social')) {
        console.log('🔄 Chargement automatique des statistiques sociales...');
        SocialAggregatorManager.loadStatistics();
    }
});