                                                            GEOPOL Analytics
                                                    
                                                 
##  GEOPOL est un cadre d’analyse géopolitique modulaire conçu pour explorer, enseigner et tester des corrélations de signaux faibles hétérogènes (OSINT, données géophysiques, économiques, électromagnétiques, narratives), sans prétention prédictive ou décisionnelle. Il s'agit d'un outil Open Souce pour l'Education Nationale, l'Enseignement et la Recherche


## Open‑source geopolitical analysis platform for education, research, and media monitoring

Version : V0.8.20PP(En dev.)

### Contact : ohenri.b@gmail.com

(Readme in english below)

## 1. Présentation générale
GEOPOL Analytics est un logiciel open‑source conçu pour l’enseignement, la recherche et l’analyse stratégique.
Il combine :
- Analyse sémantique avancée (RoBERTa, modèles LLM locaux, SpaCy NER)
- Veille géopolitique multisources (RSS, réseaux sociaux, archives historiques)
- Indicateurs économiques et environnementaux (World Bank, Open‑Meteo, Eurostat, INSEE)
- Surcouches cartographiques interactives (Leaflet, Natural Earth)
- Détection d’anomalies SDR à faible latence
- Tableau de bord analytique complet
Le logiciel fonctionne localement, sans installation système, et peut être déployé sur un serveur pour un fonctionnement continu.

## 2. Objectifs du projet
- Fournir un outil pédagogique pour les lycées, universités et écoles spécialisées.
- Offrir une plateforme de recherche pour les analystes, journalistes et laboratoires.
- Proposer un cadre open‑source pour l’étude des tendances géopolitiques.
  
## 3. Fonctionnalités principales

*3.1 Analyse sémantique* ##(100%)

- Modèle RoBERTa pour la classification des sentiments
- Modèle interne “Mini‑moi” (LLM local) pour l’affinage automatique
- Modèle IA GGUF (via llama.cpp) pour l'analyse des datas, générations de rapports, suivi des alertes configurées (Futur MAJ=>RaG), et assistance en temps réel. (j'utilise Phi 3.2 Q4 pour le développement => Mon premier choix etait....fort peu judicieux.)
- Extraction d’entités géopolitiques (SpaCy NER)
- Analyse thématique (mots‑clés, pondérations, synonymes)
  
*3.2 Veille géopolitique multisources* ##(100%)
  
- Flux RSS configurables
- Réseaux sociaux (commentaires youtube, Reddit)
- Archives historiques (Archive.org, Gallica, WebTimeMachine, google news)
- Indicateurs économiques (World Bank, Eurostat, INSEE, FRED, COMTRADE, Akshare, yFinance)
- Indicateurs environnementaux (Open‑Meteo, qualité de l’air, climat, seismes, émissions EM, etc...)
  
*3.3 Cartographie GEO‑DATA* ## (50%)
  
- Surcouches interactives : pays, blocs géopolitiques, NER, météo, SDR
- Données Natural Earth (frontières, zones disputées)
- Indicateurs économiques et environnementaux par pays
- Timeline et évolution temporelle
  
*3.4 Module SDR (nouveau – Phase 5)* ## (70%)
  
- Détection d’anomalies spectrales à faible latence
- Surveillance de la couverture SDR mondiale
- Algorithme statistique (moyenne mobile + écart‑type)
- Classification des anomalies (INFO → CRITICAL)
- Intégration cartographique en temps réel
  
  *3.5 Archiviste comparatif*  ## (en cours de refonte +/-50%)
- Recherche analogique dans les archives historiques
- Mise en relation des situations actuelles avec des précédents historiques
- Vectorisation sémantique (en cours d’amélioration)

*3.5 Surveillance satellite grace aux sources publiques Copernicus et autres ##(65%)*

Integration d'un YOLO peu evolue permettant tout de meme une surveillance environnementale (flux routiers, incendies, urbanisation,...), voir economique (calcul des volumes remplies sur un parking, flux d'actiites des zones indistrielles,...)

