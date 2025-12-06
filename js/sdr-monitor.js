// geo/static/js/sdr-monitor.js
class SDRMonitor {
    static servers = [];
    static selectedServer = null;
    static updateInterval = null;

    static async initialize() {
        console.log('📡 Initialisation SDR Monitor...');
        await this.loadDashboard();
        await this.loadServers();
        await this.checkDataStatus(); // Vérifier le statut des données
        this.setupEventListeners();
        this.setupAutoRefresh();
    }

    static async loadDashboard() {
        try {
            const response = await fetch('/api/weak-indicators/dashboard');
            const data = await response.json();

            if (data.success) {
                if (data.real_data) {
                    this.displayRealData(data);
                } else {
                    this.displaySimulatedData(data);
                    this.showNotification('Mode simulation - Activez le mode RÉEL', 'warning');
                }
                this.updateStats(data.stats || {});
            } else {
                this.displayFallbackData();
                console.error('Erreur dans les données:', data.error);
            }
        } catch (error) {
            console.error('Erreur chargement dashboard:', error);
            this.displayFallbackData();
        }
    }

    static async checkDataStatus() {
        try {
            const response = await fetch('/api/system/data-status');
            const data = await response.json();

            if (data.success) {
                const statusElement = document.getElementById('data-status');
                if (statusElement) {
                    // CORRECTION : Vérifier que data.sources existe et est un objet
                    let sourcesText = '';
                    if (data.sources && typeof data.sources === 'object') {
                        const sourcesArray = Object.entries(data.sources).map(([key, value]) => {
                            return `${key}: ${value}`;
                        });
                        sourcesText = sourcesArray.join(', ');
                    }

                    statusElement.innerHTML = `
                        <div class="px-4 py-2 rounded-lg ${data.real_mode ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                            <div class="flex items-center">
                                <i class="fas fa-${data.real_mode ? 'satellite' : 'vial'} mr-2"></i>
                                <span class="font-semibold">${data.real_mode ? 'MODE RÉEL' : 'MODE SIMULATION'}</span>
                            </div>
                            <div class="text-sm mt-1">
                                ${sourcesText}
                            </div>
                            ${!data.real_mode ? `
                            <div class="text-xs mt-2">
                                ${data.recommendation || 'Activez GEOPOL_REAL_MODE=true dans .env pour passer en mode réel'}
                            </div>
                            ` : ''}
                        </div>
                    `;
                }
            }
        } catch (error) {
            console.error('Erreur vérification statut données:', error);
        }
    }

    static generateDashboardHTML(data) {
        // Vérifier si data.data existe et a la bonne structure
        if (!data || !data.data) {
            return '<div class="text-red-500 p-4">Données indisponibles</div>';
        }

        let html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">';

        // Vérifier chaque section
        const sections = ['sdr', 'travel', 'financial'];

        sections.forEach(section => {
            const sectionData = data.data[section];
            if (sectionData) {
                html += `
                    <div class="bg-white rounded-lg shadow-lg p-6">
                        <h3 class="font-bold text-lg mb-4 text-gray-800 uppercase">${section}</h3>
                        <div class="space-y-4">
                `;

                // Afficher selon le type de données
                if (section === 'sdr') {
                    html += this.generateSDRSectionHTML(sectionData);
                } else if (section === 'travel') {
                    html += this.generateTravelSectionHTML(sectionData);
                } else if (section === 'financial') {
                    html += this.generateFinancialSectionHTML(sectionData);
                }

                html += `
                        </div>
                    </div>
                `;
            }
        });

        html += '</div>';
        return html;
    }

    static generateSDRSectionHTML(sdrData) {
        if (sdrData.error) {
            return `<div class="text-red-500">${sdrData.error}</div>`;
        }

        let html = '';
        // Vérifier si sdrData est un tableau ou un objet
        if (Array.isArray(sdrData)) {
            sdrData.forEach(item => {
                html += `
                    <div class="p-3 bg-gray-50 rounded-lg">
                        <div class="font-medium">${item.frequency || 'N/A'} MHz</div>
                        <div class="text-sm text-gray-600">
                            Émissions: ${item.emissions_count || 0}
                        </div>
                    </div>
                `;
            });
        } else if (typeof sdrData === 'object') {
            // Si c'est un objet, afficher ses propriétés
            Object.entries(sdrData).forEach(([key, value]) => {
                html += `
                    <div class="p-3 bg-gray-50 rounded-lg">
                        <div class="font-medium">${key}</div>
                        <div class="text-sm text-gray-600">
                            ${typeof value === 'object' ? JSON.stringify(value) : value}
                        </div>
                    </div>
                `;
            });
        }

        return html;
    }

