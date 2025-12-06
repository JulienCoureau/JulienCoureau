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
    print("\nInstallation de la bibliothèque 'inquirer' nécessaire")
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
    """Convertit les valeurs selon leur type et la métrique - RETOURNE DES NOMBRES"""
    if pd.isna(valeur) or valeur == '' or valeur is None:
        return None

    valeur_str = str(valeur).strip()

    # Gérer les pourcentages (retourner comme float)
    if '%' in valeur_str:
        try:
            return float(valeur_str.replace('%', '').replace(',', '.').strip())
        except ValueError:
            return None

    # Ajouter % pour le taux d'imposition si pas déjà présent
    if "imposition" in metrique.lower() and '%' not in valeur_str:
        try:
            return float(valeur_str.replace(',', '.').strip())
        except ValueError:
            return None

    # Enlever espaces
    valeur_str = valeur_str.replace(' ', '')

    # Traiter Md (milliards)
    if 'Md' in valeur_str:
        try:
            nombre = float(valeur_str.replace('Md', '').replace(',', '.'))
            return nombre * 1000000000
        except ValueError:
            return None

    # Traiter M (millions)
    if 'M' in valeur_str and 'Md' not in valeur_str:
        try:
            nombre = float(valeur_str.replace('M', '').replace(',', '.'))
            return nombre * 1000000
        except ValueError:
            return None

    # Traiter x (multiples)
    if 'x' in valeur_str.lower():
        try:
            return float(valeur_str.replace('x', '').replace('X', '').replace(',', '.'))
        except ValueError:
            return None

    # Essayer de convertir en float
    try:
        return float(valeur_str.replace(',', '.'))
    except ValueError:
        return valeur_str  # Retourner la string si conversion impossible

#7 Extrait les donnees
def extraire_donnees(fichier_excel, sheet_name, metriques):
    """Extrait les métriques spécifiées d'une feuille Excel"""
    try:
        df = pd.read_excel(fichier_excel, sheet_name=sheet_name, header=0)

        items_column = df.columns[0]
        colonnes_annees = df.columns[1:11]

        resultats = {}

        for metrique in metriques:
            metrique_normalise = normaliser_nom(metrique)
            ligne_trouvee = None

            for idx, row in df.iterrows():
                item_normalise = normaliser_nom(str(row[items_column]))
                if metrique_normalise == item_normalise:
                    ligne_trouvee = row
                    break

            if ligne_trouvee is not None:
                valeurs = {str(annees[i]): convertir_valeur(ligne_trouvee[colonnes_annees[i]], metrique) for i in range(len(annees))}
                resultats[metrique] = valeurs

        return resultats
    except Exception as e:
        print(f"  Erreur lors de la lecture de la feuille '{sheet_name}': {e}")
        return {}

#8 Traitement des fichiers
donnees_structurees = {}
metriques_total = 0

for fichier in fichiers_selectionnes:
    entreprise = trouver_entreprise(fichier, data_entreprises)

    if not entreprise:
        print(f"  Attention : Entreprise non trouvée dans le JSON pour {fichier}")
        continue

    nom_entreprise = entreprise['name']

    # Créer la structure pour cette entreprise
    donnees_structurees[nom_entreprise] = {
        "infos": {
            "ticker": entreprise['ticker'],
            "secteur": entreprise['sector'],
            "industrie": entreprise['industry'],
            "pays": entreprise['country']
        }
    }

    chemin_fichier = os.path.join(chemin_base_donnees, fichier)

    # Extraction des données par feuille
    feuilles = {
        'compte_de_resultat': ('compte de resultat', metriques_prix_juste_compte),
        'bilan': ('bilan', metriques_prix_juste_bilan),
        'flux_de_tresorerie': ('flux de tresorerie', metriques_prix_juste_fcf),
        'valorisation': ('valorisation', metriques_prix_juste_valorisation)
    }

    for cle_structure, (nom_feuille, metriques) in feuilles.items():
        donnees = extraire_donnees(chemin_fichier, nom_feuille, metriques)
        donnees_structurees[nom_entreprise][cle_structure] = donnees
        metriques_total += len(donnees)

print(f"\nTotal de {metriques_total} / 22 lignes extraites")

# Vérification des métriques manquantes
if metriques_total != 22:
    metriques_attendues = (
        metriques_prix_juste_compte +
        metriques_prix_juste_bilan +
        metriques_prix_juste_fcf +
        metriques_prix_juste_valorisation
    )

    # Collecter toutes les métriques récoltées
    metriques_recoltees = []
    for entreprise_data in donnees_structurees.values():
        for feuille in ['compte_de_resultat', 'bilan', 'flux_de_tresorerie', 'valorisation']:
            metriques_recoltees.extend(entreprise_data[feuille].keys())

    metriques_manquantes = [m for m in metriques_attendues if m not in metriques_recoltees]

    if metriques_manquantes:
        print(f"\n⚠️  ATTENTION : {len(metriques_manquantes)} métrique(s) manquante(s) :")
        for metrique in metriques_manquantes:
            print(f"  - {metrique}")

#9 Sauvegarde
# Créer le dossier de sortie si nécessaire
if not os.path.exists(chemin_json_finance):
    os.makedirs(chemin_json_finance)
    print(f"Dossier créé : {chemin_json_finance}")

output_path = os.path.join(chemin_json_finance, fichier_json_output)

# Charger les données existantes si le fichier existe
donnees_existantes = {}
if os.path.exists(output_path):
    with open(output_path, 'r', encoding='utf-8') as f:
        try:
            donnees_existantes = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️  Avertissement : Fichier JSON corrompu, création d'un nouveau fichier")
            donnees_existantes = {}

# Fusionner les nouvelles données avec les existantes (écrase les doublons)
donnees_existantes.update(donnees_structurees)

# Sauvegarder le tout
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(donnees_existantes, f, ensure_ascii=False, indent=2)

print(f"\nDonnées sauvegardées dans : {fichier_json_output}")
print(f"  - {len(donnees_structurees)} entreprise(s) ajoutée(s) : {', '.join(donnees_structurees.keys())}")
print(f"  - Total dans la base : {len(donnees_existantes)} entreprise(s)")
