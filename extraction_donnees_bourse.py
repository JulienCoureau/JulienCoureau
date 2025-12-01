"""
Code pour extraire les données boursières venant d'un excel
Un copie/colle des données financiere de Zone_bourse

Extrait les données necessaires pour faire un simulation du prix juste d'une action
"""

import pandas as pd
import json
import os
from pathlib import Path

"""Configuration des dossiers à traiter et métriques à prendre"""

# Chemins des dossiers
#chemin_code = os.path.expanduser("~/Documents/Data_Bourse/Code")
chemin_json_finance = os.path.expanduser("~/Documents/Data_Bourse/Code/json_finance") # contenant le fichier json
chemin_base_donnees = os.path.expanduser("~/Documents/Data_Bourse/Base_de_donnee") # contenant les excels

# Fichiers
fichier_json_input = "name_action.json"  # Fichier JSON contenant les informations des entreprises (nom, ticker, industrie)
fichier_json_output = "bdd_zb_prix_juste.json"  # Fichier JSON de sortie avec toutes les données extraites

# Note : nommer les  fichiers Excel par le nom de l'entreprise (ex: schneider.xlsx, asml.xlsx), le scipt fera la correspondance des noms

# Années à extraire
annees = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]

metriques_prix_juste_compte = [
    "Total Chiffre d'affaires",
    "coût des marchandises vendues, total",
    "Résultat Brut",
    "Résultat d'Exploitation",
    "Intérêts payés, total",
    "Charges d'intérêt nettes",
    "Résultat net",
    "BPA de base normalisé",
    "EBITDA",
    "Taux d'imposition effectif (%)",
    "Dividende par action"
]

metriques_prix_juste_bilan = [
    "Total des capitaux propres",
    "Total de la dette",
    "Dette nette"
]

metriques_prix_juste_fcf = [
    "Flux de trésorerie d'exploitation",
    "Dépenses d'investissement du capital (CAPEX)",
    "Flux de trésorerie d'investissement",
    "Flux de trésorerie de financement",
    "Flux de trésorerie libre pour les actionnaires FCFE"
]

metriques_prix_juste_valorisation = [
    "PER",
    "Valeur Entreprise / EBITDA",
    "FCF Yield"
]

#1 Chargement du fichier json
json_path = os.path.join(chemin_json_finance, fichier_json_input)

if not os.path.exists(json_path):
    print(f"Erreur : Fichier JSON non trouvé : {json_path}")
    exit()

with open(json_path, 'r', encoding='utf-8') as f:
    data_entreprises = json.load(f)

#2 Chargement des dossiers a traiter dans Base_de_donnee
# Chercher tous les fichiers .xlsx dans le dossier Base_de_donnée
fichiers_excel = [f for f in os.listdir(chemin_base_donnees) if f.endswith('.xlsx') and not f.startswith('~')]

if not fichiers_excel:
    print(f"Aucun fichier Excel trouvé dans : {chemin_base_donnees}")
    exit()

#3 Normalisation
def normaliser_nom(nom):
    """Normalise un nom pour la comparaison"""
    import re
    nom = nom.lower()
    # Garder les / pour différencier "valeur entreprise" de "valeur entreprise / ebitda"
    nom = re.sub(r'[^a-z0-9/]', '', nom)
    return nom

#4 Trouve l'entreprise
def trouver_entreprise(nom_fichier, data_entreprises):
    """Trouve l'entreprise correspondante dans le JSON à partir du nom de fichier"""
    # Extraire le nom sans l'extension
    nom_base = os.path.splitext(nom_fichier)[0]
    nom_normalise = normaliser_nom(nom_base)

    # Chercher dans le JSON
    for stock in data_entreprises['stocks']:
        nom_entreprise_normalise = normaliser_nom(stock['name'])
        if nom_normalise in nom_entreprise_normalise or nom_entreprise_normalise in nom_normalise:
            return stock

    # Si pas trouvé, retourner None
    return None

#5 Selection des fichiers à traiter
try:
    import inquirer
except ImportError:
    print("\nInstallation de la bibliothèque 'inquirer' nécessaire...")
    import subprocess
    subprocess.check_call(['pip', 'install', 'inquirer'])
    import inquirer

fichiers_avec_statut = []
for fichier in fichiers_excel:
    entreprise = trouver_entreprise(fichier, data_entreprises)
    if entreprise:
        fichiers_avec_statut.append(fichier)
    else:
        fichiers_avec_statut.append(f"{fichier} (?)")

questions = [
    inquirer.Checkbox(
        'fichiers',
        message="Sélectionnez les fichiers à traiter (utilisez les flèches ↑↓, Espace pour sélectionner, Entrée pour valider)",
        choices=fichiers_avec_statut,
    ),
]

