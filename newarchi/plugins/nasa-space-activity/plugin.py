# -*- coding: utf-8 -*-
"""
Plugin: NASA Space Activity
Description: Suivi de l'activite spatiale NASA
Version: 1.0.0
"""

import requests
from datetime import datetime
import json

class Plugin:
    """Plugin NASA Space Activity pour GEOPOLIS"""
    
    def __init__(self, settings):
        self.settings = settings
        self.name = "nasa-space-activity"
        self.base_urls = {
            'iss': 'http://api.open-notify.org/iss-now.json',
            'apod': 'https://api.nasa.gov/planetary/apod',
            'launches': 'https://lldev.thespacedevs.com/2.2.0/launch/upcoming/'
        }
    
    def run(self, payload=None):
        """Execute le plugin avec le type d'activite specifie"""
        try:
            activity_type = payload.get('activity_type', 'iss')
            
            if activity_type == 'iss':
                return self._get_iss_position()
            elif activity_type == 'apod':
                return self._get_astronomy_picture()
            elif activity_type == 'launches':
                return self._get_upcoming_launches()
            else:
                return {
                    'success': False,
                    'error': f'Type d\'activite inconnu: {activity_type}',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur execution plugin NASA: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_iss_position(self):
        """Recupere la position actuelle de l'ISS"""
        try:
            response = requests.get(self.base_urls['iss'], timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'success': True,
                'message': 'Position ISS recuperee avec succes',
                'timestamp': datetime.now().isoformat(),
                'data': [{
                    'latitude': float(data['iss_position']['latitude']),
                    'longitude': float(data['iss_position']['longitude']),
                    'timestamp': data['timestamp']
                }],
                'metrics': {
                    'latitude': float(data['iss_position']['latitude']),
                    'longitude': float(data['iss_position']['longitude']),
                    'status': 'en_orbite'
                }
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Erreur API ISS: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_astronomy_picture(self):
        """Recupere l'image astronomique du jour de la NASA"""
        try:
            api_key = self.settings.get('api_keys', {}).get('nasa', 'DEMO_KEY')
            params = {'api_key': api_key}
            
            response = requests.get(self.base_urls['apod'], params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            result = {
                'success': True,
                'message': 'Image astronomique du jour recuperee',
                'timestamp': datetime.now().isoformat(),
                'data': [{
                    'title': data.get('title', 'Titre non disponible'),
                    'date': data.get('date', ''),
                    'explanation': data.get('explanation', ''),
                    'url': data.get('url', ''),
                    'media_type': data.get('media_type', 'image'),
                    'copyright': data.get('copyright', 'NASA')
                }],
                'metrics': {
                    'has_image': data.get('media_type') == 'image',
                    'has_copyright': 'copyright' in data,
                    'title_length': len(data.get('title', ''))
                }
            }
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Erreur API APOD: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_upcoming_launches(self):
        """Recupere les prochains lancements spatiaux"""
        try:
            response = requests.get(self.base_urls['launches'], timeout=15)
            response.raise_for_status()
            data = response.json()
            
            launches = []
            for launch in data.get('results', [])[:10]:  # Limiter a 10 lancements
                launches.append({
                    'name': launch.get('name', 'Nom inconnu'),
                    'provider': launch.get('launch_service_provider', {}).get('name', 'Inconnu'),
                    'rocket': launch.get('rocket', {}).get('configuration', {}).get('name', 'Inconnu'),
                    'pad': launch.get('pad', {}).get('name', 'Inconnu'),
                    'location': launch.get('pad', {}).get('location', {}).get('name', 'Inconnu'),
                    'window_start': launch.get('window_start', ''),
                    'status': launch.get('status', {}).get('name', 'Inconnu')
                })
            
            return {
                'success': True,
                'message': f'{len(launches)} prochains lancements recuperes',
                'timestamp': datetime.now().isoformat(),
                'data': launches,
                'metrics': {
                    'total_launches': len(launches),
                    'next_launch': launches[0]['name'] if launches else 'Aucun',
                    'status': 'calendrier_charge'
                }
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Erreur API lancements: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }