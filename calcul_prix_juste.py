"""
Script de calcul du prix juste des actions
Méthode : Bénéfice Par Action (BPA)
"""

import json
import statistics
from pathlib import Path

# Chemins des fichiers
SCRIPT_DIR = Path(__file__).parent
JSON_FINANCE_DIR = SCRIPT_DIR / "json_finance"
BDD_FILE = JSON_FINANCE_DIR / "bdd_zb_prix_juste.json"
OUTPUT_JSON = JSON_FINANCE_DIR / "resultats_prix_juste.json"

def calculer_prix_juste_bpa(entreprise_data, rendement_cible=15):
    """
    Calcule le prix juste basé sur le BPA

    Formules :
    A. Croissance_t = (BPA_t / BPA_t-1) - 1
    B. CAGR_median = Mediane(Croissance_1 ... Croissance_n)
    C. BPA_projete = BPA_dernier * (1 + CAGR_median)
    D. PER_median = Mediane(PER_1 ... PER_n)
    E. Prix_juste_BPA = BPA_projete * PER_median
    F. Prix_achat_BPA = Prix_juste_BPA / (1 + Rendement_cible/100)

    Args:
        entreprise_data: Données de l'entreprise
        rendement_cible: Marge de sécurité en % (défaut 15%)

    Returns:
        dict: Résultats du calcul ou None
    """

    # Extraction des colonnes
    bpa_data = entreprise_data.get('compte_de_resultat', {}).get('BPA de base normalisé', {})
    per_data = entreprise_data.get('valorisation', {}).get('PER', {})
    prix_actuel = entreprise_data.get('donnees_actuelles', {}).get('prix_actuel')

    if not bpa_data or not per_data:
        return None

    annees = ['2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024']

    # Étape A : Croissance annuelle du BPA
    croissances = []
    for i in range(1, len(annees)):
        bpa_prec = bpa_data.get(annees[i-1])
        bpa_actu = bpa_data.get(annees[i])

        if bpa_prec and bpa_actu and bpa_prec > 0:
            croissance = (bpa_actu / bpa_prec) - 1
            croissances.append(croissance)

    if len(croissances) < 3:
        return None

    # Étape B : CAGR médian
    cagr_median = statistics.median(croissances)

    # Étape C : BPA projeté
    bpa_dernier = bpa_data.get('2024')
    if not bpa_dernier:
        return None

    bpa_projete = bpa_dernier * (1 + cagr_median)

    # Étape D : PER médian
    per_values = []
    for annee in annees:
        per = per_data.get(annee)
        if per and per > 0 and per < 100:  # Exclure aberrations
            per_values.append(per)

    if len(per_values) < 3:
        return None

    per_median = statistics.median(per_values)

    # Étape E : Prix Juste BPA
    prix_juste_bpa = bpa_projete * per_median

    # Étape F : Prix d'Achat (marge de sécurité)
    prix_achat_bpa = prix_juste_bpa / (1 + rendement_cible/100)

    return {
        'bpa_2024': round(bpa_dernier, 2),
        'croissance_mediane_%': round(cagr_median * 100, 2),
        'bpa_projete_2025': round(bpa_projete, 2),
        'per_median': round(per_median, 1),
        'prix_juste_bpa': round(prix_juste_bpa, 2),
        'prix_achat_bpa': round(prix_achat_bpa, 2),
        'prix_actuel': prix_actuel,
        'rendement_cible_%': rendement_cible
    }


if __name__ == "__main__":
    # Test
    with open(BDD_FILE, 'r', encoding='utf-8') as f:
        bdd = json.load(f)

    for nom_entreprise in list(bdd.keys())[:2]:
        print(f"\n{'='*60}")
        print(f"{nom_entreprise}")
        print('='*60)

        resultat = calculer_prix_juste_bpa(bdd[nom_entreprise])

        if resultat:
            for key, value in resultat.items():
                print(f"{key:25} : {value}")
