// static/js/instance-manager.js - Version corrigée

// Vérifier si ModalManager existe déjà, sinon le créer
if (typeof ModalManager === 'undefined') {
    class ModalManager {
        static showModal(modalId) {
            console.log('🔄 ModalManager.showModal appelé pour:', modalId);
            const modal = document.getElementById(modalId);
            const overlay = document.getElementById('overlay');

            if (modal) {
                modal.classList.remove('hidden');
                modal.style.display = 'block';
            }
            if (overlay) {
                overlay.classList.remove('hidden');
                overlay.style.display = 'block';
            }
        }

        static hideModal(modalId) {
            console.log('🔄 ModalManager.hideModal appelé pour:', modalId);
            const modal = document.getElementById(modalId);
            const overlay = document.getElementById('overlay');

            if (modal) {
                modal.classList.add('hidden');
                modal.style.display = 'none';
            }
            if (overlay) {
                overlay.classList.add('hidden');
                overlay.style.display = 'none';
            }
        }
    }

    window.ModalManager = ModalManager;
}

// InstanceManager
class InstanceManager {
    static showInstancePanel() {
        console.log('🔄 InstanceManager.showInstancePanel appelé');

        const content = document.getElementById('themeManagerContent');
        const title = document.getElementById('modalTitle');

        if (!content || !title) {
            console.error('❌ Éléments modal non trouvés');
            return;
        }

        title.textContent = '🛠️ Gestion des Instances Nitter';

        content.innerHTML = `
            <div class="max-w-4xl mx-auto space-y-6">
                <!-- Statut des instances -->
                <div class="bg-white rounded-lg border p-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-4">
                        <i class="fas fa-server mr-2"></i>Statut des Instances
                    </h3>
                    <div id="instancesStatus" class="space-y-3">
                        <div class="text-center py-4">
                            <i class="fas fa-spinner fa-spin text-blue-600"></i>
                            <p class="text-gray-600">Chargement du statut...</p>
                        </div>
                    </div>
                    <button onclick="InstanceManager.loadInstancesStatus()" 
                            class="mt-4 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                        <i class="fas fa-sync-alt mr-2"></i>Actualiser
                    </button>
                </div>

                <!-- Ajout d'instance -->
                <div class="bg-white rounded-lg border p-6">
                    <h3 class="text-lg font-semibold text-gray-800 mb-4">
                        <i class="fas fa-plus-circle mr-2"></i>Ajouter une Instance
                    </h3>
                    <div class="flex space-x-2">
                        <input type="text" id="newInstanceUrl" 
                               placeholder="https://nitter.example.com" 
                               class="flex-1 p-2 border border-gray-300 rounded">
                        <button onclick="InstanceManager.addCustomInstance()" 
                                class="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
                            Ajouter
                        </button>
                    </div>
                </div>

                <!-- Actions -->
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h4 class="font-semibold text-yellow-800 mb-2">
                        <i class="fas fa-tools mr-2"></i>Maintenance
                    </h4>
                    <div class="flex space-x-2">
                        <button onclick="InstanceManager.resetBlacklist()" 
                                class="bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-700 text-sm">
                            Réinitialiser blacklist
                        </button>
                        <button onclick="ModalManager.hideModal('themeManagerModal')" 
                                class="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 text-sm">
                            Fermer
                        </button>
                    </div>
                </div>
            </div>
        `;

        ModalManager.showModal('themeManagerModal');
        this.loadInstancesStatus();
    }

    static async loadInstancesStatus() {
        const statusDiv = document.getElementById('instancesStatus');
        if (!statusDiv) return;

        try {
            const response = await fetch('/api/social/instances-status');
            const data = await response.json();

            if (data.success) {
                this.displayInstancesStatus(data.instances, statusDiv);
            } else {
                this.showError(statusDiv, data.error || 'Erreur de chargement');
            }
        } catch (error) {
            this.showError(statusDiv, 'Erreur réseau: ' + error.message);
        }
    }

    static displayInstancesStatus(instances, container) {
        let html = '';

        if (instances && Object.keys(instances).length > 0) {
            Object.entries(instances).forEach(([url, status]) => {
                const healthIcon = status.health ? 'fa-check-circle text-green-500' : 'fa-times-circle text-red-500';
                const blacklistClass = status.blacklisted ? 'bg-red-50 border-red-200' : 'bg-gray-50';

                html += `
                    <div class="border rounded-lg p-3 ${blacklistClass}">
                        <div class="flex justify-between items-center">
                            <div class="flex items-center space-x-3">
                                <i class="fas ${healthIcon}"></i>
                                <div>
                                    <p class="font-medium">${url}</p>
                                    <p class="text-sm text-gray-600">
                                        Succès: ${status.success || 0} | Erreurs: ${status.errors || 0}
                                        ${status.last_used ? '<br>Dernier usage: ' + new Date(status.last_used).toLocaleTimeString() : ''}
                                    </p>
                                </div>
                            </div>
                            <div class="flex space-x-2">
                                ${status.blacklisted ? `
                                    <span class="text-xs bg-red-100 text-red-800 px-2 py-1 rounded">Blacklisté</span>
                                ` : ''}
                                <button onclick="InstanceManager.removeInstance('${url}')" 
                                        class="text-red-600 hover:text-red-800 text-sm">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                `;
            });
        } else {
            html = '<p class="text-gray-600">Aucune instance configurée</p>';
        }

        container.innerHTML = html;
    }

    static async addCustomInstance() {
        const urlInput = document.getElementById('newInstanceUrl');
        const url = urlInput.value.trim();

        if (!url) {
            alert('Veuillez entrer une URL');
            return;
        }

        try {
            const response = await fetch('/api/social/instances', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (data.success) {
                urlInput.value = '';
                this.loadInstancesStatus();
                alert('✅ Instance ajoutée avec succès');
            } else {
                alert('❌ Erreur: ' + data.error);
            }
        } catch (error) {
            alert('❌ Erreur réseau: ' + error.message);
        }
    }

    static async removeInstance(instanceUrl) {
        if (!confirm(`Supprimer l'instance ${instanceUrl} ?`)) return;

        try {
            const response = await fetch(`/api/social/instances/${encodeURIComponent(instanceUrl)}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                this.loadInstancesStatus();
            } else {
                alert('❌ Erreur: ' + data.error);
            }
        } catch (error) {
            alert('❌ Erreur réseau: ' + error.message);
        }
    }

    static async resetBlacklist() {
        try {
            const response = await fetch('/api/social/reset-blacklist', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.loadInstancesStatus();
                alert('✅ Blacklist réinitialisée');
            } else {
                alert('❌ Erreur: ' + data.error);
            }
        } catch (error) {
            alert('❌ Erreur réseau: ' + error.message);
        }
    }

    static showError(container, message) {
        container.innerHTML = `
            <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                <div class="flex items-center">
                    <i class="fas fa-exclamation-triangle text-red-600 mr-3"></i>
                    <div>
                        <p class="font-semibold text-red-800">Erreur</p>
                        <p class="text-sm text-red-600">${message}</p>
                    </div>
                </div>
            </div>
        `;
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    window.InstanceManager = InstanceManager;
    console.log('✅ InstanceManager initialisé');
});