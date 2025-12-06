// static/js/entity-manager-enhanced.js - Client JavaScript pour l'API intégrée

/**
 * GeoEntityManager - Client pour interagir avec l'API intégrée Geo-Narrative + Entities
 */
class GeoEntityManager {
    constructor(baseUrl = '/api/geo-entity') {
        this.baseUrl = baseUrl;
        this.cache = new Map();
        this.cacheDuration = 5 * 60 * 1000; // 5 minutes
    }

    // =========================================================================
    // MÉTHODES PRINCIPALES
    // =========================================================================

    /**
     * Récupère les patterns enrichis avec entités
     * @param {number} days - Nombre de jours à analyser
     * @param {number} minCountries - Nombre minimum de pays
     * @returns {Promise<Object>} Patterns enrichis
     */
    async getPatternsEnriched(days = 7, minCountries = 2) {
        const cacheKey = `patterns_${days}_${minCountries}`;
        
        // Vérifier le cache
        if (this._isCacheValid(cacheKey)) {
            console.log('📦 Données récupérées depuis le cache');
            return this.cache.get(cacheKey).data;
        }

        try {
            console.log(`🔍 Récupération patterns enrichis (${days} jours)...`);
            
            const response = await fetch(
                `${this.baseUrl}/patterns-enriched?days=${days}&min_countries=${minCountries}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            // Mettre en cache
            this._setCache(cacheKey, data);
            
            console.log(`✅ ${data.count} patterns enrichis récupérés`);
            return data;

        } catch (error) {
            console.error('❌ Erreur récupération patterns enrichis:', error);
            throw error;
        }
    }

    /**
     * Analyse complète : patterns + réseau d'entités
     * @param {number} days - Nombre de jours
     * @returns {Promise<Object>} Rapport complet
     */
    async getComprehensiveAnalysis(days = 7) {
        try {
            console.log(`🔎 Lancement analyse complète (${days} jours)...`);
            
            const response = await fetch(
                `${this.baseUrl}/comprehensive-analysis?days=${days}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            console.log('✅ Analyse complète terminée');
            console.log('📊 Résumé:', data.report.summary);
            
            return data;

        } catch (error) {
            console.error('❌ Erreur analyse complète:', error);
            throw error;
        }
    }

    /**
     * Recherche les patterns contenant une entité spécifique
     * @param {string} entityName - Nom de l'entité
     * @param {string|null} entityType - Type d'entité (optionnel)
     * @param {number} days - Nombre de jours
     * @returns {Promise<Object>} Patterns correspondants
     */
    async findPatternsByEntity(entityName, entityType = null, days = 7) {
        try {
            console.log(`🔍 Recherche patterns pour: ${entityName}`);
            
            let url = `${this.baseUrl}/patterns/by-entity?entity=${encodeURIComponent(entityName)}&days=${days}`;
            if (entityType) {
                url += `&type=${entityType}`;
            }

            const response = await fetch(url);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            console.log(`✅ ${data.count} patterns trouvés pour ${entityName}`);
            return data;

        } catch (error) {
            console.error('❌ Erreur recherche par entité:', error);
            throw error;
        }
    }

    /**
     * Récupère la timeline d'une entité
     * @param {string} entityName - Nom de l'entité
     * @param {number} days - Nombre de jours
     * @returns {Promise<Object>} Timeline
     */
    async getEntityTimeline(entityName, days = 30) {
        try {
            console.log(`📅 Récupération timeline pour: ${entityName}`);
            
            const response = await fetch(
                `${this.baseUrl}/entity/timeline?entity=${encodeURIComponent(entityName)}&days=${days}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            console.log(`✅ Timeline récupérée: ${data.timeline.total_occurrences} occurrences`);
            return data;

        } catch (error) {
            console.error('❌ Erreur timeline:', error);
            throw error;
        }
    }

    /**
     * Récupère le graphe de relations entre entités
     * @param {number} days - Nombre de jours
     * @returns {Promise<Object>} Graphe de relations
     */
    async getEntityRelations(days = 7) {
        try {
            console.log(`🕸️ Extraction relations entités (${days} jours)...`);
            
            const response = await fetch(
                `${this.baseUrl}/entity-relations?days=${days}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            const graph = data.graph;
            console.log(`✅ Graphe extrait: ${graph.metadata.total_nodes} nœuds, ${graph.metadata.total_edges} liens`);
            
            return data;

        } catch (error) {
            console.error('❌ Erreur relations:', error);
            throw error;
        }
    }

    // =========================================================================
    // EXPORT ET RAPPORTS
    // =========================================================================

    /**
     * Télécharge un rapport complet
     * @param {number} days - Nombre de jours
     * @param {string} format - Format ('json' ou 'markdown')
     */
    async downloadReport(days = 7, format = 'json') {
        try {
            console.log(`📥 Téléchargement rapport (${format})...`);
            
            const response = await fetch(
                `${this.baseUrl}/report?days=${days}&format=${format}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = `geo_report_${days}days.${format === 'json' ? 'json' : 'md'}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            window.URL.revokeObjectURL(url);
            
            console.log('✅ Rapport téléchargé');

        } catch (error) {
            console.error('❌ Erreur téléchargement:', error);
            throw error;
        }
    }

    // =========================================================================
    // STATISTIQUES
    // =========================================================================

    /**
     * Récupère les statistiques sur les patterns
     * @param {number} days - Nombre de jours
     * @returns {Promise<Object>} Statistiques
     */
    async getPatternStatistics(days = 7) {
        try {
            const response = await fetch(
                `${this.baseUrl}/stats/patterns?days=${days}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data.stats;

        } catch (error) {
            console.error('❌ Erreur statistiques patterns:', error);
            throw error;
        }
    }

    /**
     * Récupère les statistiques sur les entités
     * @param {number} days - Nombre de jours
     * @returns {Promise<Object>} Statistiques
     */
    async getEntityStatistics(days = 7) {
        try {
            const response = await fetch(
                `${this.baseUrl}/stats/entities?days=${days}`
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            return data.stats;

        } catch (error) {
            console.error('❌ Erreur statistiques entités:', error);
            throw error;
        }
    }

    // =========================================================================
    // GESTION DU CACHE
    // =========================================================================

    _isCacheValid(key) {
        if (!this.cache.has(key)) return false;
        
        const cached = this.cache.get(key);
        const now = Date.now();
        
        return (now - cached.timestamp) < this.cacheDuration;
    }

    _setCache(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }

    clearCache() {
        this.cache.clear();
        console.log('🗑️ Cache vidé');
    }

    // =========================================================================
    // HEALTH CHECK
    // =========================================================================

    async checkHealth() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            const data = await response.json();
            
            console.log('🏥 Santé du service:', data);
            return data;

        } catch (error) {
            console.error('❌ Service non disponible:', error);
            return { status: 'error', error: error.message };
        }
    }
}

// =========================================================================
// EXEMPLES D'UTILISATION
// =========================================================================

/**
 * Exemple 1 : Afficher les patterns enrichis
 */
async function exampleDisplayEnrichedPatterns() {
    const manager = new GeoEntityManager();
    
    try {
        const data = await manager.getPatternsEnriched(7, 2);
        
        console.log(`\n📊 ${data.count} PATTERNS ENRICHIS\n`);
        
        data.patterns.forEach((pattern, index) => {
            console.log(`${index + 1}. "${pattern.pattern}"`);
            console.log(`   Pays: ${pattern.countries.join(', ')}`);
            console.log(`   Entités richesse: ${pattern.entity_richness_score}`);
            
            // Afficher les entités
            const entities = pattern.entities;
            if (entities.locations?.length) {
                const locs = entities.locations.map(e => e.text).join(', ');
                console.log(`   📍 Lieux: ${locs}`);
            }
            if (entities.organizations?.length) {
                const orgs = entities.organizations.map(e => e.text).join(', ');
                console.log(`   🏛️ Organisations: ${orgs}`);
            }
            console.log('');
        });
        
    } catch (error) {
        console.error('Erreur:', error);
    }
}

/**
 * Exemple 2 : Rechercher une entité spécifique
 */
async function exampleSearchEntity(entityName) {
    const manager = new GeoEntityManager();
    
    try {
        const data = await manager.findPatternsByEntity(entityName);
        
        console.log(`\n🔍 PATTERNS MENTIONNANT "${entityName}"\n`);
        
        if (data.count === 0) {
            console.log('Aucun pattern trouvé.');
            return;
        }
        
        data.patterns.forEach((pattern, index) => {
            console.log(`${index + 1}. "${pattern.pattern}"`);
            console.log(`   Pays: ${pattern.countries.join(', ')}`);
            console.log(`   Occurrences: ${pattern.total_occurrences}`);
        });
        
    } catch (error) {
        console.error('Erreur:', error);
    }
}

/**
 * Exemple 3 : Visualiser le graphe de relations
 */
async function exampleVisualizeRelations() {
    const manager = new GeoEntityManager();
    
    try {
        const data = await manager.getEntityRelations(7);
        const graph = data.graph;
        
        console.log('\n🕸️ GRAPHE DE RELATIONS\n');
        console.log(`Nœuds: ${graph.metadata.total_nodes}`);
        console.log(`Liens: ${graph.metadata.total_edges}`);
        
        console.log('\nTop 10 relations:');
        graph.edges.slice(0, 10).forEach((edge, index) => {
            console.log(`${index + 1}. ${edge.source} ←→ ${edge.target} (${edge.weight} co-occurrences)`);
        });
        
        // Ici vous pouvez utiliser vis.js ou D3.js pour visualiser
        // visualizeGraphWithVisJS(graph);
        
    } catch (error) {
        console.error('Erreur:', error);
    }
}

/**
 * Exemple 4 : Intégration avec Leaflet (carte interactive)
 */
async function exampleIntegrateWithLeaflet() {
    const manager = new GeoEntityManager();
    
    try {
        const data = await manager.getPatternsEnriched(7, 2);
        
        // Extraire les lieux pour les placer sur la carte
        const locations = new Set();
        
        data.patterns.forEach(pattern => {
            const entities = pattern.entities;
            if (entities.locations) {
                entities.locations.forEach(loc => {
                    locations.add(loc.text);
                });
            }
        });
        
        console.log('📍 Lieux à afficher sur la carte:');
        locations.forEach(loc => console.log(`  • ${loc}`));
        
        // Ici vous pouvez ajouter des marqueurs sur votre carte Leaflet
        // addMarkersToMap(Array.from(locations));
        
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// =========================================================================
// EXPORT
// =========================================================================

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GeoEntityManager;
}

// Export global pour utilisation dans le navigateur
if (typeof window !== 'undefined') {
    window.GeoEntityManager = GeoEntityManager;
}

// =========================================================================
// UTILISATION DANS UNE PAGE HTML
// =========================================================================

/*
<!DOCTYPE html>
<html>
<head>
    <title>Geo-Entity Manager</title>
    <script src="/static/js/entity-manager-enhanced.js"></script>
</head>
<body>
    <button onclick="loadPatterns()">Charger Patterns</button>
    <button onclick="searchEntity()">Chercher Entité</button>
    <div id="results"></div>

    <script>
        const manager = new GeoEntityManager();

        async function loadPatterns() {
            const data = await manager.getPatternsEnriched(7, 2);
            
            const results = document.getElementById('results');
            results.innerHTML = '<h2>Patterns Enrichis</h2>';
            
            data.patterns.forEach(pattern => {
                results.innerHTML += `
                    <div class="pattern">
                        <h3>${pattern.pattern}</h3>
                        <p>Pays: ${pattern.countries.join(', ')}</p>
                        <p>Entités: ${pattern.entity_richness_score}</p>
                    </div>
                `;
            });
        }

        async function searchEntity() {
            const entityName = prompt('Nom de l\'entité:');
            if (!entityName) return;
            
            const data = await manager.findPatternsByEntity(entityName);
            
            const results = document.getElementById('results');
            results.innerHTML = `<h2>Patterns pour "${entityName}"</h2>`;
            
            if (data.count === 0) {
                results.innerHTML += '<p>Aucun pattern trouvé.</p>';
                return;
            }
            
            data.patterns.forEach(pattern => {
                results.innerHTML += `
                    <div class="pattern">
                        <h3>${pattern.pattern}</h3>
                        <p>Pays: ${pattern.countries.join(', ')}</p>
                    </div>
                `;
            });
        }
    </script>
</body>
</html>
*/
