# Module Indicateurs Économiques Internationaux

## 📊 Vue d'ensemble

Le module **Indicateurs Économiques Internationaux** est une extension complète de GEOPOL Analytics permettant de surveiller et analyser les marchés financiers mondiaux, les indicateurs macroéconomiques et les sanctions internationales en temps réel.

## ✨ Fonctionnalités

### 1. **Marchés Financiers (yFinance)**
- Indices boursiers mondiaux (S&P 500, Dow Jones, NASDAQ, FTSE, DAX, Shanghai, Hang Seng, Nikkei)
- Matières premières (Or, Argent, Pétrole WTI/Brent, Gaz naturel)
- Devises (EUR/USD, GBP/USD, JPY/USD, CNY/USD, RUB/USD)
- Données historiques et évolution en temps réel

### 2. **Indicateurs Macroéconomiques (Banque Mondiale)**
- PIB par pays
- Taux d'inflation
- Taux de chômage
- Exportations et importations
- Dette publique
- Séries temporelles sur 5-10 ans

### 3. **Sanctions Internationales (OpenSanctions)**
- Base de données complète des sanctions mondiales
- Filtrage par pays et type d'entité
- Statistiques et visualisations
- Mise à jour en temps réel

### 4. **Analyse BRICS**
- Indicateurs économiques des pays BRICS
- Comparaisons entre économies émergentes
- Visualisations comparatives

### 5. **Séries Temporelles**
- Stockage historique des données
- Analyse de tendances
- Graphiques interactifs

## 📁 Structure des Fichiers

```
Flask/
├── economic_indicators.py              # Gestionnaire principal
├── economic_indicators_routes.py       # Routes API Flask
└── app_factory.py                      # Configuration mise à jour

templates/
└── economic_indicators.html            # Interface utilisateur

static/
└── js/
    └── economic-indicators.js          # Logique frontend
```

## 🚀 Installation

### 1. Dépendances Python

```bash
pip install yfinance requests
```

### 2. Copier les Fichiers

1. **Backend Flask**
   ```bash
   # Copier dans le dossier Flask/
   Flask/economic_indicators.py
   Flask/economic_indicators_routes.py
   Flask/app_factory.py  # Remplacer l'existant
   ```

2. **Frontend**
   ```bash
   # Copier dans templates/
   templates/economic_indicators.html
   templates/base.html  # Remplacer l'existant
   
   # Copier dans static/js/
   static/js/economic-indicators.js
   ```

### 3. Initialiser la Base de Données

Le module crée automatiquement ses tables SQLite au premier lancement :

```sql
- financial_indicators        # Données yFinance
- world_bank_indicators       # Données Banque Mondiale
- international_sanctions     # Sanctions
- indicator_time_series       # Séries temporelles
```

### 4. Démarrer l'Application

```bash
python run.py
```

Accéder au module : **http://localhost:5000/indicators**

## 🎯 Utilisation

### Interface Utilisateur

L'interface est organisée en 6 onglets :

#### 1. **Indices Boursiers**
- Visualisation des principaux indices mondiaux
- Cartes individuelles avec variations
- Graphiques d'évolution historique
- Mise à jour automatique

#### 2. **Matières Premières**
- Prix en temps réel
- Évolutions sur 1 mois
- Graphiques de tendance

#### 3. **Devises**
- Taux de change actuels
- Variations quotidiennes
- Graphique radar comparatif

#### 4. **Banque Mondiale**
- Recherche multi-critères
- Sélection de pays et indicateurs
- Séries temporelles personnalisables
- Export des données

#### 5. **Sanctions**
- Résumé global
- Top 10 des pays
- Filtrage par type d'entité
- Liste détaillée des sanctions

#### 6. **BRICS**
- Comparaison économique
- PIB et inflation
- Tableaux de données détaillés

### API REST

#### Récupérer des Données Financières
```bash
POST /api/economic/financial/fetch
Content-Type: application/json

{
  "symbols": ["^GSPC", "GC=F", "EURUSD=X"],
  "period": "1mo"
}
```

#### Récupérer des Indicateurs Banque Mondiale
```bash
POST /api/economic/worldbank/fetch
Content-Type: application/json

{
  "countries": ["CN", "US", "FR"],
  "indicator": "NY.GDP.MKTP.CD",
  "years": 5
}
```

#### Récupérer les Sanctions
```bash
POST /api/economic/sanctions/fetch
Content-Type: application/json

{
  "countries": ["RU", "IR", "KP"]  # Optionnel
}
```

#### Dashboard Complet
```bash
GET /api/economic/dashboard
```

Retourne toutes les données principales en une seule requête.

## 📊 Base de Données

### Tables Créées

#### `financial_indicators`
```sql
CREATE TABLE financial_indicators (
    id INTEGER PRIMARY KEY,
    symbol TEXT,
    indicator_type TEXT,
    value REAL,
    currency TEXT,
    timestamp TEXT,
    metadata TEXT
);
```

#### `world_bank_indicators`
```sql
CREATE TABLE world_bank_indicators (
    id INTEGER PRIMARY KEY,
    country_code TEXT,
    country_name TEXT,
    indicator_code TEXT,
    indicator_name TEXT,
    year INTEGER,
    value REAL
);
```

#### `international_sanctions`
```sql
CREATE TABLE international_sanctions (
    id INTEGER PRIMARY KEY,
    entity_id TEXT UNIQUE,
    entity_name TEXT,
    entity_type TEXT,
    country TEXT,
    sanctions_list TEXT,
    reason TEXT,
    data_json TEXT
);
```

