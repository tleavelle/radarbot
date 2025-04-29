import discord
import datetime
import asyncio

from config import RADAR_CHANNEL_ID
from location_manager import get_lat_lon
from nexrad_locator import get_nearest_station

try:
    from config import RADAR_MESSAGE_ID
except ImportError:
    RADAR_MESSAGE_ID = None

UPDATE_INTERVAL = 300  # 5 minutes

radar_message = None  # Will store the radar message object

async def radar_task(bot, guild_id):
    global radar_message

    channel = bot.get_channel(RADAR_CHANNEL_ID)
    if channel is None:
        print("⚠️ Radar channel not found.")
        return

    lat, lon = get_lat_lon(guild_id)
    nearest_station = get_nearest_station(lat, lon)

    radar_url = f"https://radar.weather.gov/ridge/standard/{nearest_station}_loop.gif"

    embed = discord.Embed(
        title=f"🌩️ Live Radar near {nearest_station}",
        description=f"Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        color=discord.Color.blue()
    )
    embed.set_image(url=f"{radar_url}?{datetime.datetime.now().timestamp()}")

    if radar_message is None:
        if RADAR_MESSAGE_ID is not None:
            try:
                radar_message = await channel.fetch_message(RADAR_MESSAGE_ID)
                await radar_message.edit(embed=embed)
                print(f"✅ Radar message updated at {datetime.datetime.now()}")
            except discord.NotFound:
                print("⚠️ RADAR_MESSAGE_ID not found. Posting new radar message...")
                radar_message = await channel.send(embed=embed)
                print(f"📌 New radar message posted. ID: {radar_message.id}")
                print("👉 Please add this ID to your config.py as RADAR_MESSAGE_ID.")
        else:
            radar_message = await channel.send(embed=embed)
            print(f"📌 First-time radar message posted. ID: {radar_message.id}")
            print("👉 Please copy this ID and add it to config.py as RADAR_MESSAGE_ID.")
    else:
        try:
            await radar_message.edit(embed=embed)
            print(f"✅ Radar updated at {datetime.datetime.now()}")
        except Exception as e:
            print(f"❌ Failed to update radar message: {e}")

async def radar_updater(bot, guild_id):
    """Looping task to refresh radar every UPDATE_INTERVAL seconds."""
    await bot.wait_until_ready()
    print("🔄 radar_updater loop started.")
    while not bot.is_closed():
        try:
            await radar_task(bot, guild_id)
        except Exception as e:
            print(f"❌ Unhandled error in radar updater loop: {e}")
        await asyncio.sleep(UPDATE_INTERVAL)
