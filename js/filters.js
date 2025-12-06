// static/js/filters.js - Gestion des filtres avancés

class FilterManager {
    static currentFilters = {
        theme: 'all',
        sentiment: 'all',
        source: 'all',
        dateFrom: null,
        dateTo: null,
        searchTerm: ''
    };

    static async showAdvancedFilters() {
        const content = document.getElementById('themeManagerContent');
        const title = document.getElementById('modalTitle');

        if (!content || !title) return;

        title.textContent = 'Filtres Avancés';

        // Charger les thèmes et sources disponibles
        const themes = await this.loadAvailableThemes();
        const sources = await this.loadAvailableSources();

        content.innerHTML = `
            <div class="max-w-4xl mx-auto">
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    <!-- Filtre par thème -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            <i class="fas fa-tags mr-1"></i> Thème
                        </label>
                        <select id="filterTheme" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
                            <option value="all">Tous les thèmes</option>
                            ${themes.map(theme => `
                                <option value="${theme.id}" ${this.currentFilters.theme === theme.id ? 'selected' : ''}>
                                    ${theme.name}
                                </option>
                            `).join('')}
                        </select>
                    </div>

                    <!-- Filtre par sentiment -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            <i class="fas fa-smile mr-1"></i> Sentiment
                        </label>
                        <select id="filterSentiment" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
                            <option value="all" ${this.currentFilters.sentiment === 'all' ? 'selected' : ''}>Tous</option>
                            <option value="positive" ${this.currentFilters.sentiment === 'positive' ? 'selected' : ''}>Positif</option>
                            <option value="negative" ${this.currentFilters.sentiment === 'negative' ? 'selected' : ''}>Négatif</option>
                            <option value="neutral" ${this.currentFilters.sentiment === 'neutral' ? 'selected' : ''}>Neutre</option>
                        </select>
                    </div>

                    <!-- Filtre par source -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            <i class="fas fa-rss mr-1"></i> Source RSS
                        </label>
                        <select id="filterSource" class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
                            <option value="all">Toutes les sources</option>
                            ${sources.map(source => `
                                <option value="${source}" ${this.currentFilters.source === source ? 'selected' : ''}>
                                    ${this.extractDomain(source)}
                                </option>
                            `).join('')}
                        </select>
                    </div>

                    <!-- Recherche par mot-clé -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            <i class="fas fa-search mr-1"></i> Recherche
                        </label>
                        <input type="text" id="filterSearch" 
                               value="${this.currentFilters.searchTerm}"
                               placeholder="Mot-clé dans le titre ou contenu"
                               class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
                    </div>

                    <!-- Date de début -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            <i class="fas fa-calendar-alt mr-1"></i> Date de début
                        </label>
                        <input type="date" id="filterDateFrom" 
                               value="${this.currentFilters.dateFrom || ''}"
                               class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
                    </div>

                    <!-- Date de fin -->
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            <i class="fas fa-calendar-alt mr-1"></i> Date de fin
                        </label>
                        <input type="date" id="filterDateTo" 
                               value="${this.currentFilters.dateTo || ''}"
                               class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
                    </div>
                </div>

                <!-- Boutons d'action -->
                <div class="flex space-x-3 mb-6">
                    <button onclick="FilterManager.applyFilters()" 
                            class="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition duration-200">
                        <i class="fas fa-filter mr-2"></i>Appliquer les filtres
                    </button>
                    <button onclick="FilterManager.resetFilters()" 
                            class="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600 transition duration-200">
                        <i class="fas fa-undo mr-2"></i>Réinitialiser
                    </button>
                    <button onclick="FilterManager.exportFiltered()" 
                            class="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition duration-200">
                        <i class="fas fa-download mr-2"></i>Exporter les résultats
                    </button>
                </div>

                <!-- Résultats filtrés -->
                <div class="border-t pt-6">
                    <div class="flex justify-between items-center mb-4">
                        <h4 class="font-bold text-gray-800">Résultats</h4>
                        <span id="filterCount" class="text-sm text-gray-600">0 articles trouvés</span>
                    </div>
                    <div id="filteredResults" class="space-y-3 max-h-96 overflow-y-auto">
                        <div class="text-center py-8 text-gray-500">
                            <i class="fas fa-filter text-3xl mb-3"></i>
                            <p>Configurez vos filtres et cliquez sur "Appliquer"</p>
                        </div>
                    </div>
                </div>
            </div>
        `;

        ModalManager.showModal('themeManagerModal');
    }

    static async loadAvailableThemes() {
        try {
            const data = await ApiClient.get('/api/themes');
            return data.themes || [];
        } catch (error) {
            console.error('Erreur chargement thèmes:', error);
            return [];
        }
    }

    static async loadAvailableSources() {
        try {
            const data = await ApiClient.get('/api/sources');
            return data.sources || [];
        } catch (error) {
            console.error('Erreur chargement sources:', error);
            return [];
        }
    }

    static extractDomain(url) {
        try {
            const domain = new URL(url).hostname;
            return domain.replace('www.', '');
        } catch (e) {
            return url;
        }
    }

