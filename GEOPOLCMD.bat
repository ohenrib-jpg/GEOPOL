@echo off
REM ====================================
REM Script de démarrage GEOPOL + Llama
REM ====================================

title GEOPOL - Lancement

echo ========================================
echo    GEOPOL v2.1 - Demarrage
echo ========================================
echo.

REM Configuration
set LLAMA_DIR=llama.cpp
set SERVER_EXE=llama-server.exe
set MODEL_FILE=mistral-7b-v0.2-q4_0.gguf
set LLAMA_PORT=8080
set FLASK_PORT=5000
set GEOPOL_URL=http://localhost:%FLASK_PORT%

echo [1/3] Verification de l'environnement...
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)
echo   [OK] Python detecte

REM Vérifier si le serveur Llama existe
if not exist "%LLAMA_DIR%\%SERVER_EXE%" (
    echo [ERREUR] Serveur Llama introuvable: %LLAMA_DIR%\%SERVER_EXE%
    pause
    exit /b 1
)
echo   [OK] Llama.cpp trouve

REM Vérifier si le modèle existe
if not exist "%LLAMA_DIR%\models\%MODEL_FILE%" (
    echo [ERREUR] Modele introuvable: %LLAMA_DIR%\models\%MODEL_FILE%
    pause
    exit /b 1
)
echo   [OK] Modele Llama 3.2 trouve

echo.
echo [2/3] Demarrage du serveur IA Llama...
echo.

REM Démarrer le serveur Llama dans une nouvelle fenêtre
start "Serveur IA Llama 3.2" /D "%LLAMA_DIR%" cmd /k "%SERVER_EXE% -m models\%MODEL_FILE% -c 2048 -b 256 -t 6 --host 0.0.0.0 --port %LLAMA_PORT% --ctx-size 2048"

echo   [OK] Serveur IA demarre sur http://localhost:%LLAMA_PORT%
echo   Patientez 10 secondes pour l'initialisation...
timeout /t 10 /nobreak >nul

echo.
echo [3/3] Demarrage de l'application GEOPOL...
echo.# Exécution des tests

REM Démarrer l'application Flask
start "GEOPOL Flask" cmd /k ".venv\Scripts\activate.bat && python run.py

echo   [OK] Application GEOPOL demarree sur http://localhost:%FLASK_PORT%

echo.
echo ========================================
echo    GEOPOL est pret !
echo ========================================
echo.
echo  Interface Web : http://localhost:%FLASK_PORT%
echo  Serveur IA    : http://localhost:%LLAMA_PORT%
echo.
echo  Fermez cette fenetre pour tout arreter
echo.
pause