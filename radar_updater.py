import discord
import datetime
import asyncio

# ======== CONFIGURATION ========
from config import RADAR_CHANNEL_ID

try:
    from config import RADAR_MESSAGE_ID
except ImportError:
    RADAR_MESSAGE_ID = None  # Allow first-time setup without it

RADAR_URL = 'https://radar.weather.gov/ridge/standard/KSJT_loop.gif'
UPDATE_INTERVAL = 300  # 5 minutes
# =================================

radar_message = None  # Will store the radar message object

async def radar_task(bot):
    """Posts and updates the live radar in the radar channel."""
    global radar_message

    channel = bot.get_channel(RADAR_CHANNEL_ID)
    if channel is None:
        print("⚠️ Radar channel not found.")
        return

    embed = discord.Embed(
        title="🌩️ Live West/Central Texas Radar",
        description=f"Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        color=discord.Color.blue()
    )
    embed.set_image(url=f"{RADAR_URL}?{datetime.datetime.now().timestamp()}")  # Cache-busting URL

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
            # First ever run: no ID available
            print("⚠️ No RADAR_MESSAGE_ID set. Posting radar for the first time...")
            radar_message = await channel.send(embed=embed)
            print(f"📌 First-time radar message posted. ID: {radar_message.id}")
            print("👉 Please copy this ID and add it to your config.py as RADAR_MESSAGE_ID.")
    else:
        try:
            await radar_message.edit(embed=embed)
            print(f"✅ Radar updated at {datetime.datetime.now()}")
        except Exception as e:
            print(f"❌ Failed to update radar message: {e}")

async def radar_updater(bot):
    """Looping task to refresh radar every UPDATE_INTERVAL seconds."""
    await bot.wait_until_ready()
    print("🔄 radar_updater loop started.")
    while not bot.is_closed():
        try:
            await radar_task(bot)
        except Exception as e:
            print(f"❌ Unhandled error in radar updater loop: {e}")
        await asyncio.sleep(UPDATE_INTERVAL)