answers = inquirer.prompt(questions)
fichiers_selectionnes_bruts = answers['fichiers'] if answers else []

if not fichiers_selectionnes_bruts:
    print("Aucun fichier sélectionné. Arrêt du script.")
    exit()

# Nettoyer les noms de fichiers (enlever le " (?)" pour le traitement)
fichiers_selectionnes = [f.replace(" (?)", "") for f in fichiers_selectionnes_bruts]

print(f"\n{len(fichiers_selectionnes)} fichier(s) sélectionné(s) :")
for fichier in fichiers_selectionnes:
    print(f"  - {fichier}")

#6 Conversion des valeurs
def convertir_valeur(valeur, metrique):
    """Convertit les valeurs selon leur type et la métrique"""
    if pd.isna(valeur) or valeur == '' or valeur is None:
        return None

    valeur_str = str(valeur).strip()

    # Garders les pourcentages
    if '%' in valeur_str:
        return valeur_str

    # Ajouter % pour le taux d'imposition
    if "imposition" in metrique.lower():
        return f"{valeur_str}%"

    # Enlever espaces
    valeur_str = valeur_str.replace(' ', '')

    # Traiter Md
    if 'Md' in valeur_str:
        nombre = float(valeur_str.replace('Md', '').replace(',', '.'))
        return str(nombre * 1000000000).replace('.', ',')

    # Traiter M
    if 'M' in valeur_str and 'Md' not in valeur_str:
        nombre = float(valeur_str.replace('M', '').replace(',', '.'))
        return str(nombre * 1000000).replace('.', ',')

    # Traiter x
    if 'x' in valeur_str.lower():
        return valeur_str.replace('x', '').replace('X', '')

    # Retourner tel quel
    return valeur_str

#7 Extrait les donnees
def extraire_donnees(fichier_excel, sheet_name, metriques):
    """Extrait les métriques spécifiées d'une feuille Excel"""
    try:
        df = pd.read_excel(fichier_excel, sheet_name=sheet_name, header=0)

        items_column = df.columns[0]
        colonnes_annees = df.columns[1:11]

        resultats = []

        for metrique in metriques:
            metrique_normalise = normaliser_nom(metrique)
            ligne_trouvee = None

            for idx, row in df.iterrows():
                item_normalise = normaliser_nom(str(row[items_column]))
                # <CHANGE> Correspondance EXACTE au lieu de partielle
                if metrique_normalise == item_normalise:
                    ligne_trouvee = row
                    break

            if ligne_trouvee is not None:
                valeurs = {str(annees[i]): convertir_valeur(ligne_trouvee[colonnes_annees[i]], metrique) for i in range(len(annees))}
                resultats.append({
                    'Métrique': metrique,
                    'Valeurs': valeurs
                })

        return resultats
    except Exception as e:
        print(f"  Erreur lors de la lecture de la feuille '{sheet_name}': {e}")
        return []

#8 Traitement des fichiers
toutes_donnees = []

for fichier in fichiers_selectionnes:
    entreprise = trouver_entreprise(fichier, data_entreprises)

    if not entreprise:
        print(f"  Attention : Entreprise non trouvée dans le JSON pour {fichier}")
        continue

    chemin_fichier = os.path.join(chemin_base_donnees, fichier)

    # Correction des noms de feuilles (minuscules, sans accents)

    feuilles = {
        'compte de resultat': metriques_prix_juste_compte,
        'bilan': metriques_prix_juste_bilan,
        'flux de tresorerie': metriques_prix_juste_fcf,
        'valorisation': metriques_prix_juste_valorisation
    }

    for sheet_name, metriques in feuilles.items():
        donnees = extraire_donnees(chemin_fichier, sheet_name, metriques)

        for ligne in donnees:
            ligne['Nom'] = entreprise['name']
            ligne['Ticker'] = entreprise['ticker']
            ligne['Secteur'] = entreprise['sector']
            ligne['Industrie'] = entreprise['industry']
            ligne['Pays'] = entreprise['country']
            ligne['Feuille'] = sheet_name
            toutes_donnees.append(ligne)

print(f"\nTotal de {len(toutes_donnees)} / 22 lignes extraites")

#9 Sauvegarde
# Créer le dossier de sortie si nécessaire
if not os.path.exists(chemin_json_finance):
    os.makedirs(chemin_json_finance)
    print(f"Dossier créé : {chemin_json_finance}")

output_path = os.path.join(chemin_json_finance, fichier_json_output)

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(toutes_donnees, f, ensure_ascii=False, indent=2)

print(f"Données sauvegardées dans : {fichier_json_output}")
