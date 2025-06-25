#!/usr/bin/env python3
from requests_cache import CachedSession
from retry_requests import retry


class WeatherApi:
    def __init__(self, cache: str = ".weather_cache"):
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
                "hourly": ["temperature_2m", "wind_direction_100m", "wind_speed_10m"],
                "timezone": "auto",
            },
        )

        # TODO: Handle error
        response = response.json()
        data = response["hourly"]
        for timestamp in zip(
            data["time"],
            data["temperature_2m"],
            data["wind_direction_100m"],
            data["wind_speed_10m"],
        ):
            print(timestamp)


def main():
    api = WeatherApi()
    coords = (44.4571, 26.126)  # Example coordinates
    start_date = "2025-06-09"
    end_date = "2025-06-23"
    api.request_weather_data(coords, start_date, end_date)


if __name__ == "__main__":
    main()
