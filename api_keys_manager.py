"""
Gestionnaire de Clés API
Stockage sécurisé et gestion des clés API tierces (ACLED, YouTube, etc.)
"""

import sys
if sys.platform == 'win32':
    import codecs
    # Vérification sécurisée de l'attribut buffer
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')

import logging
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet, InvalidToken
import os

logger = logging.getLogger(__name__)


class APIKeysManager:
    """
    Gestionnaire centralisé des clés API
    Stocke les clés de manière sécurisée avec chiffrement
    """

    # Services supportés
    SUPPORTED_SERVICES = {
        'acled': {
            'name': 'ACLED',
            'description': 'Armed Conflict Location & Event Data (OAuth2)',
            'fields': ['email', 'password'],
            'required': True,
            'url': 'https://developer.acleddata.com/'
        },
        'youtube': {
            'name': 'YouTube Data API',
            'description': 'Google YouTube Data API v3',
            'fields': ['api_key'],
            'required': False,
            'url': 'https://console.cloud.google.com/'
        },
        'openai': {
            'name': 'OpenAI',
            'description': 'OpenAI API (GPT, DALL-E)',
            'fields': ['api_key'],
            'required': False,
            'url': 'https://platform.openai.com/'
        },
        'mistral': {
            'name': 'Mistral AI',
            'description': 'Mistral AI API',
            'fields': ['api_key'],
            'required': False,
            'url': 'https://console.mistral.ai/'
        },
        'ocha_hdx': {
            'name': 'UN OCHA HDX',
            'description': 'Humanitarian Data Exchange (no authentication required)',
            'fields': [],  # Aucune authentification requise
            'required': False,
            'url': 'https://data.humdata.org/'
        },
        'anthropic': {
            'name': 'Anthropic (Claude)',
            'description': 'Claude API pour Dev Assistant - Raisonnement strategique',
            'fields': ['api_key'],
            'required': False,
            'url': 'https://console.anthropic.com/'
        },
        'deepseek': {
            'name': 'DeepSeek',
            'description': 'DeepSeek Coder API pour Dev Assistant',
            'fields': ['api_key'],
            'required': False,
            'url': 'https://platform.deepseek.com/'
        }
    }

    def __init__(self, db_manager):
        """
        Initialise le gestionnaire de clés API

        Args:
            db_manager: Instance de DatabaseManager
        """
        self.db_manager = db_manager
        self._init_encryption()
        self._init_database()
        self._load_from_env()

    def _init_encryption(self):
        """Initialise le système de chiffrement"""
        # Clé de chiffrement (en production, stocker dans variable d'env sécurisée)
        encryption_key = os.getenv('ENCRYPTION_KEY')

        # DEBUG: Vérifier si les variables d'environnement sont chargées
        env_keys = [k for k in os.environ.keys() if 'ENCRYPTION' in k or 'KEY' in k]
        logger.debug(f"[DEBUG] Variables d'environnement liées aux clés: {env_keys}")
        logger.debug(f"[DEBUG] ENCRYPTION_KEY présente: {'ENCRYPTION_KEY' in os.environ}")
        logger.debug(f"[DEBUG] Valeur ENCRYPTION_KEY (truncated): {encryption_key[:10] + '...' if encryption_key and len(encryption_key) > 10 else 'None'}")

        # Log un hash de la clé pour le débogage (ne pas logger la clé complète)
        if encryption_key:
            import hashlib
            key_hash = hashlib.sha256(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key).hexdigest()[:16]
            logger.debug(f"[DEBUG] Hash clé de chiffrement: {key_hash}")

        if encryption_key:
            logger.info(f"[OK] Clé de chiffrement chargée depuis ENV (longueur: {len(encryption_key)})")
        else:
            # Générer une clé si inexistante (ATTENTION: à stocker de manière persistante en prod)
            encryption_key = Fernet.generate_key().decode()
            logger.warning("[WARN] Clé de chiffrement générée automatiquement. En production, définir ENCRYPTION_KEY dans .env")
            logger.warning(f"[WARN] Nouvelle clé générée (premiers 20 chars): {encryption_key[:20]}...")

        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()

        self.cipher = Fernet(encryption_key)

    def _init_database(self):
        """Crée la table api_keys si elle n'existe pas"""
        try:
            # DEBUG: Log le chemin de la base de données
            if hasattr(self.db_manager, 'db_path'):
                logger.debug(f"[DEBUG] Chemin base de données API Keys: {self.db_manager.db_path}")

            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT UNIQUE NOT NULL,
                    service_name TEXT,
                    encrypted_data TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP
                )
            """)

            # Index
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_service
                ON api_keys(service)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_api_keys_active
                ON api_keys(is_active)
            """)

            conn.commit()
            conn.close()

            logger.info("[OK] Table api_keys initialisée")

        except Exception as e:
            logger.error(f"[ERROR] Erreur init database: {e}")

    def _load_from_env(self):
        """Charge les clés API depuis les variables d'environnement"""
        logger.info("[APIKeys] Début chargement clés depuis environnement")
        try:
            # Mapping des variables d'environnement vers les services supportés
            env_mapping = {
                'ANTHROPIC_API_KEY': 'anthropic',
                'DEEPSEEK_API_KEY': 'deepseek',
                'OPENAI_API_KEY': 'openai',
                'MISTRAL_API_KEY': 'mistral',
                'YOUTUBE_API_KEY': 'youtube',
            }

            logger.debug(f"[APIKeys] Variables recherchées: {list(env_mapping.keys())}")

            for env_var, service in env_mapping.items():
                if service not in self.SUPPORTED_SERVICES:
                    logger.debug(f"[APIKeys] Service non supporté ignoré: {service}")
                    continue
                value = os.getenv(env_var)
                if value and value.strip():
                    logger.debug(f"[APIKeys] Variable trouvée: {env_var}={value[:10]}...")
                    # Vérifier si la clé existe déjà en base
                    existing = self.get_api_key(service)
                    if not existing:
                        # Sauvegarder la clé
                        credentials = {'api_key': value.strip()}
                        self.save_api_key(service, credentials)
                        logger.info(f"[OK] Clé API chargée depuis env: {service}")
                    else:
                        logger.debug(f"[APIKeys] Clé déjà présente en base pour: {service}")
                else:
                    logger.debug(f"[APIKeys] Variable non définie: {env_var}")
        except Exception as e:
            logger.error(f"[ERROR] Erreur lors du chargement depuis l'environnement: {e}")

    def _encrypt(self, data: str) -> str:
        """Chiffre une donnée"""
        return self.cipher.encrypt(data.encode()).decode()

    def _decrypt(self, encrypted_data: str) -> str:
        """Déchiffre une donnée"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def save_api_key(self, service: str, credentials: Dict[str, str]) -> bool:
        """
        Sauvegarde une clé API

        Args:
            service: Identifiant du service (ex: 'acled')
            credentials: Dictionnaire des credentials (ex: {'api_key': 'xxx', 'email': 'xxx'})

        Returns:
            True si succès, False sinon
        """
        try:
            if service not in self.SUPPORTED_SERVICES:
                logger.error(f"[ERROR] Service non supporté: {service}")
                return False

            # Récupérer les credentials existants (si présents) pour fusion
            existing_credentials = self.get_api_key(service)
            if existing_credentials:
                # Fusionner: les nouvelles valeurs écrasent les anciennes
                for key, value in credentials.items():
                    if value:  # Ne mettre à jour que si la valeur n'est pas vide
                        existing_credentials[key] = value
                # Utiliser les credentials fusionnés
                credentials = existing_credentials
                logger.debug(f"[DEBUG] Fusion des credentials pour {service}")

            # Valider que tous les champs requis sont présents après fusion
            required_fields = self.SUPPORTED_SERVICES[service]['fields']
            for field in required_fields:
                if field not in credentials or not credentials[field]:
                    logger.error(f"[ERROR] Champ requis manquant ou vide: {field}")
                    return False

            # Chiffrer les credentials
            import json
            encrypted_data = self._encrypt(json.dumps(credentials))

            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Upsert
            cursor.execute("""
                INSERT INTO api_keys (service, service_name, encrypted_data, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(service) DO UPDATE SET
                    encrypted_data = excluded.encrypted_data,
                    updated_at = excluded.updated_at,
                    is_active = 1
            """, (
                service,
                self.SUPPORTED_SERVICES[service]['name'],
                encrypted_data,
                datetime.now()
            ))

            conn.commit()
            conn.close()

            logger.info(f"[OK] Clé API sauvegardée: {service}")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Erreur save_api_key: {e}")
            return False

    def get_api_key(self, service: str) -> Optional[Dict[str, str]]:
        """
        Récupère une clé API déchiffrée

        Args:
            service: Identifiant du service

        Returns:
            Dictionnaire des credentials ou None
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT encrypted_data, is_active
                FROM api_keys
                WHERE service = ?
            """, (service,))

            row = cursor.fetchone()
            conn.close()

            if not row:
                logger.debug(f"[DEBUG] get_api_key: aucune ligne trouvée pour le service {service}")
                return None

            encrypted_data, is_active = row
            logger.debug(f"[DEBUG] get_api_key: service={service}, is_active={is_active}, encrypted_data_length={len(encrypted_data) if encrypted_data else 0}")

            if not is_active:
                logger.warning(f"[WARN] Clé API désactivée: {service}")
                return None

            # Déchiffrer
            import json
            try:
                credentials = json.loads(self._decrypt(encrypted_data))
            except InvalidToken:
                logger.error(f"[ERROR] Impossible de déchiffrer les données pour {service}. La clé de chiffrement ne correspond pas.")
                logger.error(f"[ERROR] Les données ont probablement été chiffrées avec une autre clé. Suppression de l'entrée corrompue.")
                # Supprimer l'entrée corrompue
                self.delete_api_key(service)
                return None
            except json.JSONDecodeError as e:
                logger.error(f"[ERROR] Données déchiffrées invalides (JSON) pour {service}: {e}")
                return None

            # Mettre à jour last_used
            self._update_last_used(service)

            return credentials

        except Exception as e:
            logger.error(f"[ERROR] Erreur get_api_key pour {service}: {e}")
            import traceback
            logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
            return None

    def _update_last_used(self, service: str):
        """Met à jour la date de dernière utilisation"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE api_keys
                SET last_used = ?
                WHERE service = ?
            """, (datetime.now(), service))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"[ERROR] Erreur update_last_used: {e}")

    def delete_api_key(self, service: str) -> bool:
        """
        Supprime une clé API

        Args:
            service: Identifiant du service

        Returns:
            True si succès
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM api_keys
                WHERE service = ?
            """, (service,))

            conn.commit()
            conn.close()

            logger.info(f"[OK] Clé API supprimée: {service}")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Erreur delete_api_key: {e}")
            return False

    def toggle_api_key(self, service: str, is_active: bool) -> bool:
        """
        Active/désactive une clé API

        Args:
            service: Identifiant du service
            is_active: True pour activer, False pour désactiver

        Returns:
            True si succès
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE api_keys
                SET is_active = ?, updated_at = ?
                WHERE service = ?
            """, (1 if is_active else 0, datetime.now(), service))

            conn.commit()
            conn.close()

            status = "activée" if is_active else "désactivée"
            logger.info(f"[OK] Clé API {status}: {service}")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Erreur toggle_api_key: {e}")
            return False

    def list_api_keys(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Liste toutes les clés API (sans les valeurs sensibles)

        Args:
            include_inactive: Inclure les clés désactivées

        Returns:
            Liste de dictionnaires avec infos des clés
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            query = """
                SELECT service, service_name, is_active, created_at, updated_at, last_used
                FROM api_keys
            """

            if not include_inactive:
                query += " WHERE is_active = 1"

            cursor.execute(query)

            keys = []
            for row in cursor.fetchall():
                service_info = self.SUPPORTED_SERVICES.get(row[0], {})

                keys.append({
                    'service': row[0],
                    'service_name': row[1],
                    'is_active': bool(row[2]),
                    'created_at': row[3],
                    'updated_at': row[4],
                    'last_used': row[5],
                    'description': service_info.get('description', ''),
                    'required': service_info.get('required', False),
                    'url': service_info.get('url', '')
                })

            conn.close()

            return keys

        except Exception as e:
            logger.error(f"[ERROR] Erreur list_api_keys: {e}")
            return []

    def get_supported_services(self) -> List[Dict[str, Any]]:
        """
        Retourne la liste des services supportés

        Returns:
            Liste des services avec leurs infos
        """
        services = []

        for service_id, info in self.SUPPORTED_SERVICES.items():
            services.append({
                'id': service_id,
                'name': info['name'],
                'description': info['description'],
                'fields': info['fields'],
                'required': info['required'],
                'url': info['url']
            })

        return services

    def test_api_key(self, service: str) -> Dict[str, Any]:
        """
        Teste une clé API

        Args:
            service: Identifiant du service

        Returns:
            Résultat du test
        """
        try:
            # Services sans authentification requise
            if service == 'ocha_hdx':
                return self._test_ocha_hdx({})

            credentials = self.get_api_key(service)

            if not credentials:
                return {
                    'success': False,
                    'service': service,
                    'error': 'No API key configured'
                }

            # Test spécifique par service
            if service == 'acled':
                return self._test_acled(credentials)
            elif service == 'youtube':
                return self._test_youtube(credentials)
            else:
                return {
                    'success': True,
                    'service': service,
                    'message': 'API key configured (no test available)'
                }

        except Exception as e:
            logger.error(f"[ERROR] Erreur test_api_key: {e}")
            return {
                'success': False,
                'service': service,
                'error': str(e)
            }

    def _test_acled(self, credentials: Dict) -> Dict[str, Any]:
        """Teste les credentials ACLED avec OAuth2"""
        try:
            from .security_governance.acled_connector import ACLEDConnector

            acled = ACLEDConnector(
                email=credentials.get('email'),
                password=credentials.get('password')
            )

            # Test simple: récupérer 1 événement récent
            events = acled.get_recent_events(days=7, limit=1)

            if events:
                return {
                    'success': True,
                    'service': 'acled',
                    'message': f'Connection successful - {len(events)} event(s) retrieved'
                }
            else:
                return {
                    'success': False,
                    'service': 'acled',
                    'error': 'No events retrieved (check credentials or quota)'
                }

        except Exception as e:
            return {
                'success': False,
                'service': 'acled',
                'error': str(e)
            }

    def _test_youtube(self, credentials: Dict) -> Dict[str, Any]:
        """Teste la clé YouTube"""
        try:
            import requests

            api_key = credentials.get('api_key')

            # Test simple avec API YouTube
            response = requests.get(
                'https://www.googleapis.com/youtube/v3/search',
                params={
                    'part': 'snippet',
                    'q': 'test',
                    'maxResults': 1,
                    'key': api_key
                },
                timeout=10
            )

            if response.status_code == 200:
                return {
                    'success': True,
                    'service': 'youtube',
                    'message': 'Connection successful'
                }
            else:
                return {
                    'success': False,
                    'service': 'youtube',
                    'error': f'HTTP {response.status_code}: {response.text}'
                }

        except Exception as e:
            return {
                'success': False,
                'service': 'youtube',
                'error': str(e)
            }

    def _test_ocha_hdx(self, credentials: Dict) -> Dict[str, Any]:
        """Teste la connexion à l'API HDX (pas d'authentification requise)"""
        try:
            # Import flexible pour supporter différents contextes d'exécution
            try:
                from .security_governance.ocha_hdx_connector import OchaHdxConnector
            except ImportError:
                from security_governance.ocha_hdx_connector import OchaHdxConnector

            hdx = OchaHdxConnector()
            # Test simple: recherche de datasets de crise
            result = hdx.search_datasets(query='crisis', limit=5)

            if result.get('success'):
                datasets_count = result.get('count', 0)
                return {
                    'success': True,
                    'service': 'ocha_hdx',
                    'message': f'HDX API accessible - {datasets_count} datasets found'
                }
            else:
                return {
                    'success': False,
                    'service': 'ocha_hdx',
                    'error': result.get('error', 'HDX API inaccessible')
                }

        except Exception as e:
            return {
                'success': False,
                'service': 'ocha_hdx',
                'error': str(e)
            }


def get_api_keys_manager(db_manager):
    """Factory pour obtenir le gestionnaire"""
    return APIKeysManager(db_manager)


__all__ = ['APIKeysManager', 'get_api_keys_manager']