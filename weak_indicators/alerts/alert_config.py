"""Gestion de la configuration des alertes"""
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class AlertConfig:
    """Gestionnaire de configuration des alertes"""
    
    def __init__(self, config_dir: str = "Geo/config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Dossiers d'archive
        self.archive_dir = Path("Geo/exports/alerts")
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Fichiers de configuration
        self.rules_file = self.config_dir / "alert_rules.yaml"
        self.settings_file = self.config_dir / "alert_settings.json"
        
        # Charger la configuration
        self.rules = self._load_rules()
        self.settings = self._load_settings()
    
    def _load_rules(self) -> List[Dict[str, Any]]:
        """Charge les règles depuis YAML"""
        if not self.rules_file.exists():
            return self._create_default_rules()
        
        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('rules', [])
        except Exception as e:
            logger.error(f"Erreur chargement règles: {e}")
            return self._create_default_rules()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Charge les paramètres depuis JSON"""
        default_settings = {
            'notifications': {
                'show_toast': True,
                'play_sound': False,
                'sound_volume': 0.5
            },
            'display': {
                'max_alerts_display': 20,
                'group_by_category': True,
                'auto_archive_days': 30
            },
            'cooldowns': {
                'info_minutes': 30,
                'warning_minutes': 15,
                'critical_minutes': 5
            }
        }
        
        if not self.settings_file.exists():
            return default_settings
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                user_settings = json.load(f)
                # Fusionner avec les valeurs par défaut
                return self._deep_merge(default_settings, user_settings)
        except Exception as e:
            logger.error(f"Erreur chargement paramètres: {e}")
            return default_settings
    
    def _create_default_rules(self) -> List[Dict[str, Any]]:
        """Crée des règles par défaut géopolitiquement neutres"""
        default_rules = [
            {
                'id': 'market_crash_7',
                'name': 'Crash boursier majeur',
                'category': 'financial',
                'enabled': True,
                'severity': 'critical',
                'condition': 'data.change_percent < -7',
                'parameters': {
                    'asset_types': ['index'],
                    'regions': ['global']
                },
                'message_template': 'CRASH: {name} chute de {change_percent}% à {current_price}'
            },
            {
                'id': 'significant_drop_5',
                'name': 'Baisse significative',
                'category': 'financial',
                'enabled': True,
                'severity': 'warning',
                'condition': 'data.change_percent < -5',
                'message_template': '{name} baisse de {change_percent}%'
            },
            {
                'id': 'high_volatility_3',
                'name': 'Haute volatilité',
                'category': 'financial',
                'enabled': True,
                'severity': 'info',
                'condition': 'abs(data.change_percent) > 3',
                'message_template': 'Volatilité: {name} {change_percent:+.2f}%'
            },
            {
                'id': 'do_not_travel',
                'name': 'Ne pas voyager',
                'category': 'travel',
                'enabled': True,
                'severity': 'critical',
                'condition': 'data.risk_level == 4',
                'parameters': {
                    'countries': []
                },
                'message_template': '⚠️ {country_name}: NIVEAU 4 - Ne pas voyager'
            },
            {
                'id': 'reconsider_travel',
                'name': 'Réenvisager le voyage',
                'category': 'travel',
                'enabled': True,
                'severity': 'warning',
                'condition': 'data.risk_level == 3',
                'message_template': '⚠️ {country_name}: NIVEAU 3 - Réenvisager'
            },
            {
                'id': 'risk_increased',
                'name': 'Risque augmenté',
                'category': 'travel',
                'enabled': True,
                'severity': 'warning',
                'condition': 'previous and data.risk_level > previous.risk_level',
                'message_template': '📈 {country_name}: Risque {previous.risk_level}→{data.risk_level}'
            },
            {
                'id': 'new_high_risk',
                'name': 'Nouveau pays haut risque',
                'category': 'travel',
                'enabled': True,
                'severity': 'info',
                'condition': 'data.risk_level >= 3 and (not previous or previous.risk_level < 3)',
                'message_template': '🆕 {country_name} maintenant risque {data.risk_level}'
            }
        ]
        
        # Sauvegarder les règles par défaut
        self.save_rules(default_rules)
        
        return default_rules
    
    def save_rules(self, rules: List[Dict[str, Any]]):
        """Sauvegarde les règles en YAML"""
        try:
            data = {
                'version': '1.0',
                'created': datetime.utcnow().isoformat(),
                'rules': rules
            }
            
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Règles sauvegardées: {len(rules)} règles")
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde règles: {e}")
            return False
    
    def save_settings(self, settings: Dict[str, Any]):
        """Sauvegarde les paramètres en JSON"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde paramètres: {e}")
            return False
    
    def archive_alert(self, alert: Dict[str, Any]):
        """Archive une alerte dans le dossier Geo/exports/alerts"""
        try:
            # Dossier par date
            date_str = datetime.now().strftime('%Y-%m-%d')
            day_dir = self.archive_dir / date_str
            day_dir.mkdir(exist_ok=True)
            
            # CSV du jour
            csv_file = day_dir / 'alerts.csv'
            
            import csv
            file_exists = csv_file.exists()
            
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    writer.writerow([
                        'Timestamp', 'ID', 'Category', 'Severity', 
                        'Rule', 'Message', 'Acknowledged', 'Data'
                    ])
                
                writer.writerow([
                    alert.get('timestamp', datetime.now().isoformat()),
                    alert.get('id', ''),
                    alert.get('category', ''),
                    alert.get('severity', ''),
                    alert.get('rule_name', ''),
                    alert.get('message', ''),
                    alert.get('acknowledged', False),
                    json.dumps(alert.get('data', {}), ensure_ascii=False)
                ])
            
            # JSON individuel pour backup
            json_file = day_dir / f"{alert.get('id', 'alert')}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(alert, f, indent=2, ensure_ascii=False, default=str)
            
            logger.debug(f"Alerte archivée: {alert.get('id')}")
            
        except Exception as e:
            logger.error(f"Erreur archivage alerte: {e}")
    
    def cleanup_old_alerts(self, days_to_keep: int = 30):
        """Nettoie les alertes archivées vieilles de plus de X jours"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for day_dir in self.archive_dir.iterdir():
                if not day_dir.is_dir():
                    continue
                
                try:
                    dir_date = datetime.strptime(day_dir.name, '%Y-%m-%d')
                    if dir_date < cutoff_date:
                        import shutil
                        shutil.rmtree(day_dir)
                        logger.info(f"Dossier archivé nettoyé: {day_dir.name}")
                except ValueError:
                    continue  # Pas un dossier de date
                    
        except Exception as e:
            logger.error(f"Erreur nettoyage archives: {e}")
    
    def _deep_merge(self, base: Dict, update: Dict) -> Dict:
        """Fusionne récursivement deux dictionnaires"""
        result = base.copy()
        
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result