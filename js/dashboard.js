// static/js/dashboard.js - VERSION CORRIGÉE (4 CATÉGORIES TEMPORELLES)

class DashboardManager {
    static charts = {
        sentiment: null,
        theme: null,
        timeline: null
    };

    static async loadDashboardData() {
        try {
            console.log('📊 Chargement des données dashboard...');
            const data = await ApiClient.get('/api/stats');
            console.log('📊 Données dashboard reçues:', data);

            if (!data.success) {
                console.error('❌ Erreur API stats:', data.error);
                this.showError('Erreur lors du chargement des statistiques');
                return;
            }

            this.updateStatsCards(data);
            this.createCharts(data);
            this.loadPopularThemes(data.theme_stats);
        } catch (error) {
            console.error('❌ Erreur chargement dashboard:', error);
            this.showError('Impossible de charger le dashboard');
        }
    }

    static updateStatsCards(data) {
        const elements = {
            'statTotalArticles': data.total_articles || 0,
            'statPositiveArticles': data.sentiment_distribution?.positive || 0,
            'statNegativeArticles': data.sentiment_distribution?.negative || 0,
            'statActiveThemes': Object.keys(data.theme_stats || {}).length
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                element.classList.add('pulse-animation');
                setTimeout(() => element.classList.remove('pulse-animation'), 1000);
            }
        });

        console.log('✅ Stats mises à jour:', elements);
    }

    static createCharts(data) {
        this.createSentimentChart(data.sentiment_distribution);
        this.createThemeChart(data.theme_stats);
        this.createTimelineChart(data.timeline_data);
    }

    static createSentimentChart(sentimentData) {
        const ctx = document.getElementById('sentimentChart');
        if (!ctx) {
            console.error('❌ Canvas sentimentChart non trouvé');
            return;
        }

        if (this.charts.sentiment) {
            this.charts.sentiment.destroy();
        }

        const labels = ['Positif', 'Neutre Positif', 'Neutre Négatif', 'Négatif'];
        const dataValues = [
            sentimentData?.positive || 0,
            sentimentData?.neutral_positive || 0,
            sentimentData?.neutral_negative || 0,
            sentimentData?.negative || 0
        ];

        const total = dataValues.reduce((a, b) => a + b, 0);

        if (total === 0) {
            ctx.parentElement.innerHTML = `
                <div class="flex items-center justify-center h-80 text-gray-500">
                    <div class="text-center">
                        <i class="fas fa-chart-pie text-4xl mb-3"></i>
                        <p>Aucune donnée de sentiment disponible</p>
                        <p class="text-sm mt-2">Les sentiments apparaîtront après l'analyse des articles</p>
                    </div>
                </div>
            `;
            return;
        }

        this.charts.sentiment = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: dataValues,
                    backgroundColor: [
                        '#10B981', '#60A5FA', '#FBBF24', '#EF4444'
                    ],
                    borderWidth: 2,
                    borderColor: '#FFFFFF'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    static createThemeChart(themeData) {
        const ctx = document.getElementById('themeChart');
        if (!ctx) {
            console.warn('⚠️ Canvas themeChart non trouvé');
            return;
        }

        if (this.charts.theme) {
            this.charts.theme.destroy();
        }

        if (!themeData || Object.keys(themeData).length === 0) {
            ctx.parentElement.innerHTML = `
                <div class="flex items-center justify-center h-80 text-gray-500">
                    <div class="text-center">
                        <i class="fas fa-chart-bar text-4xl mb-3"></i>
                        <p>Aucun article analysé par thème</p>
                        <p class="text-sm mt-2">Les thèmes apparaîtront après l'analyse des articles</p>
                    </div>
                </div>
            `;
            return;
        }

        const themes = Object.entries(themeData)
            .filter(([_, data]) => data.article_count > 0)
            .sort((a, b) => b[1].article_count - a[1].article_count)
            .slice(0, 10);

        if (themes.length === 0) {
            ctx.parentElement.innerHTML = `
                <div class="flex items-center justify-center h-80 text-gray-500">
                    <div class="text-center">
                        <i class="fas fa-chart-bar text-4xl mb-3"></i>
                        <p>Aucun article associé aux thèmes</p>
                    </div>
                </div>
            `;
            return;
        }

        const labels = themes.map(([_, data]) => data.name);
        const counts = themes.map(([_, data]) => data.article_count);
        const colors = themes.map(([_, data]) => data.color || '#6366f1');

        const maxCount = Math.max(...counts);
        const stepSize = this.calculateOptimalStepSize(maxCount);

        this.charts.theme = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Nombre d\'articles',
                    data: counts,
                    backgroundColor: colors,
                    borderWidth: 0,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            title: (context) => context[0].label,
                            label: (context) => `Articles: ${context.parsed.y}`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: stepSize,
                            precision: 0,
                            maxTicksLimit: 10
                        },
                        title: {
                            display: true,
                            text: 'Nombre d\'articles'
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }

    static async createTimelineChart(timelineData) {
        const ctx = document.getElementById('timelineChart');
        if (!ctx) return;

        if (this.charts.timeline) {
            this.charts.timeline.destroy();
        }

        if (!timelineData) {
            try {
                const response = await ApiClient.get('/api/stats/timeline');
                timelineData = response.timeline;
            } catch (error) {
                console.error('Erreur récupération timeline:', error);
                timelineData = null;
            }
        }

        if (!timelineData || timelineData.length === 0) {
            ctx.parentElement.innerHTML = `
                <div class="flex items-center justify-center h-96 text-gray-500">
                    <div class="text-center">
                        <i class="fas fa-chart-line text-4xl mb-3"></i>
                        <p>Données d'évolution temporelle non disponibles</p>
                        <p class="text-sm mt-2">L'historique s'enrichira au fil des analyses</p>
                    </div>
                </div>
            `;
            return;
        }

        const labels = timelineData.map(d => {
            const date = new Date(d.date);
            return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' });
        });

        // 🎯 MODIFICATION PRINCIPALE : 4 catégories au lieu de 3
        const positiveData = timelineData.map(d => d.positive || 0);
        const neutralPositiveData = timelineData.map(d => d.neutral_positive || 0);
        const neutralNegativeData = timelineData.map(d => d.neutral_negative || 0);
        const negativeData = timelineData.map(d => d.negative || 0);

        const allData = [...positiveData, ...neutralPositiveData, ...neutralNegativeData, ...negativeData];
        const maxValue = Math.max(...allData);
        const stepSize = this.calculateOptimalStepSize(maxValue);

        this.charts.timeline = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Positif',
                        data: positiveData,
                        borderColor: '#10B981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2
                    },
                    {
                        label: 'Neutre Positif',
                        data: neutralPositiveData,
                        borderColor: '#60A5FA',
                        backgroundColor: 'rgba(96, 165, 250, 0.1)',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2
                    },
                    {
                        label: 'Neutre Négatif',
                        data: neutralNegativeData,
                        borderColor: '#FBBF24',
                        backgroundColor: 'rgba(251, 191, 36, 0.1)',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2
                    },
                    {
                        label: 'Négatif',
                        data: negativeData,
                        borderColor: '#EF4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.4,
                        fill: true,
                        borderWidth: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { 
                    mode: 'index', 
                    intersect: false 
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 15,
                            font: { size: 12 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.dataset.label || '';
                                const value = context.parsed.y || 0;
                                return `${label}: ${value} article${value !== 1 ? 's' : ''}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        title: { 
                            display: true, 
                            text: 'Date',
                            font: { size: 12 }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { borderDash: [4, 4] },
                        ticks: { 
                            stepSize: stepSize, 
                            precision: 0 
                        },
                        title: { 
                            display: true, 
                            text: 'Nombre d\'articles',
                            font: { size: 12 }
                        }
                    }
                }
            }
        });

        console.log('✅ Graphique temporel créé avec 4 catégories');
    }

    static loadPopularThemes(themeStats) {
        const container = document.getElementById('popularThemes');
        if (!container) {
            console.warn('⚠️ Container popularThemes non trouvé');
            return;
        }

        console.log('🎯 Données thèmes reçues:', themeStats);

        if (!themeStats || Object.keys(themeStats).length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-tags text-3xl mb-3"></i>
                    <p>Aucune donnée de thème disponible</p>
                    <p class="text-sm mt-2">Les thèmes apparaîtront après la configuration</p>
                </div>
            `;
            return;
        }

        const sortedThemes = Object.entries(themeStats)
            .filter(([themeId, data]) => {
                const hasArticles = data.article_count > 0;
                if (!hasArticles) {
                    console.log(`ℹ️ Thème ${themeId} ignoré: 0 articles`);
                }
                return hasArticles;
            })
            .sort((a, b) => b[1].article_count - a[1].article_count)
            .slice(0, 8);

        console.log('📋 Thèmes triés:', sortedThemes);

        if (sortedThemes.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-tags text-3xl mb-3"></i>
                    <p>Aucun article associé aux thèmes</p>
                    <p class="text-sm mt-2">
                        Configurez les thèmes et analysez des articles pour voir les statistiques
                    </p>
                </div>
            `;
            return;
        }

        container.innerHTML = sortedThemes.map(([themeId, data]) => {
            const color = data.color || '#6366f1';
            const name = data.name || themeId;
            const count = data.article_count || 0;

            return `
                <div class="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition duration-200 mb-3">
                    <div class="flex items-center space-x-4 flex-1">
                        <div class="w-3 h-3 rounded-full flex-shrink-0" style="background-color: ${color}"></div>
                        <div class="flex-1 min-w-0">
                            <span class="font-medium text-gray-800 truncate block" title="${name}">
                                ${name}
                            </span>
                            <p class="text-sm text-gray-600 mt-1">
                                ${count} article${count !== 1 ? 's' : ''}
                            </p>
                        </div>
                    </div>
                    <div class="flex items-center">
                        <span class="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                            ${Math.round((count / Object.values(themeStats).reduce((sum, t) => sum + (t.article_count || 0), 0)) * 100)}%
                        </span>
                    </div>
                </div>
            `;
        }).join('');

        const totalArticles = Object.values(themeStats).reduce((sum, theme) => sum + (theme.article_count || 0), 0);
        const summaryHtml = `
            <div class="mt-4 pt-4 border-t border-gray-200">
                <div class="flex justify-between text-sm text-gray-600">
                    <span>Total articles analysés:</span>
                    <span class="font-medium">${totalArticles}</span>
                </div>
                <div class="flex justify-between text-sm text-gray-600 mt-1">
                    <span>Thèmes actifs:</span>
                    <span class="font-medium">${sortedThemes.length}</span>
                </div>
            </div>
        `;

        container.innerHTML += summaryHtml;

        console.log(`✅ ${sortedThemes.length} thèmes populaires affichés`);
    }

    static calculateOptimalStepSize(maxValue) {
        if (maxValue <= 10) return 1;
        if (maxValue <= 20) return 2;
        if (maxValue <= 50) return 5;
        if (maxValue <= 100) return 10;
        if (maxValue <= 200) return 20;
        if (maxValue <= 500) return 50;
        return Math.ceil(maxValue / 10);
    }

    static showError(message) {
        console.error('🚨', message);
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-red-500 text-white p-4 rounded-lg shadow-lg z-50';
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        document.body.appendChild(notification);

        setTimeout(() => notification.remove(), 5000);
    }

    static refreshDashboard() {
        console.log('🔄 Rafraîchissement du dashboard...');
        this.loadDashboardData();
    }

    static destroyAllCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        this.charts = { sentiment: null, theme: null, timeline: null };
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    console.log('✅ DashboardManager initialisation...');

    if (document.getElementById('sentimentChart')) {
        window.DashboardManager = DashboardManager;
        console.log('✅ DashboardManager initialisé');

        DashboardManager.loadDashboardData();

        const refreshInterval = setInterval(() => DashboardManager.loadDashboardData(), 30000);

        const refreshBtn = document.createElement('button');
        refreshBtn.className = 'fixed bottom-4 right-4 bg-blue-500 text-white p-3 rounded-full shadow-lg z-40 hover:bg-blue-600 transition duration-200';
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i>';
        refreshBtn.title = 'Rafraîchir le dashboard';
        refreshBtn.onclick = () => DashboardManager.refreshDashboard();
        document.body.appendChild(refreshBtn);

        window.addEventListener('beforeunload', () => {
            DashboardManager.destroyAllCharts();
            clearInterval(refreshInterval);
        });
    }
});