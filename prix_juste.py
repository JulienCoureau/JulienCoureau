"""
Calculateur de Prix Juste - 3 methodes (BPA, FCF, Ventes)

Ce script calcule le prix juste d'actions en utilisant 3 methodes de valorisation:
- BPA (Benefice Par Action) avec PER
- FCF (Free Cash Flow) avec FCF Yield
- Ventes (Chiffre d'affaires) avec P/S

Les resultats sont ponderes par secteur et taille d'entreprise.
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List


class PrixJuste:
    """Calculateur de prix juste d'actions basé sur 3 méthodes de valorisation."""

    def __init__(
        self,
        json_path: str = "json_finance/bdd_zb_prix_juste.json",
        ratios_path: str = "json_finance/ratios_standard.json",
        rendement_cible: float = 0.15,
        horizon_projection: int = 5,
        horizon_ratio: int = 5
    ):
        """
        Initialise le calculateur.

        Args:
            json_path: Chemin vers le fichier JSON des données financières
            ratios_path: Chemin vers le fichier JSON des pondérations
            rendement_cible: Rendement annuel cible (default: 15%)
            horizon_projection: Nombre d'années de projection (default: 5)
            horizon_ratio: Nombre d'années pour calculer les médianes des ratios (default: 5)
        """
        self.rendement_cible = rendement_cible
        self.horizon_projection = horizon_projection
        self.horizon_ratio = horizon_ratio
        self.facteur_actualisation = (1 + rendement_cible) ** horizon_projection

        self.data = self._charger_json(json_path)
        self.ratios = self._charger_ratios(ratios_path)
        self.resultats = {}

    # === Chargement ===
    def _charger_json(self, path: str) -> Dict:
        """Charge le fichier JSON principal."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _charger_ratios(self, path: str) -> Dict:
        """Charge les ratios et les indexe par clé."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {item["cle"]: item for item in data["data"]}

    # === Setters pour paramètres configurables ===
    def set_rendement(self, rendement: float):
        """
        Modifie le rendement cible et recalcule le facteur d'actualisation.

        Args:
            rendement: Nouveau rendement cible (ex: 0.10 pour 10%)
        """
        self.rendement_cible = rendement
        self.facteur_actualisation = (1 + rendement) ** self.horizon_projection
        self.resultats = {}  # Reset les résultats pour forcer un recalcul

    def set_horizon_projection(self, horizon: int):
        """
        Modifie l'horizon de projection.

        Args:
            horizon: Nouveau nombre d'années de projection
        """
        self.horizon_projection = horizon
        self.facteur_actualisation = (1 + self.rendement_cible) ** horizon
        self.resultats = {}

    def set_horizon_ratio(self, horizon: int):
        """
        Modifie l'horizon pour les ratios (médiane).

        Args:
            horizon: Nouveau nombre d'années pour les ratios
        """
        self.horizon_ratio = horizon
        self.resultats = {}

    def afficher_parametres(self):
        """Affiche les paramètres actuels du calculateur."""
        print(f"\nPARAMETRES")
        print("-" * 40)
        print(f"Rendement cible      : {self.rendement_cible * 100:.1f}%")
        print(f"Horizon projection   : {self.horizon_projection} ans")
        print(f"Horizon ratios       : {self.horizon_ratio} ans")
        print(f"Facteur actualisation: {self.facteur_actualisation:.4f}")

    # === Utilitaires ===
    def _get_taille(self, capitalisation: float) -> str:
        """
        Détermine la taille selon la capitalisation.

        Args:
            capitalisation: Capitalisation boursière en devise locale

        Returns:
            Taille: "Large", "Mid", "Small" ou "Micro"
        """
        if capitalisation >= 10_000_000_000:  # >= 10 Md
            return "Large"
        elif capitalisation >= 2_000_000_000:  # >= 2 Md
            return "Mid"
        elif capitalisation >= 300_000_000:    # >= 300 M
            return "Small"
        else:
            return "Micro"

    def _get_ponderations(self, secteur: str, taille: str) -> Optional[Dict]:
        """
        Récupère les pondérations pour un secteur/taille.

        Args:
            secteur: Secteur Yahoo Finance
            taille: Taille de l'entreprise

        Returns:
            Dictionnaire des pondérations ou None si non trouvé
        """
        cle = f"{secteur}_{taille}"
        return self.ratios.get(cle)

    def _get_n_dernieres_annees(self, valeurs_dict: Dict, n: int) -> Dict:
        """
        Retourne les n dernières années d'un dictionnaire.

        Args:
            valeurs_dict: Dictionnaire {année: valeur}
            n: Nombre d'années à retourner

        Returns:
            Dictionnaire filtré aux n dernières années
        """
        annees_triees = sorted(valeurs_dict.keys(), reverse=True)[:n]
        return {a: valeurs_dict[a] for a in annees_triees}

    def _get_derniere_valeur(self, valeurs_dict: Dict):
        """
        Retourne la valeur de la dernière année.

        Args:
            valeurs_dict: Dictionnaire {année: valeur}

        Returns:
            Tuple (valeur, année)
        """
        derniere_annee = max(valeurs_dict.keys())
        return valeurs_dict[derniere_annee], derniere_annee

    # === Calcul croissances ===
    def _calculer_croissances(self, valeurs_dict: Dict) -> List[float]:
        """
        Calcule les croissances annuelles valides.

        Args:
            valeurs_dict: Dictionnaire {année: valeur}

        Returns:
            Liste des croissances valides (entre -50% et +200%)
        """
        croissances = []
        annees = sorted(valeurs_dict.keys())

        for i in range(1, len(annees)):
            val_prec = valeurs_dict[annees[i - 1]]
            val_act = valeurs_dict[annees[i]]

            # Vérifier que les valeurs sont valides
            if val_prec is None or val_act is None:
                continue
            if val_prec <= 0:
                continue

            croissance = (val_act / val_prec) - 1

            # Filtrer les croissances aberrantes
            if -0.5 <= croissance <= 2.0:
                croissances.append(croissance)

        return croissances

    def _calculer_cagr_median(self, valeurs_dict: Dict) -> Optional[float]:
        """
        Calcule le CAGR médian et l'ajuste si nécessaire.

        Args:
            valeurs_dict: Dictionnaire {année: valeur}

        Returns:
            CAGR médian ajusté ou None si invalide
        """
        croissances = self._calculer_croissances(valeurs_dict)

        # Minimum 5 croissances valides
        if len(croissances) < 5:
            return None

        cagr = float(np.median(croissances))

        # Ajustements
        if cagr < -0.20:
            return None  # Exclure
        if cagr > 0.50:
            cagr = 0.30  # Plafonner

        return cagr

    def _calculer_mediane_ratio(
        self, valeurs_dict: Dict, min_val: float, max_val: float
    ) -> Optional[float]:
        """
        Calcule la médiane d'un ratio avec filtrage.

        Args:
            valeurs_dict: Dictionnaire {année: valeur}
            min_val: Valeur minimum acceptée (exclusive)
            max_val: Valeur maximum acceptée (inclusive)

        Returns:
            Médiane des valeurs valides ou None si insuffisant
        """
        valeurs_filtrees = [
            v for v in valeurs_dict.values()
            if v is not None and min_val < v <= max_val
        ]

        # Minimum 3 valeurs valides
        if len(valeurs_filtrees) < 3:
            return None

        return float(np.median(valeurs_filtrees))

    # === 3 méthodes de prix ===
    def _prix_bpa(self, nom_entreprise: str) -> Dict:
        """
        Méthode 1 : Prix basé sur le BPA (Bénéfice Par Action).

        Formule: BPA_dernier * (1 + CAGR)^5 * PER_median / (1.15)^5

        Args:
            nom_entreprise: Nom de l'entreprise

        Returns:
            Dictionnaire avec le prix calculé et les détails
        """
        entreprise = self.data[nom_entreprise]

        # Récupérer données
        bpa_dict = entreprise.get("compte_de_resultat", {}).get(
            "BPA de base normalisé", {}
        )
        per_dict = entreprise.get("valorisation", {}).get("PER", {})

        if not bpa_dict or not per_dict:
            return {"prix": None, "raison": "Donnees manquantes"}

        # BPA dernier
        bpa_dernier, annee = self._get_derniere_valeur(bpa_dict)
        if bpa_dernier is None or bpa_dernier <= 0:
            return {"prix": None, "raison": "BPA <= 0"}

        # CAGR médian
        cagr = self._calculer_cagr_median(bpa_dict)
        if cagr is None:
            return {"prix": None, "raison": "CAGR invalide"}

        # PER médian (5 dernières années)
        per_5ans = self._get_n_dernieres_annees(per_dict, self.horizon_ratio)
        per_median = self._calculer_mediane_ratio(per_5ans, 5, 100)
        if per_median is None:
            return {"prix": None, "raison": "PER insuffisant"}

        # Calcul prix
        prix = (
            bpa_dernier
            * ((1 + cagr) ** self.horizon_projection)
            * per_median
            / self.facteur_actualisation
        )

        return {
            "prix": prix,
            "bpa_dernier": bpa_dernier,
            "cagr": cagr,
            "per_median": per_median,
            "raison": "OK"
        }

    def _prix_fcf(self, nom_entreprise: str) -> Dict:
        """
        Méthode 2 : Prix basé sur le FCF (Free Cash Flow).

        Formule: FCF_par_action * (1 + CAGR)^5 * (100/FCF_Yield) / (1.15)^5

        Args:
            nom_entreprise: Nom de l'entreprise

        Returns:
            Dictionnaire avec le prix calculé et les détails
        """
        entreprise = self.data[nom_entreprise]

        # Récupérer données
        fcfe_dict = entreprise.get("flux_de_tresorerie", {}).get(
            "Flux de trésorerie libre pour les actionnaires FCFE", {}
        )
        yield_dict = entreprise.get("valorisation", {}).get("FCF Yield", {})
        actions = entreprise.get("donnees_actuelles", {}).get("actions_circulation")

        if not fcfe_dict or not yield_dict or not actions:
            return {"prix": None, "raison": "Donnees manquantes"}

        # FCF par action dernier
        fcfe_dernier, annee = self._get_derniere_valeur(fcfe_dict)
        if fcfe_dernier is None or fcfe_dernier <= 0:
            return {"prix": None, "raison": "FCFE <= 0"}

        fcf_par_action = fcfe_dernier / actions

        # CAGR médian
        cagr = self._calculer_cagr_median(fcfe_dict)
        if cagr is None:
            return {"prix": None, "raison": "CAGR invalide"}

        # FCF Yield médian (5 dernières années)
        yield_5ans = self._get_n_dernieres_annees(yield_dict, self.horizon_ratio)
        yield_median = self._calculer_mediane_ratio(yield_5ans, 0, 20)
        if yield_median is None:
            return {"prix": None, "raison": "FCF Yield insuffisant"}

        # Multiple = 100 / Yield (car Yield est en %)
        multiple = 100 / yield_median

        # Calcul prix
        prix = (
            fcf_par_action
            * ((1 + cagr) ** self.horizon_projection)
            * multiple
            / self.facteur_actualisation
        )

        return {
            "prix": prix,
            "fcf_par_action": fcf_par_action,
            "cagr": cagr,
            "yield_median": yield_median,
            "multiple": multiple,
            "raison": "OK"
        }

    def _prix_ventes(self, nom_entreprise: str) -> Dict:
        """
        Méthode 3 : Prix basé sur les Ventes (Chiffre d'affaires).

        Formule: CA_par_action * (1 + CAGR)^5 * P/S_median / (1.15)^5

        Args:
            nom_entreprise: Nom de l'entreprise

        Returns:
            Dictionnaire avec le prix calculé et les détails
        """
        entreprise = self.data[nom_entreprise]

        # Récupérer données
        ca_dict = entreprise.get("compte_de_resultat", {}).get(
            "Total Chiffre d'affaires", {}
        )
        ps_dict = entreprise.get("valorisation", {}).get("Capitalisation / CA", {})
        actions = entreprise.get("donnees_actuelles", {}).get("actions_circulation")

        if not ca_dict or not ps_dict or not actions:
            return {"prix": None, "raison": "Donnees manquantes"}

        # CA par action dernier
        ca_dernier, annee = self._get_derniere_valeur(ca_dict)
        if ca_dernier is None or ca_dernier <= 0:
            return {"prix": None, "raison": "CA <= 0"}

        ca_par_action = ca_dernier / actions

        # CAGR médian
        cagr = self._calculer_cagr_median(ca_dict)
        if cagr is None:
            return {"prix": None, "raison": "CAGR invalide"}

        # P/S médian (5 dernières années)
        ps_5ans = self._get_n_dernieres_annees(ps_dict, self.horizon_ratio)
        ps_median = self._calculer_mediane_ratio(ps_5ans, 0, 15)
        if ps_median is None:
            return {"prix": None, "raison": "P/S insuffisant"}

        # Calcul prix
        prix = (
            ca_par_action
            * ((1 + cagr) ** self.horizon_projection)
            * ps_median
            / self.facteur_actualisation
        )

        return {
            "prix": prix,
            "ca_par_action": ca_par_action,
            "cagr": cagr,
            "ps_median": ps_median,
            "raison": "OK"
        }

    # === Prix final pondéré ===
    def _calculer_prix_pondere(self, nom_entreprise: str) -> Dict:
        """
        Calcule le prix juste pondéré final.

        Args:
            nom_entreprise: Nom de l'entreprise

        Returns:
            Dictionnaire avec le prix juste et tous les détails
        """
        entreprise = self.data[nom_entreprise]

        # Secteur et taille
        secteur = entreprise.get("infos", {}).get("secteur", "")
        capitalisation = entreprise.get("donnees_actuelles", {}).get(
            "capitalisation", 0
        )
        taille = self._get_taille(capitalisation)

        # Pondérations
        ponderations = self._get_ponderations(secteur, taille)
        if ponderations is None:
            return {
                "prix_juste": None,
                "erreur": f"Ponderations non trouvees pour {secteur}_{taille}"
            }

        # Calculer les 3 prix
        result_bpa = self._prix_bpa(nom_entreprise)
        result_fcf = self._prix_fcf(nom_entreprise)
        result_ventes = self._prix_ventes(nom_entreprise)

        # Construire dictionnaires
        prix = {
            "benefice": result_bpa["prix"],
            "fcf": result_fcf["prix"],
            "ventes": result_ventes["prix"]
        }

        poids = {
            "benefice": ponderations["ratio_benefice"],
            "fcf": ponderations["ratio_fcf"],
            "ventes": ponderations["ratio_ventes"]
        }

        # Filtrer méthodes valides
        methodes_valides = {
            k: v for k, v in prix.items() if v is not None and poids[k] > 0
        }

        if len(methodes_valides) == 0:
            return {
                "prix_juste": None,
                "erreur": "Aucune methode valide",
                "secteur": secteur,
                "taille": taille,
                "detail_bpa": result_bpa,
                "detail_fcf": result_fcf,
                "detail_ventes": result_ventes
            }

        # Poids normalisés
        poids_valides = {k: poids[k] for k in methodes_valides.keys()}
        somme_poids = sum(poids_valides.values())
        poids_normalises = {k: v / somme_poids for k, v in poids_valides.items()}

        # Prix pondéré
        prix_pondere = sum(prix[k] * poids_normalises[k] for k in poids_normalises)

        # Facteur décote
        prix_juste = prix_pondere * ponderations["facteur_decote"]

        return {
            "prix_juste": prix_juste,
            "prix_pondere_brut": prix_pondere,
            "facteur_decote": ponderations["facteur_decote"],
            "secteur": secteur,
            "taille": taille,
            "methodes_utilisees": list(methodes_valides.keys()),
            "poids_normalises": poids_normalises,
            "detail_bpa": result_bpa,
            "detail_fcf": result_fcf,
            "detail_ventes": result_ventes
        }

    # === Validation des données ===
    def _valider_entreprise(self, nom_entreprise: str) -> tuple:
        """
        Vérifie si une entreprise a les données minimales requises.

        Args:
            nom_entreprise: Nom de l'entreprise

        Returns:
            Tuple (est_valide, message_erreur)
        """
        entreprise = self.data.get(nom_entreprise, {})

        # Vérifier donnees_actuelles
        if "donnees_actuelles" not in entreprise:
            return False, "donnees_actuelles manquantes"

        donnees = entreprise["donnees_actuelles"]
        champs_requis = ["prix_actuel", "devise", "capitalisation", "actions_circulation"]
        for champ in champs_requis:
            if champ not in donnees or donnees[champ] is None:
                return False, f"{champ} manquant dans donnees_actuelles"

        # Vérifier infos
        if "infos" not in entreprise:
            return False, "infos manquantes"

        if "secteur" not in entreprise["infos"]:
            return False, "secteur manquant dans infos"

        return True, "OK"

    # === Interface publique ===
    def calculer(self, nom_entreprise: str = None) -> Dict:
        """
        Calcule le prix juste pour une ou toutes les entreprises.

        Args:
            nom_entreprise: Nom de l'entreprise (None = toutes)

        Returns:
            Dictionnaire des résultats
        """
        if nom_entreprise:
            est_valide, msg = self._valider_entreprise(nom_entreprise)
            if est_valide:
                self.resultats[nom_entreprise] = self._calculer_prix_pondere(nom_entreprise)
            else:
                self.resultats[nom_entreprise] = {
                    "prix_juste": None,
                    "erreur": f"Donnees invalides: {msg}"
                }
        else:
            for nom in self.data.keys():
                est_valide, msg = self._valider_entreprise(nom)
                if est_valide:
                    self.resultats[nom] = self._calculer_prix_pondere(nom)
                else:
                    self.resultats[nom] = {
                        "prix_juste": None,
                        "erreur": f"Donnees invalides: {msg}"
                    }
        return self.resultats

    def afficher(self):
        """Affiche le résumé simple des résultats."""
        print(f"\nPRIX JUSTE - {len(self.resultats)} entreprise(s)")
        print("=" * 70)
        print(f"{'Entreprise':<35} {'Actuel':>10} {'Juste':>10} {'Ecart':>8}")
        print("-" * 70)

        entreprises_invalides = []

        for nom, result in self.resultats.items():
            # Vérifier si les données actuelles existent
            donnees_actuelles = self.data[nom].get("donnees_actuelles", {})
            prix_actuel = donnees_actuelles.get("prix_actuel")
            devise = donnees_actuelles.get("devise", "?")
            prix_juste = result.get("prix_juste")

            # Symbole devise
            symbole = "E" if devise == "EUR" else "$" if devise == "USD" else devise[0] if devise else "?"

            # Si données actuelles manquantes
            if prix_actuel is None:
                entreprises_invalides.append((nom, result.get("erreur", "Donnees manquantes")))
                continue

            if prix_juste is None:
                print(
                    f"{nom[:35]:<35} {prix_actuel:>9.2f}{symbole} {'N/A':>10} {'N/A':>8}"
                )
            else:
                ecart = (prix_juste - prix_actuel) / prix_actuel * 100

                # Indicateur
                if ecart > 10:
                    indicateur = "[+]"  # Sous-évalué
                elif ecart < -10:
                    indicateur = "[-]"  # Surévalué
                else:
                    indicateur = "[=]"  # Neutre

                print(
                    f"{nom[:35]:<35} {prix_actuel:>9.2f}{symbole} "
                    f"{prix_juste:>9.2f}{symbole} {ecart:>+7.1f}% {indicateur}"
                )

        print("=" * 70)
        print("[+] Sous-evalue (>10%)  [=] Neutre (+/-10%)  [-] Surevalue (<-10%)")

        # Afficher les entreprises avec données invalides
        if entreprises_invalides:
            print(f"\n[!] {len(entreprises_invalides)} entreprise(s) ignoree(s) (donnees incompletes):")
            for nom, erreur in entreprises_invalides:
                print(f"    - {nom[:40]}: {erreur}")

    def detail(self, nom_entreprise: str):
        """
        Affiche le détail complet d'une entreprise.

        Args:
            nom_entreprise: Nom de l'entreprise
        """
        if nom_entreprise not in self.data:
            print(f"\n[!] Entreprise '{nom_entreprise}' non trouvee dans la base de donnees.")
            return

        if nom_entreprise not in self.resultats:
            self.calculer(nom_entreprise)

        result = self.resultats[nom_entreprise]
        entreprise = self.data[nom_entreprise]

        # Récupérer les données de manière sécurisée
        donnees_actuelles = entreprise.get("donnees_actuelles", {})
        prix_actuel = donnees_actuelles.get("prix_actuel")
        devise = donnees_actuelles.get("devise", "?")
        infos = entreprise.get("infos", {})
        ticker = infos.get("ticker", "N/A")

        print(f"\n{'=' * 70}")
        print(f"DETAIL : {nom_entreprise} ({ticker})")
        print(f"{'=' * 70}")

        # Vérifier si les données sont valides
        if prix_actuel is None:
            print(f"[!] Donnees incompletes pour cette entreprise")
            print(f"Erreur: {result.get('erreur', 'donnees_actuelles manquantes')}")
            print(f"{'=' * 70}")
            return

        print(
            f"Secteur: {result.get('secteur', 'N/A')} | "
            f"Taille: {result.get('taille', 'N/A')} | Devise: {devise}"
        )

        yahoo = entreprise.get("yahoo_finance", {})
        if yahoo:
            print(
                f"Prix actuel: {prix_actuel:.2f} {devise} | "
                f"52W: {yahoo.get('52_week_low', 'N/A')} - "
                f"{yahoo.get('52_week_high', 'N/A')} {devise}"
            )
        else:
            print(f"Prix actuel: {prix_actuel:.2f} {devise}")

        print(f"\nMETHODES DE BASE")
        print("-" * 70)

        # BPA
        bpa = result.get("detail_bpa", {})
        if bpa.get("prix"):
            poids = result.get("poids_normalises", {}).get("benefice", 0) * 100
            print(
                f"BPA    : {bpa['prix']:>10.2f} {devise} "
                f"(CAGR: {bpa['cagr']*100:>5.1f}%, PER: {bpa['per_median']:>5.1f})  "
                f"Poids: {poids:.0f}%"
            )
        else:
            print(f"BPA    : {'Exclu':<10} ({bpa.get('raison', 'N/A')})")

        # FCF
        fcf = result.get("detail_fcf", {})
        if fcf.get("prix"):
            poids = result.get("poids_normalises", {}).get("fcf", 0) * 100
            print(
                f"FCF    : {fcf['prix']:>10.2f} {devise} "
                f"(CAGR: {fcf['cagr']*100:>5.1f}%, Yield: {fcf['yield_median']:>4.1f}%)  "
                f"Poids: {poids:.0f}%"
            )
        else:
            print(f"FCF    : {'Exclu':<10} ({fcf.get('raison', 'N/A')})")

        # Ventes
        ventes = result.get("detail_ventes", {})
        if ventes.get("prix"):
            poids = result.get("poids_normalises", {}).get("ventes", 0) * 100
            print(
                f"Ventes : {ventes['prix']:>10.2f} {devise} "
                f"(CAGR: {ventes['cagr']*100:>5.1f}%, P/S: {ventes['ps_median']:>5.2f})  "
                f"Poids: {poids:.0f}%"
            )
        else:
            print(f"Ventes : {'Exclu':<10} ({ventes.get('raison', 'N/A')})")

        print(f"\nRESULTAT")
        print("-" * 70)

        if result.get("prix_juste"):
            print(f"Prix pondere brut : {result['prix_pondere_brut']:>10.2f} {devise}")
            print(f"Facteur decote    : x {result['facteur_decote']:.2f}")
            print(f"PRIX JUSTE        : {result['prix_juste']:>10.2f} {devise}")
            print("-" * 70)

            ecart = (result['prix_juste'] - prix_actuel) / prix_actuel * 100
            print(f"Prix actuel       : {prix_actuel:>10.2f} {devise}")
            print(f"Ecart             : {ecart:>+10.1f}%")

            if ecart > 10:
                print(f"Recommandation    : [+] SOUS-EVALUE - Opportunite d'achat")
            elif ecart < -10:
                print(f"Recommandation    : [-] SUREVALUE - Attendre")
            else:
                print(f"Recommandation    : [=] NEUTRE - Prix proche de la juste valeur")
        else:
            print(f"PRIX JUSTE        : Non calculable")
            print(f"Raison            : {result.get('erreur', 'N/A')}")

        print(f"{'=' * 70}")

    def exporter_json(self, output_path: str = "resultats_prix_juste.json"):
        """
        Exporte les résultats en JSON.

        Args:
            output_path: Chemin du fichier de sortie
        """
        export_data = {}
        for nom, result in self.resultats.items():
            entreprise = self.data[nom]
            donnees_actuelles = entreprise.get("donnees_actuelles", {})
            infos = entreprise.get("infos", {})

            prix_actuel = donnees_actuelles.get("prix_actuel")
            prix_juste = result.get("prix_juste")

            # Calculer l'écart uniquement si les deux prix sont disponibles
            ecart_pct = None
            if prix_juste is not None and prix_actuel is not None and prix_actuel != 0:
                ecart_pct = (prix_juste - prix_actuel) / prix_actuel * 100

            export_data[nom] = {
                "ticker": infos.get("ticker", "N/A"),
                "secteur": result.get("secteur"),
                "taille": result.get("taille"),
                "devise": donnees_actuelles.get("devise", "?"),
                "prix_actuel": prix_actuel,
                "prix_juste": prix_juste,
                "ecart_pct": ecart_pct,
                "erreur": result.get("erreur"),
                "methodes_utilisees": result.get("methodes_utilisees", []),
                "detail_bpa": result.get("detail_bpa"),
                "detail_fcf": result.get("detail_fcf"),
                "detail_ventes": result.get("detail_ventes")
            }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"\nResultats exportes vers: {output_path}")


if __name__ == "__main__":
    # Initialiser avec rendement 15%
    calc = PrixJuste(
        json_path="json_finance/bdd_zb_prix_juste.json",
        ratios_path="json_finance/ratios_standard.json",
        rendement_cible=0.15
    )

    # Afficher les paramètres
    calc.afficher_parametres()

    # Calculer toutes les entreprises
    calc.calculer()

    # Afficher résumé
    calc.afficher()

    # Afficher le détail de chaque entreprise
    print("\n" + "=" * 70)
    print("DETAILS PAR ENTREPRISE")
    print("=" * 70)

    for nom in calc.data.keys():
        calc.detail(nom)

    # Exemple avec rendement différent
    print("\n\n" + "=" * 70)
    print("=== AVEC RENDEMENT 10% ===")
    print("=" * 70)

    calc.set_rendement(0.10)
    calc.afficher_parametres()
    calc.calculer()
    calc.afficher()
