from api import WeatherApi
from os import listdir, path

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import gpxpy

def angle_diff(a: float, b: float) -> float:
    """Calculate the difference between two angles in degrees."""
    diff = abs(a - b) % 360
    return diff if diff <= 180 else diff - 360

def plot_gpx(df: pd.DataFrame, filename: str):
    fig, axs = plt.subplots(2, 1)
    fig.suptitle(filename + " data analysis")

    axs[0].scatter(df["elapsed"], df["speed"], label="Speed (km/h)")
    axs[0].set_xlabel("Elapsed Time (s)")
    axs[0].set_ylabel("Speed (km/h)")
    axs[0].legend()

    axs[1].scatter(df["elapsed"], df["incline"], label="Incline (%)", color="orange")
    axs[1].set_xlabel("Elapsed Time (s)")
    axs[1].set_ylabel("Incline (%)")
    axs[1].legend()

    plt.tight_layout()
    plt.show()

    print(f"Average speed: {df['speed'].mean():.2f} km/h")
    print(f"Max speed: {df['speed'].max():.2f} km/h")
    print(f"Average incline: {df['incline'].mean():.2f} %")
    print(f"Total distance: {df['speed'].sum() * 1000 / 3600:.2f} m")


def read_gpx(api: WeatherApi, filename: str) -> pd.DataFrame:
    with open(filename, "r") as f:
        gpx = gpxpy.parse(f)

    points = gpx.tracks[0].segments[0].points

    prev_point = points[0]
    new_points = [
        (
            prev_point.latitude,
            prev_point.longitude,
            prev_point.elevation,
            0,  # speed
            0,  # alt_diff
            0,  # incline
            0,  # elapsed
            0,  # course
            prev_point.time.replace(minute=0, second=0, microsecond=0),  # time
        )
    ]

    start_date = points[0].time.strftime("%Y-%m-%d")
    end_date = points[-1].time.strftime("%Y-%m-%d")
    weather_data = api.request_weather_data(
        (prev_point.latitude, prev_point.longitude), start_date, end_date
    )
    weather_data.set_index("time", inplace=True)

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

        new_points.append(
            (
                point.latitude,
                point.longitude,
                point.elevation,
                speed,
                alt_diff,
                incline,
                elapsed,
                course,
                point.time.replace(minute=0, second=0, microsecond=0),
            )
        )
        prev_point = point

    data = pd.DataFrame.from_records(
        data=new_points,
        columns=[
            "lat",
            "lon",
            "alt",
            "speed",
            "altdiff",
            "incline",
            "elapsed",
            "course",
            "time",
        ],
    )

    data = data.join(weather_data, on="time")
    data.drop(columns=["time"], inplace=True)

    # insert column difference between course and wind_direction
    data["course_diff"] = data["course"] - data["wind_direction"]
    data["cos_course"] = data["course_diff"].apply(lambda x: np.cos(np.radians(x)))
    data["sin_course"] = data["course_diff"].apply(lambda x: np.sin(np.radians(x)))
    return data


def read_gpx_dir(api: WeatherApi, dir: str) -> [pd.DataFrame]:
    files = [f for f in listdir(dir) if f.endswith(".gpx")]

    dfs = []
    for file in files:
        df = read_gpx(api, path.join(dir, file))
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)
