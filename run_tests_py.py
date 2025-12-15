#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de test autonome pour le système d'indicateurs économiques
Fonctionne depuis n'importe où dans le projet
"""

import sys
import os
from pathlib import Path

# Déterminer le répertoire Flask
current_dir = Path(__file__).resolve().parent
flask_dir = current_dir / 'Flask' if (current_dir / 'Flask').exists() else current_dir

# Ajouter Flask au path Python
if str(flask_dir) not in sys.path:
    sys.path.insert(0, str(flask_dir))

print(f"📁 Répertoire de travail : {current_dir}")
print(f"📦 Répertoire Flask : {flask_dir}")
print(f"🐍 Path Python : {sys.path[0]}\n")

# Importer et lancer les tests
try:
    from test_enhanced_system import run_all_tests
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
    
except ImportError as e:
    print(f"❌ Erreur import : {e}")
    print("\n💡 Assurez-vous que les fichiers suivants existent :")
    print("   • Flask/test_enhanced_system.py")
    print("   • Flask/enhanced_indicators_connector.py")
    print("   • Flask/insee_scraper.py")
    print("   • Flask/eurostat_connector.py")
    print("   • Flask/yfinance_connector.py")
    sys.exit(1)

except Exception as e:
    print(f"❌ Erreur : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
