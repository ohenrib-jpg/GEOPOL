# Flask/real_sdr_manager.py
import logging
import requests
import json
from datetime import datetime
import sqlite3

logger = logging.getLogger(__name__)

class RealSDRManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.kiwisdr_api_url = "http://kiwisdr.com/public/"
        
    def fetch_kiwisdr_servers(self):
        """Récupère la liste réelle des serveurs KiwiSDR"""
        try:
            # API KiwiSDR publique pour obtenir les serveurs actifs
            response = requests.get(f"{self.kiwisdr_api_url}?json=1", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self.parse_kiwisdr_servers(data)
            else:
                logger.error(f"Erreur API KiwiSDR: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Erreur récupération serveurs KiwiSDR: {e}")
            return []
    
    def parse_kiwisdr_servers(self, data):
        """Parse les données des serveurs KiwiSDR"""
        servers = []
        
        if 'results' in data:
            for server in data['results']:
                server_info = {
                    'name': server.get('name', 'Unknown'),
                    'location': server.get('location', 'Unknown'),
                    'country': server.get('country', 'Unknown'),
                    'users': server.get('users', 0),
                    'max_users': server.get('max_users', 0),
                    'frequency': server.get('frequency', 0),
                    'status': 'online' if server.get('users', 0) < server.get('max_users', 1) else 'offline',
                    'last_seen': datetime.utcnow().isoformat()
                }
                servers.append(server_info)
        
        return servers
    
    def update_sdr_streams_from_reality(self):
        """Met à jour les flux SDR avec des données réelles"""
        try:
            real_servers = self.fetch_kiwisdr_servers()
            
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            # Vider la table existante
            cur.execute("DELETE FROM sdr_streams")
            
            # Insérer les serveurs réels
            for i, server in enumerate(real_servers[:10]):  # Limiter à 10 serveurs
                cur.execute("""
                    INSERT INTO sdr_streams 
                    (name, url, frequency_khz, type, description, active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    f"KiwiSDR - {server['location']}",
                    f"http://{server.get('host', 'kiwisdr.com')}",
                    server.get('frequency', 0),
                    'kiwisdr',
                    f"Server in {server['country']} - {server['users']}/{server['max_users']} users",
                    server['status'] == 'online'
                ))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ {len(real_servers)} serveurs SDR réels mis à jour")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour SDR réels: {e}")
    
    def get_geopolitical_frequencies(self):
        """Retourne les fréquences géopolitiques importantes"""
        return {
            'shortwave': {
                'BBC World Service': 12065,
                'Radio France International': 15300,
                'Voice of America': 13670,
                'Radio China International': 11710,
                'Radio Moscow': 12085
            },
            'utility': {
                'Volmet Weather': 6604,
                'Maritime Safety': 2182,
                'Aircraft Emergency': 12150,
                'Military Satcom': 13900
            },
            'numbers_stations': {
                'Lincolnshire Poacher': 13780,
                'Russian Buzz': 4625,
                'Cuban Numbers': 9330
            }
        }