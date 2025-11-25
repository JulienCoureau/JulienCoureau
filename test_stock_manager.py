"""
Tests unitaires pour le gestionnaire d'actions.
Installation : pip install pytest pytest-mock
Exécution : pytest test_stock_manager.py -v
"""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from stock_manager_improved import (
    StockDatabase,
    MarketManager,
    StockInfoFetcher,
    StockManagerCLI
)


@pytest.fixture
def temp_json_file(tmp_path):
    """Crée un fichier JSON temporaire pour les tests."""
    return tmp_path / "test_stocks.json"


@pytest.fixture
def temp_config_file(tmp_path):
    """Crée un fichier de config temporaire."""
    config_file = tmp_path / "config.json"
    config_data = {
        "markets": {
            "États-Unis": "",
            "France": ".PA",
            "Allemagne": ".DE"
        }
    }
    config_file.write_text(json.dumps(config_data))
    return config_file


class TestStockDatabase:
    """Tests pour la classe StockDatabase."""

    def test_init_creates_directory(self, temp_json_file):
        """Test que l'initialisation crée le répertoire."""
        db = StockDatabase(temp_json_file)
        assert temp_json_file.parent.exists()

    def test_load_stocks_empty_file(self, temp_json_file):
        """Test le chargement quand le fichier n'existe pas."""
        db = StockDatabase(temp_json_file)
        stocks = db.load_stocks()
        assert stocks == []

    def test_save_and_load_stocks(self, temp_json_file):
        """Test sauvegarde et chargement."""
        db = StockDatabase(temp_json_file)
        test_stocks = [
            {"ticker": "AAPL", "name": "Apple Inc."},
            {"ticker": "GOOGL", "name": "Alphabet Inc."}
        ]

        assert db.save_stocks(test_stocks) is True
        loaded = db.load_stocks()
        assert len(loaded) == 2
        assert loaded[0]["ticker"] == "AAPL"

    def test_add_stock(self, temp_json_file):
        """Test ajout d'une action."""
        db = StockDatabase(temp_json_file)
        stock_info = {
            "ticker": "MSFT",
            "name": "Microsoft Corporation",
            "sector": "Technology"
        }

        success, message = db.add_stock(stock_info)
        assert success is True
        assert "MSFT" in message

        # Vérifier que l'action est bien sauvegardée
        stocks = db.load_stocks()
        assert len(stocks) == 1
        assert stocks[0]["ticker"] == "MSFT"

    def test_add_duplicate_stock(self, temp_json_file):
        """Test qu'on ne peut pas ajouter un doublon."""
        db = StockDatabase(temp_json_file)
        stock_info = {"ticker": "AAPL", "name": "Apple Inc."}

        # Premier ajout
        success1, _ = db.add_stock(stock_info)
        assert success1 is True

        # Tentative de doublon
        success2, message2 = db.add_stock(stock_info)
        assert success2 is False
        assert "existe déjà" in message2

    def test_ticker_exists(self, temp_json_file):
        """Test la vérification d'existence."""
        db = StockDatabase(temp_json_file)
        stock_info = {"ticker": "TSLA", "name": "Tesla Inc."}

        assert db.ticker_exists("TSLA") is False
        db.add_stock(stock_info)
        assert db.ticker_exists("TSLA") is True

    def test_load_stocks_corrupted_json(self, temp_json_file):
        """Test le chargement avec JSON corrompu."""
        temp_json_file.write_text("{ invalid json }")
        db = StockDatabase(temp_json_file)
        stocks = db.load_stocks()
        assert stocks == []


class TestMarketManager:
    """Tests pour la classe MarketManager."""

    def test_load_markets(self, temp_config_file):
        """Test le chargement des marchés."""
        mgr = MarketManager(temp_config_file)
        markets = mgr.markets

        assert len(markets) == 3
        assert markets["États-Unis"] == ""
        assert markets["France"] == ".PA"

    def test_markets_cached(self, temp_config_file):
        """Test que les marchés sont mis en cache."""
        mgr = MarketManager(temp_config_file)
        markets1 = mgr.markets
        markets2 = mgr.markets
        assert markets1 is markets2  # Même objet en mémoire

    def test_find_matching_countries_exact(self, temp_config_file):
        """Test recherche exacte."""
        mgr = MarketManager(temp_config_file)
        matches = mgr.find_matching_countries("France")
        assert matches == ["France"]

    def test_find_matching_countries_partial(self, temp_config_file):
        """Test recherche partielle."""
        mgr = MarketManager(temp_config_file)
        matches = mgr.find_matching_countries("all")
        assert "Allemagne" in matches

    def test_find_matching_countries_case_insensitive(self, temp_config_file):
        """Test recherche insensible à la casse."""
        mgr = MarketManager(temp_config_file)
        matches = mgr.find_matching_countries("FRANCE")
        assert "France" in matches

    def test_find_matching_countries_no_match(self, temp_config_file):
        """Test recherche sans résultat."""
        mgr = MarketManager(temp_config_file)
        matches = mgr.find_matching_countries("Inexistant")
        assert matches == []

    def test_find_matching_countries_empty(self, temp_config_file):
        """Test recherche avec chaîne vide."""
        mgr = MarketManager(temp_config_file)
        matches = mgr.find_matching_countries("")
        assert matches == []

    def test_get_suffix(self, temp_config_file):
        """Test récupération du suffixe."""
        mgr = MarketManager(temp_config_file)
        assert mgr.get_suffix("France") == ".PA"
        assert mgr.get_suffix("États-Unis") == ""
        assert mgr.get_suffix("Inexistant") is None

    def test_load_markets_file_not_found(self, tmp_path):
        """Test erreur si fichier config manquant."""
        fake_file = tmp_path / "nonexistent.json"
        mgr = MarketManager(fake_file)

        with pytest.raises(FileNotFoundError):
            _ = mgr.markets