*3.6 Tableau de bord analytique* ## (100%)
  
- Statistiques par thème, sentiment, période
- Comparaison RSS vs réseaux sociaux
- Facteur_Z (dissonance narrative, Version 3, voir tout en bas)
- Indicateurs économiques et environnementaux
- Panneau de configuration avancé


*3.7 Retrieval-Augmented Generation ## (+/-30%)

- IA gguf alimentee par un systeme RAG "maison"

  
*3.8 Dasboard OSoME ## (+/-75%)

- Surveillance de la viralite des patterns, et sources d'origines, sur les reseaux sociaux



## 4. Architecture du projet
GEOPOL/
│

├── Flask/

│   ├── app_factory.py

│   ├── geopol_data/

│   │   ├── connectors/ (World Bank, Open-Meteo, etc.)

│   │   ├── sdr_monitoring/ (détection d’anomalies)

│   │   ├── models.py

│   │   ├── service.py

│   │   └── templates/

│   ├── static/

│   │   ├── js/

│   │   └── css/

│   └── routes/

│
├── data/

│   └── natural_earth/, etc,...

│
├── scripts/

│   └── fetch_natural_earth.py, etc,...

│

└── GEOPOLCMD.bat        <- batch windows provisoire avec fenetres cmd apparentes 


## 5. Comparatif avec d’autres outils

| Critère                        | GEOPOL | OSINT classiques | Dashboards éco | IA généralistes |
|-------------------------------|--------|------------------|----------------|------------------|
| Open‑source                   | Oui    | Variable         | Non            | Non              |
| Analyse sémantique intégrée   | Oui    | Non              | Non            | Oui (générique)  |
| Cartographie avancée          | Oui    | Rare             | Limité         | Non              |
| Indicateurs économiques       | Oui    | Non              | Oui            | Non              |
| Indicateurs environnementaux  | Oui    | Non              | Rare           | Non              |
| Module SDR                    | Oui    | Non              | Non            | Non              |
| Archiviste historique         | Oui    | Non              | Non            | Non              |
| Hors‑ligne                    | Oui    | Rare             | Non            | Non              |
| Orientation pédagogique       | Oui    | Non              | Non            | Non              |
| Veille multisource            | Oui    | Oui              | Non            | Non              |
| Analyse de dissonance         | Oui    | Non              | Non            | Non              |
| Extensibilité                 | Élevée | Faible           | Faible         | Moyenne          |


## 6. Cas d’usage

6.1 Enseignement secondaire (HGGSP, SES)

- Étude des blocs géopolitiques
- Analyse des narratifs médiatiques
- Compréhension des indicateurs économiques
- Introduction à l’OSINT et à la veille stratégique
  
6.2 Enseignement supérieur
  
- Travaux dirigés en géopolitique, relations internationales, journalisme
- Analyse de corpus médiatiques
- Études de cas historiques comparées
- Projets de data science appliquée
  
6.3 Recherche académique
  
- Analyse temporelle des tendances géopolitiques
- Études de dissonance narrative (Facteur_Z)
- Corrélation entre indicateurs économiques, environnementaux et médiatiques
- Études sur la résilience informationnelle
  
6.4 OSINT et veille stratégique
  
- Surveillance multisource (RSS, réseaux sociaux, archives)
- Détection d’événements émergents
- Analyse spectrale SDR (activité radio, anomalies)
- Cartographie dynamique des risques

## 7. Installation

Prérequis
- Windows 10/11 ou Linux
- Python 3.10+
- 12–16 Go de RAM recommandés (sur mon Ryzen5 5600U + 16 Go re RAM sans GPU, je suis limite. Avec GPU performant, divisez par deux)
  
