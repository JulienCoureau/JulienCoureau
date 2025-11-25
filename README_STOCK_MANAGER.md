# 📊 Gestionnaire d'Actions - Guide Complet

## 📁 Fichiers créés

```
/home/user/JulienCoureau/
├── stock_manager_improved.py    # ⭐ Version améliorée du code
├── test_stock_manager.py        # 🧪 Tests unitaires (pytest)
├── example_config.json          # 📋 Exemple de configuration
├── AMELIORATIONS.md             # 📖 Détails des améliorations
└── README_STOCK_MANAGER.md      # 📚 Ce fichier
```

---

## 🚀 Installation rapide

### 1. Installer les dépendances

```bash
pip install yfinance
```

### 2. Créer la structure des dossiers

```bash
mkdir -p json_finance
```

### 3. Créer le fichier de configuration

Copiez le contenu de `example_config.json` dans `json_finance/suffixe.json` :

```bash
cp example_config.json json_finance/suffixe.json
```

Ou créez-le manuellement :

```json
{
  "markets": {
    "États-Unis": "",
    "France": ".PA",
    "Allemagne": ".DE",
    "Royaume-Uni": ".L",
    "Canada": ".TO",
    "Japon": ".T"
  }
}
```

### 4. Lancer l'application

```bash
python stock_manager_improved.py
```

---

## 💡 Utilisation

### Exemple de session

```
==================================================
📊 GESTIONNAIRE D'ACTIONS
==================================================
Tapez 'q' ou 'quit' à tout moment pour quitter

--------------------------------------------------
➕ AJOUT D'UNE ACTION
--------------------------------------------------

Pays (ou 'liste' pour voir tous): france
✓ Pays sélectionné: France

Ticker: MC

Recherche de MC.PA...

==================================================
📈 INFORMATIONS DE L'ACTION
==================================================
Ticker:    MC.PA
Nom:       LVMH Moët Hennessy Louis Vuitton SE
Secteur:   Consumer Cyclical
Industrie: Luxury Goods
Pays:      France
Cap. bours.: 400,000,000,000 EUR
==================================================

✓ Confirmer l'ajout? (oui/non): oui
✅ Action MC.PA ajoutée (Total: 1)

➕ Ajouter une autre action? (oui/non): non

✅ Terminé!
```

### Fonctionnalités

#### 1. Recherche de pays intelligente

```
Pays: fra          → Trouve "France"
Pays: uni          → Propose "États-Unis" et "Royaume-Uni"
Pays: liste        → Affiche tous les pays disponibles
Pays: q            → Quitte l'application
```

#### 2. Détection de doublons

L'application vérifie automatiquement si l'action existe déjà **avant** d'interroger l'API :

```
⚠️  L'action AAPL existe déjà dans la base!
```

#### 3. Gestion des erreurs

```
❌ Action XYZ123 non trouvée ou erreur de récupération
❌ Le ticker ne peut pas être vide
❌ Aucun pays trouvé pour 'xyz'
```

#### 4. Confirmation avant ajout

Vous pouvez vérifier les informations avant de sauvegarder :

```
✓ Confirmer l'ajout? (oui/non): non
❌ Ajout annulé
```

---

## 🧪 Tests unitaires

### Installation de pytest

```bash
pip install pytest pytest-mock
```

### Lancer les tests

```bash
# Tous les tests
pytest test_stock_manager.py -v

# Tests spécifiques
pytest test_stock_manager.py::TestStockDatabase -v
pytest test_stock_manager.py::TestMarketManager -v

# Avec couverture
pip install pytest-cov
pytest test_stock_manager.py --cov=stock_manager_improved --cov-report=html
```

### Résultats attendus

```
test_stock_manager.py::TestStockDatabase::test_init_creates_directory PASSED
test_stock_manager.py::TestStockDatabase::test_load_stocks_empty_file PASSED
test_stock_manager.py::TestStockDatabase::test_save_and_load_stocks PASSED
test_stock_manager.py::TestStockDatabase::test_add_stock PASSED
test_stock_manager.py::TestStockDatabase::test_add_duplicate_stock PASSED
test_stock_manager.py::TestMarketManager::test_load_markets PASSED
test_stock_manager.py::TestMarketManager::test_find_matching_countries_exact PASSED
test_stock_manager.py::TestStockInfoFetcher::test_fetch_success PASSED
test_stock_manager.py::TestIntegration::test_full_workflow PASSED

==================== 30 passed in 2.5s ====================
```

---

## 📊 Structure de la base de données

Le fichier `json_finance/name_action.json` contient :

