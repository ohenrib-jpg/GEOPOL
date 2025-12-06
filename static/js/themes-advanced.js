// static/js/themes-advanced.js - Gestion avancée des thèmes

class AdvancedThemeManager extends ThemeManager {

    static async showAdvancedCreateForm() {
        const content = document.getElementById('themeManagerContent');
        const title = document.getElementById('modalTitle');

        if (!content || !title) return;

        title.textContent = 'Créer un Thème Avancé';

        content.innerHTML = `
            <div class="max-w-4xl mx-auto">
                <form id="advancedThemeForm" class="space-y-6">
                    <!-- Informations de base -->
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-gray-800 mb-3">📋 Informations de base</h4>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">ID du thème *</label>
                                <input type="text" id="themeId" required 
                                       placeholder="ex: geopolitique"
                                       class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Nom du thème *</label>
                                <input type="text" id="themeName" required 
                                       placeholder="ex: Géopolitique"
                                       class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Couleur</label>
                                <input type="color" id="themeColor" value="#FF6B6B" 
                                       class="w-full p-1 border border-gray-300 rounded-lg">
                            </div>
                        </div>
                        <div class="mt-4">
                            <label class="block text-sm font-medium text-gray-700 mb-1">Description</label>
                            <textarea id="themeDescription" 
                                      placeholder="Description détaillée du thème..."
                                      class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500" 
                                      rows="2"></textarea>
                        </div>
                    </div>

                    <!-- Mots-clés pondérés -->
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-gray-800 mb-3">🔑 Mots-clés pondérés</h4>
                        <p class="text-sm text-gray-600 mb-3">
                            Ajoutez des mots-clés avec leur importance (poids). Plus le poids est élevé, plus le mot est déterminant.
                        </p>
                        
                        <div id="keywordsContainer" class="space-y-2 mb-3">
                            <!-- Les mots-clés seront ajoutés ici -->
                        </div>
                        
                        <div class="flex space-x-2">
                            <input type="text" id="newKeyword" 
                                   placeholder="Nouveau mot-clé"
                                   class="flex-1 p-2 border border-gray-300 rounded-lg">
                            <select id="keywordWeight" class="p-2 border border-gray-300 rounded-lg">
                                <option value="1.0">Standard (1.0)</option>
                                <option value="1.5">Important (1.5)</option>
                                <option value="2.0">Très important (2.0)</option>
                                <option value="2.5">Critique (2.5)</option>
                                <option value="3.0">Essentiel (3.0)</option>
                            </select>
                            <select id="keywordCategory" class="p-2 border border-gray-300 rounded-lg">
                                <option value="primary">Primaire</option>
                                <option value="secondary">Secondaire</option>
                                <option value="critical">Critique</option>
                            </select>
                            <button type="button" onclick="AdvancedThemeManager.addKeyword()" 
                                    class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>

                        <!-- Templates prédéfinis -->
                        <div class="mt-3">
                            <label class="text-sm font-medium text-gray-700">Templates rapides :</label>
                            <div class="flex flex-wrap gap-2 mt-2">
                                <button type="button" onclick="AdvancedThemeManager.loadTemplate('geopolitique')" 
                                        class="text-xs bg-blue-100 text-blue-800 px-3 py-1 rounded-full hover:bg-blue-200">
                                    Géopolitique
                                </button>
                                <button type="button" onclick="AdvancedThemeManager.loadTemplate('economie')" 
                                        class="text-xs bg-green-100 text-green-800 px-3 py-1 rounded-full hover:bg-green-200">
                                    Économie
                                </button>
                                <button type="button" onclick="AdvancedThemeManager.loadTemplate('technologie')" 
                                        class="text-xs bg-purple-100 text-purple-800 px-3 py-1 rounded-full hover:bg-purple-200">
                                    Technologie
                                </button>
                                <button type="button" onclick="AdvancedThemeManager.loadTemplate('environnement')" 
                                        class="text-xs bg-teal-100 text-teal-800 px-3 py-1 rounded-full hover:bg-teal-200">
                                    Environnement
                                </button>
                            </div>
                        </div>
                    </div>

                    <!-- Synonymes -->
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-gray-800 mb-3">🔄 Synonymes et variations</h4>
                        <p class="text-sm text-gray-600 mb-3">
                            Enrichissez la détection en ajoutant des synonymes pour chaque mot-clé principal.
                        </p>
                        <div id="synonymsContainer" class="space-y-2">
                            <!-- Les synonymes seront ajoutés dynamiquement -->
                        </div>
                    </div>

                    <!-- Contexte géopolitique -->
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h4 class="font-semibold text-gray-800 mb-3">🌍 Contexte géopolitique (optionnel)</h4>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Régions ciblées</label>
                                <textarea id="contextRegions" 
                                          placeholder="Europe, Moyen-Orient, Asie..."
                                          class="w-full p-2 border border-gray-300 rounded-lg" 
                                          rows="2"></textarea>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-1">Acteurs principaux</label>
                                <textarea id="contextActors" 
                                          placeholder="États, ONU, OTAN..."
                                          class="w-full p-2 border border-gray-300 rounded-lg" 
                                          rows="2"></textarea>
                            </div>
                        </div>
                    </div>

                    <!-- Boutons -->
                    <div class="flex space-x-3">
                        <button type="submit" 
                                class="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition duration-200">
                            <i class="fas fa-save mr-2"></i>Créer le thème avancé
                        </button>
                        <button type="button" onclick="AdvancedThemeManager.loadThemes()" 
                                class="bg-gray-500 text-white px-6 py-2 rounded-lg hover:bg-gray-600 transition duration-200">
                            Annuler
                        </button>
                    </div>
                </form>
            </div>
        `;

        document.getElementById('advancedThemeForm').addEventListener('submit', (e) =>
            this.handleAdvancedSubmit(e));

        ModalManager.showModal('themeManagerModal');
    }

