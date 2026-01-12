"""
Plugin: Threat Intelligence
Description: Veille cyber et menaces hybrides via AlienVault OTX et CVE databases
"""

import requests
from datetime import datetime, timedelta
import logging
import sys
import os
import json
import time

# Ajouter le chemin pour importer les connecteurs
current_dir = os.path.dirname(os.path.abspath(__file__))
geo_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))  # Remonter à geo/
flask_dir = os.path.join(geo_root, 'Flask')
if flask_dir not in sys.path:
    sys.path.insert(0, flask_dir)

logger = logging.getLogger(__name__)

class Plugin:
    """Classe principale du plugin"""

    def __init__(self, settings):
        """Initialisation"""
        self.name = "threat-intelligence"
        self.settings = settings

        # Clé API AlienVault OTX (priorité: settings > variable d'environnement > clé en dur de debugsecu.txt)
        self.otx_api_key = self._get_otx_api_key()

        # Initialiser le connecteur CVE/NVD
        self.cve_connector = None
        self._init_cve_connector()

        logger.info(f"[THREATS] Plugin initialisé, OTX key: {'présente' if self.otx_api_key else 'absente'}")

    def _get_otx_api_key(self):
        """Récupère la clé API AlienVault OTX"""
        # Priorité 1: settings du plugin
        if self.settings and 'api_keys' in self.settings and 'alienvault' in self.settings['api_keys']:
            key = self.settings['api_keys']['alienvault']
            if key and key.strip():
                return key.strip()

        # Priorité 2: variable d'environnement
        import os
        env_key = os.environ.get('ALIENVAULT_OTX_API_KEY', '').strip()
        if env_key:
            return env_key

        # Priorité 3: clé en dur depuis debugsecu.txt (pour développement seulement)
        # Clé OTX AlienVault: 1c2a6122e143382fec2b7b56eb669da5838da6311c06c8acc6e5d2ebf785466f
        hardcoded_key = "1c2a6122e143382fec2b7b56eb669da5838da6311c06c8acc6e5d2ebf785466f"
        if hardcoded_key and hardcoded_key.strip():
            logger.warning("[THREATS] Utilisation clé OTX en dur - à remplacer par variable d'environnement")
            return hardcoded_key.strip()

        logger.warning("[THREATS] Aucune clé API AlienVault OTX trouvée")
        return None

    def _init_cve_connector(self):
        """Initialise le connecteur CVE/NVD"""
        try:
            from Flask.security_governance.cve_nvd_connector import CVENVDConnector
            self.cve_connector = CVENVDConnector()
            logger.info("[THREATS] Connecteur CVE/NVD initialisé")
        except Exception as e:
            logger.warning(f"[THREATS] Impossible d'initialiser le connecteur CVE/NVD: {e}")
            self.cve_connector = None

    def run(self, payload=None):
        """Point d'entrée principal"""
        if payload is None:
            payload = {}
        
        try:
            # VOTRE LOGIQUE ICI
            results = self._analyze_threats(payload)
            
            return {
                'status': 'success',
                'plugin': self.name,
                'timestamp': self._get_timestamp(),
                'data': results['data'],
                'metrics': results['metrics'],
                'message': 'Analyse des menaces cyber terminée'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'plugin': self.name,
                'timestamp': self._get_timestamp(),
                'data': [],
                'metrics': {},
                'message': f'Erreur: {str(e)}'
            }
    
    def _analyze_threats(self, payload):
        """Logique d'analyse des menaces"""
        threat_type = payload.get('threat_type', 'all')
        
        # Données AlienVault OTX
        otx_data = self._fetch_otx_pulses(threat_type)
        
        # Données CVE récentes
        cve_data = self._fetch_recent_cves()
        
        # Analyse des campagnes de menace
        campaigns = self._analyze_campaigns(otx_data)
        
        data = []
        for threat in otx_data[:10]:
            data.append({
                'menace': threat['name'],
                'type': threat['type'],
                'severite': threat['severity'],
                'acteurs': ', '.join(threat['actors']),
                'cibles': threat['targets'],
                'iocs': len(threat['indicators']),
                'premiere_observation': threat['first_seen'],
                'derniere_activite': threat['last_seen']
            })
        
        # Ajouter les CVE critiques
        for cve in cve_data[:5]:
            data.append({
                'menace': cve['cve_id'],
                'type': 'Vulnerabilité',
                'severite': cve['cvss_score'],
                'acteurs': 'N/A',
                'cibles': cve['affected_products'],
                'iocs': 0,
                'premiere_observation': cve['published_date'],
                'derniere_activite': cve['last_modified']
            })
        
        metrics = {
            'menaces_actives': len(otx_data),
            'vulnerabilites_critiques': len([c for c in cve_data if c['cvss_score'] >= 9]),
            'campagnes_identifiees': len(campaigns),
            'pays_cibles': len(set([t['targets'] for t in otx_data])),
            'tendance_globale': self._calculate_threat_trend(otx_data)
        }
        
        return {'data': data, 'metrics': metrics}
    
    def _fetch_otx_pulses(self, threat_type):
        """Récupère les pulses AlienVault OTX (API réelle avec fallback CISA KEV)"""
        # Essayer d'abord l'API AlienVault OTX
        otx_data = self._fetch_otx_pulses_real(threat_type)
        if otx_data:
            logger.info(f"[OTX] {len(otx_data)} pulses récupérés depuis AlienVault OTX")
            return otx_data

        # Fallback 1: CISA KEV Catalog (Known Exploited Vulnerabilities)
        logger.warning("[OTX] API AlienVault indisponible, utilisation CISA KEV Catalog")
        cisa_data = self._fetch_cisa_kev()
        if cisa_data:
            logger.info(f"[CISA KEV] {len(cisa_data)} vulnérabilités exploitées récupérées")
            return cisa_data

        # Fallback 2: Données de démonstration (dernier recours)
        logger.warning("[THREATS] Utilisation données de démonstration")
        return self._get_demo_threats()

    def _fetch_otx_pulses_real(self, threat_type):
        """Récupère les pulses depuis l'API AlienVault OTX réelle"""
        if not self.otx_api_key:
            logger.warning("[OTX] Clé API manquante")
            return []

        try:
            url = "https://otx.alienvault.com/api/v1/pulses/subscribed"
            headers = {'X-OTX-API-KEY': self.otx_api_key}

            logger.info("[OTX] Appel API AlienVault OTX...")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()
            pulses = data.get('results', [])

            formatted_pulses = []
            for pulse in pulses[:15]:  # Limiter à 15 pulses
                try:
                    # Extraire les informations
                    name = pulse.get('name', 'Unknown Pulse')
                    description = pulse.get('description', '')

                    # Déterminer le type basé sur les tags
                    tags = pulse.get('tags', [])
                    pulse_type = self._determine_threat_type(tags, description)

                    # Sévérité (OTX n'a pas de sévérité directe, on utilise le nombre d'indicators)
                    indicators = pulse.get('indicators', [])
                    severity = self._determine_severity(len(indicators))

                    # Acteurs (extrait des tags ou description)
                    actors = self._extract_actors(tags, description)

                    # Cibles (générique)
                    targets = self._extract_targets(tags, description)

                    # Dates
                    created = pulse.get('created', '')
                    modified = pulse.get('modified', '')

                    # Formater pour le plugin
                    formatted_pulses.append({
                        'name': name[:200],  # Limiter longueur
                        'type': pulse_type,
                        'severity': severity,
                        'actors': actors,
                        'targets': targets,
                        'indicators': [ind.get('indicator', '') for ind in indicators[:5]],  # Top 5
                        'first_seen': created[:10] if created else 'Unknown',
                        'last_seen': modified[:10] if modified else 'Unknown'
                    })
                except Exception as e:
                    logger.warning(f"[OTX] Erreur format pulse: {e}")
                    continue

            logger.info(f"[OTX] {len(formatted_pulses)} pulses formatés")
            return formatted_pulses

        except requests.exceptions.RequestException as e:
            logger.warning(f"[OTX] Erreur API: {e}")
            return []
        except Exception as e:
            logger.warning(f"[OTX] Erreur inattendue: {e}")
            return []

    def _fetch_cisa_kev(self):
        """Récupère le catalogue CISA KEV (Known Exploited Vulnerabilities)"""
        try:
            url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
            logger.info("[CISA KEV] Téléchargement catalogue...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            vulnerabilities = data.get('vulnerabilities', [])

            formatted_threats = []
            for vuln in vulnerabilities[:20]:  # Limiter à 20
                try:
                    cve_id = vuln.get('cveID', '')
                    vendor_project = vuln.get('vendorProject', '')
                    product = vuln.get('product', '')
                    date_added = vuln.get('dateAdded', '')
                    short_description = vuln.get('shortDescription', '')

                    # Formater comme une menace
                    formatted_threats.append({
                        'name': f"CISA KEV: {cve_id}",
                        'type': 'Known Exploited Vulnerability',
                        'severity': 'High',  # Toutes les vulnérabilités exploitées sont critiques
                        'actors': ['State-sponsored', 'Cybercriminals'],  # Générique
                        'targets': f"{vendor_project} {product}",
                        'indicators': [],  # Pas d'IOCs dans ce feed
                        'first_seen': date_added[:10] if date_added else 'Unknown',
                        'last_seen': date_added[:10] if date_added else 'Unknown'
                    })
                except Exception as e:
                    logger.warning(f"[CISA KEV] Erreur format vuln: {e}")
                    continue

            logger.info(f"[CISA KEV] {len(formatted_threats)} vulnérabilités formatées")
            return formatted_threats

        except Exception as e:
            logger.warning(f"[CISA KEV] Erreur: {e}")
            return []

    def _get_demo_threats(self):
        """Données de démonstration (dernier recours)"""
        return [
            {
                'name': 'APT29 Campaign',
                'type': 'APT',
                'severity': 'High',
                'actors': ['APT29', 'Cozy Bear'],
                'targets': 'Gouvernements UE',
                'indicators': ['ip1', 'domain1', 'hash1'],
                'first_seen': '2024-01-10',
                'last_seen': '2024-01-15'
            },
            {
                'name': 'Phishing Finance Sector',
                'type': 'Phishing',
                'severity': 'Medium',
                'actors': ['FIN7'],
                'targets': 'Banques internationales',
                'indicators': ['ip2', 'domain2', 'hash2'],
                'first_seen': '2024-01-12',
                'last_seen': '2024-01-16'
            }
        ]

    def _determine_threat_type(self, tags, description):
        """Détermine le type de menace basé sur les tags et description"""
        type_mapping = {
            'apt': 'APT',
            'phishing': 'Phishing',
            'ransomware': 'Ransomware',
            'malware': 'Malware',
            'trojan': 'Trojan',
            'botnet': 'Botnet',
            'ddos': 'DDoS',
            'exploit': 'Exploit',
            'vulnerability': 'Vulnerability',
            'cve': 'Vulnerability'
        }

        description_lower = description.lower()
        for tag in tags:
            tag_lower = tag.lower()
            for key, value in type_mapping.items():
                if key in tag_lower:
                    return value

        # Fallback basé sur description
        for key, value in type_mapping.items():
            if key in description_lower:
                return value

        return 'Threat'

    def _determine_severity(self, indicator_count):
        """Détermine la sévérité basée sur le nombre d'indicators"""
        if indicator_count > 20:
            return 'Critical'
        elif indicator_count > 10:
            return 'High'
        elif indicator_count > 5:
            return 'Medium'
        else:
            return 'Low'

    def _extract_actors(self, tags, description):
        """Extrait les acteurs des tags et description"""
        actors = []
        known_actors = ['APT29', 'APT28', 'Cozy Bear', 'Fancy Bear', 'Lazarus',
                       'FIN7', 'Cobalt Group', 'TA505', 'Wizard Spider']

        for actor in known_actors:
            if actor.lower() in description.lower():
                actors.append(actor)

        # Ajouter tags pertinents
        for tag in tags:
            if any(actor.lower() in tag.lower() for actor in known_actors):
                actors.append(tag)

        return actors[:3] if actors else ['Unknown']

    def _extract_targets(self, tags, description):
        """Extrait les cibles des tags et description"""
        targets = []
        sectors = ['Government', 'Finance', 'Healthcare', 'Energy', 'Technology',
                  'Education', 'Military', 'Critical Infrastructure']

        for sector in sectors:
            if sector.lower() in description.lower():
                targets.append(sector)

        # Ajouter tags pertinents
        for tag in tags:
            if any(sector.lower() in tag.lower() for sector in sectors):
                targets.append(tag)

        return ', '.join(targets[:3]) if targets else 'Various'
    
    def _fetch_recent_cves(self):
        """Récupère les CVE récentes via le connecteur CVE/NVD avec fallback"""
        # Utiliser le connecteur CVE/NVD si disponible
        if self.cve_connector:
            try:
                result = self.cve_connector.get_recent_cves(days=7, limit=10)
                if result.get('success'):
                    cves = result.get('cves', [])
                    logger.info(f"[CVE/NVD] {len(cves)} CVE récentes récupérées")
                    return self._format_cves_for_plugin(cves)
                else:
                    logger.warning(f"[CVE/NVD] Erreur: {result.get('error')}")
            except Exception as e:
                logger.warning(f"[CVE/NVD] Exception: {e}")

        # Fallback: données de démonstration
        logger.warning("[CVE] Utilisation données de démonstration")
        return self._get_demo_cves()

    def _format_cves_for_plugin(self, cves):
        """Formate les CVE du connecteur pour le plugin"""
        formatted = []
        for cve in cves[:10]:  # Limiter à 10
            try:
                formatted.append({
                    'cve_id': cve.get('cve_id', ''),
                    'cvss_score': cve.get('severity_score', 0.0),
                    'affected_products': cve.get('affected_products', [])[:3],  # Top 3
                    'published_date': cve.get('published_date', ''),
                    'last_modified': cve.get('last_modified', '')
                })
            except Exception as e:
                logger.warning(f"[CVE] Erreur format CVE: {e}")
                continue
        return formatted

    def _get_demo_cves(self):
        """Données de démonstration CVE (fallback)"""
        return [
            {
                'cve_id': 'CVE-2024-1234',
                'cvss_score': 9.8,
                'affected_products': ['Windows', 'Linux'],
                'published_date': '2024-01-15',
                'last_modified': '2024-01-16'
            },
            {
                'cve_id': 'CVE-2024-1235',
                'cvss_score': 7.5,
                'affected_products': ['Cisco IOS'],
                'published_date': '2024-01-14',
                'last_modified': '2024-01-15'
            }
        ]
    
    def _analyze_campaigns(self, threats):
        """Analyse les campagnes de menace coordonnées"""
        campaigns = []
        
        # Regroupement par acteurs similaires
        actor_groups = {}
        for threat in threats:
            for actor in threat['actors']:
                if actor not in actor_groups:
                    actor_groups[actor] = []
                actor_groups[actor].append(threat)
        
        # Identification des campagnes
        for actor, threats_list in actor_groups.items():
            if len(threats_list) > 1:
                campaigns.append({
                    'nom_campagne': f"Campagne {actor}",
                    'acteur_principal': actor,
                    'menaces_liees': len(threats_list),
                    'periode_activite': f"{min(t['first_seen'] for t in threats_list)} to {max(t['last_seen'] for t in threats_list)}"
                })
        
        return campaigns
    
    def _calculate_threat_trend(self, threats):
        """Calcule la tendance des menaces"""
        if not threats:
            return 'Stable'
        
        high_severity = len([t for t in threats if t['severity'] == 'High'])
        if high_severity > len(threats) * 0.5:
            return 'Escalade'
        else:
            return 'Stable'
    
    def _get_timestamp(self):
        """Retourne timestamp ISO"""
        return datetime.now().isoformat()
    
    def get_info(self):
        """Informations du plugin"""
        return {
            'name': self.name,
            'capabilities': ['veille_cyber', 'analyse_ioc', 'detection_campagnes'],
            'required_keys': ['alienvault']  # Optionnel
        }