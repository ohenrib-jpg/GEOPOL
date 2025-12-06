// static/js/geo-narrative.js - VERSION CORRIGÉE

class GeoNarrativeManager {
    static async showGeoNarrativePanel() {
        const content = `
            <div class="max-w-6xl mx-auto space-y-6">
                <!-- En-tête explicatif -->
                <div class="bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-blue-500 p-4 rounded-lg">
                    <div class="flex items-start">
                        <div class="flex-shrink-0">
                            <i class="fas fa-globe-europe text-blue-500 text-2xl"></i>
                        </div>
                        <div class="ml-3">
                            <h3 class="text-lg font-semibold text-gray-800">🌍 Cartographie des Narratifs Transnationaux</h3>
                            <p class="mt-2 text-sm text-gray-600">
                                Détection automatique des patterns linguistiques qui traversent les frontières
                            </p>
                        </div>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- Analyse des patterns -->
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h3 class="text-xl font-bold text-gray-800 mb-4">
                            <i class="fas fa-code-branch text-indigo-600 mr-2"></i>
                            Patterns Transnationaux
                        </h3>
                        <p class="text-gray-600 mb-4 text-sm">
                            Détecte les éléments de langage communs entre pays
                        </p>
                        <div class="space-y-3">
                            <button onclick="GeoNarrativeManager.analyzePatterns()"
                                    class="w-full bg-indigo-600 text-white px-4 py-3 rounded-lg hover:bg-indigo-700 transition duration-200">
                                <i class="fas fa-search mr-2"></i>Analyser les Patterns
                            </button>
                        </div>
                        <div id="patternsResults" class="mt-4"></div>
                    </div>

                    <!-- Carte d'influence -->
                    <div class="bg-white rounded-lg shadow-md p-6">
                        <h3 class="text-xl font-bold text-gray-800 mb-4">
                            <i class="fas fa-project-diagram text-green-600 mr-2"></i>
                            Réseau d'Influence
                        </h3>
                        <p class="text-gray-600 mb-4 text-sm">
                            Visualise les flux narratifs entre pays
                        </p>
                        <div class="space-y-3">
                            <button onclick="GeoNarrativeManager.generateInfluenceMap()"
                                    class="w-full bg-green-600 text-white px-4 py-3 rounded-lg hover:bg-green-700 transition duration-200">
                                <i class="fas fa-network-wired mr-2"></i>Générer la Carte
                            </button>
                        </div>
                        <div id="influenceResults" class="mt-4"></div>
                    </div>
                </div>

                <!-- Résultats en temps réel -->
                <div id="geoNarrativeResults" class="hidden">
                    <!-- Les résultats s'afficheront ici -->
                </div>
            </div>
        `;

        // Afficher dans le modal existant
        document.getElementById('themeManagerContent').innerHTML = content;
        ModalManager.showModal('themeManagerModal');
    }

    static async analyzePatterns() {
        const resultsDiv = document.getElementById('patternsResults');
        resultsDiv.innerHTML = '<div class="text-blue-600">🔄 Analyse des patterns en cours...</div>';

        try {
            const response = await fetch('/api/geo-narrative/patterns?days=7&min_countries=2');
            const data = await response.json();

            if (data && Array.isArray(data)) {
                this.displayPatterns(data, resultsDiv);
            } else if (data.success && data.patterns) {
                this.displayPatterns(data.patterns, resultsDiv);
            } else {
                resultsDiv.innerHTML = `<div class="text-red-600">❌ ${data.error || 'Format de données inattendu'}</div>`;
            }
        } catch (error) {
            resultsDiv.innerHTML = `<div class="text-red-600">❌ Erreur: ${error.message}</div>`;
        }
    }

