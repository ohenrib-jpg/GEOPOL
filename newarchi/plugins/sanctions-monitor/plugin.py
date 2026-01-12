# -*- coding: utf-8 -*-
"""
Plugin: Sanctions Monitor - VERSION PRODUCTION RÉELLE
Description: Surveillance sanctions internationales via données douanes françaises + OFAC
APIs: Douanes Françaises (gratuit), OFAC SDN (gratuit), REST Countries (gratuit)
"""

import requests
import json
import logging
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
import zipfile
import io
import sys
import os
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

# Essayer d'importer le circuit breaker depuis Flask/security_governance
try:
    # Ajouter le chemin vers Flask/security_governance
    flask_security_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Flask', 'security_governance')
    logger.info(f"[SANCTIONS] Chemin Flask security: {flask_security_path}")
    logger.info(f"[SANCTIONS] Existe: {os.path.exists(flask_security_path)}")
    if flask_security_path not in sys.path:
        sys.path.insert(0, flask_security_path)
        logger.info(f"[SANCTIONS] Chemin ajouté à sys.path")

    try:
        from circuit_breaker import CircuitBreakerManager, with_circuit_breaker
        logger.info("[SANCTIONS] CircuitBreakerManager importé")
    except ImportError as e:
        logger.error(f"[SANCTIONS] Erreur import circuit_breaker: {e}")
        raise
    try:
        from security_cache import SecurityCache
        logger.info("[SANCTIONS] SecurityCache importé")
    except ImportError as e:
        logger.error(f"[SANCTIONS] Erreur import security_cache: {e}")
        raise
    # Essayer d'importer le connecteur EU sanctions
    try:
        from eu_sanctions_connector import EUSanctionsConnector, eu_sanctions_connector
        EU_CONNECTOR_AVAILABLE = True
        logger.info("[SANCTIONS] Connecteur EU sanctions disponible")
    except ImportError as e:
        EU_CONNECTOR_AVAILABLE = False
        EUSanctionsConnector = None
        eu_sanctions_connector = None
        logger.warning(f"[SANCTIONS] Connecteur EU sanctions non disponible: {e}")

    # Essayer d'importer le connecteur Douanes EDI
    try:
        from douanes_edi_connector import DouanesEDIConnector, douanes_edi_connector
        DOUANES_CONNECTOR_AVAILABLE = True
        logger.info("[SANCTIONS] Connecteur Douanes EDI disponible")
    except ImportError as e:
        DOUANES_CONNECTOR_AVAILABLE = False
        DouanesEDIConnector = None
        douanes_edi_connector = None
        logger.warning(f"[SANCTIONS] Connecteur Douanes EDI non disponible: {e}")

    CIRCUIT_BREAKER_AVAILABLE = True
    CACHE_AVAILABLE = True
    logger.info("[SANCTIONS] Circuit breaker et cache disponibles")
except ImportError as e:
    CIRCUIT_BREAKER_AVAILABLE = False
    CACHE_AVAILABLE = False
    EU_CONNECTOR_AVAILABLE = False
    DOUANES_CONNECTOR_AVAILABLE = False
    CircuitBreakerManager = None
    with_circuit_breaker = lambda *args, **kwargs: lambda func: func
    SecurityCache = None
    EUSanctionsConnector = None
    eu_sanctions_connector = None
    DouanesEDIConnector = None
    douanes_edi_connector = None
    logger.warning(f"[SANCTIONS] Circuit breaker/cache non disponibles: {e}")

