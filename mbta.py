import json
import os
from dataclasses import dataclass
from typing import Literal

import requests
from dotenv import load_dotenv

load_dotenv()

MBTA_API_ADDR = 'https://api-v3.mbta.com'
MBTA_API_KEY = os.getenv('MBTA_API_KEY')

@dataclass
class Route:
    """Represents a green line route
    """
    id: Literal['B', 'C', 'D', 'E']
    long_name: str
    short_name: str
    direction_destinations: tuple[str, str]

def load_routes() -> dict[Literal['B', 'C', 'D', 'E'], Route]:
    """Loads the stored information about each green line route
    """
    with open('green_line.json') as file:
        return json.load(file)

def download_routes():
    headers = {
        "x-api-key": MBTA_API_KEY
    }

    with requests.get(f'{MBTA_API_ADDR}/routes?filter[type]=0', headers=headers) as req:
        with open('data.json', 'w') as file:
            json.dump(req.json(), file, indent=2)

def download_single_trip():
    trip_id= "71193895"

def download_data():
    headers = {
        "x-api-key": MBTA_API_KEY
    }
    
    with open('output.json', 'w') as file:
        with requests.get(f'{MBTA_API_ADDR}/stops?filter[route]=Green-B', headers=headers) as req:
            json.dump(req.json(), file, indent=2)

if __name__ == '__main__':
    download_data()