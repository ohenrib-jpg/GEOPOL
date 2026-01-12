"""
Dashboard Analytics pour Module Sécurité & Gouvernance
Agrège les données de tous les connecteurs et génère des analytics avancées

Usage:
    from analytics_dashboard import SecurityAnalyticsDashboard

    dashboard = SecurityAnalyticsDashboard()
    overview = dashboard.get_global_overview()
    report = dashboard.generate_comprehensive_report()
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from collections import defaultdict

logger = logging.getLogger(__name__)

# Import des connecteurs
try:
    from .ucdp_connector import UCDPConnector
    from .transparency_cpi_connector import TransparencyCPIConnector
    from .worldbank_corruption_connector import WorldBankCorruptionConnector
    from .ofac_sdn_connector import OFACSDNConnector
    from .ocha_hdx_connector import OchaHdxConnector
    CONNECTORS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Erreur import connecteurs: {e}")
    CONNECTORS_AVAILABLE = False


class SecurityAnalyticsDashboard:
    """
    Dashboard centralisé pour analytics sécurité & gouvernance
    Agrège et analyse les données de tous les connecteurs
    """

    def __init__(self):
        """Initialise le dashboard avec tous les connecteurs"""
        self.connectors = {}

        if CONNECTORS_AVAILABLE:
            try:
                self.connectors['ucdp'] = UCDPConnector()
                self.connectors['cpi'] = TransparencyCPIConnector()
                self.connectors['worldbank'] = WorldBankCorruptionConnector()
                self.connectors['ofac'] = OFACSDNConnector()
                self.connectors['ocha'] = OchaHdxConnector()
                logger.info(f"Dashboard initialisé avec {len(self.connectors)} connecteurs")
            except Exception as e:
                logger.error(f"Erreur initialisation connecteurs: {e}")

    def is_available(self) -> bool:
        """Vérifie si le dashboard est disponible"""
        return CONNECTORS_AVAILABLE and len(self.connectors) > 0

    def get_global_overview(self) -> Dict[str, Any]:
        """
        Génère une vue d'ensemble globale de la sécurité mondiale

        Returns:
            Dict avec statistiques agrégées de tous les connecteurs
        """
        if not self.is_available():
            return {
                'success': False,
                'available': False,
                'error': 'Connecteurs non disponibles'
            }

        overview = {
            'success': True,
            'available': True,
            'timestamp': datetime.now().isoformat(),
            'data_sources': list(self.connectors.keys()),
            'sections': {}
        }

        # Section 1: Conflits (UCDP)
        try:
            ucdp_data = self.connectors['ucdp'].get_recent_conflicts(days=30, limit=100)
            if ucdp_data.get('success'):
                overview['sections']['conflicts'] = {
                    'source': 'UCDP',
                    'total_events': ucdp_data.get('total_events', 0),
                    'statistics': ucdp_data.get('statistics', {}),
                    'status': 'success'
                }
            else:
                overview['sections']['conflicts'] = {'status': 'error', 'error': ucdp_data.get('error')}
        except Exception as e:
            logger.error(f"Erreur récupération UCDP: {e}")
            overview['sections']['conflicts'] = {'status': 'error', 'error': str(e)}

        # Section 2: Corruption (CPI + World Bank)
        try:
            # CPI
            cpi_data = self.connectors['cpi'].get_cpi_data(year=2023)
            # World Bank
            wb_data = self.connectors['worldbank'].get_corruption_data(year=2022, limit=50)

            corruption_stats = {
                'source': 'CPI + World Bank',
                'status': 'success'
            }

            if cpi_data.get('success'):
                corruption_stats['cpi'] = {
                    'countries': cpi_data.get('total_countries', 0),
                    'average_score': cpi_data.get('statistics', {}).get('average_score', 0)
                }

            if wb_data.get('success'):
                corruption_stats['world_bank'] = {
                    'countries': wb_data.get('total_countries', 0),
                    'average_score': wb_data.get('statistics', {}).get('average_score', 0)
                }

            overview['sections']['corruption'] = corruption_stats
        except Exception as e:
            logger.error(f"Erreur récupération corruption: {e}")
            overview['sections']['corruption'] = {'status': 'error', 'error': str(e)}

        # Section 3: Sanctions (OFAC)
        try:
            ofac_data = self.connectors['ofac'].get_sdn_list(limit=100)
            if ofac_data.get('success'):
                overview['sections']['sanctions'] = {
                    'source': 'OFAC SDN',
                    'total_entries': ofac_data.get('count', 0),
                    'total_available': ofac_data.get('total_available', 0),
                    'status': 'success'
                }
            else:
                overview['sections']['sanctions'] = {'status': 'error', 'error': ofac_data.get('error')}
        except Exception as e:
            logger.error(f"Erreur récupération OFAC: {e}")
            overview['sections']['sanctions'] = {'status': 'error', 'error': str(e)}

        # Section 4: Crises Humanitaires (OCHA HDX)
        try:
            ocha_data = self.connectors['ocha'].get_crisis_data()
            if ocha_data.get('success'):
                overview['sections']['humanitarian'] = {
                    'source': 'UN OCHA HDX',
                    'datasets': ocha_data.get('datasets_count', 0),
                    'crisis_types': ocha_data.get('crisis_types', []),
                    'status': 'success'
                }
            else:
                overview['sections']['humanitarian'] = {'status': 'error', 'error': ocha_data.get('error')}
        except Exception as e:
            logger.error(f"Erreur récupération OCHA: {e}")
            overview['sections']['humanitarian'] = {'status': 'error', 'error': str(e)}

        return overview

    def get_country_profile(self, country_code: str) -> Dict[str, Any]:
        """
        Génère un profil complet pour un pays spécifique

        Args:
            country_code: Code ISO du pays (ex: 'SYR', 'AFG')

        Returns:
            Profil sécurité & gouvernance du pays
        """
        if not self.is_available():
            return {
                'success': False,
                'available': False,
                'error': 'Connecteurs non disponibles'
            }

        profile = {
            'success': True,
            'available': True,
            'country_code': country_code.upper(),
            'timestamp': datetime.now().isoformat(),
            'data': {}
        }

        # Corruption (World Bank)
        try:
            wb_trend = self.connectors['worldbank'].get_country_trend(country_code, years=5)
            if wb_trend.get('success'):
                profile['data']['corruption'] = {
                    'source': 'World Bank CC.EST',
                    'current_score': wb_trend.get('statistics', {}).get('current_score'),
                    'trend': wb_trend.get('statistics', {}).get('trend'),
                    'change_5_years': wb_trend.get('statistics', {}).get('score_change'),
                    'data_points': wb_trend.get('trend_data', [])
                }
        except Exception as e:
            logger.error(f"Erreur corruption pays: {e}")
            profile['data']['corruption'] = {'error': str(e)}

        # Sanctions (OFAC)
        try:
            # Mapper code pays vers nom
            country_names = {
                'SYR': 'syria', 'AFG': 'afghanistan', 'IRQ': 'iraq',
                'YEM': 'yemen', 'LBY': 'libya', 'IRN': 'iran',
                'PRK': 'north korea', 'RUS': 'russia', 'VEN': 'venezuela'
            }
            country_name = country_names.get(country_code.upper(), country_code)
            ofac_data = self.connectors['ofac'].get_sanctions_by_country(country_name, limit=50)
            if ofac_data.get('success'):
                profile['data']['sanctions'] = {
                    'source': 'OFAC SDN',
                    'total_sanctions': ofac_data.get('count', 0),
                    'entries': ofac_data.get('sanctions', [])[:10]  # Top 10
                }
        except Exception as e:
            logger.error(f"Erreur sanctions pays: {e}")
            profile['data']['sanctions'] = {'error': str(e)}

        # Crises humanitaires (OCHA HDX)
        try:
            ocha_data = self.connectors['ocha'].get_country_data(country_code.lower())
            if ocha_data.get('success'):
                profile['data']['humanitarian'] = {
                    'source': 'UN OCHA HDX',
                    'datasets': ocha_data.get('datasets_count', 0),
                    'categories': ocha_data.get('categories', {}),
                    'datasets': ocha_data.get('datasets', [])[:5]  # Top 5
                }
        except Exception as e:
            logger.error(f"Erreur humanitaire pays: {e}")
            profile['data']['humanitarian'] = {'error': str(e)}

        return profile

    def get_top_risks(self, limit: int = 10) -> Dict[str, Any]:
        """
        Identifie les principaux risques sécuritaires globaux

        Args:
            limit: Nombre de risques à retourner

        Returns:
            Liste des principaux risques classés par sévérité
        """
        if not self.is_available():
            return {
                'success': False,
                'available': False,
                'error': 'Connecteurs non disponibles'
            }

        risks = []

        # Risque 1: Zones de conflit actif (UCDP)
        try:
            conflicts = self.connectors['ucdp'].get_recent_conflicts(days=30, limit=100)
            if conflicts.get('success'):
                stats = conflicts.get('statistics', {})
                by_country = stats.get('by_country', {})

                # Top pays par nombre de conflits
                for country, count in list(by_country.items())[:5]:
                    risks.append({
                        'type': 'armed_conflict',
                        'country': country,
                        'severity': 'high' if count > 10 else 'medium',
                        'indicator': f"{count} événements violents (30 jours)",
                        'source': 'UCDP',
                        'score': count * 10  # Score pour classement
                    })
        except Exception as e:
            logger.error(f"Erreur identification conflits: {e}")

        # Risque 2: Corruption élevée (World Bank)
        try:
            wb_data = self.connectors['worldbank'].get_corruption_data(year=2022, limit=200)
            if wb_data.get('success'):
                corruption_data = wb_data.get('corruption_data', [])
                # Pays avec score < -1.0 (forte corruption)
                for item in corruption_data:
                    if item['score'] < -1.0:
                        risks.append({
                            'type': 'corruption',
                            'country': item['country_name'],
                            'severity': 'high' if item['score'] < -1.5 else 'medium',
                            'indicator': f"Score corruption: {item['score']:.2f}",
                            'source': 'World Bank',
                            'score': abs(item['score']) * 30
                        })
        except Exception as e:
            logger.error(f"Erreur identification corruption: {e}")

        # Risque 3: Sanctions internationales (OFAC)
        try:
            programs = self.connectors['ofac'].get_program_summary()
            if programs.get('success'):
                for program in programs.get('programs', [])[:5]:
                    if program['count'] > 100:  # Programmes majeurs
                        risks.append({
                            'type': 'sanctions',
                            'program': program['program'],
                            'severity': 'high' if program['count'] > 500 else 'medium',
                            'indicator': f"{program['count']} entités sanctionnées",
                            'source': 'OFAC',
                            'score': program['count'] / 10
                        })
        except Exception as e:
            logger.error(f"Erreur identification sanctions: {e}")

        # Risque 4: Crises humanitaires (OCHA)
        try:
            crisis = self.connectors['ocha'].get_crisis_data()
            if crisis.get('success'):
                crisis_types = crisis.get('crisis_types', [])
                for ctype in crisis_types:
                    risks.append({
                        'type': 'humanitarian_crisis',
                        'crisis_type': ctype,
                        'severity': 'high',
                        'indicator': f"Crise active: {ctype}",
                        'source': 'UN OCHA',
                        'score': 80  # Score fixe élevé
                    })
        except Exception as e:
            logger.error(f"Erreur identification crises: {e}")

        # Trier par score décroissant et limiter
        risks.sort(key=lambda x: x.get('score', 0), reverse=True)

        return {
            'success': True,
            'available': True,
            'timestamp': datetime.now().isoformat(),
            'total_risks': len(risks),
            'risks': risks[:limit],
            'top_risks': risks[:limit],
            'categories': {
                'armed_conflict': len([r for r in risks if r.get('type') == 'armed_conflict']),
                'corruption': len([r for r in risks if r.get('type') == 'corruption']),
                'sanctions': len([r for r in risks if r.get('type') == 'sanctions']),
                'humanitarian': len([r for r in risks if r.get('type') == 'humanitarian_crisis'])
            }
        }

    def get_trends_analysis(self, months: int = 6) -> Dict[str, Any]:
        """
        Analyse les tendances sur plusieurs mois

        Args:
            months: Nombre de mois à analyser

        Returns:
            Analyse des tendances par catégorie
        """
        if not self.is_available():
            return {
                'available': False,
                'error': 'Connecteurs non disponibles'
            }

        trends = {
            'available': True,
            'timestamp': datetime.now().isoformat(),
            'period_months': months,
            'trends': {}
        }

        # Tendance: Conflits (basé sur UCDP)
        try:
            # Récupérer données récentes
            recent = self.connectors['ucdp'].get_recent_conflicts(days=30, limit=200)
            if recent.get('success'):
                trends['trends']['conflicts'] = {
                    'direction': 'stable',  # À améliorer avec données historiques
                    'current_level': recent.get('total_events', 0),
                    'note': 'Basé sur données 30 derniers jours',
                    'hotspots': list(recent.get('statistics', {}).get('by_country', {}).keys())[:5]
                }
        except Exception as e:
            logger.error(f"Erreur tendances conflits: {e}")

        # Tendance: Corruption (World Bank historical)
        trends['trends']['corruption'] = {
            'direction': 'à analyser',
            'note': 'Nécessite données multi-années pour tendance précise'
        }

        return trends

    def generate_comprehensive_report(self) -> str:
        """
        Génère un rapport complet formaté en texte

        Returns:
            Rapport textuel complet
        """
        if not self.is_available():
            return "❌ Dashboard non disponible (connecteurs manquants)\n"

        report = []
        report.append("=" * 80)
        report.append("RAPPORT ANALYTICS SÉCURITÉ & GOUVERNANCE".center(80))
        report.append("=" * 80)
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Vue d'ensemble
        overview = self.get_global_overview()
        if overview.get('available'):
            report.append("📊 VUE D'ENSEMBLE GLOBALE")
            report.append("-" * 80)
            report.append(f"Sources de données actives: {len(overview['data_sources'])}")
            report.append("")

            for section_name, section_data in overview['sections'].items():
                if section_data.get('status') == 'success':
                    report.append(f"  ✅ {section_name.upper()}")
                    for key, value in section_data.items():
                        if key not in ['status', 'source']:
                            report.append(f"     - {key}: {value}")
                else:
                    report.append(f"  ❌ {section_name.upper()}: {section_data.get('error', 'Erreur')}")
                report.append("")

        # Top risques
        risks = self.get_top_risks(limit=10)
        if risks.get('available'):
            report.append("🚨 TOP 10 RISQUES SÉCURITAIRES")
            report.append("-" * 80)
            for i, risk in enumerate(risks['top_risks'], 1):
                severity_icon = "🔴" if risk['severity'] == 'high' else "🟠"
                report.append(f"  {i}. {severity_icon} {risk['type'].upper()}")
                report.append(f"     {risk.get('indicator', 'N/A')}")
                if 'country' in risk:
                    report.append(f"     Pays: {risk['country']}")
                report.append(f"     Source: {risk['source']}")
                report.append("")

        report.append("=" * 80)

        return "\n".join(report)

    def export_data(self, format: str = 'json') -> Any:
        """
        Exporte toutes les données dans un format spécifique

        Args:
            format: Format d'export ('json', 'dict')

        Returns:
            Données exportées
        """
        data = {
            'timestamp': datetime.now().isoformat(),
            'dashboard_version': '1.0.0',
            'overview': self.get_global_overview(),
            'top_risks': self.get_top_risks(limit=20),
            'trends': self.get_trends_analysis()
        }

        if format == 'json':
            return json.dumps(data, indent=2, default=str)
        else:
            return data


def get_security_analytics_dashboard() -> SecurityAnalyticsDashboard:
    """Factory pour obtenir le dashboard"""
    return SecurityAnalyticsDashboard()


__all__ = ['SecurityAnalyticsDashboard', 'get_security_analytics_dashboard']
