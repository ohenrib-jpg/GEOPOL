"""
Gestionnaire centralisé des surcouches pour DataService
Orchestre toutes les surcouches (météo, SDR, etc.)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class OverlayManager:
    """Gestionnaire central des surcouches de la carte"""
    
    def __init__(self, data_service):
        self.data_service = data_service
        self.overlays = {}  # Dict des surcouches chargées
        self.active_overlays = {}  # Dict des surcouches actives
        self.overlay_configs = {}  # Configurations des surcouches
        
        # Initialiser les surcouches disponibles
        self._init_available_overlays()
        
        logger.info("OverlayManager initialisé")
    
    def _init_available_overlays(self):
        """Initialise les surcouches disponibles"""
        self.overlay_configs = {
            'weather': {
                'name': 'Météo',
                'description': 'Données météorologiques et qualité de l\'air',
                'enabled': False,
                'requires': ['open_meteo'],
                'category': 'environment',
                'order': 1,
                'icon': '🌤️'
            },
            'sdr_health': {
                'name': 'Santé SDR',
                'description': 'Surveillance santé réseau radio',
                'enabled': False,
                'requires': ['sdr'],
                'category': 'security',
                'order': 2,
                'icon': '📡'
            },
            'geopolitical_risk': {
                'name': 'Risque Géopolitique',
                'description': 'Indices de risque géopolitique',
                'enabled': True,  # Activé par défaut
                'requires': [],
                'category': 'geopolitics',
                'order': 0,
                'icon': '🌍'
            },
            'economic_indicators': {
                'name': 'Indicateurs Économiques',
                'description': 'PIB, chômage, inflation',
                'enabled': True,  # Activé par défaut
                'requires': [],
                'category': 'economy',
                'order': 3,
                'icon': '💰'
            }
        }
    
    def load_overlay(self, overlay_id: str) -> bool:
        """Charge une surcouche spécifique"""
        if overlay_id not in self.overlay_configs:
            logger.warning(f"Surcouche inconnue: {overlay_id}")
            return False
        
        config = self.overlay_configs[overlay_id]
        
        # Vérifier les dépendances
        for requirement in config.get('requires', []):
            if not self._check_requirement(requirement):
                logger.warning(f"Dépendance manquante pour {overlay_id}: {requirement}")
                return False
        
        try:
            if overlay_id == 'weather':
                self._load_weather_overlay()
            elif overlay_id == 'sdr_health':
                self._load_sdr_overlay()
            elif overlay_id == 'geopolitical_risk':
                self._load_geopolitical_overlay()
            elif overlay_id == 'economic_indicators':
                self._load_economic_overlay()
            
            config['enabled'] = True
            self.active_overlays[overlay_id] = config
            logger.info(f"✅ Surcouche chargée: {overlay_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement surcouche {overlay_id}: {e}")
            return False
    
    def _load_weather_overlay(self):
        """Charge la surcouche météo"""
        if not OPEN_METEO_AVAILABLE:
            raise ImportError("Module Open-Meteo non disponible")
        
        from .open_meteo_integration import OpenMeteoIntegration
        self.overlays['weather'] = OpenMeteoIntegration()
        
        # Tester la connexion
        if hasattr(self.overlays['weather'], 'test_connection'):
            if not self.overlays['weather'].test_connection():
                logger.warning("⚠️ Connexion Open-Meteo échouée")
    
    def _load_sdr_overlay(self):
        """Charge la surcouche SDR"""
        if not SDR_AVAILABLE:
            raise ImportError("Module SDR non disponible")
        
        from .sdr_integration import SDRIntegrationManager
        # Note: besoin de l'app et db_manager - à passer depuis l'extérieur
        self.overlays['sdr_health'] = None  # Placeholder
    
    def _load_geopolitical_overlay(self):
        """Charge la surcouche risque géopolitique"""
        # Utilise les données existantes du DataService
        self.overlays['geopolitical_risk'] = {
            'type': 'calculated',
            'source': 'world_bank',
            'calculator': self._calculate_geopolitical_risk
        }
    
    def _load_economic_overlay(self):
        """Charge la surcouche indicateurs économiques"""
        self.overlays['economic_indicators'] = {
            'type': 'direct',
            'source': 'world_bank',
            'indicators': ['gdp', 'gdp_growth', 'unemployment', 'inflation']
        }
    
    def _check_requirement(self, requirement: str) -> bool:
        """Vérifie si une dépendance est disponible"""
        if requirement == 'open_meteo':
            return OPEN_METEO_AVAILABLE
        elif requirement == 'sdr':
            return SDR_AVAILABLE
        return True
    
    def enable_overlay(self, overlay_id: str) -> bool:
        """Active une surcouche"""
        if overlay_id in self.active_overlays:
            logger.info(f"Surcouche déjà active: {overlay_id}")
            return True
        
        return self.load_overlay(overlay_id)
    
    def disable_overlay(self, overlay_id: str) -> bool:
        """Désactive une surcouche"""
        if overlay_id in self.active_overlays:
            del self.active_overlays[overlay_id]
            if overlay_id in self.overlays:
                # Optionnel: nettoyer les ressources
                pass
            logger.info(f"Surcouche désactivée: {overlay_id}")
            return True
        return False
    
    def get_overlay(self, overlay_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une surcouche"""
        if overlay_id in self.overlays:
            overlay = self.overlays[overlay_id]
            config = self.overlay_configs.get(overlay_id, {})
            
            return {
                'id': overlay_id,
                'config': config,
                'instance': overlay,
                'active': overlay_id in self.active_overlays,
                'data_available': self._check_data_availability(overlay_id)
            }
        return None
    
    def get_all_overlays(self, active_only: bool = False) -> Dict[str, Any]:
        """Récupère toutes les surcouches"""
        overlays = {}
        
        for overlay_id, config in self.overlay_configs.items():
            if active_only and not config['enabled']:
                continue
            
            overlay_info = {
                'id': overlay_id,
                'name': config['name'],
                'description': config['description'],
                'enabled': config['enabled'],
                'active': overlay_id in self.active_overlays,
                'category': config['category'],
                'order': config['order'],
                'icon': config['icon'],
                'has_data': self._check_data_availability(overlay_id)
            }
            
            # Ajouter des infos spécifiques
            if overlay_id in self.overlays:
                overlay_info['loaded'] = True
                overlay_info['type'] = type(self.overlays[overlay_id]).__name__
            
            overlays[overlay_id] = overlay_info
        
        return overlays
    
    def _check_data_availability(self, overlay_id: str) -> bool:
        """Vérifie la disponibilité des données pour une surcouche"""
        if overlay_id == 'weather':
            # Vérifier la connexion Open-Meteo
            if 'weather' in self.overlays:
                return hasattr(self.overlays['weather'], 'test_connection') and \
                       self.overlays['weather'].test_connection()
            return OPEN_METEO_AVAILABLE
        
        elif overlay_id == 'sdr_health':
            return SDR_AVAILABLE
        
        elif overlay_id in ['geopolitical_risk', 'economic_indicators']:
            # Toujours disponible (données World Bank)
            return True
        
        return False
    
    def get_overlay_data(self, overlay_id: str, country_code: str = None) -> Dict[str, Any]:
        """Récupère les données d'une surcouche"""
        if overlay_id not in self.active_overlays:
            return {'error': f'Surcouche non active: {overlay_id}'}
        
        try:
            if overlay_id == 'weather':
                return self._get_weather_data(country_code)
            elif overlay_id == 'geopolitical_risk':
                return self._get_geopolitical_data(country_code)
            elif overlay_id == 'economic_indicators':
                return self._get_economic_data(country_code)
            else:
                return {'error': f'Données non disponibles pour: {overlay_id}'}
                
        except Exception as e:
            logger.error(f"Erreur données surcouche {overlay_id}: {e}")
            return {'error': str(e)}
    
    def _get_weather_data(self, country_code: str = None) -> Dict[str, Any]:
        """Récupère les données météo"""
        if 'weather' not in self.overlays:
            return {'error': 'Surcouche météo non chargée'}
        
        weather_integration = self.overlays['weather']
        
        if country_code:
            # Données pour un pays spécifique
            return weather_integration.fetch_country_weather(country_code)
        else:
            # Données pour tous les pays prioritaires
            from .constants import PRIORITY_COUNTRIES
            return weather_integration.fetch_multiple_countries(PRIORITY_COUNTRIES[:10])
    
    def _get_geopolitical_data(self, country_code: str = None) -> Dict[str, Any]:
        """Calcule le risque géopolitique"""
        if country_code:
            snapshot = self.data_service.get_country_snapshot(country_code)
            if snapshot:
                return {
                    'country_code': country_code,
                    'risk_score': self._calculate_geopolitical_risk(snapshot),
                    'factors': self._extract_risk_factors(snapshot),
                    'level': self._get_risk_level(snapshot)
                }
            return {'error': f'Données non disponibles pour {country_code}'}
        
        # Pour tous les pays
        from .constants import PRIORITY_COUNTRIES
        results = {}
        
        for code in PRIORITY_COUNTRIES[:20]:
            snapshot = self.data_service.get_country_snapshot(code)
            if snapshot:
                results[code] = {
                    'risk_score': self._calculate_geopolitical_risk(snapshot),
                    'level': self._get_risk_level(snapshot)
                }
        
        return results
    
    def _calculate_geopolitical_risk(self, snapshot) -> float:
        """Calcule un score de risque géopolitique (0-100)"""
        factors = []
        
        # Facteur militaire
        if snapshot.military_spending_pct:
            military_factor = min(100, snapshot.military_spending_pct * 10)
            factors.append(military_factor * 0.3)
        
        # Facteur économique
        if snapshot.unemployment:
            economic_factor = snapshot.unemployment * 2
            factors.append(economic_factor * 0.25)
        
        # Facteur environnemental
        if snapshot.pm25:
            environmental_factor = min(100, snapshot.pm25 * 2)
            factors.append(environmental_factor * 0.2)
        
        # Facteur dette
        if snapshot.debt:
            debt_factor = min(100, snapshot.debt)
            factors.append(debt_factor * 0.25)
        
        return round(sum(factors), 1) if factors else 0.0
    
    def _extract_risk_factors(self, snapshot) -> Dict[str, float]:
        """Extrait les facteurs de risque individuels"""
        factors = {}
        
        if snapshot.military_spending_pct:
            factors['military'] = snapshot.military_spending_pct
        
        if snapshot.unemployment:
            factors['unemployment'] = snapshot.unemployment
        
        if snapshot.pm25:
            factors['pollution'] = snapshot.pm25
        
        if snapshot.debt:
            factors['debt'] = snapshot.debt
        
        return factors
    
    def _get_risk_level(self, snapshot) -> str:
        """Détermine le niveau de risque"""
        risk_score = self._calculate_geopolitical_risk(snapshot)
        
        if risk_score > 75:
            return 'CRITICAL'
        elif risk_score > 50:
            return 'HIGH'
        elif risk_score > 25:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_economic_data(self, country_code: str = None) -> Dict[str, Any]:
        """Récupère les données économiques"""
        if country_code:
            snapshot = self.data_service.get_country_snapshot(country_code)
            if snapshot:
                return {
                    'country_code': country_code,
                    'gdp': snapshot.gdp,
                    'gdp_per_capita': snapshot.gdp_per_capita,
                    'gdp_growth': snapshot.gdp_growth,
                    'unemployment': snapshot.unemployment,
                    'inflation': snapshot.inflation,
                    'debt': snapshot.debt
                }
            return {'error': f'Données non disponibles pour {country_code}'}
        
        # Pour tous les pays
        from .constants import PRIORITY_COUNTRIES
        results = {}
        
        for code in PRIORITY_COUNTRIES[:20]:
            snapshot = self.data_service.get_country_snapshot(code)
            if snapshot:
                results[code] = {
                    'gdp': snapshot.gdp,
                    'gdp_per_capita': snapshot.gdp_per_capita,
                    'gdp_growth': snapshot.gdp_growth
                }
        
        return results
    
    def get_control_panel_config(self) -> Dict[str, Any]:
        """Configuration pour le panneau de contrôle"""
        overlays = self.get_all_overlays()
        
        # Grouper par catégorie
        categories = {}
        for overlay in overlays.values():
            category = overlay['category']
            if category not in categories:
                categories[category] = {
                    'name': self._get_category_name(category),
                    'overlays': []
                }
            categories[category]['overlays'].append(overlay)
        
        # Trier les catégories
        category_order = ['geopolitics', 'economy', 'environment', 'security']
        sorted_categories = []
        for cat in category_order:
            if cat in categories:
                # Trier les surcouches dans la catégorie
                categories[cat]['overlays'].sort(key=lambda x: x['order'])
                sorted_categories.append({
                    'id': cat,
                    'name': categories[cat]['name'],
                    'overlays': categories[cat]['overlays']
                })
        
        return {
            'title': '🎛️ Panneau de Contrôle',
            'description': 'Gérez les surcouches de la carte',
            'categories': sorted_categories,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _get_category_name(self, category_id: str) -> str:
        """Retourne le nom d'une catégorie"""
        names = {
            'geopolitics': 'Géopolitique',
            'economy': 'Économie',
            'environment': 'Environnement',
            'security': 'Sécurité'
        }
        return names.get(category_id, category_id)
    
    def toggle_overlay(self, overlay_id: str, enable: bool = None) -> Dict[str, Any]:
        """Active/désactive une surcouche"""
        if enable is None:
            # Basculer
            enable = overlay_id not in self.active_overlays
        
        if enable:
            success = self.enable_overlay(overlay_id)
            action = 'activée'
        else:
            success = self.disable_overlay(overlay_id)
            action = 'désactivée'
        
        return {
            'success': success,
            'overlay_id': overlay_id,
            'action': action,
            'enabled': enable,
            'message': f'Surcouche {overlay_id} {action}'
        }
    
    def update_overlay_opacity(self, overlay_id: str, opacity: float) -> Dict[str, Any]:
        """Met à jour l'opacité d'une surcouche"""
        if overlay_id not in self.overlay_configs:
            return {'error': f'Surcouche inconnue: {overlay_id}'}
        
        # Limiter entre 0 et 1
        opacity = max(0.0, min(1.0, opacity))
        
        # Stocker dans la configuration
        self.overlay_configs[overlay_id]['opacity'] = opacity
        
        logger.info(f"Opacité surcouche {overlay_id}: {opacity}")
        
        return {
            'success': True,
            'overlay_id': overlay_id,
            'opacity': opacity,
            'message': f'Opacité mise à jour: {int(opacity * 100)}%'
        }