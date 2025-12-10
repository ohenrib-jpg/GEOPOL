🌍 GEOPOL - Analyseur Géopolitique Intelligent 
===============================================
Contact : ohenri.b@gmail.com 

**Version de développement : certaines fonctions sont encore en cours de stabilisation ou mockées pour la démo. L’essentiel du pipeline est déjà opérationnel (≈80% en mode prod).**

(Un grand merci a DeepSeek et a Claude pour leur aide *capitale* dans ce developpement).
(PS : desole pour les accents manquants....Ce n'est pas facile avec un clavier qwerty sans stickers ;-))

Système d'analyse avancée des flux médiatiques/sociaux, d'indicateurs géopolitiques avec IA pour la veille géopolitique. Tableau de bord ETR pour la veille stratégique. Analyse en temps réel des tendances géopolitiques avec IA intégrées (RoBERTa + Deeplearning + Llama 3.2). Intégration de SpaCy pour NER (Named Entity Recognition)
Pour le "Fun", mais avec une vraie utilite =>Systeme de comtage des pics SDR sur les frequences civiles et militaires (indicateur d'activite zonale)


Seul outil pédagogique géopolitique open-source en français

🎯 Positionnement
=====================
- Concurrents :
- GDELT (anglais, complexe, cher, peu adapté)
- MediaCloud (archivé)
- Approche multi‑échelles : du local (cartographie narrative) au global (rapports synthétiques).
- Publics cibles : programmes scolaires (Terminale HGGSP, Eco/Soc), chercheurs, journalistes, analystes, entreprises exposées à l’international.

🚀 Fonctionnalités principales
===============================
**🔍 Analyse sémantique avancée**
- RoBERTa : analyse fine des sentiments et émotions.
- Llama 3.2 : génération de rapports intelligents.
- SpaCy (NER) : extraction d’entités (pays, villes, organisations, personnalités).
- Classification automatique par thèmes géopolitiques (via llama.cpp + modèles gguf).
- Assistant géopolitique intégré (fenêtre flottante, MAJ 27/11).
  
**📊 Tableaux de bord interactifs**
- Visualisation en temps réel des tendances.
- Statistiques détaillées par thème et sentiment.
- Évolution temporelle sur 30 jours.
- Indicateurs macroéconomiques :
- Mode scolaire → Eurostat, INSEE.
- Mode recherche → Eurostat, yFinance, WorldBank.
- Surveillance des indicateurs clés (MAJ 30/11) :
- VIX (indice de peur des marchés)
- Pétrole Brent (baromètre géopolitique)
- Or (valeur refuge)
- Taux obligataires (sentiment risque)
- Devises refuges (à définir)
- Corrélations géopolitiques (patterns) :
- tensions_russes → RTSI, Gazprom, Rosneft
- crise_moyen_orient → pétrole, or, VIX
  
**🌐 Agrégation multi‑sources**
- Flux RSS traditionnels.
- Réseaux sociaux (Twitter via Nitter, Reddit).
- Archives historiques (Archive.org depuis 1945).
- Sources économiques : INSEE, Eurostat, WorldBank, yFinance.
- Spectrum WebSDR (surveillance des pics d’activité, sans écoute).
  
**🤖 Intelligence artificielle**
- Détection d’anomalies et tendances émergentes.
- Corroboration automatique entre sources (V.0.6).
- Analyse bayésienne pour la confiance (V.0.6).
- Génération automatique de rapports PDF.
- Affinage des résultats via Deep Learning.

**⚙️ Installation**
Installation rapide
git clone https://github.com/ohenrib-jpg/GEO.git -b GEOPOL-V.0.6-preprod
cd GEO
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

pip install -r requirements.txt
python run.py
# ou
GEOPOL.bat
# ou
GEOPOLCMD.bat   # mode debug


⚠️ N’oubliez pas d’installer llama.cpp et de placer un modèle GGUF dans le dossier /models.
👉 Les modèles GGUF sont disponibles gratuitement sur HuggingFace.

🗺️ Roadmap
- [X] Intégration des fonctions éco/macroéco
- [X] Détecteur de signaux faibles
- [X] Cartographie Leaflet.js (MAJ 30/11 → intégrée, HTML fait, routes à suivre)
- [X] MAJ 10/12===> Nouvelle architecture V3 de l'Archiviste
- [ ] --IA légère en arrière‑plan pour fine‑tuning métier (LoRA)-- MAJ 10/12=> Suivant le temps dont je dispose. Sinon, RaG directement.
- [ ] Support multilingue étendu
- [ ] API REST complète
- [ ] Applications mobiles
- [ ] Analyses prédictives
- [ ] Plugin Zotero pour export bibliographique
- [ ] Mise en conformité aux normes de recherche

🌈 Impacts potentiels
Scolaires
- Terminale HGGSP
- Terminale Éco & Soc
Formations / Chercheurs
- Journalistes et médias
- Analystes géopolitiques
- Chercheurs en sciences politiques
- Entreprises avec exposition internationale
  

Travaillant seul sur ce petit projet, je ne suis plus aussi presse de terminer la "base solide", puisqu'apres commencera le GROS boulot : creation d'un pipeline RAG interne (Retrieval-Augmented Generation) pour croiser les donnees...Et a la fin, si on y arrive, la migration "Big-Bang" vers PostgreSQL.

En cours avant 0.7PP:
=====================
Correction de leaflet pour permettre aisement les surcouches datas a venir
Evolution des fonctions du module "assistant", afin de lui donner les commandes des fonctions analytiques.
Correction du module de Deeplearning (devenu assez efficace, sauf sur certains patterns, principalement lorsque la semantique est "aleatoire")
Corrections des indices strategiques ==> ils sont "frais", mais ils ne sont pas tous "In real Time". Ce n'est pas satisfaisant.
L'onglet "Avis aux voyageurs" des indicateurs divers doit etre rectifie=> tout les sites gouvernementaux n'utilisent pas les memes formats de donnees. PAr simplicite, je compte rectifier en commencant a partir des sources US, UK et Australie, car elles ont les memes formats json.
M'acheter des stickers AZERTY pour ce clavier...





