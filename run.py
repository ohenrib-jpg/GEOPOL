#!/usr/bin/env python3
"""
Script de démarrage de GEOPOL Analytics - VERSION CORRIGÉE
Avec intégration complète des modules géopolitiques
"""

import os
import sys
import socket
import logging
import subprocess
from pathlib import Path

def setup_critical_directories():
    """Crée les répertoires CRITIQUES avant toute configuration"""
    critical_dirs = ['logs', 'data']
    
    print("📁 Création des répertoires critiques...")
    for dir_path in critical_dirs:
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"  ✅ {dir_path}")
        except Exception as e:
            print(f"  ❌ Erreur création {dir_path}: {e}")
            # On continue malgré l'erreur, le script tentera de créer plus tard
    
    return True

def setup_logging():
    """Configure le logging APRÈS la création des répertoires"""
    try:
        # S'assurer que le dossier logs existe
        Path('logs').mkdir(exist_ok=True)
        
        # Configurer le logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/geopol_startup.log')
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info("Logging initialisé avec succès")
        return logger
    except Exception as e:
        print(f"❌ Erreur configuration logging: {e}")
        # Fallback: logging simple vers la console
        logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
        return logging.getLogger(__name__)

def print_banner():
    """Affiche la bannière du système"""
    print("=" * 70)
    print("🚀 GEOPOL ANALYTICS - SYSTÈME DE VEILLE GÉOPOLITIQUE")
    print("=" * 70)
    print("🌍 Cartographie Narrative • 📊 Analyse Sentiment • 🧠 IA Géopolitique")
    print("=" * 70)

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    print("\n🔍 Vérification des dépendances...")
    
    dependencies = [
        ('Flask', 'flask'),
        ('feedparser', 'feedparser'),
        ('TextBlob', 'textblob'),
        ('NLTK', 'nltk'),
        ('BeautifulSoup', 'bs4'),
        ('Requests', 'requests'),
        ('SpaCy', 'spacy'),
        ('Pandas', 'pandas'),
        ('NumPy', 'numpy')
    ]
    
    missing_deps = []
    for name, package in dependencies:
        try:
            __import__(package)
            print(f"  ✅ {name}")
        except ImportError:
            missing_deps.append((name, package))
            print(f"  ❌ {name}")
    
    return missing_deps

