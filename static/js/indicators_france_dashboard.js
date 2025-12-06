// static/js/indicators_france_dashboard.js

class FranceIndicatorsDashboard {
    constructor() {
        this.currentData = {};
        this.currentChart = null;
        this.refreshInterval = null;
        this.init();
    }

    async init() {
        console.log('🚀 Initialisation Dashboard France...');

        try {
            await this.loadAllData();
            this.setupEventListeners();
            this.startAutoRefresh();
            console.log('✅ Dashboard France initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
            this.showError('Erreur initialisation dashboard');
        }
    }

    setupEventListeners() {
        // Boutons principaux
        document.addEventListener('click', (e) => {
            if (e.target.id === 'refreshDataBtn' || e.target.closest('#refreshDataBtn')) {
                e.preventDefault();
                this.forceRefresh();
            }
        });

        // Sélection période
        const periodSelect = document.getElementById('periodSelect');
        if (periodSelect) {
            periodSelect.addEventListener('change', (e) => {
                this.loadHistoricalChart('^FCHI', e.target.value);
            });
        }
    }

    async loadAllData() {
        try {
            this.showLoading();

            // Récupérer toutes les données via l'endpoint
            const response = await fetch('/indicators/france/api/dashboard');
            const data = await response.json();

            if (data.success) {
                this.currentData = data;
                console.log('📊 Données France reçues:', data);
                this.renderAllComponents();
                this.updateSystemStatus(data);
            } else {
                throw new Error(data.error || 'Erreur chargement données');
            }

        } catch (error) {
            console.error('❌ Erreur chargement données:', error);
            this.showError('Erreur de connexion');
        }
    }

    renderAllComponents() {
        // 1. Indicateurs Eurostat
        this.renderEurostatIndicators();

        // 2. Indicateurs INSEE
        this.renderInseeIndicators();

        // 3. Tableau détaillé
        this.renderDetailedTable();

        // 4. Graphique CAC 40
        this.loadHistoricalChart('^FCHI', '6mo');

        // 5. Mise à jour timestamp
        this.updateTimestamp();
    }

    renderEurostatIndicators() {
        const grid = document.getElementById('eurostatIndicatorsGrid');
        if (!grid) return;

        const eurostatIndicators = Object.entries(this.currentData.indicators || {})
            .filter(([id, _]) => id.startsWith('eurostat_'));

        if (eurostatIndicators.length === 0) {
            grid.innerHTML = '<div class="col-span-4 text-center text-gray-500">Aucun indicateur Eurostat disponible</div>';
            return;
        }

        grid.innerHTML = eurostatIndicators.map(([id, indicator]) =>
            this.createIndicatorCard(indicator, 'eurostat')
        ).join('');
    }

    renderInseeIndicators() {
        const grid = document.getElementById('inseeIndicatorsGrid');
        if (!grid) return;

        const inseeIndicators = Object.entries(this.currentData.indicators || {})
            .filter(([id, _]) => id.startsWith('insee_'));

        if (inseeIndicators.length === 0) {
            grid.innerHTML = '<div class="col-span-3 text-center text-gray-500">Aucun indicateur INSEE disponible</div>';
            return;
        }

        grid.innerHTML = inseeIndicators.map(([id, indicator]) =>
            this.createIndicatorCard(indicator, 'insee')
        ).join('');
    }

    createIndicatorCard(indicator, sourceType) {
        const trendIcon = indicator.change_percent > 0 ? '📈' :
            indicator.change_percent < 0 ? '📉' : '➡️';
        const trendColor = indicator.change_percent > 0 ? 'text-green-600' :
            indicator.change_percent < 0 ? 'text-red-600' : 'text-gray-600';

        // Couleurs par source
        const sourceColors = {
            'eurostat': 'from-blue-600 to-blue-800',
            'insee': 'from-yellow-600 to-yellow-800'
        };

        const gradient = sourceColors[sourceType] || 'from-gray-600 to-gray-800';

        // Badge de fiabilité
        const reliabilityBadge = {
            'official': '<span class="text-xs bg-white bg-opacity-30 px-2 py-1 rounded-full">🔵 Officiel</span>',
            'scraped': '<span class="text-xs bg-white bg-opacity-30 px-2 py-1 rounded-full">🟢 Temps réel</span>',
            'fallback': '<span class="text-xs bg-white bg-opacity-30 px-2 py-1 rounded-full">🟡 Cache</span>'
        };

        return `
            <div class="bg-gradient-to-br ${gradient} rounded-xl shadow-lg p-6 text-white border-2 border-white border-opacity-20 transform hover:scale-105 transition duration-200">
                <div class="flex items-center justify-between mb-3">
                    <h3 class="text-lg font-semibold text-white">${this.truncateName(indicator.name)}</h3>
                    ${sourceType === 'insee' ? '<i class="fas fa-star text-yellow-300"></i>' : ''}
                </div>
                
                <div class="text-3xl font-bold mb-2 text-white">
                    ${indicator.value} ${indicator.unit}
                </div>
                
                <div class="flex justify-between items-center text-sm mb-2">
                    <span class="font-medium text-white opacity-90">
                        ${trendIcon} ${indicator.change_percent >= 0 ? '+' : ''}${indicator.change_percent.toFixed(2)}%
                    </span>
                    <span class="text-white opacity-90">${indicator.period}</span>
                </div>
                
                <div class="text-xs opacity-75 mb-2 text-white">
                    <span title="${indicator.description}">
                        ${indicator.source}
                    </span>
                </div>
                
                <div class="mt-2">
                    ${reliabilityBadge[indicator.reliability] || ''}
                </div>
            </div>
        `;
    }

    renderDetailedTable() {
        const tbody = document.getElementById('detailedTableBody');
        if (!tbody) return;

        // Trier par source (Eurostat d'abord)
        const allIndicators = Object.entries(this.currentData.indicators || {})
            .sort(([a], [b]) => {
                if (a.startsWith('eurostat_') && !b.startsWith('eurostat_')) return -1;
                if (!a.startsWith('eurostat_') && b.startsWith('eurostat_')) return 1;
                return 0;
            });

        if (allIndicators.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-8 text-center text-gray-500">
                        Aucune donnée disponible
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = allIndicators.map(([id, indicator]) => {
            const trendClass = indicator.change_percent > 0 ? 'text-green-600 font-medium' :
                indicator.change_percent < 0 ? 'text-red-600 font-medium' : 'text-gray-600';

            const reliabilityIcon = indicator.reliability_icon || '⚪';

            return `
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 text-sm">
                        <span class="text-lg mr-2">${reliabilityIcon}</span>
                        <span class="font-medium text-gray-900">${indicator.name}</span>
                        <div class="text-xs text-gray-500 mt-1">
                            ${id.startsWith('eurostat_') ? '🇪🇺 Eurostat' : '🇫🇷 INSEE'}
                        </div>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-500">${indicator.value} ${indicator.unit}</td>
                    <td class="px-6 py-4 text-sm ${trendClass}">
                        ${indicator.change_percent >= 0 ? '+' : ''}${indicator.change_percent.toFixed(2)}%
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-500">${indicator.period}</td>
                    <td class="px-6 py-4 text-sm text-gray-500">${indicator.source}</td>
                    <td class="px-6 py-4 text-xs">
                        <span class="px-2 py-1 rounded-full ${indicator.reliability === 'official' ? 'bg-blue-100 text-blue-800' :
                    indicator.reliability === 'scraped' ? 'bg-green-100 text-green-800' :
                        'bg-yellow-100 text-yellow-800'
                }">
                            ${indicator.reliability}
                        </span>
                    </td>
                </tr>
            `;
        }).join('');
    }

    async loadHistoricalChart(symbol, period) {
        try {
            const response = await fetch(`/indicators/france/api/historical/${symbol}?period=${period}`);
            const data = await response.json();

            if (data.success) {
                this.renderChart(data.data);

                const info = document.getElementById('cac40Info');
                if (info && data.data.length > 0) {
                    const latest = data.data[data.data.length - 1];
                    info.textContent = `Dernière valeur: ${latest.close} pts (${latest.date})`;
                }
            }
        } catch (error) {
            console.error('❌ Erreur graphique:', error);
        }
    }

    renderChart(data) {
        const ctx = document.getElementById('mainChart');
        if (!ctx) return;

        if (this.currentChart) {
            this.currentChart.destroy();
        }

        const dates = data.map(item => item.date);
        const values = data.map(item => item.close);

        this.currentChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'CAC 40',
                    data: values,
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                    tooltip: { 
                        mode: 'index', 
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                return `CAC 40: ${context.parsed.y.toFixed(2)} points`;
                            }
                        }
                    }
                },
                scales: {
                    y: { 
                        beginAtZero: false, 
                        grid: { color: 'rgba(0, 0, 0, 0.05)' },
                        ticks: {
                            callback: function(value) {
                                return value.toLocaleString() + ' pts';
                            }
                        }
                    },
                    x: { 
                        grid: { display: false },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }

    updateSystemStatus(data) {
        const statusDiv = document.getElementById('systemStatus');
        if (!statusDiv) return;

        const quality = data.summary?.data_quality || 'acceptable';
        const qualityInfo = {
            'excellent': { icon: '🟢', text: 'Excellente', color: 'green' },
            'good': { icon: '🟡', text: 'Bonne', color: 'yellow' },
            'acceptable': { icon: '🟠', text: 'Acceptable', color: 'orange' },
            'limited': { icon: '🔴', text: 'Limité', color: 'red' }
        };

        const info = qualityInfo[quality] || qualityInfo['acceptable'];

        const sourcesHtml = Object.entries(data.sources || {})
            .map(([source, status]) => {
                const icon = status === 'operational' ? '✅' : '❌';
                return `<span class="text-sm">${icon} ${source}</span>`;
            })
            .join(' • ');

        statusDiv.innerHTML = `
            <div class="relative">
                <div class="flex items-center justify-between flex-wrap gap-4">
                    <div class="flex items-center">
                        <span class="text-2xl mr-3">${info.icon}</span>
                        <div>
                            <h4 class="font-semibold text-${info.color}-800">
                                Qualité des données: ${info.text}
                            </h4>
                            <p class="text-sm text-${info.color}-700">${sourcesHtml}</p>
                        </div>
                    </div>
                    <div class="flex flex-wrap gap-2 items-center">
                        <button id="refreshDataBtn" class="bg-${info.color}-600 hover:bg-${info.color}-700 text-white px-4 py-2 rounded-lg text-sm transition whitespace-nowrap flex items-center shadow-md">
                            <i class="fas fa-sync-alt mr-2"></i>Actualiser
                        </button>
                        <a href="/indicators" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm transition whitespace-nowrap flex items-center shadow-md">
                            <i class="fas fa-globe mr-2"></i>Indicateurs Internationaux
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    async forceRefresh() {
        try {
            this.showNotification('🔄 Rafraîchissement en cours...', 'info');

            const response = await fetch('/indicators/france/api/refresh', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                this.currentData = data;
                this.renderAllComponents();
                this.showNotification('✅ Données françaises rafraîchies', 'success');
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('❌ Erreur refresh:', error);
            this.showNotification('❌ Erreur rafraîchissement', 'error');
        }
    }

    startAutoRefresh() {
        // Auto-refresh toutes les 5 minutes
        this.refreshInterval = setInterval(() => {
            console.log('🔄 Auto-refresh données françaises...');
            this.loadAllData();
        }, 5 * 60 * 1000);
    }

    truncateName(name) {
        return name.length > 30 ? name.substring(0, 27) + '...' : name;
    }

    updateTimestamp() {
        const lastUpdate = document.getElementById('lastUpdate');
        if (lastUpdate) {
            const now = new Date();
            lastUpdate.textContent = now.toLocaleString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }

    showLoading() {
        const tbody = document.getElementById('detailedTableBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-8 text-center text-gray-500">
                        <i class="fas fa-spinner fa-spin mr-2"></i>Chargement des données...
                    </td>
                </tr>
            `;
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        const colors = {
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'warning': 'bg-yellow-500',
            'info': 'bg-blue-500'
        };

        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${colors[type]} text-white transform transition-all duration-300`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    window.franceDashboard = new FranceIndicatorsDashboard();
    console.log('✅ Dashboard France chargé');
});
