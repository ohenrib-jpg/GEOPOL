// static/js/weak-indicators.js
/**
 * Gestionnaire des Indicateurs Faibles
 */

class WeakIndicatorsManager {
    constructor() {
        this.data = {};
        this.charts = {};
        console.log('📡 Initialisation Weak Indicators Manager');
    }

    async init() {
        console.log('📊 Initialisation des indicateurs faibles...');
        await this.loadDashboardData();
    }

    async loadDashboardData() {
        try {
            // Charger les données du dashboard
            const response = await fetch('/weak-indicators/api/dashboard');
            const result = await response.json();

            if (result.success) {
                this.data = result.data;
                this.renderFinancialIndicators();
                this.renderTravelIndicators();
                this.renderSDRIndicators();
            }
        } catch (error) {
            console.error('❌ Erreur chargement données faibles:', error);
        }
    }

    renderFinancialIndicators() {
        const container = document.getElementById('financial-indicators');
        if (!container || !this.data.financial) return;

        container.innerHTML = '<h3 class="text-lg font-bold mb-3">📈 Indicateurs Financiers</h3>';

        Object.entries(this.data.financial).forEach(([symbol, data]) => {
            if (data.error) return;

            const change = data.change_percent || 0;
            const isPositive = change >= 0;

            const div = document.createElement('div');
            div.className = 'indicator-item p-3 bg-white rounded-lg shadow mb-2';
            div.innerHTML = `
                <div class="flex justify-between items-center">
                    <span class="font-semibold">${data.name || symbol}</span>
                    <span class="text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}">
                        ${isPositive ? '▲' : '▼'} ${Math.abs(change).toFixed(2)}%
                    </span>
                </div>
                <div class="text-xl font-bold mt-1">
                    ${this.formatNumber(data.current_price)} ${data.currency || ''}
                </div>
            `;
            container.appendChild(div);
        });
    }

    renderTravelIndicators() {
        const container = document.getElementById('travel-indicators');
        if (!container || !this.data.travel) return;

        container.innerHTML = '<h3 class="text-lg font-bold mb-3">✈️ Indicateurs Voyage</h3>';

        // Données de démonstration si nécessaire
        const demoData = [
            { name: 'Réservations', value: '1,245', trend: 'up', change: '+12%' },
            { name: 'Annulations', value: '89', trend: 'down', change: '-5%' },
            { name: 'Disponibilité', value: '67%', trend: 'up', change: '+3%' }
        ];

        demoData.forEach(item => {
            const div = document.createElement('div');
            div.className = 'indicator-item p-3 bg-white rounded-lg shadow mb-2';
            div.innerHTML = `
                <div class="flex justify-between items-center">
                    <span class="font-semibold">${item.name}</span>
                    <span class="text-sm ${item.trend === 'up' ? 'text-green-600' : 'text-red-600'}">
                        ${item.change}
                    </span>
                </div>
                <div class="text-xl font-bold mt-1">${item.value}</div>
            `;
            container.appendChild(div);
        });
    }

    renderSDRIndicators() {
        const container = document.getElementById('sdr-indicators');
        if (!container) return;

        container.innerHTML = '<h3 class="text-lg font-bold mb-3">📻 Indicateurs SDR</h3>';

        // Données de démonstration
        const demoData = [
            { freq: '14.2 MHz', power: '-75 dBm', status: 'Actif' },
            { freq: '7.1 MHz', power: '-82 dBm', status: 'Faible' },
            { freq: '21.3 MHz', power: '-68 dBm', status: 'Fort' }
        ];

        demoData.forEach(item => {
            const div = document.createElement('div');
            div.className = 'indicator-item p-3 bg-white rounded-lg shadow mb-2';
            div.innerHTML = `
                <div class="flex justify-between items-center">
                    <span class="font-semibold">${item.freq}</span>
                    <span class="px-2 py-1 text-xs rounded ${item.status === 'Actif' ? 'bg-green-100 text-green-800' : item.status === 'Fort' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}">
                        ${item.status}
                    </span>
                </div>
                <div class="text-sm text-gray-600 mt-1">Puissance: ${item.power}</div>
            `;
            container.appendChild(div);
        });
    }

    formatNumber(num) {
        if (!num) return '0';
        return parseFloat(num).toLocaleString('fr-FR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    async refreshAll() {
        await this.loadDashboardData();
        console.log('✅ Données indicateurs faibles actualisées');
    }
}

// Initialisation globale
const WeakIndicators = new WeakIndicatorsManager();

document.addEventListener('DOMContentLoaded', function () {
    if (window.location.pathname.includes('/weak-indicators')) {
        WeakIndicators.init();
    }
});

console.log('✅ WeakIndicatorsManager chargé');
