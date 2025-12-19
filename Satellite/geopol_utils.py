"""
Utilitaires géographiques pour GEOPOL
"""
from typing import Tuple, List
import math

def bbox_to_center(bbox: Tuple[float, float, float, float]) -> Tuple[float, float]:
    """Convertit une bbox en point central"""
    lon = (bbox[0] + bbox[2]) / 2
    lat = (bbox[1] + bbox[3]) / 2
    return (lon, lat)

def extend_bbox(bbox: Tuple, distance_km: float = 10) -> Tuple:
    """Étend une bbox de X km dans toutes les directions"""
    # 1 degré ≈ 111 km à l'équateur
    extend = distance_km / 111.0
    return (
        bbox[0] - extend,
        bbox[1] - extend,
        bbox[2] + extend,
        bbox[3] + extend
    )

def get_region_type(lat: float, lon: float) -> str:
    """Détermine le type de région (pour recommandations)"""
    # Simplifié - à améliorer
    if abs(lat) < 30:
        return "tropical"
    elif abs(lat) > 60:
        return "polar"
    else:
        return "temperate"