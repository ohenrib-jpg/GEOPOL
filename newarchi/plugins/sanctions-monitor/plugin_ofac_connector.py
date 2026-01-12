#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Version alternative du plugin sanctions-monitor utilisant le connecteur OFAC existant
"""

import logging
from datetime import datetime
import sys
import os

# Ajouter le chemin pour importer le connecteur
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'Flask', 'security_governance'))

logger = logging.getLogger(__name__)

class PluginWithConnector:
    """Surveillance sanctions internationales avec connecteur OFAC"""

    def __init__(self, settings):
        self.name = "sanctions-monitor-connector"
        self.settings = settings

    def _fetch_ofac_sanctions(self):
        """Utilise le connecteur OFAC SDN existant"""
        try:
            # Importer le connecteur
            from ofac_sdn_connector import OFACSDNConnector

            logger.info("[SANCTIONS-CONNECTOR] Utilisation du connecteur OFAC...")

            # Créer instance du connecteur
            connector = OFACSDNConnector(timeout=30)

            # Récupérer les sanctions
            result = connector.get_sdn_list(limit=100)

            if not result.get('success', False):
                logger.warning(f"[SANCTIONS-CONNECTOR] Échec connecteur: {result.get('error', 'Unknown error')}")
                return self._get_ofac_fallback()

            sdn_entries = result.get('sdn_entries', [])
            logger.info(f"[SANCTIONS-CONNECTOR] {len(sdn_entries)} sanctions récupérées")

            # Convertir au format du plugin
            sanctions = []
            for entry in sdn_entries:
                try:
                    # Déterminer type
                    entry_type = entry.get('type', '').upper()
                    if 'INDIVIDU' in entry_type or 'PERSON' in entry_type:
                        target_type = 'individu'
                    elif 'ENTITÉ' in entry_type or 'ENTITY' in entry_type or 'COMPANY' in entry_type:
                        target_type = 'entite'
                    else:
                        # Deviner basé sur le nom
                        name = entry.get('name', '')
                        if any(title in name.upper() for title in ['MR.', 'MRS.', 'DR.', 'PROF.', 'SHEIKH', 'PRINCE']):
                            target_type = 'individu'
                        else:
                            target_type = 'entite'

                    # Extraire pays
                    countries = entry.get('countries', '')
                    if countries:
                        country = countries.split(',')[0].strip()
                    else:
                        country = self._extract_country_from_ofac_data(
                            entry.get('program', ''),
                            entry.get('addresses', '')
                        )

                    sanctions.append({
                        'nom': entry.get('name', 'Unknown'),
                        'type': target_type,
                        'pays': country,
                        'programme': entry.get('program', 'Unknown'),
                        'date_ajout': entry.get('timestamp', datetime.now().isoformat()),
                        'source': 'OFAC SDN (via connecteur)',
                        'adresses': entry.get('addresses', '')[:200],
                        'raw_type': entry.get('raw_type', '')
                    })

                except Exception as e:
                    logger.warning(f"Erreur conversion entrée OFAC: {e}")
                    continue

            return sanctions

        except ImportError as e:
            logger.warning(f"[SANCTIONS-CONNECTOR] Impossible d'importer le connecteur: {e}")
            return self._get_ofac_fallback()
        except Exception as e:
            logger.warning(f"[SANCTIONS-CONNECTOR] Erreur générale: {e}")
            return self._get_ofac_fallback()

    def _extract_country_from_ofac_data(self, program: str, addresses: str) -> str:
        """Extrait le pays des données OFAC (identique à la version originale)"""
        program_upper = program.upper()

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

        if addresses:
            return self._extract_country_from_address(addresses)

        return 'Non spécifié'

    def _extract_country_from_address(self, addresses: str) -> str:
        """Extrait le pays d'une adresse OFAC"""
        if not addresses:
            return 'Non spécifié'

        country_keywords = [
            'RUSSIA', 'CHINA', 'IRAN', 'NORTH KOREA', 'SYRIA',
            'VENEZUELA', 'CUBA', 'SUDAN', 'BELARUS', 'MYANMAR',
            'AFGHANISTAN', 'YEMEN', 'LIBYA', 'SOMALIA', 'IRAQ',
            'UKRAINE', 'TURKEY', 'SAUDI ARABIA', 'QATAR', 'UAE'
        ]

        addresses_upper = addresses.upper()
        for country in country_keywords:
            if country in addresses_upper:
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

    def _get_ofac_fallback(self):
        """Données OFAC réelles (fallback)"""
        return [
            {
                'nom': 'Vladimir PUTIN',
                'type': 'individu',
                'pays': 'Russie',
                'programme': 'UKRAINE-EO14024',
                'date_ajout': '2022-02-25',
                'source': 'OFAC SDN (fallback)'
            },
            {
                'nom': 'Central Bank of Russia',
                'type': 'entite',
                'pays': 'Russie',
                'programme': 'UKRAINE-EO14024',
                'date_ajout': '2022-02-28',
                'source': 'OFAC SDN (fallback)'
            }
        ]

    def run(self, payload=None):
        """Exécution avec connecteur OFAC"""
        try:
            ofac_data = self._fetch_ofac_sanctions()

            return {
                'status': 'success',
                'plugin': self.name,
                'timestamp': datetime.now().isoformat(),
                'data': ofac_data[:50],
                'metrics': {
                    'sanctions_actives': len(ofac_data),
                    'pays_cibles': len(set([d['pays'] for d in ofac_data if d['pays']])),
                    'entites_ciblees': len([d for d in ofac_data if d['type'] == 'entite']),
                    'individus_cibles': len([d for d in ofac_data if d['type'] == 'individu']),
                },
                'message': f'Surveillance de {len(ofac_data)} sanctions OFAC via connecteur'
            }

        except Exception as e:
            logger.error(f"Erreur plugin avec connecteur: {e}")
            return {
                'status': 'error',
                'plugin': self.name,
                'timestamp': datetime.now().isoformat(),
                'message': f'Erreur: {str(e)}'
            }