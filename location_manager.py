import json
import os

LOCATION_FILE = "locations.json"

# Default fallback location if none set yet
default_location = {
    "lat": 31.4638,
    "lon": -100.4370,
    "city": "San Angelo",
    "state": "TX",
    "station_id": None
}

def load_all_locations():
    """Load all saved locations from file."""
    if not os.path.exists(LOCATION_FILE):
        return {}
    try:
        with open(LOCATION_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load location file: {e}")
        return {}

def save_all_locations(locations):
    """Save all locations to file."""
    try:
        with open(LOCATION_FILE, "w") as f:
            json.dump(locations, f, indent=4)
        print("✅ Locations saved successfully.")
    except Exception as e:
        print(f"❌ Failed to save locations: {e}")

def load_location(guild_id):
    """Load the location for a specific guild."""
    locations = load_all_locations()
    return locations.get(str(guild_id), default_location.copy())

def save_location(guild_id, lat=None, lon=None, city=None, state=None, station_id=None):
    """Save location or station override for a specific guild."""
    locations = load_all_locations()
    location = locations.get(str(guild_id), default_location.copy())

    if lat is not None and lon is not None:
        location["lat"] = float(lat)
        location["lon"] = float(lon)

    if city is not None:
        location["city"] = city

    if state is not None:
        location["state"] = state

    if station_id is not None:
        location["station_id"] = station_id.upper()

    locations[str(guild_id)] = location
    save_all_locations(locations)

def get_lat_lon(guild_id):
    loc = load_location(guild_id)
    return loc.get("lat", default_location["lat"]), loc.get("lon", default_location["lon"])

def get_city_state(guild_id):
    loc = load_location(guild_id)
    return loc.get("city", default_location["city"]), loc.get("state", default_location["state"])

def get_station_id(guild_id):
    loc = load_location(guild_id)
    return loc.get("station_id", None)
