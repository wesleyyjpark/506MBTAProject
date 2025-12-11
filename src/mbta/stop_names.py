"""
Utility to map MBTA stop IDs to stop names using MBTA API v3
"""

import requests
import os
from typing import Dict, Optional
import json
from dotenv import load_dotenv

load_dotenv()

MBTA_API_ADDR = 'https://api-v3.mbta.com'
MBTA_API_KEY = os.getenv('MBTA_API_KEY')


def get_stop_name(stop_id: str, cache: Optional[Dict[str, str]] = None) -> str:
    """
    Get stop name from MBTA API given a stop ID.
    
    Args:
        stop_id: MBTA stop ID (e.g., '70196', 'place-buest')
        cache: Optional dictionary to cache results
        
    Returns:
        Stop name or stop_id if not found
    """
    if cache is not None and stop_id in cache:
        return cache[stop_id]
    
    headers = {}
    if MBTA_API_KEY:
        headers['x-api-key'] = MBTA_API_KEY
    
    try:
        # Try to get stop info from API
        url = f"{MBTA_API_ADDR}/stops/{stop_id}"
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            stop_name = data['data']['attributes'].get('name', stop_id)
            
            if cache is not None:
                cache[stop_id] = stop_name
            
            return stop_name
        else:
            # If API call fails, return stop_id
            return stop_id
    except Exception as e:
        # If error, return stop_id
        return stop_id


def get_stop_names_batch(stop_ids: list, cache_file: Optional[str] = None) -> Dict[str, str]:
    """
    Get stop names for multiple stop IDs, with caching.
    
    Args:
        stop_ids: List of stop IDs
        cache_file: Optional path to JSON file to cache results
        
    Returns:
        Dictionary mapping stop_id -> stop_name
    """
    # Load cache if exists
    cache = {}
    if cache_file and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                cache = json.load(f)
        except:
            pass
    
    # Get names for stops not in cache
    headers = {}
    if MBTA_API_KEY:
        headers['x-api-key'] = MBTA_API_KEY
    
    for stop_id in stop_ids:
        if stop_id not in cache:
            try:
                url = f"{MBTA_API_ADDR}/stops/{stop_id}"
                response = requests.get(url, headers=headers, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    cache[stop_id] = data['data']['attributes'].get('name', stop_id)
                else:
                    cache[stop_id] = stop_id
            except:
                cache[stop_id] = stop_id
    
    # Save cache
    if cache_file:
        os.makedirs(os.path.dirname(cache_file) if os.path.dirname(cache_file) else '.', exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    
    return cache


def get_green_line_stops(cache_file: str = "data/stop_names_cache.json") -> Dict[str, str]:
    """
    Get all Green Line stops with their names.
    
    Args:
        cache_file: Path to cache file
        
    Returns:
        Dictionary mapping stop_id -> stop_name
    """
    headers = {}
    if MBTA_API_KEY:
        headers['x-api-key'] = MBTA_API_KEY
    
    # Get all Green Line stops
    try:
        url = f"{MBTA_API_ADDR}/stops"
        params = {
            'filter[route]': 'Green-B,Green-C,Green-D,Green-E',
            'page[limit]': 200
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            stops = {}
            
            for stop in data.get('data', []):
                stop_id = stop['id']
                stop_name = stop['attributes'].get('name', stop_id)
                stops[stop_id] = stop_name
            
            # Save to cache
            if cache_file:
                os.makedirs(os.path.dirname(cache_file) if os.path.dirname(cache_file) else '.', exist_ok=True)
                with open(cache_file, 'w') as f:
                    json.dump(stops, f, indent=2)
            
            return stops
        else:
            # Load from cache if API fails
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    return json.load(f)
            return {}
    except Exception as e:
        # Load from cache if error
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

