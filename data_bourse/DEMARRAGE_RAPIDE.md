# 🚀 Démarrage Rapide

Guide rapide pour utiliser l'Extracteur de Métriques Financières en 3 étapes.

## ⚡ Installation Rapide (2 minutes)

### Étape 1: Installer les dépendances

```bash
cd ~/documents/data_bourse/code
bash install.sh
```

Ou manuellement:
```bash
pip3 install pandas openpyxl xlrd
```

### Étape 2: Créer un fichier de test

```bash
python3 test_script.py
```

Cela créera un fichier Excel exemple avec des données Apple.

### Étape 3: Exécuter l'extraction

```bash
python3 extracteur_metriques.py
```

Les résultats seront dans `~/documents/data_bourse/output/`

## 📊 Utilisation avec vos propres données

### 1. Préparez vos fichiers Excel

Placez-les dans: `~/documents/data_bourse/base_de_donnee/`

**Nom du fichier**: `NomEntreprise_financials.xlsx` (ou juste `NomEntreprise.xlsx`)

**Feuilles requises** (au moins une):
- "Compte de résultat" ou "Income Statement"
- "Bilan" ou "Balance Sheet"
- "Flux de trésorerie" ou "Cash Flow"
- "Valorisation" ou "Valuation"

**Format des données**:
```
Première colonne = Nom de la métrique
Colonnes suivantes = Années (2021, 2022, etc.)
```

### 2. Mettez à jour le fichier JSON

Éditez: `~/documents/data_bourse/code/json_finance/entreprises_exemple.json`

```json
[
  {
    "nom": "NomDeVotreEntreprise",
    "ticker": "TICK",
    "industrie": "Secteur d'activité"
  }
]
```

**Important**: Le `nom` doit correspondre au nom dans votre fichier Excel.

### 3. Lancez l'extraction

```bash
cd ~/documents/data_bourse/code
python3 extracteur_metriques.py
```

## 📁 Résultats

Après l'exécution, consultez le dossier `output/`:

- **metriques_extraites.xlsx** - Fichier Excel facile à utiliser
- **metriques_extraites.csv** - Pour importer dans d'autres outils
- **metriques_extraites.json** - Données brutes complètes
- **rapport_extraction.txt** - Résumé de l'extraction

## 🎯 Exemple de Workflow Complet

```bash
# 1. Installation (une seule fois)
cd ~/documents/data_bourse/code
bash install.sh

# 2. Créer un test (optionnel)
python3 test_script.py

# 3. Ajouter vos fichiers Excel
cp /chemin/vers/vos/fichiers/*.xlsx ~/documents/data_bourse/base_de_donnee/

# 4. Modifier le JSON
nano ~/documents/data_bourse/code/json_finance/entreprises_exemple.json

# 5. Exécuter l'extraction
python3 extracteur_metriques.py

# 6. Consulter les résultats
cd ~/documents/data_bourse/output
ls -lh
```

## ❓ Questions Fréquentes

**Q: Comment savoir si mes fichiers Excel sont au bon format?**
R: Exécutez le script, il affichera des messages détaillés sur ce qu'il trouve ou ne trouve pas.

**Q: Le script ne trouve pas mes métriques**
R: Vérifiez que:
- Les noms de métriques correspondent exactement (majuscules, accents, etc.)
- Les métriques sont dans la première colonne
- Les noms de feuilles correspondent

**Q: Comment ajouter de nouvelles métriques?**
R: Éditez `extracteur_metriques.py` et ajoutez vos métriques dans les listes au début du fichier.

**Q: Puis-je traiter plusieurs entreprises en même temps?**
R: Oui! Placez tous vos fichiers Excel dans `base_de_donnee/` et ajoutez toutes les entreprises dans le JSON.

## 🔄 Workflow Recommandé

1. **Test initial**: Utilisez `test_script.py` pour valider l'installation
2. **Un fichier d'abord**: Testez avec UN fichier Excel avant de traiter tous vos fichiers
3. **Vérification**: Consultez le `rapport_extraction.txt` pour voir ce qui a été extrait
4. **Ajustements**: Modifiez les listes de métriques si nécessaire
5. **Production**: Lancez l'extraction sur tous vos fichiers

## 📞 Besoin d'aide?

Consultez le fichier README.md complet pour:
- Instructions détaillées
- Personnalisation avancée
- Dépannage
- Structure des données

## 🎓 Pour comprendre le code

Le fichier `extracteur_metriques.py` est entièrement commenté avec:
- Explication de chaque étape
- Commentaires en français
- Structure modulaire facile à modifier

N'hésitez pas à l'ouvrir et le modifier selon vos besoins!
