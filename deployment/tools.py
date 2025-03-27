import requests
from serpapi import GoogleSearch
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
import json
import os

env_values = {"WEATHERAPI_KEY": os.environ.get("WEATHERAPI_KEY"), "SERP_API_KEY": os.environ.get("SERP_API_KEY")}

def clean_flight_data(flight_data):
    # Remove airline_logo and departure_token from the top-level dictionary
    # flight_data.pop('departure_token', None)
    flight_data.pop('airline_logo', None)

    # Iterate through flights and remove airline_logo from each flight
    for flight in flight_data.get('flights', []):
        flight.pop('airline_logo', None)

    return flight_data

@tool
def get_flight_data(departure_city:str, arrival_city:str, return_date:str | None, outbound_date:str, currency:str="USD", type:str="2", travel_class:str="1", multi_city_json:str=None, adults:str="1", children:str="0", sort_by:str="1", stops:str="0", return_times:str=None, layover_duration:str=None, max_price:str=None, departure_token:str=None) -> dict:
    """
    Fetch flight details using SerpAPI.

    Parameters:
    departure_id (str): Name of the departure city in IATA code (e.g., 'New York').
    arrival_id (str): Name of the arrival city in IATA code (e.g., 'London').
    retrun_date (str | None): Return date in YYYY-MM-DD format.
    outbound_date (str): Departure date in YYYY-MM-DD format.
    currency (str): Parameter defines the currency of the returned prices.
    type (str): Parameter defines the type of the flights. Available options:

        1 - Round trip (default)
        2 - One way
        3 - Multi-city


    travel_class (str): Parameter defines the travel class.
            Available options:
            1 - Economy (default)
            2 - Premium economy
            3 - Business
            4 - First

    multi_city_json (dict): Parameter defines the flight information for multi-city flights. It's a JSON string containing multiple flight information objects. Each object should contain the following fields:

departure_id - The departure airport code or location kgmid. The format is the same as the main departure_id parameter.
arrival_id - The arrival airport code or location kgmid. The format is the same as the main arrival_id parameter.
date - Flight date. The format is the same as the outbound_date parameter.
times - Time range for the flight. The format is the same as the outbound_times parameter. This parameter is optional.

Example:
[{"departure_id":"CDG","arrival_id":"NRT","date":"2025-04-01"},{"departure_id":"NRT","arrival_id":"LAX,SEA","date":"2025-04-08"},{"departure_id":"LAX,SEA","arrival_id":"AUS","date":"2025-04-15","times":"8,18,9,23"}]

    adults (str): Number of adults
    children (str): Number of children
    sort_by (str): Parameter defines the sorting order of the results.
            Available options:

            1 - Top flights (default)
            2 - Price
            3 - Departure time
            4 - Arrival time
            5 - Duration
            6 - Emissions
    stops (str): Parameter defines the number of stops during the flight.
                Available options:

                0 - Any number of stops (default)
                1 - Nonstop only
                2 - 1 stop or fewer
                3 - 2 stops or fewer
    max_price (str): Maximum price of the ticket.
    return_times (str): Parameter defines the return times range. It's a string containing two (for departure only) or four (for departure and arrival) comma-separated numbers. Each number represents the beginning of an hour. For example:

        4,18: 4:00 AM - 7:00 PM departure
        0,18: 12:00 AM - 7:00 PM departure
        19,23: 7:00 PM - 12:00 AM departure
        4,18,3,19: 4:00 AM - 7:00 PM departure, 3:00 AM - 8:00 PM arrival
        0,23,3,19: unrestricted departure, 3:00 AM - 8:00 PM arrival

    layover_duration (str): Parameter defines the layover duration, in minutes. It's a string containing two comma-separated numbers. For example, specify 90,330 for 1 hr 30 min - 5 hr 30 min.

    departure_token (str): Used to get details of the return flight

    Returns:
    dict: Flight details if available, else an error message.

    """
    cities_iata = {
    "new york": "JFK",
    "los angeles": "LAX",
    "chicago": "ORD",
    "san francisco": "SFO",
    "dallas": "DFW",
    "miami": "MIA",
    "atlanta": "ATL",
    "london": "LHR",
    "paris": "CDG",
    "tokyo": "HND",
    "dubai": "DXB",
    "singapore": "SIN",
    "hong kong": "HKG",
    "sydney": "SYD",
    "toronto": "YYZ",
    "frankfurt": "FRA",
    "amsterdam": "AMS",
    "madrid": "MAD",
    "beijing": "PEK",
    "seoul": "ICN",
    "bangkok": "BKK",
    "rome": "FCO",
    "istanbul": "IST",
    "são paulo": "GRU",
    "mexico city": "MEX",
    "moscow": "SVO",
    "delhi": "DEL",
    "mumbai": "BOM",
    "shanghai": "PVG",
    "johannesburg": "JNB",
    "bangalore": "BLR",
    "berlin": "BER",
}

    departure_id = cities_iata.get(departure_city.lower(), departure_city)
    arrival_id = cities_iata.get(arrival_city.lower(), arrival_city)


    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "return_date": return_date,
        "outbound_date": outbound_date,
        "api_key": env_values["SERP_API_KEY"],
        "currency": currency,
        "type": type,
        "travel_class": travel_class,
        "multi_city_json": multi_city_json,
        "adults": adults,
        "children": children,
        "sort_by": sort_by,
        "max_price": max_price,
        "return_times": return_times,
        "layover_duration": layover_duration,
        "stops": stops,
        "departure_token": departure_token
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        results = results['best_flights'][:10]
        print(results)
        cleaned_flights = [clean_flight_data(flight) for flight in results]
        tidy_json = json.dumps(cleaned_flights, indent=4)
        # print(tidy_json)
        return tidy_json
    except Exception as e:
        return "There are no such flights for the given criteria."

