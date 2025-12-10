# install_python312.py
import subprocess
import sys

def run_cmd(cmd, desc=""):
    """Exécute une commande avec gestion d'erreur améliorée"""
    print(f"🔧 {desc}" if desc else f"🔧 {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print("✅ Succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Échec")
        if "error" in e.stderr.lower():
            print(f"   Message: {e.stderr.strip()}")
        return False

print("🚀 Installation optimisée pour Python 3.12...")

# Étape 1: Nettoyage des versions problématiques
print("\n🧹 Nettoyage des versions problématiques...")
problematic_packages = ["aiohttp"]
for pkg in problematic_packages:
    run_cmd(f"pip uninstall {pkg} -y", f"Nettoyage de {pkg}")

# Étape 2: Packages de base
print("\n📦 Installation des packages de base...")
base_packages = [
    "Flask==3.0.0", "Werkzeug==3.0.1", "Jinja2==3.1.2", "click==8.1.7",
    "requests==2.31.0", "feedparser==6.0.10", "beautifulsoup4==4.12.2", 
    "lxml==4.9.3", "urllib3==2.0.7", "pandas==2.1.4", "yfinance==0.2.18",
    "python-dateutil==2.8.2", "Pillow==10.0.1", "html5lib==1.1", "tzdata==2023.3"
]

for pkg in base_packages:
    run_cmd(f"pip install {pkg}", f"Installation de {pkg}")

# Étape 3: Packages async compatibles
print("\n📦 Installation des packages async...")
async_packages = [
    "aiohttp==3.9.0",
    "websockets==13.0"
]

for pkg in async_packages:
    run_cmd(f"pip install {pkg}", f"Installation de {pkg}")

# Étape 4: Packages scientifiques (pré-compilés)
print("\n📦 Installation des packages scientifiques...")
scientific_packages = [
    "numpy==1.26.0", 
    "scipy==1.11.4", 
    "scikit-learn==1.5.2"
]

for pkg in scientific_packages:
    run_cmd(f"pip install {pkg} --only-binary=all", f"Installation de {pkg}")

# Étape 5: PyTorch
print("\n📦 Installation PyTorch...")
run_cmd(
    "pip install torch==2.9.1+cpu --index-url https://download.pytorch.org/whl/cpu",
    "Installation de PyTorch 2.9.1 (CPU)"
)

# Étape 6: NLP
print("\n📦 Installation NLP...")
nlp_packages = [
    "sentencepiece==0.1.99",
    "protobuf==4.25.1", 
    "transformers==4.35.2",
    "sentence-transformers==2.2.2"
]

for pkg in nlp_packages:
    run_cmd(f"pip install {pkg}", f"Installation de {pkg}")

print("\n🎉 Installation terminée!")