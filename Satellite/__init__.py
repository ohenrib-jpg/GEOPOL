"""
Module satellite pour GEOPOL - Intégration simplifiée
"""
from .satellite_blueprint import satellite_bp, init_satellite_blueprint
from .satellite_manager import SatelliteManager

__all__ = ['satellite_bp', 'init_satellite_blueprint', 'SatelliteManager']