    static generateTravelSectionHTML(travelData) {
        if (travelData.error) {
            return `<div class="text-red-500">${travelData.error}</div>`;
        }

        let html = '';
        if (travelData.countries && Array.isArray(travelData.countries)) {
            travelData.countries.slice(0, 5).forEach(country => {
                const riskLevel = country.risk_level || 1;
                const riskColor = riskLevel >= 4 ? 'bg-red-100 text-red-800' :
                    riskLevel >= 3 ? 'bg-orange-100 text-orange-800' :
                        riskLevel >= 2 ? 'bg-yellow-100 text-yellow-800' :
                            'bg-green-100 text-green-800';

                html += `
                    <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                        <div>
                            <div class="font-medium">${country.country_name || 'Unknown'}</div>
                            <div class="text-sm text-gray-600">${country.source || 'Unknown'}</div>
                        </div>
                        <span class="px-2 py-1 rounded-full text-xs ${riskColor}">
                            Niveau ${riskLevel}
                        </span>
                    </div>
                `;
            });
        }

        return html;
    }

    static generateFinancialSectionHTML(financialData) {
        if (financialData.error) {
            return `<div class="text-red-500">${financialData.error}</div>`;
        }

        let html = '';
        if (financialData.indices && typeof financialData.indices === 'object') {
            Object.entries(financialData.indices).forEach(([symbol, data]) => {
                if (data && typeof data === 'object') {
                    const change = data.change_percent || 0;
                    const changeColor = change >= 0 ? 'text-green-600' : 'text-red-600';
                    const changeIcon = change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';

                    html += `
                        <div class="p-3 bg-gray-50 rounded-lg">
                            <div class="flex justify-between items-center">
                                <div class="font-medium">${data.name || symbol}</div>
                                <div class="${changeColor}">
                                    <i class="fas ${changeIcon} mr-1"></i>
                                    ${Math.abs(change).toFixed(2)}%
                                </div>
                            </div>
                            <div class="text-sm text-gray-600">
                                ${data.current_price ? data.current_price.toFixed(2) : 'N/A'}
                            </div>
                        </div>
                    `;
                }
            });
        }

        return html;
    }

    static displayRealData(data) {
        const container = document.getElementById('sdr-dashboard');
        if (!container) return;

        container.innerHTML = `
            <div class="mb-4">
                <span class="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm">
                    <i class="fas fa-satellite mr-1"></i> DONNÉES RÉELLES
                </span>
            </div>
            ${this.generateDashboardHTML(data)}
        `;
    }

    static displaySimulatedData(data) {
        const container = document.getElementById('sdr-dashboard');
        if (!container) return;

        container.innerHTML = `
            <div class="mb-4">
                <span class="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm">
                    <i class="fas fa-vial mr-1"></i> MODE SIMULATION
                </span>
                <button onclick="SDRMonitor.enableRealMode()" class="ml-4 px-4 py-1 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 transition">
                    Activer le mode RÉEL
                </button>
            </div>
            ${this.generateDashboardHTML(data)}
        `;
    }

