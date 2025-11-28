# Extracteur de Métriques Financières

Ce projet permet d'extraire automatiquement des métriques financières depuis des fichiers Excel contenant des données d'entreprises et de les synchroniser avec des informations complémentaires (ticker, industrie) stockées dans un fichier JSON.

## 📋 Structure du Projet

```
documents/data_bourse/
├── base_de_donnee/          # Placez vos fichiers Excel ici
│   ├── Apple_financials.xlsx
│   ├── Microsoft_financials.xlsx
│   └── ...
├── code/
│   ├── extracteur_metriques.py    # Script principal
│   ├── requirements.txt            # Dépendances Python
│   └── json_finance/
│       └── entreprises.json        # Informations des entreprises
└── output/                          # Résultats générés automatiquement
    ├── metriques_extraites.json
    ├── metriques_extraites.xlsx
    ├── metriques_extraites.csv
    └── rapport_extraction.txt
```

## 🎯 Métriques Extraites

Le script extrait les métriques suivantes depuis 4 feuilles Excel différentes:

### 📊 Compte de Résultat
- Total Chiffre d'affaires
- Coût des marchandises vendues, total
- Résultat Brut
- Résultat d'Exploitation
- Intérêts payés, total
- Charges d'intérêt nettes
- Résultat net
- BPA de base normalisé
- Dividende par action
- EBITDA
- Taux d'imposition effectif (%)

### 💼 Bilan
- Total des capitaux propres
- Total de la dette
- Dette nette

### 💰 Flux de Trésorerie
- Flux de trésorerie d'exploitation
- Dépenses d'investissement du capital (CAPEX)
- Flux de trésorerie d'investissement
- Flux de trésorerie de financement
- Flux de trésorerie libre pour les actionnaires (FCFE)

### 📈 Valorisation
- PER
- Valeur entreprise / EBITDA
- FCF Yield

## 🚀 Installation

### 1. Installation des dépendances Python

```bash
cd ~/documents/data_bourse/code
pip install -r requirements.txt
```

Ou installez manuellement:
```bash
pip install pandas openpyxl xlrd
```

### 2. Préparation des fichiers

#### a) Fichiers Excel
Placez vos fichiers Excel dans le dossier `base_de_donnee/`.

**Format attendu du nom de fichier:**
- `NomEntreprise_financials.xlsx`
- `NomEntreprise.xlsx`
- Tout nom contenant le nom de l'entreprise

**Feuilles requises dans chaque fichier Excel:**
Les noms de feuilles peuvent varier, le script reconnaît:
- Compte de Résultat: "Compte de résultat", "Income Statement", "P&L"
- Bilan: "Bilan", "Balance Sheet"
- Flux de Trésorerie: "Flux de trésorerie", "Cash Flow"
- Valorisation: "Valorisation", "Valuation"

**Structure des feuilles:**
```
| Métrique                    | 2021    | 2022    | 2023    | 2024    |
|-----------------------------|---------|---------|---------|---------|
| Total Chiffre d'affaires    | 100000  | 120000  | 150000  | 180000  |
| Résultat Brut               | 40000   | 48000   | 60000   | 72000   |
| ...                         | ...     | ...     | ...     | ...     |
```

#### b) Fichier JSON
Créez ou modifiez le fichier `code/json_finance/entreprises.json` avec les informations de vos entreprises:

```json
[
  {
    "nom": "Apple",
    "ticker": "AAPL",
    "industrie": "Technologie - Électronique"
  },
  {
    "nom": "Microsoft",
    "ticker": "MSFT",
    "industrie": "Technologie - Logiciels"
  }
]
```

**Important:** Le nom dans le JSON doit correspondre (au moins partiellement) au nom dans le fichier Excel.

## 💻 Utilisation

### Exécution du script

```bash
cd ~/documents/data_bourse/code
python extracteur_metriques.py
```

### Processus d'exécution

Le script va:

1. **Charger les informations du JSON** (nom, ticker, industrie)
2. **Scanner tous les fichiers Excel** dans `base_de_donnee/`
3. **Pour chaque fichier:**
   - Extraire le nom de l'entreprise
   - Synchroniser avec les données JSON
   - Lire les 4 feuilles (Compte de résultat, Bilan, Flux de trésorerie, Valorisation)
   - Extraire les métriques définies
