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
        dict: Résultats du calcul avec détails
    """
    print("\n" + "="*70)
    print("CALCUL DÉTAILLÉ - MÉTHODE BÉNÉFICE")
    print("="*70)

    # Étape 1 : BPA actuel
    print("\n[1] CALCUL DU BPA ACTUEL (2024)")
    resultat_net_2024 = entreprise_data.get('compte_de_resultat', {}).get('Résultat net', {}).get('2024')
    actions = entreprise_data.get('donnees_actuelles', {}).get('actions_circulation')

    if not resultat_net_2024 or not actions:
        print("❌ Données manquantes")
        return None

    bpa_actuel = resultat_net_2024 / actions
    print(f"  Résultat net 2024 : {resultat_net_2024:,.0f}")
    print(f"  Actions circulation : {actions:,.0f}")
    print(f"  ➜ BPA 2024 = {resultat_net_2024:,.0f} / {actions:,.0f} = {bpa_actuel:.2f}")

    # Étape 2 : Croissance médiane
    print("\n[2] CALCUL DE LA CROISSANCE MÉDIANE (2015-2024)")
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
            print(f"  {annee_prec}→{annee_actu}: {taux:+.1f}%")

    if len(taux_croissance) < 3:
        print("❌ Pas assez de données")
        return None

    import statistics
    croissance_mediane = statistics.median(taux_croissance)
    print(f"  ➜ Médiane = {croissance_mediane:.2f}%")

    # Étape 3 : BPA futur
    print(f"\n[3] PROJECTION DU BPA FUTUR (dans {horizon_annees} ans)")
    bpa_futur = bpa_actuel * ((1 + croissance_mediane/100) ** horizon_annees)
    print(f"  BPA futur = {bpa_actuel:.2f} × (1 + {croissance_mediane:.2f}%)^{horizon_annees}")
    print(f"  ➜ BPA futur = {bpa_futur:.2f}")

    # Étape 4 : PER médian historique
    print("\n[4] CALCUL DU PER MÉDIAN HISTORIQUE")
    print("  (À implémenter : nécessite prix historiques)")
    per_median = 15  # Valeur par défaut pour l'instant
    print(f"  ➜ PER médian = {per_median} (valeur par défaut)")

    # Étape 5 : Prix futur
    print(f"\n[5] CALCUL DU PRIX FUTUR")
    prix_futur = bpa_futur * per_median
    print(f"  Prix futur = {bpa_futur:.2f} × {per_median}")
    print(f"  ➜ Prix futur = {prix_futur:.2f}")

    # Étape 6 : Prix juste aujourd'hui
    print(f"\n[6] ACTUALISATION AU PRIX JUSTE AUJOURD'HUI")
    print(f"  (avec rendement cible = {rendement_cible}%)")
    prix_juste = prix_futur / ((1 + rendement_cible/100) ** horizon_annees)
    print(f"  Prix juste = {prix_futur:.2f} / (1 + {rendement_cible}%)^{horizon_annees}")
    print(f"  ➜ Prix juste = {prix_juste:.2f}")

    print("="*70)

    return {
        'bpa_actuel': round(bpa_actuel, 2),
        'croissance_mediane_%': round(croissance_mediane, 2),
        'bpa_futur': round(bpa_futur, 2),
        'per_median': per_median,
        'prix_futur': round(prix_futur, 2),
        'prix_juste': round(prix_juste, 2),
        'rendement_cible_%': rendement_cible,
        'horizon_annees': horizon_annees
    }