    static async applyFilters() {
        // Récupérer les valeurs des filtres
        this.currentFilters = {
            theme: document.getElementById('filterTheme')?.value || 'all',
            sentiment: document.getElementById('filterSentiment')?.value || 'all',
            source: document.getElementById('filterSource')?.value || 'all',
            dateFrom: document.getElementById('filterDateFrom')?.value || null,
            dateTo: document.getElementById('filterDateTo')?.value || null,
            searchTerm: document.getElementById('filterSearch')?.value || ''
        };

        // Construire l'URL avec les paramètres
        const params = new URLSearchParams();
        if (this.currentFilters.theme !== 'all') params.append('theme', this.currentFilters.theme);
        if (this.currentFilters.sentiment !== 'all') params.append('sentiment', this.currentFilters.sentiment);
        if (this.currentFilters.source !== 'all') params.append('source', this.currentFilters.source);
        if (this.currentFilters.dateFrom) params.append('date_from', this.currentFilters.dateFrom);
        if (this.currentFilters.dateTo) params.append('date_to', this.currentFilters.dateTo);
        if (this.currentFilters.searchTerm) params.append('search', this.currentFilters.searchTerm);
        params.append('limit', '100');

        try {
            const data = await ApiClient.get(`/api/articles/filter?${params.toString()}`);
            this.displayFilteredResults(data.articles || []);
        } catch (error) {
            console.error('Erreur filtrage:', error);
            this.showError('Erreur lors de l\'application des filtres');
        }
    }

    static displayFilteredResults(articles) {
        const container = document.getElementById('filteredResults');
        const countElement = document.getElementById('filterCount');

        if (!container) return;

        countElement.textContent = `${articles.length} article${articles.length !== 1 ? 's' : ''} trouvé${articles.length !== 1 ? 's' : ''}`;

        if (articles.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-search text-3xl mb-3"></i>
                    <p>Aucun article ne correspond à vos critères</p>
                    <p class="text-sm mt-2">Essayez d'élargir vos filtres</p>
                </div>
            `;
            return;
        }

        container.innerHTML = articles.map(article => `
            <div class="border-l-4 ${this.getSentimentBorderColor(article.sentiment)} bg-white border border-gray-200 p-4 rounded-r-lg hover:shadow-md transition duration-200">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-semibold text-gray-800 flex-1">${article.title}</h4>
                    <span class="text-xs text-gray-500 whitespace-nowrap ml-2">
                        ${this.formatDate(article.pub_date)}
                    </span>
                </div>
                <p class="text-gray-600 text-sm mb-3">${this.truncate(article.content, 150)}</p>
                <div class="flex justify-between items-center">
                    <div class="flex space-x-2">
                        <span class="text-xs px-2 py-1 rounded-full ${this.getSentimentBadge(article.sentiment)}">
                            <i class="fas ${this.getSentimentIcon(article.sentiment)} mr-1"></i>
                            ${article.sentiment || 'neutral'}
                        </span>
                        ${article.feed_url ? `
                            <span class="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700">
                                ${this.extractDomain(article.feed_url)}
                            </span>
                        ` : ''}
                    </div>
                    ${article.link ? `
                        <a href="${article.link}" target="_blank" 
                           class="text-indigo-600 hover:text-indigo-800 text-sm font-medium flex items-center">
                            Lire <i class="fas fa-external-link-alt ml-1 text-xs"></i>
                        </a>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    static resetFilters() {
        this.currentFilters = {
            theme: 'all',
            sentiment: 'all',
            source: 'all',
            dateFrom: null,
            dateTo: null,
            searchTerm: ''
        };

        document.getElementById('filterTheme').value = 'all';
        document.getElementById('filterSentiment').value = 'all';
        document.getElementById('filterSource').value = 'all';
        document.getElementById('filterDateFrom').value = '';
        document.getElementById('filterDateTo').value = '';
        document.getElementById('filterSearch').value = '';

        const container = document.getElementById('filteredResults');
        container.innerHTML = `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-filter text-3xl mb-3"></i>
                <p>Filtres réinitialisés</p>
                <p class="text-sm mt-2">Cliquez sur "Appliquer" pour voir tous les articles</p>
            </div>
        `;

        document.getElementById('filterCount').textContent = '0 articles trouvés';
    }

    static async exportFiltered() {
        // Récupérer les articles filtrés actuels
        const params = new URLSearchParams();
        if (this.currentFilters.theme !== 'all') params.append('theme', this.currentFilters.theme);
        if (this.currentFilters.sentiment !== 'all') params.append('sentiment', this.currentFilters.sentiment);
        if (this.currentFilters.source !== 'all') params.append('source', this.currentFilters.source);
        if (this.currentFilters.dateFrom) params.append('date_from', this.currentFilters.dateFrom);
        if (this.currentFilters.dateTo) params.append('date_to', this.currentFilters.dateTo);
        if (this.currentFilters.searchTerm) params.append('search', this.currentFilters.searchTerm);
        params.append('format', 'csv');

        window.location.href = `/api/articles/export?${params.toString()}`;
    }

    // Fonctions utilitaires
    static getSentimentBorderColor(sentiment) {
        switch (sentiment) {
            case 'positive': return 'border-green-500';
            case 'negative': return 'border-red-500';
            default: return 'border-gray-500';
        }
    }

    static getSentimentBadge(sentiment) {
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

    static formatDate(dateString) {
        if (!dateString) return 'Date inconnue';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('fr-FR', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            });
        } catch (e) {
            return 'Date invalide';
        }
    }

    static truncate(text, maxLength) {
        if (!text) return 'Aucun contenu';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    static showError(message) {
        const container = document.getElementById('filteredResults');
        if (container) {
            container.innerHTML = `
                <div class="text-center py-8 text-red-500">
                    <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                    <p>${message}</p>
                </div>
            `;
        }
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    window.FilterManager = FilterManager;
    console.log('✅ FilterManager initialisé');
});