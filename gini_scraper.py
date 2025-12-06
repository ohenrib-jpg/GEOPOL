# Flask/gini_scraper.py
"""
Scraper pour l'indice GINI (inégalités de revenus)
Sources : Eurostat + Banque Mondiale
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json
import os
import re

logger = logging.getLogger(__name__)


class GINIScraper:
    """Scraper pour l'indice GINI des inégalités"""
    
    # Sources multiples pour plus de robustesse
    SOURCES = {
        'eurostat': {
            'url': "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ilc_di12",
            'dataset': 'ilc_di12',
            'params': {
                'format': 'JSON',
                'lang': 'EN',
                'geo': 'FR',
                'precision': 1,
                'time': '2023'  # Dernière année disponible
            }
        },
        'worldbank': {
            'url': "https://api.worldbank.org/v2/country/FR/indicator/SI.POV.GINI",
            'params': {
                'format': 'json',
                'per_page': 5  # 5 dernières années
            }
        }
    }
    
    # Données fallback (mises à jour)
    FALLBACK_DATA = {
        'value': 29.8,  # GINI France 2022 (dernière disponible)
        'period': '2022',
        'name': 'Indice GINI (inégalités)',
        'unit': 'Points (0-100)',
        'description': 'Mesure des inégalités de revenus (0=égalité parfaite, 100=inégalité maximale)',
        'source': 'INSEE 2022'
    }
    
    def __init__(self, cache_file: str = 'instance/gini_cache.json'):
        self.cache_file = cache_file
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json,text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive'
        })
        logger.info("✅ GINIScraper initialisé avec sources multiples")
    
    def get_gini_data(self) -> Dict[str, Any]:
        """
        Récupère l'indice GINI pour la France
        Essai multiple de sources avec fallback intelligent
        """
        # 1. Vérifier le cache
        cached_data = self._load_from_cache()
        if cached_data and self._is_cache_valid(cached_data):
            logger.info("📦 Utilisation GINI depuis cache")
            cached_data['source'] = cached_data.get('source', 'Cache')
            cached_data['note'] = 'Données en cache (moins de 24h)'
            return cached_data
        
        # 2. Essayer Eurostat (source principale)
        logger.info("📊 Tentative récupération GINI depuis Eurostat...")
        eurostat_data = self._fetch_from_eurostat()
        
        if eurostat_data and eurostat_data.get('success'):
            self._save_to_cache(eurostat_data)
            logger.info("✅ GINI Eurostat récupéré avec succès")
            return eurostat_data
        
        # 3. Essayer Banque Mondiale (source secondaire)
        logger.info("🌍 Tentative récupération GINI depuis Banque Mondiale...")
        worldbank_data = self._fetch_from_worldbank()
        
        if worldbank_data and worldbank_data.get('success'):
            self._save_to_cache(worldbank_data)
            logger.info("✅ GINI Banque Mondiale récupéré avec succès")
            return worldbank_data
        
        # 4. Essayer INSEE (via scraping)
        logger.info("🏛️ Tentative récupération GINI depuis INSEE...")
        insee_data = self._fetch_from_insee()
        
        if insee_data and insee_data.get('success'):
            self._save_to_cache(insee_data)
            logger.info("✅ GINI INSEE récupéré avec succès")
            return insee_data
        
        # 5. Utiliser cache même expiré
        if cached_data:
            logger.info("📦 Utilisation cache expiré en secours")
            cached_data['note'] = 'Cache expiré - toutes les sources ont échoué'
            return cached_data
        
        # 6. Fallback final
        logger.info("🔄 Utilisation données GINI fallback")
        return self._get_fallback_data()
    
    def _fetch_from_eurostat(self) -> Optional[Dict[str, Any]]:
        """Récupère GINI depuis Eurostat API"""
        try:
            source = self.SOURCES['eurostat']
            response = self.session.get(
                source['url'],
                params=source['params'],
                timeout=15,
                verify=True
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_eurostat_response(data)
            else:
                logger.warning(f"⚠️ Eurostat status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur Eurostat: {e}")
            return None
    
    def _parse_eurostat_response(self, data: Dict) -> Optional[Dict[str, Any]]:
        """Parse la réponse Eurostat"""
        try:
            # Structure de réponse Eurostat typique
            values = data.get('value', {})
            dimensions = data.get('dimension', {})
            
            if not values:
                return None
            
            # Extraire les valeurs et périodes
            gini_values = []
            
            # Parcourir les valeurs
            for key, value in values.items():
                try:
                    # Trouver la période correspondante
                    period_idx = int(key)
                    
                    # Chercher la période dans les dimensions
                    time_index = data.get('dimension', {}).get('time', {}).get('category', {}).get('index', {})
                    period = None
                    for p, idx in time_index.items():
                        if idx == period_idx:
                            period = p
                            break
                    
                    if period and value:
                        gini_values.append({
                            'period': period,
                            'value': float(value)
                        })
                except (ValueError, KeyError):
                    continue
            
            if not gini_values:
                return None
            
            # Trier par période (la plus récente d'abord)
            gini_values.sort(key=lambda x: x['period'], reverse=True)
            
            latest = gini_values[0]
            previous = gini_values[1] if len(gini_values) > 1 else latest
            
            # Calculer les variations
            change = latest['value'] - previous['value']
            change_percent = (change / previous['value'] * 100) if previous['value'] != 0 else 0
            
            return {
                'success': True,
                'id': 'eurostat_gini',
                'name': 'Indice GINI (inégalités)',
                'value': round(latest['value'], 1),
                'previous_value': round(previous['value'], 1),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'unit': 'Points (0-100)',
                'period': latest['period'],
                'previous_period': previous['period'],
                'source': 'Eurostat (UE)',
                'dataset': 'ilc_di12',
                'description': 'Coefficient de GINI - Mesure des inégalités de revenus disponibles',
                'category': 'inequality',
                'reliability': 'official',
                'last_update': datetime.now().isoformat(),
                'interpretation': self._interpret_gini(latest['value']),
                'note': 'Données officielles Eurostat'
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur parsing Eurostat: {e}")
            return None
    
    def _fetch_from_worldbank(self) -> Optional[Dict[str, Any]]:
        """Récupère GINI depuis Banque Mondiale"""
        try:
            source = self.SOURCES['worldbank']
            response = self.session.get(
                source['url'],
                params=source['params'],
                timeout=15,
                verify=True
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_worldbank_response(data)
            else:
                logger.warning(f"⚠️ Banque Mondiale status {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur Banque Mondiale: {e}")
            return None
    
    def _parse_worldbank_response(self, data: list) -> Optional[Dict[str, Any]]:
        """Parse la réponse Banque Mondiale"""
        try:
            if not data or len(data) < 2:
                return None
            
            indicators = data[1]  # Les données sont dans le deuxième élément
            
            if not indicators:
                return None
            
            # Filtrer les années avec données valides
            valid_years = []
            for item in indicators:
                if item.get('value') is not None:
                    try:
                        valid_years.append({
                            'year': int(item.get('date')),
                            'value': float(item.get('value'))
                        })
                    except (ValueError, TypeError):
                        continue
            
            if not valid_years:
                return None
            
            # Trier par année (décroissant)
            valid_years.sort(key=lambda x: x['year'], reverse=True)
            
            latest = valid_years[0]
            previous = valid_years[1] if len(valid_years) > 1 else latest
            
            # Calculer les variations
            change = latest['value'] - previous['value']
            change_percent = (change / previous['value'] * 100) if previous['value'] != 0 else 0
            
            return {
                'success': True,
                'id': 'worldbank_gini',
                'name': 'Indice GINI (inégalités)',
                'value': round(latest['value'], 1),
                'previous_value': round(previous['value'], 1),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'unit': 'Points (0-100)',
                'period': str(latest['year']),
                'previous_period': str(previous['year']),
                'source': 'Banque Mondiale',
                'description': 'Coefficient de GINI - Mesure des inégalités de revenus',
                'category': 'inequality',
                'reliability': 'official',
                'last_update': datetime.now().isoformat(),
                'interpretation': self._interpret_gini(latest['value']),
                'note': 'Données Banque Mondiale'
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur parsing Banque Mondiale: {e}")
            return None
    
    def _fetch_from_insee(self) -> Optional[Dict[str, Any]]:
        """Essaie de récupérer GINI depuis INSEE"""
        try:
            # URL INSEE pour les inégalités
            insee_url = "https://www.insee.fr/fr/statistiques/serie/010599953"
            
            response = self.session.get(insee_url, timeout=15, verify=True)
            
            if response.status_code == 200:
                # Recherche simple de valeurs GINI dans la page
                content = response.text
                
                # Patterns pour trouver GINI
                patterns = [
                    r'Gini.*?(\d+[,\.]\d+)',
                    r'gini.*?(\d+[,\.]\d+)',
                    r'(\d+[,\.]\d+).*?coefficient.*?Gini',
                    r'(\d+[,\.]\d+).*?indice.*?Gini'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        try:
                            value = float(match.group(1).replace(',', '.'))
                            if 20 <= value <= 40:  # Plage raisonnable pour GINI
                                current_year = datetime.now().year
                                return {
                                    'success': True,
                                    'id': 'insee_gini',
                                    'name': 'Indice GINI (inégalités)',
                                    'value': round(value, 1),
                                    'previous_value': round(value, 1),
                                    'change': 0,
                                    'change_percent': 0,
                                    'unit': 'Points (0-100)',
                                    'period': str(current_year - 1),  # Année précédente
                                    'source': 'INSEE scraping',
                                    'description': 'Coefficient de GINI estimé',
                                    'category': 'inequality',
                                    'reliability': 'estimated',
                                    'last_update': datetime.now().isoformat(),
                                    'interpretation': self._interpret_gini(value),
                                    'note': 'Valeur estimée depuis site INSEE'
                                }
                        except (ValueError, TypeError):
                            continue
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur INSEE scraping: {e}")
            return None
    
    def _interpret_gini(self, value: float) -> str:
        """Interprète la valeur du GINI"""
        value = float(value)
        if value < 25:
            return "Inégalités très faibles (pays très égalitaires)"
        elif value < 30:
            return "Inégalités faibles à modérées (pays développés typiques)"
        elif value < 35:
            return "Inégalités modérées"
        elif value < 40:
            return "Inégalités élevées"
        else:
            return "Inégalités très élevées"
    
    def _load_from_cache(self) -> Optional[Dict]:
        """Charge depuis le cache JSON"""
        try:
            if not os.path.exists(self.cache_file):
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Vérifier la structure de base
            if isinstance(data, dict) and data.get('value') is not None:
                return data
            return None
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Erreur chargement cache: {e}")
            return None
    
    def _save_to_cache(self, data: Dict):
        """Sauvegarde dans le cache"""
        try:
            # Créer le dossier si nécessaire
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("💾 Cache GINI sauvegardé")
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache: {e}")
    
    def _is_cache_valid(self, cached_data: Dict) -> bool:
        """Vérifie si le cache est valide (< 24h)"""
        try:
            last_update = cached_data.get('last_update')
            if not last_update:
                return False
            
            cache_time = datetime.fromisoformat(last_update)
            age = datetime.now() - cache_time
            return age < timedelta(hours=24)
        except (ValueError, TypeError, KeyError):
            return False
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Retourne les données de secours"""
        fb = self.FALLBACK_DATA
        
        return {
            'success': True,
            'id': 'fallback_gini',
            'name': fb['name'],
            'value': fb['value'],
            'previous_value': fb['value'],
            'change': 0,
            'change_percent': 0,
            'unit': fb['unit'],
            'period': fb['period'],
            'source': fb['source'],
            'description': fb['description'],
            'category': 'inequality',
            'reliability': 'fallback',
            'last_update': datetime.now().isoformat(),
            'interpretation': self._interpret_gini(fb['value']),
            'note': 'Données de référence - sources temporairement indisponibles'
        }
    
    def force_refresh(self) -> Dict[str, Any]:
        """Force le rafraîchissement (ignore cache)"""
        logger.info("🔄 Rafraîchissement forcé GINI")
        
        # Essayer toutes les sources
        eurostat_data = self._fetch_from_eurostat()
        if eurostat_data:
            self._save_to_cache(eurostat_data)
            return eurostat_data
        
        worldbank_data = self._fetch_from_worldbank()
        if worldbank_data:
            self._save_to_cache(worldbank_data)
            return worldbank_data
        
        return self._get_fallback_data()


# Test du module
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    scraper = GINIScraper()
    data = scraper.get_gini_data()
    
    print("=" * 60)
    print("📊 INDICE GINI (Inégalités)")
    print("=" * 60)
    
    if data.get('success'):
        print(f"\n{data['name']}: {data['value']} {data['unit']}")
        print(f"Période: {data['period']}")
        print(f"Source: {data['source']}")
        print(f"Fiabilité: {data.get('reliability', 'N/A')}")
        print(f"Interprétation: {data.get('interpretation', 'N/A')}")
        
        if 'change' in data and data['change'] != 0:
            change_sign = "+" if data['change'] > 0 else ""
            print(f"Variation: {change_sign}{data['change']} points")
        
        if 'note' in data:
            print(f"Note: {data['note']}")
        
        print(f"\nDernière mise à jour: {data.get('last_update', 'N/A')}")
    else:
        print("❌ Erreur récupération données")