    static async loadServers() {
        try {
            const response = await fetch('/api/weak-indicators/sdr/servers');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.servers) {
                this.servers = data.servers;
                this.displayServers();
            } else {
                console.error('Erreur dans la réponse serveurs:', data.error);
                // Fallback : serveurs simulés
                this.servers = [
                    {
                        id: 1,
                        name: 'KiwiSDR Public (simulé)',
                        url: 'http://kiwisdr.com/',
                        type: 'kiwisdr',
                        active: true
                    }
                ];
                this.displayServers();
            }
        } catch (error) {
            console.error('Erreur chargement serveurs:', error);
            // Fallback minimal
            this.servers = [];
            this.displayServers();
        }
    }

    static updateStats(stats) {
        const updateElement = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        };

        updateElement('total-frequencies', stats.total_frequencies || 0);
        updateElement('anomalies-detected', stats.anomalies_count || 0);
        updateElement('active-servers', stats.active_servers || 0);
    }

    static displayServers() {
        const container = document.getElementById('sdr-servers-list');
        if (!container || !this.servers.length) return;

        container.innerHTML = this.servers.map(server => `
            <div class="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition">
                <div>
                    <div class="font-medium">${server.name || 'Serveur sans nom'}</div>
                    <div class="text-sm text-gray-600">${server.url || 'URL non disponible'}</div>
                    <div class="text-xs text-gray-500 capitalize">${server.type || 'unknown'}</div>
                </div>
                <div class="flex items-center space-x-2">
                    <span class="px-2 py-1 rounded-full text-xs ${server.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}">
                        ${server.active ? 'Actif' : 'Inactif'}
                    </span>
                    ${server.url ? `
                    <button onclick="SDRMonitor.testServer('${server.url.replace(/'/g, "\\'")}')" 
                            class="text-blue-600 hover:text-blue-800 p-1" title="Tester le serveur">
                        <i class="fas fa-vial"></i>
                    </button>
                    ` : ''}
                </div>
            </div>
        `).join('');
    }

    static async testServer(serverUrl) {
        try {
            this.showNotification('Test en cours...', 'info');

            const response = await fetch('/api/weak-indicators/sdr/test-server', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ server_url: serverUrl })
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification(`✅ Serveur accessible: ${data.message}`, 'success');
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }
        } catch (error) {
            this.showNotification(`❌ Erreur: ${error.message}`, 'error');
        }
    }

    static displayFallbackData() {
        const container = document.getElementById('sdr-dashboard');
        if (!container) return;

        container.innerHTML = `
            <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
                <i class="fas fa-exclamation-triangle text-yellow-600 text-3xl mb-3"></i>
                <h3 class="font-bold text-lg text-yellow-800 mb-2">Mode Simulation</h3>
                <p class="text-yellow-700">RTL-SDR/WebSDR non disponible - Données simulées</p>
                <button onclick="SDRMonitor.loadDashboard()" class="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition">
                    Réessayer
                </button>
            </div>
        `;
    }

    static enableRealMode() {
        this.showNotification('Redirection vers la configuration du mode réel...', 'info');
        // Rediriger vers la page de configuration ou ouvrir un modal
        setTimeout(() => {
            alert('Pour activer le mode RÉEL :\n1. Ouvrez le fichier .env\n2. Ajoutez : GEOPOL_REAL_MODE=true\n3. Redémarrez le serveur');
        }, 500);
    }

    static setupEventListeners() {
        // Bouton de rafraîchissement manuel
        const refreshBtn = document.getElementById('refresh-sdr');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadDashboard();
                this.showNotification('Actualisation lancée...', 'info');
            });
        }

        // Sélection de serveur
        const serverSelect = document.getElementById('server-select');
        if (serverSelect) {
            serverSelect.addEventListener('change', (e) => {
                this.selectedServer = e.target.value;
            });
        }

        // Bouton de test de tous les serveurs
        const testAllBtn = document.getElementById('test-all-servers');
        if (testAllBtn) {
            testAllBtn.addEventListener('click', async () => {
                this.showNotification('Test de tous les serveurs en cours...', 'info');
                for (const server of this.servers) {
                    if (server.url) {
                        await this.testServer(server.url);
                        await new Promise(resolve => setTimeout(resolve, 1000)); // Pause entre les tests
                    }
                }
            });
        }
    }

    static setupAutoRefresh() {
        // Rafraîchissement toutes les 5 minutes
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        this.updateInterval = setInterval(() => {
            this.loadDashboard();
            console.log('🔄 Rafraîchissement automatique SDR');
        }, 300000); // 5 minutes
    }

    static showNotification(message, type = 'info') {
        // Supprimer les notifications existantes
        const existingToasts = document.querySelectorAll('.sdr-notification-toast');
        existingToasts.forEach(toast => toast.remove());

        const toast = document.createElement('div');
        toast.className = `sdr-notification-toast fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-md ${type === 'error' ? 'bg-red-500' :
            type === 'success' ? 'bg-green-500' :
                type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
            } text-white animate-fade-in`;
        toast.style.maxWidth = '400px';

        const icons = {
            'error': 'exclamation-triangle',
            'success': 'check-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };

        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${icons[type] || 'info-circle'} mr-2"></i>
                <span class="flex-1">${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-2 text-white hover:text-gray-200">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.body.appendChild(toast);

        // Auto-suppression après 5 secondes
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.5s';
                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.remove();
                    }
                }, 500);
            }
        }, 5000);
    }

    static destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
}

// Initialisation sécurisée
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('sdr-dashboard') || document.getElementById('weak-indicators-dashboard')) {
        try {
            SDRMonitor.initialize();
            console.log('✅ SDR Monitor initialisé avec succès');
        } catch (error) {
            console.error('❌ Erreur initialisation SDR Monitor:', error);
        }
    }
});

// Nettoyage avant déchargement
window.addEventListener('beforeunload', () => {
    SDRMonitor.destroy();
});

// Exposer globalement
window.SDRMonitor = SDRMonitor;

// Fonction utilitaire pour vérifier la disponibilité des services
window.checkSDRService = async function () {
    try {
        const response = await fetch('/api/weak-indicators/status');
        const data = await response.json();
        return data.success && data.status;
    } catch (error) {
        console.error('Erreur vérification service SDR:', error);
        return null;
    }
};