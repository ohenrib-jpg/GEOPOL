"""
Générateur de rapports pour le module Sécurité & Gouvernance
Génère des rapports formatés (HTML, PDF, JSON) à partir des données analytics
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

# Vérifier disponibilité Jinja2
try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
    logger.info("Jinja2 disponible pour templates de rapports")
except ImportError:
    JINJA2_AVAILABLE = False
    logger.warning("Jinja2 non disponible - rapports HTML limités")

# Vérifier disponibilité weasyprint pour PDF
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
    logger.info("WeasyPrint disponible pour export PDF")
except ImportError:
    WEASYPRINT_AVAILABLE = False
    logger.warning("WeasyPrint non disponible - export PDF désactivé")


class ReportGenerator:
    """
    Générateur de rapports avancés pour Sécurité & Gouvernance
    Supporte HTML, PDF, JSON et text formats
    """

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialise le générateur de rapports

        Args:
            templates_dir: Répertoire des templates (par défaut: templates/reports)
        """
        self.templates_dir = templates_dir or os.path.join(
            os.path.dirname(__file__), '..', 'templates', 'reports'
        )

        # Créer le répertoire si nécessaire
        os.makedirs(self.templates_dir, exist_ok=True)

        # Créer templates par défaut si nécessaire
        self._create_default_templates()

        # Initialiser Jinja2 si disponible
        if JINJA2_AVAILABLE:
            self.jinja_env = Environment(
                loader=FileSystemLoader(self.templates_dir),
                autoescape=select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )
        else:
            self.jinja_env = None

    def _create_default_templates(self):
        """Crée les templates par défaut si absents"""
        default_templates = {
            'security_report.html': self._get_default_html_template(),
            'security_report_simple.html': self._get_simple_html_template()
        }

        for filename, content in default_templates.items():
            template_path = os.path.join(self.templates_dir, filename)
            if not os.path.exists(template_path):
                try:
                    with open(template_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Template créé: {filename}")
                except Exception as e:
                    logger.error(f"Erreur création template {filename}: {e}")

    def _get_default_html_template(self) -> str:
        """Retourne le template HTML par défaut"""
        return """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport Sécurité & Gouvernance - {{ report_date }}</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; color: #333; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; }
        .header h1 { margin: 0; font-size: 2.5em; }
        .header .subtitle { font-size: 1.2em; opacity: 0.9; margin-top: 10px; }
        .section { margin-bottom: 30px; padding: 20px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .section-title { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; margin-bottom: 20px; font-size: 1.5em; }
        .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric-card { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db; }
        .metric-value { font-size: 2em; font-weight: bold; color: #2c3e50; }
        .metric-label { color: #7f8c8d; font-size: 0.9em; }
        .risk-item { padding: 10px; margin: 5px 0; background: #fff; border-radius: 5px; border-left: 4px solid #e74c3c; }
        .risk-item.medium { border-left-color: #f39c12; }
        .risk-item.low { border-left-color: #27ae60; }
        .risk-type { font-weight: bold; color: #2c3e50; }
        .risk-details { color: #7f8c8d; font-size: 0.9em; margin-top: 5px; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 0.9em; text-align: center; }
        .data-source { display: inline-block; background: #ecf0f1; padding: 5px 10px; border-radius: 15px; margin-right: 5px; font-size: 0.8em; }
        .status-healthy { color: #27ae60; }
        .status-warning { color: #f39c12; }
        .status-critical { color: #e74c3c; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="header">
        <h1>Rapport Sécurité & Gouvernance</h1>
        <div class="subtitle">Analyse globale des risques sécuritaires et indicateurs de gouvernance</div>
        <div>Généré le {{ report_date }} • Sources: {% for source in data_sources %}<span class="data-source">{{ source }}</span>{% endfor %}</div>
    </div>

    {% if overview %}
    <div class="section">
        <h2 class="section-title">📊 Vue d'ensemble</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{{ overview.total_events or 0 }}</div>
                <div class="metric-label">Événements de conflit (30j)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ overview.corruption_score|default('N/A') }}</div>
                <div class="metric-label">Score corruption moyen</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ overview.total_sanctions or 0 }}</div>
                <div class="metric-label">Sanctions actives</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ overview.humanitarian_crises or 0 }}</div>
                <div class="metric-label">Crises humanitaires</div>
            </div>
        </div>
    </div>
    {% endif %}

    {% if analytics and analytics.overview and analytics.overview.sections %}
    <div class="section">
        <h2 class="section-title">📈 Graphiques détaillés</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <h3>Conflits par région</h3>
                <canvas id="conflictsChart" width="400" height="300"></canvas>
            </div>
            <div class="metric-card">
                <h3>Scores de corruption</h3>
                <canvas id="corruptionChart" width="400" height="300"></canvas>
            </div>
        </div>
        <script>
            // Données extraites des analytics
            const analyticsData = {{ analytics|tojson }};

            // Graphique conflits
            const conflictsCtx = document.getElementById('conflictsChart').getContext('2d');
            const conflictsSection = analyticsData.overview.sections.conflicts;
            if (conflictsSection && conflictsSection.statistics && conflictsSection.statistics.by_country) {
                const countries = Object.keys(conflictsSection.statistics.by_country);
                const counts = Object.values(conflictsSection.statistics.by_country);
                new Chart(conflictsCtx, {
                    type: 'bar',
                    data: {
                        labels: countries.slice(0, 8),
                        datasets: [{
                            label: 'Événements de conflit',
                            data: counts.slice(0, 8),
                            backgroundColor: '#2E86AB'
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { display: false }
                        }
                    }
                });
            }

            // Graphique corruption
            const corruptionCtx = document.getElementById('corruptionChart').getContext('2d');
            const corruptionSection = analyticsData.overview.sections.corruption;
            if (corruptionSection && corruptionSection.cpi && corruptionSection.cpi.countries) {
                const countries = corruptionSection.cpi.countries.slice(0, 6).map(c => c.country);
                const scores = corruptionSection.cpi.countries.slice(0, 6).map(c => c.cpi_score);
                new Chart(corruptionCtx, {
                    type: 'horizontalBar',
                    data: {
                        labels: countries,
                        datasets: [{
                            label: 'Score CPI (0-100)',
                            data: scores,
                            backgroundColor: '#06A77D'
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            x: { beginAtZero: true, max: 100 }
                        }
                    }
                });
            }
        </script>
    </div>
    {% endif %}

    {% if risks %}
    <div class="section">
        <h2 class="section-title">🚨 Principaux risques identifiés</h2>
        {% for risk in risks %}
        <div class="risk-item {{ risk.severity }}">
            <div class="risk-type">{{ risk.type|replace('_', ' ')|title }}</div>
            <div class="risk-details">{{ risk.indicator }} • {{ risk.country or risk.program or risk.crisis_type }}</div>
        </div>
        {% endfor %}
    </div>
    {% endif %}

    {% if cache_stats %}
    <div class="section">
        <h2 class="section-title">💾 Statistiques du cache</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{{ cache_stats.total_files or 0 }}</div>
                <div class="metric-label">Fichiers cache</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ cache_stats.total_size_mb|default(0)|round(2) }} MB</div>
                <div class="metric-label">Taille totale</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{{ cache_stats.source_count or 0 }}</div>
                <div class="metric-label">Sources actives</div>
            </div>
            <div class="metric-card">
                <div class="metric-value status-{{ cache_health.status|default('healthy') }}">{{ cache_health.status|default('healthy')|title }}</div>
                <div class="metric-label">Santé du cache</div>
            </div>
        </div>
    </div>
    {% endif %}

    <div class="section">
        <h2 class="section-title">📈 Tendances et recommandations</h2>
        <p><strong>Direction:</strong> {{ trends.direction|default('stable')|title }}</p>
        <p><strong>Période analysée:</strong> {{ trends.period_months|default(6) }} mois</p>
        {% if trends.hotspots %}
        <p><strong>Zones sensibles:</strong> {{ trends.hotspots|join(', ') }}</p>
        {% endif %}
        {% if recommendations %}
        <h3>Recommandations</h3>
        <ul>
            {% for rec in recommendations %}
            <li>{{ rec }}</li>
            {% endfor %}
        </ul>
        {% endif %}
    </div>

    <div class="footer">
        <p>Rapport généré automatiquement par GEOPOL Security Analytics Dashboard</p>
        <p>© {{ current_year }} - Données sources: UCDP, Transparency International, World Bank, OFAC, UN OCHA HDX</p>
    </div>
</body>
</html>"""

    def _get_simple_html_template(self) -> str:
        """Retourne un template HTML simplifié"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Security Report - {{ report_date }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #2c3e50; }
        .section { margin: 20px 0; padding: 15px; background: #f9f9f9; border-radius: 5px; }
        .metric { margin: 10px 0; }
        .risk { padding: 10px; margin: 5px 0; border-left: 3px solid #e74c3c; }
    </style>
</head>
<body>
    <h1>Security & Governance Report</h1>
    <p>Generated: {{ report_date }}</p>

    {% if overview %}
    <div class="section">
        <h2>Overview</h2>
        {% for key, value in overview.items() %}
        <div class="metric"><strong>{{ key|replace('_', ' ')|title }}:</strong> {{ value }}</div>
        {% endfor %}
    </div>
    {% endif %}

    {% if risks %}
    <div class="section">
        <h2>Top Risks</h2>
        {% for risk in risks %}
        <div class="risk">
            <strong>{{ risk.type|replace('_', ' ')|title }}</strong>: {{ risk.indicator }}
            {% if risk.country %}({{ risk.country }}){% endif %}
        </div>
        {% endfor %}
    </div>
    {% endif %}
</body>
</html>"""

    def generate_html_report(self,
                           analytics_data: Dict[str, Any],
                           cache_stats: Optional[Dict[str, Any]] = None,
                           cache_health: Optional[Dict[str, Any]] = None,
                           template_name: str = 'security_report.html') -> str:
        """
        Génère un rapport HTML formaté

        Args:
            analytics_data: Données du dashboard analytics
            cache_stats: Statistiques du cache (optionnel)
            cache_health: Santé du cache (optionnel)
            template_name: Nom du template à utiliser

        Returns:
            HTML généré
        """
        if not self.jinja_env:
            return "<html><body>Jinja2 non disponible pour génération HTML</body></html>"

        try:
            # Préparer données pour template
            template_data = {
                'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'current_year': datetime.now().year,
                'data_sources': analytics_data.get('data_sources', []),
                'overview': self._extract_overview_metrics(analytics_data),
                'risks': analytics_data.get('top_risks', {}).get('risks', [])[:10],
                'trends': analytics_data.get('trends', {}).get('trends', {}),
                'cache_stats': cache_stats,
                'cache_health': cache_health,
                'recommendations': self._generate_recommendations(analytics_data, cache_stats, cache_health),
                'analytics': analytics_data  # Données complètes pour graphiques avancés
            }

            # Charger et rendre template
            template = self.jinja_env.get_template(template_name)
            html_content = template.render(**template_data)

            return html_content

        except Exception as e:
            logger.error(f"Erreur génération HTML: {e}")
            return f"<html><body>Erreur génération rapport: {str(e)}</body></html>"

    def generate_pdf_report(self,
                          analytics_data: Dict[str, Any],
                          cache_stats: Optional[Dict[str, Any]] = None,
                          cache_health: Optional[Dict[str, Any]] = None,
                          output_path: Optional[str] = None) -> Optional[str]:
        """
        Génère un rapport PDF

        Args:
            analytics_data: Données du dashboard analytics
            cache_stats: Statistiques du cache (optionnel)
            cache_health: Santé du cache (optionnel)
            output_path: Chemin de sortie (optionnel)

        Returns:
            Chemin du fichier PDF généré ou None
        """
        if not WEASYPRINT_AVAILABLE:
            logger.error("WeasyPrint non disponible pour génération PDF")
            return None

        try:
            # Générer HTML d'abord
            html_content = self.generate_html_report(
                analytics_data, cache_stats, cache_health
            )

            # Déterminer chemin de sortie
            if not output_path:
                reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
                os.makedirs(reports_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(reports_dir, f'security_report_{timestamp}.pdf')

            # Générer PDF
            HTML(string=html_content).write_pdf(output_path)
            logger.info(f"Rapport PDF généré: {output_path}")

            return output_path

        except Exception as e:
            logger.error(f"Erreur génération PDF: {e}")
            return None

    def generate_json_report(self,
                           analytics_data: Dict[str, Any],
                           cache_stats: Optional[Dict[str, Any]] = None,
                           cache_health: Optional[Dict[str, Any]] = None) -> str:
        """
        Génère un rapport JSON structuré

        Args:
            analytics_data: Données du dashboard analytics
            cache_stats: Statistiques du cache (optionnel)
            cache_health: Santé du cache (optionnel)

        Returns:
            JSON string formaté
        """
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'report_type': 'security_governance_analysis',
                'version': '1.0.0'
            },
            'analytics': analytics_data,
            'cache': {
                'stats': cache_stats,
                'health': cache_health
            } if cache_stats else {},
            'summary': self._generate_summary(analytics_data, cache_stats, cache_health)
        }

        return json.dumps(report, indent=2, default=str)

    def generate_text_report(self,
                           analytics_data: Dict[str, Any],
                           cache_stats: Optional[Dict[str, Any]] = None,
                           cache_health: Optional[Dict[str, Any]] = None) -> str:
        """
        Génère un rapport textuel simple

        Args:
            analytics_data: Données du dashboard analytics
            cache_stats: Statistiques du cache (optionnel)
            cache_health: Santé du cache (optionnel)

        Returns:
            Rapport textuel
        """
        lines = []
        lines.append("=" * 80)
        lines.append("RAPPORT SÉCURITÉ & GOUVERNANCE".center(80))
        lines.append("=" * 80)
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Vue d'ensemble
        overview = self._extract_overview_metrics(analytics_data)
        if overview:
            lines.append("VUE D'ENSEMBLE")
            lines.append("-" * 80)
            for key, value in overview.items():
                lines.append(f"  {key.replace('_', ' ').title()}: {value}")
            lines.append("")

        # Risques
        risks = analytics_data.get('top_risks', {}).get('risks', [])[:10]
        if risks:
            lines.append("TOP RISQUES")
            lines.append("-" * 80)
            for i, risk in enumerate(risks, 1):
                severity_icon = "🔴" if risk.get('severity') == 'high' else "🟠" if risk.get('severity') == 'medium' else "🟢"
                lines.append(f"  {i}. {severity_icon} {risk.get('type', '').replace('_', ' ').title()}")
                lines.append(f"     {risk.get('indicator', '')}")
                if risk.get('country'):
                    lines.append(f"     Pays: {risk.get('country')}")
                lines.append("")

        # Cache
        if cache_stats and cache_stats.get('available'):
            lines.append("STATISTIQUES CACHE")
            lines.append("-" * 80)
            lines.append(f"  Fichiers: {cache_stats.get('total_files', 0)}")
            lines.append(f"  Taille: {cache_stats.get('total_size_mb', 0)} MB")
            lines.append(f"  Sources: {cache_stats.get('source_count', 0)}")
            lines.append("")

        return "\n".join(lines)

    def _extract_overview_metrics(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les métriques principales pour le rapport"""
        overview = analytics_data.get('overview', {})
        if not overview or not overview.get('available'):
            return {}

        metrics = {}

        # Conflits
        conflicts = overview.get('sections', {}).get('conflicts', {})
        if conflicts.get('status') == 'success':
            metrics['total_events'] = conflicts.get('total_events', 0)

        # Corruption
        corruption = overview.get('sections', {}).get('corruption', {})
        if corruption.get('status') == 'success':
            cpi_score = corruption.get('cpi', {}).get('average_score')
            wb_score = corruption.get('world_bank', {}).get('average_score')
            if cpi_score or wb_score:
                metrics['corruption_score'] = cpi_score or wb_score

        # Sanctions
        sanctions = overview.get('sections', {}).get('sanctions', {})
        if sanctions.get('status') == 'success':
            metrics['total_sanctions'] = sanctions.get('total_entries', 0)

        # Humanitaire
        humanitarian = overview.get('sections', {}).get('humanitarian', {})
        if humanitarian.get('status') == 'success':
            metrics['humanitarian_crises'] = humanitarian.get('datasets', 0)

        return metrics

    def _generate_summary(self,
                         analytics_data: Dict[str, Any],
                         cache_stats: Optional[Dict[str, Any]] = None,
                         cache_health: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Génère un résumé exécutif"""
        overview = self._extract_overview_metrics(analytics_data)
        risks = analytics_data.get('top_risks', {}).get('risks', [])[:5]

        summary = {
            'total_risks_identified': len(risks),
            'critical_risks': len([r for r in risks if r.get('severity') == 'high']),
            'overall_security_status': 'stable',  # À améliorer
            'key_metrics': overview,
            'cache_status': cache_health.get('status') if cache_health else 'unknown'
        }

        return summary

    def _generate_recommendations(self,
                                analytics_data: Dict[str, Any],
                                cache_stats: Optional[Dict[str, Any]] = None,
                                cache_health: Optional[Dict[str, Any]] = None) -> list:
        """Génère des recommandations basées sur les données"""
        recommendations = []
        risks = analytics_data.get('top_risks', {}).get('risks', [])[:10]

        # Recommandations basées sur les risques
        high_risks = [r for r in risks if r.get('severity') == 'high']
        if len(high_risks) > 3:
            recommendations.append("Surveillance renforcée requise: Plus de 3 risques élevés identifiés")

        # Recommandations cache
        if cache_health:
            if cache_health.get('status') == 'critical':
                recommendations.append("Action immédiate: Cache en état critique - nécessite nettoyage")
            elif cache_health.get('status') == 'warning':
                recommendations.append("Surveillance: Cache nécessite attention - vérifier stratégies TTL")

        # Recommandations générales
        recommendations.append("Revue trimestrielle recommandée: Analyser tendances et ajuster stratégies")
        recommendations.append("Intégrer sources additionnelles: Considérer ACLED, CIRI pour données enrichies")

        return recommendations

    def save_report(self,
                   content: str,
                   format: str = 'html',
                   output_dir: Optional[str] = None) -> Optional[str]:
        """
        Sauvegarde un rapport sur disque

        Args:
            content: Contenu du rapport
            format: Format ('html', 'pdf', 'json', 'txt')
            output_dir: Répertoire de sortie (optionnel)

        Returns:
            Chemin du fichier sauvegardé ou None
        """
        try:
            if not output_dir:
                output_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')

            os.makedirs(output_dir, exist_ok=True)

            # Générer nom de fichier
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'security_report_{timestamp}.{format}'
            filepath = os.path.join(output_dir, filename)

            # Sauvegarder
            if format == 'pdf' and isinstance(content, bytes):
                with open(filepath, 'wb') as f:
                    f.write(content)
            else:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

            logger.info(f"Rapport sauvegardé: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Erreur sauvegarde rapport: {e}")
            return None


def get_report_generator() -> ReportGenerator:
    """Factory pour obtenir le générateur de rapports"""
    return ReportGenerator()


__all__ = ['ReportGenerator', 'get_report_generator']