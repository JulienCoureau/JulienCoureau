"""
Script de calcul du prix juste des actions
Utilise les ratios pondérés par secteur et taille d'entreprise

Calcule 2 estimations :
- Prix juste conservateur (prudent)
- Prix juste standard (optimiste)
"""

import json
import os
from pathlib import Path
import pandas as pd
import statistics

# Chemins des fichiers
SCRIPT_DIR = Path(__file__).parent
JSON_FINANCE_DIR = SCRIPT_DIR / "json_finance"
BDD_FILE = JSON_FINANCE_DIR / "bdd_zb_prix_juste.json"
RATIOS_CONSERVATEUR = JSON_FINANCE_DIR / "ratios_conservateur.json"
RATIOS_STANDARD = JSON_FINANCE_DIR / "ratios_standard.json"
OUTPUT_JSON = JSON_FINANCE_DIR / "resultats_prix_juste.json"
OUTPUT_CSV = JSON_FINANCE_DIR / "resultats_prix_juste.csv"

def determiner_taille(capitalisation):
    """Détermine la taille de l'entreprise selon sa capitalisation

    Args:
        capitalisation: Capitalisation boursière

    Returns:
        str: "Large", "Mid", "Small" ou "Micro"
    """
    if capitalisation is None:
        return "Large"  # Par défaut

    # Conversion en milliards
    cap_md = capitalisation / 1_000_000_000

    if cap_md >= 10:
        return "Large"
    elif cap_md >= 2:
        return "Mid"
    elif cap_md >= 0.3:
        return "Small"
    else:
        return "Micro"

def trouver_ratios(secteur, taille, ratios_data):
    """Trouve les ratios correspondant au secteur et à la taille

    Args:
        secteur: Secteur de l'entreprise (ex: "Industrials")
        taille: Taille de l'entreprise ("Large", "Mid", "Small", "Micro")
        ratios_data: Liste des ratios

    Returns:
        dict: Ratios trouvés ou None
    """
    cle = f"{secteur}_{taille}"

    for ratio in ratios_data:
        if ratio['cle'] == cle:
            return ratio

    return None

def calculer_croissance_mediane(entreprise_data):
    """Calcule la médiane de croissance sur 10 ans (2015-2024) pour toutes les métriques

    Args:
        entreprise_data: Données de l'entreprise

    Returns:
        dict: Médianes de croissance par métrique (en %)
    """
    annees = ['2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024']

    metriques = {
        'ca': entreprise_data.get('compte_de_resultat', {}).get('Total Chiffre d\'affaires', {}),
        'benefice': entreprise_data.get('compte_de_resultat', {}).get('Résultat net', {}),
        'fcf': entreprise_data.get('flux_de_tresorerie', {}).get('Flux de trésorerie libre pour les actionnaires FCFE', {}),
        'ebitda': entreprise_data.get('compte_de_resultat', {}).get('EBITDA', {})
    }

    resultats = {}

    for nom_metrique, donnees_metrique in metriques.items():
        taux_croissance = []

        # Calculer les taux de croissance année par année
        for i in range(1, len(annees)):
            annee_precedente = annees[i-1]
            annee_actuelle = annees[i]

            valeur_precedente = donnees_metrique.get(annee_precedente)
            valeur_actuelle = donnees_metrique.get(annee_actuelle)

            # Vérifier que les deux valeurs existent et sont positives
            if valeur_precedente and valeur_actuelle and valeur_precedente > 0:
                taux = ((valeur_actuelle / valeur_precedente) - 1) * 100
                taux_croissance.append(taux)

        # Calculer la médiane si on a au moins 3 points de données
        if len(taux_croissance) >= 3:
            mediane = statistics.median(taux_croissance)
            resultats[nom_metrique] = round(mediane, 2)
        else:
            resultats[nom_metrique] = None

    return resultats

