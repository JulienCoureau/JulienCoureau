"""Script de test pour le calcul de croissance médiane"""

import json
from pathlib import Path
from calcul_prix_juste import calculer_croissance_mediane

# Charger les données
SCRIPT_DIR = Path(__file__).parent
JSON_FINANCE_DIR = SCRIPT_DIR / "json_finance"
BDD_FILE = JSON_FINANCE_DIR / "bdd_zb_prix_juste.json"

with open(BDD_FILE, 'r', encoding='utf-8') as f:
    bdd_data = json.load(f)

print("\n" + "="*70)
print("TEST CALCUL CROISSANCE MÉDIANE (2015-2024)")
print("="*70 + "\n")

for nom_entreprise, entreprise_data in bdd_data.items():
    ticker = entreprise_data.get('infos', {}).get('ticker')

    print(f"\n{nom_entreprise}")
    print(f"  Ticker : {ticker}")

    croissances = calculer_croissance_mediane(entreprise_data)

    print(f"  Médiane croissance CA      : {croissances['ca']:>6}%") if croissances['ca'] else print(f"  Médiane croissance CA      : N/A")
    print(f"  Médiane croissance Bénéfice: {croissances['benefice']:>6}%") if croissances['benefice'] else print(f"  Médiane croissance Bénéfice: N/A")
    print(f"  Médiane croissance FCF     : {croissances['fcf']:>6}%") if croissances['fcf'] else print(f"  Médiane croissance FCF     : N/A")
    print(f"  Médiane croissance EBITDA  : {croissances['ebitda']:>6}%") if croissances['ebitda'] else print(f"  Médiane croissance EBITDA  : N/A")

print("\n" + "="*70)
