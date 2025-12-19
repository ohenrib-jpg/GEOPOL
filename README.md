                                                            GEOPOL Analytics
                                                    
                                                 
## Environnement open‑source pour la recherche géopolitique et la veille stratégique avec fonctions OSINT: analyse multisource, IA locales, détection d’anomalies et visualisation dynamique des indicateurs faibles

Open‑Source Platform for Geopolitical Analysis and Strategic Monitoring, with OSINT Capabilities and Local AI Models

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
- Permettre une veille OSINT structurée, transparente et reproductible.

## 3. Fonctionnalités principales

*3.1 Analyse sémantique*

- Modèle RoBERTa pour la classification des sentiments
- Modèle interne “Mini‑moi” (LLM local) pour l’affinage automatique
- Modèle IA GGUF (via llama.cpp) pour l'analyse des datas, générations de rapports, suivi des alertes configurées (Futur MAJ=>RaG), et assistance en temps réel. (j'utilise    Mistral 3.2 Q4 pour le développement => souveraineté numérique oblige)
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
- 10–12 Go de RAM recommandés
- Aucun package système requis (environnement virtuel isolé)
- Eventuellement : console CMD => pip install -r requirements.txt
Lancement
- Télécharger le dépôt
- Télécharger un mod. d'IA GGUF (En créant un compte gratuit sur "Hugging Face", par exemple.)

  VEILLEZ A UTILISER UNE QUANTIFICATION UTILISABLE SUR VOTRE CONFIGURATION.
  PAR DEFAUT, LE SERVEUR LLAMA DEMARRE EN MODE CPU. VOUS POUVEZ LE MODIFIER DANS LE BATCH WINDOWS
 
- Exécuter GEOPOLCMD.bat <- batch windows de dev.  affichant les cmd
- Attendre le démarrage des services (15/30 secondes)
  
- Accéder à l’interface :
                                      ###http://localhost:5000###


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
- Pas encore de base de données résiliente pour les réseaux sociaux
- Pas de captures d’écran dans le README (limitation GitHub actuelle)

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

Open‑Source Platform for Geopolitical, Media and Environmental Analysis
(Open‑source license strictly limited to Education and Research use)
Overview
GEOPOL Analytics is a professional‑grade analytical platform designed for education, academic research, and strategic studies.
It integrates semantic analysis, multi‑source monitoring, economic and environmental indicators, and interactive geospatial visualisation.
The system runs locally without external dependencies and can operate continuously on a server for long‑term monitoring.

Key Features
Semantic & Media Analysis
- RoBERTa‑based sentiment classification
- Local refinement model (“Mini‑moi”)
- Named Entity Recognition (SpaCy)
- Thematic classification with weighted keywords
Multi‑Source Geopolitical Monitoring
- RSS feeds (2,700+ available)
- Social media (X/Twitter via Nitter, Reddit)
- Historical archives (Archive.org, Gallica, WebTimeMachine)
- Economic indicators (World Bank, Eurostat, INSEE)
- Environmental indicators (Open‑Meteo: air quality, climate, weather)
GEO‑DATA Mapping
- Leaflet‑based interactive world map
- Natural Earth datasets
- Country‑level economic and environmental dashboards
- Geopolitical blocs, NER overlays, weather layers
- SDR network activity visualisation
SDR Monitoring (New)
- Low‑latency anomaly detection (moving average + standard deviation)
- Classification from INFO to CRITICAL
- Monitoring of global SDR network coverage
- Real‑time integration into the map
Historical “Archivist”
- Retrieval of comparable historical situations
- Semantic vector search (in progress)
- Cross‑analysis with current indicators
Analytical Dashboard
- Sentiment evolution over 30 days
- Theme‑based statistics
- RSS vs Social Media divergence
- Narrative dissonance index (Factor_Z)

**Use Cases**
Education (High School & University)
- Geopolitical blocs and global indicators
- Media literacy and narrative analysis
- OSINT introduction and practical exercises
Academic Research
- Long‑term trend analysis
- Narrative divergence studies
- Correlation between economic, environmental and media indicators
OSINT & Strategic Monitoring
- Multi‑source early‑warning signals
- SDR‑based anomaly detection
- Cross‑validation with historical precedents



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
- RSS 新闻源（超过 2700 个）
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