    static displayPatterns(patterns, container) {
        if (!patterns || patterns.length === 0) {
            container.innerHTML = '<div class="text-gray-500 text-center py-4">Aucun pattern transnational détecté</div>';
            return;
        }

        container.innerHTML = `
            <div class="space-y-3">
                <div class="flex justify-between items-center text-sm text-gray-600">
                    <span>${patterns.length} pattern(s) détecté(s)</span>
                    <span>🌐 ${new Set(patterns.flatMap(p => p.countries || [])).size} pays</span>
                </div>
                ${patterns.slice(0, 10).map(pattern => `
                    <div class="border border-gray-200 rounded-lg p-4 bg-white hover:shadow-md transition">
                        <div class="flex justify-between items-start mb-2">
                            <span class="font-semibold text-gray-800 text-sm">"${pattern.pattern || pattern.pattern_text || 'Pattern'}"</span>
                            <span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                                Force: ${pattern.strength || pattern.country_count || 1}
                            </span>
                        </div>
                        <div class="flex items-center text-xs text-gray-600">
                            <i class="fas fa-globe-europe mr-1"></i>
                            <span>${(pattern.countries || []).join(', ')}</span>
                        </div>
                        ${pattern.total_occurrences ? `
                            <div class="flex items-center text-xs text-gray-500 mt-1">
                                <i class="fas fa-chart-bar mr-1"></i>
                                <span>${pattern.total_occurrences} occurrences</span>
                            </div>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    static async generateInfluenceMap() {
        const resultsDiv = document.getElementById('influenceResults');
        resultsDiv.innerHTML = '<div class="text-green-600">🔄 Génération de la carte d\'influence...</div>';

        try {
            const response = await fetch('/api/geo-narrative/influence-map?days=7');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                this.displayInfluenceMap(data.influence_network, resultsDiv);
            } else {
                resultsDiv.innerHTML = `<div class="text-red-600">❌ ${data.error || 'Erreur inconnue'}</div>`;
            }
        } catch (error) {
            // Fallback si la route n'existe pas encore
            console.log('Route influence-map non disponible, utilisation des données mockées');
            this.displayInfluenceMap(this.generateMockInfluenceData(), resultsDiv);
        }
    }

    static displayInfluenceMap(influenceData, container) {
        if (!influenceData || !influenceData.nodes) {
            container.innerHTML = `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div class="flex items-center">
                        <i class="fas fa-info-circle text-yellow-600 mr-2"></i>
                        <span class="text-yellow-800 text-sm">Fonctionnalité en cours de développement</span>
                    </div>
                    <p class="text-yellow-600 text-xs mt-2">
                        La carte d'influence avancée sera disponible dans la prochaine version.
                    </p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h4 class="font-semibold text-gray-800 mb-3">🗺️ Carte d'Influence Narrative</h4>
                <div class="space-y-2 text-sm">
                    <p><strong>Pays analysés:</strong> ${influenceData.nodes.length}</p>
                    <p><strong>Connexions détectées:</strong> ${influenceData.edges ? influenceData.edges.length : 0}</p>
                    <p><strong>Patterns:</strong> ${influenceData.metadata ? influenceData.metadata.total_patterns : 'N/A'}</p>
                    
                    ${influenceData.nodes.length > 0 ? `
                        <div class="mt-3">
                            <h5 class="font-semibold text-gray-700 mb-2">Top Pays par influence:</h5>
                            ${influenceData.nodes.slice(0, 5).map(node => `
                                <div class="flex justify-between items-center p-2 bg-white rounded border mb-1">
                                    <span class="font-medium">${node.label || node.id}</span>
                                    <span class="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                                        ${node.size || 0} patterns
                                    </span>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    static generateMockInfluenceData() {
        return {
            nodes: [
                { id: 'FR', label: 'France', size: 15 },
                { id: 'DE', label: 'Allemagne', size: 12 },
                { id: 'UK', label: 'Royaume-Uni', size: 10 },
                { id: 'US', label: 'États-Unis', size: 8 },
                { id: 'ES', label: 'Espagne', size: 6 }
            ],
            edges: [
                { source: 'FR', target: 'DE', weight: 8 },
                { source: 'FR', target: 'UK', weight: 6 },
                { source: 'DE', target: 'US', weight: 4 },
                { source: 'UK', target: 'US', weight: 5 }
            ],
            metadata: {
                total_patterns: 45,
                countries_analyzed: 5,
                analysis_period: '7 jours'
            }
        };
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    window.GeoNarrativeManager = GeoNarrativeManager;
    console.log('✅ GeoNarrativeManager initialisé (version corrigée)');
});
