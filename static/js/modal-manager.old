// static/js/modal-manager.js - Gestionnaire de modales avec centrage et défilement

class ModalManager {
    /**
     * Affiche une modale avec centrage et défilement appropriés
     * @param {string} modalId - ID de la modale à afficher
     */
    static showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`❌ Modale ${modalId} non trouvée`);
            return;
        }

        // Vérifier si la modale a déjà la bonne structure
        if (!modal.classList.contains('modal-overlay')) {
            this.restructureModal(modal);
        }

        // Afficher la modale
        modal.classList.remove('hidden');
        modal.classList.add('modal-visible');
        
        // Empêcher le scroll du body
        document.body.style.overflow = 'hidden';
        
        // Focus sur la modale
        modal.focus();
        
        console.log(`✅ Modale ${modalId} affichée`);
    }

    /**
     * Cache une modale
     * @param {string} modalId - ID de la modale à cacher
     */
    static hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) {
            console.error(`❌ Modale ${modalId} non trouvée`);
            return;
        }

        modal.classList.add('hidden');
        modal.classList.remove('modal-visible');
        
        // Réactiver le scroll du body
        document.body.style.overflow = '';
        
        console.log(`✅ Modale ${modalId} cachée`);
    }

    /**
     * Restructure une modale existante pour avoir la bonne structure
     * @param {HTMLElement} modal - Élément modal à restructurer
     */
    static restructureModal(modal) {
        // Sauvegarder le contenu actuel
        const content = modal.innerHTML;
        
        // Appliquer la classe overlay
        modal.classList.add('modal-overlay', 'hidden');
        
        // Créer la nouvelle structure
        modal.innerHTML = `
            <div class="modal-content-wrapper" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h2 id="modalTitle" class="modal-title">Modale</h2>
                    <button type="button" 
                            class="modal-close-button" 
                            onclick="ModalManager.hideModal('${modal.id}')"
                            aria-label="Fermer">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div id="themeManagerContent" class="modal-body">
                    ${content}
                </div>
            </div>
        `;
        
        // Fermer en cliquant sur l'overlay
        modal.onclick = (e) => {
            if (e.target === modal) {
                this.hideModal(modal.id);
            }
        };
        
        // Fermer avec Échap
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                this.hideModal(modal.id);
            }
        });
    }

    /**
     * Crée une nouvelle modale dynamiquement
     * @param {string} id - ID unique de la modale
     * @param {string} title - Titre de la modale
     * @param {string} content - Contenu HTML de la modale
     * @param {Object} options - Options supplémentaires
     * @returns {HTMLElement} - L'élément modal créé
     */
    static createModal(id, title, content, options = {}) {
        // Supprimer une modale existante avec le même ID
        const existing = document.getElementById(id);
        if (existing) {
            existing.remove();
        }

        const modal = document.createElement('div');
        modal.id = id;
        modal.className = 'modal-overlay hidden';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.setAttribute('aria-labelledby', 'modalTitle');

        const maxWidth = options.maxWidth || '1200px';
        const showFooter = options.showFooter || false;

        modal.innerHTML = `
            <div class="modal-content-wrapper" style="max-width: ${maxWidth}" onclick="event.stopPropagation()">
                <div class="modal-header">
                    <h2 id="modalTitle" class="modal-title">${title}</h2>
                    <button type="button" 
                            class="modal-close-button" 
                            onclick="ModalManager.hideModal('${id}')"
                            aria-label="Fermer">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div id="themeManagerContent" class="modal-body">
                    ${content}
                </div>
                ${showFooter ? `
                    <div class="modal-footer">
                        <button type="button" 
                                class="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600"
                                onclick="ModalManager.hideModal('${id}')">
                            Fermer
                        </button>
                    </div>
                ` : ''}
            </div>
        `;

        // Fermer en cliquant sur l'overlay
        modal.onclick = (e) => {
            if (e.target === modal) {
                this.hideModal(id);
            }
        };

        // Ajouter au DOM
        document.body.appendChild(modal);

        // Fermer avec Échap
        const escapeHandler = (e) => {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                this.hideModal(id);
            }
        };
        document.addEventListener('keydown', escapeHandler);

        // Nettoyer à la destruction
        modal._escapeHandler = escapeHandler;

        console.log(`✅ Modale ${id} créée`);
        return modal;
    }

    /**
     * Détruit une modale
     * @param {string} modalId - ID de la modale à détruire
     */
    static destroyModal(modalId) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        // Nettoyer les event listeners
        if (modal._escapeHandler) {
            document.removeEventListener('keydown', modal._escapeHandler);
        }

        // Supprimer du DOM
        modal.remove();

        // Réactiver le scroll du body
        document.body.style.overflow = '';

        console.log(`✅ Modale ${modalId} détruite`);
    }

    /**
     * Met à jour le titre d'une modale
     * @param {string} modalId - ID de la modale
     * @param {string} title - Nouveau titre
     */
    static updateTitle(modalId, title) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        const titleElement = modal.querySelector('#modalTitle');
        if (titleElement) {
            titleElement.textContent = title;
        }
    }

    /**
     * Met à jour le contenu d'une modale
     * @param {string} modalId - ID de la modale
     * @param {string} content - Nouveau contenu HTML
     */
    static updateContent(modalId, content) {
        const modal = document.getElementById(modalId);
        if (!modal) return;

        const contentElement = modal.querySelector('#themeManagerContent, .modal-body');
        if (contentElement) {
            contentElement.innerHTML = content;
            // Scroll en haut après mise à jour
            contentElement.scrollTop = 0;
        }
    }

    /**
     * Affiche une confirmation modale
     * @param {string} title - Titre de la confirmation
     * @param {string} message - Message de confirmation
     * @param {Function} onConfirm - Callback si confirmé
     * @param {Function} onCancel - Callback si annulé
     */
    static confirm(title, message, onConfirm, onCancel = null) {
        const modalId = 'confirmModal_' + Date.now();
        
        const content = `
            <div class="text-center">
                <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-yellow-100 mb-4">
                    <i class="fas fa-exclamation-triangle text-yellow-600 text-xl"></i>
                </div>
                <p class="text-gray-700 mb-6">${message}</p>
                <div class="flex justify-center space-x-3">
                    <button type="button" 
                            id="confirmBtn"
                            class="bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition duration-200">
                        <i class="fas fa-check mr-2"></i>Confirmer
                    </button>
                    <button type="button" 
                            id="cancelBtn"
                            class="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600 transition duration-200">
                        <i class="fas fa-times mr-2"></i>Annuler
                    </button>
                </div>
            </div>
        `;

        const modal = this.createModal(modalId, title, content, { maxWidth: '500px' });
        this.showModal(modalId);

        // Gérer les boutons
        document.getElementById('confirmBtn').onclick = () => {
            this.hideModal(modalId);
            setTimeout(() => this.destroyModal(modalId), 300);
            if (onConfirm) onConfirm();
        };

        document.getElementById('cancelBtn').onclick = () => {
            this.hideModal(modalId);
            setTimeout(() => this.destroyModal(modalId), 300);
            if (onCancel) onCancel();
        };
    }

    /**
     * Affiche un message d'alerte modale
     * @param {string} title - Titre de l'alerte
     * @param {string} message - Message d'alerte
     * @param {string} type - Type: 'info', 'success', 'warning', 'error'
     */
    static alert(title, message, type = 'info') {
        const modalId = 'alertModal_' + Date.now();
        
        const icons = {
            info: 'fa-info-circle text-blue-600',
            success: 'fa-check-circle text-green-600',
            warning: 'fa-exclamation-triangle text-yellow-600',
            error: 'fa-times-circle text-red-600'
        };

        const bgColors = {
            info: 'bg-blue-100',
            success: 'bg-green-100',
            warning: 'bg-yellow-100',
            error: 'bg-red-100'
        };

        const icon = icons[type] || icons.info;
        const bgColor = bgColors[type] || bgColors.info;

        const content = `
            <div class="text-center">
                <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full ${bgColor} mb-4">
                    <i class="fas ${icon} text-xl"></i>
                </div>
                <p class="text-gray-700 mb-6">${message}</p>
                <button type="button" 
                        id="okBtn"
                        class="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition duration-200">
                    <i class="fas fa-check mr-2"></i>OK
                </button>
            </div>
        `;

        const modal = this.createModal(modalId, title, content, { maxWidth: '500px' });
        this.showModal(modalId);

        document.getElementById('okBtn').onclick = () => {
            this.hideModal(modalId);
            setTimeout(() => this.destroyModal(modalId), 300);
        };
    }
}

// Initialisation globale
window.ModalManager = ModalManager;

// Au chargement du DOM, restructurer les modales existantes
document.addEventListener('DOMContentLoaded', function () {
    // Rechercher toutes les modales existantes
    const modals = document.querySelectorAll('[id$="Modal"]');
    modals.forEach(modal => {
        if (!modal.classList.contains('modal-overlay')) {
            ModalManager.restructureModal(modal);
        }
    });

    console.log('✅ ModalManager initialisé - Modales restructurées');
});