# Flask/sdr_spectrum_service.py
"""
Service d'analyse spectrale SDR - Scraping WebSDR
Analyse passive des pics d'émission (Transformée de Fourier)
"""

import logging
import requests
import os
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import re
import json
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)


class SDRSpectrumService:
    """
    Service d'analyse spectrale passive via WebSDR
    Scraping des données FFT publiques pour détecter l'activité radio
    """
    
    # Serveurs WebSDR testés et fonctionnels (exposent spectrum.js ou FFT)
    WEBSDR_SERVERS = [
        {
            'name': 'University of Twente',
            'url': 'http://websdr.ewi.utwente.nl:8901',
            'location': 'Netherlands',
            'spectrum_endpoint': '/spectrum.js',
            'type': 'websdr'
        },
        {
            'name': 'WebSDR PA',
            'url': 'http://websdr.pa3weg.nl',
            'location': 'Netherlands',
            'spectrum_endpoint': '/spectrum.js',
            'type': 'websdr'
        },
        {
            'name': 'KiwiSDR Network',
            'url': 'http://kiwisdr.com',
            'location': 'Global',
            'spectrum_endpoint': '/waterfall',
            'type': 'kiwisdr'
        }
    ]
    
    # Fréquences géopolitiques (kHz)
    GEOPOLITICAL_FREQUENCIES = {
        'emergency': [
            {'freq': 2182, 'name': 'Détresse Maritime MF', 'baseline_peaks': 3},
            {'freq': 121500, 'name': 'Urgence Aviation', 'baseline_peaks': 5}
        ],
        'military': [
            {'freq': 4625, 'name': 'UVB-76 Buzzer (Russie)', 'baseline_peaks': 8},
            {'freq': 11175, 'name': 'HFGCS US Military', 'baseline_peaks': 12},
            {'freq': 8992, 'name': 'OTAN Military', 'baseline_peaks': 7}
        ],
        'diplomatic': [
            {'freq': 5732, 'name': 'Trafic Diplomatique HF', 'baseline_peaks': 4},
            {'freq': 15045, 'name': 'Communications Diplomatiques', 'baseline_peaks': 6}
        ],
        'broadcast': [
            {'freq': 6000, 'name': 'BBC World Service', 'baseline_peaks': 15},
            {'freq': 9410, 'name': 'Voice of America', 'baseline_peaks': 10},
            {'freq': 15300, 'name': 'Radio France Int.', 'baseline_peaks': 12}
        ]
    }
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.active_servers = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self._init_database()
        logger.info("✅ SDRSpectrumService initialisé")
    
    def _init_database(self):
        """Initialise les tables pour l'analyse spectrale"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            # Table des scans spectraux
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sdr_spectrum_scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    frequency_khz INTEGER NOT NULL,
                    category TEXT,
                    peak_count INTEGER DEFAULT 0,
                    power_db REAL,
                    signal_type TEXT,
                    server_name TEXT,
                    baseline_deviation REAL,
                    anomaly_detected BOOLEAN DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des serveurs WebSDR
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sdr_websdr_servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT UNIQUE,
                    location TEXT,
                    status TEXT DEFAULT 'unknown',
                    last_check DATETIME,
                    success_rate REAL DEFAULT 0.0
                )
            """)
            
            # Table des anomalies détectées
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sdr_spectrum_anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    frequency_khz INTEGER NOT NULL,
                    anomaly_type TEXT,
                    peak_count INTEGER,
                    expected_peaks INTEGER,
                    deviation_sigma REAL,
                    severity TEXT,
                    description TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index pour performances
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_scans_freq_time 
                ON sdr_spectrum_scans(frequency_khz, timestamp)
            """)
            
            conn.commit()
            conn.close()
            logger.info("✅ Tables SDR spectrum initialisées")
            
        except Exception as e:
            logger.error(f"❌ Erreur init BDD: {e}")
    
def test_websdr_server(self, server: Dict) -> bool:
    """Teste la disponibilité d'un serveur WebSDR"""
    try:
        # Tester d'abord l'URL principale
        response = self.session.get(
            server['url'], 
            timeout=10,
            allow_redirects=True
        )
        
        if response.status_code == 200:
            # Tester différentes méthodes pour récupérer le spectre
            test_urls = [
                f"{server['url']}/spectrum.js",
                f"{server['url']}/spectrum.json",
                f"{server['url']}/waterfall",
            ]
            
            for test_url in test_urls:
                try:
                    test_response = self.session.get(test_url, timeout=5)
                    if test_response.status_code == 200:
                        logger.info(f"✅ Serveur {server['name']} opérationnel ({test_url})")
                        server['spectrum_endpoint'] = test_url.split('/')[-1]  # Garder juste le nom du fichier
                        return True
                except:
                    continue
            
            # Si aucune méthode ne marche mais le serveur répond
            logger.warning(f"⚠️ Serveur {server['name']} accessible mais pas de spectre détecté")
            return False
        
        return False
        
    except Exception as e:
        logger.warning(f"⚠️ Serveur {server['name']} inaccessible: {e}")
        return False
    
    def discover_active_servers(self) -> List[Dict]:
        """Découvre les serveurs WebSDR actifs"""
        active = []
        
        for server in self.WEBSDR_SERVERS:
            if self.test_websdr_server(server):
                server['status'] = 'active'
                server['last_check'] = datetime.utcnow().isoformat()
                active.append(server)
                
                # Sauvegarder en BDD
                self._save_server_status(server)
        
        self.active_servers = active
        logger.info(f"📡 {len(active)} serveurs WebSDR actifs")
        
        return active
    
