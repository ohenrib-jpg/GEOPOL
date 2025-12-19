import os
import secrets

# Chemins de base
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'rss_analyzer.db')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

# SÉCURITÉ: SECRET_KEY pour sessions et CSRF
# En production, définir FLASK_SECRET_KEY dans les variables d'environnement
# Génération automatique si non définie (à éviter en production)
SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
if not SECRET_KEY:
    # ATTENTION: Générer une nouvelle clé à chaque démarrage n'est pas recommandé en production
    # Les sessions seront invalidées à chaque redémarrage
    SECRET_KEY = secrets.token_hex(32)
    import warnings
    warnings.warn(
        "SECRET_KEY non définie dans les variables d'environnement. "
        "Définissez FLASK_SECRET_KEY pour la production.",
        RuntimeWarning
    )

# Configuration RSS
UPDATE_INTERVAL = 3600  # 1 heure en secondes
MAX_ARTICLES_PER_FEED = 50

# Configuration de l'analyse
SENTIMENT_THRESHOLD = 0.2
CONFIDENCE_THRESHOLD = 0.3

# Thèmes par défaut
DEFAULT_THEMES = {
    "technologie": {
        "keywords": ["ai", "intelligence artificielle", "chatgpt", "machine learning", "python", "programmation", "développement", "software", "hardware", "robot", "blockchain", "cloud", "cybersécurité"],
        "color": "#3B82F6"
    },
    "politique": {
        "keywords": ["gouvernement", "élection", "président", "ministre", "parlement", "loi", "réforme", "politique", "député", "sénateur", "vote", "assemblée"],
        "color": "#EF4444"
    },
    "économie": {
        "keywords": ["économie", "inflation", "croissance", "banque", "finance", "bourse", "investissement", "entreprise", "marché", "chômage", "emploi", "crise"],
        "color": "#10B981"
    },
    "santé": {
        "keywords": ["santé", "médecine", "hôpital", "vaccin", "maladie", "médecin", "patient", "recherche", "traitement", "épidémie", "virus", "médical"],
        "color": "#8B5CF6"
    },
    "environnement": {
        "keywords": ["environnement", "climat", "écologie", "réchauffement", "pollution", "énergie", "durable", "biodiversité", "transition", "carbone", "renouvelable"],
        "color": "#22C55E"
    }
}

# Archiviste v3 configuration
ARCHIVISTE_CONFIG = {
    'cache_ttl': 3600,  # 1 heure
    'max_cache_size': 100,
    'max_retries': 3,
    'deep_analysis': True,  # Active l'analyse linguistique
    'default_max_items': 50
}

