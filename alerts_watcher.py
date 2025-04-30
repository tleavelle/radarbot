import discord
import aiohttp
import asyncio
import feedparser
import datetime

# --- CONFIGURATION ---
from config import ALERTS_CHANNEL_ID, SEVERE_ROLE_ID, ALERT_STATUS_MESSAGE_ID, ALERT_TIMESTAMP_MESSAGE_ID

WATCHED_COUNTIES = [
    "Haskell", "Throckmorton", "Fisher", "Jones", "Shackleford", "Nolan", "Taylor", "Callahan",
    "Sterling", "Coke", "Runnels", "Coleman", "Brown", "Irion", "Tom Green", "Concho",
    "McCulloch", "San Saba", "Crockett", "Schleicher", "Menard", "Mason", "Sutton", "Kimble"
]
NOAA_FEED_URL = "https://api.weather.gov/alerts/active.atom?area=TX"

ALERT_COLORS = {
    "Tornado Warning": 0xFF0000,
    "Severe Thunderstorm Warning": 0xFFFF00,
    "Flash Flood Warning": 0x00CED1,
    "Tornado Watch": 0xFFA500,
    "Severe Thunderstorm Watch": 0xFFA500,
    "Flood Warning": 0x00CED1,
}

def get_alert_emoji(title):
    title = title.lower()
    if "tornado" in title:
        return "🌪"
    elif "severe thunderstorm" in title:
        return "🌩"
    elif "flood" in title:
        return "🌊"
    else:
        return "⚠️"

def get_alert_color(title):
    for key, color in ALERT_COLORS.items():
        if key in title:
            return color
    return 0xFFFFFF

# Track posted alerts
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

    channel = bot.get_channel(ALERTS_CHANNEL_ID)
    if not channel:
        print("⚠️ Alert channel not found.")
        return

    try:
        status_msg = await channel.fetch_message(ALERT_STATUS_MESSAGE_ID)
        timestamp_msg = await channel.fetch_message(ALERT_TIMESTAMP_MESSAGE_ID)
    except Exception as e:
        print(f"❌ Failed to fetch status or timestamp messages: {e}")
        return

    entries = await fetch_alerts()
    new_alerts = []

    for entry in entries:
        title = entry.title
        summary = entry.summary
        link = entry.link
        area = entry.get("cap_areadesc", "")

        if link in posted_alerts:
            continue

        combined_text = f"{title} {summary} {area}"
        if any(county.lower() in combined_text.lower() for county in WATCHED_COUNTIES):
            posted_alerts.add(link)
            new_alerts.append((title, summary))
            last_alert_time = datetime.datetime.utcnow()

    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if new_alerts:
        embed = discord.Embed(
            title="🔴 Active Severe Weather Alerts",
            description=f"{len(new_alerts)} active alert(s) for monitored counties.",
            timestamp=datetime.datetime.utcnow(),
            color=0xFF0000
        )

        total_length = len(embed.title) + len(embed.description)
        max_embed_length = 6000
        cutoff_triggered = False

        for title, summary in new_alerts:
            emoji = get_alert_emoji(title)

            # 🧠 Smart line extraction for better location context
            lines = summary.splitlines()
            key_lines = [line for line in lines if line.strip().startswith(("At", "WHAT", "...", "THE NATIONAL WEATHER SERVICE"))]
            condensed = key_lines[0].strip() if key_lines else lines[0].strip()
            if len(condensed) > 350:
                condensed = condensed[:347] + "..."

            field_name = f"{emoji} {title}"
            field_value = condensed
            field_len = len(field_name) + len(field_value)

            if total_length + field_len >= max_embed_length:
                cutoff_triggered = True
                break

            embed.add_field(name=field_name, value=field_value, inline=False)
            total_length += field_len

        if cutoff_triggered:
            embed.set_footer(text=f"⚠️ Showing first alerts only (Discord limit hit) • Radarbot")
        else:
            embed.set_footer(text="Radarbot – Stay safe!")

        await status_msg.edit(content=None, embed=embed)
        print(f"✅ Posted {len(embed.fields)} alert(s) to embed.")
    else:
        print(f"🕒 Checked alerts at {now}, no new alerts found.")
        last_alert_time = datetime.datetime.utcnow()

    try:
        await timestamp_msg.edit(content=f"📡 Last alert check: `{now} UTC`")
    except Exception as e:
        print(f"⚠️ Failed to update timestamp message: {e}")

async def clear_status(bot):
    global last_alert_time

    channel = bot.get_channel(ALERTS_CHANNEL_ID)
    if not channel:
        return

    try:
        status_msg = await channel.fetch_message(ALERT_STATUS_MESSAGE_ID)
        timestamp_msg = await channel.fetch_message(ALERT_TIMESTAMP_MESSAGE_ID)
    except Exception as e:
        print(f"❌ Failed to fetch status or timestamp messages: {e}")
        return

    now = datetime.datetime.utcnow()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    difference = (now - last_alert_time).total_seconds()

    if difference > 3600:
        embed = discord.Embed(
            title="✅ No Active Warnings",
            description="There are currently no watches or warnings in effect.",
            timestamp=datetime.datetime.utcnow(),
            color=0x00FF00
        )
        embed.set_footer(text="Radarbot - Enjoy the calm!")
        await status_msg.edit(content=None, embed=embed)
        print("🟢 Cleared alert status message to 'No Active Warnings'.")
        last_alert_time = datetime.datetime.utcnow()
    else:
        print("🕒 No need to clear status yet (recent alert).")

    try:
        await timestamp_msg.edit(content=f"📡 Last alert check: `{now_str} UTC`")
    except Exception as e:
        print(f"⚠️ Failed to update timestamp message during clear_status: {e}")