- Aucun package système requis (environnement virtuel isolé)
- Eventuellement : console CMD => pip install -r requirements.txt
Lancement
- Télécharger le dépôt
- Télécharger un mod. d'IA GGUF (En créant un compte gratuit sur "Hugging Face", par exemple.)

  VEILLEZ A UTILISER UNE QUANTIFICATION UTILISABLE SUR VOTRE CONFIGURATION.
  PAR DEFAUT, LE SERVEUR LLAMA DEMARRE EN MODE CPU. VOUS POUVEZ LE MODIFIER DANS LE BATCH WINDOWS
  LE MODELE DOIT ETRE PLACE DANS GEO\LLAMA.CPP\MODELS

- Exécuter GEOPOLCMD.bat <- batch windows de dev.  affichant les cmd
- Attendre le démarrage des services (15/30 secondes)
  
- Accéder à l’interface :
                                      http://localhost:5000


**Vous pouvez consulter ce fichier pour vous familiariser avec l'interface de base (ancien fichier de prise en main. Obsolete):**

https://docs.google.com/document/d/16En08evIWGONLgTneTCkD1uWiB2Qb9V4/edit?usp=sharing&ouid=115737246611272047832&rtpof=true&sd=true


## 8. Roadmap (V0.8PP → V1.0)

Stabilisation des fonctions.
Rajout des db pour utilisations ponctuelles.
Rajout des surcouches leaflet
Mise en conformite académique
Migration "Big-Bang vers PostgreSQL
debug
debug
debug
API REST ?

## **!!9. Limitations actuelles!!**

- LE LOGICIEL EST TOUJOURS EN DEV ===> TOUT N'EST PAS FONCTIONNEL
- Archiviste en cours d’amélioration
- Bataille epique contre le Commandant Zorg
- L'API Eurostat n'est pas compatissante
- OSoME en cours d'integration 
- Pas de README visuel 

##10. Licence##
Projet open‑source sous licence MIT.
Utilisation **libre pour l’enseignement, la recherche et l’analyse**.

## 11. Contribution

Les contributions sont les bienvenues :
- Documentation
- Connecteurs de données
- Surcouches cartographiques
- Amélioration du module SDR
- Optimisation du pipeline IA



#### GEOPOL Analytics

Open‑source geopolitical analysis platform for education, research, and media monitoring
Geopol Analytics is an open‑source platform designed to provide structured, transparent, and accessible geopolitical analysis.
Initially developed from the perspective of a History & Geography teacher, the project aims to support:

- educators
  
- students
  
- researchers
  
- journalists
  
- analysts
  
…by offering a modular environment for understanding media flows, socio‑economic signals, and narrative dynamics.

🚀 Key Features

🧠 Local AI Engine (GGUF)

Geopol Analytics uses a fully local AI model in GGUF format for:
- inference
- data processing
- automated report generation
This ensures:
- data sovereignty
- offline capability
- reproducibility
- transparency
No external API is required.

🔍 Retrieval‑Augmented Generation (RAG)

An integrated RAG system allows the platform to:
- cross‑reference heterogeneous datasets
- consolidate weak signals
- contextualize media and social flows
- improve the reliability of analytical outputs

🎭 Emotional Trend Comparison (BERT‑based)

A dedicated module compares:
- emotional trends in media streams
- emotional trends in social networks
It identifies:
- divergences
- dissonances
- narrative shifts
- sentiment asymmetries
This helps users understand how public discourse evolves across ecosystems.

🛰️ Lightweight OSINT Framework

Geopol Analytics includes a minimal OSINT layer based on:
- weak‑signal detection
- distributed micro‑sensors
- open‑source data streams
The goal is not intrusive intelligence gathering, but transparent, ethical, and educational monitoring.

🧩 Modular Architecture

The platform is structured into independent modules:
- media analysis
- socio‑economic indicators
- strategic monitoring
- AI inference
- RAG engine
- visualization tools
- data ingestion pipelines
Each module can evolve independently and be replaced or extended.

🎓 Educational & Research Orientation

Geopol Analytics is designed to remain:
- open‑source
- transparent
- reproducible
- accessible
It is intended for:
- classrooms
- universities
- research labs
- journalism schools
- civic education initiatives

