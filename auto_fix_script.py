#!/usr/bin/env python3
"""
Script pour corriger automatiquement routes.py
"""

import os
import shutil
from datetime import datetime

def backup_file(filepath):
    """Crée une sauvegarde du fichier"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        print(f"✅ Sauvegarde créée: {backup_path}")
        return backup_path
    return None

def fix_routes_indentation():
    """Corrige l'indentation dans routes.py"""
    
    routes_path = 'Flask/routes.py'
    
    if not os.path.exists(routes_path):
        print(f"❌ Fichier introuvable: {routes_path}")
        return False
    
    # Créer une sauvegarde
    backup_file(routes_path)
    
    print("🔧 Lecture de routes.py...")
    with open(routes_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Identifier la ligne problématique (autour de 280)
    fixed_lines = []
    in_get_stats = False
    get_stats_indent = 0
    
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        
        # Détecter la fonction get_stats
        if 'def get_stats():' in line:
            in_get_stats = True
            get_stats_indent = current_indent
            print(f"📍 Fonction get_stats() trouvée à la ligne {i+1}")
        
        # Sortir de get_stats si une nouvelle fonction commence
        elif in_get_stats and stripped.startswith('def ') and current_indent == get_stats_indent:
            in_get_stats = False
        
        # Corriger les lignes dans get_stats qui ont une indentation incorrecte
        if in_get_stats:
            # Si c'est un except/finally au niveau de la fonction (mauvaise indentation)
            if stripped.startswith(('except ', 'finally:')) and current_indent <= get_stats_indent:
                # Ajouter 4 espaces d'indentation
                line = '    ' + line
                print(f"🔧 Correction ligne {i+1}: ajout d'indentation pour {stripped[:20]}...")
        
        fixed_lines.append(line)
    
    # Écrire le fichier corrigé
    print("💾 Écriture du fichier corrigé...")
    with open(routes_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print("✅ Fichier routes.py corrigé !")
    return True

def main():
    print("=" * 60)
    print("🛠️  CORRECTION AUTOMATIQUE DE ROUTES.PY")
    print("=" * 60)
    print()
    
    if fix_routes_indentation():
        print("\n✅ Correction terminée avec succès !")
        print("💡 Relancez l'application: python run.py")
    else:
        print("\n❌ Correction échouée")
        print("💡 Utilisez le fichier artifact 'routes_complete_fixed'")

if __name__ == "__main__":
    main()