    static addKeyword() {
        const keywordInput = document.getElementById('newKeyword');
        const weightSelect = document.getElementById('keywordWeight');
        const categorySelect = document.getElementById('keywordCategory');
        const container = document.getElementById('keywordsContainer');

        const keyword = keywordInput.value.trim();
        if (!keyword) return;

        const weight = parseFloat(weightSelect.value);
        const category = categorySelect.value;

        const keywordElement = document.createElement('div');
        keywordElement.className = 'flex items-center space-x-2 bg-white p-2 rounded border';
        keywordElement.innerHTML = `
            <span class="flex-1 font-medium">${this.escapeHtml(keyword)}</span>
            <span class="text-xs px-2 py-1 rounded ${this.getCategoryBadge(category)}">
                ${category}
            </span>
            <span class="text-sm text-gray-600">Poids: ${weight}</span>
            <button type="button" onclick="this.parentElement.remove()" 
                    class="text-red-600 hover:text-red-800">
                <i class="fas fa-times"></i>
            </button>
        `;
        keywordElement.dataset.keyword = keyword;
        keywordElement.dataset.weight = weight;
        keywordElement.dataset.category = category;

        container.appendChild(keywordElement);
        keywordInput.value = '';

        // Mettre à jour la section synonymes
        this.updateSynonymsSection();
    }

