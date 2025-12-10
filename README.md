🌍 GEOPOL - Analyseur Géopolitique Intelligent
===============================================
Contact : ohenri.b@gmail.com / olivier.bellanza@ac-toulouse.fr 

(Un grand merci a DeepSeek et a Claude pour leur aide *capitale* dans ce developpement).
(PS : desole pour les accents manquants....Ce n'est pas facile avec un clavier qwerty sans stickers ;-))

Système d'analyse avancée des flux médiatiques/sociaux, d'indicateurs géopolitiques avec IA pour la veille géopolitique. Tableau de bord ETR pour la veille stratégique. Analyse en temps réel des tendances géopolitiques avec IA intégrées (RoBERTa + Deeplearning + Llama 3.2). Intégration de SpaCy pour NER (Named Entity Recognition)
Pour le "Fun", mais avec une vraie utilite =>Systeme de comtage des pics SDR sur les frequences civiles et militaires (indicateur d'activite zonale)


Seul outil pédagogique géopolitique open-source en français

Concurrents : GDELT (anglais, complexe, cher, pas toujours adapte), MediaCloud (archivé)

Approche Multi-Échelles: Du local (cartographie narrative) au global (rapports synthétiques) Correspond aux programmes scolaires (géopolitique en Term ES/L/S/sup.)


🚀 Fonctionnalités Principales
===============================

🔍 Analyse Sémantique Avancée
* RoBERTa pour l'analyse fine des sentiments et émotions + Deeplearning pour affiner les resultats (sequence de correction tout les 20 articles analyses).
* Llama 3.2 pour la génération de rapports intelligents.
* MAJ 27/11 ==> Le modele IA est egalement integre comme "assistant geopolitique" dans l'interface via fenetre flottante.
* Classification automatique par thèmes géopolitiques configurables (utiliser llama.cpp avec modele gguf).
* Spacy pour le NER (recherche et construction des réseaux d'influences=> pays, villes, organisations, personnalités ((entities = nlp(article_text).ents)).

📊 Tableaux de Bord Interactifs
Visualisation en temps réel des tendances.
Statistiques détaillées par thème et sentiment.
Évolution temporelle sur 30 jours.
Indicateurs macroéconomiques (français et inter. pour la version V.06pp, source Eurostat, WorldBank (https://data360.worldbank.org/en/api) et scrap leger INSEE) "mode scolaire".
Veille Economique en temps reel, et comparaison avec les pays de la zone Euros (utilise sources Eurostat, yFinance) "Mode etendu Recherche".
MAJ3011=> Integration en cours Surveillance des indicateurs clés (VIX (indice de peur des marchés),Pétrole Brent (baromètre géopolitique),Or (valeur refuge),taux des bonds (sentiment risque),Devises refuges (A definir)), Corrélations géopolitiques (detec. de patterns exemple :"tensions_russes": ["RTSI", "Gazprom", "Rosneft"],"crise_moyen_orient": ["pétrole", "or", "VIX"]).

🌐 Agrégation Multi-Sources
Flux RSS traditionnels.
Réseaux sociaux (Twitter via Nitter, Reddit) MAJ 0812==>Integration des "bruits" de WallStreet.
Archives historiques (Archive.org depuis 1945). **MAJ0912 => Evolution 3.0 : l'Archiviste gere a present, en plus des analyses de periodes, la Recherche Vectorielle et les Analogies Historiques. SpaCy est egalement integre pour NER, et future surcouche dans leaflet**
SpaCy NER
Sources Economiques : INSEE, Eurostat, World Bank, yFinance.
Spectrum WebSDR (surveillance des pics d'activites, **sans ecoutes**)

🤖 Intelligence Artificielle
Détection d'anomalies et tendances émergentes.
Corroboration automatique entre sources (automatisée dans la V.0.6).
Analyse bayésienne pour la confiance (automatisée dans la V.0.6).
Génération de rapports d'analyses en PDF automatisés.
Affinage des résultats automatiques (-> Deeplearning automatise dans la v.0.6).
Fonctions d'Assistance IA.

⚙️ Installation
Prérequis
Python 3.8+
llama.cpp
6GB RAM minimum (8GB pour IA rec. MINIMUM ====>Mistral 3.2 3b (Q4) 2/3 Go, RoBERTa 1,2 Go, Spacy 1 Go, serveur logiciel 1/1,5 Go)
7GB espace disque (sans compter le modèle gguf et les donnees de vos traitements. Compter 15 Go d'espace disque pour un mois d'analyses sur 200/300 sources)
(** Avant la version V.1.0, je devrais effectuer une migration big-bang, de sqlite vers Postgresql**)

                                                                          ======= A suivre ======
Travaillant seul sur ce petit projet, je ne suis plus aussi presse de terminer la "base solide", puisqu'apres commencera le GROS boulot : creation d'un pipeline RAG interne (Retrieval-Augmented Generation) pour croiser les donnees.

En cours avant 0.7PP:
=====================
Correction de leaflet pour permettre aisement les surcouches datas a venir
Evolution des fonctions du module "assistant", afin de lui donner acces et commandes aux fonctions analytiques.
