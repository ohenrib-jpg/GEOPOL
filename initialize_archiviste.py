# Flask/initialize_archiviste.py
import logging
from .database import DatabaseManager
from .theme_manager import ThemeManager

logger = logging.getLogger(__name__)

def initialize_archiviste_themes(db_manager):
    """Initialise les thèmes pour l'Archiviste"""
    try:
        theme_manager = ThemeManager(db_manager)
        
        # Vérifier si des thèmes existent déjà
        existing_themes = theme_manager.get_all_themes()
        
        if existing_themes:
            logger.info(f"✅ {len(existing_themes)} thèmes existants trouvés")
            return True
        
        # Créer des thèmes de test s'il n'y en a pas
        sample_themes = [
            {
                'id': 'conflits-armes',
                'name': 'Conflits armés',
                'keywords': ['guerre', 'conflit', 'combat', 'bataille', 'armée', 'militaire', 'soldat', 'attaque', 'défense', 'otan'],
                'description': 'Conflits armés et opérations militaires',
                'color': '#ef4444'
            },
            {
                'id': 'diplomatie',
                'name': 'Diplomatie internationale', 
                'keywords': ['diplomatie', 'ambassade', 'traité', 'accord', 'négociation', 'sommet', 'relations internationales', 'onu'],
                'description': 'Relations diplomatiques et accords internationaux',
                'color': '#3b82f6'
            }
        ]
        
        created_count = 0
        for theme_data in sample_themes:
            success = theme_manager.create_theme(
                theme_id=theme_data['id'],
                name=theme_data['name'],
                keywords=theme_data['keywords'],
                color=theme_data['color'],
                description=theme_data['description']
            )
            if success:
                created_count += 1
        
        logger.info(f"✅ {created_count} thèmes de test créés pour l'Archiviste")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation thèmes Archiviste: {e}")
        return False