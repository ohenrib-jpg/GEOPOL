"""
Script d'arrêt propre pour GEOPOL
Ferme tous les services (Flask + Mistral) de manière ordonnée
"""

import os
import sys
import signal
import psutil
import time
from flask import jsonify

def shutdown_geopol():
    """Arrête proprement tous les services GEOPOL"""
    
    print("🔴 Arrêt propre de GEOPOL...")
    services_stopped = []
    
    try:
        # 1. Arrêter le serveur Flask (celui qui exécute ce script)
        print("  → Arrêt du serveur Flask...")
        services_stopped.append("Flask")
        
        # 2. Trouver et arrêter le serveur Llama (Mistral)
        print("  → Recherche du serveur Mistral...")
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Détecter llama-server.exe
                if 'llama-server.exe' in proc.info['name'].lower():
                    print(f"  → Arrêt du serveur IA (PID: {proc.info['pid']})")
                    proc.terminate()
                    services_stopped.append("Serveur IA Mistral")
                    
                    # Attendre la fermeture gracieuse (max 5 secondes)
                    try:
                        proc.wait(timeout=5)
                    except psutil.TimeoutExpired:
                        print(f"  ⚠️  Forçage de l'arrêt du serveur IA...")
                        proc.kill()
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 3. Nettoyer les processus Python liés à GEOPOL
        current_pid = os.getpid()
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] == current_pid:
                    continue
                    
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'run.py' in cmdline or 'flask' in cmdline.lower():
                    print(f"  → Arrêt du processus Flask (PID: {proc.info['pid']})")
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        proc.kill()
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        print("\n✅ Arrêt terminé avec succès")
        print(f"Services arrêtés: {', '.join(services_stopped)}")
        
        return True, services_stopped
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'arrêt: {e}")
        return False, []


def shutdown_endpoint():
    """
    Endpoint Flask pour déclencher l'arrêt propre
    À intégrer dans votre application Flask
    """
    try:
        success, services = shutdown_geopol()
        
        # Arrêter Flask après avoir envoyé la réponse
        def delayed_shutdown():
            time.sleep(2)  # Augmenté à 2s pour que le client reçoive la réponse
            os.kill(os.getpid(), signal.SIGTERM)
        
        # Lancer l'arrêt en arrière-plan
        import threading
        threading.Thread(target=delayed_shutdown, daemon=True).start()
        
        return jsonify({
            'status': 'success' if success else 'error',
            'message': 'Arrêt en cours...',
            'services_stopped': services
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    # Exécution directe du script
    success, _ = shutdown_geopol()
    sys.exit(0 if success else 1)