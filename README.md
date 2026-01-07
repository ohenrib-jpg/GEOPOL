                                                            GEOPOL Analytics
                                                    
                                                 
##  GEOPOL est un cadre d’analyse géopolitique modulaire conçu pour explorer, enseigner et tester des corrélations de signaux faibles hétérogènes (OSINT, données géophysiques, économiques, électromagnétiques, narratives), sans prétention prédictive ou décisionnelle.  

## Open‑source geopolitical analysis platform for education, research, and media monitoring

具备 OSINT 功能、使用本地人工智能模型的地缘政治分析与战略监测开源平台


Version : V0.8PPStable(En dev.)

### Contact : ohenri.b@gmail.com

(Readme in english below / 以下为本项目的中文 Readme)

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

*3.1 Analyse sémantique*

- Modèle RoBERTa pour la classification des sentiments
- Modèle interne “Mini‑moi” (LLM local) pour l’affinage automatique
- Modèle IA GGUF (via llama.cpp) pour l'analyse des datas, générations de rapports, suivi des alertes configurées (Futur MAJ=>RaG), et assistance en temps réel. (j'utilise    Qwen pour le développement => Mon premier choix etait....fort peu judicieux.)
- Extraction d’entités géopolitiques (SpaCy NER)
- Analyse thématique (mots‑clés, pondérations, synonymes)
  
*3.2 Veille géopolitique multisources*
  
