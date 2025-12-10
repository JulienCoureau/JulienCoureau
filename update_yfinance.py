"""
Script de mise à jour des données Yahoo Finance
Met à jour les prix actuels, capitalisations, actions en circulation
et données supplémentaires (beta, PER, PEG, 52 semaines)
dans le fichier bdd_zb_prix_juste.json

Utilisation pour appeler dans le terminal : python update_yfinance.py
"""

import yfinance as yf
import json
import os
from pathlib import Path

# Chemins des fichiers
SCRIPT_DIR = Path(__file__).parent
JSON_FINANCE_DIR = SCRIPT_DIR / "json_finance"
BDD_FILE = JSON_FINANCE_DIR / "bdd_zb_prix_juste.json"


def get_all_yfinance_data(ticker):
    """Récupère toutes les données depuis Yahoo Finance en un seul appel
    Args:
        ticker: Le symbole boursier
    Returns:
        tuple: (donnees_actuelles, yahoo_finance) ou (None, None) si erreur
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Vérifier que les données existent
        if not info or not info.get('currentPrice'):
            return None, None

        # Données actuelles (section existante)
        donnees_actuelles = {
            "prix_actuel": info.get('currentPrice', info.get('regularMarketPrice')),
            "devise": info.get('currency', 'N/A'),
            "capitalisation": info.get('marketCap'),
            "actions_circulation": info.get('sharesOutstanding')
        }

        # Données Yahoo Finance supplémentaires (nouvelle section)
        yahoo_finance = {
            "beta": info.get('beta'),
            "52_week_high": info.get('fiftyTwoWeekHigh'),
            "52_week_low": info.get('fiftyTwoWeekLow'),
            "per_ttm": info.get('trailingPE'),
            "per_forward": info.get('forwardPE'),
            "peg_ratio": info.get('pegRatio')
        }

        return donnees_actuelles, yahoo_finance

    except Exception as e:
        print(f"  ⚠️  Erreur pour {ticker}: {str(e)}")
        return None, None


def get_yfinance_data(ticker):
    """Récupère les données actuelles depuis Yahoo Finance
    Args:
        ticker: Le symbole boursier
    Returns:
        dict: Données actuelles ou None si erreur

    Note: Cette fonction est conservée pour compatibilité.
    Préférer get_all_yfinance_data() pour éviter les appels multiples.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Vérifier que les données existent
        if not info or not info.get('currentPrice'):
            return None

        return {
            "prix_actuel": info.get('currentPrice', info.get('regularMarketPrice')),
            "devise": info.get('currency', 'N/A'),
            "capitalisation": info.get('marketCap'),
            "actions_circulation": info.get('sharesOutstanding')
        }

    except Exception as e:
        print(f"  ⚠️  Erreur pour {ticker}: {str(e)}")
        return None


def get_yahoo_finance_extras(ticker):
    """Récupère les données Yahoo Finance supplémentaires pour le prix juste
    Args:
        ticker: Le symbole boursier
    Returns:
        dict: Données supplémentaires ou None si erreur

    Note: Cette fonction est conservée pour compatibilité.
    Préférer get_all_yfinance_data() pour éviter les appels multiples.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        return {
            "beta": info.get('beta'),
            "52_week_high": info.get('fiftyTwoWeekHigh'),
            "52_week_low": info.get('fiftyTwoWeekLow'),
            "per_ttm": info.get('trailingPE'),
            "per_forward": info.get('forwardPE'),
            "peg_ratio": info.get('pegRatio')
        }

    except Exception as e:
        print(f"  ⚠️  Erreur extras pour {ticker}: {str(e)}")
        return None


def update_yfinance_data():
    """Fonction principale - Met à jour toutes les données Yahoo Finance"""

    # Vérifier que le fichier JSON existe
    if not BDD_FILE.exists():
        print(f"❌ Erreur : Fichier {BDD_FILE} non trouvé")
        print("   Veuillez d'abord extraire les données Excel avec extraction_donnees_bourse.py")
        return False

    # Charger le JSON
    print()
    print("MISE À JOUR DES DONNÉES YAHOO FINANCE")
    print()

    with open(BDD_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nb_entreprises = len(data)
    print(f"\n ⤳ {nb_entreprises} entreprise(s) trouvée(s) dans la base\n")

    # Compteurs
    succes = 0
    erreurs = 0

    # Mettre à jour chaque entreprise
    for i, (nom_entreprise, entreprise_data) in enumerate(data.items(), 1):
        ticker = entreprise_data.get('infos', {}).get('ticker')

        if not ticker:
            print(f"[{i}/{nb_entreprises}] ⚠️  {nom_entreprise} - Pas de ticker")
            erreurs += 1
            continue

        print(f"[{i}/{nb_entreprises}] {ticker:8} - {nom_entreprise[:40]:40} ... ", end="", flush=True)

        # Récupérer toutes les données Yahoo Finance en un seul appel
        donnees_actuelles, yahoo_finance = get_all_yfinance_data(ticker)

        if donnees_actuelles:
            # Mettre à jour la section donnees_actuelles
            data[nom_entreprise]['donnees_actuelles'] = donnees_actuelles

            # Ajouter la nouvelle section yahoo_finance
            data[nom_entreprise]['yahoo_finance'] = yahoo_finance

            # Affichage avec le beta
            prix = donnees_actuelles['prix_actuel']
            devise = donnees_actuelles['devise']
            beta = yahoo_finance.get('beta') if yahoo_finance else None

            if beta is not None:
                print(f"✅ {prix:.2f} {devise} | β={beta:.2f}")
            else:
                print(f"✅ {prix:.2f} {devise} | β=N/A")

            succes += 1
        else:
            print("❌")
            erreurs += 1

    # Sauvegarder le JSON mis à jour
    with open(BDD_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Résumé
    print()
    print("✅ MISE À JOUR TERMINÉE")
    print()
    print(f"  Succès   : {succes}/{nb_entreprises}")
    print(f"  Erreurs  : {erreurs}/{nb_entreprises}")
    print(f"\n📁 Fichier mis à jour : {BDD_FILE}")

    return True


if __name__ == "__main__":
    update_yfinance_data()