@tool
def get_hotel_data(location: str, checkin_date: str, checkout_date: str, adults:str="1", children:str="0",
                   rating:str="8", hotel_class:str="4"):
    """
    Fetches hotel data from Google Hotels using SerpAPI.

    :param location: City or location name
    :param checkin_date: Check-in date in YYYY-MM-DD format
    :param checkout_date: Check-out date in YYYY-MM-DD format
    :param adults: Number of adults
    :param children: Number of children
    :param rating: Hotel rating
    :param hotel_class: The number of stars of the hotel
    :return: List of hotels with their details
    """
    params = {
        "engine": "google_hotels",
        "q": location,
        "check_in_date": checkin_date,
        "check_out_date": checkout_date,
        "api_key": env_values["SERP_API_KEY"],
        "adults": adults,
        "children": children,
        "rating": rating,
        "hotel_class": hotel_class,
    }

    response = GoogleSearch(params)
    data = response.get_dict()

    hotels = []
    # print(data)

    if "properties" in data:
        for hotel in data["properties"]:
            hotels.append({
                "name": hotel.get("name"),
                "price": hotel.get("rate_per_night"),
                "description": hotel.get("description"),
                "ratings": hotel.get("overall_rating"),
                "stars": hotel.get("hotel_class"),
                "check_in_time": hotel.get("check_in_time"),
                "check_out_time": hotel.get("check_out_time"),
                "link": hotel.get("link"),
            })
            # hotels.append(hotel)
    else:
        hotels = "No results found."

    return hotels

@tool
def get_weather(city, days):
    """
    Get weather from weather API.
    :param city: The city name.
    :param days: The number of days to forecast
    :return: weather data.
    """
# URLs for current weather and forecast
    API_KEY = env_values['WEATHERAPI_KEY']
    CURRENT_URL = f"http://api.weatherapi.com/v1/current.json?key={API_KEY}&q={city}&aqi=no"
    FORECAST_URL = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={city}&days={days}&aqi=no&alerts=no"

    output = ""
    # Fetch Current Weather
    current_response = requests.get(CURRENT_URL)
    if current_response.status_code == 200:
        current_data = current_response.json()
        current_temp = current_data["current"]["temp_c"]
        condition = current_data["current"]["condition"]["text"]
        output += f"Current Weather in {city}: {current_temp}°C, {condition}\n"
    else:
        output +=  f"Error fetching current weather: {current_response.status_code}, {current_response.text}"

    # Fetch Forecast Weather
    forecast_response = requests.get(FORECAST_URL)
    if forecast_response.status_code == 200:
        forecast_data = forecast_response.json()

        print("\nForecast:")
        for day in forecast_data["forecast"]["forecastday"]:
            date = day["date"]
            max_temp = day["day"]["maxtemp_c"]
            min_temp = day["day"]["mintemp_c"]
            condition = day["day"]["condition"]["text"]
            output += f"{date}: {condition}, {min_temp}-{max_temp}°C"
    else:
        output += f"Error fetching forecast: {forecast_response.status_code}, {forecast_response.text}"

    return output

tools = [get_flight_data, get_hotel_data, get_weather]

tools_node = ToolNode(tools)