import discord
import aiohttp
import asyncio
import feedparser
import datetime

# --- CONFIGURATION ---
from config import ALERTS_CHANNEL_ID
from config import SEVERE_ROLE_ID
WATCHED_COUNTIES = [
    "Haskell", "Throckmorton", "Fisher", "Jones", "Shackleford", "Nolan", "Taylor", "Callahan",
    "Sterling", "Coke", "Runnels", "Coleman", "Brown", "Irion", "Tom Green", "Concho",
    "McCulloch", "San Saba", "Crockett", "Schleicher", "Menard", "Mason", "Sutton", "Kimble"
]
NOAA_FEED_URL = "https://api.weather.gov/alerts/active.atom?area=TX"

# Alert color mapping
ALERT_COLORS = {
    "Tornado Warning": 0xFF0000,
    "Severe Thunderstorm Warning": 0xFFFF00,
    "Flash Flood Warning": 0x00CED1,
    "Tornado Watch": 0xFFA500,
    "Severe Thunderstorm Watch": 0xFFA500,
    "Flood Warning": 0x00CED1,
}

# Track alerts we've already posted
posted_alerts = set()
last_alert_time = datetime.datetime.utcnow()

async def fetch_alerts():
    async with aiohttp.ClientSession() as session:
        async with session.get(NOAA_FEED_URL) as resp:
            text = await resp.text()
            feed = feedparser.parse(text)
            return feed.entries

async def process_alerts(bot):
    global last_alert_time

    entries = await fetch_alerts()
    for entry in entries:
        title = entry.title
        summary = entry.summary
        updated = entry.updated
        link = entry.link

        # Skip already posted alerts
        if link in posted_alerts:
            continue

        # Match only if the alert is in our counties
        if any(county in title for county in WATCHED_COUNTIES):
            last_alert_time = datetime.datetime.utcnow()
            posted_alerts.add(link)

            embed = discord.Embed(
                title=f"⚠️ {title}",
                description=summary,
                url=link,
                timestamp=datetime.datetime.utcnow(),
                color=get_alert_color(title)
            )
            embed.set_footer(text="Radarbot - Stay safe out there!")

            channel = bot.get_channel(ALERTS_CHANNEL_ID)
            role = f"<@&{SEVERE_ROLE_ID}>"

            if channel:
                await channel.send(role, embed=embed)

async def clear_status(bot):
    """Post 'No active warnings' if it's been quiet for a while."""
    global last_alert_time

    now = datetime.datetime.utcnow()
    difference = (now - last_alert_time).total_seconds()

    if difference > 3600:  # 1 hour without any alert
        channel = bot.get_channel(ALERTS_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="✅ No Active Warnings",
                description="There are currently no watches or warnings in effect.",
                timestamp=datetime.datetime.utcnow(),
                color=0x00FF00
            )
            embed.set_footer(text="Radarbot - Enjoy the calm!")
            await channel.send(embed=embed)
        last_alert_time = datetime.datetime.utcnow()  # Reset timer to avoid spam

def get_alert_color(title):
    """Decide color based on alert type."""
    for key, color in ALERT_COLORS.items():
        if key in title:
            return color
    return 0xFFFFFF  # Default to white if not matched
