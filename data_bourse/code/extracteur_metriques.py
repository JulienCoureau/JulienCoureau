"""
Extracteur de Métriques Financières
====================================
Ce script extrait des métriques financières spécifiques depuis des fichiers Excel
et les synchronise avec des informations d'entreprise stockées dans un fichier JSON.

Auteur: Julien Coureau
Date: 2025-11-28
"""

import pandas as pd
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import glob

# ============================================================================
# ÉTAPE 1: DÉFINITION DES MÉTRIQUES À EXTRAIRE
# ============================================================================

# Métriques du compte de résultat
metriques_prix_juste_compte = [
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
    "Taux d'imposition effectif (%)",
]

# Métriques du bilan
metriques_prix_juste_bilan = [
    "Total dess capitaux propres",
    "Total de la dette",
    "Dette nette"
]

# Métriques des flux de trésorerie
metriques_prix_juste_fcf = [
    "Flux de trésorerie d'exploitation",
    "Dépenses d'investissement du capital (CAPEX)",
    "Flux de trésorerie d'investissement",
    "Flux de trésorerie de financement",
    "Flux de trésorerie libre pour les actionnaires FCFE"
]

# Métriques de valorisation
metriques_prix_juste_valorisation = [
    "PER",
    "Valeur entreprise / EBITDA",
    "FCF Yield"
]

# Configuration des chemins
CHEMIN_BASE_DONNEES = os.path.expanduser("~/documents/data_bourse/base_de_donnee")
CHEMIN_JSON = os.path.expanduser("~/documents/data_bourse/code/json_finance")
CHEMIN_SORTIE = os.path.expanduser("~/documents/data_bourse/output")


# ============================================================================
# ÉTAPE 2: FONCTION POUR CHARGER LES INFORMATIONS DU JSON
# ============================================================================

def charger_infos_entreprises(chemin_json: str) -> Dict:
    """
    Charge les informations des entreprises depuis le fichier JSON.

    Args:
        chemin_json: Chemin vers le répertoire contenant le fichier JSON

    Returns:
        Dictionnaire avec les informations des entreprises
        Format: {nom_entreprise: {ticker, industrie, ...}}
    """
    print("\n📂 ÉTAPE 2: Chargement des informations des entreprises...")

    # Chercher le fichier JSON dans le répertoire
    fichiers_json = glob.glob(os.path.join(chemin_json, "*.json"))

    if not fichiers_json:
        print(f"⚠️  Aucun fichier JSON trouvé dans {chemin_json}")
        return {}

    # Prendre le premier fichier JSON trouvé
    fichier_json = fichiers_json[0]
    print(f"✓ Fichier JSON trouvé: {os.path.basename(fichier_json)}")

    try:
        with open(fichier_json, 'r', encoding='utf-8') as f:
            donnees = json.load(f)

        # Créer un dictionnaire indexé par nom d'entreprise
        infos_entreprises = {}

        # Adapter selon la structure de votre JSON
        if isinstance(donnees, list):
            for entreprise in donnees:
                nom = entreprise.get('nom', '')
                infos_entreprises[nom] = entreprise
        elif isinstance(donnees, dict):
            infos_entreprises = donnees

        print(f"✓ {len(infos_entreprises)} entreprises chargées depuis le JSON")
        return infos_entreprises

    except Exception as e:
        print(f"❌ Erreur lors du chargement du JSON: {e}")
        return {}


# ============================================================================
# ÉTAPE 3: FONCTION POUR EXTRAIRE LE NOM DE L'ENTREPRISE DU FICHIER
# ============================================================================

def extraire_nom_entreprise(nom_fichier: str) -> str:
    """
    Extrait le nom de l'entreprise depuis le nom du fichier Excel.

    Args:
        nom_fichier: Nom du fichier (ex: "Apple_financials.xlsx")

    Returns:
        Nom de l'entreprise nettoyé
    """
    # Retirer l'extension
    nom_base = os.path.splitext(nom_fichier)[0]

    # Retirer les suffixes communs (à adapter selon vos fichiers)
    suffixes_a_retirer = ['_financials', '_data', '_metrics', '-financials', '-data']
    for suffixe in suffixes_a_retirer:
        if suffixe in nom_base:
            nom_base = nom_base.replace(suffixe, '')

    return nom_base.strip()


