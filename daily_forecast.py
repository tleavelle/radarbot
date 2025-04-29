import discord
import aiohttp
import datetime

# --- CONFIGURATION ---
from config import FORECAST_CHANNEL_ID, FORECAST_MESSAGE_ID
from location_manager import get_lat_lon, get_city_state

FORECAST_DAYS = 7

# --- Emoji icons based on weather codes ---
WEATHER_EMOJIS = {
    "clear": "☀️",
    "mainly_clear": "🌤️",
    "partly_cloudy": "⛅",
    "overcast": "☁️",
    "fog": "🌫️",
    "drizzle": "🌦️",
    "rain": "🌧️",
    "freezing_rain": "🥶🌧️",
    "snow": "🌨️",
    "thunderstorm": "⛈️"
}

def interpret_weather_code(code):
    if code in [0]:
        return "clear"
    elif code in [1]:
        return "mainly_clear"
    elif code in [2]:
        return "partly_cloudy"
    elif code in [3]:
        return "overcast"
    elif code in [45, 48]:
        return "fog"
    elif code in [51, 53, 55, 56, 57]:
        return "drizzle"
    elif code in [61, 63, 65, 66, 67, 80, 81, 82]:
        return "rain"
    elif code in [71, 73, 75, 77, 85, 86]:
        return "snow"
    elif code in [95, 96, 99]:
        return "thunderstorm"
    else:
        return "unknown"

def c_to_f(celsius):
    return round((celsius * 9 / 5) + 32)

def ms_to_mph(ms):
    return round(ms * 2.23694)

async def fetch_forecast(guild_id):
    lat, lon = get_lat_lon(guild_id)
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"daily=weathercode,temperature_2m_max,temperature_2m_min,"
        f"precipitation_probability_max,dewpoint_2m_min,windgusts_10m_max&"
        f"timezone=America/Chicago"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

async def fetch_current_conditions(guild_id):
    lat, lon = get_lat_lon(guild_id)
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"current_weather=true&timezone=America/Chicago"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

async def post_forecast(bot, guild_id):
    forecast_data = await fetch_forecast(guild_id)
    current_data = await fetch_current_conditions(guild_id)

    if "daily" not in forecast_data or "current_weather" not in current_data:
        print("⚠️ Failed to fetch forecast or current weather data")
        return

    days = forecast_data["daily"]["time"]
    highs_c = forecast_data["daily"]["temperature_2m_max"]
    lows_c = forecast_data["daily"]["temperature_2m_min"]
    codes = forecast_data["daily"]["weathercode"]
    pops = forecast_data["daily"]["precipitation_probability_max"]
    dews_c = forecast_data["daily"]["dewpoint_2m_min"]
    gusts = forecast_data["daily"].get("windgusts_10m_max", [None] * FORECAST_DAYS)

    current = current_data["current_weather"]
    temp_f = c_to_f(current["temperature"])
    wind_mph = ms_to_mph(current["windspeed"])
    wind_dir = current["winddirection"]
    conditions_code = interpret_weather_code(current["weathercode"])
    conditions_emoji = WEATHER_EMOJIS.get(conditions_code, "❓")

    city, state = get_city_state(guild_id)

    lines = []
    lines.append(f"**7-Day Forecast for {city}, {state}**\n")

    # Current Conditions
    lines.append(f"**Current Conditions at {city}, {state}**")
    lines.append(f"Current Forecast: {conditions_code.replace('_', ' ').title()} {conditions_emoji}")
    lines.append(f"Temperature: {temp_f}°F")
    lines.append(f"Wind Speed: {wind_dir}° at {wind_mph} mph")
    lines.append(f"Last update: {datetime.datetime.utcnow().strftime('%d %b %I:%M %p UTC')}\n")

    # 7-Day Forecast
    lines.append("**Detailed Forecast:**")
    for i in range(min(FORECAST_DAYS, len(days))):
        date = datetime.datetime.strptime(days[i], "%Y-%m-%d").strftime("%A")
        condition = interpret_weather_code(codes[i])
        emoji = WEATHER_EMOJIS.get(condition, "❓")
        high_f = c_to_f(highs_c[i])
        low_f = c_to_f(lows_c[i])
        dew_f = c_to_f(dews_c[i])
        pop = pops[i]
        gust_mph = f"{round(gusts[i])} mph" if gusts[i] is not None else "N/A"

        lines.append(f"\n**{date}:** {emoji}")
        lines.append(f"• High: {high_f}°F | Low: {low_f}°F")
        lines.append(f"• Dewpoint: {dew_f}°F | Precip: {pop}%")
        lines.append(f"• Gusts: {gust_mph}")

    forecast_text = "\n".join(lines)

    channel = bot.get_channel(FORECAST_CHANNEL_ID)
    if not channel:
        print("⚠️ Forecast channel not found!")
        return

    try:
        forecast_message = await channel.fetch_message(FORECAST_MESSAGE_ID)
        await forecast_message.edit(content=forecast_text)
        print("✅ Forecast message updated successfully.")
    except discord.NotFound:
        new_message = await channel.send(forecast_text)
        print("✅ Forecast message posted successfully (new message).")
    except Exception as e:
        print(f"❌ Failed to update forecast message: {e}")