def calculer_prix_juste(entreprise_data, ratios):
    """Calcule le prix juste d'une action

    Args:
        entreprise_data: Données de l'entreprise
        ratios: Ratios pondérés à utiliser

    Returns:
        dict: Résultats du calcul
    """
    # Récupérer les données nécessaires (année 2024)
    actions_circulation = entreprise_data.get('donnees_actuelles', {}).get('actions_circulation')

    if not actions_circulation:
        return None

    # Extraire les métriques 2024
    resultat_net = entreprise_data.get('compte_de_resultat', {}).get('Résultat net', {}).get('2024')
    fcfe = entreprise_data.get('flux_de_tresorerie', {}).get('Flux de trésorerie libre pour les actionnaires FCFE', {}).get('2024')
    ca = entreprise_data.get('compte_de_resultat', {}).get('Total Chiffre d\'affaires', {}).get('2024')
    ebitda = entreprise_data.get('compte_de_resultat', {}).get('EBITDA', {}).get('2024')
    capitaux_propres = entreprise_data.get('bilan', {}).get('Total des capitaux propres', {}).get('2024')

    # Calcul des prix par action pour chaque métrique
    prix_par_action = {}

    if resultat_net:
        prix_par_action['benefice'] = resultat_net / actions_circulation
    else:
        prix_par_action['benefice'] = 0

    if fcfe:
        prix_par_action['fcf'] = fcfe / actions_circulation
    else:
        prix_par_action['fcf'] = 0

    if ca:
        prix_par_action['ventes'] = ca / actions_circulation
    else:
        prix_par_action['ventes'] = 0

    if ebitda:
        prix_par_action['ebitda'] = ebitda / actions_circulation
    else:
        prix_par_action['ebitda'] = 0

    if capitaux_propres:
        prix_par_action['book_value'] = capitaux_propres / actions_circulation
    else:
        prix_par_action['book_value'] = 0

    # Calcul du prix juste pondéré
    prix_juste_brut = (
        prix_par_action['benefice'] * ratios['ratio_benefice'] +
        prix_par_action['fcf'] * ratios['ratio_fcf'] +
        prix_par_action['ventes'] * ratios['ratio_ventes'] +
        prix_par_action['ebitda'] * ratios['ratio_ebitda'] +
        prix_par_action['book_value'] * ratios['ratio_book_value']
    )

    # Application du facteur de décote (marge de sécurité)
    prix_juste_final = prix_juste_brut * ratios['facteur_decote']

    return {
        'prix_juste_brut': round(prix_juste_brut, 2),
        'prix_juste_final': round(prix_juste_final, 2),
        'prix_par_action': {k: round(v, 2) for k, v in prix_par_action.items()},
        'ratios_utilises': {
            'ratio_benefice': ratios['ratio_benefice'],
            'ratio_fcf': ratios['ratio_fcf'],
            'ratio_ventes': ratios['ratio_ventes'],
            'ratio_ebitda': ratios['ratio_ebitda'],
            'ratio_book_value': ratios['ratio_book_value'],
            'facteur_decote': ratios['facteur_decote']
        }
    }

