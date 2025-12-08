"""
Script de calcul du prix juste des actions
Version étape par étape
"""

import json
from pathlib import Path

# Chemins des fichiers
SCRIPT_DIR = Path(__file__).parent
JSON_FINANCE_DIR = SCRIPT_DIR / "json_finance"
BDD_FILE = JSON_FINANCE_DIR / "bdd_zb_prix_juste.json"
RATIOS_CONSERVATEUR = JSON_FINANCE_DIR / "ratios_conservateur.json"
RATIOS_STANDARD = JSON_FINANCE_DIR / "ratios_standard.json"
OUTPUT_JSON = JSON_FINANCE_DIR / "resultats_prix_juste.json"

print("✅ Configuration OK")
