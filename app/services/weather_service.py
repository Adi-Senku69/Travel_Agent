# weather_service.py
import requests
from typing import Dict, Any, Optional


class WeatherAPIService:
    def _init_(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.weatherapi.com/v1"

    def get_current_weather(self, location: str) -> Dict[str, Any]:
        """
        Get current weather for a location.
        
        Args:
            location: City name or coordinates
            
        Returns:
            Dictionary containing current weather data
        """
        try:
            url = f"{self.base_url}/current.json"
            params = {
                'key': self.api_key,
                'q': location,
                'aqi': 'yes'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching current weather: {e}")
            raise

    def get_forecast(self, location: str, days: int = 3) -> Dict[str, Any]:
        """
        Get weather forecast for a location.
        
        Args:
            location: City name or coordinates
            days: Number of forecast days (max 10)
            
        Returns:
            Dictionary containing forecast data
        """
        try:
            url = f"{self.base_url}/forecast.json"
            params = {
                'key': self.api_key,
                'q': location,
                'days': days,
                'aqi': 'yes',
                'alerts': 'yes'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather forecast: {e}")
            raise
 