# ============================================================================
# ÉTAPE 4: FONCTION POUR EXTRAIRE LES MÉTRIQUES D'UNE FEUILLE
# ============================================================================

def extraire_metriques_feuille(df: pd.DataFrame, metriques: List[str],
                               nom_feuille: str) -> Dict:
    """
    Extrait les métriques spécifiques d'une feuille Excel.

    Args:
        df: DataFrame contenant les données de la feuille
        metriques: Liste des métriques à extraire
        nom_feuille: Nom de la feuille (pour les messages)

    Returns:
        Dictionnaire {nom_métrique: valeurs}
    """
    resultats = {}

    print(f"  📊 Extraction des métriques de: {nom_feuille}")

    # Supposons que la première colonne contient les noms des métriques
    # et les colonnes suivantes contiennent les valeurs (années)

    if df.empty:
        print(f"    ⚠️  Feuille vide: {nom_feuille}")
        return resultats

    # Identifier la colonne contenant les noms de métriques
    # (généralement la première colonne)
    colonne_noms = df.columns[0]

    for metrique in metriques:
        # Recherche exacte
        lignes_trouvees = df[df[colonne_noms] == metrique]

        if not lignes_trouvees.empty:
            # Extraire toutes les valeurs (années) pour cette métrique
            valeurs = lignes_trouvees.iloc[0, 1:].to_dict()
            resultats[metrique] = valeurs
            print(f"    ✓ {metrique}: {len(valeurs)} années trouvées")
        else:
            # Essayer une recherche partielle (insensible à la casse)
            lignes_partielles = df[df[colonne_noms].str.contains(
                metrique, case=False, na=False
            )]

            if not lignes_partielles.empty:
                valeurs = lignes_partielles.iloc[0, 1:].to_dict()
                resultats[metrique] = valeurs
                print(f"    ✓ {metrique}: {len(valeurs)} années trouvées (correspondance partielle)")
            else:
                print(f"    ⚠️  {metrique}: non trouvée")
                resultats[metrique] = None

    return resultats


# ============================================================================
# ÉTAPE 5: FONCTION PRINCIPALE POUR TRAITER UN FICHIER EXCEL
# ============================================================================

