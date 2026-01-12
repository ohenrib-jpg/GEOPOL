"""
Prompts d'analyse démographique pour l'IA locale (Qwen)
Templates de prompts pour l'analyse géopolitique des données socio-démographiques
"""

from typing import Dict, List, Optional


class DemographicAnalysisPrompts:
    """
    Collection de prompts pour l'analyse démographique par l'IA
    Utilise le contexte RAG enrichi avec les données OECD, Eurostat, World Bank, INSEE
    """

    @staticmethod
    def country_profile(country_code: str, rag_context: str = "") -> str:
        """
        Génère un prompt pour un profil pays complet

        Args:
            country_code: Code ISO du pays (FR, DE, etc.)
            rag_context: Contexte enrichi depuis le RAG

        Returns:
            Prompt formaté pour Qwen
        """
        return f"""
Tu es un analyste géopolitique spécialisé en démographie et socio-économie.

MISSION: Analyse le profil socio-démographique de {country_code.upper()} en utilisant les données disponibles.

{rag_context}

INSTRUCTIONS:
1. Synthétise les indicateurs démographiques clés (population, âge, natalité, mortalité)
2. Analyse les tendances socio-économiques (éducation, santé, emploi)
3. Identifie les points forts et défis démographiques
4. Compare avec les moyennes européennes/mondiales si données disponibles
5. Projette les implications géopolitiques de ces tendances

FORMAT DE RÉPONSE:
## Profil Démographique - {country_code.upper()}

### 1. Indicateurs Démographiques
[Population totale, croissance, densité, structure par âge]

### 2. Indicateurs Socio-Économiques
[Éducation, santé, emploi, inégalités]

### 3. Tendances et Évolutions
[Analyse temporelle des changements]

### 4. Comparaison Internationale
[Position par rapport aux pairs]

### 5. Implications Géopolitiques
[Conséquences stratégiques]

SOURCES: Cite systématiquement les sources (OECD, Eurostat, World Bank, INSEE) avec les années.
""".strip()

    @staticmethod
    def demographic_comparison(countries: List[str], rag_context: str = "") -> str:
        """
        Génère un prompt pour comparer plusieurs pays

        Args:
            countries: Liste des codes pays à comparer
            rag_context: Contexte enrichi depuis le RAG

        Returns:
            Prompt formaté pour Qwen
        """
        countries_str = ", ".join([c.upper() for c in countries])

        return f"""
Tu es un analyste géopolitique spécialisé en démographie comparative.

MISSION: Compare les profils socio-démographiques de {countries_str}.

{rag_context}

INSTRUCTIONS:
1. Identifie les indicateurs clés pour chaque pays
2. Compare les forces et faiblesses relatives
3. Analyse les divergences et convergences
4. Évalue les implications géopolitiques des écarts
5. Projette les trajectoires futures

FORMAT DE RÉPONSE:
## Analyse Comparative - {countries_str}

### 1. Vue d'Ensemble
[Tableau comparatif des indicateurs clés]

### 2. Forces Relatives
[Points forts de chaque pays]

### 3. Défis Spécifiques
[Faiblesses et risques par pays]

### 4. Convergences et Divergences
[Tendances communes vs écarts]

### 5. Implications Géopolitiques
[Conséquences stratégiques des écarts démographiques]

SOURCES: Cite les données avec sources et années.
""".strip()

    @staticmethod
    def demographic_trend(indicator: str, countries: List[str], rag_context: str = "") -> str:
        """
        Génère un prompt pour analyser une tendance spécifique

        Args:
            indicator: Nom de l'indicateur (population, fécondité, etc.)
            countries: Liste des codes pays
            rag_context: Contexte enrichi depuis le RAG

        Returns:
            Prompt formaté pour Qwen
        """
        countries_str = ", ".join([c.upper() for c in countries])

        return f"""
Tu es un analyste géopolitique spécialisé en tendances démographiques.

MISSION: Analyse l'évolution de l'indicateur "{indicator}" pour {countries_str}.

{rag_context}

INSTRUCTIONS:
1. Identifie les valeurs actuelles et historiques de cet indicateur
2. Analyse les tendances temporelles (croissance, déclin, stabilité)
3. Compare les trajectoires entre pays
4. Identifie les facteurs explicatifs (politiques, économiques, culturels)
5. Projette les implications géopolitiques futures

FORMAT DE RÉPONSE:
## Analyse de Tendance: {indicator}

### 1. État Actuel
[Valeurs récentes par pays]

### 2. Évolution Historique
[Tendances sur 10-20 ans]

### 3. Comparaison Inter-Pays
[Écarts et convergences]

### 4. Facteurs Explicatifs
[Causes des tendances observées]

### 5. Projections et Implications
[Scénarios futurs et conséquences géopolitiques]

SOURCES: Données chiffrées avec sources et années.
""".strip()

    @staticmethod
    def geopolitical_impact(topic: str, rag_context: str = "") -> str:
        """
        Génère un prompt pour analyser l'impact géopolitique d'une tendance démographique

        Args:
            topic: Sujet d'analyse (vieillissement, migration, urbanisation, etc.)
            rag_context: Contexte enrichi depuis le RAG

        Returns:
            Prompt formaté pour Qwen
        """
        return f"""
Tu es un analyste géopolitique senior spécialisé en prospective démographique.

MISSION: Analyse l'impact géopolitique de "{topic}" en Europe et dans le monde.

{rag_context}

INSTRUCTIONS:
1. Synthétise les données démographiques pertinentes
2. Identifie les enjeux géopolitiques majeurs
3. Analyse les risques et opportunités stratégiques
4. Évalue les réponses politiques actuelles
5. Propose des scénarios prospectifs

FORMAT DE RÉPONSE:
## Impact Géopolitique: {topic}

### 1. État des Lieux Démographique
[Données quantitatives sur la tendance]

### 2. Enjeux Géopolitiques
[Conséquences sur l'équilibre des puissances]

### 3. Risques et Opportunités
[Menaces et leviers stratégiques]

### 4. Réponses Politiques
[Politiques publiques en place]

### 5. Scénarios Prospectifs
[Projections à 10-20 ans et implications]

APPROCHE: Analyse systémique, multi-factorielle, fondée sur les données.
SOURCES: Citations précises avec années.
""".strip()

    @staticmethod
    def custom_query(query: str, rag_context: str = "") -> str:
        """
        Génère un prompt pour une requête personnalisée

        Args:
            query: Question ou requête de l'utilisateur
            rag_context: Contexte enrichi depuis le RAG

        Returns:
            Prompt formaté pour Qwen
        """
        return f"""
Tu es un analyste géopolitique expert en données socio-démographiques.

REQUÊTE UTILISATEUR: {query}

{rag_context}

INSTRUCTIONS:
1. Analyse les données démographiques pertinentes disponibles
2. Réponds précisément à la question posée
3. Cite systématiquement les sources avec années
4. Contextualise dans une perspective géopolitique
5. Identifie les implications stratégiques

FORMAT DE RÉPONSE:
## Réponse: {query}

### Analyse des Données
[Synthèse des données pertinentes]

### Réponse Détaillée
[Réponse argumentée à la requête]

### Contexte Géopolitique
[Mise en perspective stratégique]

### Implications
[Conséquences et recommandations]

APPROCHE: Factuelle, sourcée, géopolitique.
SOURCES: Citations précises avec sources et années.
""".strip()

    @staticmethod
    def regional_analysis(region: str, focus: str = "démographie", rag_context: str = "") -> str:
        """
        Génère un prompt pour une analyse régionale

        Args:
            region: Nom de la région (Europe, Asie, etc.)
            focus: Focus de l'analyse (démographie, santé, éducation, etc.)
            rag_context: Contexte enrichi depuis le RAG

        Returns:
            Prompt formaté pour Qwen
        """
        return f"""
Tu es un analyste géopolitique régional spécialisé en {focus}.

MISSION: Analyse régionale de {region} avec focus sur {focus}.

{rag_context}

INSTRUCTIONS:
1. Cartographie les données disponibles pour la région
2. Identifie les sous-régions ou pays clés
3. Analyse les disparités intra-régionales
4. Évalue les dynamiques régionales (convergence, divergence)
5. Projette les implications géopolitiques

FORMAT DE RÉPONSE:
## Analyse Régionale: {region} - {focus}

### 1. Vue d'Ensemble
[Indicateurs agrégés pour la région]

### 2. Disparités Intra-Régionales
[Écarts entre pays/sous-régions]

### 3. Dynamiques Régionales
[Tendances communes et divergences]

### 4. Enjeux Stratégiques
[Implications géopolitiques régionales]

### 5. Perspectives
[Projections et scénarios]

APPROCHE: Comparative, territoriale, prospective.
SOURCES: Données avec sources et années.
""".strip()

    @staticmethod
    def data_quality_assessment(rag_context: str = "") -> str:
        """
        Génère un prompt pour évaluer la qualité et couverture des données

        Args:
            rag_context: Contexte enrichi depuis le RAG

        Returns:
            Prompt formaté pour Qwen
        """
        return f"""
Tu es un expert en qualité des données statistiques.

MISSION: Évalue la qualité et la couverture des données démographiques disponibles.

{rag_context}

INSTRUCTIONS:
1. Recense les sources de données disponibles (OECD, Eurostat, World Bank, INSEE)
2. Identifie les pays et indicateurs couverts
3. Évalue la fraîcheur des données (années disponibles)
4. Identifie les lacunes et manques
5. Recommande des améliorations

FORMAT DE RÉPONSE:
## Évaluation de la Qualité des Données

### 1. Sources Disponibles
[Inventaire des sources]

### 2. Couverture Géographique
[Pays couverts par source]

### 3. Couverture Indicateurs
[Types d'indicateurs disponibles]

### 4. Fraîcheur des Données
[Années les plus récentes par source]

### 5. Lacunes Identifiées
[Manques dans la couverture]

### 6. Recommandations
[Priorités d'amélioration]

APPROCHE: Audit méthodique, factuel, constructif.
""".strip()