4. **Générer les fichiers de sortie** dans le dossier `output/`

### Résultats générés

Après l'exécution, vous trouverez dans `output/`:

1. **metriques_extraites.json** - Format JSON brut avec toutes les données et années
2. **metriques_extraites.xlsx** - Fichier Excel avec une ligne par entreprise (dernière année)
3. **metriques_extraites.csv** - Version CSV du fichier Excel
4. **rapport_extraction.txt** - Rapport résumé de l'extraction

## 📝 Exemple de Sortie

### Format JSON (extrait)
```json
[
  {
    "nom": "Apple",
    "ticker": "AAPL",
    "industrie": "Technologie - Électronique",
    "metriques": {
      "Total Chiffre d'affaires": {
        "2021": 365000000,
        "2022": 394000000,
        "2023": 383000000
      },
      "PER": {
        "2021": 28.5,
        "2022": 24.3,
        "2023": 29.8
      }
    }
  }
]
```

### Format Excel/CSV
| Nom      | Ticker | Industrie                    | Total Chiffre d'affaires | PER  | EBITDA    | ... |
|----------|--------|------------------------------|--------------------------|------|-----------|-----|
| Apple    | AAPL   | Technologie - Électronique   | 383000000                | 29.8 | 120000000 | ... |
| Microsoft| MSFT   | Technologie - Logiciels      | 211000000                | 32.1 | 95000000  | ... |

## 🔧 Personnalisation

### Modifier les métriques à extraire

Éditez le fichier `extracteur_metriques.py` et modifiez les listes au début du fichier:

```python
metriques_prix_juste_compte = [
    "Total Chiffre d'affaires",
    "Résultat net",
    # Ajoutez vos métriques ici
]
```

### Adapter les noms de feuilles

Si vos feuilles Excel ont des noms différents, modifiez le dictionnaire `feuilles_mapping` dans la fonction `traiter_fichier_excel()`:

```python
feuilles_mapping = {
    'compte_resultat': ['Compte de résultat', 'VotreNomDeFeuille'],
    # ...
}
```

### Modifier le matching nom entreprise/fichier

Si vos fichiers ont un format de nom différent, modifiez la fonction `extraire_nom_entreprise()`:

```python
def extraire_nom_entreprise(nom_fichier: str) -> str:
    nom_base = os.path.splitext(nom_fichier)[0]
    # Ajoutez votre logique ici
    return nom_base.strip()
```

## ⚠️ Dépannage

### Problème: "Aucun fichier Excel trouvé"
- Vérifiez que vos fichiers sont bien dans `~/documents/data_bourse/base_de_donnee/`
- Vérifiez l'extension (.xlsx ou .xls)

### Problème: "Feuille non trouvée"
- Vérifiez les noms exacts de vos feuilles Excel
- Ajoutez les noms de vos feuilles dans `feuilles_mapping`

### Problème: "Métrique non trouvée"
- Vérifiez l'orthographe exacte dans votre fichier Excel
- Le script essaie une correspondance partielle si l'exacte ne fonctionne pas
- Vérifiez que la métrique est bien dans la première colonne

### Problème: "Aucune information trouvée dans le JSON"
- Vérifiez que le nom dans le JSON correspond au nom du fichier
- Le matching est partiel et insensible à la casse

## 🎓 Comment ça marche étape par étape

1. **Chargement du JSON** → Le script lit toutes les infos des entreprises
2. **Scan des Excel** → Trouve tous les fichiers .xlsx et .xls
3. **Pour chaque fichier:**
   - Extrait le nom de l'entreprise du nom de fichier
   - Cherche les infos correspondantes dans le JSON
   - Ouvre le fichier Excel
   - Pour chaque feuille, cherche les métriques dans la première colonne
   - Extrait toutes les valeurs (années)
4. **Sauvegarde** → Crée les fichiers de sortie dans différents formats

## 📞 Support

Si vous rencontrez des problèmes:
1. Vérifiez les messages d'erreur affichés par le script
2. Consultez le fichier `rapport_extraction.txt` dans le dossier output
3. Vérifiez que vos fichiers Excel ont la bonne structure

## 📄 Licence

Projet personnel - Julien Coureau - 2025