def traiter_fichier_excel(chemin_fichier: str, infos_entreprises: Dict) -> Optional[Dict]:
    """
    Traite un fichier Excel et extrait toutes les métriques.

    Args:
        chemin_fichier: Chemin complet vers le fichier Excel
        infos_entreprises: Dictionnaire des informations des entreprises

    Returns:
        Dictionnaire contenant toutes les données extraites
    """
    nom_fichier = os.path.basename(chemin_fichier)
    print(f"\n{'='*70}")
    print(f"📄 Traitement de: {nom_fichier}")
    print(f"{'='*70}")

    # Extraire le nom de l'entreprise
    nom_entreprise = extraire_nom_entreprise(nom_fichier)
    print(f"🏢 Entreprise: {nom_entreprise}")

    # Chercher les infos dans le JSON
    info_entreprise = None
    for nom_json, info in infos_entreprises.items():
        if nom_entreprise.lower() in nom_json.lower() or nom_json.lower() in nom_entreprise.lower():
            info_entreprise = info
            break

    if info_entreprise:
        print(f"✓ Informations trouvées dans le JSON")
        print(f"  - Ticker: {info_entreprise.get('ticker', 'N/A')}")
        print(f"  - Industrie: {info_entreprise.get('industrie', 'N/A')}")
    else:
        print(f"⚠️  Aucune information trouvée dans le JSON pour {nom_entreprise}")
        info_entreprise = {'ticker': 'N/A', 'industrie': 'N/A'}

    # Initialiser le dictionnaire de résultats
    resultats = {
        'nom': nom_entreprise,
        'ticker': info_entreprise.get('ticker', 'N/A'),
        'industrie': info_entreprise.get('industrie', 'N/A'),
        'metriques': {}
    }

    try:
        # Charger le fichier Excel
        excel_file = pd.ExcelFile(chemin_fichier)
        print(f"\n📑 Feuilles disponibles: {excel_file.sheet_names}")

        # Mapping des noms de feuilles possibles
        feuilles_mapping = {
            'compte_resultat': ['Compte de résultat', 'Compte de resultat', 'Income Statement', 'P&L'],
            'bilan': ['Bilan', 'Balance Sheet'],
            'flux_tresorerie': ['Flux de trésorerie', 'Flux de tresorerie', 'Cash Flow'],
            'valorisation': ['Valorisation', 'Valuation', 'Valorisations']
        }

        # Traiter chaque type de feuille
        for type_feuille, noms_possibles in feuilles_mapping.items():
            feuille_trouvee = None

            # Chercher la feuille correspondante
            for nom_possible in noms_possibles:
                if nom_possible in excel_file.sheet_names:
                    feuille_trouvee = nom_possible
                    break

            if not feuille_trouvee:
                print(f"  ⚠️  Feuille '{type_feuille}' non trouvée")
                continue

            # Lire la feuille
            df = pd.read_excel(chemin_fichier, sheet_name=feuille_trouvee)

            # Extraire les métriques selon le type
            if type_feuille == 'compte_resultat':
                metriques = extraire_metriques_feuille(
                    df, metriques_prix_juste_compte, feuille_trouvee
                )
                resultats['metriques'].update(metriques)

            elif type_feuille == 'bilan':
                metriques = extraire_metriques_feuille(
                    df, metriques_prix_juste_bilan, feuille_trouvee
                )
                resultats['metriques'].update(metriques)

            elif type_feuille == 'flux_tresorerie':
                metriques = extraire_metriques_feuille(
                    df, metriques_prix_juste_fcf, feuille_trouvee
                )
                resultats['metriques'].update(metriques)

            elif type_feuille == 'valorisation':
                metriques = extraire_metriques_feuille(
                    df, metriques_prix_juste_valorisation, feuille_trouvee
                )
                resultats['metriques'].update(metriques)

        print(f"\n✓ Extraction terminée: {len(resultats['metriques'])} métriques extraites")
        return resultats

    except Exception as e:
        print(f"\n❌ Erreur lors du traitement: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# ÉTAPE 6: FONCTION POUR SAUVEGARDER LES RÉSULTATS
# ============================================================================

def sauvegarder_resultats(tous_resultats: List[Dict], chemin_sortie: str):
    """
    Sauvegarde les résultats dans différents formats.

    Args:
        tous_resultats: Liste de tous les résultats extraits
        chemin_sortie: Répertoire de sortie
    """
    print(f"\n{'='*70}")
    print("💾 SAUVEGARDE DES RÉSULTATS")
    print(f"{'='*70}")

    # Créer le répertoire de sortie si nécessaire
    os.makedirs(chemin_sortie, exist_ok=True)

    # 1. Sauvegarder en JSON (format brut)
    chemin_json = os.path.join(chemin_sortie, "metriques_extraites.json")
    with open(chemin_json, 'w', encoding='utf-8') as f:
        json.dump(tous_resultats, f, indent=2, ensure_ascii=False)
    print(f"✓ JSON sauvegardé: {chemin_json}")

    # 2. Créer un DataFrame pour Excel/CSV
    # On va créer un format "large" avec une ligne par entreprise
    donnees_pour_df = []

    for resultat in tous_resultats:
        ligne = {
            'Nom': resultat['nom'],
            'Ticker': resultat['ticker'],
            'Industrie': resultat['industrie']
        }

        # Ajouter chaque métrique (on prend la dernière année disponible)
        for nom_metrique, valeurs in resultat['metriques'].items():
            if valeurs and isinstance(valeurs, dict):
                # Prendre la dernière colonne (année la plus récente)
                derniere_valeur = list(valeurs.values())[-1] if valeurs else None
                ligne[nom_metrique] = derniere_valeur
            else:
                ligne[nom_metrique] = valeurs

        donnees_pour_df.append(ligne)

    df_resultats = pd.DataFrame(donnees_pour_df)

    # Sauvegarder en Excel
    chemin_excel = os.path.join(chemin_sortie, "metriques_extraites.xlsx")
    df_resultats.to_excel(chemin_excel, index=False, engine='openpyxl')
    print(f"✓ Excel sauvegardé: {chemin_excel}")

    # Sauvegarder en CSV
    chemin_csv = os.path.join(chemin_sortie, "metriques_extraites.csv")
    df_resultats.to_csv(chemin_csv, index=False, encoding='utf-8')
    print(f"✓ CSV sauvegardé: {chemin_csv}")

    # 3. Créer un rapport résumé
    chemin_rapport = os.path.join(chemin_sortie, "rapport_extraction.txt")
    with open(chemin_rapport, 'w', encoding='utf-8') as f:
        f.write("RAPPORT D'EXTRACTION DES MÉTRIQUES FINANCIÈRES\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Nombre d'entreprises traitées: {len(tous_resultats)}\n\n")

        for resultat in tous_resultats:
            f.write(f"\n{resultat['nom']} ({resultat['ticker']})\n")
            f.write(f"  Industrie: {resultat['industrie']}\n")
            f.write(f"  Métriques extraites: {len([m for m in resultat['metriques'].values() if m])}\n")

    print(f"✓ Rapport sauvegardé: {chemin_rapport}")

    print(f"\n{'='*70}")
    print(f"✅ Tous les fichiers ont été sauvegardés dans: {chemin_sortie}")
    print(f"{'='*70}")


# ============================================================================
# ÉTAPE 7: FONCTION PRINCIPALE
# ============================================================================

def main():
    """
    Fonction principale qui orchestre tout le processus d'extraction.
    """
    print("\n" + "="*70)
    print("🚀 EXTRACTEUR DE MÉTRIQUES FINANCIÈRES")
    print("="*70)

    # Vérifier que les répertoires existent
    if not os.path.exists(CHEMIN_BASE_DONNEES):
        print(f"\n❌ Le répertoire {CHEMIN_BASE_DONNEES} n'existe pas!")
        print("Veuillez placer vos fichiers Excel dans ce répertoire.")
        return

    if not os.path.exists(CHEMIN_JSON):
        print(f"\n⚠️  Le répertoire {CHEMIN_JSON} n'existe pas!")
        print("Création du répertoire...")
        os.makedirs(CHEMIN_JSON, exist_ok=True)

    # Étape 1: Charger les informations des entreprises
    infos_entreprises = charger_infos_entreprises(CHEMIN_JSON)

    # Étape 2: Lister tous les fichiers Excel
    print(f"\n📂 ÉTAPE 3: Recherche des fichiers Excel...")
    fichiers_excel = glob.glob(os.path.join(CHEMIN_BASE_DONNEES, "*.xlsx"))
    fichiers_excel += glob.glob(os.path.join(CHEMIN_BASE_DONNEES, "*.xls"))

    print(f"✓ {len(fichiers_excel)} fichier(s) Excel trouvé(s)")

    if not fichiers_excel:
        print("\n⚠️  Aucun fichier Excel trouvé!")
        print(f"Veuillez placer vos fichiers dans: {CHEMIN_BASE_DONNEES}")
        return

    # Étape 3: Traiter chaque fichier
    print(f"\n{'='*70}")
    print("📊 ÉTAPE 4: TRAITEMENT DES FICHIERS")
    print(f"{'='*70}")

    tous_resultats = []

    for fichier in fichiers_excel:
        resultat = traiter_fichier_excel(fichier, infos_entreprises)
        if resultat:
            tous_resultats.append(resultat)

    # Étape 4: Sauvegarder les résultats
    if tous_resultats:
        sauvegarder_resultats(tous_resultats, CHEMIN_SORTIE)

        print(f"\n✅ EXTRACTION TERMINÉE AVEC SUCCÈS!")
        print(f"   {len(tous_resultats)} entreprise(s) traitée(s)")
    else:
        print("\n⚠️  Aucune donnée extraite")


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    main()
