"""
Gestionnaire d'actions pour créer et maintenir une base de données d'actions boursières.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yfinance as yf

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes
SCRIPT_DIR = Path(__file__).parent
JSON_DIR = SCRIPT_DIR / "json_finance"
CONFIG_FILE = JSON_DIR / "suffixe.json"
JSON_FILE = JSON_DIR / "name_action.json"

# Commandes acceptées pour continuer
POSITIVE_RESPONSES = {'oui', 'o', 'yes', 'y'}
QUIT_COMMANDS = {'q', 'quit', 'exit', 'quitter'}


class StockDatabase:
    """Gère la base de données d'actions."""

    def __init__(self, json_file: Path):
        self.json_file = json_file
        self._ensure_directory()

    def _ensure_directory(self) -> None:
        """Crée le répertoire si il n'existe pas."""
        self.json_file.parent.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Répertoire vérifié: {self.json_file.parent}")

    def load_stocks(self) -> List[Dict]:
        """Charge la liste des actions depuis le fichier JSON."""
        if not self.json_file.exists():
            logger.info("Création d'un nouveau fichier JSON")
            return []

        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('stocks', [])
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de lecture du JSON: {e}")
            return []
        except Exception as e:
            logger.error(f"Erreur inattendue: {e}")
            return []

    def save_stocks(self, stocks: List[Dict]) -> bool:
        """Sauvegarde la liste des actions dans le fichier JSON."""
        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump({'stocks': stocks}, f, indent=2, ensure_ascii=False)
            logger.info(f"Base de données sauvegardée ({len(stocks)} actions)")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return False

    def add_stock(self, stock_info: Dict) -> Tuple[bool, str]:
        """
        Ajoute une action à la base de données.

        Returns:
            Tuple[bool, str]: (succès, message)
        """
        stocks = self.load_stocks()

        # Vérifier les doublons
        ticker = stock_info['ticker']
        if any(s['ticker'] == ticker for s in stocks):
            return False, f"L'action {ticker} existe déjà dans la base"

        stocks.append(stock_info)

        if self.save_stocks(stocks):
            return True, f"Action {ticker} ajoutée (Total: {len(stocks)})"
        else:
            return False, "Erreur lors de la sauvegarde"

    def ticker_exists(self, ticker: str) -> bool:
        """Vérifie si un ticker existe déjà."""
        stocks = self.load_stocks()
        return any(s['ticker'] == ticker for s in stocks)


class MarketManager:
    """Gère les marchés et leurs suffixes."""

    def __init__(self, config_file: Path):
        self.config_file = config_file
        self._markets: Optional[Dict[str, str]] = None

    @property
    def markets(self) -> Dict[str, str]:
        """Charge et met en cache la liste des marchés."""
        if self._markets is None:
            self._markets = self._load_markets()
        return self._markets

    def _load_markets(self) -> Dict[str, str]:
        """Charge la configuration des marchés depuis le fichier JSON."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('markets', {})
        except FileNotFoundError:
            logger.error(f"Fichier de configuration introuvable: {self.config_file}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de lecture du JSON de configuration: {e}")
            raise

    def find_matching_countries(self, search_term: str) -> List[str]:
        """
        Trouve les pays qui correspondent à la recherche partielle.

        Args:
            search_term: Terme de recherche (insensible à la casse)

        Returns:
            Liste des pays correspondants
        """
        if not search_term.strip():
            return []

        search_lower = search_term.lower()
        return [
            country for country in self.markets.keys()
            if search_lower in country.lower()
        ]

    def get_suffix(self, country: str) -> Optional[str]:
        """Retourne le suffixe pour un pays donné."""
        return self.markets.get(country)


class StockInfoFetcher:
    """Récupère les informations d'une action via yfinance."""

    @staticmethod
    def fetch(ticker: str) -> Optional[Dict]:
        """
        Récupère les informations d'une action.

        Args:
            ticker: Le ticker complet (avec suffixe)

        Returns:
            Dictionnaire avec les infos ou None si erreur
        """
        try:
            logger.info(f"Recherche de {ticker}...")
            stock = yf.Ticker(ticker)
            info = stock.info

            # Vérification que l'action existe
            if not info or not info.get('longName'):
                logger.warning(f"Aucune information trouvée pour {ticker}")
                return None

            return {
                "ticker": ticker.upper(),
                "name": info.get('longName', 'N/A'),
                "sector": info.get('sector', 'N/A'),
                "industry": info.get('industry', 'N/A'),
                "country": info.get('country', 'N/A'),
                "marketCap": info.get('marketCap', 'N/A'),
                "currency": info.get('currency', 'N/A')
            }

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de {ticker}: {e}")
            return None


