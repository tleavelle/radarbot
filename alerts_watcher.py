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

def get_alert_emoji(title):
    """Return an appropriate emoji based on alert type."""
    title = title.lower()
    if "tornado" in title:
        return "🌪"
    elif "severe thunderstorm" in title:
        return "🌩"
    elif "flood" in title:
        return "🌊"
    else:
        return "⚠️"

# Track alerts we've already posted
posted_alerts = set()
last_alert_time = datetime.datetime.utcnow()

# Track the status message so we can update it
alert_status_message_id = None  # Will store message ID after first post

async def fetch_alerts():
    async with aiohttp.ClientSession() as session:
        async with session.get(NOAA_FEED_URL) as resp:
            text = await resp.text()
            feed = feedparser.parse(text)
            return feed.entries

async def process_alerts(bot):
    global last_alert_time, alert_status_message_id

    new_alert_posted = False

    entries = await fetch_alerts()
    for entry in entries:
        title = entry.title
        summary = entry.summary
        updated = entry.updated
        link = entry.link

        if link in posted_alerts:
            continue

        if any(county in title for county in WATCHED_COUNTIES):
            last_alert_time = datetime.datetime.utcnow()
            posted_alerts.add(link)

            emoji = get_alert_emoji(title)
            header = f"{emoji}  | NWS | `{title}`"

            channel = bot.get_channel(ALERTS_CHANNEL_ID)
            role_mention = f"<@&{SEVERE_ROLE_ID}>"

            if channel:
                final_message = f"""{header}

{role_mention}
{summary}"""

                await channel.send(final_message)
                print(f"✅ Posted alert: {title}")

            new_alert_posted = True

    # Update or create the status message
    channel = bot.get_channel(ALERTS_CHANNEL_ID)
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    status_text = f"📡 Last alert check: `{now} UTC`"

    if channel:
        try:
            if alert_status_message_id:
                msg = await channel.fetch_message(alert_status_message_id)
                await msg.edit(content=status_text)
            else:
                status_msg = await channel.send(status_text)
                alert_status_message_id = status_msg.id
        except Exception as e:
            print(f"⚠️ Could not edit or send status message: {e}")

    if not new_alert_posted:
        print(f"🕒 Checked alerts at {now} UTC, no new alerts found.")

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
        last_alert_time = datetime.datetime.utcnow()

def get_alert_color(title):
    for key, color in ALERT_COLORS.items():
        if key in title:
            return color
    return 0xFFFFFF
