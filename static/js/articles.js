// static/js/articles.js - Gestion des articles

class ArticleManager {
    static async loadRecentArticles(limit = 5) {
        try {
            const data = await ApiClient.get(`/api/articles?limit=${limit}`);
            this.displayArticles(data.articles, 'recentArticles');
        } catch (error) {
            this.showError('Erreur lors du chargement des articles');
        }
    }

    static async loadAllArticles() {
        try {
            const data = await ApiClient.get('/api/articles?limit=100');
            this.displayAllArticles(data.articles);
        } catch (error) {
            this.showError('Erreur lors du chargement des articles');
        }
    }

    static displayArticles(articles, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!articles || articles.length === 0) {
            container.innerHTML = this.getNoArticlesTemplate();
            return;
        }

        container.innerHTML = articles.map(article => this.getArticleTemplate(article)).join('');
    }

    static displayAllArticles(articles) {
        const container = document.getElementById('allArticlesList');
        if (!container) return;

        if (!articles || articles.length === 0) {
            container.innerHTML = this.getNoArticlesTemplate();
            return;
        }

        container.innerHTML = articles.map(article => this.getArticleTemplate(article, true)).join('');
    }

    static getArticleTemplate(article, showFullContent = false) {
        const content = showFullContent ?
            (article.content || 'Aucun contenu disponible') :
            Formatters.truncateText(article.content, 200);

        return `
            <div class="border-l-4 ${Formatters.getSentimentColor(article.sentiment)} 
                        bg-white border border-gray-200 p-4 rounded-r-lg hover:shadow-md transition duration-200">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-semibold text-gray-800 text-lg">${article.title}</h4>
                    <span class="text-xs text-gray-500 whitespace-nowrap ml-2">
                        ${Formatters.formatDate(article.pub_date)}
                    </span>
                </div>
                <p class="text-gray-600 text-sm mb-3">${content}</p>
                <div class="flex justify-between items-center">
                    <span class="text-xs px-2 py-1 rounded-full ${Formatters.getSentimentBadge(article.sentiment)}">
                        <i class="fas ${Formatters.getSentimentIcon(article.sentiment)} mr-1"></i>
                        ${article.sentiment || 'neutral'}
                    </span>
                    ${article.link ? `
                    <a href="${article.link}" target="_blank" 
                       class="text-indigo-600 hover:text-indigo-800 text-sm font-medium flex items-center">
                        Lire <i class="fas fa-external-link-alt ml-1 text-xs"></i>
                    </a>
                    ` : ''}
                </div>
            </div>
        `;
    }

    static getNoArticlesTemplate() {
        return `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-newspaper text-3xl mb-3"></i>
                <p>Aucun article disponible</p>
                <p class="text-sm mt-2">Mettez à jour les flux RSS pour commencer</p>
            </div>
        `;
    }

    static showAllArticles() {
        ModalManager.showModal('themeManagerModal');
        const content = document.getElementById('themeManagerContent');
        const title = document.getElementById('modalTitle');

        if (!content || !title) return;

        title.textContent = 'Tous les Articles';

        content.innerHTML = `
            <div class="max-w-6xl mx-auto">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-2xl font-bold text-gray-800">Tous les Articles</h3>
                    <div class="flex space-x-4">
                        <select id="articleFilter" class="border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-indigo-500">
                            <option value="all">Tous les sentiments</option>
                            <option value="positive">Positifs</option>
                            <option value="negative">Négatifs</option>
                            <option value="neutral">Neutres</option>
                        </select>
                    </div>
                </div>
                <div id="allArticlesList" class="space-y-4 max-h-96 overflow-y-auto">
                    <div class="text-center py-8">
                        <i class="fas fa-spinner fa-spin text-2xl text-gray-400 mb-2"></i>
                        <p class="text-gray-500">Chargement des articles...</p>
                    </div>
                </div>
            </div>
        `;

        // Ajouter l'écouteur d'événement pour le filtre
        document.getElementById('articleFilter').addEventListener('change', () => this.filterArticles());

        this.loadAllArticles();
    }

    static async filterArticles() {
        const sentiment = document.getElementById('articleFilter').value;
        let url = '/api/articles?limit=100';

        if (sentiment !== 'all') {
            url += `&sentiment=${sentiment}`;
        }

        try {
            const data = await ApiClient.get(url);
            this.displayAllArticles(data.articles);
        } catch (error) {
            this.showError('Erreur lors du filtrage des articles');
        }
    }

    static showError(message) {
        const container = document.getElementById('recentArticles') || document.getElementById('allArticlesList');
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

// Initialisation des articles
document.addEventListener('DOMContentLoaded', function () {
    window.ArticleManager = ArticleManager;
    console.log('✅ ArticleManager initialisé');

    // Charger les articles récents si on est sur la page d'accueil
    if (document.getElementById('recentArticles')) {
        ArticleManager.loadRecentArticles();
    }
});