- Flux RSS configurables
- Réseaux sociaux (X/Twitter via Nitter, Reddit =>totalement operationnel en mode "Server", mais pas de résilience des datas lors de la coupure du logiciel pour l'instant)
- Archives historiques (Archive.org, Gallica, WebTimeMachine)
- Indicateurs économiques (World Bank, Eurostat, INSEE)
- Indicateurs environnementaux (Open‑Meteo, qualité de l’air, climat, seismes, émissions EM)
  
*3.3 Cartographie GEO‑DATA*
  
- Surcouches interactives : pays, blocs géopolitiques, NER, météo, SDR
- Données Natural Earth (frontières, zones disputées)
- Indicateurs économiques et environnementaux par pays
- Timeline et évolution temporelle
  
*3.4 Module SDR (nouveau – Phase 5)*
  
- Détection d’anomalies spectrales à faible latence
- Surveillance de la couverture SDR mondiale
- Algorithme statistique (moyenne mobile + écart‑type)
- Classification des anomalies (INFO → CRITICAL)
- Intégration cartographique en temps réel
  *3.5 Archiviste comparatif* (en cours de refonte)
- Recherche analogique dans les archives historiques
- Mise en relation des situations actuelles avec des précédents historiques
- Vectorisation sémantique (en cours d’amélioration)

*3.5 Surveillance satellite grace aux sources publiques Copernicus et autres (nouveau – Phase 5)*

- En cours de test. Les fichiers sont dans ce repo, mais le blueprint n'est pas encore dans app_factory.py

*3.6 Tableau de bord analytique*
  
- Statistiques par thème, sentiment, période
- Comparaison RSS vs réseaux sociaux
- Facteur_Z (dissonance narrative)
- Indicateurs économiques et environnementaux
- Panneau de configuration avancé
  
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


**Vous pouvez consulter ce fichier pour vous familiariser avec l'interface :**

https://docs.google.com/document/d/16En08evIWGONLgTneTCkD1uWiB2Qb9V4/edit?usp=sharing&ouid=115737246611272047832&rtpof=true&sd=true


## 8. Roadmap (V0.8PP → V1.0)

Stabilisation des fonctions.
Rajout des db pour utilisations ponctuelles.
Rajout des surcouches leaflet
Fabrique de l'orchestrateur (RAG)
Mise en conformite académique
Migration "Big-Bang vers PostgreSQL
API REST ?

## **!!9. Limitations actuelles!!**

- Certaines fonctions sont encore simulées (mock)
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




#### GEOPOL Analytics

地缘政治、媒体与环境分析的开源平台
（开源许可仅限教育与科研用途）
概述
GEOPOL Analytics 是一款面向 教育机构、学术研究者与战略分析人员 的专业级分析平台。
系统集成语义分析、多源情报监测、经济与环境指标、交互式地理数据可视化等功能。
软件可在本地独立运行，无需外部依赖，也可部署在服务器上进行长期监测。

核心功能
语义与媒体分析
- 基于 RoBERTa 的情感分类
- 本地微调模型 “Mini‑moi”
- SpaCy 命名实体识别（NER）
- 主题分类（关键词、权重、同义词）
多源地缘政治监测
- RSS 新闻源
- 社交媒体（X/Twitter via Nitter、Reddit）
- 历史档案（Archive.org、Gallica、WebTimeMachine）
- 经济指标（世界银行、Eurostat、INSEE）
- 环境指标（Open‑Meteo：空气质量、气候、天气）
GEO‑DATA 地图
- 基于 Leaflet 的交互式世界地图
- Natural Earth 地理数据
- 国家级经济与环境仪表盘
- 地缘政治集团、NER 图层、气象图层
- SDR 网络活动可视化
SDR 监测（新增）
- 低延迟异常检测（移动平均 + 标准差）
- 异常等级：INFO → CRITICAL
- 全球 SDR 覆盖监测
- 实时地图集成
历史“档案比对器”
- 检索相似历史情境
- 语义向量搜索（开发中）
- 与当前指标交叉分析
综合分析仪表盘
- 30 天情感趋势
- 主题统计
- RSS 与社交媒体叙事差异
- 叙事失谐指数（Factor_Z）

| 指标                         | GEOPOL | 传统 OSINT 工具 | 经济仪表盘 | 通用 AI 工具 |
|------------------------------|--------|------------------|------------|---------------|
| 开源（限教育/科研）          | 是     | 不定             | 否         | 否            |
| 语义分析                     | 是     | 否               | 否         | 是（通用）    |
| 高级地图                     | 是     | 罕见             | 有限       | 否            |
| 经济指标                     | 是     | 否               | 是         | 否            |
| 环境指标                     | 是     | 否               | 罕见       | 否            |
| SDR 异常检测                 | 是     | 否               | 否         | 否            |
| 历史档案比对                 | 是     | 否               | 否         | 否            |
| 离线运行                     | 是     | 罕见             | 否         | 否            |
| 教育导向                     | 是     | 否               | 否         | 否            |
| 多源监测（RSS+社交）         | 是     | 是               | 否         | 否            |
| 叙事失谐指数                 | 是     | 否               | 否         | 否            |
| 可扩展性                     | 高     | 低               | 低         | 中            |

应用场景
教育（高中与大学）
- 地缘政治集团与全球指标
- 媒体叙事分析
- OSINT 入门与实践
学术研究
- 长期趋势分析
- 叙事差异研究
- 经济、环境与媒体指标的相关性研究
OSINT 与战略监测
- 多源预警信号
- 基于 SDR 的异常检测
- 与历史先例的交叉验证

安装说明
要求：
- Windows 10/11 或 Linux
- Python 3.10+
- 建议 10–12 GB RAM
运行：
- 下载仓库
- 运行 GEOPOLCMD.bat
- 打开浏览器访问：
http://localhost:5000

开发路线图（摘要）
- Phase 1： 世界银行经济数据引擎
- Phase 2： GEO‑DATA 地图（Natural Earth + Leaflet）
- Phase 3： 分析仪表盘 + Open‑Meteo
- Phase 4： 配置文件系统（导入/导出、脏状态检测）
- Phase 5： SDR 异常检测模块
- Phase 6： 档案比对器 v3（语义向量搜索）
- Phase 7： 基于 RAG 的地缘政治推理

许可
本软件的开源许可仅限教育与科研用途。
禁止商业用途或情报行动用途。


By the people, for the people




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



🔬 The Z‑Factor: A Divergence‑Based Indicator for Media–Social Asymmetry Analysis

1. Theoretical Motivation
   
Contemporary research in computational social science suggests that social tension emerges less from the absolute polarity of media discourse than from the dissonance between institutional narratives and the emotional dynamics expressed within social networks.
To formalize this phenomenon, we introduce the Z‑Factor, a divergence‑based indicator designed to quantify the misalignment between:
- media sentiment trajectories, and
- social‑network emotional responses,
while incorporating temporal asymmetry, emotional weighting, event‑level modulation, and adaptive segmentation.
A key assumption is that clivage‑inducing events (e.g., political crises, scandals, sudden policy announcements) produce abrupt narrative shifts. These shifts alter the temporal structure of reactions, requiring dynamic segmentation rather than fixed time windows.
Furthermore, empirical observations show that neutral emotional categories (neutral+, neutral–) are the most sensitive to narrative disruptions. Their evolution curves often reveal early inflection points preceding polarized reactions.
Thus, monitoring their trajectories is essential for detecting emerging tensions.

2. Model Components
   
2.1 Adaptive Temporal Segmentation
   
Unlike fixed‑window approaches, the Z‑Factor uses event‑dependent temporal segmentation.

Segments S_k are defined by:

- abrupt changes in media narrative structure
  
- spikes in social‑network activity
  
- shifts in neutral emotion distributions
  
- clustering of clivage‑inducing events
  
This ensures that divergence is computed within coherent narrative intervals, rather than arbitrary time slices.

2.2 Temporal Asymmetry

A systematic delay is observed between media publication and social reaction.

We operationalize this through:

\Delta _{lag}=6\mathrm{\  hours}

This lag may be adjusted in future versions based on event‑specific dynamics.

2.3 Instantaneous Divergence

For each media item i at time t:

The hyperbolic tangent ensures boundedness and robustness to extreme values.

2.4 Emotional Weighting

Each divergence value is modulated by an emotion‑specific weight w(i):

- anger × 1.5
  
- fear × 1.4
  
- irony × 0.7
  
- joy × 0.8
  
- neutral+ × 1.6
  
- neutral– × 1.6
  
The increased weight for neutral categories reflects their high sensitivity to narrative transitions, making them early indicators of structural dissonance.
A social‑virality coefficient (post volume in the 6‑hour window) is also included.

2.5 Segment‑Level Aggregation

For each adaptive segment S_k:

\Delta (S_k)=\sum _{i\in S_k}D(t,i)\times w(i)

This captures the cumulative divergence associated with a coherent narrative phase.

2.6 Saturation Mechanism

To prevent extreme values from dominating:

If

|\bar {\Delta }|>\theta _{sat}\quad (\theta _{sat}=5.0)

Then:

Where \gamma =0.85 ensures diminishing returns.

Else:

\Delta _{sat}=\bar {\Delta }

2.7 Event‑Level Modulation

Z=\Delta _{sat}\times modulation_{events}
Where:

- negative events > positive → × 1.3
  
- positive events > negative → × 0.8
  
This reflects the asymmetric impact of event polarity on collective dynamics.

3. Analytical Significance
   
The Z‑Factor provides a compact, interpretable measure of media–social divergence, enabling:

- early detection of narrative fractures
  
- identification of clivage‑inducing events
  
- monitoring of neutral emotion inflection points
  
- enhanced media‑literacy analysis
  
- integration into OSINT and strategic‑monitoring workflows
  
Its adaptive segmentation and emphasis on neutral‑emotion sensitivity make it particularly suited for real‑time socio‑political monitoring.



