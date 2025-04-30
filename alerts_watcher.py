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
            new_alerts.append((title, summary, link))
            last_alert_time = datetime.datetime.utcnow()

    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if new_alerts:
        lines = [f"🔴 **Active Severe Weather Alerts** ({len(new_alerts)} active)\n"]

        for title, summary, link in new_alerts:
            emoji = get_alert_emoji(title)
            title_line = f"**{emoji} [{title}]({link})**"
            lines.append(title_line)
            lines.append(f"*{summary.strip()}*")
            lines.append("")

        message_text = "\n".join(lines)
        if len(message_text) > 2000:
            message_text = message_text[:1997] + "..."

        await status_msg.edit(content=message_text)
        print(f"✅ Posted {len(new_alerts)} full alerts.")
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
        message_text = (
            "✅ **No Active Warnings**\n"
            "There are currently no watches or warnings in effect.\n"
            "Radarbot - Enjoy the calm!"
        )
        await status_msg.edit(content=message_text)
        print("🟢 Cleared alert status message to 'No Active Warnings'.")
        last_alert_time = datetime.datetime.utcnow()
    else:
        print("🕒 No need to clear status yet (recent alert).")

    try:
        await timestamp_msg.edit(content=f"📡 Last alert check: `{now_str} UTC`")
    except Exception as e:
        print(f"⚠️ Failed to update timestamp message during clear_status: {e}")
