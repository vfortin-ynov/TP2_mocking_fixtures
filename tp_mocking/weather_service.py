import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


class WeatherService:
    def __init__(self):
        self.base_url = os.getenv("OPENWEATHER_API_URL")
        self.api_key = os.getenv("OPENWEATHER_API_KEY")

    def _make_request(self, endpoint, params=None):
        """Méthode utilitaire pour faire les requêtes à l'API"""
        if params is None:
            params = {}
        params["appid"] = self.api_key
        params["units"] = "metric"

        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.RequestException, Exception):
            return None

    def get_temperature(self, city):
        """Récupère la température d'une ville via l'API"""
        data = self._make_request("weather", {"q": city})
        return data["main"]["temp"] if data and "main" in data else None

    def save_weather_report(self, city, filename="weather_log.json"):
        """Récupère la météo et la sauvegarde dans un fichier"""
        # 1. Récupérer la température
        temp = self.get_temperature(city)
        if temp is None:
            return False

        # 2. Créer le rapport
        report = {
            "city": city,
            "temperature": temp,
            "timestamp": datetime.now().isoformat(),
        }

        # 3. Sauvegarder dans le fichier
        try:
            # Lire le fichier existant
            with open(filename, "r") as f:
                reports = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            reports = []

        # Ajouter le nouveau rapport
        reports.append(report)

        # Écrire dans le fichier
        with open(filename, "w") as f:
            json.dump(reports, f, indent=2)

        return True

    def get_forecast(self, city, days=5):
        """Récupère les prévisions météo sur N jours"""
        data = self._make_request(
            "forecast", {"q": city, "cnt": days * 8}
        )  # 8 prévisions par jour
        if not data or "list" not in data:
            return None
        return data["list"]

    def is_good_weather(self, city):
        """Vérifie si la météo est bonne (>20°C et pas de pluie)"""
        data = self._make_request("weather", {"q": city})
        if not data or "main" not in data or "weather" not in data:
            return None

        temp = data["main"]["temp"]
        weather_condition = data["weather"][0]["main"].lower()
        return temp > 20 and "rain" not in weather_condition

    def compare_cities(self, city1, city2):
        """Compare les températures entre deux villes"""
        temp1 = self.get_temperature(city1)
        temp2 = self.get_temperature(city2)

        if temp1 is None or temp2 is None:
            return "Impossible de comparer les villes"

        if temp1 > temp2:
            return f"{city1} est plus chaud que {city2} ({temp1}°C > {temp2}°C)"
        elif temp2 > temp1:
            return f"{city2} est plus chaud que {city1} ({temp2}°C > {temp1}°C)"
        else:
            return f"Les deux villes ont la même température ({temp1}°C)"
