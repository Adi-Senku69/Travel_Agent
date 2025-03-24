# sherpa_service.py
import requests
from typing import Dict, Any


class SherpaService:
    def _init_(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.joinsherpa.com/v2"
        self.headers = {
            'API-Key': self.api_key,
            'Accept-Language': 'en'
        }

    def get_visa_requirements(self, citizenship: str, destination: str) -> Dict[str, Any]:
        """
        Get visa requirements for travel between countries.
        
        Args:
            citizenship: Country code of traveler's citizenship
            destination: Country code of destination
            
        Returns:
            Dictionary containing visa requirement data
        """
        try:
            url = f"{self.base_url}/entry-requirements"
            params = {
                'citizenship': citizenship,
                'destination': destination
            }
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching visa requirements: {e}")
            raise

    def get_covid_restrictions(self, citizenship: str, destination: str) -> Dict[str, Any]:
        """
        Get COVID-19 travel restrictions.
        
        Args:
            citizenship: Country code of traveler's citizenship
            destination: Country code of destination
            
        Returns:
            Dictionary containing COVID restriction data
        """
        try:
            url = f"{self.base_url}/travel-restrictions"
            params = {
                'citizenship': citizenship,
                'destination': destination
            }
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching COVID restrictions: {e}")
            raise