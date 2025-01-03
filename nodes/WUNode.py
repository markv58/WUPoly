"""Node class for Weather Underground data."""
import time
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import polyinterface

LOGGER = polyinterface.LOGGER

class WUNode(polyinterface.Node):
    """Weather Node Class"""
    
    id = 'weather'
    hint = 0x01020800
    
    WEATHER_API_BASE = 'https://api.weatherapi.com/v1/current.json'
    FORECAST_API_BASE = 'https://api.weatherapi.com/v1/forecast.json'
    DEFAULT_TIMEOUT = 10
    MAX_RETRIES = 3
    RETRY_DELAY = 5
    RATE_LIMIT_CALLS = 10
    RATE_LIMIT_PERIOD = 60
    
    drivers = [
        {'driver': 'ST', 'value': 0, 'uom': 17},     # Temperature (F)
        {'driver': 'CLITEMP', 'value': 0, 'uom': 17},# Temperature (F)
        {'driver': 'CLIHUM', 'value': 0, 'uom': 51}, # Humidity %
        {'driver': 'BARPRES', 'value': 0, 'uom': 117},# Barometric Pressure (inHg)
        {'driver': 'WINDDIR', 'value': 0, 'uom': 76}, # Wind Direction (degrees)
        {'driver': 'WINDSPD', 'value': 0, 'uom': 48}, # Wind Speed (mph)
        {'driver': 'RAINRT', 'value': 0, 'uom': 46},  # Rain Rate (in/hr)
        {'driver': 'GV0', 'value': 0, 'uom': 51},     # Chance of Rain %
        {'driver': 'GV1', 'value': 0, 'uom': 25},     # Condition Text
    ]

    def __init__(self, controller, primary, address, name, api_key=None, location=None):
        """Initialize the weather node."""
        super().__init__(controller, primary, address, name)
        self.api_key = api_key
        self.location = location
        self._last_api_call = datetime.min
        self._api_calls = []
        self._last_update = datetime.min
        self._cached_data = {}
        self.commands = {'QUERY': self.query}

    def start(self):
        """Start the node."""
        try:
            self.update_weather()
        except Exception as err:
            LOGGER.error(f'Error starting node: {err}')
            self.setDriver('ST', 0)

    def stop(self):
        """Stop the node."""
        try:
            LOGGER.info('Stopping weather node')
            self.setDriver('ST', 0)
        except Exception as err:
            LOGGER.error(f'Error stopping node: {err}')
        
    def query(self, command=None):
        """Query the node's status."""
        try:
            self.reportDrivers()
        except Exception as err:
            LOGGER.error(f'Error querying node: {err}')

    def shortPoll(self):
        """Poll for frequent updates."""
        try:
            if self._cached_data and datetime.now() - self._last_update < timedelta(minutes=5):
                return
            self.update_weather()
        except Exception as err:
            LOGGER.error(f'Error in shortPoll: {err}')

    def longPoll(self):
        """Poll for infrequent updates."""
        try:
            self.update_weather()
        except Exception as err:
            LOGGER.error(f'Error in longPoll: {err}')

    def _check_rate_limit(self):
        """Implement rate limiting for API calls."""
        try:
            now = datetime.now()
            self._api_calls = [t for t in self._api_calls 
                              if now - t < timedelta(seconds=self.RATE_LIMIT_PERIOD)]
            
            if len(self._api_calls) >= self.RATE_LIMIT_CALLS:
                sleep_time = (self._api_calls[0] + 
                             timedelta(seconds=self.RATE_LIMIT_PERIOD) - now).total_seconds()
                if sleep_time > 0:
                    LOGGER.info(f'Rate limit reached, waiting {sleep_time:.1f} seconds')
                    time.sleep(sleep_time)
            self._api_calls.append(now)
        except Exception as err:
            LOGGER.error(f'Error in rate limiting: {err}')

    def _format_location(self) -> str:
        """Convert location to required format for API."""
        if not self.location:
            return ''
        if ',' in self.location:
            lat, lon = self.location.split(',')
            return f"{lat.strip()},{lon.strip()}"
        if self.location.isdigit():
            return self.location
        return self.location.replace(' ', '_')

    def update_weather(self) -> bool:
        """Update weather data from API."""
        if not self.api_key or not self.location:
            LOGGER.error('Missing API key or location')
            self.setDriver('ST', 0)
            return False

        try:
            self._check_rate_limit()
            current_params = {
                'key': self.api_key,
                'q': self._format_location(),
                'aqi': 'no'
            }
            
            current_data = self._make_api_request(
                self.WEATHER_API_BASE, 
                current_params
            )
            if not current_data:
                self.setDriver('ST', 0)
                return False

            forecast_params = {**current_params, 'days': 1}
            forecast_data = self._make_api_request(
                self.FORECAST_API_BASE,
                forecast_params
            )

            weather_data = {
                'current': current_data.get('current', {}),
                'forecast': forecast_data.get('forecast', {})
            }

            self._cached_data = weather_data
            self._last_update = datetime.now()
            self._update_drivers(weather_data)
            return True

        except Exception as e:
            LOGGER.error(f'Failed to update weather: {str(e)}')
            self.setDriver('ST', 0)
            return False

    def _make_api_request(self, url: str, params: dict) -> Optional[dict]:
        """Make API request with retries.
        
        Args:
            url: API endpoint URL
            params: Query parameters for the request
            
        Returns:
            Optional[dict]: API response data or None if request fails
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(
                    url,
                    params=params,
                    timeout=self.DEFAULT_TIMEOUT
                )
                response.raise_for_status()
                data = response.json()
                if 'error' in data:
                    LOGGER.error(f"API Error: {data['error']['message']}")
                    return None
                return data
            except requests.exceptions.RequestException as e:
                if attempt == self.MAX_RETRIES - 1:
                    LOGGER.error(f'API request failed after {self.MAX_RETRIES} attempts: {e}')
                    return None
                time.sleep(self.RETRY_DELAY)
        return None

    def _update_drivers(self, data: dict) -> None:
        """Update node drivers with weather data.
        
        Args:
            data: Weather data from API
        """
        try:
            current = data.get('current', {})
            forecast = data.get('forecast', {}).get('forecastday', [{}])[0]

            self.setDriver('ST', float(current.get('temp_f', 0)))
            self.setDriver('CLITEMP', float(current.get('temp_f', 0)))
            self.setDriver('CLIHUM', int(current.get('humidity', 0)))
            self.setDriver('BARPRES', float(current.get('pressure_in', 0)))
            self.setDriver('WINDDIR', int(current.get('wind_degree', 0)))
            self.setDriver('WINDSPD', float(current.get('wind_mph', 0)))
            self.setDriver('RAINRT', float(current.get('precip_in', 0)))

            day = forecast.get('day', {})
            self.setDriver('GV0', int(day.get('daily_chance_of_rain', 0)))
            self.setDriver('GV1', str(current.get('condition', {}).get('text', 'Unknown')))

        except (ValueError, TypeError, KeyError) as e:
            LOGGER.error(f'Error updating drivers: {e}')
            self.setDriver('ST', 0) 