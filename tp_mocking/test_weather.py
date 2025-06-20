import unittest
from unittest.mock import patch, Mock
from weather_service import WeatherService


class TestWeather(unittest.TestCase):
    """Tests pour la classe WeatherService."""

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
        self.sample_weather_data = {
            "main": {"temp": 25.5},
            "weather": [{"main": "Clear", "description": "ciel dégagé"}],
        }
        self.not_found_response = {"cod": "404", "message": "city not found"}

    def tearDown(self):
        """Nettoyage après chaque test."""
        self.env_patcher.stop()

    @patch("weather_service.requests.get")
    def test_get_temperature_success(self, mock_get):
        """Test avec données de la fixture"""
        # Configuration du mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_weather_data
        mock_get.return_value = mock_response

        # Appel de la méthode
        temp = self.service.get_temperature("Paris")

        # Vérifications
        self.assertEqual(temp, 25.5)

        # Vérification de l'appel à l'API
        expected_url = "http://api.openweathermap.org/data/2.5/weather"
        expected_params = {"q": "Paris", "appid": "fake_api_key", "units": "metric"}
        mock_get.assert_called_once_with(expected_url, params=expected_params)

    @patch("weather_service.requests.get")
    def test_get_temperature_city_not_found(self, mock_get):
        """Test quand la ville n'existe pas"""
        # Configuration du mock
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = self.not_found_response
        mock_get.return_value = mock_response

        # Appel de la méthode
        temp = self.service.get_temperature("VilleInexistante")

        # Vérifications
        self.assertIsNone(temp)

    @patch("weather_service.requests.get")
    def test_get_temperature_network_error(self, mock_get):
        """Test quand il y a une erreur réseau"""
        # Configuration du mock pour simuler une erreur réseau
        mock_get.side_effect = Exception("Erreur réseau")

        # Appel de la méthode
        temp = self.service.get_temperature("Paris")

        # Vérifications
        self.assertIsNone(temp)

    @patch("weather_service.requests.get")
    def test_multiple_cities(self, mock_get):
        """Test plusieurs villes avec une seule méthode"""
        cities_and_temps = [("Paris", 25.0), ("Lyon", 22.5), ("Marseille", 27.3)]

        for city, expected_temp in cities_and_temps:
            with self.subTest(city=city):
                # Configuration du mock pour cette ville
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "main": {"temp": expected_temp},
                    "weather": [{"main": "Clear"}],
                }
                mock_get.return_value = mock_response

                # Appel de la méthode
                temp = self.service.get_temperature(city)

                # Vérifications
                self.assertEqual(temp, expected_temp)

                # Vérification de l'appel à l'API
                args, kwargs = mock_get.call_args
                self.assertEqual(kwargs["params"]["q"], city)

                # Réinitialisation du mock pour la prochaine itération
                mock_get.reset_mock()

    @patch("weather_service.requests.get")
    def test_get_forecast_success(self, mock_get):
        """Test la récupération des prévisions météo"""
        # Configuration du mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "list": [
                {
                    "dt": 1624000000,
                    "main": {"temp": 22.5},
                    "weather": [{"main": "Clear"}],
                },
                {
                    "dt": 1624003600,
                    "main": {"temp": 23.1},
                    "weather": [{"main": "Clouds"}],
                },
            ]
        }
        mock_get.return_value = mock_response

        # Appel de la méthode
        forecast = self.service.get_forecast("Paris", days=1)

        # Vérifications
        self.assertEqual(len(forecast), 2)
        self.assertEqual(forecast[0]["main"]["temp"], 22.5)
        self.assertEqual(forecast[1]["main"]["temp"], 23.1)

        # Vérification de l'appel à l'API
        expected_url = "http://api.openweathermap.org/data/2.5/forecast"
        expected_params = {
            "q": "Paris",
            "appid": "fake_api_key",
            "units": "metric",
            "cnt": 8,  # 1 jour * 8 prévisions par jour
        }
        mock_get.assert_called_once_with(expected_url, params=expected_params)

    @patch("weather_service.requests.get")
    def test_get_forecast_error(self, mock_get):
        """Test la gestion des erreurs lors de la récupération des prévisions"""
        # Configuration du mock pour simuler une erreur
        mock_get.side_effect = Exception("Erreur réseau")

        # Appel de la méthode
        forecast = self.service.get_forecast("Paris")

        # Vérifications
        self.assertIsNone(forecast)

    @patch("weather_service.requests.get")
    def test_is_good_weather_true(self, mock_get):
        """Test quand la météo est bonne"""
        # Configuration du mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {"temp": 25.0},
            "weather": [{"main": "Clear"}],
        }
        mock_get.return_value = mock_response

        # Appel de la méthode
        is_good = self.service.is_good_weather("Nice")

        # Vérifications
        self.assertTrue(is_good)

    @patch("weather_service.requests.get")
    def test_is_good_weather_false(self, mock_get):
        """Test quand la météo n'est pas bonne (température basse)"""
        # Configuration du mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {"temp": 15.0},  # Température < 20°C
            "weather": [{"main": "Clear"}],
        }
        mock_get.return_value = mock_response

        # Appel de la méthode
        is_good = self.service.is_good_weather("Brest")

        # Vérifications
        self.assertFalse(is_good)

    @patch("weather_service.requests.get")
    def test_is_good_weather_rainy(self, mock_get):
        """Test quand il pleut"""
        # Configuration du mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "main": {"temp": 25.0},
            "weather": [{"main": "Rain"}],  # Il pleut
        }
        mock_get.return_value = mock_response

        # Appel de la méthode
        is_good = self.service.is_good_weather("Lyon")

        # Vérifications
        self.assertFalse(is_good)

    @patch("weather_service.WeatherService.get_temperature")
    def test_compare_cities_city1_warmer(self, mock_get_temp):
        """Test la comparaison quand la première ville est plus chaude"""
        # Configuration du mock
        mock_get_temp.side_effect = [28.0, 22.0]  # Paris: 28°C, Lyon: 22°C

        # Appel de la méthode
        result = self.service.compare_cities("Paris", "Lyon")

        # Vérifications
        self.assertIn("Paris est plus chaud que Lyon", result)
        self.assertIn("28.0", result)
        self.assertIn("22.0", result)

    @patch("weather_service.WeatherService.get_temperature")
    def test_compare_cities_city2_warmer(self, mock_get_temp):
        """Test la comparaison quand la deuxième ville est plus chaude"""
        # Configuration du mock
        mock_get_temp.side_effect = [18.0, 22.0]  # Paris: 18°C, Nice: 22°C

        # Appel de la méthode
        result = self.service.compare_cities("Paris", "Nice")

        # Vérifications
        self.assertIn("Nice est plus chaud que Paris", result)
        self.assertIn("22.0", result)
        self.assertIn("18.0", result)

    @patch("weather_service.WeatherService.get_temperature")
    def test_compare_cities_same_temperature(self, mock_get_temp):
        """Test la comparaison quand les deux villes ont la même température"""
        # Configuration du mock
        mock_get_temp.side_effect = [20.0, 20.0]  # Même température

        # Appel de la méthode
        result = self.service.compare_cities("Paris", "Toulouse")

        # Vérifications
        self.assertIn("même température", result.lower())
        self.assertIn("20.0", result)

    @patch("weather_service.WeatherService.get_temperature")
    def test_compare_cities_error(self, mock_get_temp):
        """Test la comparaison quand une température est None"""
        # Configuration du mock
        mock_get_temp.side_effect = [22.0, None]  # Seconde ville non trouvée

        # Appel de la méthode
        result = self.service.compare_cities("Paris", "VilleInconnue")

        # Vérifications
        self.assertEqual(result, "Impossible de comparer les villes")


if __name__ == "__main__":
    unittest.main(verbosity=2)
