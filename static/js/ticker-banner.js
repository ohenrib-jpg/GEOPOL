// static/js/ticker-banner.js - VERSION CORRIGÉE

class TickerBanner {
    constructor() {
        this.tickerData = {
            articles: [],
            stocks: [],
            indicators: [],
            social: {}
        };
        this.updateInterval = null;
        this.isPaused = false;
        this.animationFrame = null;
        this.position = 0;
        this.lastTimestamp = 0;
        this.scrollSpeed = 30;
    }

    async initialize() {
        console.log('🎬 Initialisation du bandeau ticker...');
        this.createBannerHTML();
        await this.loadAllData();
        this.startAutoRefresh();
        this.startSmoothScroll();
        console.log('✅ Bandeau ticker initialisé');
    }

    createBannerHTML() {
        // Vérifier si le bandeau existe déjà
        if (document.getElementById('ticker-banner')) {
            return;
        }

        // Créer le HTML du bandeau
        const bannerHTML = `
            <div id="ticker-banner" class="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-gray-900 via-blue-900 to-gray-900 text-white shadow-lg border-b-2 border-blue-500">
                <div class="relative overflow-hidden h-10">
                    <!-- Contenu défilant -->
                    <div id="ticker-content" class="absolute whitespace-nowrap flex items-center h-full">
                        <div id="ticker-items" class="flex items-center space-x-8">
                            <span class="text-yellow-400 font-bold">
                                <i class="fas fa-sync-alt fa-spin mr-2"></i>Chargement...
                            </span>
                        </div>
                    </div>
                </div>
                
                <!-- Bouton de contrôle -->
                <button id="ticker-toggle" 
                        class="absolute right-2 top-1/2 transform -translate-y-1/2 bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs transition-colors">
                    <i class="fas fa-pause"></i>
                </button>
            </div>
            
            <style>
                #ticker-banner {
                    animation: slideDown 0.3s ease-out;
                }
                
                @keyframes slideDown {
                    from { transform: translateY(-100%); }
                    to { transform: translateY(0); }
                }
                
                body { padding-top: 40px; }
                
                .ticker-highlight {
                    text-shadow: 0 0 10px rgba(96, 165, 250, 0.5);
                }
                
                .ticker-positive { color: #10B981; }
                .ticker-negative { color: #EF4444; }
                .ticker-neutral { color: #60A5FA; }
                .ticker-warning { color: #F59E0B; }
            </style>
        `;

        document.body.insertAdjacentHTML('afterbegin', bannerHTML);

        const toggleBtn = document.getElementById('ticker-toggle');
        toggleBtn.addEventListener('click', () => this.toggleAnimation());
    }

    async loadAllData() {
        try {
            await Promise.all([
                this.loadRecentArticles(),
                this.loadStockData(),
                this.loadIndicators(),
                this.loadSocialData()
            ]);

            this.updateTickerContent();
        } catch (error) {
            console.error('❌ Erreur chargement données ticker:', error);
            this.showError();
        }
    }

    async loadRecentArticles() {
        try {
            const response = await fetch('/api/articles?limit=5');
            if (response.ok) {
                const data = await response.json();
                if (data.articles) {
                    this.tickerData.articles = data.articles.map(article => ({
                        title: this.truncateText(article.title, 80),
                        sentiment: article.detailed_sentiment || article.sentiment,
                        score: article.sentiment_score || 0,
                        pubDate: article.pub_date
                    }));
                }
            }
        } catch (error) {
            console.log('ℹ️ Articles non disponibles:', error.message);
        }
    }

    // ✅ CORRECTION : Utiliser la bonne URL API
    async loadStockData() {
        try {
            const response = await fetch('/indicators/api/indices');

            if (!response.ok) {
                console.log('ℹ️ Service stocks non disponible, ignoré');
                return;
            }

            const data = await response.json();

            if (data.success && data.indices) {
                this.tickerData.stocks = Object.values(data.indices).map(index => ({
                    symbol: index.symbol,
                    name: index.name,
                    price: index.current_price,
                    change: index.change_percent,
                    trend: index.trend
                }));
            }
        } catch (error) {
            console.log('ℹ️ Données boursières non disponibles:', error.message);
        }
    }

