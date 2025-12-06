"""
Script de mise à jour des données Yahoo Finance
Met à jour les prix actuels, capitalisations et actions en circulation
dans le fichier bdd_zb_prix_juste.json

Utilisation : python update_yfinance.py
"""

import yfinance as yf
import json
import os
from pathlib import Path

# Chemins des fichiers
SCRIPT_DIR = Path(__file__).parent
JSON_FINANCE_DIR = SCRIPT_DIR / "json_finance"
BDD_FILE = JSON_FINANCE_DIR / "bdd_zb_prix_juste.json"

def get_yfinance_data(ticker):
    """Récupère les données actuelles depuis Yahoo Finance

    Args:
        ticker: Le symbole boursier (ex: "AMZN", "SU.PA")

    Returns:
        dict: Données actuelles ou None si erreur
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

def update_yfinance_data():
    """Fonction principale - Met à jour toutes les données Yahoo Finance"""

    # Vérifier que le fichier JSON existe
    if not BDD_FILE.exists():
        print(f"❌ Erreur : Fichier {BDD_FILE} non trouvé")
        print("   Veuillez d'abord extraire les données Excel avec extraction_donnees_bourse.py")
        return False

    # Charger le JSON
    print("\n" + "="*60)
    print("MISE À JOUR DES DONNÉES YAHOO FINANCE")
    print("="*60)

    with open(BDD_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nb_entreprises = len(data)
    print(f"\n📊 {nb_entreprises} entreprise(s) trouvée(s) dans la base\n")

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

        # Récupérer les données Yahoo Finance
        yf_data = get_yfinance_data(ticker)

        if yf_data:
            # Ajouter/mettre à jour la section donnees_actuelles
            data[nom_entreprise]['donnees_actuelles'] = yf_data
            print(f"✅ {yf_data['prix_actuel']:.2f} {yf_data['devise']}")
            succes += 1
        else:
            print("❌")
            erreurs += 1

    # Sauvegarder le JSON mis à jour
    with open(BDD_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Résumé
    print("\n" + "="*60)
    print("✅ MISE À JOUR TERMINÉE")
    print("="*60)
    print(f"  Succès   : {succes}/{nb_entreprises}")
    print(f"  Erreurs  : {erreurs}/{nb_entreprises}")
    print(f"\n📁 Fichier mis à jour : {BDD_FILE}")
    print("="*60)

    return True

if __name__ == "__main__":
    update_yfinance_data()
