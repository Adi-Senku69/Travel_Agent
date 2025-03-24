# aviation_service.py
import requests
from typing import Dict, Any, Optional


class AviationService:
    def _init_(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.aviationstack.com/v1"

    def get_flight_status(self, flight_number: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status information for a specific flight.
        
        Args:
            flight_number: The flight number (e.g., 'BA123')
            date: Optional flight date (YYYY-MM-DD)
            
        Returns:
            Dictionary containing flight status information
        """
        try:
            url = f"{self.base_url}/flights"
            params = {
                'access_key': self.api_key,
                'flight_number': flight_number
            }
            
            if date:
                params['flight_date'] = date
                
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching flight status: {e}")
            raise

    def search_flights(self, origin: str, destination: str, date: str) -> Dict[str, Any]:
        """
        Search flights between two airports on a specific date.
        
        Args:
            origin: IATA code of origin airport
            destination: IATA code of destination airport
            date: Flight date (YYYY-MM-DD)
            
        Returns:
            Dictionary containing flight search results
        """
        try:
            url = f"{self.base_url}/flights"
            params = {
                'access_key': self.api_key,
                'dep_iata': origin,
                'arr_iata': destination,
                'flight_date': date
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error searching flights: {e}")
            raise