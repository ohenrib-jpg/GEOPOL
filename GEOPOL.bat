@echo off
REM ====================================
REM Script de démarrage GEOPOL + Mistral
REM Version discrète avec fenêtres minimisées
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

REM Vérifications
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)
echo   [OK] Python detecte

if not exist "%LLAMA_DIR%\%SERVER_EXE%" (
    echo [ERREUR] Serveur Llama introuvable: %LLAMA_DIR%\%SERVER_EXE%
    pause
    exit /b 1
)
echo   [OK] Llama.cpp trouve

if not exist "%LLAMA_DIR%\models\%MODEL_FILE%" (
    echo [ERREUR] Modele introuvable: %LLAMA_DIR%\models\%MODEL_FILE%
    pause
    exit /b 1
)
echo   [OK] Modele Mistral 7B trouve

echo.
echo [2/3] Demarrage du serveur IA Mistral 7B...
echo   (fenetre minimisee dans la barre des taches)
echo.

REM Démarrage du serveur IA en mode MINIMISÉ
start "Serveur IA - Mistral 7B" /MIN /D "%LLAMA_DIR%" cmd /c "%SERVER_EXE% -m models\%MODEL_FILE% --host 0.0.0.0 --port %LLAMA_PORT% --ctx-size 4096 --threads 10 --temp 0.1 --repeat-penalty 1.1"

echo   [OK] Serveur IA demarre (minimise)
echo.

REM Compte à rebours visuel
echo [Initialisation du modele IA...]
for /L %%i in (30,-1,1) do (
    <nul set /p="  Patientez encore %%i secondes...  "
    ping localhost -n 2 >nul
    echo.
)
echo   [OK] Initialisation terminee
echo.

echo [3/3] Demarrage de l'application GEOPOL...
echo   (fenetre minimisee dans la barre des taches)
echo.

REM Démarrage de Flask en mode MINIMISÉ
start "GEOPOL Flask" /MIN cmd /c ".venv\Scripts\activate.bat && python run.py"

echo   [OK] Application GEOPOL demarree (minimise)
echo.

echo Attente du demarrage de Flask...
set MAX_ATTEMPTS=6
set ATTEMPT=1

:CHECK_FLASK
<nul set /p="  Test %ATTEMPT%/%MAX_ATTEMPTS%... "
curl --silent --connect-timeout 5 "%GEOPOL_URL%/health" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCES]
    goto :OPEN_BROWSER
)
echo [En attente]

if %ATTEMPT% geq %MAX_ATTEMPTS% (
    echo   [ATTENTION] GEOPOL ne repond pas encore, ouverture...
    goto :OPEN_BROWSER
)

set /a ATTEMPT+=1
timeout /t 5 /nobreak >nul
goto :CHECK_FLASK

:OPEN_BROWSER
echo.
echo Ouverture du navigateur...
start "" "%GEOPOL_URL%"

echo.
echo ========================================
echo    GEOPOL est pret !
echo ========================================
echo.
echo  Interface Web : %GEOPOL_URL%
echo  Serveur IA    : http://localhost:%LLAMA_PORT%
echo  Modele        : Mistral 7B v0.2 Q4_0
echo.
echo  Les services tournent en arriere-plan
echo  Utilisez le bouton "Arret propre" dans l'interface
echo  ou fermez cette fenetre pour tout arreter
echo.
echo ========================================
pause