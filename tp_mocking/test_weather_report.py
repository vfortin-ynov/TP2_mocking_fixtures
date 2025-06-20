import unittest
import json
from unittest.mock import patch, Mock, mock_open
from weather_service import WeatherService


class TestWeatherReport(unittest.TestCase):
    """Tests pour la sauvegarde des rapports météo"""

    def setUp(self):
        """Prépare les données de test communes."""
        # Patch de l'environnement avant de créer l'instance de WeatherService
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "OPENWEATHER_API_KEY": "fake_api_key",
                "OPENWEATHER_API_URL": "http://api.openweathermap.org/data/2.5",
            },
        )

        self.env_patcher.start()

        self.service = WeatherService()

        self.test_city = "Paris"

        self.test_temp = 25.5

        self.test_timestamp = "2023-01-01T12:00:00.000000"

        self.test_report = {
            "city": self.test_city,
            "temperature": self.test_temp,
            "timestamp": self.test_timestamp,
        }

        self.sample_weather_data = {
            "main": {"temp": self.test_temp},
            "weather": [{"main": "Clear"}],
        }

    def tearDown(self):
        """Nettoyage après chaque test."""
        self.env_patcher.stop()

    @patch("weather_service.datetime")
    @patch("builtins.open", new_callable=mock_open, read_data="[]")
    @patch("weather_service.WeatherService.get_temperature")
    def test_save_weather_report_success(self, mock_get_temp, mock_file, mock_datetime):
        """Test la sauvegarde réussie d'un rapport météo"""
        # Configuration des mocks
        mock_get_temp.return_value = self.test_temp
        mock_datetime.now.return_value.isoformat.return_value = self.test_timestamp

        # Appel de la méthode
        result = self.service.save_weather_report(self.test_city)

        # Vérifications
        self.assertTrue(result)
        mock_get_temp.assert_called_once_with(self.test_city)

        # Vérification de l'écriture dans le fichier
        mock_file.assert_called_with("weather_log.json", "w")

        # Vérifie que write a été appelé au moins une fois
        self.assertGreaterEqual(len(mock_file().write.call_args_list), 1)

    @patch("weather_service.WeatherService.get_temperature")
    def test_save_weather_report_api_failure(self, mock_get_temp):
        """Test l'échec de sauvegarde quand l'API échoue"""
        # Configuration du mock pour simuler un échec de l'API
        mock_get_temp.return_value = None

        # Appel de la méthode
        result = self.service.save_weather_report("VilleInexistante")

        # Vérifications
        self.assertFalse(result)

    @patch("weather_service.WeatherService.get_temperature")
    @patch("builtins.open")
    def test_save_weather_report_file_handling(self, mock_open_file, mock_get_temp):
        """Test la gestion des fichiers lors de la sauvegarde"""
        # Configuration des mocks
        mock_get_temp.return_value = self.test_temp

        # Simuler un fichier existant avec des données
        existing_reports = [
            {"city": "Lyon", "temperature": 22.5, "timestamp": "2023-01-01T10:00:00"}
        ]
        mock_open_file.return_value.__enter__.return_value.read.return_value = json.dumps(
            existing_reports
        )

        # Configuration du mock pour json.dump
        with patch("json.dump") as mock_json_dump:
            # Appel de la méthode
            result = self.service.save_weather_report(self.test_city)

            # Vérifications
            self.assertTrue(result)

            # Vérifier que json.dump a été appelé avec la bonne structure
            args, _ = mock_json_dump.call_args
            saved_reports = args[0]
            self.assertEqual(len(saved_reports), 2)
            self.assertEqual(saved_reports[0]["city"], "Lyon")
            self.assertEqual(saved_reports[1]["city"], self.test_city)


if __name__ == "__main__":
    unittest.main(verbosity=2)
