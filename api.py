from requests_cache import CachedSession
from retry_requests import retry

import pandas as pd

API_URL = "https://archive-api.open-meteo.com/v1/archive"
REQUESTED_PARAMS = ["temperature_2m", "wind_direction_10m", "wind_speed_10m"]


class WeatherApi:
    def __init__(self, cache: str = ".cache/weather_data"):
        self.session = CachedSession(cache, expire_after=-1)
        self.session = retry(self.session, retries=3, backoff_factor=0.5)

    def request_weather_data(
        self, latitude: float, longitude: float, start_date: str, end_date: str
    ) -> pd.DataFrame | None:
        response = self.session.get(
            API_URL,
            {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date,
                "end_date": end_date,
                "hourly": REQUESTED_PARAMS,
                "timezone": "GMT",
            },
        )

        if response.status_code != 200:
            print(f"Error fetching weather data: {response.status_code}")
            return

        response = response.json()
        data = response["hourly"]

        hourly_data = {
            "weather_time": pd.to_datetime(data["time"], utc=True),
            "temperature": data["temperature_2m"],
            "wind_direction": data["wind_direction_10m"],
            "wind_speed": data["wind_speed_10m"],
        }
        data = pd.DataFrame(data=hourly_data)
        data.set_index("weather_time", inplace=True)
        return data
