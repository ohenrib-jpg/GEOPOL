# Flask/__init__.py
"""
Package Flask de GEOPOL Analytics
Contient l'application principale et tous les modules
"""

# Version du package
__version__ = '1.0.0'

# Imports principaux (optionnel)
try:
    from .app_factory import create_app
    __all__ = ['create_app']
except ImportError:
    # Si app_factory n'est pas encore disponible
    pass
