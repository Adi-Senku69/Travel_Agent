import requests
from typing import Dict, Any, Union, List, Tuple

class OpenRouteService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openrouteservice.org/v2"

    def get_directions(self, origin: Union[str, List[float], Tuple[float, float]], 
                       destination: Union[str, List[float], Tuple[float, float]], 
                       profile: str = 'driving-car') -> Dict[str, Any]:
        """
        Get directions between two points using OpenRouteService.

        Args:
            origin: Origin point as coordinates [lng, lat] or string.
            destination: Destination point as coordinates [lng, lat] or string.
            profile: Routing profile (driving-car, cycling-regular, walking).

        Returns:
            Dictionary containing directions data.
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

            url = f"{self.base_url}/directions/{profile}/geojson"
            params = {
                'api_key': self.api_key
            }
            json_data = {
                'coordinates': [[float(origin_coords.split(',')[0]), float(origin_coords.split(',')[1])],
                                [float(dest_coords.split(',')[0]), float(dest_coords.split(',')[1])]]
            }

            response = requests.post(url, json=json_data, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching directions: {e}")
            raise
