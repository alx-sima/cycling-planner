from api import WeatherApi
from os import listdir, path
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import gpxpy


class GPXParser:
    def __init__(self, api: WeatherApi):
        self.api = api

    @staticmethod
    def angle_diff(a: float, b: float) -> float:
        """Calculate the difference between two angles in degrees."""
        diff = abs(a - b) % 360
        return diff if diff <= 180 else diff - 360

    @staticmethod
    def plot_gpx(df: pd.DataFrame, title: str = "GPX Track"):
        """Show info about a GPX track."""
        fig, axs = plt.subplots(3, 2)
        fig.suptitle(title + " data analysis")

        axs[0][0].scatter(df["elapsed_time"], df["speed"], label="Speed (km/h)", color="red")
        axs[0][0].set_xlabel("Elapsed Time (s)")
        axs[0][0].set_ylabel("Speed (km/h)")
        axs[0][0].legend()

        axs[0][1].axis("off")

        axs[1][0].scatter(
            df["elapsed_time"], df["incline"], label="Incline (%)", color="blue"
        )
        axs[1][0].set_xlabel("Elapsed Time (s)")
        axs[1][0].set_ylabel("Incline (%)")
        axs[1][0].legend()

        axs[1][1].scatter(df["elapsed_time"], df["temperature"], label="Temperature (°C)", color="orange")
        axs[1][1].set_xlabel("Elapsed Time (s)")
        axs[1][1].set_ylabel("Temperature (°C)")
        axs[1][1].legend()

        axs[2][0].scatter(
            df["elapsed_time"], df["wind_course_diff"], label="Wind Course Diff (°)", color="green"
        )
        axs[2][0].set_xlabel("Elapsed Time (s)")
        axs[2][0].set_ylabel("Wind Course Diff (°)")
        axs[2][0].legend()

        axs[2][1].scatter(
            df["elapsed_time"], df["wind_speed"], label="Wind Speed (m/s)", color="purple"
        )
        axs[2][1].set_xlabel("Elapsed Time (s)")
        axs[2][1].set_ylabel("Wind Speed (m/s)")
        axs[2][1].legend()

        plt.tight_layout()
        plt.show()

        print(f"Average speed: {df['speed'].mean():.2f} km/h")
        print(f"Max speed: {df['speed'].max():.2f} km/h")
        print(f"Average incline: {df['incline'].mean():.2f} %")
        print(f"Total distance: {df['speed'].sum() * 1000 / 3600:.2f} m")

    def request_weather_data(
        self, lat: float, lon: float, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Request weather data for a given latitude and longitude."""
        start_date = start_date.strftime("%Y-%m-%d")
        end_date = end_date.strftime("%Y-%m-%d")

        return self.api.request_weather_data(lat, lon, start_date, end_date)

    def parse_segment(
        self, filename: str, segment: gpxpy.gpx.GPXTrackSegment
    ) -> pd.DataFrame:
        """Parse a GPX track segment and return a DataFrame with additional calculated data."""
        points = segment.points

        timestamps = [points[0].time]
        latitudes = [points[0].latitude]
        longitudes = [points[0].longitude]
        elevations = [points[0].elevation]
        speeds = [0]
        alt_diffs = [0]
        inclines = [0]
        elapsed_times = [0]
        courses = [0]
        weather_times = [points[0].time.replace(minute=0, second=0, microsecond=0)]

        prev_point = points[0]
        for point in points[1:]:
            dist = point.distance_3d(prev_point)
            time_diff = (point.time - prev_point.time).total_seconds()
            speed = 3.6 * (dist / time_diff) if time_diff > 0 else 0
            alt_diff = point.elevation - prev_point.elevation
            incline = alt_diff / dist * 100 if dist > 0 else 0
            elapsed = (point.time - points[0].time).total_seconds()
            course = gpxpy.geo.get_course(
                prev_point.latitude,
                prev_point.longitude,
                point.latitude,
                point.longitude,
            )
            weather_time = point.time.replace(minute=0, second=0, microsecond=0)

            timestamps.append(point.time)
            latitudes.append(point.latitude)
            longitudes.append(point.longitude)
            elevations.append(point.elevation)
            speeds.append(speed)
            alt_diffs.append(alt_diff)
            inclines.append(incline)
            elapsed_times.append(elapsed)
            courses.append(course)
            weather_times.append(weather_time)

            prev_point = point

        data = {
            "filename": filename,
            "timestamp": timestamps,
            "latitude": latitudes,
            "longitude": longitudes,
            "altitude": elevations,
            "speed": speeds,
            "altitude_diff": alt_diffs,
            "incline": inclines,
            "elapsed_time": elapsed_times,
            "course": courses,
            "weather_time": weather_times,
        }
        data = pd.DataFrame(data=data)

        # Correlate with weather data
        weather_data = self.request_weather_data(
            points[0].latitude,
            points[0].longitude,
            points[0].time,
            points[-1].time,
        )
        data = data.join(weather_data, on="weather_time")
        data.drop(columns=["weather_time"], inplace=True)

        # Compute wind relative angle
        data["wind_course_diff"] = data["course"] - data["wind_direction"]
        data["wind_course_diff_cos"] = data["wind_course_diff"].apply(
            lambda x: np.cos(np.radians(x))
        )
        return data

    def parse_gpx_file(self, filename: str) -> pd.DataFrame:
        with open(filename, "r") as f:
            gpx_data = gpxpy.parse(f)

        dfs = []
        for track in gpx_data.tracks:
            for segment in track.segments:
                df = self.parse_segment(filename, segment)
                dfs.append(df)
        return pd.concat(dfs, ignore_index=True)

    def parse_gpx_dir(self, dir: str) -> list[pd.DataFrame]:
        """Read all GPX files from a directory."""
        files = [f for f in listdir(dir) if f.endswith(".gpx")]

        dfs = []
        for file in files:
            df = self.parse_gpx_file(path.join(dir, file))
            dfs.append(df)
        return dfs
