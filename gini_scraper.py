# Flask/gini_scraper.py
"""
Scraper amélioré pour l'indice GINI avec sources multiples
Sources prioritaires: Eurostat API, Data.gouv.fr, World Bank
"""

import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json
import os
import re
import csv
from io import StringIO

logger = logging.getLogger(__name__)


class GINIScraper:
    """Scraper amélioré pour l'indice GINI"""
    
    # Sources multiples avec priorités
    SOURCES = {
        'eurostat': {
            'name': 'Eurostat',
            'url': "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ilc_di12",
            'params': {
                'format': 'JSON',
                'lang': 'EN',
                'geo': 'FR',
                'precision': 1,
                'lastTimePeriod': 10  # 10 dernières années
            },
            'priority': 1
        },
        'data_gouv': {
            'name': 'Data.gouv.fr',
            'url': "https://www.data.gouv.fr/fr/datasets/r/44d2fa1e-6fd9-4d1d-82b8-d72545d17dfa",
            'type': 'csv',
            'priority': 2
        },
        'worldbank': {
            'name': 'Banque Mondiale',
            'url': "https://api.worldbank.org/v2/country/FRA/indicator/SI.POV.GINI",
            'params': {
                'format': 'json',
                'per_page': 20,
                'date': '2010:2024'
            },
            'priority': 3
        },
        'oecd': {
            'name': 'OECD',
            'url': "https://stats.oecd.org/SDMX-JSON/data/IDD/.GINI.../FRA",
            'params': {
                'dimensionAtObservation': 'AllDimensions',
                'detail': 'Full',
                'startTime': 2010,
                'endTime': 2024
            },
            'priority': 4
        }
    }
    
    def __init__(self, cache_dir: str = 'instance/cache'):
        self.cache_dir = cache_dir
        self.cache_file = os.path.join(cache_dir, 'gini_data.json')
        os.makedirs(cache_dir, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json,text/csv',
            'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8'
        })
        logger.info("[OK] GINIScraper amélioré initialisé")
    
    def get_gini_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Récupère l'indice GINI avec système de cache intelligent
        """
        # 1. Vérifier le cache (sauf si force_refresh)
        if not force_refresh:
            cached = self._load_cache()
            if cached and self._is_cache_valid(cached):
                logger.info("📦 Utilisation données GINI depuis cache")
                return cached
        
        # 2. Essayer toutes les sources par ordre de priorité
        sources_sorted = sorted(
            self.SOURCES.items(),
            key=lambda x: x[1].get('priority', 999)
        )
        
        latest_data = None
        for source_key, source_config in sources_sorted:
            try:
                logger.info(f"[SEARCH] Tentative source: {source_config['name']}")
                data = self._fetch_from_source(source_key, source_config)
                
                if data and self._validate_gini_data(data):
                    if not latest_data or self._is_data_newer(data, latest_data):
                        latest_data = data
                        logger.info(f"[OK] Données valides de {source_config['name']}")
                        
                        # Si haute priorité et données récentes, on s'arrête
                        if source_config.get('priority', 999) <= 2:
                            break
            except Exception as e:
                logger.warning(f"[WARN] Erreur source {source_key}: {e}")
                continue
        
        # 3. Si aucune donnée fraîche, vérifier cache expiré
        if not latest_data:
            cached = self._load_cache()
            if cached:
                logger.warning("[WARN] Utilisation cache expiré")
                cached['note'] = 'Cache expiré - sources indisponibles'
                return cached
            return self._get_fallback_data()
        
        # 4. Enrichir et sauvegarder les données
        enriched_data = self._enrich_data(latest_data)
        self._save_cache(enriched_data)
        
        return enriched_data
    
    def _fetch_from_source(self, source_key: str, config: Dict) -> Optional[Dict]:
        """Récupère les données depuis une source spécifique"""
        try:
            if source_key == 'eurostat':
                return self._fetch_eurostat(config)
            elif source_key == 'data_gouv':
                return self._fetch_data_gouv(config)
            elif source_key == 'worldbank':
                return self._fetch_worldbank(config)
            elif source_key == 'oecd':
                return self._fetch_oecd(config)
        except Exception as e:
            logger.error(f"Erreur source {source_key}: {e}")
            return None
    
    def _fetch_eurostat(self, config: Dict) -> Optional[Dict]:
        """Récupère depuis Eurostat API"""
        try:
            response = self.session.get(
                config['url'],
                params=config.get('params', {}),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_eurostat(data)
        except Exception as e:
            logger.error(f"Eurostat error: {e}")
        return None
    
    def _parse_eurostat(self, data: Dict) -> Optional[Dict]:
        """Parse les données Eurostat"""
        try:
            values = data.get('value', {})
            dimensions = data.get('dimension', {}).get('time', {}).get('category', {}).get('index', {})
            
            if not values or not dimensions:
                return None
            
            # Convertir les indexes en années
            year_mapping = {idx: year for year, idx in dimensions.items()}
            
            # Récupérer toutes les valeurs
            gini_values = []
            for idx_str, value in values.items():
                try:
                    idx = int(idx_str)
                    year = year_mapping.get(str(idx))
                    if year and value:
                        gini_values.append({
                            'year': int(year),
                            'value': float(value)
                        })
                except:
                    continue
            
            if not gini_values:
                return None
            
            # Trier et retourner les plus récentes
            gini_values.sort(key=lambda x: x['year'], reverse=True)
            
            result = {
                'values': gini_values[:5],  # 5 dernières années
                'source': 'Eurostat',
                'retrieved_at': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Parse Eurostat error: {e}")
            return None
    
    def _fetch_data_gouv(self, config: Dict) -> Optional[Dict]:
        """Récupère depuis Data.gouv.fr"""
        try:
            response = self.session.get(config['url'], timeout=10)
            
            if response.status_code == 200:
                if config.get('type') == 'csv':
                    # Lire le CSV
                    csv_content = StringIO(response.text)
                    reader = csv.DictReader(csv_content)
                    
                    gini_values = []
                    for row in reader:
                        # Chercher les colonnes pertinentes
                        for key, value in row.items():
                            if 'gini' in key.lower() and value:
                                try:
                                    year_match = re.search(r'\d{4}', key)
                                    year = int(year_match.group()) if year_match else None
                                    
                                    if year and 2000 <= year <= 2025:
                                        gini_values.append({
                                            'year': year,
                                            'value': float(value.replace(',', '.'))
                                        })
                                except:
                                    continue
                    
                    if gini_values:
                        gini_values.sort(key=lambda x: x['year'], reverse=True)
                        return {
                            'values': gini_values[:5],
                            'source': 'Data.gouv.fr',
                            'retrieved_at': datetime.now().isoformat()
                        }
        
        except Exception as e:
            logger.error(f"Data.gouv error: {e}")
        
        return None
    
    def _fetch_worldbank(self, config: Dict) -> Optional[Dict]:
        """Récupère depuis World Bank"""
        try:
            response = self.session.get(
                config['url'],
                params=config.get('params', {}),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if len(data) > 1 and isinstance(data[1], list):
                    indicators = data[1]
                    
                    gini_values = []
                    for item in indicators:
                        if item.get('value'):
                            try:
                                gini_values.append({
                                    'year': int(item.get('date')),
                                    'value': float(item.get('value'))
                                })
                            except:
                                continue
                    
                    if gini_values:
                        gini_values.sort(key=lambda x: x['year'], reverse=True)
                        return {
                            'values': gini_values[:5],
                            'source': 'World Bank',
                            'retrieved_at': datetime.now().isoformat()
                        }
        
        except Exception as e:
            logger.error(f"World Bank error: {e}")
        
        return None
    
    def _fetch_oecd(self, config: Dict) -> Optional[Dict]:
        """Récupère depuis OECD API"""
        try:
            response = self.session.get(
                config['url'],
                params=config.get('params', {}),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse JSON complexe de l'OCDE
                gini_values = []
                try:
                    observations = data.get('dataSets', [{}])[0].get('observations', {})
                    
                    for key, value in observations.items():
                        parts = key.split(':')
                        if len(parts) >= 3 and value:
                            try:
                                year = 2010 + int(parts[1])  # Ajuster selon la structure
                                gini_values.append({
                                    'year': year,
                                    'value': float(value[0])
                                })
                            except:
                                continue
                    
                    if gini_values:
                        gini_values.sort(key=lambda x: x['year'], reverse=True)
                        return {
                            'values': gini_values[:5],
                            'source': 'OECD',
                            'retrieved_at': datetime.now().isoformat()
                        }
                except:
                    pass
        
        except Exception as e:
            logger.error(f"OECD error: {e}")
        
        return None
    
    def _validate_gini_data(self, data: Dict) -> bool:
        """Valide les données GINI"""
        try:
            if not data.get('values'):
                return False
            
            # Vérifier au moins une valeur
            values = data['values']
            if not values or len(values) == 0:
                return False
            
            # Vérifier la plage des valeurs
            for item in values:
                value = item.get('value')
                if not (0 <= value <= 100):
                    return False
            
            return True
        except:
            return False
    
    def _is_data_newer(self, new_data: Dict, old_data: Dict) -> bool:
        """Compare la fraîcheur des données"""
        try:
            new_latest = max(item['year'] for item in new_data['values'])
            old_latest = max(item['year'] for item in old_data['values'])
            return new_latest > old_latest
        except:
            return True
    
    def _enrich_data(self, raw_data: Dict) -> Dict[str, Any]:
        """Enrichit les données avec des métadonnées"""
        values = raw_data['values']
        
        if len(values) >= 2:
            latest = values[0]
            previous = values[1]
            
            change = latest['value'] - previous['value']
            change_percent = (change / previous['value'] * 100) if previous['value'] != 0 else 0
        else:
            latest = values[0]
            previous = latest
            change = 0
            change_percent = 0
        
        return {
            'success': True,
            'id': 'gini_index',
            'name': 'Indice GINI (inégalités de revenus)',
            'value': round(latest['value'], 1),
            'previous_value': round(previous['value'], 1),
            'change': round(change, 2),
            'change_percent': round(change_percent, 1),
            'unit': 'Points (0-100)',
            'period': str(latest['year']),
            'previous_period': str(previous['year']),
            'source': raw_data['source'],
            'description': 'Coefficient de GINI mesurant les inégalités de revenus',
            'category': 'inequality',
            'reliability': 'official',
            'last_update': raw_data['retrieved_at'],
            'interpretation': self._interpret_gini(latest['value']),
            'historical_values': values,
            'note': f'Données {raw_data["source"]} - Actualisé quotidiennement'
        }
    
    def _interpret_gini(self, value: float) -> str:
        """Interprète la valeur du GINI"""
        if value < 25:
            return "Inégalités très faibles (société égalitaire)"
        elif value < 30:
            return "Inégalités faibles (pays nordiques typiques)"
        elif value < 35:
            return "Inégalités modérées (France, Allemagne)"
        elif value < 40:
            return "Inégalités élevées (USA, UK)"
        else:
            return "Inégalités très élevées (pays émergents)"
    
    def _load_cache(self) -> Optional[Dict]:
        """Charge depuis le cache"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if data.get('last_update'):
                    cache_time = datetime.fromisoformat(data['last_update'])
                    if datetime.now() - cache_time < timedelta(days=1):
                        return data
        except Exception as e:
            logger.warning(f"Cache load error: {e}")
        
        return None
    
    def _save_cache(self, data: Dict):
        """Sauvegarde dans le cache"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Cache save error: {e}")
    
    def _is_cache_valid(self, cached_data: Dict) -> bool:
        """Vérifie si le cache est valide (< 24h)"""
        try:
            last_update = datetime.fromisoformat(cached_data['last_update'])
            return datetime.now() - last_update < timedelta(hours=24)
        except:
            return False
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Données de secours avec historique"""
        historical = [
            {'year': 2022, 'value': 29.8},
            {'year': 2021, 'value': 29.3},
            {'year': 2020, 'value': 29.5},
            {'year': 2019, 'value': 29.2},
            {'year': 2018, 'value': 28.9}
        ]
        
        return {
            'success': True,
            'id': 'fallback_gini',
            'name': 'Indice GINI (inégalités)',
            'value': 29.8,
            'previous_value': 29.3,
            'change': 0.5,
            'change_percent': 1.7,
            'unit': 'Points (0-100)',
            'period': '2022',
            'previous_period': '2021',
            'source': 'INSEE - Données de référence',
            'description': 'Coefficient de GINI - Mesure des inégalités de revenus',
            'category': 'inequality',
            'reliability': 'estimated',
            'last_update': datetime.now().isoformat(),
            'interpretation': self._interpret_gini(29.8),
            'historical_values': historical,
            'note': 'Données de référence - sources primaires temporairement indisponibles'
        }
    
    def force_refresh(self) -> Dict[str, Any]:
        """Force le rafraîchissement des données"""
        return self.get_gini_data(force_refresh=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    scraper = GINIScraper()
    data = scraper.get_gini_data()
    
    print("\n" + "="*60)
    print("[DATA] INDICE GINI - DONNÉES AMÉLIORÉES")
    print("="*60)
    
    if data.get('success'):
        print(f"\n{data['name']}: {data['value']} {data['unit']}")
        print(f"Période: {data['period']} (précédent: {data['previous_period']})")
        print(f"Source: {data['source']}")
        print(f"Variation: {data['change']:+} points ({data['change_percent']:+}%)")
        print(f"Interprétation: {data['interpretation']}")
        
        print(f"\n[CHART] Historique récent:")
        for item in data.get('historical_values', [])[:3]:
            print(f"  {item['year']}: {item['value']}")
        
        print(f"\n🕒 Dernière mise à jour: {data['last_update'][:16].replace('T', ' ')}")
        print(f"[NOTE] Note: {data.get('note', '')}")
    else:
        print("[ERROR] Erreur de récupération")