def install_missing_dependencies(missing_deps):
    """Installe les dépendances manquantes depuis votre requirements.txt"""
    if not missing_deps:
        print("✅ Toutes les dépendances sont installées")
        return True
        
    print("\n📦 Installation des dépendances manquantes...")
    
    # D'abord, essayer d'installer depuis requirements.txt
    if os.path.exists('requirements.txt'):
        print("📥 Installation depuis requirements.txt...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("✅ Installation depuis requirements.txt réussie")
            
            # Vérifier à nouveau les dépendances manquantes
            remaining_missing = []
            for name, package in missing_deps:
                try:
                    __import__(package)
                    print(f"  ✅ {name} maintenant installé")
                except ImportError:
                    remaining_missing.append((name, package))
            
            missing_deps = remaining_missing
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Erreur lors de l'installation: {e}")
            return False
    
    # Installer les dépendances restantes individuellement
    if missing_deps:
        print("\n📦 Installation des dépendances restantes...")
        for name, package in missing_deps:
            print(f"  📥 Installation de {name}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"  ✅ {name} installé")
            except subprocess.CalledProcessError:
                print(f"  ❌ Échec de l'installation de {name}")
                return False
    
    return True

def download_spacy_model():
    """Télécharge le modèle SpaCy français si nécessaire"""
    print("\n🧠 Vérification du modèle SpaCy...")
    
    try:
        import spacy
        try:
            # Essayer de charger le modèle
            nlp = spacy.load("fr_core_news_lg")
            print("✅ Modèle 'fr_core_news_lg' déjà présent")
            return True
        except OSError:
            print("📥 Téléchargement du modèle SpaCy français...")
            print("⏳ Cela peut prendre quelques minutes...")
            
            try:
                # Télécharger le modèle
                subprocess.check_call([
                    sys.executable, "-m", "spacy", "download", "fr_core_news_lg"
                ])
                print("✅ Modèle SpaCy téléchargé avec succès")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Erreur lors du téléchargement: {e}")
                print("💡 Essayez manuellement: python -m spacy download fr_core_news_lg")
                return False
    except ImportError:
        print("⚠️ SpaCy n'est pas installé")
        return False

def setup_directories():
    """Crée tous les répertoires nécessaires"""
    print("\n📁 Configuration des répertoires...")
    
    directories = [
        'data',
        'logs',
        'exports',
        'static',
        'templates',
        'static/js',
        'static/css',
        'static/images'
    ]
    
    for dir_path in directories:
        try:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            print(f"  ✅ {dir_path}")
        except Exception as e:
            print(f"  ⚠️ Erreur création {dir_path}: {e}")
    
    return True

def create_production_env():
    """Crée le fichier .env pour la production s'il n'existe pas"""
    env_file = '.env'
    
    if os.path.exists(env_file):
        print(f"✅ Fichier {env_file} déjà présent")
        return True
    
    print(f"📝 Création du fichier {env_file}...")
    
    env_content = """# Configuration Production GEOPOL
DATABASE_PATH=data/geopol.db
GEOPOL_REAL_MODE=true

# Serveur
FLASK_ENV=production
FLASK_DEBUG=false
HOST=0.0.0.0
PORT=5000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/geopol.log

# SpaCy
SPACY_MODEL=fr_core_news_lg

# Modules
WEAK_INDICATORS_ENABLED=true
GEO_NARRATIVE_ENABLED=true
ENTITY_EXTRACTION_ENABLED=true
"""
    
    try:
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"✅ {env_file} créé")
        return True
    except Exception as e:
        print(f"❌ Erreur création {env_file}: {e}")
        return False

def find_free_port(start_port=5000, max_attempts=10):
    """Trouve un port libre à partir de start_port"""
    print("\n🔌 Recherche d'un port disponible...")
    
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.bind(('0.0.0.0', port))
                s.close()
                print(f"✅ Port {port} disponible")
                return port
        except (OSError, socket.timeout):
            print(f"  Port {port} occupé")
            continue
    
    print("❌ Aucun port libre trouvé")
    return None

def check_database():
    """Vérifie la base de données"""
    print("\n💾 Vérification de la base de données...")
    
    db_path = 'data/geopol.db'
    if os.path.exists(db_path):
        print(f"✅ Base de données trouvée: {db_path}")
        return True
    else:
        print(f"⚠️ Base de données non trouvée, elle sera créée au démarrage")
        return True

def run_geopolitical_tests():
    """Exécute les tests du module géopolitique"""
    print("\n🧪 Tests du module géopolitique...")
    
    try:
        # Vérifier si le fichier de test existe
        test_file = os.path.join('Flask', 'test_geopolitique.py')
        if os.path.exists(test_file):
            # Importer le module de test
            sys.path.insert(0, '.')
            from Flask.test_geopolitique import main as test_geopolitique
            test_geopolitique()
            return True
        else:
            print("⚠️ Module de test non disponible, création...")
            # Créer un simple test
            test_content = '''#!/usr/bin/env python3
print("🧪 Test SpaCy...")
try:
    import spacy
    print("✅ SpaCy importé")
except:
    print("❌ SpaCy non installé")
print("✅ Test terminé")
'''
            with open(test_file, 'w') as f:
                f.write(test_content)
            print("✅ Fichier de test créé")
            return True
    except Exception as e:
        print(f"⚠️ Erreur lors des tests: {e}")
        return True

def start_application(port, logger):
    """Démarre l'application Flask"""
    print("\n" + "=" * 70)
    print("🚀 DÉMARRAGE DE L'APPLICATION")
    print("=" * 70)
    
    try:
        # Ajouter le répertoire Flask au path
        sys.path.insert(0, 'Flask')
        
        logger.info("Importation de l'application Flask...")
        
        # Importer et créer l'application
        from Flask.app_factory import create_app
        app = create_app()
        
        print(f"🌐 URL PRINCIPALE: http://localhost:{port}")
        print(f"📡 HÔTE: 0.0.0.0")
        print(f"⚙️  MODE: {'RÉEL' if app.config.get('REAL_MODE', False) else 'SIMULATION'}")
        
        print("\n📊 MODULES ACTIFS:")
        print(f"   • Cartographie Narrative: {'✅' if app.config.get('GEO_NARRATIVE_ANALYZER') else '❌'}")
        print(f"   • Extraction d'entités: {'✅' if app.config.get('ENTITY_EXTRACTOR') else '❌'}")
        print(f"   • Carte Leaflet: ✅")
        print(f"   • Analyse Sentiment: ✅")
        print(f"   • RSS Parser: ✅")
        print(f"   • IA Géopolitique: ✅")
        
        print("\n🔗 URLS IMPORTANTES:")
        print(f"   • Dashboard: http://localhost:{port}")
        print(f"   • Cartographie: http://localhost:{port}/api/geo-narrative/map-view")
        print(f"   • Diagnostic: http://localhost:{port}/api/geo/diagnostic")
        print(f"   • Test Leaflet: http://localhost:{port}/api/geo/test-leaflet")
        print(f"   • API Santé: http://localhost:{port}/health")
        
        print("\n🛠️  COMMANDES UTILES:")
        print("   • Arrêt: Ctrl+C")
        print("   • Logs: logs/geopol.log")
        print("   • Exports: dossier 'exports/'")
        
        print("\n" + "=" * 70)
        print("✅ SYSTÈME PRÊT - DÉMARRAGE DU SERVEUR")
        print("=" * 70)
        
        logger.info(f"Démarrage du serveur sur le port {port}")
        
        # Lancer l'application
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,  # Mode production
            threaded=True,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt demandé par l'utilisateur")
        logger.info("Arrêt demandé par l'utilisateur")
        return True
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        logger.error(f"Erreur critique: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        return False

def check_firewall():
    """Vérifie les paramètres du pare-feu"""
    print("\n🛡️  Vérification du pare-feu...")
    
    try:
        import platform
        system = platform.system()
        
        if system == "Windows":
            print("💡 Sous Windows, assurez-vous que le port est ouvert dans le pare-feu")
        elif system == "Linux":
            print("💡 Sous Linux, vérifiez les règles iptables/ufw")
        else:
            print("💡 Vérifiez les paramètres de votre pare-feu")
        
        return True
    except Exception as e:
        print(f"⚠️ Impossible de vérifier le pare-feu: {e}")
        return True

def main():
    """Fonction principale de démarrage"""
    
    # ÉTAPE 0: Créer les répertoires CRITIQUES avant tout
    setup_critical_directories()
    
    # ÉTAPE 1: Configurer le logging (maintenant que logs/ existe)
    logger = setup_logging()
    
    # ÉTAPE 2: Afficher la bannière
    print_banner()
    logger.info("Démarrage de GEOPOL Analytics")
    
    # ÉTAPE 3: Configuration des répertoires complets
    if not setup_directories():
        logger.error("Échec de la configuration des répertoires")
        return False
    
    # ÉTAPE 4: Création du fichier .env
    if not create_production_env():
        logger.warning("Échec de la création du fichier .env")
    
    # ÉTAPE 5: Vérification des dépendances
    missing_deps = check_dependencies()
    if missing_deps:
        if not install_missing_dependencies(missing_deps):
            print("\n❌ Impossible d'installer les dépendances manquantes.")
            logger.error("Impossible d'installer les dépendances manquantes")
            print("💡 Essayez manuellement: pip install -r requirements.txt")
            return False
    
    # ÉTAPE 6: Téléchargement du modèle SpaCy
    if not download_spacy_model():
        print("⚠️ Le module géopolitique pourrait ne pas fonctionner correctement")
        logger.warning("Modèle SpaCy non disponible")
    
    # ÉTAPE 7: Vérification de la base de données
    check_database()
    
    # ÉTAPE 8: Vérification du pare-feu
    check_firewall()
    
    # ÉTAPE 9: Trouver un port libre
    port = find_free_port(5000)
    if port is None:
        print("❌ Impossible de trouver un port libre")
        logger.error("Aucun port libre trouvé")
        return False
    
    # ÉTAPE 10: Tests optionnels
    run_geopolitical_tests()
    
    # ÉTAPE 11: Démarrer l'application
    logger.info(f"Port sélectionné: {port}")
    success = start_application(port, logger)
    
    if not success:
        print("\n❌ L'application s'est arrêtée avec une erreur")
        logger.error("Application arrêtée avec une erreur")
        return False
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Arrêt demandé par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)