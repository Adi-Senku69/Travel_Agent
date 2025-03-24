# booking_service.py
import requests
from typing import Dict, Any, Optional, List


class BookingAPIService:
    def _init_(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://booking-com.p.rapidapi.com"
        self.headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': 'booking-com.p.rapidapi.com'
        }

    def search_hotels(self, location: str, check_in: str, check_out: str, adults: int = 1) -> Dict[str, Any]:
        """
        Search for hotels based on location and dates.
        
        Args:
            location: Location ID or name
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            adults: Number of adults
            
        Returns:
            Dictionary containing hotel search results
        """
        try:
            url = f"{self.base_url}/v1/hotels/search"
            params = {
                'location_id': location,
                'checkin_date': check_in,
                'checkout_date': check_out,
                'adults_number': adults,
                'room_number': 1,
                'locale': 'en-us'
            }
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error searching hotels: {e}")
            raise

    def get_hotel_details(self, hotel_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific hotel.
        
        Args:
            hotel_id: The ID of the hotel
            
        Returns:
            Dictionary containing hotel details
        """
        try:
            url = f"{self.base_url}/v1/hotels/details"
            params = {'hotel_id': hotel_id}
            
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching hotel details: {e}")
            raise
