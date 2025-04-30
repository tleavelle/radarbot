import discord
import aiohttp
import asyncio
import feedparser
import datetime

# --- CONFIGURATION ---
from config import ALERTS_CHANNEL_ID, ALERT_STATUS_MESSAGE_ID, ALERT_TIMESTAMP_MESSAGE_ID

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
alert_message_ids = []  # Messages created for alerts (to be deleted later)

async def fetch_alerts():
    async with aiohttp.ClientSession() as session:
        async with session.get(NOAA_FEED_URL) as resp:
            text = await resp.text()
            feed = feedparser.parse(text)
            return feed.entries

async def process_alerts(bot):
    global last_alert_time, alert_message_ids

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

    # Always clear embed just in case
    await status_msg.edit(content="🔄 Checking for new alerts...", embed=None)

    # Delete previously posted alert messages
    for msg_id in alert_message_ids:
        try:
            msg = await channel.fetch_message(msg_id)
            await msg.delete()
        except Exception:
            pass
    alert_message_ids.clear()

    entries = await fetch_alerts()
    new_alerts = []

    for entry in entries:
        title = entry.title
        summary = entry.summary
        link = entry.link
        area = entry.get("cap_areadesc", "")

        if any(county.lower() in f"{title} {summary} {area}".lower() for county in WATCHED_COUNTIES):
            new_alerts.append((title, summary, link))
            last_alert_time = datetime.datetime.utcnow()

    now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if new_alerts:
        pointer_text = f"🔴 **{len(new_alerts)} Active Severe Weather Alert(s)**\n⚠️ See messages below ⬇️"
        await status_msg.edit(content=pointer_text, embed=None)

        chunks = []
        current = ""

        for title, summary, link in new_alerts:
            emoji = get_alert_emoji(title)
            alert_text = f"**{emoji} [{title}]({link})**\n*{summary.strip()}*\n\n"
            if len(current) + len(alert_text) > 2000:
                chunks.append(current)
                current = alert_text
            else:
                current += alert_text

        if current:
            chunks.append(current)

        for chunk in chunks:
            msg = await channel.send(chunk)
            alert_message_ids.append(msg.id)

        print(f"✅ Posted {len(new_alerts)} alerts across {len(chunks)} messages.")
    else:
        last_alert_time = datetime.datetime.utcnow()
        await status_msg.edit(content="✅ **No Active Warnings**\nRadarbot - Enjoy the calm!", embed=None)
        print("🟢 No alerts found — status message cleared.")

    try:
        await timestamp_msg.edit(content=f"📡 Last alert check: `{now_str} UTC`")
    except Exception as e:
        print(f"⚠️ Failed to update timestamp message: {e}")

async def clear_status(bot):
    global last_alert_time, alert_message_ids

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
        for msg_id in alert_message_ids:
            try:
                msg = await channel.fetch_message(msg_id)
                await msg.delete()
            except Exception:
                pass
        alert_message_ids.clear()

        await status_msg.edit(content="✅ **No Active Warnings**\nRadarbot - Enjoy the calm!", embed=None)
        print("🟢 Cleared alert messages and updated status.")
        last_alert_time = datetime.datetime.utcnow()
    else:
        print("🕒 No need to clear status yet (recent alert).")

    try:
        await timestamp_msg.edit(content=f"📡 Last alert check: `{now_str} UTC`")
    except Exception as e:
        print(f"⚠️ Failed to update timestamp message during clear_status: {e}")