class StockManagerCLI:
    """Interface en ligne de commande pour gérer les actions."""

    def __init__(self):
        self.db = StockDatabase(JSON_FILE)
        self.market_mgr = MarketManager(CONFIG_FILE)
        self.fetcher = StockInfoFetcher()

    def run(self) -> None:
        """Lance l'application."""
        print("=" * 50)
        print("📊 GESTIONNAIRE D'ACTIONS")
        print("=" * 50)
        print("Tapez 'q' ou 'quit' à tout moment pour quitter\n")

        while True:
            if not self.add_stock_workflow():
                break

            continuer = self._ask_continue()
            if not continuer:
                print("\n✅ Terminé!")
                break

    def add_stock_workflow(self) -> bool:
        """
        Workflow complet pour ajouter une action.

        Returns:
            False si l'utilisateur veut quitter, True sinon
        """
        print("\n" + "-" * 50)
        print("➕ AJOUT D'UNE ACTION")
        print("-" * 50)

        # Sélection du pays
        country = self._select_country()
        if country is None:
            return False

        # Récupération du suffixe
        suffix = self.market_mgr.get_suffix(country)
        if suffix is None:
            print(f"❌ Erreur: Aucun suffixe trouvé pour {country}")
            return True

        # Saisie du ticker
        ticker_input = self._input_with_quit("Ticker: ")
        if ticker_input is None:
            return False

        ticker_input = ticker_input.strip().upper()
        if not ticker_input:
            print("❌ Le ticker ne peut pas être vide")
            return True

        full_ticker = ticker_input + suffix

        # Vérifier si le ticker existe déjà
        if self.db.ticker_exists(full_ticker):
            print(f"⚠️  L'action {full_ticker} existe déjà dans la base!")
            return True

        # Récupération des infos
        stock_info = self.fetcher.fetch(full_ticker)

        if not stock_info:
            print(f"❌ Action {full_ticker} non trouvée ou erreur de récupération")
            return True

        # Affichage des informations
        self._display_stock_info(stock_info)

        # Confirmation
        confirm = input("\n✓ Confirmer l'ajout? (oui/non): ").strip().lower()
        if confirm not in POSITIVE_RESPONSES:
            print("❌ Ajout annulé")
            return True

        # Ajout à la base
        success, message = self.db.add_stock(stock_info)

        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")

        return True

    def _select_country(self) -> Optional[str]:
        """
        Permet à l'utilisateur de sélectionner un pays.

        Returns:
            Le nom du pays ou None si quit
        """
        while True:
            country_input = self._input_with_quit(
                "\nPays (ou 'liste' pour voir tous): "
            )

            if country_input is None:
                return None

            country_input = country_input.strip()

            if not country_input:
                print("❌ Veuillez entrer un pays")
                continue

            if country_input.lower() == 'liste':
                self._display_countries()
                continue

            # Recherche partielle
            matches = self.market_mgr.find_matching_countries(country_input)

            if len(matches) == 0:
                print(f"❌ Aucun pays trouvé pour '{country_input}'")
                print("💡 Tapez 'liste' pour voir tous les pays disponibles")
                continue

            elif len(matches) == 1:
                country = matches[0]
                print(f"✓ Pays sélectionné: {country}")
                return country

            else:
                # Plusieurs correspondances
                country = self._choose_from_list(matches)
                if country is None:
                    return None
                if country:
                    print(f"✓ Pays sélectionné: {country}")
                    return country

    def _display_countries(self) -> None:
        """Affiche la liste de tous les pays disponibles."""
        print("\n📋 Pays disponibles:")
        countries = sorted(self.market_mgr.markets.keys())
        for i, country in enumerate(countries, 1):
            suffix = self.market_mgr.markets[country]
            print(f"  {i:2d}. {country:20s} (suffixe: {suffix})")
        print()

    def _choose_from_list(self, options: List[str]) -> Optional[str]:
        """
        Permet de choisir parmi une liste d'options.

        Returns:
            L'option choisie, chaîne vide si invalide, None si quit
        """
        print(f"\n🔍 Plusieurs pays correspondent:")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")

        choice = self._input_with_quit("Choix (numéro ou nom complet): ")
        if choice is None:
            return None

        choice = choice.strip()

        # Choix par numéro
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]

        # Choix par nom
        if choice in options:
            return choice

        print("❌ Choix invalide")
        return ""

    def _display_stock_info(self, stock_info: Dict) -> None:
        """Affiche les informations d'une action."""
        print("\n" + "=" * 50)
        print("📈 INFORMATIONS DE L'ACTION")
        print("=" * 50)
        print(f"Ticker:    {stock_info['ticker']}")
        print(f"Nom:       {stock_info['name']}")
        print(f"Secteur:   {stock_info['sector']}")
        print(f"Industrie: {stock_info['industry']}")
        print(f"Pays:      {stock_info['country']}")
        if stock_info.get('marketCap') and stock_info['marketCap'] != 'N/A':
            print(f"Cap. bours.: {stock_info['marketCap']:,} {stock_info.get('currency', '')}")
        print("=" * 50)

    def _input_with_quit(self, prompt: str) -> Optional[str]:
        """
        Demande une entrée utilisateur avec possibilité de quitter.

        Returns:
            L'entrée utilisateur ou None si quit
        """
        user_input = input(prompt).strip()
        if user_input.lower() in QUIT_COMMANDS:
            return None
        return user_input

    def _ask_continue(self) -> bool:
        """Demande si l'utilisateur veut continuer."""
        response = input("\n➕ Ajouter une autre action? (oui/non): ").strip().lower()
        return response in POSITIVE_RESPONSES


def main():
    """Point d'entrée principal."""
    try:
        cli = StockManagerCLI()
        cli.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interruption par l'utilisateur")
    except FileNotFoundError as e:
        logger.error(f"Fichier manquant: {e}")
        print(f"\n❌ Erreur: Fichier de configuration manquant")
        print(f"Vérifiez que {CONFIG_FILE} existe")
    except Exception as e:
        logger.exception("Erreur fatale")
        print(f"\n❌ Erreur inattendue: {e}")


if __name__ == "__main__":
    main()
