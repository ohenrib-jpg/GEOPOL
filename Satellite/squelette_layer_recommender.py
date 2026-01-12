"""
Système de recommandation de couches
TODO: Logique ML basique basée sur région/usage
"""
class LayerRecommender:
    def __init__(self):
        self.rules = self._load_recommendation_rules()
    
    def recommend(self, bbox, purpose, constraints=None):
        """
        TODO: 
        1. Analyser caractéristiques région
        2. Appliquer règles de recommandation
        3. Retourner top 3 couches avec scores
        """
        pass
    
    def _load_recommendation_rules(self):
        """Règles prédéfinies par usage"""
        return {
            'vegetation': ['s2cloudless', 'ndvi'],
            'urban': ['landsat', 'osm'],
            'water': ['sentinel1', 'ndwi'],
            # À compléter...
        }