@echo off
echo 📦 Installation de GEOPOL Analytics...
echo ======================================

:: Créer l'environnement virtuel
python -m venv venv
call venv\Scripts\activate.bat

:: Mettre à jour pip
python -m pip install --upgrade pip

:: Installer les dépendances
echo 📥 Installation des dépendances...
pip install -r requirements.txt

:: Télécharger le modèle SpaCy
echo 🧠 Téléchargement du modèle SpaCy...
python -m spacy download fr_core_news_lg

:: Créer les répertoires
mkdir data 2>nul
mkdir logs 2>nul
mkdir exports 2>nul
mkdir static 2>nul
mkdir static\js 2>nul
mkdir static\css 2>nul
mkdir static\images 2>nul
mkdir templates 2>nul

echo ✅ Installation terminée !
echo 🚀 Pour démarrer : python run.py
pause