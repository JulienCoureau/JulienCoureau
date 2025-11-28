"""
Script de Test - Extracteur de Métriques Financières
Ce script crée un fichier Excel de test pour vérifier que tout fonctionne.
"""

import pandas as pd
import os
from pathlib import Path

def creer_excel_test():
    """Crée un fichier Excel de test avec des données fictives."""

    print("🔧 Création d'un fichier Excel de test...")

    # Chemin de sortie
    chemin_base = os.path.expanduser("~/documents/data_bourse/base_de_donnee")
    os.makedirs(chemin_base, exist_ok=True)
    chemin_fichier = os.path.join(chemin_base, "Apple_test.xlsx")

    # Créer les données pour le Compte de Résultat
    compte_resultat = pd.DataFrame({
        'Métrique': [
            "Total Chiffre d'affaires",
            "coût des marchandises vendues, total",
            "Résultat Brut",
            "Résultat d'Exploitation",
            "Intérêts payés, total",
            "Charges d'intérêt nettes",
            "Résultat net",
            "BPA de base normalisé",
            "Dividende par action",
            "EBITDA",
            "Taux d'imposition effectif (%)"
        ],
        '2021': [365817000000, 212981000000, 152836000000, 108949000000,
                 2645000000, 2645000000, 94680000000, 5.61, 0.85,
                 120233000000, 14.4],
        '2022': [394328000000, 223546000000, 170782000000, 119437000000,
                 2931000000, 2931000000, 99803000000, 6.11, 0.90,
                 130541000000, 16.2],
        '2023': [383285000000, 214137000000, 169148000000, 114301000000,
                 3933000000, 3933000000, 96995000000, 6.13, 0.94,
                 125820000000, 14.7],
        '2024': [391035000000, 210352000000, 180683000000, 123217000000,
                 3803000000, 3803000000, 101956000000, 6.42, 0.98,
                 135489000000, 15.1]
    })

    # Créer les données pour le Bilan
    bilan = pd.DataFrame({
        'Métrique': [
            "Total dess capitaux propres",
            "Total de la dette",
            "Dette nette"
        ],
        '2021': [63090000000, 124719000000, 90434000000],
        '2022': [50672000000, 120069000000, 96423000000],
        '2023': [62146000000, 111088000000, 77963000000],
        '2024': [74420000000, 106639000000, 68250000000]
    })

    # Créer les données pour les Flux de Trésorerie
    flux_tresorerie = pd.DataFrame({
        'Métrique': [
            "Flux de trésorerie d'exploitation",
            "Dépenses d'investissement du capital (CAPEX)",
            "Flux de trésorerie d'investissement",
            "Flux de trésorerie de financement",
            "Flux de trésorerie libre pour les actionnaires FCFE"
        ],
        '2021': [104038000000, -11085000000, -14545000000, -93353000000, 92953000000],
        '2022': [122151000000, -10708000000, -22354000000, -110749000000, 111443000000],
        '2023': [110543000000, -10959000000, -3705000000, -108488000000, 99584000000],
        '2024': [118254000000, -9447000000, -8018000000, -101168000000, 108807000000]
    })

    # Créer les données pour la Valorisation
    valorisation = pd.DataFrame({
        'Métrique': [
            "PER",
            "Valeur entreprise / EBITDA",
            "FCF Yield"
        ],
        '2021': [26.88, 21.45, 3.21],
        '2022': [24.35, 19.87, 3.85],
        '2023': [29.43, 22.31, 3.52],
        '2024': [31.25, 23.15, 3.68]
    })

    # Créer le fichier Excel avec plusieurs feuilles
    with pd.ExcelWriter(chemin_fichier, engine='openpyxl') as writer:
        compte_resultat.to_excel(writer, sheet_name='Compte de résultat', index=False)
        bilan.to_excel(writer, sheet_name='Bilan', index=False)
        flux_tresorerie.to_excel(writer, sheet_name='Flux de trésorerie', index=False)
        valorisation.to_excel(writer, sheet_name='Valorisation', index=False)

    print(f"✓ Fichier Excel de test créé: {chemin_fichier}")
    print(f"  - Feuille 1: Compte de résultat ({len(compte_resultat)} métriques)")
    print(f"  - Feuille 2: Bilan ({len(bilan)} métriques)")
    print(f"  - Feuille 3: Flux de trésorerie ({len(flux_tresorerie)} métriques)")
    print(f"  - Feuille 4: Valorisation ({len(valorisation)} métriques)")

    return chemin_fichier


def verifier_structure():
    """Vérifie que toute la structure de répertoires existe."""

    print("\n🔍 Vérification de la structure des répertoires...")

    repertoires = [
        "~/documents/data_bourse/base_de_donnee",
        "~/documents/data_bourse/code/json_finance",
        "~/documents/data_bourse/output"
    ]

    tous_ok = True
    for rep in repertoires:
        chemin = os.path.expanduser(rep)
        if os.path.exists(chemin):
            print(f"  ✓ {rep}")
        else:
            print(f"  ❌ {rep} - manquant!")
            tous_ok = False

    return tous_ok


def main():
    """Fonction principale du script de test."""

    print("\n" + "="*60)
    print("🧪 SCRIPT DE TEST - Extracteur de Métriques Financières")
    print("="*60 + "\n")

    # Vérifier la structure
    if not verifier_structure():
        print("\n⚠️  Certains répertoires sont manquants.")
        print("Veuillez d'abord exécuter le script principal.")
        return

    # Créer le fichier de test
    print("\n" + "="*60)
    fichier_cree = creer_excel_test()

    # Vérifier le fichier JSON
    chemin_json = os.path.expanduser("~/documents/data_bourse/code/json_finance")
    fichiers_json = [f for f in os.listdir(chemin_json) if f.endswith('.json')]

    print(f"\n📄 Fichiers JSON trouvés: {len(fichiers_json)}")
    if fichiers_json:
        print(f"  ✓ {fichiers_json[0]}")
    else:
        print("  ⚠️  Aucun fichier JSON trouvé!")
        print("  Un fichier exemple a été créé lors de l'installation.")

    print("\n" + "="*60)
    print("✅ FICHIER DE TEST CRÉÉ AVEC SUCCÈS!")
    print("="*60)
    print("\nVous pouvez maintenant exécuter:")
    print("  python3 extracteur_metriques.py")
    print("\nPour tester l'extraction avec le fichier de test.")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
