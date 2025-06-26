import api
import gpx

apix = api.WeatherApi()
gpx.read_gpx(apix, "data/liber.gpx")