    // ✅ CORRECTION : Utiliser le bon endpoint et format
    async loadIndicators() {
        try {
            // Utiliser l'endpoint dashboard qui fonctionne
            const response = await fetch('/indicators/api/dashboard');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.success && data.indicators) {
                this.tickerData.indicators = [];

                // Traiter les indicateurs selon le nouveau format
                Object.values(data.indicators).forEach(indicator => {
                    if (indicator && indicator.name) {
                        // Mapper les indicateurs vers un format cohérent
                        let displayName = indicator.name;
                        let unit = indicator.unit;

                        // Noms d'affichage optimisés
                        const nameMapping = {
                            'PIB': 'PIB',
                            'Inflation': 'IPCH',
                            'Commerce': 'Commerce',
                            'Chômage': 'Chômage',
                            'GINI': 'GINI'
                        };

                        // Trouver le nom court
                        for (const [key, value] of Object.entries(nameMapping)) {
                            if (displayName.includes(key)) {
                                displayName = value;
                                break;
                            }
                        }

                        this.tickerData.indicators.push({
                            name: displayName,
                            value: parseFloat(indicator.value),
                            unit: unit,
                            change: indicator.change_percent,
                            trend: indicator.change_percent > 0 ? 'up' :
                                indicator.change_percent < 0 ? 'down' : 'stable'
                        });
                    }
                });

                console.log('📊 Indicateurs chargés:', this.tickerData.indicators.length);
            }
        } catch (error) {
            console.error('Erreur chargement indicateurs:', error);
        }
    }

    async loadSocialData() {
        try {
            const response = await fetch('/api/social/statistics?days=1');

            if (response.status === 503) {
                console.log('ℹ️ Service social non disponible, ignoré');
                return;
            }

            if (response.ok) {
                const data = await response.json();

                if (data.success && data.statistics) {
                    this.tickerData.social = {
                        totalPosts: data.statistics.total_posts || 0,
                        positive: data.statistics.sentiment_distribution?.positive || 0,
                        negative: data.statistics.sentiment_distribution?.negative || 0
                    };
                }
            }

            // Récupérer le Factor Z
            const comparisonResponse = await fetch('/api/social/comparison-history?limit=1');

            if (comparisonResponse.status === 503) {
                console.log('ℹ️ Service comparaison social non disponible, ignoré');
                return;
            }

            if (comparisonResponse.ok) {
                const comparisonData = await comparisonResponse.json();

                if (comparisonData.success && comparisonData.history?.length > 0) {
                    this.tickerData.social.factorZ = comparisonData.history[0].factor_z;
                }
            }
        } catch (error) {
            console.log('ℹ️ Données sociales non disponibles:', error.message);
        }
    }

    updateTickerContent() {
        const tickerItems = document.getElementById('ticker-items');
        if (!tickerItems) return;

        const items = [];

        // 1. Heure actuelle
        items.push(`
            <span class="ticker-highlight font-bold">
                <i class="fas fa-clock mr-1"></i>
                <span class="current-time">${this.getCurrentTime()}</span>
            </span>
        `);

        // 2. Articles récents avec sentiment
        if (this.tickerData.articles.length > 0) {
            this.tickerData.articles.forEach(article => {
                const sentimentClass = this.getSentimentClass(article.sentiment);
                const sentimentIcon = this.getSentimentIcon(article.sentiment);

                items.push(`
                    <span class="flex items-center">
                        <i class="fas fa-newspaper mr-2 text-blue-400"></i>
                        <span class="font-medium">${article.title}</span>
                        <span class="ml-2 ${sentimentClass}">
                            ${sentimentIcon} ${(Math.abs(article.score) * 100).toFixed(0)}%
                        </span>
                    </span>
                `);
            });
        }

        // 3. Données boursières
        if (this.tickerData.stocks.length > 0) {
            this.tickerData.stocks.forEach(stock => {
                const trendClass = stock.trend === 'up' ? 'ticker-positive' : 'ticker-negative';
                const trendIcon = stock.trend === 'up' ? '📈' : '📉';

                items.push(`
                    <span class="flex items-center">
                        <i class="fas fa-chart-line mr-2 text-yellow-400"></i>
                        <span class="font-bold">${stock.symbol}</span>
                        <span class="ml-2">${stock.price?.toFixed ? stock.price.toFixed(2) : stock.price}</span>
                        <span class="ml-2 ${trendClass}">
                            ${trendIcon} ${stock.change >= 0 ? '+' : ''}${(stock.change || 0).toFixed(2)}%
                        </span>
                    </span>
                `);
            });
        }

        // 4. Indicateurs économiques
        if (this.tickerData.indicators.length > 0) {
            this.tickerData.indicators.forEach(indicator => {
                const trendIcon = indicator.trend === 'up' ? '↗️' :
                    indicator.trend === 'down' ? '↘️' : '➡️';

                let displayValue = '';
                if (indicator.unit === '%') {
                    displayValue = `${(indicator.value || 0).toFixed(1)}%`;
                } else if (indicator.unit && indicator.unit.includes('Milliards')) {
                    displayValue = `${(indicator.value || 0).toLocaleString('fr-FR')} Mds`;
                } else if (indicator.unit && indicator.unit.includes('points')) {
                    displayValue = `${(indicator.value || 0).toLocaleString('fr-FR')} pts`;
                } else {
                    displayValue = `${(indicator.value || 0).toLocaleString('fr-FR')} ${indicator.unit || ''}`;
                }

                items.push(`
                    <span class="flex items-center">
                        <i class="fas fa-chart-bar mr-2 text-purple-400"></i>
                        <span class="font-medium">${indicator.name}:</span>
                        <span class="ml-2 font-bold">${displayValue}</span>
                        ${indicator.change !== undefined ? `
                            <span class="ml-2 text-sm">
                                ${trendIcon} ${indicator.change > 0 ? '+' : ''}${(indicator.change || 0).toFixed(1)}
                            </span>
                        ` : ''}
                    </span>
                `);
            });
        }

        // 5. Réseaux sociaux
        if (this.tickerData.social.totalPosts > 0) {
            items.push(`
                <span class="flex items-center">
                    <i class="fas fa-share-alt mr-2 text-cyan-400"></i>
                    <span class="font-medium">Réseaux Sociaux:</span>
                    <span class="ml-2 ticker-positive">${this.tickerData.social.positive} positifs</span>
                    <span class="mx-1">•</span>
                    <span class="ticker-negative">${this.tickerData.social.negative} négatifs</span>
                </span>
            `);

            if (this.tickerData.social.factorZ !== undefined) {
                const factorZClass = this.getFactorZClass(this.tickerData.social.factorZ);

                items.push(`
                    <span class="flex items-center">
                        <i class="fas fa-balance-scale mr-2 text-orange-400"></i>
                        <span class="font-medium">Factor Z:</span>
                        <span class="ml-2 ${factorZClass} font-bold">
                            ${this.tickerData.social.factorZ.toFixed(3)}
                        </span>
                    </span>
                `);
            }
        }

        // Mettre à jour le contenu
        tickerItems.innerHTML = items.join('<span class="mx-4 text-gray-600">•</span>');

        // Dupliquer le contenu pour un défilement continu
        tickerItems.innerHTML += items.join('<span class="mx-4 text-gray-600">•</span>');
    }

    startSmoothScroll() {
        const tickerContent = document.getElementById('ticker-content');
        const tickerItems = document.getElementById('ticker-items');

        if (!tickerContent || !tickerItems) return;

        const animate = (timestamp) => {
            if (!this.lastTimestamp) this.lastTimestamp = timestamp;

            const deltaTime = timestamp - this.lastTimestamp;
            this.lastTimestamp = timestamp;

            if (!this.isPaused) {
                const moveDistance = (this.scrollSpeed * deltaTime) / 1000;
                this.position -= moveDistance;

                const contentWidth = tickerItems.offsetWidth;
                if (Math.abs(this.position) >= contentWidth / 2) {
                    this.position = 0;
                }

                tickerItems.style.transform = `translateX(${this.position}px)`;
            }

            this.animationFrame = requestAnimationFrame(animate);
        };

        this.animationFrame = requestAnimationFrame(animate);
    }

    startAutoRefresh() {
        // Rafraîchir toutes les 45 secondes
        this.updateInterval = setInterval(() => {
            this.loadAllData();
        }, 45000);

        // Mettre à jour l'heure chaque seconde
        setInterval(() => {
            this.updateClock();
        }, 1000);
    }

    updateClock() {
        const timeElements = document.querySelectorAll('.current-time');
        timeElements.forEach(el => {
            el.textContent = this.getCurrentTime();
        });
    }

    toggleAnimation() {
        this.isPaused = !this.isPaused;
        const toggleBtn = document.getElementById('ticker-toggle');

        if (this.isPaused) {
            toggleBtn.innerHTML = '<i class="fas fa-play"></i>';
        } else {
            toggleBtn.innerHTML = '<i class="fas fa-pause"></i>';
        }
    }

    showError() {
        const tickerItems = document.getElementById('ticker-items');
        if (tickerItems) {
            tickerItems.innerHTML = `
                <span class="text-red-400">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    Erreur de chargement des données
                </span>
            `;
        }
    }

    // Utilitaires
    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString('fr-FR', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    getSentimentClass(sentiment) {
        switch (sentiment?.toLowerCase()) {
            case 'positive': return 'ticker-positive';
            case 'negative': return 'ticker-negative';
            case 'neutral_positive': return 'text-blue-400';
            case 'neutral_negative': return 'text-yellow-400';
            default: return 'ticker-neutral';
        }
    }

    getSentimentIcon(sentiment) {
        switch (sentiment?.toLowerCase()) {
            case 'positive': return '😊';
            case 'negative': return '😟';
            case 'neutral_positive': return '🙂';
            case 'neutral_negative': return '😐';
            default: return '😶';
        }
    }

    getFactorZClass(factorZ) {
        const absZ = Math.abs(factorZ);
        if (absZ > 2.5) return 'ticker-negative';
        if (absZ > 1.5) return 'ticker-warning';
        if (absZ > 0.5) return 'ticker-neutral';
        return 'ticker-positive';
    }

    truncateText(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }
        const banner = document.getElementById('ticker-banner');
        if (banner) {
            banner.remove();
        }
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', function () {
    // Attendre que les autres scripts soient chargés
    setTimeout(() => {
        window.tickerBanner = new TickerBanner();
        window.tickerBanner.initialize();
        console.log('✅ TickerBanner initialisé globalement');
    }, 1000);
});

console.log('✅ ticker-banner.js chargé');
