# mapbox_service.py
import requests
from typing import Dict, Any, List, Union, Tuple


class MapboxService:
    def _init_(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.mapbox.com"

    def get_directions(self, origin: Union[str, List[float], Tuple[float, float]], 
                        destination: Union[str, List[float], Tuple[float, float]], 
                        profile: str = 'driving') -> Dict[str, Any]:
        """
        Get directions between two points.
        
        Args:
            origin: Origin point as coordinates [lng, lat] or string
            destination: Destination point as coordinates [lng, lat] or string
            profile: Routing profile (driving, walking, cycling)
            
        Returns:
            Dictionary containing directions data
        """
        try:
            if isinstance(origin, (list, tuple)):
                origin_coords = f"{origin[0]},{origin[1]}"
            else:
                origin_coords = origin
                
            if isinstance(destination, (list, tuple)):
                dest_coords = f"{destination[0]},{destination[1]}"
            else:
                dest_coords = destination
            
            url = f"{self.base_url}/directions/v5/mapbox/{profile}/{origin_coords};{dest_coords}"
            params = {
                'access_token': self.access_token,
                'geometries': 'geojson',
                'steps': 'true',
                'overview': 'full',
                'annotations': 'duration,distance,speed'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching directions: {e}")
            raise

    def get_traffic_data(self, coordinates: Union[str, List[float], Tuple[float, float]]) -> Dict[str, Any]:
        """
        Get traffic flow data for a location.
        
        Args:
            coordinates: Location as coordinates [lng, lat] or string
            
        Returns:
            Dictionary containing traffic data
        """
        try:
            if isinstance(coordinates, (list, tuple)):
                coords = f"{coordinates[0]},{coordinates[1]}"
            else:
                coords = coordinates
                
            url = f"{self.base_url}/traffic/v1/flow"
            params = {
                'access_token': self.access_token,
                'location': coords
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching traffic data: {e}")
            raise