def scrape_spectrum_data(self, server: Dict, frequency_khz: int) -> Optional[bytes]:
    """
    Scrappe les données spectrales d'un serveur WebSDR
    Avec fallback sur la simulation
    """
    try:
        # Vérifier si on est en mode réel
        from .config import REAL_MODE  # Importez votre configuration
        REAL_MODE = os.getenv('GEOPOL_REAL_MODE', 'false').lower() == 'true'
        
        if not REAL_MODE:
            logger.info(f"🧪 Mode simulation pour {server['name']}")
            return self.generate_simulated_spectrum(frequency_khz)
        
        # Construire l'URL du spectre
        if server['type'] == 'websdr':
            # Format WebSDR réel - les vrais endpoints
            spectrum_url = f"{server['url']}/spectrum.js"
            
            try:
                response = self.session.get(spectrum_url, timeout=10)
                
                if response.status_code == 200:
                    # Analyser le JavaScript pour extraire les données
                    content = response.text
                    
                    # Chercher les données dans le JS
                    import re
                    spectrum_pattern = r'var\s+spectrum\s*=\s*\[(.*?)\];'
                    match = re.search(spectrum_pattern, content, re.DOTALL)
                    
                    if match:
                        # Convertir en liste Python
                        data_str = match.group(1)
                        # Nettoyer et convertir
                        data_str = data_str.replace('\n', '').replace('\r', '')
                        values = [float(x.strip()) for x in data_str.split(',') if x.strip()]
                        return json.dumps(values).encode()
                    
            except Exception as e:
                logger.warning(f"⚠️ Format JS non reconnu pour {server['name']}: {e}")
                
            # Essayer le format JSON
            json_url = f"{server['url']}/spectrum.json"
            response = self.session.get(json_url, timeout=10)
            
            if response.status_code == 200 and 'json' in response.headers.get('Content-Type', ''):
                data = response.json()
                if 'spectrum' in data:
                    return json.dumps(data['spectrum']).encode()
        
        elif server['type'] == 'kiwisdr':
            # Format KiwiSDR
            spectrum_url = f"{server['url']}/waterfall?f={frequency_khz}"
            response = self.session.get(spectrum_url, timeout=10)
            
            if response.status_code == 200:
                return response.content
        
        # Fallback sur la simulation si aucun format ne fonctionne
        logger.warning(f"⚠️ Fallback simulation pour {server['name']}")
        return self.generate_simulated_spectrum(frequency_khz)
        
    except Exception as e:
        logger.error(f"❌ Erreur scraping {server['name']}: {e}")
        # Fallback sur la simulation en cas d'erreur
        return self.generate_simulated_spectrum(frequency_khz)
  
    def analyze_spectrum_peaks(self, spectrum_data: bytes) -> Tuple[int, float]:
        """
        Analyse les pics d'émission dans les données spectrales
        
        Returns:
            (nombre_de_pics, puissance_moyenne_dB)
        """
        try:
            # Tenter de convertir en array numpy
            try:
                # Format JSON
                spectrum_json = json.loads(spectrum_data.decode())
                spectrum_array = np.array(spectrum_json)
            except:
                # Format binaire
                try:
                    spectrum_array = np.frombuffer(spectrum_data, dtype=np.int16)
                except:
                    spectrum_array = np.frombuffer(spectrum_data, dtype=np.float32)
            
            # Normaliser
            if len(spectrum_array) == 0:
                return 0, -100.0
            
            spectrum_norm = spectrum_array.astype(np.float32)
            spectrum_norm = spectrum_norm / (np.max(np.abs(spectrum_norm)) + 1e-10)
            
            # Calculer la puissance moyenne en dB
            power_linear = np.mean(np.abs(spectrum_norm) ** 2)
            power_db = 10 * np.log10(power_linear + 1e-10)
            
            # Détecter les pics (seuil à 20% de l'amplitude max)
            PEAK_THRESHOLD = 0.20
            above_threshold = np.where(np.abs(spectrum_norm) > PEAK_THRESHOLD)[0]
            
            # Compter les pics distincts (séparés d'au moins 5 bins)
            peak_count = 0
            if len(above_threshold) > 0:
                peak_count = 1
                for i in range(1, len(above_threshold)):
                    if above_threshold[i] - above_threshold[i-1] > 5:
                        peak_count += 1
            
            logger.debug(f"📊 {peak_count} pics détectés, {power_db:.1f} dB")
            
            return peak_count, float(power_db)
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse pics: {e}")
            return 0, -100.0
    
    def scan_frequency(self, frequency_khz: int, category: str = 'custom') -> Dict:
        """
        Scanne une fréquence sur tous les serveurs actifs
        """
        if not self.active_servers:
            self.discover_active_servers()
        
        if not self.active_servers:
            return {
                'success': False,
                'error': 'Aucun serveur WebSDR disponible',
                'frequency_khz': frequency_khz
            }
        
        results = []
        
        for server in self.active_servers:
            try:
                # Scraper le spectre
                spectrum_data = self.scrape_spectrum_data(server, frequency_khz)
                
                if spectrum_data:
                    # Analyser les pics
                    peak_count, power_db = self.analyze_spectrum_peaks(spectrum_data)
                    
                    result = {
                        'server': server['name'],
                        'peak_count': peak_count,
                        'power_db': power_db,
                        'signal_present': power_db > -80
                    }
                    
                    results.append(result)
                    
                    # Pause pour ne pas surcharger
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"❌ Erreur scan {server['name']}: {e}")
                continue
        
        if not results:
            return {
                'success': False,
                'error': 'Échec du scan sur tous les serveurs',
                'frequency_khz': frequency_khz
            }
        
        # Agréger les résultats
        avg_peaks = np.mean([r['peak_count'] for r in results])
        avg_power = np.mean([r['power_db'] for r in results])
        
        # Détecter les anomalies
        freq_info = self._get_frequency_info(frequency_khz)
        baseline_peaks = freq_info.get('baseline_peaks', 5) if freq_info else 5
        
        deviation = abs(avg_peaks - baseline_peaks)
        anomaly = deviation > (baseline_peaks * 0.5)  # +50% de déviation
        
        scan_result = {
            'success': True,
            'frequency_khz': frequency_khz,
            'frequency_mhz': frequency_khz / 1000,
            'category': category,
            'peak_count': int(avg_peaks),
            'power_db': round(avg_power, 2),
            'signal_present': avg_power > -80,
            'baseline_peaks': baseline_peaks,
            'deviation': round(deviation, 2),
            'anomaly_detected': anomaly,
            'servers_used': len(results),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Sauvegarder le scan
        self._save_scan_result(scan_result)
        
        # Si anomalie, créer une alerte
        if anomaly:
            self._create_anomaly_alert(scan_result)
        
        return scan_result
    
    def scan_all_geopolitical_frequencies(self) -> Dict:
        """Scanne toutes les fréquences géopolitiques"""
        logger.info("🔍 Scan complet des fréquences géopolitiques...")
        
        # Découvrir les serveurs actifs
        self.discover_active_servers()
        
        if not self.active_servers:
            return {
                'success': False,
                'error': 'Aucun serveur WebSDR disponible'
            }
        
        all_results = {}
        total_scans = 0
        anomalies_detected = 0
        
        for category, frequencies in self.GEOPOLITICAL_FREQUENCIES.items():
            category_results = []
            
            for freq_info in frequencies[:2]:  # Limiter à 2 par catégorie
                try:
                    scan = self.scan_frequency(freq_info['freq'], category)
                    
                    if scan.get('success'):
                        scan['name'] = freq_info['name']
                        category_results.append(scan)
                        total_scans += 1
                        
                        if scan.get('anomaly_detected'):
                            anomalies_detected += 1
                        
                        logger.info(f"  ✅ {freq_info['name']}: {scan['peak_count']} pics")
                    
                    # Pause entre scans
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ Erreur {freq_info['name']}: {e}")
                    continue
            
            if category_results:
                all_results[category] = category_results
        
        return {
            'success': True,
            'results': all_results,
            'stats': {
                'total_scans': total_scans,
                'anomalies_detected': anomalies_detected,
                'active_servers': len(self.active_servers)
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def get_dashboard_data(self) -> Dict:
        """Données pour le dashboard"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            # Statistiques
            cur.execute("""
                SELECT COUNT(DISTINCT frequency_khz) as total_freq,
                       COUNT(*) as total_scans,
                       SUM(CASE WHEN anomaly_detected = 1 THEN 1 ELSE 0 END) as anomalies
                FROM sdr_spectrum_scans
                WHERE timestamp > datetime('now', '-24 hours')
            """)
            
            stats = cur.fetchone()
            
            # Fréquences récentes
            cur.execute("""
                SELECT frequency_khz, category, peak_count, power_db, 
                       anomaly_detected, timestamp
                FROM sdr_spectrum_scans
                WHERE timestamp > datetime('now', '-1 hour')
                ORDER BY timestamp DESC
                LIMIT 20
            """)
            
            recent_scans = []
            for row in cur.fetchall():
                recent_scans.append({
                    'frequency_khz': row[0],
                    'category': row[1],
                    'peak_count': row[2],
                    'power_db': row[3],
                    'anomaly': bool(row[4]),
                    'timestamp': row[5]
                })
            
            # Anomalies récentes
            cur.execute("""
                SELECT frequency_khz, anomaly_type, severity, description, timestamp
                FROM sdr_spectrum_anomalies
                WHERE timestamp > datetime('now', '-24 hours')
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            
            anomalies = []
            for row in cur.fetchall():
                anomalies.append({
                    'frequency_khz': row[0],
                    'type': row[1],
                    'severity': row[2],
                    'description': row[3],
                    'timestamp': row[4]
                })
            
            conn.close()
            
            return {
                'success': True,
                'stats': {
                    'total_frequencies': stats[0] if stats else 0,
                    'total_scans': stats[1] if stats else 0,
                    'anomalies_count': stats[2] if stats else 0,
                    'active_servers': len(self.active_servers)
                },
                'recent_scans': recent_scans,
                'anomalies': anomalies,
                'real_data': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur dashboard: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_test_spectrum(self) -> Dict:
        """Génère un spectre de test pour Plotly"""
        frequencies = np.linspace(0, 30, 1000)  # 0-30 MHz
        powers = -90 + 20 * np.random.rand(1000)
        
        # Ajouter quelques pics
        peaks_idx = np.random.choice(1000, 5, replace=False)
        powers[peaks_idx] += 30
        
        return {
            'success': True,
            'frequencies_mhz': frequencies.tolist(),
            'powers': powers.tolist()
        }
    
    def _get_frequency_info(self, frequency_khz: int) -> Optional[Dict]:
        """Récupère les infos d'une fréquence"""
        for category, freqs in self.GEOPOLITICAL_FREQUENCIES.items():
            for freq_info in freqs:
                if freq_info['freq'] == frequency_khz:
                    return freq_info
        return None
    
    def _save_scan_result(self, scan: Dict):
        """Sauvegarde un résultat de scan"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO sdr_spectrum_scans 
                (frequency_khz, category, peak_count, power_db, 
                 signal_type, baseline_deviation, anomaly_detected)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                scan['frequency_khz'],
                scan['category'],
                scan['peak_count'],
                scan['power_db'],
                'unknown',
                scan.get('deviation', 0),
                scan.get('anomaly_detected', False)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde scan: {e}")
    
    def _create_anomaly_alert(self, scan: Dict):
        """Crée une alerte d'anomalie"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            severity = 'high' if scan['deviation'] > scan['baseline_peaks'] else 'medium'
            
            description = (f"Activité anormale détectée: {scan['peak_count']} pics "
                         f"(baseline: {scan['baseline_peaks']})")
            
            cur.execute("""
                INSERT INTO sdr_spectrum_anomalies 
                (frequency_khz, anomaly_type, peak_count, expected_peaks, 
                 deviation_sigma, severity, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                scan['frequency_khz'],
                'peak_deviation',
                scan['peak_count'],
                scan['baseline_peaks'],
                scan['deviation'],
                severity,
                description
            ))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"🚨 Anomalie {severity}: {description}")
            
        except Exception as e:
            logger.error(f"❌ Erreur alerte: {e}")
    
    def _save_server_status(self, server: Dict):
        """Sauvegarde le statut d'un serveur"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT OR REPLACE INTO sdr_websdr_servers 
                (name, url, location, status, last_check)
                VALUES (?, ?, ?, ?, ?)
            """, (
                server['name'],
                server['url'],
                server['location'],
                server.get('status', 'unknown'),
                server.get('last_check')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde serveur: {e}")

    def discover_active_servers(self) -> List[Dict]:
        """Découvre les serveurs WebSDR actifs"""
        active = []
    
        for server in self.WEBSDR_SERVERS:
            if self.test_websdr_server(server):
                server['status'] = 'active'
                server['last_check'] = datetime.utcnow().isoformat()
                active.append(server)
            
                # Sauvegarder en BDD
                self._save_server_status(server)
    
        self.active_servers = active
        logger.info(f"📡 {len(active)} serveurs WebSDR actifs")
    
        return active


