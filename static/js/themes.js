// static/js/themes.js - VERSION CORRIGÉE

class ThemeManager {
    static async loadThemes() {
        try {
            const data = await ApiClient.get('/api/themes');
            this.displayThemes(data.themes);
        } catch (error) {
            this.showError('Erreur lors du chargement des thèmes');
        }
    }

    static displayThemes(themes) {
        const container = document.getElementById('themeManagerContent');
        const title = document.getElementById('modalTitle');

        if (!container || !title) return;

        title.textContent = 'Gestion des Thèmes';

        if (!themes || themes.length === 0) {
            container.innerHTML = this.getNoThemesTemplate();
            return;
        }

        container.innerHTML = `
            <div class="mb-6">
                <button onclick="ThemeManager.showCreateForm()" class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition duration-200">
                    <i class="fas fa-plus mr-2"></i>Nouveau thème
                </button>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4" id="themesList">
                ${themes.map(theme => this.getThemeTemplate(theme)).join('')}
            </div>
        `;
    }

    static getThemeTemplate(theme) {
        return `
            <div class="border rounded-lg p-4" style="border-left-color: ${theme.color}; border-left-width: 4px;">
                <div class="flex justify-between items-start mb-2">
                    <h4 class="font-bold text-lg">${this.escapeHtml(theme.name)}</h4>
                    <span class="text-xs px-2 py-1 rounded-full text-white" style="background-color: ${theme.color}">
                        ${this.escapeHtml(theme.id)}
                    </span>
                </div>
                <p class="text-gray-600 text-sm mb-3">${this.escapeHtml(theme.description || 'Aucune description')}</p>
                <div class="flex flex-wrap gap-1 mb-3">
                    ${theme.keywords.slice(0, 5).map(keyword =>
            `<span class="text-xs bg-gray-100 px-2 py-1 rounded">${this.escapeHtml(keyword)}</span>`
        ).join('')}
                    ${theme.keywords.length > 5 ?
                `<span class="text-xs text-gray-500">+${theme.keywords.length - 5} autres</span>` : ''}
                </div>
                <div class="flex space-x-2">
                    <button onclick="ThemeManager.editTheme('${this.escapeHtml(theme.id)}')" 
                            class="text-blue-600 hover:text-blue-800 text-sm">
                        <i class="fas fa-edit mr-1"></i>Modifier
                    </button>
                    <button onclick="ThemeManager.deleteTheme('${this.escapeHtml(theme.id)}')" 
                            class="text-red-600 hover:text-red-800 text-sm">
                        <i class="fas fa-trash mr-1"></i>Supprimer
                    </button>
                </div>
            </div>
        `;
    }

    static getNoThemesTemplate() {
        return `
            <div class="text-center py-8 text-gray-500">
                <i class="fas fa-tags text-3xl mb-3"></i>
                <p>Aucun thème configuré</p>
                <p class="text-sm mt-2">Créez votre premier thème pour commencer l'analyse</p>
                <button onclick="ThemeManager.showCreateForm()" class="mt-4 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">
                    Créer un thème
                </button>
            </div>
        `;
    }

    static showCreateForm() {
        const content = document.getElementById('themeManagerContent');
        const title = document.getElementById('modalTitle');

        if (!content || !title) return;

        title.textContent = 'Créer un Thème';

        content.className = 'p-6 overflow-y-auto flex-1 modal-form-container';

        content.innerHTML = `
            <div class="max-w-2xl mx-auto modal-form-container">
                <form id="createThemeForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">ID du thème *</label>
                        <input type="text" id="themeId" required
                            placeholder="ex: conflits_moyen_orient"
                            class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
                        <p class="text-xs text-gray-500 mt-1">Utilisez des lettres minuscules et underscores</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Nom du thème *</label>
                        <input type="text" id="themeName" required
                            placeholder="ex: Conflits au Moyen-Orient"
                            class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Couleur</label>
                        <input type="color" id="themeColor" value="#6366f1"
                            class="w-full p-1 border border-gray-300 rounded-lg">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                        <textarea id="themeDescription"
                            placeholder="Description du thème..."
                            class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                            rows="3"></textarea>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Mots-clés * (un par ligne)</label>
                        <textarea id="themeKeywords" required
                            class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                            rows="8"
                            placeholder="iran&#10;irak&#10;syrie&#10;israël&#10;palestine&#10;hezbollah"></textarea>
                        <p class="text-xs text-gray-500 mt-1">Un mot-clé par ligne. Soyez précis pour améliorer la détection.</p>
                    </div>
                    <div class="flex space-x-3">
                        <button type="submit"
                            class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition duration-200">
                            <i class="fas fa-save mr-2"></i>Créer le thème
                        </button>
                        <button type="button" onclick="ThemeManager.loadThemes()"
                            class="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition duration-200">
                            Annuler
                        </button>
                    </div>
                </form>
            </div>
        `;

        document.getElementById('createThemeForm').addEventListener('submit', (e) => this.handleCreateSubmit(e));
    }

