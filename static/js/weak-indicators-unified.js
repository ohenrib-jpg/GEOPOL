// static/js/weak-indicators-unified.js
/**
 * Gestionnaire unifié des indicateurs faibles
 */

class WeakIndicatorsManager {
    constructor() {
        this.baseUrl = '/weak-indicators/api';
        this.currentData = null;
    }
    
    async init() {
        console.log('🚀 Initialisation Weak Indicators Manager');
        await this.loadDashboardData();
        this.setupEventListeners();
    }
    
    async loadDashboardData() {
        try {
            const response = await fetch(`${this.baseUrl}/dashboard`);
            const data = await response.json();
            
            if (data.success) {
                this.currentData = data;
                this.renderDashboard();
            } else {
                this.showError('Erreur chargement données');
            }
        } catch (error) {
            console.error('❌ Erreur chargement dashboard:', error);
            this.showError('Erreur de connexion');
        }
    }
    
    renderDashboard() {
        this.renderSDRSection();
        this.renderTravelSection();
        this.renderFinancialSection();
        this.updateTimestamp();
    }
    
    renderSDRSection() {
        const container = document.getElementById('sdr-monitoring');
        if (!container || !this.currentData?.data?.sdr) return;
        
        const sdrData = this.currentData.data.sdr;
        
        container.innerHTML = `
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h3 class="text-lg font-bold mb-4 flex items-center">
                    <i class="fas fa-broadcast-tower text-blue-500 mr-2"></i>
                    Surveillance SDR
                    <span class="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        ${sdrData.active_monitors?.length || 0} fréquences
                    </span>
                </h3>
                
                <div class="space-y-3">
                    ${(sdrData.active_monitors || []).map(monitor => `
                        <div class="flex justify-between items-center p-3 border rounded-lg">
                            <div>
                                <div class="font-mono font-bold">${monitor.frequency}</div>
                                <div class="text-sm text-gray-600">${monitor.description}</div>
                            </div>
                            <div class="text-right">
                                <span class="inline-block w-3 h-3 rounded-full ${monitor.status === 'active' ? 'bg-green-500' : 'bg-yellow-500'}"></span>
                                <div class="text-xs text-gray-500">${monitor.signal_strength} dB</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="mt-4 text-xs text-gray-500">
                    Source: ${sdrData.source} • Dernier scan: ${new Date(sdrData.last_scan).toLocaleString()}
                </div>
            </div>
        `;
    }
    
    renderTravelSection() {
        const container = document.getElementById('travel-advisories');
        if (!container || !this.currentData?.data?.travel) return;
        
        const travelData = this.currentData.data.travel;
        
        container.innerHTML = `
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h3 class="text-lg font-bold mb-4 flex items-center">
                    <i class="fas fa-globe-americas text-green-500 mr-2"></i>
                    Avis aux Voyageurs
                </h3>
                
                <div class="space-y-2">
                    ${(travelData.countries || []).map(country => `
                        <div class="flex justify-between items-center p-2 border-b">
                            <div>
                                <span class="font-medium">${country.name}</span>
                                <span class="text-xs text-gray-500 ml-2">${country.code}</span>
                            </div>
                            <span class="px-2 py-1 text-xs rounded ${
                                country.risk_level === 1 ? 'bg-green-100 text-green-800' :
                                country.risk_level === 2 ? 'bg-yellow-100 text-yellow-800' :
                                country.risk_level === 3 ? 'bg-orange-100 text-orange-800' :
                                'bg-red-100 text-red-800'
                            }">
                                Niveau ${country.risk_level}
                            </span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    renderFinancialSection() {
        const container = document.getElementById('financial-markets');
        if (!container || !this.currentData?.data?.financial) return;
        
        const financialData = this.currentData.data.financial;
        
        container.innerHTML = `
            <div class="bg-white rounded-lg shadow-lg p-6">
                <h3 class="text-lg font-bold mb-4 flex items-center">
                    <i class="fas fa-chart-line text-purple-500 mr-2"></i>
                    Marchés Financiers
                </h3>
                
                <div class="space-y-3">
                    ${Object.entries(financialData.indices || {}).map(([name, data]) => `
                        <div class="flex justify-between items-center p-3 bg-gray-50 rounded">
                            <span class="font-medium">${name}</span>
                            <div class="text-right">
                                <div class="font-bold">${data.value}</div>
                                <div class="text-sm ${data.change >= 0 ? 'text-green-600' : 'text-red-600'}">
                                    ${data.change >= 0 ? '+' : ''}${data.change}%
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    updateTimestamp() {
        const element = document.getElementById('last-update');
        if (element && this.currentData?.metadata?.timestamp) {
            element.textContent = new Date(this.currentData.metadata.timestamp).toLocaleString();
        }
    }
    
    setupEventListeners() {
        // Bouton rafraîchissement
        const refreshBtn = document.getElementById('refresh-data');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadDashboardData());
        }
    }
    
    showError(message) {
        const container = document.getElementById('weak-indicators-container');
        if (container) {
            container.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                    <i class="fas fa-exclamation-triangle text-red-500 text-2xl mb-2"></i>
                    <p class="text-red-800 font-medium">${message}</p>
                    <button onclick="weakIndicators.loadDashboardData()" 
                            class="mt-2 bg-red-100 text-red-800 px-4 py-2 rounded hover:bg-red-200">
                        Réessayer
                    </button>
                </div>
            `;
        }
    }
}

// Initialisation globale
const weakIndicators = new WeakIndicatorsManager();

document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('/weak-indicators')) {
        weakIndicators.init();
    }
});
