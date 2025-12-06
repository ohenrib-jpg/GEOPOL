// static/js/indicators_international_dashboard.js

class InternationalIndicatorsDashboard {
    constructor() {
        this.currentData = {};
        this.currentChart = null;
        this.refreshInterval = null;
        this.init();
    }

    async init() {
        console.log('🚀 Initialisation Dashboard International...');

        try {
            await this.loadAllData();
            this.setupEventListeners();
            this.startAutoRefresh();
            console.log('✅ Dashboard International initialisé');
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
                this.loadHistoricalChart('^GSPC', e.target.value);
            });
        }
    }

    async loadAllData() {
        try {
            this.showLoading();

            // Récupérer toutes les données via l'endpoint
            const response = await fetch('/indicators/api/dashboard');
            const data = await response.json();

            if (data.success) {
                this.currentData = data;
                console.log('📊 Données internationales reçues:', data);
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
        // 1. Indices internationaux
        this.renderInternationalIndices();

        // 2. Indices européens
        this.renderEuropeanIndices();

        // 3. Graphique S&P 500
        this.loadHistoricalChart('^GSPC', '6mo');

        // 4. Mise à jour timestamp
        this.updateTimestamp();
    }

    renderInternationalIndices() {
        const container = document.getElementById('internationalIndices');
        if (!container) return;

        const markets = this.currentData.markets || {};

        if (Object.keys(markets).length === 0) {
            container.innerHTML = '<div class="col-span-5 text-center text-gray-500">Chargement indices...</div>';
            return;
        }

        // Indices internationaux principaux
        const mainIndices = ['^GSPC', '^DJI', '^IXIC', '^N225'];
        const filteredMarkets = Object.fromEntries(
            Object.entries(markets).filter(([key]) => mainIndices.includes(key))
        );

        container.innerHTML = Object.values(filteredMarkets).map(index => {
            const trendColor = index.trend === 'up' ? 'text-green-600' : 'text-red-600';
            const trendIcon = index.trend === 'up' ? '↑' : '↓';

            return `
                <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                    <div class="text-sm font-medium text-gray-600 mb-1">${index.name}</div>
                    <div class="text-2xl font-bold text-gray-900 mb-1">${index.current_price}</div>
                    <div class="${trendColor} text-sm font-medium">
                        ${trendIcon} ${index.change_percent >= 0 ? '+' : ''}${index.change_percent.toFixed(2)}%
                    </div>
                </div>
            `;
        }).join('');
    }

    renderEuropeanIndices() {
        const container = document.getElementById('europeanIndices');
        if (!container) return;

        const markets = this.currentData.markets || {};

        // Indices européens
        const europeanIndices = ['^FCHI', '^GDAXI', '^FTSE'];
        const filteredMarkets = Object.fromEntries(
            Object.entries(markets).filter(([key]) => europeanIndices.includes(key))
        );

        if (Object.keys(filteredMarkets).length === 0) {
            container.innerHTML = '<div class="col-span-3 text-center text-gray-500">Chargement indices européens...</div>';
            return;
        }

        container.innerHTML = Object.values(filteredMarkets).map(index => {
            const trendColor = index.trend === 'up' ? 'text-green-600' : 'text-red-600';
            const trendIcon = index.trend === 'up' ? '↑' : '↓';

            return `
                <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                    <div class="text-sm font-medium text-gray-600 mb-1">${index.name}</div>
                    <div class="text-xl font-bold text-gray-900 mb-1">${index.current_price}</div>
                    <div class="${trendColor} text-sm font-medium">
                        ${trendIcon} ${index.change_percent >= 0 ? '+' : ''}${index.change_percent.toFixed(2)}%
                    </div>
                </div>
            `;
        }).join('');
    }

    async loadHistoricalChart(symbol, period) {
        try {
            const response = await fetch(`/indicators/api/historical/${symbol}?period=${period}`);
            const data = await response.json();

            if (data.success) {
                this.renderChart(data.data);

                const info = document.getElementById('sp500Info');
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
                    label: 'S&P 500',
                    data: values,
                    borderColor: '#8B5CF6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
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
                                return `S&P 500: ${context.parsed.y.toFixed(2)} points`;
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

        statusDiv.innerHTML = `
            <div class="relative">
                <div class="flex items-center justify-between flex-wrap gap-4">
                    <div class="flex items-center">
                        <i class="fas fa-check-circle text-purple-600 text-xl mr-3"></i>
                        <div>
                            <h4 class="font-semibold text-purple-800">
                                Système opérationnel
                            </h4>
                            <p class="text-sm text-purple-700">Indices boursiers actifs</p>
                        </div>
                    </div>
                    <div class="flex flex-wrap gap-2 items-center">
                        <button id="refreshDataBtn" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm transition whitespace-nowrap flex items-center shadow-md">
                            <i class="fas fa-sync-alt mr-2"></i>Actualiser
                        </button>
                        <a href="/indicators/france" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition whitespace-nowrap flex items-center shadow-md">
                            <i class="fas fa-flag-france mr-2"></i>Indicateurs Français
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    async forceRefresh() {
        try {
            this.showNotification('🔄 Rafraîchissement en cours...', 'info');

            const response = await fetch('/indicators/api/dashboard');
            const data = await response.json();

            if (data.success) {
                this.currentData = data;
                this.renderAllComponents();
                this.showNotification('✅ Données internationales rafraîchies', 'success');
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
            console.log('🔄 Auto-refresh données internationales...');
            this.loadAllData();
        }, 5 * 60 * 1000);
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
        // Pour l'instant, pas de loading spécifique
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
            'info': 'bg-purple-500'
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
    window.internationalDashboard = new InternationalIndicatorsDashboard();
    console.log('✅ Dashboard International chargé');
});