    static async handleCreateSubmit(event) {
        event.preventDefault();

        const themeData = {
            id: document.getElementById('themeId').value.trim(),
            name: document.getElementById('themeName').value.trim(),
            color: document.getElementById('themeColor').value,
            description: document.getElementById('themeDescription').value.trim(),
            keywords: document.getElementById('themeKeywords').value
                .split('\n')
                .map(k => k.trim())
                .filter(k => k.length > 0)
        };

        if (!themeData.id || !themeData.name || themeData.keywords.length === 0) {
            this.showError('Veuillez remplir tous les champs obligatoires');
            return;
        }

        try {
            await ApiClient.post('/api/themes', themeData);
            this.showSuccess('Thème créé avec succès!');
            setTimeout(() => {
                this.loadThemes();
            }, 1500);
        } catch (error) {
            this.showError('Erreur lors de la création du thème: ' + error.message);
        }
    }

    static async editTheme(themeId) {
        try {
            // Charger les détails du thème
            const themes = await ApiClient.get('/api/themes');
            const theme = themes.themes.find(t => t.id === themeId);

            if (!theme) {
                this.showError('Thème non trouvé');
                return;
            }

            const content = document.getElementById('themeManagerContent');
            const title = document.getElementById('modalTitle');

            if (!content || !title) return;

            title.textContent = `Modifier le thème: ${theme.name}`;

            content.innerHTML = `
                <div class="max-w-2xl mx-auto">
                    <form id="editThemeForm" class="space-y-4">
                        <div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4">
                            <p class="text-sm text-blue-700">
                                <i class="fas fa-info-circle mr-2"></i>
                                ID du thème : <strong>${this.escapeHtml(theme.id)}</strong> (non modifiable)
                            </p>
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Nom du thème *</label>
                            <input type="text" id="editThemeName" required
                                value="${this.escapeHtml(theme.name)}"
                                class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Couleur</label>
                            <input type="color" id="editThemeColor"
                                value="${theme.color || '#6366f1'}"
                                class="w-full p-1 border border-gray-300 rounded-lg">
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                            <textarea id="editThemeDescription"
                                class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                rows="3">${this.escapeHtml(theme.description || '')}</textarea>
                        </div>

                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Mots-clés * (un par ligne)</label>
                            <textarea id="editThemeKeywords" required
                                class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                                rows="8">${theme.keywords.join('\n')}</textarea>
                            <p class="text-xs text-gray-500 mt-1">
                                ${theme.keywords.length} mot(s)-clé(s) actuellement
                            </p>
                        </div>

                        <div class="flex space-x-3">
                            <button type="submit"
                                class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition duration-200">
                                <i class="fas fa-save mr-2"></i>Enregistrer les modifications
                            </button>
                            <button type="button" onclick="ThemeManager.loadThemes()"
                                class="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition duration-200">
                                Annuler
                            </button>
                        </div>
                    </form>
                </div>
            `;

            document.getElementById('editThemeForm').addEventListener('submit', (e) =>
                this.handleEditSubmit(e, themeId));

        } catch (error) {
            console.error('Erreur chargement thème:', error);
            this.showError('Impossible de charger le thème');
        }
    }

    static async handleEditSubmit(event, themeId) {
        event.preventDefault();

        const themeData = {
            name: document.getElementById('editThemeName').value.trim(),
            color: document.getElementById('editThemeColor').value,
            description: document.getElementById('editThemeDescription').value.trim(),
            keywords: document.getElementById('editThemeKeywords').value
                .split('\n')
                .map(k => k.trim())
                .filter(k => k.length > 0)
        };

        if (!themeData.name || themeData.keywords.length === 0) {
            this.showError('Veuillez remplir tous les champs obligatoires');
            return;
        }

        try {
            await ApiClient.put(`/api/themes/${themeId}`, themeData);
            this.showSuccess('Thème modifié avec succès!');
            setTimeout(() => {
                this.loadThemes();
            }, 1500);
        } catch (error) {
            this.showError('Erreur lors de la modification du thème: ' + error.message);
        }
    }

    static async deleteTheme(themeId) {
        if (!confirm(`Êtes-vous sûr de vouloir supprimer le thème "${themeId}" ?\n\nCette action est irréversible.`)) {
            return;
        }

        try {
            await ApiClient.delete(`/api/themes/${themeId}`);
            this.showSuccess('Thème supprimé avec succès!');
            setTimeout(() => {
                this.loadThemes();
            }, 1500);
        } catch (error) {
            this.showError('Erreur lors de la suppression du thème: ' + error.message);
        }
    }

    static showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded shadow-lg z-50 animate-fade-in';
        errorDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-exclamation-circle mr-3 text-xl"></i>
                <div>
                    <p class="font-bold">Erreur</p>
                    <p class="text-sm">${this.escapeHtml(message)}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-red-700 hover:text-red-900">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        document.body.appendChild(errorDiv);

        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }

    static showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'fixed top-4 right-4 bg-green-100 border-l-4 border-green-500 text-green-700 p-4 rounded shadow-lg z-50 animate-fade-in';
        successDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-check-circle mr-3 text-xl"></i>
                <div>
                    <p class="font-bold">Succès</p>
                    <p class="text-sm">${this.escapeHtml(message)}</p>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-green-700 hover:text-green-900">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        document.body.appendChild(successDiv);

        setTimeout(() => {
            if (successDiv.parentElement) {
                successDiv.remove();
            }
        }, 3000);
    }

    static escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    window.ThemeManager = ThemeManager;
    console.log('✅ ThemeManager initialisé');
});