📰 Professional Testing (Upcoming)

Once the core modules reach stable production‑ready status, the platform will be offered for free testing to a regional newspaper editorial team.
Goals:
- gather professional feedback
- validate real‑world usefulness
- improve ergonomics and workflows
- strengthen the credibility of the project
This step supports the long‑term mission:
an open‑source tool with academic rigor and operational relevance.

🛠️ Current Status (2026)

- Core architecture: stable
- Local AI inference: stable
- RAG engine: functional, improving
- Emotional comparison module: operational
- OSINT weak‑signal module: beta
- UI/UX: in progress
- Documentation: being updated

🗺️ Roadmap

Short term
- Stabilize all modules
- Improve UI/UX
- Add multilingual support
- Expand documentation
- 
Medium term
- Deploy a public demo
- Conduct testing in a newsroom
- Publish academic‑style documentation
- 
Long term
- Build a community of contributors
- Integrate additional data sources
- Develop advanced visualization dashboards



Et pour ceux qui aiment bien trainer jusqu'au "THE END" du generique de fin :

## 🔬 LE FACTEUR_Z : THÉORIE & MOTIVATION
 **Hypothèse centrale:**
> La tension sociale ne résulte PAS directement de l'intensité du discours médiatique,
> mais de la **DISSONANCE** entre la doxa médiatique et l'inconscient populaire exprimé sur les réseaux sociaux.

Il faut donc prendre en compte :
1. ✅ **La segmentation événementielle** - Analyser par contexte
2. ✅ **L'asymétrie temporelle** - Lag de 6h média → social
3. ✅ **Le poids émotionnel** - Colère/peur amplifient, ironie/humour atténuent
4. ✅ **La fonction de saturation** - Robustesse contre outliers

## 📐 FORMULE ACADÉMIQUE

**Divergence instantanée D(t,i):**
D(t,i) = tanh(RSS_sentiment(t) - Social_sentiment(t+Δlag))
où:
  - t = timestamp de l'article média
  - Δlag = 6h (asymétrie temporelle)
  - tanh normalise ∈ [-1, +1]


**Dissonance cumulée par segment Δ(Sₖ):**
Δ(Sₖ) = Σ[i∈Sₖ] D(t,i) × w(i)

où w(i) = poids combiné:
  - Poids émotionnel (anger×1.5, fear×1.4, irony×0.7, joy×0.8)
  - Viralité sociale (nombre de posts dans fenêtre 6h)


**Facteur_Z final avec saturation:**
Si |Δ̄| > θ_saturation (= 5.0):
    Δ_saturé = sign(Δ̄) × (θ + (|Δ̄| - θ) × γ)
    où γ = 0.85 (décroissance)
Sinon:
    Δ_saturé = Δ̄

Facteur_Z = Δ_saturé × modulation_événements

où modulation_événements:
  - Si événements négatifs > positifs: ×1.3 (amplification)
  - Si événements positifs > négatifs: ×0.8 (atténuation)


## **Exemple concret:**

**Scénario:** Média annonce une réforme controversée avec ton neutre (RSS = 0.1)
**Réaction sociale:** Colère massive sur Twitter (Social = -0.8)

D(t) = tanh(0.1 - (-0.8)) = tanh(0.9) = 0.72
Poids émotionnel (colère) = 1.5
Δ(segment) = 0.72 × 1.5 = 1.08
Modulation événement négatif = ×1.3
Facteur_Z = 1.08 × 1.3 = 1.40

Interprétation: "Dissonance modérée - Divergence notable"
Direction: "amplification" (médias minimisent vs social rejette)

**Différence clé:** V2 détecte que les médias **minimisent** (ton neutre) alors que le public **rejette massivement** (colère) → signal d'alerte pour les décideurs.


## **Formulation V3. Corrections des problemes majeurs releves
## ===========================================================