    static getCategoryBadge(category) {
        switch (category) {
            case 'critical': return 'bg-red-100 text-red-800';
            case 'primary': return 'bg-blue-100 text-blue-800';
            case 'secondary': return 'bg-gray-100 text-gray-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }

    static updateSynonymsSection() {
        const container = document.getElementById('synonymsContainer');
        const keywordsContainer = document.getElementById('keywordsContainer');
        const keywords = Array.from(keywordsContainer.children).map(el => el.dataset.keyword);

        if (keywords.length === 0) {
            container.innerHTML = '<p class="text-sm text-gray-500">Ajoutez d\'abord des mots-clés</p>';
            return;
        }

        container.innerHTML = keywords.map(keyword => `
            <div class="border p-3 rounded">
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Synonymes pour "${keyword}"
                </label>
                <input type="text" 
                       id="synonyms_${keyword}" 
                       placeholder="ex: conflit armé, hostilités, guerre (séparés par des virgules)"
                       class="w-full p-2 border border-gray-300 rounded-lg text-sm">
            </div>
        `).join('');
    }

    static loadTemplate(templateName) {
        const templates = {
            geopolitique: {
                name: 'Géopolitique',
                color: '#FF6B6B',
                description: 'Analyse des relations internationales, conflits et diplomatie',
                keywords: [
                    { word: 'guerre', weight: 3.0, category: 'critical' },
                    { word: 'conflit', weight: 2.5, category: 'critical' },
                    { word: 'diplomatie', weight: 2.0, category: 'primary' },
                    { word: 'sanctions', weight: 2.0, category: 'primary' },
                    { word: 'alliance', weight: 1.5, category: 'primary' },
                    { word: 'tension', weight: 1.5, category: 'primary' },
                    { word: 'négociation', weight: 1.0, category: 'secondary' },
                    { word: 'traité', weight: 1.0, category: 'secondary' }
                ],
                synonyms: {
                    'guerre': 'conflit armé, hostilités, combat',
                    'diplomatie': 'relations internationales, négociations',
                    'sanctions': 'mesures restrictives, embargo'
                }
            },
            economie: {
                name: 'Économie',
                color: '#10B981',
                description: 'Analyse économique et financière',
                keywords: [
                    { word: 'économie', weight: 2.5, category: 'critical' },
                    { word: 'croissance', weight: 2.0, category: 'primary' },
                    { word: 'inflation', weight: 2.0, category: 'primary' },
                    { word: 'banque', weight: 1.5, category: 'primary' },
                    { word: 'investissement', weight: 1.5, category: 'primary' },
                    { word: 'marché', weight: 1.0, category: 'secondary' }
                ]
            },
            technologie: {
                name: 'Technologie',
                color: '#6366f1',
                description: 'Innovations et développements technologiques',
                keywords: [
                    { word: 'intelligence artificielle', weight: 3.0, category: 'critical' },
                    { word: 'AI', weight: 3.0, category: 'critical' },
                    { word: 'innovation', weight: 2.0, category: 'primary' },
                    { word: 'technologie', weight: 2.0, category: 'primary' },
                    { word: 'numérique', weight: 1.5, category: 'primary' }
                ]
            },
            environnement: {
                name: 'Environnement',
                color: '#22C55E',
                description: 'Enjeux environnementaux et climatiques',
                keywords: [
                    { word: 'climat', weight: 3.0, category: 'critical' },
                    { word: 'environnement', weight: 2.5, category: 'critical' },
                    { word: 'réchauffement', weight: 2.5, category: 'critical' },
                    { word: 'pollution', weight: 2.0, category: 'primary' },
                    { word: 'biodiversité', weight: 1.5, category: 'primary' }
                ]
            }
        };

        const template = templates[templateName];
        if (!template) return;

        // Remplir les champs
        document.getElementById('themeId').value = templateName;
        document.getElementById('themeName').value = template.name;
        document.getElementById('themeColor').value = template.color;
        document.getElementById('themeDescription').value = template.description;

        // Vider et remplir les mots-clés
        const container = document.getElementById('keywordsContainer');
        container.innerHTML = '';

        template.keywords.forEach(kw => {
            const keywordElement = document.createElement('div');
            keywordElement.className = 'flex items-center space-x-2 bg-white p-2 rounded border';
            keywordElement.innerHTML = `
                <span class="flex-1 font-medium">${kw.word}</span>
                <span class="text-xs px-2 py-1 rounded ${this.getCategoryBadge(kw.category)}">
                    ${kw.category}
                </span>
                <span class="text-sm text-gray-600">Poids: ${kw.weight}</span>
                <button type="button" onclick="this.parentElement.remove()" 
                        class="text-red-600 hover:text-red-800">
                    <i class="fas fa-times"></i>
                </button>
            `;
            keywordElement.dataset.keyword = kw.word;
            keywordElement.dataset.weight = kw.weight;
            keywordElement.dataset.category = kw.category;
            container.appendChild(keywordElement);
        });

        // Mettre à jour les synonymes
        this.updateSynonymsSection();

        if (template.synonyms) {
            Object.entries(template.synonyms).forEach(([keyword, syns]) => {
                const input = document.getElementById(`synonyms_${keyword}`);
                if (input) input.value = syns;
            });
        }

        this.showSuccess('Template chargé ! Modifiez selon vos besoins.');
    }

    static async handleAdvancedSubmit(event) {
        event.preventDefault();

        // Collecter les données
        const themeId = document.getElementById('themeId').value.trim();
        const themeName = document.getElementById('themeName').value.trim();
        const themeColor = document.getElementById('themeColor').value;
        const themeDescription = document.getElementById('themeDescription').value.trim();

        // Collecter les mots-clés
        const keywordsContainer = document.getElementById('keywordsContainer');
        const keywords = Array.from(keywordsContainer.children).map(el => ({
            word: el.dataset.keyword,
            weight: parseFloat(el.dataset.weight),
            category: el.dataset.category
        }));

        if (keywords.length === 0) {
            this.showError('Ajoutez au moins un mot-clé');
            return;
        }

        // Collecter les synonymes
        const synonyms = {};
        keywords.forEach(kw => {
            const input = document.getElementById(`synonyms_${kw.word}`);
            if (input && input.value.trim()) {
                synonyms[kw.word] = input.value.split(',').map(s => s.trim()).filter(s => s);
            }
        });

        // Contexte
        const contextRegions = document.getElementById('contextRegions').value.trim();
        const contextActors = document.getElementById('contextActors').value.trim();

        const context = {};
        if (contextRegions) context.regions = contextRegions.split(',').map(s => s.trim());
        if (contextActors) context.actors = contextActors.split(',').map(s => s.trim());

        const themeData = {
            id: themeId,
            name: themeName,
            color: themeColor,
            description: themeDescription,
            keywords: keywords,
            synonyms: synonyms,
            context: context
        };

        try {
            await ApiClient.post('/api/themes/advanced', themeData);
            this.showSuccess('Thème avancé créé avec succès!');
            this.loadThemes();
        } catch (error) {
            this.showError('Erreur lors de la création: ' + error.message);
        }
    }

    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    window.AdvancedThemeManager = AdvancedThemeManager;
    console.log('✅ AdvancedThemeManager initialisé');
});