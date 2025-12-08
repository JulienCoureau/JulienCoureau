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

def calculer_prix_juste_benefice(entreprise_data, rendement_cible=15, horizon_annees=10):
    """
    Calcule le prix juste basé sur le bénéfice par action

    Formule :
    1. BPA actuel = Résultat net 2024 / Actions en circulation
    2. Croissance médiane = Médiane des taux de croissance 2015-2024
    3. BPA futur = BPA actuel × (1 + croissance)^horizon_annees
    4. Prix futur = BPA futur × PER médian historique
    5. Prix juste = Prix futur / (1 + rendement_cible)^horizon_annees

    Args:
        entreprise_data: Données de l'entreprise
        rendement_cible: Rendement annuel souhaité en % (défaut 15%)
        horizon_annees: Nombre d'années de projection (défaut 10)

    Returns:
        dict: Résultats du calcul
    """
    import statistics

    # Étape 1 : BPA actuel
    resultat_net_2024 = entreprise_data.get('compte_de_resultat', {}).get('Résultat net', {}).get('2024')
    actions = entreprise_data.get('donnees_actuelles', {}).get('actions_circulation')

    if not resultat_net_2024 or not actions:
        return None

    bpa_actuel = resultat_net_2024 / actions

    # Étape 2 : Croissance médiane
    benefices = entreprise_data.get('compte_de_resultat', {}).get('Résultat net', {})
    annees = ['2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024']

    taux_croissance = []
    for i in range(1, len(annees)):
        annee_prec = annees[i-1]
        annee_actu = annees[i]

        val_prec = benefices.get(annee_prec)
        val_actu = benefices.get(annee_actu)

        if val_prec and val_actu and val_prec > 0:
            taux = ((val_actu / val_prec) - 1) * 100
            taux_croissance.append(taux)

    if len(taux_croissance) < 3:
        return None

    croissance_mediane = statistics.median(taux_croissance)

    # Étape 3 : BPA futur
    bpa_futur = bpa_actuel * ((1 + croissance_mediane/100) ** horizon_annees)

    # Étape 4 : PER médian historique
    per_historiques = entreprise_data.get('valorisation', {}).get('PER', {})

    per_valeurs = []
    for annee, per in per_historiques.items():
        if per and per > 0:
            per_valeurs.append(per)

    if len(per_valeurs) < 3:
        return None

    per_median = statistics.median(per_valeurs)

    # Étape 5 : Prix futur
    prix_futur = bpa_futur * per_median

    # Étape 6 : Prix juste aujourd'hui
    prix_juste = prix_futur / ((1 + rendement_cible/100) ** horizon_annees)

    return {
        'bpa_actuel': round(bpa_actuel, 2),
        'croissance_mediane_%': round(croissance_mediane, 2),
        'bpa_futur': round(bpa_futur, 2),
        'per_median': round(per_median, 1),
        'prix_futur': round(prix_futur, 2),
        'prix_juste': round(prix_juste, 2),
        'rendement_cible_%': rendement_cible,
        'horizon_annees': horizon_annees
    }