def main():
    """Fonction principale"""

    print("\n" + "="*70)
    print("CALCUL DU PRIX JUSTE DES ACTIONS")
    print("="*70)

    # Charger les données
    print("\n📂 Chargement des données...")

    with open(BDD_FILE, 'r', encoding='utf-8') as f:
        bdd_data = json.load(f)

    with open(RATIOS_CONSERVATEUR, 'r', encoding='utf-8') as f:
        ratios_conservateur = json.load(f)['data']

    with open(RATIOS_STANDARD, 'r', encoding='utf-8') as f:
        ratios_standard = json.load(f)['data']

    print(f"   ✅ {len(bdd_data)} entreprise(s) chargée(s)")
    print(f"   ✅ {len(ratios_conservateur)} ratios conservateurs")
    print(f"   ✅ {len(ratios_standard)} ratios standard")

    # Calcul pour chaque entreprise
    resultats = {}
    resultats_liste = []  # Pour CSV

    print(f"\n🔢 Calcul du prix juste...\n")

    for i, (nom_entreprise, entreprise_data) in enumerate(bdd_data.items(), 1):
        print(f"[{i}/{len(bdd_data)}] {nom_entreprise[:50]:50} ", end="", flush=True)

        # Récupérer infos
        infos = entreprise_data.get('infos', {})
        secteur = infos.get('secteur')
        ticker = infos.get('ticker')
        donnees_actuelles = entreprise_data.get('donnees_actuelles', {})
        prix_actuel = donnees_actuelles.get('prix_actuel')
        capitalisation = donnees_actuelles.get('capitalisation')
        devise = donnees_actuelles.get('devise', 'N/A')

        if not secteur or not capitalisation:
            print("⚠️  Données manquantes")
            continue

        # Déterminer la taille
        taille = determiner_taille(capitalisation)

        # Trouver les ratios
        ratios_cons = trouver_ratios(secteur, taille, ratios_conservateur)
        ratios_std = trouver_ratios(secteur, taille, ratios_standard)

        if not ratios_cons or not ratios_std:
            print(f"⚠️  Ratios non trouvés ({secteur}_{taille})")
            continue

        # Calculer prix juste
        calcul_conservateur = calculer_prix_juste(entreprise_data, ratios_cons)
        calcul_standard = calculer_prix_juste(entreprise_data, ratios_std)

        if not calcul_conservateur or not calcul_standard:
            print("⚠️  Erreur de calcul")
            continue

        # Calcul des écarts avec prix actuel
        ecart_conservateur = None
        ecart_standard = None
        potentiel_conservateur = None
        potentiel_standard = None

        if prix_actuel:
            ecart_conservateur = calcul_conservateur['prix_juste_final'] - prix_actuel
            ecart_standard = calcul_standard['prix_juste_final'] - prix_actuel
            potentiel_conservateur = ((calcul_conservateur['prix_juste_final'] / prix_actuel) - 1) * 100
            potentiel_standard = ((calcul_standard['prix_juste_final'] / prix_actuel) - 1) * 100

        # Stocker résultats
        resultats[nom_entreprise] = {
            'infos': {
                'ticker': ticker,
                'secteur': secteur,
                'taille': taille,
                'devise': devise
            },
            'prix_actuel': prix_actuel,
            'prix_juste_conservateur': calcul_conservateur['prix_juste_final'],
            'prix_juste_standard': calcul_standard['prix_juste_final'],
            'ecart_conservateur': round(ecart_conservateur, 2) if ecart_conservateur else None,
            'ecart_standard': round(ecart_standard, 2) if ecart_standard else None,
            'potentiel_conservateur_%': round(potentiel_conservateur, 2) if potentiel_conservateur else None,
            'potentiel_standard_%': round(potentiel_standard, 2) if potentiel_standard else None,
            'details_conservateur': calcul_conservateur,
            'details_standard': calcul_standard
        }

        # Pour CSV
        resultats_liste.append({
            'Entreprise': nom_entreprise,
            'Ticker': ticker,
            'Secteur': secteur,
            'Taille': taille,
            'Devise': devise,
            'Prix actuel': prix_actuel,
            'Prix juste conservateur': calcul_conservateur['prix_juste_final'],
            'Prix juste standard': calcul_standard['prix_juste_final'],
            'Écart conservateur': round(ecart_conservateur, 2) if ecart_conservateur else None,
            'Écart standard': round(ecart_standard, 2) if ecart_standard else None,
            'Potentiel conservateur %': round(potentiel_conservateur, 2) if potentiel_conservateur else None,
            'Potentiel standard %': round(potentiel_standard, 2) if potentiel_standard else None
        })

        print(f"✅ {calcul_conservateur['prix_juste_final']:.2f} / {calcul_standard['prix_juste_final']:.2f} {devise}")

    # Sauvegarder JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)

    # Sauvegarder CSV
    df = pd.DataFrame(resultats_liste)
    df = df.sort_values('Potentiel conservateur %', ascending=False)
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')

    # Résumé
    print("\n" + "="*70)
    print("✅ CALCUL TERMINÉ")
    print("="*70)
    print(f"  Entreprises traitées : {len(resultats)}/{len(bdd_data)}")
    print(f"\n📁 Fichiers générés :")
    print(f"  - {OUTPUT_JSON}")
    print(f"  - {OUTPUT_CSV}")
    print("="*70)

    # Affichage top 5 opportunités
    if resultats_liste:
        print(f"\n🎯 TOP 5 OPPORTUNITÉS (conservateur) :\n")
        df_top = df.head(5)
        for idx, row in df_top.iterrows():
            pot = row['Potentiel conservateur %']
            signe = "📈" if pot > 0 else "📉"
            print(f"{signe} {row['Entreprise'][:40]:40} {row['Prix actuel']:8.2f} → {row['Prix juste conservateur']:8.2f} {row['Devise']} ({pot:+.1f}%)")

    return resultats

if __name__ == "__main__":
    main()
