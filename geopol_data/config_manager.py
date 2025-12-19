"""
Gestionnaire de configurations et profils utilisateur pour la carte géopolitique.

Ce module permet de:
- Définir et gérer des profils de configuration (default, analyst, meteo)
- Sauvegarder les préférences utilisateur
- Charger et appliquer des configurations
- Valider les configurations
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from pathlib import Path


@dataclass
class LayerConfig:
    """Configuration d'une couche de carte."""
    enabled: bool = False
    opacity: float = 0.7
    z_index: int = 100
    refresh_interval: Optional[int] = None  # En secondes

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire."""
        return {
            'enabled': self.enabled,
            'opacity': self.opacity,
            'z_index': self.z_index,
            'refresh_interval': self.refresh_interval
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayerConfig':
        """Crée depuis un dictionnaire."""
        return cls(
            enabled=data.get('enabled', False),
            opacity=data.get('opacity', 0.7),
            z_index=data.get('z_index', 100),
            refresh_interval=data.get('refresh_interval')
        )


@dataclass
class WeatherConfig:
    """Configuration spécifique pour les couches météo."""
    metric: str = 'temperature'  # temperature, precipitation, air_quality
    show_forecast: bool = False
    forecast_days: int = 7
    color_scale: str = 'default'  # default, inverted, custom

    def to_dict(self) -> Dict[str, Any]:
        return {
            'metric': self.metric,
            'show_forecast': self.show_forecast,
            'forecast_days': self.forecast_days,
            'color_scale': self.color_scale
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WeatherConfig':
        return cls(
            metric=data.get('metric', 'temperature'),
            show_forecast=data.get('show_forecast', False),
            forecast_days=data.get('forecast_days', 7),
            color_scale=data.get('color_scale', 'default')
        )


@dataclass
class EarthquakeConfig:
    """Configuration spécifique pour les séismes."""
    min_magnitude: float = 4.5
    time_period: str = 'last_7_days'  # last_24h, last_7_days, last_30_days
    show_legends: bool = True
    pulse_animation: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'min_magnitude': self.min_magnitude,
            'time_period': self.time_period,
            'show_legends': self.show_legends,
            'pulse_animation': self.pulse_animation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EarthquakeConfig':
        return cls(
            min_magnitude=data.get('min_magnitude', 4.5),
            time_period=data.get('time_period', 'last_7_days'),
            show_legends=data.get('show_legends', True),
            pulse_animation=data.get('pulse_animation', True)
        )


@dataclass
class ConfigProfile:
    """Profil de configuration pour la carte géopolitique."""

    # Métadonnées
    name: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Couches activées/désactivées
    layers: Dict[str, LayerConfig] = field(default_factory=dict)

    # Entités géopolitiques à afficher
    entities: List[str] = field(default_factory=list)  # ['GPE', 'ORG', 'PERSON', 'EVENT']

    # Configuration météo
    weather: WeatherConfig = field(default_factory=WeatherConfig)

    # Configuration séismes
    earthquakes: EarthquakeConfig = field(default_factory=EarthquakeConfig)

    # Préférences visuelles
    theme: str = 'light'  # light, dark, satellite
    entity_marker_size: str = 'medium'  # small, medium, large
    show_tooltips: bool = True

    # Vue par défaut de la carte
    default_view: Dict[str, Any] = field(default_factory=lambda: {
        'center': [20, 0],  # lat, lon
        'zoom': 2
    })

    def to_dict(self) -> Dict[str, Any]:
        """Convertit le profil en dictionnaire."""
        return {
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'layers': {k: v.to_dict() for k, v in self.layers.items()},
            'entities': self.entities,
            'weather': self.weather.to_dict(),
            'earthquakes': self.earthquakes.to_dict(),
            'theme': self.theme,
            'entity_marker_size': self.entity_marker_size,
            'show_tooltips': self.show_tooltips,
            'default_view': self.default_view
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConfigProfile':
        """Crée un profil depuis un dictionnaire."""
        layers = {}
        for layer_name, layer_data in data.get('layers', {}).items():
            layers[layer_name] = LayerConfig.from_dict(layer_data)

        return cls(
            name=data['name'],
            description=data.get('description', ''),
            created_at=data.get('created_at', datetime.utcnow().isoformat()),
            updated_at=data.get('updated_at', datetime.utcnow().isoformat()),
            layers=layers,
            entities=data.get('entities', []),
            weather=WeatherConfig.from_dict(data.get('weather', {})),
            earthquakes=EarthquakeConfig.from_dict(data.get('earthquakes', {})),
            theme=data.get('theme', 'light'),
            entity_marker_size=data.get('entity_marker_size', 'medium'),
            show_tooltips=data.get('show_tooltips', True),
            default_view=data.get('default_view', {'center': [20, 0], 'zoom': 2})
        )

    def to_json(self) -> str:
        """Convertit le profil en JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'ConfigProfile':
        """Crée un profil depuis JSON."""
        return cls.from_dict(json.loads(json_str))


