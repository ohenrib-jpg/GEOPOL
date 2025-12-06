# Flask/restore_default_themes.py
import sqlite3
import json

def restore_default_themes():
    """Restaure les thèmes par défaut"""
    try:
        conn = sqlite3.connect('instance/geopol.db')
        cursor = conn.cursor()
        
        # Thèmes par défaut
        default_themes = [
            {
                'id': 'geopolitique',
                'name': 'Géopolitique',
                'keywords': ['politique', 'international', 'diplomatie', 'conflit', 'guerre', 'paix', 'relations'],
                'color': '#FF6B6B',
                'description': 'Relations internationales et conflits'
            },
            {
                'id': 'economie', 
                'name': 'Économie',
                'keywords': ['économie', 'finance', 'marché', 'investissement', 'croissance', 'crise', 'banque'],
                'color': '#4ECDC4',
                'description': 'Économie et finances'
            },
            {
                'id': 'technologie',
                'name': 'Technologie', 
                'keywords': ['technologie', 'innovation', 'digital', 'IA', 'robot', 'internet', 'données'],
                'color': '#45B7D1',
                'description': 'Innovations technologiques'
            },
            {
                'id': 'environnement',
                'name': 'Environnement',
                'keywords': ['environnement', 'climat', 'écologie', 'pollution', 'énergie', 'durable', 'biodiversité'],
                'color': '#96CEB4',
                'description': 'Enjeux environnementaux'
            },
            {
                'id': 'sante',
                'name': 'Santé',
                'keywords': ['santé', 'médecine', 'hôpital', 'vaccin', 'maladie', 'recherche', 'traitement'],
                'color': '#FFEAA7',
                'description': 'Santé et médecine'
            },
            {
                'id': 'culture',
                'name': 'Culture',
                'keywords': ['culture', 'art', 'musique', 'cinéma', 'littérature', 'éducation', 'patrimoine'],
                'color': '#DDA0DD',
                'description': 'Culture et arts'
            },
            {
                'id': 'sports',
                'name': 'Sports', 
                'keywords': ['sport', 'football', 'jeux', 'compétition', 'athlète', 'championnat', 'olympique'],
                'color': '#98D8C8',
                'description': 'Sports et compétitions'
            }
        ]
        
        # Vider la table
        cursor.execute("DELETE FROM themes")
        cursor.execute("DELETE FROM theme_analyses")
        
        # Insérer les thèmes par défaut
        for theme in default_themes:
            cursor.execute("""
                INSERT INTO themes (id, name, keywords, color, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                theme['id'],
                theme['name'],
                json.dumps(theme['keywords'], ensure_ascii=False),
                theme['color'],
                theme['description']
            ))
            print(f"✅ Thème créé: {theme['name']}")
        
        conn.commit()
        
        # Vérifier
        cursor.execute("SELECT COUNT(*) FROM themes")
        count = cursor.fetchone()[0]
        print(f"🎉 {count} thèmes par défaut restaurés!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    restore_default_themes()