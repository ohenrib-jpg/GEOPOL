// static/js/settings.js - Gestion des paramètres

class SettingsManager {
    static showSettings() {
        const modal = document.getElementById('themeManagerModal');
        const content = document.getElementById('themeManagerContent');
        const title = document.getElementById('modalTitle');

        if (!modal || !content || !title) return;

        title.textContent = 'Paramètres';

        content.innerHTML = `
            <div class="max-w-2xl mx-auto">
                <div class="space-y-6">
                    <!-- Configuration des flux par défaut -->
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-gray-800 mb-3">Flux RSS par défaut</h4>
                        <textarea id="defaultFeeds" class="w-full h-32 p-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500" 
                                  placeholder="Entrez les URLs des flux RSS par défaut (un par ligne)"></textarea>
                        <button id="saveDefaultFeedsBtn" class="mt-2 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm transition duration-200">
                            Sauvegarder les flux par défaut
                        </button>
                    </div>
                    
                    <!-- Actions système -->
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-gray-800 mb-3">Actions système</h4>
                        <div class="space-y-2">
                            <button id="clearDatabaseBtn" class="w-full bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 text-sm transition duration-200">
                                <i class="fas fa-trash mr-2"></i>Vider la base de données
                            </button>
                            <button id="exportDataBtn" class="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm transition duration-200">
                                <i class="fas fa-download mr-2"></i>Exporter les données
                            </button>
                        </div>
                    </div>
                    
                    <!-- Apprentissage Continu -->
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-gray-800 mb-3">🧠 Apprentissage Continu</h4>
                        <div class="space-y-3">
                            <p class="text-sm text-gray-600">
                                Le système s'améliore automatiquement grâce aux corrections et feedbacks.
                            </p>
                            <button onclick="SettingsManager.showContinuousLearningPanel()" 
                                    class="w-full bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 text-sm transition duration-200">
                                <i class="fas fa-chart-line mr-2"></i>Surveiller l'apprentissage
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.setupSettingsEventListeners();
        this.loadSettings();
        ModalManager.showModal('themeManagerModal');
    }

    static setupSettingsEventListeners() {
        // Sauvegarde des flux par défaut
        const saveFeedsBtn = document.getElementById('saveDefaultFeedsBtn');
        if (saveFeedsBtn) {
            saveFeedsBtn.addEventListener('click', this.saveDefaultFeeds.bind(this));
        }

        // Actions système
        const clearDbBtn = document.getElementById('clearDatabaseBtn');
        if (clearDbBtn) {
            clearDbBtn.addEventListener('click', this.clearDatabase.bind(this));
        }

        const exportBtn = document.getElementById('exportDataBtn');
        if (exportBtn) {
            exportBtn.addEventListener('click', this.exportData.bind(this));
        }
    }

    static loadSettings() {
        // Charger les flux par défaut depuis le localStorage
        const defaultFeeds = localStorage.getItem('defaultFeeds');
        if (defaultFeeds) {
            const feedsTextarea = document.getElementById('defaultFeeds');
            if (feedsTextarea) {
                feedsTextarea.value = defaultFeeds;
            }
        }
    }

    static saveDefaultFeeds() {
        const feedsTextarea = document.getElementById('defaultFeeds');
        if (feedsTextarea) {
            localStorage.setItem('defaultFeeds', feedsTextarea.value);
            this.showMessage('Flux par défaut sauvegardés avec succès!', 'success');
        }
    }

    static clearDatabase() {
        if (confirm('Êtes-vous sûr de vouloir vider toute la base de données ? Cette action est irréversible.')) {
            this.showMessage('Fonctionnalité à implémenter', 'info');
        }
    }

    static exportData() {
        this.showMessage('Fonctionnalité à implémenter', 'info');
    }

    static showMessage(message, type = 'info') {
        alert(message);
    }

    static showContinuousLearningPanel() {
        // Vérifier si ContinuousLearningManager est disponible
        if (typeof ContinuousLearningManager !== 'undefined') {
            ContinuousLearningManager.showLearningPanel();
        } else {
            console.error('ContinuousLearningManager non disponible');
            alert('Module d\'apprentissage non chargé');
        }
    }
}

// Initialisation des paramètres
document.addEventListener('DOMContentLoaded', function () {
    window.SettingsManager = SettingsManager;
    console.log('✅ SettingsManager initialisé');
});