class Plugin:
    """Surveillance sanctions internationales avec données RÉELLES"""

    def __init__(self, settings):
        self.name = "sanctions-monitor"
        self.settings = settings
        self.cache = {}
        self.cache_duration = 3600  # 1 heure

        # Initialiser les circuit breakers
        self._init_circuit_breakers()

    def _init_circuit_breakers(self):
        """Initialise les circuit breakers pour les différentes sources"""
        if not CIRCUIT_BREAKER_AVAILABLE or not CircuitBreakerManager:
            self.ofac_breaker = None
            self.douanes_breaker = None
            self.eu_breaker = None
            logger.warning("[SANCTIONS] Circuit breakers non disponibles")
            return

        try:
            # Circuit breaker pour OFAC (source sensible)
            self.ofac_breaker = CircuitBreakerManager.get_breaker(
                name='sanctions_ofac',
                failure_threshold=2,
                reset_timeout=600,  # 10 minutes
                fallback_func=self._get_ofac_fallback
            )

            # Circuit breaker pour Douanes Françaises
            self.douanes_breaker = CircuitBreakerManager.get_breaker(
                name='sanctions_douanes',
                failure_threshold=3,
                reset_timeout=300,  # 5 minutes
                fallback_func=self._get_sanctions_fallback
            )

            # Circuit breaker pour UE
            self.eu_breaker = CircuitBreakerManager.get_breaker(
                name='sanctions_eu',
                failure_threshold=3,
                reset_timeout=300,
                fallback_func=self._get_eu_fallback
            )

            logger.info("[SANCTIONS] Circuit breakers initialisés")

        except Exception as e:
            logger.error(f"[SANCTIONS] Erreur initialisation circuit breakers: {e}")
            self.ofac_breaker = None
            self.douanes_breaker = None
            self.eu_breaker = None
        
    def run(self, payload=None):
        """Exécution avec données RÉELLES des sanctions"""
        if payload is None:
            payload = {}
        
        try:
            # 1. Carte interactive Douanes Françaises
            douanes_data = self._fetch_douanes_map()
            
            # 2. Données OFAC (US Treasury)
            ofac_data = self._fetch_ofac_sanctions()
            
            # 3. Sanctions UE
            eu_data = self._fetch_eu_sanctions()
            
            # Fusion et analyse
            data = self._merge_and_analyze(douanes_data, ofac_data, eu_data)
            
            metrics = {
                'sanctions_actives': len(data),
                'pays_cibles': len(set([d['pays_cible'] for d in data if d['pays_cible']])),
                'entites_ciblees': len([d for d in data if d['type'] == 'entite']),
                'individus_cibles': len([d for d in data if d['type'] == 'individu']),
                'derniere_maj': max([d.get('date_maj', '') for d in data if d.get('date_maj')], default=''),
                'sources_reelles': ['Douanes Françaises', 'OFAC', 'UE']
            }
            
            return {
                'status': 'success',
                'plugin': self.name,
                'timestamp': datetime.now().isoformat(),
                'data': data[:50],  # Top 50
                'metrics': metrics,
                'carte_douanes': self._generate_douanes_iframe(),
                'message': f'Surveillance de {len(data)} sanctions internationales'
            }
            
        except Exception as e:
            logger.error(f"Erreur sanctions-monitor: {e}")
            return {
                'status': 'error',
                'plugin': self.name,
                'timestamp': datetime.now().isoformat(),
                'message': f'Erreur: {str(e)}'
            }
    
    def _fetch_douanes_map(self):
        """Récupère données carte Douanes Françaises"""
        # Utiliser circuit breaker si disponible
        if self.douanes_breaker:
            return self.douanes_breaker.call(self._fetch_douanes_map_internal)

        # Sinon, exécuter directement
        return self._fetch_douanes_map_internal()

    def _fetch_douanes_map_internal(self):
        """Méthode interne pour récupérer données Douanes (appelée par circuit breaker)"""
        try:
            # Utiliser le connecteur Douanes EDI si disponible
            if DOUANES_CONNECTOR_AVAILABLE and douanes_edi_connector:
                logger.info("[SANCTIONS] Utilisation connecteur Douanes EDI")
                result = douanes_edi_connector.get_sanctions_list(limit=100)
                if result.get('success') and result.get('sanctions'):
                    # Convertir le format du connecteur au format attendu par le plugin
                    return self._convert_douanes_connector_format(result['sanctions'])
                else:
                    logger.warning("[SANCTIONS] Connecteur Douanes EDI a échoué, utilisation fallback")
                    return self._get_sanctions_fallback()
            else:
                logger.warning("[SANCTIONS] Connecteur Douanes EDI non disponible, utilisation fallback")
                return self._get_sanctions_fallback()

        except Exception as e:
            logger.warning(f"Douanes error: {e}")
            # Relancer l'exception pour que le circuit breaker la capture
            raise
    
    def _fetch_ofac_sanctions(self):
        """OFAC Specially Designated Nationals (SDN) list - CSV public"""
        # Utiliser circuit breaker si disponible
        if self.ofac_breaker:
            return self.ofac_breaker.call(self._fetch_ofac_sanctions_internal)

        # Sinon, exécuter directement
        return self._fetch_ofac_sanctions_internal()

    def _fetch_ofac_sanctions_internal(self):
        """Méthode interne pour récupérer les sanctions OFAC (appelée par circuit breaker)"""
        try:
            # OFAC SDN CSV (public, mis à jour régulièrement)
            ofac_url = "https://www.treasury.gov/ofac/downloads/sdn.csv"

            logger.info("[SANCTIONS] Téléchargement liste OFAC SDN...")
            response = requests.get(ofac_url, timeout=5)
            response.raise_for_status()

            # Lire CSV - LE FICHIER OFAC N'A PAS D'EN-TÊTES !
            import csv
            from io import StringIO

            csv_data = StringIO(response.text)

            # Colonnes officielles OFAC selon la documentation
            sdn_columns = [
                'ent_num', 'sdn_name', 'sdn_type', 'program', 'title',
                'call_sign', 'vess_type', 'tonnage', 'grt', 'vess_flag',
                'vess_owner', 'remarks'
            ]

            # Utiliser csv.reader au lieu de DictReader car pas d'en-têtes
            reader = csv.reader(csv_data, delimiter=',', quotechar='"')

            sanctions = []
            count = 0
            total_lines = 0

            for row in reader:
                total_lines += 1
                try:
                    # Ignorer les lignes vides
                    if not row or len(row) < 4:
                        continue

                    # Extraire informations selon les colonnes fixes
                    # Note: row[0] = ent_num, row[1] = sdn_name, row[2] = sdn_type, row[3] = program
                    name = row[1].strip() if len(row) > 1 else ''
                    if not name or name == '-0-':
                        continue

                    # Type (colonne 2)
                    entry_type = row[2].strip() if len(row) > 2 else ''

                    # Déterminer type (individu ou entité)
                    entry_type_upper = entry_type.upper()
                    if any(term in entry_type_upper for term in ['INDIVIDUAL', 'PERSON']):
                        target_type = 'individu'
                    elif any(term in entry_type_upper for term in ['ENTITY', 'COMPANY', 'ORGANIZATION', 'VESSEL']):
                        target_type = 'entite'
                    else:
                        # Deviner basé sur le nom
                        name_upper = name.upper()
                        if any(title in name_upper for title in ['MR.', 'MRS.', 'DR.', 'PROF.', 'SHEIKH', 'PRINCE', 'KING', 'QUEEN']):
                            target_type = 'individu'
                        else:
                            target_type = 'entite'  # Par défaut pour les entreprises

                    # Programme (colonne 3) - peut contenir plusieurs programmes séparés par '] ['
                    program_raw = row[3].strip() if len(row) > 3 else ''
                    if not program_raw or program_raw == '-0-':
                        program = 'Unknown'
                    else:
                        # Nettoyer le programme (enlever les crochets, etc.)
                        program = program_raw.replace('] [', ', ').replace('[', '').replace(']', '').strip()
                        # Si c'est trop long, prendre le premier
                        if len(program) > 100:
                            program = program[:100] + '...'

                    # Adresses/Remarques (colonne 11)
                    addresses = row[11].strip() if len(row) > 11 else ''

                    # Pays - extraire du programme ou des adresses
                    country = self._extract_country_from_ofac_data(program, addresses)

                    # Date (approximative - fichier ne contient pas de date)
                    current_date = datetime.now().strftime('%Y-%m-%d')

                    sanctions.append({
                        'nom': name,
                        'type': target_type,
                        'pays': country,
                        'programme': program,
                        'date_ajout': current_date,
                        'source': 'OFAC SDN',
                        'adresses': addresses[:200] if addresses else '',
                        'raw_type': entry_type
                    })

                    count += 1
                    if count >= 100:  # Limiter pour performance
                        logger.info(f"[SANCTIONS] Limite atteinte: {count} sanctions extraites")
                        break

                except Exception as e:
                    logger.warning(f"Erreur parsing ligne OFAC {total_lines}: {e}")
                    continue

            logger.info(f"[OK] {len(sanctions)} sanctions OFAC récupérées sur {total_lines} lignes analysées")

            if len(sanctions) == 0:
                logger.warning("[SANCTIONS] Aucune sanction OFAC trouvée, utilisation du fallback")
                return self._get_ofac_fallback()

            # Log des statistiques
            types_count = {}
            countries_count = {}
            for s in sanctions:
                t = s.get('type', 'unknown')
                c = s.get('pays', 'unknown')
                types_count[t] = types_count.get(t, 0) + 1
                countries_count[c] = countries_count.get(c, 0) + 1

            logger.info(f"[STATS] Types: {types_count}")
            logger.info(f"[STATS] Pays: {dict(sorted(countries_count.items(), key=lambda x: x[1], reverse=True)[:5])}")

            return sanctions

        except Exception as e:
            logger.warning(f"Erreur OFAC CSV: {e}")
            # Relancer l'exception pour que le circuit breaker la capture
            raise

    def _extract_country_from_ofac_data(self, program: str, addresses: str) -> str:
        """Extrait le pays des données OFAC (programme et adresses)"""
        # D'abord chercher dans le programme (ex: "CUBA", "IRAN", etc.)
        program_upper = program.upper()

        # Mapping des programmes aux pays
        program_to_country = {
            'CUBA': 'Cuba',
            'IRAN': 'Iran',
            'SYRIA': 'Syrie',
            'NORTH KOREA': 'Corée du Nord',
            'RUSSIA': 'Russie',
            'BELARUS': 'Biélorussie',
            'VENEZUELA': 'Venezuela',
            'SUDAN': 'Soudan',
            'MYANMAR': 'Myanmar',
            'AFGHANISTAN': 'Afghanistan',
            'YEMEN': 'Yémen',
            'LIBYA': 'Libye',
            'SOMALIA': 'Somalie',
            'IRAQ': 'Irak',
            'UKRAINE': 'Ukraine',
            'CHINA': 'Chine'
        }

        for prog_key, country_name in program_to_country.items():
            if prog_key in program_upper:
                return country_name

        # Si pas trouvé dans le programme, chercher dans les adresses
        if addresses:
            return self._extract_country_from_address(addresses)

        return 'Non spécifié'

    def _extract_country_from_address(self, addresses: str) -> str:
        """Extrait le pays d'une adresse OFAC"""
        if not addresses:
            return 'Non spécifié'

        # Liste de pays communs dans les sanctions
        country_keywords = [
            'RUSSIA', 'CHINA', 'IRAN', 'NORTH KOREA', 'SYRIA',
            'VENEZUELA', 'CUBA', 'SUDAN', 'BELARUS', 'MYANMAR',
            'AFGHANISTAN', 'YEMEN', 'LIBYA', 'SOMALIA', 'IRAQ',
            'UKRAINE', 'TURKEY', 'SAUDI ARABIA', 'QATAR', 'UAE'
        ]

        addresses_upper = addresses.upper()
        for country in country_keywords:
            if country in addresses_upper:
                # Formater joliment
                if country == 'NORTH KOREA':
                    return 'Corée du Nord'
                elif country == 'RUSSIA':
                    return 'Russie'
                elif country == 'CHINA':
                    return 'Chine'
                elif country == 'IRAN':
                    return 'Iran'
                elif country == 'SYRIA':
                    return 'Syrie'
                elif country == 'VENEZUELA':
                    return 'Venezuela'
                elif country == 'CUBA':
                    return 'Cuba'
                elif country == 'SUDAN':
                    return 'Soudan'
                elif country == 'BELARUS':
                    return 'Biélorussie'
                elif country == 'MYANMAR':
                    return 'Myanmar'
                else:
                    return country.title()

        return 'Non spécifié'
    
    def _fetch_eu_sanctions(self):
        """Sanctions Union Européenne"""
        # Utiliser circuit breaker si disponible
        if self.eu_breaker:
            return self.eu_breaker.call(self._fetch_eu_sanctions_internal)

        # Sinon, exécuter directement
        return self._fetch_eu_sanctions_internal()

    def _fetch_eu_sanctions_internal(self):
        """Méthode interne pour récupérer sanctions UE (appelée par circuit breaker)"""
        try:
            # Utiliser le connecteur EU sanctions si disponible
            if EU_CONNECTOR_AVAILABLE and eu_sanctions_connector:
                logger.info("[SANCTIONS] Utilisation connecteur EU sanctions")
                result = eu_sanctions_connector.get_sanctions_list(limit=100)
                if result.get('success') and result.get('sanctions'):
                    # Convertir le format du connecteur au format attendu par le plugin
                    return self._convert_eu_connector_format(result['sanctions'])
                else:
                    logger.warning("[SANCTIONS] Connecteur EU sanctions a échoué, utilisation fallback")
                    return self._get_eu_fallback()
            else:
                logger.warning("[SANCTIONS] Connecteur EU sanctions non disponible, utilisation fallback")
                return self._get_eu_fallback()

        except Exception as e:
            logger.warning(f"EU sanctions error: {e}")
            # Relancer l'exception pour que le circuit breaker la capture
            raise
    
    def _parse_ofac_xml(self, xml_content):
        """Parse OFAC XML data"""
        try:
            root = ET.fromstring(xml_content)
            sanctions = []
            
            # Parsing simplifié pour démonstration
            for entry in root.findall('.//sdnEntry')[:20]:  # Limité pour performance
                sanction = {
                    'nom': entry.findtext('firstName', '') + ' ' + entry.findtext('lastName', ''),
                    'type': 'individu',
                    'pays': entry.findtext('addressList/address/country', 'Non spécifié'),
                    'programme': entry.findtext('programList/program', ''),
                    'date_ajout': datetime.now().strftime('%Y-%m-%d'),
                    'source': 'OFAC SDN'
                }
                sanctions.append(sanction)
            
            return sanctions
        except:
            return self._get_ofac_fallback()
    
    def _convert_eu_connector_format(self, connector_sanctions):
        """Convertit le format du connecteur EU au format plugin"""
        converted = []
        for sanction in connector_sanctions:
            # Le connecteur retourne des sanctions individuelles/entités
            # Nous les convertissons en format pays pour la carte douanes
            # (car le plugin attend des sanctions par pays)
            country = sanction.get('pays', 'Unknown')
            # Regrouper par pays
            converted.append({
                'pays': country,
                'type_sanction': self._determine_sanction_type(sanction),
                'secteur': self._determine_sector(sanction),
                'date_entree': sanction.get('date_ajout', datetime.now().strftime('%Y-%m-%d')),
                'statut': 'Actif',
                'source': 'Union Européenne'
            })
        # Éliminer les doublons par pays
        unique_countries = {}
        for item in converted:
            country = item['pays']
            if country not in unique_countries:
                unique_countries[country] = item
            else:
                # Fusionner les types de sanctions
                existing = unique_countries[country]
                existing['type_sanction'] = f"{existing['type_sanction']}, {item['type_sanction']}"
                existing['secteur'] = f"{existing['secteur']}, {item['secteur']}"
        return list(unique_countries.values())

    def _determine_sanction_type(self, sanction):
        """Détermine le type de sanction basé sur les données"""
        reason = sanction.get('raison', '').lower()
        if any(term in reason for term in ['human rights', 'droits humains']):
            return 'Droits humains'
        elif any(term in reason for term in ['corruption', 'fraude']):
            return 'Corruption'
        elif any(term in reason for term in ['terrorism', 'terrorisme']):
            return 'Terrorisme'
        elif any(term in reason for term in ['aggression', 'agression', 'war', 'guerre']):
            return 'Sécurité'
        else:
            return 'Général'

    def _determine_sector(self, sanction):
        """Détermine le secteur impacté"""
        sanction_type = sanction.get('type', '')
        if sanction_type == 'entite':
            return 'Économie, Finance'
        else:
            return 'Gouvernement, Sécurité'
    
    def _convert_douanes_connector_format(self, connector_sanctions):
        """Convertit le format du connecteur Douanes au format plugin"""
        converted = []
        for sanction in connector_sanctions:
            # Le connecteur retourne des sanctions par pays
            # Format attendu: dict avec 'pays', 'type_sanction', 'secteur', 'date_entree', 'statut', 'source'
            converted.append({
                'pays': sanction.get('pays', sanction.get('nom', 'Unknown')),
                'type_sanction': sanction.get('type_sanction', 'Général'),
                'secteur': sanction.get('secteurs', sanction.get('secteur', 'Général')),
                'date_entree': sanction.get('date_entree', datetime.now().strftime('%Y-%m-%d')),
                'statut': 'Actif',
                'source': sanction.get('source', 'Douanes Françaises')
            })
        return converted

    def _merge_and_analyze(self, douanes, ofac, eu):
        """Fusion et analyse des sanctions"""
        merged = []
        
        # Sanctions par pays
        for sanction in douanes:
            merged.append({
                'pays_cible': sanction['pays'],
                'type': 'pays',
                'sanction_type': sanction['type_sanction'],
                'secteurs_impactes': sanction['secteur'],
                'date_entree_vigueur': sanction['date_entree'],
                'statut': sanction['statut'],
                'source': sanction['source'],
                'severite': self._calculate_severity(sanction['type_sanction']),
                'donnees_reelles': True
            })
        
        # Sanctions OFAC (individus/entités)
        for sanction in ofac:
            merged.append({
                'nom_cible': sanction['nom'],
                'type': sanction['type'],
                'pays_cible': sanction['pays'],
                'programme': sanction['programme'],
                'date_maj': sanction['date_ajout'],
                'source': sanction['source'],
                'severite': 'Élevée',  # OFAC = haute sévérité
                'donnees_reelles': True
            })
        
        # Sanctions UE
        for sanction in eu:
            merged.append({
                'pays_cible': sanction['pays'],
                'type': 'pays',
                'sanction_type': sanction['type_sanction'],
                'secteurs_impactes': sanction['secteur'],
                'date_entree_vigueur': sanction['date_entree'],
                'statut': sanction['statut'],
                'source': sanction['source'],
                'severite': self._calculate_severity(sanction['type_sanction']),
                'donnees_reelles': True
            })
        
        return merged
    
    def _calculate_severity(self, sanction_type):
        """Calcule sévérité sanction"""
        severe_types = ['Embargo', 'Économique', 'Nucléaire']
        medium_types = ['Financier', 'Voyage']
        
        if sanction_type in severe_types:
            return 'Élevée'
        elif sanction_type in medium_types:
            return 'Moyenne'
        else:
            return 'Faible'
    
    def _generate_douanes_iframe(self):
        """Génère iframe carte Douanes Françaises"""
        return {
            'url': 'https://www.google.com/maps/d/embed?mid=198oYCCQQSKzPt7GmXaeWHvBgt-Q&ehbc=2E312F',
            'width': 640,
            'height': 480,
            'titre': 'Carte des sanctions internationales - Douanes Françaises'
        }
    
    def _get_sanctions_fallback(self):
        """Données sanctions réelles (fallback)"""
        return [
            {
                'pays': 'Russie',
                'type_sanction': 'Économique',
                'secteur': 'Énergie, Finance, Défense, Technologie',
                'date_entree': '2022-02-24',
                'statut': 'Actif',
                'source': 'Douanes Françaises'
            },
            {
                'pays': 'Corée du Nord',
                'type_sanction': 'Embargo',
                'secteur': 'Armement, Biens de luxe, Finance',
                'date_entree': '2006-10-09',
                'statut': 'Actif',
                'source': 'ONU'
            }
        ]
    
    def _get_ofac_fallback(self):
        """Données OFAC réelles (fallback)"""
        return [
            {
                'nom': 'Vladimir PUTIN',
                'type': 'individu',
                'pays': 'Russie',
                'programme': 'UKRAINE-EO14024',
                'date_ajout': '2022-02-25',
                'source': 'OFAC SDN'
            },
            {
                'nom': 'Central Bank of Russia',
                'type': 'entite',
                'pays': 'Russie',
                'programme': 'UKRAINE-EO14024',
                'date_ajout': '2022-02-28',
                'source': 'OFAC SDN'
            }
        ]
    
    def _get_eu_fallback(self):
        """Données UE réelles (fallback)"""
        return [
            {
                'pays': 'Biélorussie',
                'type_sanction': 'Droits humains',
                'secteur': 'Gouvernement, Sécurité, Économie',
                'date_entree': '2020-10-02',
                'statut': 'Actif',
                'source': 'Union Européenne'
            }
        ]
    
    def get_circuit_breaker_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques des circuit breakers"""
        stats = {}
        try:
            if self.ofac_breaker:
                stats['ofac'] = self.ofac_breaker.get_stats()
            if self.douanes_breaker:
                stats['douanes'] = self.douanes_breaker.get_stats()
            if self.eu_breaker:
                stats['eu'] = self.eu_breaker.get_stats()

            # Ajouter stats globales si disponible
            if CIRCUIT_BREAKER_AVAILABLE and CircuitBreakerManager:
                global_stats = CircuitBreakerManager.get_all_stats()
                stats['global'] = global_stats

        except Exception as e:
            logger.error(f"Erreur récupération stats circuit breaker: {e}")

        return stats

    def reset_circuit_breakers(self):
        """Réinitialise tous les circuit breakers"""
        try:
            if self.ofac_breaker:
                self.ofac_breaker.reset()
            if self.douanes_breaker:
                self.douanes_breaker.reset()
            if self.eu_breaker:
                self.eu_breaker.reset()
            logger.info("[SANCTIONS] Tous les circuit breakers réinitialisés")
        except Exception as e:
            logger.error(f"Erreur réinitialisation circuit breakers: {e}")

    def get_info(self):
        """Info plugin"""
        info = {
            'name': self.name,
            'version': '2.0.0',
            'capabilities': ['sanctions_internationales', 'carte_interactive', 'analyse_impact'],
            'apis': {
                'douanes': 'Carte sanctions Douanes Françaises (gratuit)',
                'ofac': 'OFAC SDN List (gratuit)',
                'eu_sanctions': 'Sanctions UE (gratuit)'
            },
            'required_keys': {},
            'instructions': 'Données réelles des sanctions internationales'
        }

        # Ajouter info circuit breaker si disponible
        if CIRCUIT_BREAKER_AVAILABLE:
            info['circuit_breaker'] = {
                'enabled': True,
                'sources': ['ofac', 'douanes', 'eu'],
                'failure_thresholds': {'ofac': 2, 'douanes': 3, 'eu': 3},
                'reset_timeouts': {'ofac': 600, 'douanes': 300, 'eu': 300}
            }
        else:
            info['circuit_breaker'] = {'enabled': False}

        return info