# Flask/sdr_interface.py
"""
Interface commune pour tous les services SDR
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class SDRInterface(ABC):
    """Interface que tous les services SDR doivent implémenter"""
    
    @abstractmethod
    def discover_active_servers(self) -> List[Dict[str, Any]]:
        """Découvre les serveurs SDR actifs"""
        pass
    
    @abstractmethod
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Données pour le dashboard"""
        pass
    
    @abstractmethod
    def get_test_spectrum(self) -> Dict[str, Any]:
        """Spectre de test pour visualisation"""
        pass
    
    @abstractmethod
    def scan_frequency(self, frequency_khz: int, category: str = 'custom') -> Dict[str, Any]:
        """Scanne une fréquence spécifique"""
        pass
    
    @abstractmethod
    def scan_all_geopolitical_frequencies(self) -> Dict[str, Any]:
        """Scanne toutes les fréquences géopolitiques"""
        pass
    
    def test_websdr_server(self, server: Dict) -> bool:
        """Teste un serveur WebSDR (optionnel)"""
        return False