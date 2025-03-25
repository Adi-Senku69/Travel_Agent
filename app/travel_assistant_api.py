# travel_assistant_api.py
from datetime import datetime
from typing import Dict, Any, List, Optional
from config import config


from services.booking_service import BookingAPIService
from services.weather_service import WeatherAPIService
from services.mapbox_service import OpenRouteService
from services.sherpa_service import SherpaService
from services.aviation_service import AviationService


class TravelAssistantAPI:
    def __init__(self, config: Dict[str, str]):
        """
        Initialize the Travel Assistant API with service API keys.
        
        Args:
            config: Dictionary containing API keys for all services
        """
        #self.booking_service = BookingAPIService(config['booking_api_key'])
        self.booking_service = BookingAPIService(config['api_keys']['booking_api_key'])  # ✅ Correct

        # self.weather_service = WeatherAPIService(config['weather_api_key'])
        # self.mapbox_service = OpenRouteService(config['mapbox_token'])
        # self.sherpa_service = SherpaService(config['sherpa_api_key'])
        # self.aviation_service = AviationService(config['aviation_api_key'])
        self.weather_service = WeatherAPIService(config['api_keys']['weather_api_key'])
        self.mapbox_service = OpenRouteService(config['api_keys']['mapbox_token'])
        self.sherpa_service = SherpaService(config['api_keys']['sherpa_api_key'])
        self.aviation_service = AviationService(config['api_keys']['aviation_api_key'])


    def plan_trip(self, trip_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive trip planning using multiple APIs.
        
        Args:
            trip_details: Dictionary containing trip parameters
            
        Returns:
            Dictionary containing comprehensive trip plan data
        """
        destination = trip_details.get('destination')
        dates = trip_details.get('dates')
        purpose = trip_details.get('purpose')
        traveler_info = trip_details.get('traveler_info')
        
        # Calculate days between dates
        days = self._calculate_days_between_dates(dates['check_in'], dates['check_out'])
        
        # Get weather forecast for destination
        weather_forecast = self.weather_service.get_forecast(destination, days)
        
        # Get hotel options
        hotels = self.booking_service.search_hotels(
            destination, dates['check_in'], dates['check_out'], traveler_info['adults'])
        
        # Get visa and travel requirements
        travel_requirements = self.sherpa_service.get_visa_requirements(
            traveler_info['citizenship'], destination)
        
        covid_restrictions = self.sherpa_service.get_covid_restrictions(
            traveler_info['citizenship'], destination)
        
        return {
            'destination': destination,
            'dates': dates,
            'weather': weather_forecast,
            'hotels': hotels,
            'travel_requirements': {
                'visa': travel_requirements,
                'covid': covid_restrictions
            }
        }

    def get_flight_info(self, flight_number: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed flight information.
        
        Args:
            flight_number: The flight number
            date: Optional flight date
            
        Returns:
            Dictionary containing flight information
        """
        return self.aviation_service.get_flight_status(flight_number, date)

    def get_travel_route(self, origin: str, destination: str) -> Dict[str, Any]:
        """
        Get travel route with traffic information.
        
        Args:
            origin: Origin location
            destination: Destination location
            
        Returns:
            Dictionary containing route and traffic information
        """
        return self.mapbox_service.get_directions(origin, destination)

    def _calculate_days_between_dates(self, start_date: str, end_date: str) -> int:
        """
        Calculate number of days between two dates.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Number of days between dates
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        diff = end - start
        return diff.days + 1  # Including the end date
