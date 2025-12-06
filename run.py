#!/usr/bin/env python3
"""
Script de démarrage de l'Analyseur RSS avec détection automatique de port
"""

import os
import sys
import socket
import logging

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(__file__))

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    dependencies = [
        ('Flask', 'flask'),
        ('feedparser', 'feedparser'),
        ('TextBlob', 'textblob'),
        ('NLTK', 'nltk'),
        ('BeautifulSoup', 'bs4'),
        ('Requests', 'requests')
    ]
    
    missing_deps = []
    for name, package in dependencies:
        try:
            __import__(package)
            print(f"✅ {name}")
        except ImportError:
            missing_deps.append((name, package))
            print(f"❌ {name}")
    
    return missing_deps

def install_missing_dependencies(missing_deps):
    """Installe les dépendances manquantes"""
    if not missing_deps:
        return True
        
    print("\n📦 Installation des dépendances manquantes...")
    for name, package in missing_deps:
        print(f"Installation de {name}...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {name} installé avec succès")
        except subprocess.CalledProcessError:
            print(f"❌ Échec de l'installation de {name}")
            return False
    
    return True

def find_free_port(start_port=5000, max_attempts=10):
    """Trouve un port libre à partir de start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            continue
    
    return None

def main():
    """Fonction principale de démarrage"""
    print("=" * 50)
    print("🚀 Démarrage de l'Analyseur RSS Intelligent")
    print("=" * 50)
    
    # Vérification des dépendances
    print("🔍 Vérification des dépendances...")
    missing_deps = check_dependencies()
    
    if missing_deps:
        if not install_missing_dependencies(missing_deps):
            print("\n❌ Impossible d'installer les dépendances manquantes.")
            print("💡 Essayez d'installer manuellement: pip install -r requirements.txt")
            return
    
    # Recherche d'un port libre
    print("\n🔌 Recherche d'un port disponible...")
    port = find_free_port(5000)
    
    if port is None:
        print("❌ Impossible de trouver un port libre entre 5000 et 5009")
        print("💡 Fermez d'autres applications et réessayez")
        return
    
    # Démarrage de l'application
    print(f"\n🌐 Application disponible sur: http://localhost:{port}")
    print("📊 Base de données: rss_analyzer.db")
    print("🛑 Pour arrêter: Ctrl+C")
    print("-" * 50)
    
    try:
        from Flask.app_factory import create_app
        app = create_app()
        app.run(debug=True, host='0.0.0.0', port=port)
    except Exception as e:
        print(f"\n❌ Erreur au démarrage: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()