class TestStockInfoFetcher:
    """Tests pour la classe StockInfoFetcher."""

    @patch('stock_manager_improved.yf.Ticker')
    def test_fetch_success(self, mock_ticker):
        """Test récupération réussie."""
        # Mock de la réponse yfinance
        mock_info = {
            'longName': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'country': 'United States',
            'marketCap': 2500000000000,
            'currency': 'USD'
        }
        mock_ticker.return_value.info = mock_info

        fetcher = StockInfoFetcher()
        result = fetcher.fetch("AAPL")

        assert result is not None
        assert result['ticker'] == 'AAPL'
        assert result['name'] == 'Apple Inc.'
        assert result['sector'] == 'Technology'

    @patch('stock_manager_improved.yf.Ticker')
    def test_fetch_no_info(self, mock_ticker):
        """Test quand aucune info n'est disponible."""
        mock_ticker.return_value.info = {}

        fetcher = StockInfoFetcher()
        result = fetcher.fetch("INVALID")

        assert result is None

    @patch('stock_manager_improved.yf.Ticker')
    def test_fetch_exception(self, mock_ticker):
        """Test gestion des exceptions."""
        mock_ticker.side_effect = Exception("API Error")

        fetcher = StockInfoFetcher()
        result = fetcher.fetch("ERROR")

        assert result is None


class TestStockManagerCLI:
    """Tests pour la classe StockManagerCLI."""

    @patch('stock_manager_improved.CONFIG_FILE')
    @patch('stock_manager_improved.JSON_FILE')
    def test_init(self, mock_json, mock_config, temp_json_file, temp_config_file):
        """Test initialisation du CLI."""
        mock_json.return_value = temp_json_file
        mock_config.return_value = temp_config_file

        cli = StockManagerCLI()
        assert cli.db is not None
        assert cli.market_mgr is not None
        assert cli.fetcher is not None

    def test_input_with_quit_normal(self):
        """Test input normal."""
        cli = StockManagerCLI()
        with patch('builtins.input', return_value='test'):
            result = cli._input_with_quit("Prompt: ")
            assert result == 'test'

    def test_input_with_quit_commands(self):
        """Test commandes de quit."""
        cli = StockManagerCLI()
        quit_commands = ['q', 'quit', 'exit', 'quitter', 'Q', 'QUIT']

        for cmd in quit_commands:
            with patch('builtins.input', return_value=cmd):
                result = cli._input_with_quit("Prompt: ")
                assert result is None

    def test_ask_continue_yes(self):
        """Test réponse positive pour continuer."""
        cli = StockManagerCLI()
        with patch('builtins.input', return_value='oui'):
            assert cli._ask_continue() is True

    def test_ask_continue_no(self):
        """Test réponse négative."""
        cli = StockManagerCLI()
        with patch('builtins.input', return_value='non'):
            assert cli._ask_continue() is False

    def test_choose_from_list_by_number(self):
        """Test choix par numéro."""
        cli = StockManagerCLI()
        options = ['France', 'Allemagne', 'Italie']

        with patch('builtins.input', return_value='2'):
            result = cli._choose_from_list(options)
            assert result == 'Allemagne'

    def test_choose_from_list_by_name(self):
        """Test choix par nom."""
        cli = StockManagerCLI()
        options = ['France', 'Allemagne', 'Italie']

        with patch('builtins.input', return_value='France'):
            result = cli._choose_from_list(options)
            assert result == 'France'

    def test_choose_from_list_invalid(self):
        """Test choix invalide."""
        cli = StockManagerCLI()
        options = ['France', 'Allemagne']

        with patch('builtins.input', return_value='invalid'):
            result = cli._choose_from_list(options)
            assert result == ''

    def test_choose_from_list_quit(self):
        """Test quit pendant le choix."""
        cli = StockManagerCLI()
        options = ['France', 'Allemagne']

        with patch('builtins.input', return_value='q'):
            result = cli._choose_from_list(options)
            assert result is None


# Tests d'intégration
class TestIntegration:
    """Tests d'intégration bout-en-bout."""

    @patch('stock_manager_improved.yf.Ticker')
    def test_full_workflow(self, mock_ticker, tmp_path):
        """Test workflow complet d'ajout d'action."""
        # Setup
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"markets": {"France": ".PA"}}))

        json_file = tmp_path / "stocks.json"

        # Mock yfinance
        mock_info = {
            'longName': 'Total Energies',
            'sector': 'Energy',
            'industry': 'Oil & Gas',
            'country': 'France',
            'marketCap': 150000000000,
            'currency': 'EUR'
        }
        mock_ticker.return_value.info = mock_info

        # Créer les composants
        db = StockDatabase(json_file)
        mgr = MarketManager(config_file)
        fetcher = StockInfoFetcher()

        # Workflow
        suffix = mgr.get_suffix("France")
        assert suffix == ".PA"

        ticker = "TTE" + suffix
        stock_info = fetcher.fetch(ticker)
        assert stock_info is not None

        success, message = db.add_stock(stock_info)
        assert success is True

        # Vérification
        stocks = db.load_stocks()
        assert len(stocks) == 1
        assert stocks[0]['ticker'] == 'TTE.PA'


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
