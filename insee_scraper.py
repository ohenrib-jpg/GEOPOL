# Flask/insee_scraper.py
"""
Scraper léger et respectueux pour les indicateurs clés INSEE
Récupère inflation, chômage et croissance depuis la page d'accueil
Usage éducatif - 1 requête par jour maximum
"""

import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json
import re
import os

logger = logging.getLogger(__name__)


class INSEEScraper:
    """Scraper pour les indicateurs clés INSEE"""
    
    INSEE_URL = "https://www.insee.fr/fr/accueil"
    CACHE_DURATION_HOURS = 24  # Cache 24h
    
    # Fallback values (dernières données connues)
    FALLBACK_DATA = {
        'inflation': {
            'value': 2.1,
            'period': '2024-12',
            'name': 'Inflation (glissement annuel)',
            'unit': '%'
        },
        'unemployment': {
            'value': 7.4,
            'period': '2024-Q3',
            'name': 'Taux de chômage',
            'unit': '%'
        },
        'growth': {
            'value': 0.9,
            'period': '2024-Q4',
            'name': 'Croissance du PIB',
            'unit': '% (variation trimestrielle)'
        }
    }
    
    def __init__(self, cache_file: str = 'instance/insee_cache.json'):
        self.cache_file = cache_file
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
        logger.info("✅ INSEEScraper initialisé")
    
    def get_indicators(self) -> Dict[str, Any]:
        """
        Récupère les 3 indicateurs clés INSEE
        Avec système de cache intelligent
        """
        # Vérifier le cache d'abord
        cached_data = self._load_from_cache()
        if cached_data and self._is_cache_valid(cached_data):
            logger.info("📦 Utilisation données INSEE depuis cache")
            cached_data['source'] = 'Cache INSEE'
            return cached_data
        
        # Tenter de scraper les nouvelles données
        try:
            logger.info("🌐 Récupération données INSEE depuis le site...")
            fresh_data = self._scrape_insee_homepage()
            
            if fresh_data and self._validate_data(fresh_data):
                self._save_to_cache(fresh_data)
                logger.info("✅ Données INSEE fraîches récupérées")
                return fresh_data
            else:
                logger.warning("⚠️ Données scrapées invalides, utilisation fallback")
                fallback_data = self._get_fallback_data()
                fallback_data['note'] = 'Données scrapées invalides - utilisation fallback'
                return fallback_data
        
        except Exception as e:
            logger.error(f"❌ Erreur scraping INSEE: {e}")
            # Retourner le cache même expiré ou fallback
            if cached_data:
                logger.info("📦 Utilisation cache expiré en secours")
                cached_data['note'] = f'Cache expiré - erreur scraping: {str(e)[:50]}'
                return cached_data
            else:
                logger.info("🔄 Utilisation données fallback")
                fallback_data = self._get_fallback_data()
                fallback_data['note'] = f'Erreur scraping - fallback: {str(e)[:50]}'
                return fallback_data
    
    def _scrape_insee_homepage(self) -> Optional[Dict[str, Any]]:
        """
        Scrape la page d'accueil INSEE pour extraire les indicateurs
        Méthode respectueuse : 1 seule requête, timeout court
        """
        try:
            response = self.session.get(
                self.INSEE_URL,
                timeout=20,
                allow_redirects=True,
                verify=True
            )
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Status code INSEE: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Nouvelle stratégie : recherche des cartes de chiffres clés
            indicators = self._extract_from_modern_layout(soup)
            
            # Si pas assez d'indicateurs, essayer l'ancienne méthode
            if len(indicators) < 2:
                logger.info("Essai extraction avec méthode alternative")
                alternative_indicators = self._extract_alternative_method(soup)
                indicators.update(alternative_indicators)
            
            # Nettoyer et valider les indicateurs
            cleaned_indicators = {}
            for key, data in indicators.items():
                if data and isinstance(data, dict) and 'value' in data and data['value'] is not None:
                    try:
                        # Convertir la valeur en float si c'est une string
                        if isinstance(data['value'], str):
                            clean_match = re.search(r'([+-]?\d+[,\.]?\d*)', data['value'])
                            if clean_match:
                                clean_value = float(clean_match.group(1).replace(',', '.'))
                            else:
                                continue
                        else:
                            clean_value = float(data['value'])
                        
                        # Validation
                        if self._is_value_reasonable(clean_value, key):
                            data['value'] = clean_value
                            cleaned_indicators[key] = data
                        else:
                            logger.warning(f"⚠️ Valeur aberrante pour {key}: {clean_value}")
                    except Exception as e:
                        logger.warning(f"⚠️ Erreur traitement valeur {key}: {e}")
                        continue
            
            if cleaned_indicators:
                return {
                    'success': True,
                    'indicators': cleaned_indicators,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'INSEE scraping direct',
                    'scraped_url': self.INSEE_URL,
                    'note': 'Données extraites de la page d\'accueil INSEE'
                }
            else:
                return None
            
        except Exception as e:
            logger.error(f"❌ Erreur scraping: {e}")
            return None
    
    def _extract_from_modern_layout(self, soup) -> Dict[str, Dict]:
        """Extraction depuis la mise en page moderne d'INSEE"""
        indicators = {}
        
        # Recherche des sections de chiffres clés
        sections = soup.find_all(['section', 'div', 'article'], 
                                class_=re.compile(r'(chiffre|figure|indicateur|key|stat|data|valeur)', re.I))
        
        for section in sections:
            text_content = section.get_text(strip=True, separator=' ')
            lower_content = text_content.lower()
            
            # Vérifier si c'est un élément contenant des chiffres
            if len(text_content) < 200:  # Éviter les grands textes
                # Inflation
                if any(keyword in lower_content for keyword in ['inflation', 'ipc', 'prix', 'consommation', 'hausse', 'indice']):
                    if 'inflation' not in indicators:  # Prendre la première occurrence
                        value = self._extract_numeric_value(text_content)
                        if value is not None:
                            indicators['inflation'] = {
                                'value': value,
                                'period': self._extract_period_from_text(text_content),
                                'name': 'Inflation (glissement annuel)',
                                'unit': '%',
                                'source': 'INSEE homepage',
                                'confidence': 'medium'
                            }
                
                # Chômage
                elif any(keyword in lower_content for keyword in ['chômage', 'chomage', 'emploi', 'actifs', 'taux']):
                    if 'unemployment' not in indicators:
                        value = self._extract_numeric_value(text_content)
                        if value is not None:
                            indicators['unemployment'] = {
                                'value': value,
                                'period': self._extract_period_from_text(text_content),
                                'name': 'Taux de chômage',
                                'unit': '%',
                                'source': 'INSEE homepage',
                                'confidence': 'medium'
                            }
                
                # Croissance
                elif any(keyword in lower_content for keyword in ['croissance', 'pib', 'gdp', 'produit', 'variation']):
                    if 'growth' not in indicators:
                        value = self._extract_numeric_value(text_content)
                        if value is not None:
                            indicators['growth'] = {
                                'value': value,
                                'period': self._extract_period_from_text(text_content),
                                'name': 'Croissance du PIB',
                                'unit': '% (variation trimestrielle)',
                                'source': 'INSEE homepage',
                                'confidence': 'medium'
                            }
        
        return indicators
    
    def _extract_alternative_method(self, soup) -> Dict[str, Dict]:
        """Méthode alternative d'extraction"""
        indicators = {}
        all_text = soup.get_text()
        
        # Patterns améliorés
        patterns = {
            'inflation': [
                r'inflation.*?(\d+[,\.]\d+)\s*%',
                r'(\d+[,\.]\d+)\s*%.*?inflation',
                r'ipc.*?(\d+[,\.]\d+)\s*%'
            ],
            'unemployment': [
                r'chômage.*?(\d+[,\.]\d+)\s*%',
                r'taux.*?chômage.*?(\d+[,\.]\d+)\s*%',
                r'(\d+[,\.]\d+)\s*%.*?chômage'
            ],
            'growth': [
                r'croissance.*?pib.*?([+-]?\d+[,\.]\d+)\s*%',
                r'pib.*?([+-]?\d+[,\.]\d+)\s*%.*?croissance',
                r'variation.*?pib.*?([+-]?\d+[,\.]\d+)\s*%'
            ]
        }
        
        for indicator_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, all_text, re.IGNORECASE | re.DOTALL)
                if matches:
                    # Prendre la dernière occurrence (la plus récente)
                    try:
                        value_str = matches[-1]
                        value = float(value_str.replace(',', '.'))
                        if self._is_value_reasonable(value, indicator_type):
                            indicators[indicator_type] = {
                                'value': value,
                                'period': self._extract_current_period(),
                                'name': {
                                    'inflation': 'Inflation (glissement annuel)',
                                    'unemployment': 'Taux de chômage',
                                    'growth': 'Croissance du PIB'
                                }[indicator_type],
                                'unit': '%',
                                'source': 'INSEE text mining',
                                'confidence': 'low'
                            }
                            break
                    except Exception as e:
                        logger.warning(f"Erreur extraction {indicator_type}: {e}")
        
        return indicators
    
    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """Extrait une valeur numérique d'un texte"""
        patterns = [
            r'([+-]?\d+[,\.]\d+)\s*%',
            r'([+-]?\d+[,\.]\d+)',
            r'([+-]?\d+)\s*%'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    value_str = match.group(1).replace(',', '.')
                    return float(value_str)
                except:
                    continue
        return None
    
    def _extract_period_from_text(self, text: str) -> str:
        """Extrait la période depuis un texte"""
        # Patterns pour dates
        date_patterns = [
            r'(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(\d{4})',
            r'T[1-4]\s+(\d{4})',
            r'(\d{4})[-–]\s*T[1-4]',
            r'(\d{4})[-–]Q[1-4]',
            r'(\d{2}/\d{4})',
            r'(\d{4}-\d{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        
        # Par défaut, retourner période actuelle
        return self._extract_current_period()
    
    def _is_value_reasonable(self, value: float, indicator_type: str) -> bool:
        """Vérifie si une valeur est raisonnable"""
        ranges = {
            'inflation': (-2, 15),      # Inflation (déflation à inflation élevée)
            'unemployment': (0, 30),     # Chômage (0% à 30%)
            'growth': (-15, 15)          # Croissance (-15% à +15%)
        }
        
        if indicator_type in ranges:
            min_val, max_val = ranges[indicator_type]
            return min_val <= value <= max_val
        return True
    
    def _extract_current_period(self) -> str:
        """Période actuelle par défaut"""
        now = datetime.now()
        # Retourner le trimestre précédent pour plus de réalisme
        quarter = (now.month - 1) // 3 + 1
        year = now.year
        if quarter == 0:
            quarter = 4
            year -= 1
        return f"{year}-Q{quarter}"
    
    def _validate_data(self, data: Dict) -> bool:
        """Valide les données"""
        if not data or not data.get('success'):
            return False
        
        indicators = data.get('indicators', {})
        
        # Au moins 1 indicateur valide
        if len(indicators) == 0:
            return False
        
        # Vérifier la structure
        for key, indicator in indicators.items():
            if not isinstance(indicator, dict):
                return False
            if 'value' not in indicator or 'name' not in indicator:
                return False
        
        return True
    
    def _load_from_cache(self) -> Optional[Dict]:
        """Charge depuis le cache"""
        try:
            if not os.path.exists(self.cache_file):
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Vérifier la structure
            if isinstance(data, dict) and data.get('success'):
                return data
            elif 'indicators' in data:
                # Ancien format
                return {
                    'success': True,
                    'indicators': data.get('indicators', {}),
                    'timestamp': data.get('timestamp', datetime.now().isoformat()),
                    'source': 'Cache converti'
                }
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
            logger.info("💾 Cache INSEE sauvegardé")
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache: {e}")
    
    def _is_cache_valid(self, cached_data: Dict) -> bool:
        """Vérifie la validité du cache"""
        try:
            timestamp = cached_data.get('timestamp')
            if not timestamp:
                return False
            
            cache_time = datetime.fromisoformat(timestamp)
            age = datetime.now() - cache_time
            return age < timedelta(hours=self.CACHE_DURATION_HOURS)
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Erreur validation cache: {e}")
            return False
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Données de secours"""
        return {
            'success': True,
            'indicators': self.FALLBACK_DATA.copy(),
            'timestamp': datetime.now().isoformat(),
            'source': 'Fallback INSEE',
            'note': 'Données de référence - site INSEE temporairement indisponible'
        }
    
    def force_refresh(self) -> Dict[str, Any]:
        """Force un rafraîchissement"""
        logger.info("🔄 Rafraîchissement forcé INSEE")
        try:
            data = self._scrape_insee_homepage()
            if data and self._validate_data(data):
                self._save_to_cache(data)
                return data
        except Exception as e:
            logger.error(f"Erreur rafraîchissement: {e}")
        
        return self._get_fallback_data()


# Test
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    scraper = INSEEScraper()
    data = scraper.get_indicators()
    
    print("=" * 60)
    print("📊 Indicateurs INSEE")
    print("=" * 60)
    
    if data.get('success'):
        print(f"Source: {data.get('source', 'N/A')}")
        print(f"Timestamp: {data.get('timestamp', 'N/A')}")
        
        if 'note' in data:
            print(f"Note: {data['note']}")
        
        for key, indicator in data['indicators'].items():
            print(f"\n{indicator['name']}: {indicator['value']} {indicator['unit']}")
            print(f"  Période: {indicator.get('period', 'N/A')}")
            print(f"  Source: {indicator.get('source', 'N/A')}")
            if 'confidence' in indicator:
                print(f"  Confiance: {indicator['confidence']}")
    else:
        print("❌ Erreur récupération données")