1. Principe résumé
- Objectif : utiliser la dynamique relative des séries neutral+ et neutral‑ sur le segment temporel en cours pour détecter une rupture narrative clivante.
- Idée clé : un croisement net (crossing) accompagné d’une inflexion forte et d’une concordance de volume (viralité) signale un événement clivant pertinent pour alimenter le Facteur_Z.

2. Prétraitement et lissage
- Agrégation temporelle : choisir une granularité adaptée (ex. 1h ou 3h) **selon volume**.
- Lissage : appliquer un **filtre robuste** (Savitzky‑Golay) pour réduire le bruit sans retarder excessivement les inflexions.
- Normalisation : standardiser chaque série par z‑score sur une fenêtre historique glissante (ex. 30 jours) pour comparabilité inter‑segments.
- Dédoublonnage : réduire l’impact des reposts/retweets en normalisant la viralité.

3. Détection de croisement net et critères de robustesse
- Détection de crossing : repérer les instants **t_c où neutral_+(t) et neutral_-(t) se croisent** (sign change of neutral_+-neutral_-).
- Conditions pour qualifier le crossing de net
- Amplitude minimale : différence pré/post crossing > seuil A_{min} (ex. 0.5 z‑score).
- Pente minimale : **dérivée moyenne sur fenêtre courte avant/après > slope threshold.**
- Concordance volumique : volume social dans la fenêtre autour de **t_c > Vmin (évite signaux sur séries très faibles).**
- Durée de maintien : la nouvelle relation (neutral+ > neutral‑ ou inverse) doit se maintenir au moins T_{hold} (ex. 6h) pour éviter flapping.
- Hystérésis : **appliquer une zone morte pour éviter oscillations rapides (ex. require change > 10% beyond previous extreme).**

4. Intégration au Facteur_Z et logique de reset
- Segment en cours : tant que le segment n’est pas reset, calculer Z comme indicateur général basé sur la dissonance moyenne pondérée.
- Trigger de clivage : **si un crossing net est détecté et validé par les critères, marquer le segment comme clivant et augmenter temporairement la pondération du Facteur_Z** 
- Reset du segment : règle de reset explicite :
- reset automatique après T_{segment\_ max} (72h) ;
- reset si la série neutral+ / neutral‑ revient à l’état antérieur et que la dérivée est nulle pendant T_{stable}.

5. Significance testing et incertitude
- Bootstrap temporel : estimer intervalle de confiance de la différence neutral_+-neutral_- autour du crossing. Si l’IC exclut zéro, crossing significatif.
- Test de permutation : vérifier que l’observation n’est pas due au hasard en permutant fenêtres temporelles.
- Score de confiance : combiner corroboration bayésienne C, p‑value bootstrap, et volume en un score Conf\in [0,1] affiché avec Z.

6. Visualisation, calibration et validation
- Visuals à produire :
- séries lissées neutral+ et neutral‑ avec zones de crossing annotées ;
- bande de confiance autour de la différence ;
- histogramme de volumes et heatmap temporelle.
**- Calibration : définir A_{min},V_{min},T_{hold},m_{cliv} sur un corpus d’événements historiques (victoires sportives, crises, armistices) via cross‑validation temporelle.**
- Validation opérationnelle : mesurer délai d’alerte, taux de faux positifs, utilité perçue par journalistes.
- Règle d’interprétation : toujours présenter Z avec son Confiance et la composante neutral crossing pour éviter sur‑interprétation.

  ## Pseudocode résumé ==>
- lissage → normalisation → calcul diff = neutral+ − neutral−
- détecter zeros de diff → pour chaque zero vérifier amplitude, pente, volume, maintien
- si validé → bootstrap CI ; si CI exclut 0 et Conf>threshold → flag clivage, augmenter Z, journaliser
- appliquer hysteresis et règles de reset.

## Précautions finales
- Ne pas confondre amplitude attentionnelle et gravité structurelle : **un crossing en période de haute réceptivité peut produire un Z élevé sans conséquence durable.**