# Fonction factory pour créer des prompts rapidement
def create_analysis_prompt(
    analysis_type: str,
    countries: Optional[List[str]] = None,
    indicator: Optional[str] = None,
    query: Optional[str] = None,
    rag_context: str = ""
) -> str:
    """
    Fonction factory pour créer des prompts d'analyse

    Args:
        analysis_type: Type d'analyse ('profile', 'comparison', 'trend', 'impact', 'custom')
        countries: Liste des codes pays
        indicator: Nom de l'indicateur (pour 'trend')
        query: Requête personnalisée (pour 'custom')
        rag_context: Contexte enrichi depuis le RAG

    Returns:
        Prompt formaté pour Qwen
    """
    prompts = DemographicAnalysisPrompts()

    if analysis_type == 'profile':
        if not countries or len(countries) == 0:
            raise ValueError("country_code required for profile analysis")
        return prompts.country_profile(countries[0], rag_context)

    elif analysis_type == 'comparison':
        if not countries or len(countries) < 2:
            raise ValueError("At least 2 countries required for comparison")
        return prompts.demographic_comparison(countries, rag_context)

    elif analysis_type == 'trend':
        if not indicator or not countries:
            raise ValueError("indicator and countries required for trend analysis")
        return prompts.demographic_trend(indicator, countries, rag_context)

    elif analysis_type == 'impact':
        if not query:
            raise ValueError("topic required for impact analysis")
        return prompts.geopolitical_impact(query, rag_context)

    elif analysis_type == 'custom':
        if not query:
            raise ValueError("query required for custom analysis")
        return prompts.custom_query(query, rag_context)

    else:
        raise ValueError(f"Unknown analysis_type: {analysis_type}")
