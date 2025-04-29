import discord
import aiohttp
import datetime

# --- CONFIGURATION ---
from config import FORECAST_CHANNEL_ID
LATITUDE = 31.4638  # Replace with your target location latitude (example: San Angelo, TX)
LONGITUDE = -100.4370  # Replace with your longitude
FORECAST_DAYS = 7

# Emoji icons based on weather codes
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

async def fetch_forecast():
    """Fetch 7-day forecast data from Open-Meteo API."""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LATITUDE}&longitude={LONGITUDE}&"
        f"daily=weathercode,temperature_2m_max,temperature_2m_min&"
        f"timezone=America/Chicago"
    )

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()

def interpret_weather_code(code):
    """Map Open-Meteo weather code to simple emojis/text."""
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

async def post_forecast(bot):
    forecast_data = await fetch_forecast()

    if "daily" not in forecast_data:
        print("Failed to fetch forecast data")
        return

    days = forecast_data["daily"]["time"]
    highs = forecast_data["daily"]["temperature_2m_max"]
    lows = forecast_data["daily"]["temperature_2m_min"]
    codes = forecast_data["daily"]["weathercode"]

    embed = discord.Embed(
        title=f"📅 Forecast for {datetime.datetime.now().strftime('%A, %B %d')}",
        description="Here's the 7-day weather outlook:",
        timestamp=datetime.datetime.utcnow(),
        color=0x1E90FF  # Nice light blue
    )
    embed.set_footer(text="Radarbot - Forecast powered by Open-Meteo")

    for i in range(min(FORECAST_DAYS, len(days))):
        date = datetime.datetime.strptime(days[i], "%Y-%m-%d").strftime("%a %b %d")
        condition = interpret_weather_code(codes[i])
        emoji = WEATHER_EMOJIS.get(condition, "❓")
        high = highs[i]
        low = lows[i]

        embed.add_field(
            name=f"{emoji} {date}",
            value=f"High: {high}°F\nLow: {low}°F",
            inline=True
        )

    channel = bot.get_channel(FORECAST_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)
