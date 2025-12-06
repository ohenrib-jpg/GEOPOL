# Flask/debug_themes_check.py
"""
Script de diagnostic pour vérifier la structure des thèmes
Exécutez ce script pour voir ce que retourne votre API themes
"""

import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_themes_structure(db_path='instance/geopol.db'):
    """Vérifie la structure de la table themes"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier la structure de la table
        print("\n" + "="*60)
        print("STRUCTURE DE LA TABLE 'themes'")
        print("="*60)
        cursor.execute("PRAGMA table_info(themes)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]:<20} {col[2]:<15} {'NOT NULL' if col[3] else ''} {'PRIMARY KEY' if col[5] else ''}")
        
        # Récupérer tous les thèmes
        print("\n" + "="*60)
        print("CONTENU DE LA TABLE 'themes'")
        print("="*60)
        
        cursor.execute("SELECT * FROM themes")
        themes = cursor.fetchall()
        
        # Récupérer les noms de colonnes
        col_names = [description[0] for description in cursor.description]
        
        for i, theme in enumerate(themes, 1):
            print(f"\n--- THÈME {i} ---")
            for col_name, value in zip(col_names, theme):
                if col_name == 'keywords':
                    try:
                        keywords = json.loads(value) if value else []
                        print(f"  {col_name:<15}: {keywords[:3]}..." if len(keywords) > 3 else f"  {col_name:<15}: {keywords}")
                    except:
                        print(f"  {col_name:<15}: {value}")
                else:
                    print(f"  {col_name:<15}: {value}")
        
        # Vérifier les types de données dans la colonne 'id'
        print("\n" + "="*60)
        print("ANALYSE DES IDs")
        print("="*60)
        
        cursor.execute("SELECT id FROM themes")
        ids = cursor.fetchall()
        
        for theme_id in ids:
            id_value = theme_id[0]
            print(f"  ID: {id_value:<30} Type Python: {type(id_value).__name__:<15} Est numérique: {isinstance(id_value, (int, float))}")
        
        conn.close()
        
        print("\n" + "="*60)
        print("RECOMMANDATIONS")
        print("="*60)
        
        # Vérifier si les IDs sont numériques
        all_numeric = all(isinstance(theme_id[0], (int, float)) for theme_id in ids)
        
        if all_numeric:
            print("  ✅ Tous les IDs sont numériques - Configuration OK")
        else:
            print("  ⚠️  PROBLÈME DÉTECTÉ: Certains IDs ne sont pas numériques")
            print("  Solution 1: Recréer la table themes avec une colonne id INTEGER PRIMARY KEY")
            print("  Solution 2: Ajouter une colonne numeric_id INTEGER et l'utiliser pour l'API")
            
        return themes, col_names
        
    except sqlite3.Error as e:
        logger.error(f"❌ Erreur SQLite: {e}")
        return None, None
    except Exception as e:
        logger.error(f"❌ Erreur générale: {e}")
        return None, None

def suggest_fix(themes, col_names):
    """Suggère un correctif SQL si nécessaire"""
    if not themes or not col_names:
        return
    
    # Créer un mapping pour trouver l'index de la colonne 'id'
    try:
        id_index = col_names.index('id')
    except ValueError:
        print("\n⚠️  La colonne 'id' n'existe pas dans la table!")
        return
    
    # Vérifier si on a des IDs non-numériques
    non_numeric_ids = []
    for i, theme in enumerate(themes, 1):
        theme_id = theme[id_index]
        if not isinstance(theme_id, (int, float)):
            non_numeric_ids.append((i, theme_id))
    
    if non_numeric_ids:
        print("\n" + "="*60)
        print("SCRIPT SQL DE CORRECTION")
        print("="*60)
        print("""
-- Option 1: Ajouter une colonne numeric_id
ALTER TABLE themes ADD COLUMN numeric_id INTEGER;

-- Mettre à jour avec des IDs séquentiels
""")
        for i, (row_num, old_id) in enumerate(non_numeric_ids, 1):
            print(f"UPDATE themes SET numeric_id = {i} WHERE id = '{old_id}';")
        
        print("""
-- Créer un index sur la nouvelle colonne
CREATE INDEX IF NOT EXISTS idx_themes_numeric_id ON themes(numeric_id);
""")

if __name__ == '__main__':
    print("\n🔍 DIAGNOSTIC DE LA TABLE THEMES")
    print("="*60)
    
    themes, col_names = check_themes_structure()
    
    if themes:
        suggest_fix(themes, col_names)
        
        print("\n" + "="*60)
        print("Pour tester l'API, copiez ce JSON dans votre navigateur:")
        print("="*60)
        print("URL: http://localhost:5000/archiviste/api/themes")
        print("\nStructure attendue:")
        print(json.dumps({
            "success": True,
            "themes": [
                {
                    "id": 1,  # DOIT être un entier
                    "name": "Géopolitique",
                    "keywords": ["politique", "international"],
                    "description": "...",
                    "color": "#6366f1"
                }
            ]
        }, indent=2))
    
    print("\n✅ Diagnostic terminé!\n")
