// static/js/settings.js - VERSION CORRIGÉE AVEC APPRENTISSAGE ACTIF

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
                    
                    <!-- Apprentissage Continu - VERSION AMÉLIORÉE -->
                    <div class="bg-gradient-to-r from-purple-50 to-blue-50 border-l-4 border-purple-500 p-4 rounded-lg">
                        <div class="flex items-start justify-between">
                            <div>
                                <h4 class="font-semibold text-gray-800 mb-2">
                                    🧠 Apprentissage Continu
                                </h4>
                                <p class="text-sm text-gray-600 mb-3">
                                    Le système s'améliore automatiquement grâce aux corrections et feedbacks.
                                </p>
                            </div>
                            <div id="learning-status-badge" class="learning-status-indicator">
                                <i class="fas fa-spinner fa-spin text-gray-400"></i>
                            </div>
                        </div>
                        
                        <!-- Statistiques rapides -->
                        <div id="learning-quick-stats" class="grid grid-cols-3 gap-2 mb-3 text-xs">
                            <div class="bg-white p-2 rounded text-center">
                                <div class="text-gray-500">Total</div>
                                <div class="font-bold text-blue-600" id="quick-total">-</div>
                            </div>
                            <div class="bg-white p-2 rounded text-center">
                                <div class="text-gray-500">Traité</div>
                                <div class="font-bold text-green-600" id="quick-processed">-</div>
                            </div>
                            <div class="bg-white p-2 rounded text-center">
                                <div class="text-gray-500">En attente</div>
                                <div class="font-bold text-yellow-600" id="quick-pending">-</div>
                            </div>
                        </div>
                        
                        <!-- Boutons d'action -->
                        <div class="space-y-2">
                            <button onclick="SettingsManager.showContinuousLearningPanel()" 
                                    class="w-full bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 text-sm transition duration-200">
                                <i class="fas fa-chart-line mr-2"></i>Tableau de bord d'apprentissage
                            </button>
                            
                            <button onclick="SettingsManager.triggerLearningSession()" 
                                    id="triggerLearningBtn"
                                    class="w-full bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 text-sm transition duration-200">
                                <i class="fas fa-play mr-2"></i>Forcer une session d'apprentissage
                            </button>
                            
                            <button onclick="SettingsManager.refreshLearningStatus()" 
                                    class="w-full bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 text-sm transition duration-200">
                                <i class="fas fa-sync mr-2"></i>Rafraîchir le statut
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.setupSettingsEventListeners();
        this.loadSettings();
        
        // Charger le statut de l'apprentissage
        this.refreshLearningStatus();
        
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

    // ============================================================
    // MÉTHODES D'APPRENTISSAGE CONTINU - NOUVELLES
    // ============================================================

    static async refreshLearningStatus() {
        console.log('🔄 Rafraîchissement statut apprentissage...');
        
        try {
            // Vérifier si l'intégration est disponible
            if (typeof window.LearningIntegration === 'undefined') {
                console.warn('⚠️ LearningIntegration non chargé');
                this.updateLearningStatusUI(false, 'Module non chargé');
                return;
            }

            // Vérifier le statut système
            const status = await window.LearningIntegration.checkSystemStatus();
            
            if (status.success) {
                // Récupérer les statistiques
                const stats = await window.LearningIntegration.displayStatistics();
                
                if (stats) {
                    this.updateLearningStatusUI(true, 'Actif', stats);
                } else {
                    this.updateLearningStatusUI(true, 'Actif (stats indisponibles)');
                }
            } else {
                this.updateLearningStatusUI(false, status.message);
            }
        } catch (error) {
            console.error('❌ Erreur refresh statut:', error);
            this.updateLearningStatusUI(false, 'Erreur: ' + error.message);
        }
    }

    static updateLearningStatusUI(active, message, stats = null) {
        // Mettre à jour le badge de statut
        const badge = document.getElementById('learning-status-badge');
        if (badge) {
            if (active) {
                badge.innerHTML = '<span class="text-green-600"><i class="fas fa-check-circle"></i> Actif</span>';
                badge.className = 'learning-status-indicator active';
            } else {
                badge.innerHTML = `<span class="text-yellow-600"><i class="fas fa-exclamation-circle"></i> ${message}</span>`;
                badge.className = 'learning-status-indicator inactive';
            }
        }

        // Mettre à jour les statistiques rapides
        if (stats) {
            const totalEl = document.getElementById('quick-total');
            const processedEl = document.getElementById('quick-processed');
            const pendingEl = document.getElementById('quick-pending');

            if (totalEl) totalEl.textContent = stats.total_feedbacks || 0;
            if (processedEl) processedEl.textContent = stats.processed_feedbacks || 0;
            if (pendingEl) pendingEl.textContent = stats.pending_feedbacks || 0;
        }
    }

    static async showContinuousLearningPanel() {
        console.log('📊 Ouverture tableau de bord apprentissage...');
        
        // Vérifier si ContinuousLearningManager est disponible
        if (typeof ContinuousLearningManager !== 'undefined') {
            try {
                await ContinuousLearningManager.showLearningPanel();
            } catch (error) {
                console.error('❌ Erreur ouverture panel:', error);
                this.showMessage('Erreur lors de l\'ouverture du tableau de bord: ' + error.message, 'error');
            }
        } else {
            console.error('❌ ContinuousLearningManager non disponible');
            this.showMessage('Le module d\'apprentissage n\'est pas chargé. Veuillez recharger la page.', 'error');
        }
    }

    static async triggerLearningSession() {
        console.log('🎯 Déclenchement session d\'apprentissage...');
        
        const btn = document.getElementById('triggerLearningBtn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Déclenchement en cours...';
        }

        try {
            if (typeof window.LearningIntegration === 'undefined') {
                throw new Error('Module d\'intégration non chargé');
            }

            const result = await window.LearningIntegration.triggerLearningSession();

            if (result.success) {
                this.showMessage('Session d\'apprentissage déclenchée avec succès !', 'success');
            } else {
                this.showMessage(`Session non déclenchée: ${result.message}. ${result.pending || 0}/20 feedbacks en attente.`, 'info');
            }

            // Rafraîchir le statut
            await this.refreshLearningStatus();

        } catch (error) {
            console.error('❌ Erreur déclenchement:', error);
            this.showMessage('Erreur: ' + error.message, 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-play mr-2"></i>Forcer une session d\'apprentissage';
            }
        }
    }
}

// Initialisation des paramètres
document.addEventListener('DOMContentLoaded', function () {
    window.SettingsManager = SettingsManager;
    console.log('✅ SettingsManager initialisé avec support apprentissage continu');
});
