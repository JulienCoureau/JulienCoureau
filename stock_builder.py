"""
Construction d'une base de données d'actions - Version simple étape par étape
"""
import json
from pathlib import Path

# NOTE: Pour l'instant on simule les données
# Une fois yfinance installé, décommentez les lignes avec yfinance

# import yfinance as yf  # À décommenter plus tard

# Fichier où on va sauvegarder nos actions
JSON_FILE = Path("base_actions.json")

print("=" * 50)
print("CONSTRUCTION DE VOTRE BASE D'ACTIONS")
print("=" * 50)

# ÉTAPE 3 : Boucle pour ajouter plusieurs actions
while True:
    # ÉTAPE 1 : Récupérer les infos d'un ticker
    ticker = input("\nEntrez un ticker (ou 'q' pour quitter): ").strip().upper()

    # Quitter si l'utilisateur tape 'q'
    if ticker == 'Q':
        print("\nBase sauvegardée ! Au revoir.")
        break

    if not ticker:
        print("⚠️  Ticker vide, veuillez entrer un ticker valide")
        continue

    print(f"\nRecherche de {ticker}...")

    # VERSION SIMULÉE (pour comprendre la logique)
    # On simule quelques actions connues
    donnees_simulees = {
        "AAPL": {
            "longName": "Apple Inc.",
            "country": "United States",
            "sector": "Technology",
            "industry": "Consumer Electronics"
        },
        "TSLA": {
            "longName": "Tesla, Inc.",
            "country": "United States",
            "sector": "Consumer Cyclical",
            "industry": "Auto Manufacturers"
        },
        "MC.PA": {
            "longName": "LVMH Moët Hennessy Louis Vuitton",
            "country": "France",
            "sector": "Consumer Cyclical",
            "industry": "Luxury Goods"
        }
    }

    # Récupérer les infos (simulées pour l'instant)
    if ticker in donnees_simulees:
        info = donnees_simulees[ticker]
    else:
        # Si le ticker n'existe pas dans nos données simulées
        info = {
            "longName": f"[Simulation] {ticker} Company",
            "country": "Unknown",
            "sector": "Unknown",
            "industry": "Unknown"
        }

    # VERSION AVEC YFINANCE (à utiliser plus tard quand yfinance sera installé)
    # stock = yf.Ticker(ticker)
    # info = stock.info

    # Afficher ce qu'on récupère
    print("\nInformations récupérées:")
    print(f"Ticker: {ticker}")
    print(f"Nom: {info.get('longName', 'N/A')}")
    print(f"Pays: {info.get('country', 'N/A')}")
    print(f"Secteur: {info.get('sector', 'N/A')}")
    print(f"Industrie: {info.get('industry', 'N/A')}")

    # ÉTAPE 2 : Sauvegarder dans un fichier JSON

    # Créer le dictionnaire pour cette action
    action = {
        "ticker": ticker,
        "nom": info.get('longName', 'N/A'),
        "pays": info.get('country', 'N/A'),
        "secteur": info.get('sector', 'N/A'),
        "industrie": info.get('industry', 'N/A')
    }

    # Charger les actions existantes (si le fichier existe)
    if JSON_FILE.exists():
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        # Créer une nouvelle structure
        data = {"actions": []}

    # Vérifier si l'action existe déjà
    existe_deja = False
    for a in data["actions"]:
        if a["ticker"] == ticker:
            existe_deja = True
            print(f"\n⚠️  {ticker} existe déjà dans la base !")
            break

    # Ajouter l'action si elle n'existe pas
    if not existe_deja:
        data["actions"].append(action)

        # Sauvegarder dans le fichier JSON
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ {ticker} ajouté à la base !")
        print(f"Total d'actions: {len(data['actions'])}")