class ConfigManager:
    """Gestionnaire de profils de configuration."""

    # Profils par défaut
    DEFAULT_PROFILES = {
        'default': ConfigProfile(
            name='default',
            description='Configuration par défaut - Vue basique avec pays et zones géopolitiques',
            layers={
                'geopolitical_entities': LayerConfig(enabled=True, opacity=0.7, z_index=350),
                'sdr_receivers': LayerConfig(enabled=False, opacity=0.8, z_index=450),
                'weather': LayerConfig(enabled=False, opacity=0.6, z_index=200),
                'earthquakes': LayerConfig(enabled=False, opacity=0.8, z_index=400)
            },
            entities=['GPE'],  # Seulement les lieux géopolitiques
            weather=WeatherConfig(metric='temperature', show_forecast=False),
            earthquakes=EarthquakeConfig(min_magnitude=4.5, time_period='last_7_days'),
            theme='light',
            entity_marker_size='medium'
        ),

        'analyst': ConfigProfile(
            name='analyst',
            description='Mode analyste - Toutes les couches activées pour analyse approfondie',
            layers={
                'geopolitical_entities': LayerConfig(enabled=True, opacity=0.7, z_index=350),
                'sdr_receivers': LayerConfig(enabled=True, opacity=0.8, z_index=450, refresh_interval=300),
                'weather': LayerConfig(enabled=True, opacity=0.5, z_index=200),
                'earthquakes': LayerConfig(enabled=True, opacity=0.7, z_index=400)
            },
            entities=['GPE', 'ORG', 'PERSON'],  # Lieux, organisations, personnalités
            weather=WeatherConfig(metric='air_quality', show_forecast=True, forecast_days=7),
            earthquakes=EarthquakeConfig(min_magnitude=3.0, time_period='last_30_days', pulse_animation=True),
            theme='dark',
            entity_marker_size='large',
            show_tooltips=True
        ),

        'meteo': ConfigProfile(
            name='meteo',
            description='Mode météo - Focus sur données environnementales et climatiques',
            layers={
                'geopolitical_entities': LayerConfig(enabled=False, opacity=0.5, z_index=350),
                'sdr_receivers': LayerConfig(enabled=False, opacity=0.8, z_index=450),
                'weather': LayerConfig(enabled=True, opacity=0.8, z_index=200),
                'earthquakes': LayerConfig(enabled=True, opacity=0.6, z_index=400)
            },
            entities=[],  # Aucune entité géopolitique
            weather=WeatherConfig(
                metric='precipitation',
                show_forecast=True,
                forecast_days=7,
                color_scale='default'
            ),
            earthquakes=EarthquakeConfig(min_magnitude=5.0, time_period='last_7_days'),
            theme='light',
            entity_marker_size='small',
            default_view={'center': [45, 0], 'zoom': 3}
        )
    }

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialise le gestionnaire de configuration.

        Args:
            storage_path: Chemin optionnel pour sauvegarder les profils personnalisés
        """
        self.storage_path = storage_path
        self.custom_profiles: Dict[str, ConfigProfile] = {}

        if storage_path and storage_path.exists():
            self._load_custom_profiles()

    def get_profile(self, name: str) -> Optional[ConfigProfile]:
        """
        Récupère un profil par son nom.

        Args:
            name: Nom du profil

        Returns:
            Le profil ou None s'il n'existe pas
        """
        # Chercher d'abord dans les profils par défaut
        if name in self.DEFAULT_PROFILES:
            return self.DEFAULT_PROFILES[name]

        # Puis dans les profils personnalisés
        return self.custom_profiles.get(name)

    def list_profiles(self) -> Dict[str, Dict[str, str]]:
        """
        Liste tous les profils disponibles.

        Returns:
            Dictionnaire {nom: {description, type}}
        """
        profiles = {}

        # Profils par défaut
        for name, profile in self.DEFAULT_PROFILES.items():
            profiles[name] = {
                'description': profile.description,
                'type': 'default',
                'created_at': profile.created_at,
                'updated_at': profile.updated_at
            }

        # Profils personnalisés
        for name, profile in self.custom_profiles.items():
            profiles[name] = {
                'description': profile.description,
                'type': 'custom',
                'created_at': profile.created_at,
                'updated_at': profile.updated_at
            }

        return profiles

    def save_profile(self, profile: ConfigProfile, overwrite: bool = False) -> bool:
        """
        Sauvegarde un profil personnalisé.

        Args:
            profile: Le profil à sauvegarder
            overwrite: Si True, écrase un profil existant

        Returns:
            True si succès, False sinon
        """
        # Ne pas écraser les profils par défaut
        if profile.name in self.DEFAULT_PROFILES and not overwrite:
            return False

        # Mettre à jour le timestamp
        profile.updated_at = datetime.utcnow().isoformat()

        # Sauvegarder dans la mémoire
        self.custom_profiles[profile.name] = profile

        # Sauvegarder sur disque si storage_path défini
        if self.storage_path:
            self._save_to_disk(profile)

        return True

    def delete_profile(self, name: str) -> bool:
        """
        Supprime un profil personnalisé.

        Args:
            name: Nom du profil

        Returns:
            True si succès, False sinon
        """
        # Ne pas supprimer les profils par défaut
        if name in self.DEFAULT_PROFILES:
            return False

        if name not in self.custom_profiles:
            return False

        # Supprimer de la mémoire
        del self.custom_profiles[name]

        # Supprimer du disque
        if self.storage_path:
            profile_file = self.storage_path / f"{name}.json"
            if profile_file.exists():
                profile_file.unlink()

        return True

    def validate_profile(self, profile: ConfigProfile) -> tuple[bool, Optional[str]]:
        """
        Valide un profil de configuration.

        Args:
            profile: Le profil à valider

        Returns:
            (valide, message_erreur)
        """
        # Vérifier le nom
        if not profile.name or not profile.name.strip():
            return False, "Le nom du profil ne peut pas être vide"

        # Vérifier les couches
        valid_layers = ['geopolitical_entities', 'sdr_receivers', 'weather', 'earthquakes']
        for layer_name in profile.layers.keys():
            if layer_name not in valid_layers:
                return False, f"Couche invalide: {layer_name}"

        # Vérifier les entités
        valid_entities = ['GPE', 'ORG', 'PERSON', 'EVENT']
        for entity in profile.entities:
            if entity not in valid_entities:
                return False, f"Entité invalide: {entity}"

        # Vérifier le thème
        valid_themes = ['light', 'dark', 'satellite']
        if profile.theme not in valid_themes:
            return False, f"Thème invalide: {profile.theme}"

        # Vérifier la taille des marqueurs
        valid_sizes = ['small', 'medium', 'large']
        if profile.entity_marker_size not in valid_sizes:
            return False, f"Taille de marqueur invalide: {profile.entity_marker_size}"

        # Vérifier la métrique météo
        valid_metrics = ['temperature', 'precipitation', 'air_quality']
        if profile.weather.metric not in valid_metrics:
            return False, f"Métrique météo invalide: {profile.weather.metric}"

        # Vérifier la magnitude des séismes
        if not 0 <= profile.earthquakes.min_magnitude <= 10:
            return False, "La magnitude doit être entre 0 et 10"

        return True, None

    def _load_custom_profiles(self):
        """Charge les profils personnalisés depuis le disque."""
        if not self.storage_path or not self.storage_path.exists():
            return

        for profile_file in self.storage_path.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                    profile = ConfigProfile.from_dict(profile_data)
                    self.custom_profiles[profile.name] = profile
            except Exception as e:
                print(f"Erreur lors du chargement du profil {profile_file}: {e}")

    def _save_to_disk(self, profile: ConfigProfile):
        """Sauvegarde un profil sur le disque."""
        if not self.storage_path:
            return

        self.storage_path.mkdir(parents=True, exist_ok=True)
        profile_file = self.storage_path / f"{profile.name}.json"

        try:
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du profil {profile.name}: {e}")

    def create_profile_from_current_state(
        self,
        name: str,
        description: str,
        current_state: Dict[str, Any]
    ) -> ConfigProfile:
        """
        Crée un nouveau profil basé sur l'état actuel de la carte.

        Args:
            name: Nom du nouveau profil
            description: Description du profil
            current_state: État actuel de la carte (layers, entities, etc.)

        Returns:
            Le nouveau profil créé
        """
        # Créer les configurations de couches
        layers = {}
        for layer_name, layer_state in current_state.get('layers', {}).items():
            layers[layer_name] = LayerConfig(
                enabled=layer_state.get('enabled', False),
                opacity=layer_state.get('opacity', 0.7),
                z_index=layer_state.get('z_index', 100),
                refresh_interval=layer_state.get('refresh_interval')
            )

        # Créer le profil
        profile = ConfigProfile(
            name=name,
            description=description,
            layers=layers,
            entities=current_state.get('entities', []),
            weather=WeatherConfig.from_dict(current_state.get('weather', {})),
            earthquakes=EarthquakeConfig.from_dict(current_state.get('earthquakes', {})),
            theme=current_state.get('theme', 'light'),
            entity_marker_size=current_state.get('entity_marker_size', 'medium'),
            show_tooltips=current_state.get('show_tooltips', True),
            default_view=current_state.get('default_view', {'center': [20, 0], 'zoom': 2})
        )

        return profile
