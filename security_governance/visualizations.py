"""
Système de visualisations pour le Security Analytics Dashboard
Génère des graphiques et visualisations à partir des données agrégées

Fonctionnalités:
- Graphiques de conflits par région
- Scores de corruption (bar charts, radar charts)
- Timeline des sanctions
- Distribution des types de crises
- Top risques sécuritaires
- Tendances temporelles

Bibliothèques supportées: matplotlib, plotly
"""

import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Import des bibliothèques de visualisation
try:
    import matplotlib
    matplotlib.use('Agg')  # Backend sans GUI pour serveurs
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
    logger.info("Matplotlib disponible")
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("Matplotlib non disponible - visualisations limitées")

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
    logger.info("Plotly disponible")
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly non disponible - visualisations interactives désactivées")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("NumPy non disponible - certaines fonctionnalités limitées")


class SecurityVisualizationEngine:
    """
    Moteur de génération de visualisations pour les données sécuritaires
    """

    def __init__(self, output_dir: str = None):
        """
        Initialise le moteur de visualisation

        Args:
            output_dir: Répertoire de sortie pour les fichiers générés
        """
        self.output_dir = output_dir or os.path.join(os.getcwd(), 'visualizations')

        # Créer le répertoire si nécessaire
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
                logger.info(f"Répertoire créé: {self.output_dir}")
            except Exception as e:
                logger.warning(f"Impossible de créer {self.output_dir}: {e}")

        # Palette de couleurs professionnelle
        self.colors = {
            'primary': '#2E86AB',
            'secondary': '#A23B72',
            'success': '#06A77D',
            'warning': '#F77F00',
            'danger': '#D62828',
            'info': '#4EA8DE',
            'neutral': '#8B8C89'
        }

        # Configuration par défaut
        self.default_figsize = (12, 8)
        self.dpi = 100

    def is_available(self) -> bool:
        """Vérifie si au moins une bibliothèque de visualisation est disponible"""
        return MATPLOTLIB_AVAILABLE or PLOTLY_AVAILABLE

    def create_conflict_map(self, conflicts_data: List[Dict],
                           output_file: str = 'conflict_map.png',
                           backend: str = 'matplotlib') -> Optional[str]:
        """
        Crée une carte/visualisation des conflits par région

        Args:
            conflicts_data: Liste de données de conflits
            output_file: Nom du fichier de sortie
            backend: 'matplotlib' ou 'plotly'

        Returns:
            Chemin du fichier créé ou None
        """
        if not conflicts_data:
            logger.warning("Pas de données de conflits à visualiser")
            return None

        try:
            if backend == 'plotly' and PLOTLY_AVAILABLE:
                return self._create_conflict_map_plotly(conflicts_data, output_file)
            elif MATPLOTLIB_AVAILABLE:
                return self._create_conflict_map_matplotlib(conflicts_data, output_file)
            else:
                logger.error("Aucun backend de visualisation disponible")
                return None
        except Exception as e:
            logger.error(f"Erreur création carte conflits: {e}")
            return None

    def _create_conflict_map_matplotlib(self, conflicts_data: List[Dict],
                                       output_file: str) -> Optional[str]:
        """Crée carte des conflits avec matplotlib"""
        try:
            fig, ax = plt.subplots(figsize=self.default_figsize, dpi=self.dpi)

            # Grouper par région/pays
            regions = {}
            for conflict in conflicts_data:
                region = conflict.get('region', 'Unknown')
                if region not in regions:
                    regions[region] = []
                regions[region].append(conflict)

            # Créer bar chart horizontal
            region_names = list(regions.keys())[:15]  # Top 15
            conflict_counts = [len(regions[r]) for r in region_names]

            y_pos = range(len(region_names))
            bars = ax.barh(y_pos, conflict_counts, color=self.colors['danger'])

            ax.set_yticks(y_pos)
            ax.set_yticklabels(region_names)
            ax.set_xlabel('Nombre de conflits', fontsize=12)
            ax.set_title('Conflits armés par région', fontsize=14, fontweight='bold')
            ax.grid(axis='x', alpha=0.3)

            # Annotations
            for i, (bar, count) in enumerate(zip(bars, conflict_counts)):
                ax.text(count + 0.1, i, str(count),
                       va='center', fontsize=10)

            plt.tight_layout()

            filepath = os.path.join(self.output_dir, output_file)
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()

            logger.info(f"Carte conflits créée: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Erreur matplotlib conflict map: {e}")
            return None

    def _create_conflict_map_plotly(self, conflicts_data: List[Dict],
                                   output_file: str) -> Optional[str]:
        """Crée carte interactive des conflits avec plotly"""
        try:
            # Grouper par région
            regions = {}
            for conflict in conflicts_data:
                region = conflict.get('region', 'Unknown')
                regions[region] = regions.get(region, 0) + 1

            # Trier et limiter
            sorted_regions = sorted(regions.items(), key=lambda x: x[1], reverse=True)[:15]
            region_names = [r[0] for r in sorted_regions]
            conflict_counts = [r[1] for r in sorted_regions]

            fig = go.Figure(data=[
                go.Bar(
                    y=region_names,
                    x=conflict_counts,
                    orientation='h',
                    marker=dict(color=self.colors['danger'])
                )
            ])

            fig.update_layout(
                title='Conflits armés par région',
                xaxis_title='Nombre de conflits',
                yaxis_title='Région',
                height=600,
                showlegend=False
            )

            filepath = os.path.join(self.output_dir, output_file.replace('.png', '.html'))
            fig.write_html(filepath)

            logger.info(f"Carte conflits interactive créée: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Erreur plotly conflict map: {e}")
            return None

    def create_corruption_chart(self, corruption_data: List[Dict],
                               chart_type: str = 'bar',
                               output_file: str = 'corruption_scores.png') -> Optional[str]:
        """
        Crée un graphique des scores de corruption

        Args:
            corruption_data: Données de corruption (CPI, World Bank)
            chart_type: 'bar', 'radar', 'scatter'
            output_file: Nom du fichier

        Returns:
            Chemin du fichier créé
        """
        if not corruption_data or not MATPLOTLIB_AVAILABLE:
            logger.warning("Données ou matplotlib non disponibles")
            return None

        try:
            if chart_type == 'bar':
                return self._create_corruption_bar_chart(corruption_data, output_file)
            elif chart_type == 'radar':
                return self._create_corruption_radar_chart(corruption_data, output_file)
            else:
                logger.warning(f"Type de graphique non supporté: {chart_type}")
                return None
        except Exception as e:
            logger.error(f"Erreur création graphique corruption: {e}")
            return None

    def _create_corruption_bar_chart(self, corruption_data: List[Dict],
                                    output_file: str) -> Optional[str]:
        """Crée bar chart des scores de corruption"""
        try:
            fig, ax = plt.subplots(figsize=self.default_figsize, dpi=self.dpi)

            # Extraire top/bottom pays
            sorted_data = sorted(corruption_data,
                               key=lambda x: x.get('score', 0),
                               reverse=True)

            # Top 10 et Bottom 10
            top_10 = sorted_data[:10]
            bottom_10 = sorted_data[-10:]

            countries = [d.get('country', 'Unknown') for d in top_10 + bottom_10]
            scores = [d.get('score', 0) for d in top_10 + bottom_10]

            # Couleurs: vert pour top, rouge pour bottom
            colors = [self.colors['success']] * 10 + [self.colors['danger']] * 10

            y_pos = range(len(countries))
            bars = ax.barh(y_pos, scores, color=colors)

            ax.set_yticks(y_pos)
            ax.set_yticklabels(countries, fontsize=9)
            ax.set_xlabel('Score de corruption (plus élevé = moins corrompu)', fontsize=11)
            ax.set_title('Scores de corruption - Meilleurs et pires pays',
                        fontsize=14, fontweight='bold')
            ax.axhline(y=9.5, color='black', linestyle='--', linewidth=1, alpha=0.5)
            ax.grid(axis='x', alpha=0.3)

            # Légende
            top_patch = mpatches.Patch(color=self.colors['success'], label='Top 10 (moins corrompus)')
            bottom_patch = mpatches.Patch(color=self.colors['danger'], label='Bottom 10 (plus corrompus)')
            ax.legend(handles=[top_patch, bottom_patch], loc='lower right')

            plt.tight_layout()

            filepath = os.path.join(self.output_dir, output_file)
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()

            logger.info(f"Graphique corruption créé: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Erreur bar chart corruption: {e}")
            return None

    def _create_corruption_radar_chart(self, corruption_data: List[Dict],
                                      output_file: str) -> Optional[str]:
        """Crée radar chart pour comparer pays"""
        try:
            if not NUMPY_AVAILABLE:
                logger.warning("NumPy requis pour radar chart")
                return None

            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'), dpi=self.dpi)

            # Sélectionner 5-8 pays significatifs
            selected = corruption_data[:8]

            categories = [d.get('country', 'Unknown')[:15] for d in selected]
            values = [d.get('score', 0) for d in selected]

            # Nombre de variables
            N = len(categories)

            # Angles pour chaque axe
            angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
            values += values[:1]
            angles += angles[:1]

            ax.plot(angles, values, 'o-', linewidth=2, color=self.colors['primary'])
            ax.fill(angles, values, alpha=0.25, color=self.colors['primary'])
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories, fontsize=9)
            ax.set_ylim(0, 100)
            ax.set_title('Comparaison scores de corruption',
                        fontsize=14, fontweight='bold', pad=20)
            ax.grid(True)

            plt.tight_layout()

            filepath = os.path.join(self.output_dir, output_file)
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()

            logger.info(f"Radar chart corruption créé: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Erreur radar chart: {e}")
            return None

    def create_sanctions_timeline(self, sanctions_data: List[Dict],
                                 output_file: str = 'sanctions_timeline.png') -> Optional[str]:
        """
        Crée une timeline des sanctions

        Args:
            sanctions_data: Données de sanctions OFAC
            output_file: Nom du fichier

        Returns:
            Chemin du fichier créé
        """
        if not sanctions_data or not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(14, 6), dpi=self.dpi)

            # Grouper par programme de sanctions
            programs = {}
            for sanction in sanctions_data:
                program = sanction.get('program', 'Unknown')
                programs[program] = programs.get(program, 0) + 1

            # Trier par nombre
            sorted_programs = sorted(programs.items(), key=lambda x: x[1], reverse=True)[:12]
            program_names = [p[0] for p in sorted_programs]
            counts = [p[1] for p in sorted_programs]

            # Créer bar chart
            bars = ax.bar(range(len(program_names)), counts,
                         color=self.colors['warning'])

            ax.set_xticks(range(len(program_names)))
            ax.set_xticklabels(program_names, rotation=45, ha='right', fontsize=9)
            ax.set_ylabel('Nombre de sanctions', fontsize=11)
            ax.set_title('Sanctions par programme (OFAC SDN)',
                        fontsize=14, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)

            # Annotations
            for bar, count in zip(bars, counts):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{count}', ha='center', va='bottom', fontsize=9)

            plt.tight_layout()

            filepath = os.path.join(self.output_dir, output_file)
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()

            logger.info(f"Timeline sanctions créée: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Erreur timeline sanctions: {e}")
            return None

    def create_crisis_distribution(self, crisis_data: Dict[str, int],
                                  output_file: str = 'crisis_distribution.png') -> Optional[str]:
        """
        Crée un graphique de distribution des types de crises

        Args:
            crisis_data: Dict {type_de_crise: count}
            output_file: Nom du fichier

        Returns:
            Chemin du fichier créé
        """
        if not crisis_data or not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(10, 8), dpi=self.dpi)

            # Préparer données
            crisis_types = list(crisis_data.keys())
            counts = list(crisis_data.values())

            # Créer pie chart
            colors_list = [self.colors['danger'], self.colors['warning'],
                          self.colors['info'], self.colors['secondary'],
                          self.colors['neutral'], self.colors['primary']]

            wedges, texts, autotexts = ax.pie(counts, labels=crisis_types,
                                              autopct='%1.1f%%',
                                              colors=colors_list[:len(crisis_types)],
                                              startangle=90)

            # Style
            for text in texts:
                text.set_fontsize(11)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(10)
                autotext.set_fontweight('bold')

            ax.set_title('Distribution des types de crises humanitaires',
                        fontsize=14, fontweight='bold')

            plt.tight_layout()

            filepath = os.path.join(self.output_dir, output_file)
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()

            logger.info(f"Distribution crises créée: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Erreur distribution crises: {e}")
            return None

    def create_top_risks_chart(self, risks_data: List[Dict],
                              output_file: str = 'top_risks.png') -> Optional[str]:
        """
        Crée un graphique des principaux risques sécuritaires

        Args:
            risks_data: Liste de risques avec scores
            output_file: Nom du fichier

        Returns:
            Chemin du fichier créé
        """
        if not risks_data or not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=self.default_figsize, dpi=self.dpi)

            # Extraire top 15 risques
            top_risks = risks_data[:15]

            risk_labels = [r.get('label', 'Unknown') for r in top_risks]
            risk_scores = [r.get('score', 0) for r in top_risks]
            risk_types = [r.get('type', 'unknown') for r in top_risks]

            # Couleurs par type
            color_map = {
                'conflict': self.colors['danger'],
                'corruption': self.colors['warning'],
                'sanctions': self.colors['info'],
                'humanitarian': self.colors['secondary'],
                'unknown': self.colors['neutral']
            }
            colors_list = [color_map.get(t, self.colors['neutral']) for t in risk_types]

            y_pos = range(len(risk_labels))
            bars = ax.barh(y_pos, risk_scores, color=colors_list)

            ax.set_yticks(y_pos)
            ax.set_yticklabels(risk_labels, fontsize=9)
            ax.set_xlabel('Score de risque', fontsize=11)
            ax.set_title('Principaux risques sécuritaires identifiés',
                        fontsize=14, fontweight='bold')
            ax.grid(axis='x', alpha=0.3)

            # Légende
            patches = [mpatches.Patch(color=color_map[t], label=t.replace('_', ' ').title())
                      for t in set(risk_types)]
            ax.legend(handles=patches, loc='lower right')

            plt.tight_layout()

            filepath = os.path.join(self.output_dir, output_file)
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()

            logger.info(f"Graphique top risques créé: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Erreur top risks chart: {e}")
            return None

    def create_trends_chart(self, trends_data: Dict[str, List],
                           output_file: str = 'trends_analysis.png') -> Optional[str]:
        """
        Crée un graphique d'évolution des tendances

        Args:
            trends_data: Dict avec séries temporelles
            output_file: Nom du fichier

        Returns:
            Chemin du fichier créé
        """
        if not trends_data or not MATPLOTLIB_AVAILABLE:
            return None

        try:
            fig, ax = plt.subplots(figsize=(14, 7), dpi=self.dpi)

            # Tracer chaque série
            for metric, values in trends_data.items():
                if isinstance(values, list) and values:
                    ax.plot(range(len(values)), values,
                           marker='o', linewidth=2, label=metric)

            ax.set_xlabel('Période', fontsize=11)
            ax.set_ylabel('Valeur', fontsize=11)
            ax.set_title('Évolution des tendances sécuritaires',
                        fontsize=14, fontweight='bold')
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)

            plt.tight_layout()

            filepath = os.path.join(self.output_dir, output_file)
            plt.savefig(filepath, dpi=self.dpi, bbox_inches='tight')
            plt.close()

            logger.info(f"Graphique tendances créé: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Erreur trends chart: {e}")
            return None

    def generate_dashboard_visualizations(self, analytics_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Génère toutes les visualisations du dashboard à partir des données analytics

        Args:
            analytics_data: Données du SecurityAnalyticsDashboard

        Returns:
            Dict {type_visualisation: chemin_fichier}
        """
        results = {}

        try:
            # 1. Carte des conflits
            if 'conflicts' in analytics_data:
                conflicts = analytics_data['conflicts'].get('data', [])
                if conflicts:
                    filepath = self.create_conflict_map(conflicts)
                    if filepath:
                        results['conflict_map'] = filepath

            # 2. Graphique corruption
            if 'corruption' in analytics_data:
                corruption = analytics_data['corruption'].get('data', [])
                if corruption:
                    filepath = self.create_corruption_chart(corruption, chart_type='bar')
                    if filepath:
                        results['corruption_bar'] = filepath

            # 3. Timeline sanctions
            if 'sanctions' in analytics_data:
                sanctions = analytics_data['sanctions'].get('data', [])
                if sanctions:
                    filepath = self.create_sanctions_timeline(sanctions)
                    if filepath:
                        results['sanctions_timeline'] = filepath

            # 4. Distribution crises
            if 'humanitarian' in analytics_data:
                humanitarian = analytics_data['humanitarian']
                crisis_types = humanitarian.get('crisis_types', [])
                if crisis_types:
                    # Créer dict de distribution
                    crisis_dist = {ct: 1 for ct in crisis_types}
                    filepath = self.create_crisis_distribution(crisis_dist)
                    if filepath:
                        results['crisis_distribution'] = filepath

            logger.info(f"Dashboard visualizations générées: {len(results)} fichiers")
            return results

        except Exception as e:
            logger.error(f"Erreur génération dashboard visualizations: {e}")
            return results

    def export_visualization_report(self, visualizations: Dict[str, str],
                                   output_file: str = 'visualization_report.json') -> Optional[str]:
        """
        Exporte un rapport JSON des visualisations générées

        Args:
            visualizations: Dict {type: filepath}
            output_file: Nom du fichier JSON

        Returns:
            Chemin du fichier rapport
        """
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'total_visualizations': len(visualizations),
                'visualizations': visualizations,
                'output_directory': self.output_dir
            }

            filepath = os.path.join(self.output_dir, output_file)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            logger.info(f"Rapport visualisations exporté: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Erreur export rapport: {e}")
            return None


def get_visualization_engine(output_dir: str = None) -> SecurityVisualizationEngine:
    """Factory pour obtenir le moteur de visualisation"""
    return SecurityVisualizationEngine(output_dir=output_dir)


__all__ = ['SecurityVisualizationEngine', 'get_visualization_engine']
