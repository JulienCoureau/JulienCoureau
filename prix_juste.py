"""
Calculateur de Prix Juste d'Actions
====================================
Calcule un prix juste unique par action en combinant:
- 5 methodes de base ponderees par secteur/taille
- 3 methodes complementaires (PEG, Gordon, Beta)
- 6 types de moyennes pour la synthese finale
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class PrixJuste:
    """Calculateur de prix juste pour actions."""

    # Limites de validation des ratios
    LIMITES_RATIOS = {
        "PER": (0, 100),
        "FCF_Yield": (0, 20),
        "EV_EBITDA": (0, 50),
        "PS": (0, 30),
        "PB": (0, 20)
    }

    # Limites de validation des croissances
    LIMITE_CROISSANCE_MIN = -0.50  # -50%
    LIMITE_CROISSANCE_MAX = 2.00   # +200%

    # Seuils CAGR
    CAGR_PLAFOND = 0.30  # 30% - plafonner si > 50%
    CAGR_EXCLUSION = -0.20  # -20% - exclure si inferieur

    # Minimums de donnees
    MIN_RATIOS = 3  # Minimum 3 valeurs sur 5 ans
    MIN_CROISSANCES = 5  # Minimum 5 valeurs sur 10 ans

    def __init__(
        self,
        json_path: str = "json_finance/bdd_zb_prix_juste.json",
        ratios_path: str = "json_finance/ratios_standard.json",
        rendement_cible: float = 0.15,
        horizon_croissance: int = 10,
        horizon_ratio: int = 5,
        taux_sans_risque: float = 0.03,
        prime_risque: float = 0.06,
        peg_cible: float = 1.0
    ):
        """
        Initialise le calculateur.

        Args:
            json_path: Chemin vers la base de donnees financieres
            ratios_path: Chemin vers le fichier de ponderations
            rendement_cible: Rendement annuel cible (defaut 15%)
            horizon_croissance: Nombre d'annees pour calcul croissance
            horizon_ratio: Nombre d'annees pour calcul ratios
            taux_sans_risque: Taux sans risque pour CAPM
            prime_risque: Prime de risque marche pour CAPM
            peg_cible: PEG cible pour methode PEG
        """
        self.rendement_cible = rendement_cible
        self.horizon_croissance = horizon_croissance
        self.horizon_ratio = horizon_ratio
        self.taux_sans_risque = taux_sans_risque
        self.prime_risque = prime_risque
        self.peg_cible = peg_cible

        self.data = self._charger_json(json_path)
        self.ratios = self._charger_ratios(ratios_path)
        self.resultats: Dict[str, Dict] = {}

    # ========== CHARGEMENT ==========

    def _charger_json(self, path: str) -> Dict:
        """Charge la base de donnees JSON."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _charger_ratios(self, path: str) -> Dict[str, Dict]:
        """Charge et indexe les ponderations par cle secteur_taille."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Indexer par cle pour acces rapide
        return {item["cle"]: item for item in data["data"]}

    # ========== UTILITAIRES ==========

    def _get_taille(self, capitalisation: float) -> str:
        """Determine la taille selon la capitalisation."""
        if capitalisation >= 10_000_000_000:  # >= 10 Md
            return "Large"
        elif capitalisation >= 2_000_000_000:  # >= 2 Md
            return "Mid"
        elif capitalisation >= 300_000_000:    # >= 300 M
            return "Small"
        else:
            return "Micro"

    def _get_ponderations(self, secteur: str, taille: str) -> Dict:
        """Recupere les ponderations pour un secteur et une taille."""
        cle = f"{secteur}_{taille}"

        # Essayer la cle exacte
        if cle in self.ratios:
            return self.ratios[cle]

        # Fallback: secteur avec taille Default
        for t in ["Large", "Mid", "Small", "Micro"]:
            cle_fallback = f"{secteur}_{t}"
            if cle_fallback in self.ratios:
                return self.ratios[cle_fallback]

        # Fallback ultime: Default
        cle_default = f"Default_{taille}"
        if cle_default in self.ratios:
            return self.ratios[cle_default]

        return self.ratios.get("Default_Large", {
            "ratio_benefice": 0.25,
            "ratio_fcf": 0.35,
            "ratio_ventes": 0.20,
            "ratio_ebitda": 0.15,
            "ratio_book_value": 0.05,
            "facteur_decote": 1.0
        })

    def _get_dernieres_annees(self, valeurs_dict: Dict[str, Any], n: int) -> Dict[str, Any]:
        """Retourne les n dernieres annees de donnees."""
        annees = sorted([k for k in valeurs_dict.keys() if k.isdigit()], reverse=True)
        return {a: valeurs_dict[a] for a in annees[:n] if a in valeurs_dict}

    def _get_derniere_valeur(self, valeurs_dict: Dict[str, Any]) -> Tuple[Optional[str], Optional[float]]:
        """Retourne la derniere annee et valeur disponible."""
        annees = sorted([k for k in valeurs_dict.keys() if k.isdigit()], reverse=True)
        for a in annees:
            v = valeurs_dict.get(a)
            if v is not None and v != 0:
                return a, v
        return None, None

    # ========== VALIDATION ==========

    def _valider_ratio(self, valeur: float, type_ratio: str) -> bool:
        """Verifie si un ratio est dans les limites acceptables."""
        if valeur is None:
            return False

        limites = self.LIMITES_RATIOS.get(type_ratio)
        if limites is None:
            return True

        min_val, max_val = limites
        return min_val < valeur <= max_val

    def _valider_croissance(self, valeur: float) -> bool:
        """Verifie si une croissance est dans les limites acceptables."""
        if valeur is None:
            return False
        return self.LIMITE_CROISSANCE_MIN <= valeur <= self.LIMITE_CROISSANCE_MAX

    def _ajuster_cagr(self, cagr: float) -> Optional[float]:
        """
        Ajuste le CAGR selon les regles:
        - Plafonner a 30% si > 50%
        - Exclure (None) si < -20%
        """
        if cagr is None:
            return None

        if cagr < self.CAGR_EXCLUSION:
            return None

        if cagr > 0.50:
            return self.CAGR_PLAFOND

        return cagr

    def _coefficient_variation(self, valeurs: List[float]) -> float:
        """Calcule le coefficient de variation."""
        if len(valeurs) < 2:
            return 0
        moyenne = np.mean(valeurs)
        if moyenne == 0:
            return float('inf')
        return np.std(valeurs) / abs(moyenne)

    # ========== CALCULS CROISSANCE ==========

    def _calculer_croissances(self, valeurs_dict: Dict[str, Any]) -> List[float]:
        """
        Calcule les croissances annuelles.
        Retourne une liste de croissances valides.
        """
        annees = sorted([k for k in valeurs_dict.keys() if k.isdigit()])
        croissances = []

        for i in range(1, len(annees)):
            v_prev = valeurs_dict.get(annees[i-1])
            v_curr = valeurs_dict.get(annees[i])

            if v_prev is not None and v_curr is not None and v_prev != 0:
                croissance = (v_curr / v_prev) - 1
                if self._valider_croissance(croissance):
                    croissances.append(croissance)

        return croissances

    def _calculer_cagr_median(self, valeurs_dict: Dict[str, Any]) -> Optional[float]:
        """
        Calcule le CAGR median a partir des croissances annuelles.
        Retourne None si pas assez de donnees.
        """
        croissances = self._calculer_croissances(valeurs_dict)

        if len(croissances) < self.MIN_CROISSANCES:
            return None

        cagr = np.median(croissances)
        return self._ajuster_cagr(cagr)

    # ========== 5 METHODES DE BASE ==========

    def _prix_bpa(self, entreprise: Dict) -> Dict:
        """
        Methode 1: Prix base sur le BPA.
        Prix_BPA = BPA_projete * PER_median
        """
        result = {"prix": None, "cagr": None, "ratio": None, "exclu": False, "raison": None}

        try:
            bpa_data = entreprise["compte_de_resultat"].get("BPA de base normalise", {})
            per_data = entreprise["valorisation"].get("PER", {})

            # Derniere valeur BPA
            _, bpa_dernier = self._get_derniere_valeur(bpa_data)
            if bpa_dernier is None or bpa_dernier <= 0:
                result["exclu"] = True
                result["raison"] = "BPA invalide"
                return result

            # CAGR median du BPA
            cagr = self._calculer_cagr_median(bpa_data)
            if cagr is None:
                result["exclu"] = True
                result["raison"] = "CAGR invalide"
                return result

            result["cagr"] = cagr

            # PER median sur 5 ans
            per_recents = self._get_dernieres_annees(per_data, self.horizon_ratio)
            per_valides = [v for v in per_recents.values()
                          if self._valider_ratio(v, "PER")]

            if len(per_valides) < self.MIN_RATIOS:
                result["exclu"] = True
                result["raison"] = f"PER insuffisants ({len(per_valides)}/{self.MIN_RATIOS})"
                return result

            per_median = np.median(per_valides)
            result["ratio"] = per_median

            # Calcul prix
            bpa_projete = bpa_dernier * (1 + cagr)
            result["prix"] = bpa_projete * per_median

        except Exception as e:
            result["exclu"] = True
            result["raison"] = str(e)

        return result

    def _prix_fcf(self, entreprise: Dict) -> Dict:
        """
        Methode 2: Prix base sur le FCF.
        Prix_FCF = FCF_projete / (FCF_Yield_median / 100)
        """
        result = {"prix": None, "cagr": None, "ratio": None, "exclu": False, "raison": None}

        try:
            fcfe_data = entreprise["flux_de_tresorerie"].get(
                "Flux de tresorerie libre pour les actionnaires FCFE", {})
            yield_data = entreprise["valorisation"].get("FCF Yield", {})
            actions = entreprise["donnees_actuelles"].get("actions_circulation", 0)

            if actions <= 0:
                result["exclu"] = True
                result["raison"] = "Actions invalides"
                return result

            # Calculer FCF par action
            fcf_par_action = {}
            for annee, fcfe in fcfe_data.items():
                if fcfe is not None:
                    fcf_par_action[annee] = fcfe / actions

            # Derniere valeur
            _, fcf_dernier = self._get_derniere_valeur(fcf_par_action)
            if fcf_dernier is None or fcf_dernier <= 0:
                result["exclu"] = True
                result["raison"] = "FCF invalide"
                return result

            # CAGR median
            cagr = self._calculer_cagr_median(fcf_par_action)
            if cagr is None:
                result["exclu"] = True
                result["raison"] = "CAGR invalide"
                return result

            result["cagr"] = cagr

            # FCF Yield median sur 5 ans
            yield_recents = self._get_dernieres_annees(yield_data, self.horizon_ratio)
            yield_valides = [v for v in yield_recents.values()
                           if self._valider_ratio(v, "FCF_Yield")]

            if len(yield_valides) < self.MIN_RATIOS:
                result["exclu"] = True
                result["raison"] = f"FCF Yield insuffisants ({len(yield_valides)}/{self.MIN_RATIOS})"
                return result

            yield_median = np.median(yield_valides)
            result["ratio"] = yield_median

            # Calcul prix
            fcf_projete = fcf_dernier * (1 + cagr)
            result["prix"] = fcf_projete / (yield_median / 100)

        except Exception as e:
            result["exclu"] = True
            result["raison"] = str(e)

        return result

    def _prix_ventes(self, entreprise: Dict) -> Dict:
        """
        Methode 3: Prix base sur les ventes.
        Prix_Ventes = CA_projete * PS_median
        """
        result = {"prix": None, "cagr": None, "ratio": None, "exclu": False, "raison": None}

        try:
            ca_data = entreprise["compte_de_resultat"].get("Total Chiffre d'affaires", {})
            actions = entreprise["donnees_actuelles"].get("actions_circulation", 0)
            prix_actuel = entreprise["donnees_actuelles"].get("prix_actuel", 0)

            if actions <= 0:
                result["exclu"] = True
                result["raison"] = "Actions invalides"
                return result

            # Calculer CA par action
            ca_par_action = {}
            for annee, ca in ca_data.items():
                if ca is not None:
                    ca_par_action[annee] = ca / actions

            # Derniere valeur
            _, ca_dernier = self._get_derniere_valeur(ca_par_action)
            if ca_dernier is None or ca_dernier <= 0:
                result["exclu"] = True
                result["raison"] = "CA invalide"
                return result

            # CAGR median
            cagr = self._calculer_cagr_median(ca_par_action)
            if cagr is None:
                result["exclu"] = True
                result["raison"] = "CAGR invalide"
                return result

            result["cagr"] = cagr

            # Calculer P/S historique
            # P/S = Prix / (CA / Actions) = Prix * Actions / CA
            ps_historique = {}
            annees_recentes = sorted([k for k in ca_data.keys() if k.isdigit()], reverse=True)[:self.horizon_ratio]

            for annee in annees_recentes:
                ca = ca_data.get(annee)
                if ca is not None and ca > 0:
                    # Utiliser capitalisation / CA comme proxy
                    cap = entreprise["donnees_actuelles"].get("capitalisation", 0)
                    if cap > 0:
                        ps = cap / ca
                        ps_historique[annee] = ps

            ps_valides = [v for v in ps_historique.values()
                        if self._valider_ratio(v, "PS")]

            if len(ps_valides) < self.MIN_RATIOS:
                result["exclu"] = True
                result["raison"] = f"P/S insuffisants ({len(ps_valides)}/{self.MIN_RATIOS})"
                return result

            ps_median = np.median(ps_valides)
            result["ratio"] = ps_median

            # Calcul prix
            ca_projete = ca_dernier * (1 + cagr)
            result["prix"] = ca_projete * ps_median

        except Exception as e:
            result["exclu"] = True
            result["raison"] = str(e)

        return result

    def _prix_ebitda(self, entreprise: Dict) -> Dict:
        """
        Methode 4: Prix base sur l'EBITDA.
        EV_projete = EBITDA_projete * Actions * EV_EBITDA_median
        Prix_EBITDA = (EV_projete - Dette_nette) / Actions
        """
        result = {"prix": None, "cagr": None, "ratio": None, "exclu": False, "raison": None}

        try:
            ebitda_data = entreprise["compte_de_resultat"].get("EBITDA", {})
            ev_ebitda_data = entreprise["valorisation"].get("Valeur Entreprise / EBITDA", {})
            actions = entreprise["donnees_actuelles"].get("actions_circulation", 0)

            if actions <= 0:
                result["exclu"] = True
                result["raison"] = "Actions invalides"
                return result

            # Calculer EBITDA par action
            ebitda_par_action = {}
            for annee, ebitda in ebitda_data.items():
                if ebitda is not None:
                    ebitda_par_action[annee] = ebitda / actions

            # Derniere valeur
            annee_derniere, ebitda_dernier = self._get_derniere_valeur(ebitda_par_action)
            if ebitda_dernier is None or ebitda_dernier <= 0:
                result["exclu"] = True
                result["raison"] = "EBITDA invalide"
                return result

            # CAGR median
            cagr = self._calculer_cagr_median(ebitda_par_action)
            if cagr is None:
                result["exclu"] = True
                result["raison"] = "CAGR invalide"
                return result

            result["cagr"] = cagr

            # EV/EBITDA median sur 5 ans
            ev_ebitda_recents = self._get_dernieres_annees(ev_ebitda_data, self.horizon_ratio)
            ev_ebitda_valides = [v for v in ev_ebitda_recents.values()
                                if self._valider_ratio(v, "EV_EBITDA")]

            if len(ev_ebitda_valides) < self.MIN_RATIOS:
                result["exclu"] = True
                result["raison"] = f"EV/EBITDA insuffisants ({len(ev_ebitda_valides)}/{self.MIN_RATIOS})"
                return result

            ev_ebitda_median = np.median(ev_ebitda_valides)
            result["ratio"] = ev_ebitda_median

            # Dette nette (derniere valeur)
            dette_data = entreprise["bilan"].get("Dette nette", {})
            _, dette_nette = self._get_derniere_valeur(dette_data)
            if dette_nette is None:
                dette_nette = 0

            # Calcul prix
            ebitda_projete = ebitda_dernier * (1 + cagr)
            ev_projete = ebitda_projete * actions * ev_ebitda_median
            result["prix"] = (ev_projete - dette_nette) / actions

        except Exception as e:
            result["exclu"] = True
            result["raison"] = str(e)

        return result

    def _prix_book_value(self, entreprise: Dict) -> Dict:
        """
        Methode 5: Prix base sur la Book Value.
        Prix_BookValue = BV_projete * PB_median
        """
        result = {"prix": None, "cagr": None, "ratio": None, "exclu": False, "raison": None}

        try:
            bv_data = entreprise["bilan"].get("Total des capitaux propres", {})
            actions = entreprise["donnees_actuelles"].get("actions_circulation", 0)

            if actions <= 0:
                result["exclu"] = True
                result["raison"] = "Actions invalides"
                return result

            # Calculer BV par action
            bv_par_action = {}
            for annee, bv in bv_data.items():
                if bv is not None:
                    bv_par_action[annee] = bv / actions

            # Derniere valeur
            _, bv_dernier = self._get_derniere_valeur(bv_par_action)
            if bv_dernier is None or bv_dernier <= 0:
                result["exclu"] = True
                result["raison"] = "BV invalide"
                return result

            # CAGR median
            cagr = self._calculer_cagr_median(bv_par_action)
            if cagr is None:
                result["exclu"] = True
                result["raison"] = "CAGR invalide"
                return result

            result["cagr"] = cagr

            # Calculer P/B historique
            pb_historique = {}
            annees_recentes = sorted([k for k in bv_data.keys() if k.isdigit()], reverse=True)[:self.horizon_ratio]

            for annee in annees_recentes:
                bv = bv_data.get(annee)
                if bv is not None and bv > 0:
                    cap = entreprise["donnees_actuelles"].get("capitalisation", 0)
                    if cap > 0:
                        pb = cap / bv
                        pb_historique[annee] = pb

            pb_valides = [v for v in pb_historique.values()
                        if self._valider_ratio(v, "PB")]

            if len(pb_valides) < self.MIN_RATIOS:
                result["exclu"] = True
                result["raison"] = f"P/B insuffisants ({len(pb_valides)}/{self.MIN_RATIOS})"
                return result

            pb_median = np.median(pb_valides)
            result["ratio"] = pb_median

            # Calcul prix
            bv_projete = bv_dernier * (1 + cagr)
            result["prix"] = bv_projete * pb_median

        except Exception as e:
            result["exclu"] = True
            result["raison"] = str(e)

        return result

    # ========== PRIX PONDERE ==========

    def _calculer_prix_pondere(self, nom_entreprise: str) -> Dict:
        """
        Calcule le prix pondere des 5 methodes de base.
        Redistribue les poids si une methode est exclue.
        """
        entreprise = self.data[nom_entreprise]
        secteur = entreprise["infos"].get("secteur", "Default")
        cap = entreprise["donnees_actuelles"].get("capitalisation", 0)
        taille = self._get_taille(cap)

        # Recuperer ponderations
        pond = self._get_ponderations(secteur, taille)

        # Calculer chaque methode
        methodes = {
            "benefice": (self._prix_bpa(entreprise), pond.get("ratio_benefice", 0)),
            "fcf": (self._prix_fcf(entreprise), pond.get("ratio_fcf", 0)),
            "ventes": (self._prix_ventes(entreprise), pond.get("ratio_ventes", 0)),
            "ebitda": (self._prix_ebitda(entreprise), pond.get("ratio_ebitda", 0)),
            "book_value": (self._prix_book_value(entreprise), pond.get("ratio_book_value", 0))
        }

        # Filtrer methodes valides avec poids > 0
        methodes_valides = {}
        for nom, (result, poids) in methodes.items():
            if result["prix"] is not None and poids > 0:
                methodes_valides[nom] = (result, poids)

        if not methodes_valides:
            return {
                "prix_pondere": None,
                "prix_pondere_brut": None,
                "facteur_decote": pond.get("facteur_decote", 1.0),
                "methodes": methodes,
                "poids_normalises": {},
                "secteur": secteur,
                "taille": taille
            }

        # Redistribuer les poids
        somme_poids = sum(p for _, p in methodes_valides.values())
        poids_normalises = {k: p / somme_poids for k, (_, p) in methodes_valides.items()}

        # Calculer prix pondere brut
        prix_pondere_brut = sum(
            methodes_valides[k][0]["prix"] * poids_normalises[k]
            for k in poids_normalises
        )

        # Appliquer facteur de decote
        facteur_decote = pond.get("facteur_decote", 1.0)
        prix_pondere = prix_pondere_brut * facteur_decote

        return {
            "prix_pondere": prix_pondere,
            "prix_pondere_brut": prix_pondere_brut,
            "facteur_decote": facteur_decote,
            "methodes": methodes,
            "poids_normalises": poids_normalises,
            "secteur": secteur,
            "taille": taille
        }

    # ========== 3 METHODES COMPLEMENTAIRES ==========

    def _prix_peg(self, entreprise: Dict, cagr_bpa: Optional[float]) -> Dict:
        """
        Methode 6: Prix base sur le PEG.
        PER_juste = PEG_cible * Croissance_BPA_pct
        Prix_PEG = BPA_dernier * PER_juste
        """
        result = {"prix": None, "cagr": cagr_bpa, "peg": self.peg_cible, "exclu": False, "raison": None}

        try:
            if cagr_bpa is None or cagr_bpa <= 0:
                result["exclu"] = True
                result["raison"] = "CAGR BPA <= 0"
                return result

            bpa_data = entreprise["compte_de_resultat"].get("BPA de base normalise", {})
            _, bpa_dernier = self._get_derniere_valeur(bpa_data)

            if bpa_dernier is None or bpa_dernier <= 0:
                result["exclu"] = True
                result["raison"] = "BPA invalide"
                return result

            # PER juste = PEG_cible * Croissance_BPA_pct
            croissance_pct = cagr_bpa * 100
            per_juste = self.peg_cible * croissance_pct

            result["prix"] = bpa_dernier * per_juste

        except Exception as e:
            result["exclu"] = True
            result["raison"] = str(e)

        return result

    def _prix_gordon(self, entreprise: Dict) -> Dict:
        """
        Methode 7: Prix Gordon (DDM).
        Prix_Gordon = Dividende * (1 + g) / (r - g)
        """
        result = {"prix": None, "croissance_div": None, "exclu": False, "raison": None}

        try:
            div_data = entreprise["compte_de_resultat"].get("Dividende par action", {})

            # Derniere valeur dividende
            _, div_dernier = self._get_derniere_valeur(div_data)

            if div_dernier is None or div_dernier <= 0:
                result["exclu"] = True
                result["raison"] = "Dividende = 0"
                return result

            # Croissance dividende
            croissances_div = self._calculer_croissances(div_data)

            if len(croissances_div) < 3:
                result["exclu"] = True
                result["raison"] = "Historique dividende insuffisant"
                return result

            g = np.median(croissances_div)
            result["croissance_div"] = g

            r = self.rendement_cible

            # Exclusions
            if g >= r:
                result["exclu"] = True
                result["raison"] = "g >= r"
                return result

            if g < 0:
                result["exclu"] = True
                result["raison"] = "g < 0"
                return result

            # Calcul prix Gordon
            result["prix"] = div_dernier * (1 + g) / (r - g)

        except Exception as e:
            result["exclu"] = True
            result["raison"] = str(e)

        return result

    def _prix_beta(self, entreprise: Dict, prix_pondere: Optional[float]) -> Dict:
        """
        Methode 8: Prix ajuste Beta (CAPM).
        Rendement_ajuste = Taux_sans_risque + Beta * Prime_risque
        Prix_Beta = Prix_pondere / (1 + Rendement_ajuste)
        """
        result = {"prix": None, "beta": None, "rendement_ajuste": None, "exclu": False, "raison": None}

        try:
            if prix_pondere is None:
                result["exclu"] = True
                result["raison"] = "Prix pondere invalide"
                return result

            yahoo_data = entreprise.get("yahoo_finance", {})
            beta = yahoo_data.get("beta")

            if beta is None:
                result["exclu"] = True
                result["raison"] = "Beta non disponible"
                return result

            result["beta"] = beta

            # Rendement ajuste via CAPM
            rendement_ajuste = self.taux_sans_risque + beta * self.prime_risque
            result["rendement_ajuste"] = rendement_ajuste

            # Prix ajuste
            result["prix"] = prix_pondere / (1 + rendement_ajuste)

        except Exception as e:
            result["exclu"] = True
            result["raison"] = str(e)

        return result

    # ========== MOYENNES ==========

    def _moyenne_arithmetique(self, valeurs: List[float]) -> Optional[float]:
        """Moyenne simple."""
        if not valeurs:
            return None
        return float(np.mean(valeurs))

    def _moyenne_harmonique(self, valeurs: List[float]) -> Optional[float]:
        """Moyenne harmonique - favorise les valeurs basses."""
        valeurs_pos = [v for v in valeurs if v > 0]
        if not valeurs_pos:
            return None
        return len(valeurs_pos) / sum(1/v for v in valeurs_pos)

    def _moyenne_geometrique(self, valeurs: List[float]) -> Optional[float]:
        """Moyenne geometrique - equilibree."""
        valeurs_pos = [v for v in valeurs if v > 0]
        if not valeurs_pos:
            return None
        return float(np.exp(np.mean(np.log(valeurs_pos))))

    def _ema(self, valeurs: List[float], alpha: float = 0.3) -> Optional[float]:
        """Exponential Moving Average - poids recents plus forts."""
        if not valeurs:
            return None
        result = valeurs[0]
        for v in valeurs[1:]:
            result = alpha * v + (1 - alpha) * result
        return result

    def _dema(self, valeurs: List[float], alpha: float = 0.3) -> Optional[float]:
        """Double EMA - plus reactif."""
        if not valeurs:
            return None

        # Premiere EMA
        ema1 = valeurs[0]
        ema_series = [ema1]
        for v in valeurs[1:]:
            ema1 = alpha * v + (1 - alpha) * ema1
            ema_series.append(ema1)

        # Deuxieme EMA sur la serie EMA
        ema2 = ema_series[0]
        for v in ema_series[1:]:
            ema2 = alpha * v + (1 - alpha) * ema2

        return 2 * ema1 - ema2

    def _smma(self, valeurs: List[float]) -> Optional[float]:
        """Smoothed Moving Average."""
        if not valeurs:
            return None
        n = len(valeurs)
        result = np.mean(valeurs)
        return result

    # ========== SYNTHESE ==========

    def _calculer_prix_final(self, nom_entreprise: str) -> Dict:
        """
        Calcule le prix final en combinant toutes les methodes
        et en appliquant les 6 types de moyennes.
        """
        entreprise = self.data[nom_entreprise]

        # 1. Prix pondere des methodes de base
        result_pondere = self._calculer_prix_pondere(nom_entreprise)
        prix_pondere = result_pondere["prix_pondere"]

        # Recuperer CAGR BPA pour methode PEG
        cagr_bpa = None
        methode_bpa = result_pondere["methodes"].get("benefice", ({}, 0))[0]
        if methode_bpa and methode_bpa.get("cagr"):
            cagr_bpa = methode_bpa["cagr"]

        # 2. Methodes complementaires
        result_peg = self._prix_peg(entreprise, cagr_bpa)
        result_gordon = self._prix_gordon(entreprise)
        result_beta = self._prix_beta(entreprise, prix_pondere)

        # 3. Collecter tous les prix valides
        prix_valides = []

        if prix_pondere is not None:
            prix_valides.append(prix_pondere)

        if result_peg["prix"] is not None:
            prix_valides.append(result_peg["prix"])

        if result_gordon["prix"] is not None:
            prix_valides.append(result_gordon["prix"])

        if result_beta["prix"] is not None:
            prix_valides.append(result_beta["prix"])

        # 4. Calculer les 6 moyennes
        if prix_valides:
            moyennes = {
                "arithmetique": self._moyenne_arithmetique(prix_valides),
                "harmonique": self._moyenne_harmonique(prix_valides),
                "geometrique": self._moyenne_geometrique(prix_valides),
                "ema": self._ema(prix_valides),
                "dema": self._dema(prix_valides),
                "smma": self._smma(prix_valides)
            }

            # Prix juste = mediane des moyennes
            moyennes_valides = [v for v in moyennes.values() if v is not None]
            prix_juste = float(np.median(moyennes_valides)) if moyennes_valides else None
        else:
            moyennes = {
                "arithmetique": None,
                "harmonique": None,
                "geometrique": None,
                "ema": None,
                "dema": None,
                "smma": None
            }
            prix_juste = None

        # 5. Prix d'achat
        prix_achat = prix_juste / (1 + self.rendement_cible) if prix_juste else None

        # 6. Informations supplementaires
        prix_actuel = entreprise["donnees_actuelles"].get("prix_actuel", 0)
        devise = entreprise["donnees_actuelles"].get("devise", "EUR")

        ecart = None
        if prix_achat and prix_actuel:
            ecart = (prix_achat - prix_actuel) / prix_actuel

        return {
            "nom": nom_entreprise,
            "ticker": entreprise["infos"].get("ticker", ""),
            "secteur": result_pondere["secteur"],
            "taille": result_pondere["taille"],
            "devise": devise,
            "prix_actuel": prix_actuel,
            "52_week_high": entreprise.get("yahoo_finance", {}).get("52_week_high"),
            "52_week_low": entreprise.get("yahoo_finance", {}).get("52_week_low"),

            # Methodes de base
            "methodes_base": result_pondere["methodes"],
            "poids_normalises": result_pondere["poids_normalises"],
            "prix_pondere_brut": result_pondere["prix_pondere_brut"],
            "facteur_decote": result_pondere["facteur_decote"],
            "prix_pondere": prix_pondere,

            # Methodes complementaires
            "prix_peg": result_peg,
            "prix_gordon": result_gordon,
            "prix_beta": result_beta,

            # Prix collectes
            "prix_valides": prix_valides,

            # Moyennes
            "moyennes": moyennes,

            # Resultat final
            "prix_juste": prix_juste,
            "prix_achat": prix_achat,
            "ecart": ecart
        }

    # ========== INTERFACE PUBLIQUE ==========

    def calculer(self, nom_entreprise: str = None) -> Dict:
        """
        Calcule le prix juste pour une ou toutes les entreprises.

        Args:
            nom_entreprise: Nom de l'entreprise ou None pour toutes

        Returns:
            Dictionnaire des resultats
        """
        if nom_entreprise:
            if nom_entreprise not in self.data:
                raise ValueError(f"Entreprise '{nom_entreprise}' non trouvee")
            self.resultats[nom_entreprise] = self._calculer_prix_final(nom_entreprise)
        else:
            for nom in self.data.keys():
                self.resultats[nom] = self._calculer_prix_final(nom)

        return self.resultats

    def afficher(self):
        """Affiche le resume simple des resultats."""
        if not self.resultats:
            print("Aucun resultat. Executez calculer() d'abord.")
            return

        n = len(self.resultats)
        print(f"\nPRIX JUSTE - {n} entreprise(s)")
        print("=" * 66)
        print(f"{'':40} {'Actuel':>10} {'Achat':>10} {'Ecart':>8}")

        for nom, r in self.resultats.items():
            devise = r["devise"]
            symbole = "€" if devise == "EUR" else "$"

            prix_actuel = r["prix_actuel"]
            prix_achat = r["prix_achat"]
            ecart = r["ecart"]

            # Formatage
            actuel_str = f"{prix_actuel:.2f} {symbole}" if prix_actuel else "N/A"
            achat_str = f"{prix_achat:.2f} {symbole}" if prix_achat else "N/A"

            if ecart is not None:
                ecart_pct = ecart * 100
                if ecart > 0.10:
                    indicateur = "🟢"
                elif ecart < -0.10:
                    indicateur = "🔴"
                else:
                    indicateur = "🟠"
                ecart_str = f"{ecart_pct:+.1f}%  {indicateur}"
            else:
                ecart_str = "N/A"

            # Tronquer le nom si trop long
            nom_affiche = nom[:38] + ".." if len(nom) > 40 else nom

            print(f"{nom_affiche:40} {actuel_str:>10} {achat_str:>10} {ecart_str:>8}")

        print("=" * 66)
        print("🟢 Sous-evalue (>10%)  🟠 Neutre (±10%)  🔴 Surevalue (<-10%)")

    def detail(self, nom_entreprise: str):
        """Affiche le detail complet d'une entreprise."""
        if nom_entreprise not in self.resultats:
            # Calculer si pas encore fait
            self.calculer(nom_entreprise)

        r = self.resultats[nom_entreprise]
        devise = r["devise"]
        symbole = "€" if devise == "EUR" else "$"

        print()
        print("=" * 66)
        print(f"DETAIL : {nom_entreprise} ({r['ticker']})")
        print("=" * 66)

        # Infos generales
        low = r.get("52_week_low", "N/A")
        high = r.get("52_week_high", "N/A")
        low_str = f"{low:.2f}" if isinstance(low, (int, float)) else "N/A"
        high_str = f"{high:.2f}" if isinstance(high, (int, float)) else "N/A"

        print(f"Secteur: {r['secteur']} | Taille: {r['taille']} | Devise: {devise}")
        print(f"Prix actuel: {r['prix_actuel']:.2f} {symbole} | 52W: {low_str} - {high_str} {symbole}")

        # Methodes de base
        print()
        print("METHODES DE BASE (ponderees)")
        print("-" * 66)

        noms_methodes = {
            "benefice": "BPA",
            "fcf": "FCF",
            "ventes": "Ventes",
            "ebitda": "EBITDA",
            "book_value": "Book Value"
        }

        noms_ratios = {
            "benefice": "PER",
            "fcf": "Yield",
            "ventes": "P/S",
            "ebitda": "EV/EBITDA",
            "book_value": "P/B"
        }

        for cle, nom_m in noms_methodes.items():
            result, _ = r["methodes_base"].get(cle, ({}, 0))
            poids = r["poids_normalises"].get(cle, 0) * 100

            if result.get("exclu") or result.get("prix") is None:
                raison = result.get("raison", "ratio = 0")
                print(f"{nom_m:10} : Exclu ({raison}){' ':20} Poids: {poids:.0f}%")
            else:
                prix = result["prix"]
                cagr = result.get("cagr", 0) * 100 if result.get("cagr") else 0
                ratio = result.get("ratio", 0)
                ratio_nom = noms_ratios[cle]
                print(f"{nom_m:10} : {prix:.2f} {symbole} (CAGR: {cagr:.1f}%, {ratio_nom}: {ratio:.1f}){' ':5} Poids: {poids:.0f}%")

        print("-" * 66)

        if r["prix_pondere_brut"]:
            print(f"Prix pondere brut  : {r['prix_pondere_brut']:.2f} {symbole}")
        print(f"Facteur decote     : x {r['facteur_decote']:.2f}")
        if r["prix_pondere"]:
            print(f"Prix pondere       : {r['prix_pondere']:.2f} {symbole}")

        # Methodes complementaires
        print()
        print("METHODES COMPLEMENTAIRES")
        print("-" * 66)

        # PEG
        peg = r["prix_peg"]
        if peg.get("exclu"):
            print(f"PEG        : Exclu ({peg.get('raison', 'N/A')})")
        else:
            cagr_pct = peg.get("cagr", 0) * 100 if peg.get("cagr") else 0
            print(f"PEG        : {peg['prix']:.2f} {symbole} (CAGR: {cagr_pct:.1f}%, PEG: {peg.get('peg', 1.0)})")

        # Gordon
        gordon = r["prix_gordon"]
        if gordon.get("exclu"):
            print(f"Gordon     : Exclu ({gordon.get('raison', 'N/A')})")
        else:
            g_pct = gordon.get("croissance_div", 0) * 100 if gordon.get("croissance_div") else 0
            print(f"Gordon     : {gordon['prix']:.2f} {symbole} (g: {g_pct:.1f}%)")

        # Beta
        beta = r["prix_beta"]
        if beta.get("exclu"):
            print(f"Beta       : Exclu ({beta.get('raison', 'N/A')})")
        else:
            rend_pct = beta.get("rendement_ajuste", 0) * 100 if beta.get("rendement_ajuste") else 0
            print(f"Beta       : {beta['prix']:.2f} {symbole} (Beta: {beta.get('beta', 0):.2f}, Rend: {rend_pct:.2f}%)")

        # Synthese moyennes
        print()
        print("SYNTHESE (6 moyennes)")
        print("-" * 66)

        moyennes = r["moyennes"]
        for nom_m, val in moyennes.items():
            val_str = f"{val:.2f} {symbole}" if val else "N/A"
            print(f"{nom_m.capitalize():14} : {val_str}")

        # Resultat final
        print()
        print("RESULTAT FINAL")
        print("=" * 66)

        if r["prix_juste"]:
            print(f"Prix juste (mediane)  : {r['prix_juste']:.2f} {symbole}")
        print(f"Rendement cible       : {self.rendement_cible * 100:.0f}%")

        if r["prix_achat"]:
            print(f"PRIX D'ACHAT          : {r['prix_achat']:.2f} {symbole}")

        print("-" * 66)
        print(f"Prix actuel           : {r['prix_actuel']:.2f} {symbole}")

        if r["ecart"] is not None:
            ecart_pct = r["ecart"] * 100
            if ecart_pct > 10:
                statut = "SOUS-EVALUE"
                reco = "🟢 ACHETER"
            elif ecart_pct < -10:
                statut = "SUREVALUE"
                reco = "🔴 ATTENDRE"
            else:
                statut = "NEUTRE"
                reco = "🟠 SURVEILLER"

            print(f"Ecart                 : {ecart_pct:+.1f}% ({statut})")
            print(f"Recommandation        : {reco}")

        print("=" * 66)

    def exporter_json(self, output_path: str = "resultats_prix_juste.json"):
        """Exporte les resultats en JSON."""
        if not self.resultats:
            print("Aucun resultat. Executez calculer() d'abord.")
            return

        # Preparer donnees exportables (convertir numpy types)
        def convert(obj):
            if isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert(i) for i in obj]
            elif isinstance(obj, tuple):
                return tuple(convert(i) for i in obj)
            return obj

        export_data = convert(self.resultats)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        print(f"Resultats exportes vers: {output_path}")


if __name__ == "__main__":
    # Initialisation
    calc = PrixJuste()

    # Calculer pour toutes les entreprises
    calc.calculer()

    # Afficher resume
    calc.afficher()

    # Pour voir le detail d'une entreprise :
    # calc.detail("Schneider Electric S.E.")