#### `indicator_time_series`
```sql
CREATE TABLE indicator_time_series (
    id INTEGER PRIMARY KEY,
    indicator_key TEXT,
    indicator_type TEXT,
    date TEXT,
    value REAL,
    metadata TEXT
);
```

## 🔧 Configuration

### Variables d'Environnement (Optionnel)

```env
# Aucune clé API nécessaire pour les fonctionnalités de base
# yFinance et Banque Mondiale sont des APIs publiques

# Pour des fonctionnalités avancées futures :
# ALPHA_VANTAGE_KEY=votre_cle
# FRED_API_KEY=votre_cle
```

### Indicateurs Prédéfinis

Le module inclut des méthodes pour récupérer rapidement :

```python
# Dans economic_indicators.py
eco_manager.get_major_indices()    # Indices mondiaux
eco_manager.get_commodities()      # Matières premières
eco_manager.get_currencies()       # Devises
eco_manager.get_brics_indicators() # Indicateurs BRICS
```

## 🎨 Personnalisation

### Ajouter des Symboles Financiers

Dans `economic-indicators.js` :

```javascript
const customSymbols = [
    'AAPL',   // Apple
    'MSFT',   // Microsoft
    'GOOGL',  // Google
    // ...
];

EconomicIndicators.fetchFinancial({
    symbols: customSymbols,
    period: '1mo'
});
```

### Ajouter des Indicateurs Banque Mondiale

Codes disponibles : https://data.worldbank.org/indicator

Exemples :
- `NY.GDP.MKTP.CD` : PIB (USD courants)
- `FP.CPI.TOTL.ZG` : Inflation
- `SL.UEM.TOTL.ZS` : Chômage
- `NE.EXP.GNFS.ZS` : Exportations

### Modifier le Design

Les styles sont dans `economic_indicators.html` :

```css
.indicator-card {
    /* Personnaliser l'apparence des cartes */
}

.eco-tab.active {
    /* Personnaliser les onglets actifs */
}
```

## 📈 Exemples d'Utilisation

### Exemple 1 : Surveiller les Marchés Asiatiques

```python
from Flask.economic_indicators import EconomicIndicatorsManager

eco_manager = EconomicIndicatorsManager(db_manager)

asian_indices = [
    '000001.SS',  # Shanghai
    '^HSI',       # Hang Seng
    '^N225',      # Nikkei
    '^KS11'       # KOSPI
]

data = eco_manager.fetch_financial_data(asian_indices, period='5d')
```

### Exemple 2 : Analyser l'Économie Chinoise

```python
# PIB de la Chine sur 10 ans
gdp_data = eco_manager.fetch_world_bank_data(
    country_codes=['CN'],
    indicator_code='NY.GDP.MKTP.CD',
    years=10
)

# Inflation
inflation_data = eco_manager.fetch_world_bank_data(
    country_codes=['CN'],
    indicator_code='FP.CPI.TOTL.ZG',
    years=10
)
```

### Exemple 3 : Créer un Rapport Personnalisé

```javascript
// Dans le frontend
async function generateCustomReport() {
    const indices = await fetch('/api/economic/indices').then(r => r.json());
    const commodities = await fetch('/api/economic/commodities').then(r => r.json());
    const sanctions = await fetch('/api/economic/sanctions/summary').then(r => r.json());
    
    // Générer un rapport PDF ou Excel
    const report = {
        date: new Date(),
        markets: indices.data,
        commodities: commodities.data,
        sanctions: sanctions.data
    };
    
    // Export
    EconomicIndicators.exportData();
}
```

## 🔍 Dépannage

### Erreur : "Module yfinance not found"
```bash
pip install yfinance
```

### Erreur : "No data found for symbol"
Vérifier que le symbole est correct sur Yahoo Finance : https://finance.yahoo.com

### Données Banque Mondiale vides
- Vérifier les codes pays (format ISO : 'CN', 'US', etc.)
- Vérifier les codes indicateurs
- Certains indicateurs n'ont pas de données récentes

### Sanctions non chargées
- Vérifier la connexion internet
- L'API OpenSanctions peut être temporairement indisponible
- Les données sont mises en cache en base de données

## 🚧 Développements Futurs

### Prévus
- [ ] Scraping des banques centrales BRICS (Scrapy)
- [ ] National Bureau of Statistics of China
- [ ] Alertes personnalisées
- [ ] Export automatique (PDF/Excel)
- [ ] Comparaisons historiques avancées
- [ ] Intégration avec le module IA pour prédictions

### Suggestions Bienvenues
Ouvrez une issue sur GitHub pour proposer de nouvelles fonctionnalités.

## 📝 Licence

Ce module fait partie de GEOPOL Analytics.

## 👨‍💻 Auteur

Développé pour GEOPOL Analytics v0.6PP
Contact : ohenri.b@gmail.com

## 🙏 Remerciements

- **yFinance** : Données financières
- **Banque Mondiale** : Indicateurs macroéconomiques
- **OpenSanctions** : Base de sanctions internationales
- **Chart.js** : Visualisations

---

**Note Importante** : Ce module utilise des APIs publiques et gratuites. Pour une utilisation professionnelle intensive, envisagez des solutions payantes avec des garanties de disponibilité et des limites de taux plus élevées.
