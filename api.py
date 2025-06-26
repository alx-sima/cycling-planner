from requests_cache import CachedSession
from retry_requests import retry

import pandas as pd


class WeatherApi:
    def __init__(self, cache: str = ".cache/weather_data"):
        self.session = CachedSession(cache, expire_after=-1)
        self.session = retry(self.session, retries=3, backoff_factor=0.5)

    def request_weather_data(
        self, coords: tuple[float, float], start_date: str, end_date: str
    ) -> dict:
        latitude, longitude = coords
        response = self.session.get(
            "https://archive-api.open-meteo.com/v1/archive",
            {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date,
                "end_date": end_date,
                "hourly": ["temperature_2m", "wind_direction_10m", "wind_speed_10m"],
                "timezone": "GMT",
            },
        )

        if response.status_code != 200:
            # Handle error appropriately, e.g., raise an exception or log the error
            raise Exception(f"Error fetching weather data: {response.status_code}")

        # TODO: Handle error
        response = response.json()
        data = response["hourly"]

        hourly_data = {
            "time": pd.to_datetime(data["time"], utc=True),
            "temperature": data["temperature_2m"],
            "wind_direction": data["wind_direction_10m"],
            "wind_speed": data["wind_speed_10m"],
        }
        return pd.DataFrame(data=hourly_data)
