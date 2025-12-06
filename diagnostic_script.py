#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnostic pour identifier les erreurs de syntaxe
Utilisez : python test_syntax.py
"""

import sys
import ast
import os

def check_file_syntax(filepath):
    """Vérifie la syntaxe d'un fichier Python"""
    print(f"\n{'='*60}")
    print(f"🔍 Vérification de: {filepath}")
    print(f"{'='*60}")
    
    if not os.path.exists(filepath):
        print(f"❌ Fichier non trouvé: {filepath}")
        return False
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Essayer de parser le fichier
        ast.parse(content)
        print(f"✅ Syntaxe correcte!")
        return True
        
    except SyntaxError as e:
        print(f"❌ ERREUR DE SYNTAXE:")
        print(f"   Ligne {e.lineno}: {e.msg}")
        print(f"   Texte: {e.text}")
        print(f"   Position: {' ' * (e.offset - 1)}^")
        return False
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return False

def check_indentation(filepath):
    """Vérifie spécifiquement les problèmes d'indentation"""
    print(f"\n🔎 Analyse détaillée de l'indentation...")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        issues = []
        for i, line in enumerate(lines, 1):
            # Vérifier les tabulations mélangées avec des espaces
            if '\t' in line and ' ' * 4 in line:
                issues.append((i, "⚠️  Mélange tabulations/espaces"))
            
            # Vérifier les lignes avec indentation impaire
            stripped = line.lstrip()
            if stripped and not line.startswith('#'):
                indent = len(line) - len(stripped)
                if indent % 4 != 0:
                    issues.append((i, f"⚠️  Indentation {indent} espaces (pas multiple de 4)"))
        
        if issues:
            print(f"   Problèmes potentiels trouvés:")
            for line_num, issue in issues[:10]:  # Afficher max 10 problèmes
                print(f"   Ligne {line_num}: {issue}")
        else:
            print(f"   ✅ Aucun problème d'indentation détecté")
            
        return len(issues) == 0
        
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification: {e}")
        return False

def main():
    """Point d'entrée principal"""
    print("="*60)
    print("🔧 DIAGNOSTIC SYNTAXE GEOPOL")
    print("="*60)
    
    files_to_check = [
        'Flask/app_factory.py',
        'Flask/routes.py',
    ]
    
    all_ok = True
    
    for filepath in files_to_check:
        syntax_ok = check_file_syntax(filepath)
        indent_ok = check_indentation(filepath)
        
        if not (syntax_ok and indent_ok):
            all_ok = False
    
    print("\n" + "="*60)
    if all_ok:
        print("✅ TOUS LES FICHIERS SONT CORRECTS")
        print("   Si Flask ne démarre toujours pas, vérifiez:")
        print("   1. Les imports (psutil, threading, signal)")
        print("   2. Les logs de Flask au démarrage")
        print("   3. Le port 5000 est libre")
    else:
        print("❌ DES ERREURS ONT ÉTÉ DÉTECTÉES")
        print("   Corrigez les erreurs ci-dessus et relancez ce script")
    print("="*60)
    
    return 0 if all_ok else 1

if __name__ == '__main__':
    sys.exit(main())