```json
{
  "stocks": [
    {
      "ticker": "AAPL",
      "name": "Apple Inc.",
      "sector": "Technology",
      "industry": "Consumer Electronics",
      "country": "United States",
      "marketCap": 2500000000000,
      "currency": "USD"
    },
    {
      "ticker": "MC.PA",
      "name": "LVMH Moët Hennessy Louis Vuitton SE",
      "sector": "Consumer Cyclical",
      "industry": "Luxury Goods",
      "country": "France",
      "marketCap": 400000000000,
      "currency": "EUR"
    }
  ]
}
```

---

## 🎯 Comparaison : Avant vs Après

### Version originale
✅ Fonctionnelle
✅ Simple et directe
❌ Pas de gestion d'erreurs détaillée
❌ Pas de logging
❌ Pas de tests
❌ Difficile à maintenir

### Version améliorée
✅ Architecture orientée objet
✅ Gestion d'erreurs robuste
✅ Logging intégré
✅ Tests unitaires complets
✅ Type hints
✅ Documentation détaillée
✅ Validation des entrées
✅ UX améliorée avec émojis
✅ Confirmation avant ajout
✅ Cache des données

---

## 🔧 Personnalisation

### Ajouter de nouveaux marchés

Éditez `json_finance/suffixe.json` :

```json
{
  "markets": {
    "Singapour": ".SI",
    "Corée du Sud": ".KS",
    "Nouvelle-Zélande": ".NZ"
  }
}
```

### Modifier les champs récupérés

Dans `stock_manager_improved.py`, méthode `StockInfoFetcher.fetch()` :

```python
return {
    "ticker": ticker.upper(),
    "name": info.get('longName', 'N/A'),
    # Ajoutez vos champs ici
    "dividend": info.get('dividendYield', 'N/A'),
    "pe_ratio": info.get('trailingPE', 'N/A'),
    "volume": info.get('volume', 'N/A')
}
```

### Changer le niveau de logging

```python
# Au début de stock_manager_improved.py
logging.basicConfig(
    level=logging.DEBUG,  # INFO, WARNING, ERROR, DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

---

## 🐛 Dépannage

### Problème : "Fichier de configuration manquant"

```bash
# Vérifiez que le fichier existe
ls json_finance/suffixe.json

# Sinon, créez-le
cp example_config.json json_finance/suffixe.json
```

### Problème : "ModuleNotFoundError: No module named 'yfinance'"

```bash
pip install yfinance
```

### Problème : "Action non trouvée"

- Vérifiez le ticker sur Yahoo Finance
- Assurez-vous d'utiliser le bon suffixe pour le pays
- Exemple : "LVMH" → utiliser "MC" pour la France (MC.PA)

### Problème : Erreur réseau

```python
# yfinance utilise parfois un cache
# Supprimez le cache si nécessaire
import yfinance as yf
yf.Ticker("AAPL").info  # Essayez manuellement
```

---

## 📚 Ressources

### Tickers Yahoo Finance

- **États-Unis** : AAPL, GOOGL, MSFT, TSLA, AMZN
- **France** : MC.PA, OR.PA, SU.PA, BNP.PA, AI.PA
- **Allemagne** : VOW3.DE, SAP.DE, SIE.DE, BAYN.DE
- **Japon** : 7203.T (Toyota), 9984.T (SoftBank)

### Documentation

- [yfinance](https://pypi.org/project/yfinance/)
- [pytest](https://docs.pytest.org/)
- [Python type hints](https://docs.python.org/3/library/typing.html)

---

## 🚀 Prochaines étapes

1. **Recherche dans la base** : Ajouter une fonction pour chercher des actions
2. **Mise à jour** : Actualiser les données d'actions existantes
3. **Export** : Exporter en CSV, Excel, PDF
4. **Statistiques** : Dashboard avec répartition par secteur/pays
5. **API REST** : Exposer via FastAPI
6. **GUI** : Interface Streamlit ou Gradio
7. **Base de données** : Migrer vers SQLite/PostgreSQL

---

## 📝 License

Code d'exemple pour usage éducatif et personnel.

---

## 🤝 Contribution

Pour toute suggestion d'amélioration :
1. Consultez `AMELIORATIONS.md` pour voir les améliorations déjà apportées
2. Lancez les tests avant toute modification : `pytest test_stock_manager.py`
3. Ajoutez des tests pour les nouvelles fonctionnalités

---

## ✅ Checklist de démarrage

- [ ] Python 3.7+ installé
- [ ] `pip install yfinance` exécuté
- [ ] Dossier `json_finance/` créé
- [ ] Fichier `json_finance/suffixe.json` créé
- [ ] Test d'exécution : `python stock_manager_improved.py`
- [ ] (Optionnel) Tests installés : `pip install pytest pytest-mock`
- [ ] (Optionnel) Tests lancés : `pytest test_stock_manager.py -v`

---

**Bon trading ! 📈💰**
