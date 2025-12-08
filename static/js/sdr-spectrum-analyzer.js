// static/js/sdr-spectrum-analyzer.js
class SDRSpectrumAnalyzer {
    constructor() {
        this.currentPlot = null;
        this.waterfallActive = false;
        this.updateInterval = null;
        this.init();
    }

    async init() {
        console.log('📡 Initialisation SDR Spectrum Analyzer...');
        
        this.setupEventListeners();
        await this.loadDashboard();
        this.startAutoRefresh();
        
        console.log('✅ Spectrum Analyzer initialisé');
    }

    setupEventListeners() {
        // Scan toutes les bandes
        document.getElementById('scan-all')?.addEventListener('click', () => {
            this.scanAllBands();
        });

        // Scan fréquence spécifique
        document.getElementById('scan-frequency')?.addEventListener('click', () => {
            this.scanSpecificFrequency();
        });

        // Boutons de bandes
        document.querySelectorAll('.band-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const band = e.target.dataset.band;
                this.scanBand(band);
            });
        });

        // Waterfall controls
        document.getElementById('start-waterfall')?.addEventListener('click', () => {
            this.startWaterfall();
        });

        document.getElementById('stop-waterfall')?.addEventListener('click', () => {
            this.stopWaterfall();
        });
    }

    async loadDashboard() {
        try {
            const response = await fetch('/api/sdr/dashboard');
            const data = await response.json();

            if (data.success) {
                this.updateStats(data.stats);
                this.renderFrequencies(data.frequencies);
                this.renderAnomalies(data.anomalies);
                this.displayStatus(data.real_data);
            } else {
                throw new Error(data.error);
            }

        } catch (error) {
            console.error('❌ Erreur chargement dashboard:', error);
            this.showError('Erreur de chargement des données SDR');
        }
    }

    updateStats(stats) {
        const updateElement = (id, value) => {
            const element = document.getElementById(id);
            if (element) element.textContent = value;
        };

        updateElement('total-frequencies', stats.total_frequencies || 0);
        updateElement('anomalies-detected', stats.anomalies_count || 0);
        updateElement('active-servers', stats.active_servers || 0);
    }

    renderFrequencies(frequencies) {
        const container = document.getElementById('bands-results');
        if (!container) return;

        container.innerHTML = frequencies.map(freq => {
            const categoryColors = {
                'emergency': 'bg-red-600',
                'military': 'bg-orange-600', 
                'diplomatic': 'bg-blue-600',
                'broadcast': 'bg-green-600'
            };

            const colorClass = categoryColors[freq.category] || 'bg-gray-600';

            return `
                <div class="p-4 bg-gray-700 rounded-lg border border-gray-600">
                    <div class="flex justify-between items-start mb-2">
                        <div>
                            <h4 class="font-semibold text-white">${freq.name}</h4>
                            <p class="text-sm text-gray-400">${freq.freq} kHz</p>
                        </div>
                        <span class="px-2 py-1 rounded text-xs ${colorClass} text-white">
                            ${freq.category}
                        </span>
                    </div>
                    <div class="grid grid-cols-3 gap-4 text-sm">
                        <div>
                            <span class="text-gray-400">Puissance:</span>
                            <div class="text-white font-medium">${freq.power_db} dB</div>
                        </div>
                        <div>
                            <span class="text-gray-400">Pics:</span>
                            <div class="text-white font-medium">${freq.peaks_count}</div>
                        </div>
                        <div>
                            <span class="text-gray-400">Statut:</span>
                            <div class="font-medium ${freq.status === 'active' ? 'text-green-400' : 'text-red-400'}">
                                ${freq.status === 'active' ? '🟢 Actif' : '🔴 Inactif'}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderAnomalies(anomalies) {
        const container = document.getElementById('anomalies-list');
        if (!container) return;

        if (anomalies.length === 0) {
            container.innerHTML = '<div class="text-gray-500 text-center py-4">Aucune anomalie détectée</div>';
            return;
        }

        container.innerHTML = anomalies.map(anomaly => {
            const severityColors = {
                'low': 'bg-yellow-600',
                'medium': 'bg-orange-600', 
                'high': 'bg-red-600'
            };

            const colorClass = severityColors[anomaly.severity] || 'bg-gray-600';

            return `
                <div class="p-3 bg-gray-700 rounded-lg border-l-4 border-red-500">
                    <div class="flex justify-between items-start mb-2">
                        <h4 class="font-semibold text-white">${anomaly.type}</h4>
                        <span class="px-2 py-1 rounded text-xs ${colorClass} text-white">
                            ${anomaly.severity}
                        </span>
                    </div>
                    <p class="text-sm text-gray-300 mb-1">${anomaly.description}</p>
                    <p class="text-xs text-gray-400">${anomaly.frequency} kHz • ${anomaly.timestamp}</p>
                </div>
            `;
        }).join('');
    }

    displayStatus(realData) {
        const statusElement = document.getElementById('data-status');
        if (!statusElement) return;

        if (realData) {
            statusElement.innerHTML = `
                <div class="px-4 py-2 rounded-lg bg-green-100 text-green-800">
                    <i class="fas fa-satellite mr-2"></i>
                    <span class="font-semibold">MODE RÉEL</span>
                    <div class="text-sm mt-1">Données SDR réelles en cours</div>
                </div>
            `;
        } else {
            statusElement.innerHTML = `
                <div class="px-4 py-2 rounded-lg bg-yellow-100 text-yellow-800">
                    <i class="fas fa-vial mr-2"></i>
                    <span class="font-semibold">MODE SIMULATION</span>
                    <div class="text-sm mt-1">Données simulées - Activez GEOPOL_REAL_MODE=true</div>
                </div>
            `;
        }
    }

    async scanAllBands() {
        this.logToConsole('🔍 Lancement du scan complet des bandes...');
        
        // Simulation d'un scan de toutes les bandes
        const bands = ['emergency', 'military', 'diplomatic', 'broadcast'];
        
        for (const band of bands) {
            this.logToConsole(`📡 Scan de la bande ${band}...`);
            await this.sleep(1000);
        }
        
        this.logToConsole('✅ Scan complet terminé');
        await this.loadDashboard(); // Recharger les données
    }

    async scanSpecificFrequency() {
        const frequency = document.getElementById('frequency-input')?.value;
        const bandwidth = document.getElementById('bandwidth-input')?.value;

        if (!frequency) {
            this.showError('Veuillez spécifier une fréquence');
            return;
        }

        this.logToConsole(`🎯 Scan spécifique: ${frequency} kHz (bande passante: ${bandwidth} kHz)`);

        try {
            const response = await fetch('/api/sdr/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    frequency: parseInt(frequency),
                    bandwidth: parseInt(bandwidth)
                })
            });

            const data = await response.json();

            if (data.success) {
                const result = data.results;
                this.logToConsole(`✅ Scan terminé - Puissance: ${result.power_db} dB, Pics: ${result.peaks_count}`);
                
                // Afficher le résultat
                this.displayScanResult(result);
                
                // Mettre à jour le graphique
                this.updateSpectrumPlot(frequency, result);
            } else {
                throw new Error(data.error);
            }

        } catch (error) {
            this.logToConsole(`❌ Erreur scan: ${error.message}`);
            this.showError(`Erreur lors du scan: ${error.message}`);
        }
    }

    async scanBand(band) {
        this.logToConsole(`📡 Scan de la bande ${band}...`);
        
        // Simuler un scan de bande
        await this.sleep(2000);
        
        this.logToConsole(`✅ Bande ${band} scannée`);
        await this.loadDashboard();
    }

    displayScanResult(result) {
        this.logToConsole(`
            📊 Résultats du scan:
            - Puissance: ${result.power_db} dB
            - Pics détectés: ${result.peaks_count}
            - Type de signal: ${result.signal_type}
            - Signal présent: ${result.signal_present ? 'Oui' : 'Non'}
        `);
    }

    async updateSpectrumPlot(frequency, scanResult) {
        try {
            // Générer des données de spectre autour de la fréquence scannée
            const response = await fetch('/api/sdr/test-spectrum');
            const data = await response.json();

            if (data.success) {
                this.renderSpectrumPlot(data);
            }

        } catch (error) {
            console.error('Erreur mise à jour graphique:', error);
        }
    }

    renderSpectrumPlot(data) {
        const plotElement = document.getElementById('spectrum-plot');
        if (!plotElement) return;

        const trace = {
            x: data.frequencies_mhz,
            y: data.powers,
            type: 'scatter',
            mode: 'lines',
            name: 'Spectre',
            line: {
                color: '#3B82F6',
                width: 2
            }
        };

        const layout = {
            title: 'Spectre Radio',
            xaxis: {
                title: 'Fréquence (MHz)',
                gridcolor: '#374151'
            },
            yaxis: {
                title: 'Puissance (dB)',
                gridcolor: '#374151'
            },
            plot_bgcolor: '#1F2937',
            paper_bgcolor: '#1F2937',
            font: {
                color: '#D1D5DB'
            }
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        if (this.currentPlot) {
            this.currentPlot.destroy();
        }

        this.currentPlot = Plotly.newPlot(plotElement, [trace], layout, config);
    }

    startWaterfall() {
        this.waterfallActive = true;
        this.logToConsole('🌊 Démarrage du waterfall...');
        
        // Simuler le waterfall
        this.updateInterval = setInterval(async () => {
            if (this.waterfallActive) {
                await this.updateSpectrumPlot();
            }
        }, 2000);
    }

    stopWaterfall() {
        this.waterfallActive = false;
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        this.logToConsole('⏹️ Waterfall arrêté');
    }

    startAutoRefresh() {
        // Auto-refresh toutes les 30 secondes
        setInterval(() => {
            this.loadDashboard();
        }, 30000);
    }

    logToConsole(message) {
        const consoleElement = document.getElementById('sdr-console');
        if (!consoleElement) return;

        const timestamp = new Date().toLocaleTimeString('fr-FR');
        const logEntry = document.createElement('div');
        logEntry.className = 'text-green-400 mb-1';
        logEntry.textContent = `[${timestamp}] ${message}`;

        consoleElement.appendChild(logEntry);
        consoleElement.scrollTop = consoleElement.scrollHeight;

        // Limiter à 100 lignes
        while (consoleElement.children.length > 100) {
            consoleElement.removeChild(consoleElement.firstChild);
        }
    }

    showError(message) {
        this.logToConsole(`❌ ERREUR: ${message}`);
        
        // Afficher une notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-red-500 text-white p-4 rounded-lg shadow-lg z-50';
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    destroy() {
        this.stopWaterfall();
        
        if (this.currentPlot) {
            this.currentPlot.destroy();
        }
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    window.sdrAnalyzer = new SDRSpectrumAnalyzer();
});

// Nettoyage
window.addEventListener('beforeunload', () => {
    if (window.sdrAnalyzer) {
        window.sdrAnalyzer.destroy();
    }
});

console.log('✅ SDR Spectrum Analyzer chargé');
