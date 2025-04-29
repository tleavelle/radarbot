import discord
import datetime
import asyncio

# ======== CONFIGURATION ========
from config import RADAR_CHANNEL_ID, RADAR_MESSAGE_ID  # Add RADAR_MESSAGE_ID to config.py
RADAR_URL = 'https://radar.weather.gov/ridge/standard/KSJT_loop.gif'
UPDATE_INTERVAL = 300  # Update every 5 minutes
# =================================

radar_message = None  # Cached radar message object

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
    embed.set_image(url=f"{RADAR_URL}?{datetime.datetime.now().timestamp()}")  # Cache-busting

    if radar_message is None:
        try:
            radar_message = await channel.fetch_message(RADAR_MESSAGE_ID)
            await radar_message.edit(embed=embed)
            print(f"✅ Radar message updated at {datetime.datetime.now()}")
        except discord.NotFound:
            # If message not found, post a new one and log warning
            radar_message = await channel.send(embed=embed)
            print(f"⚠️ Radar message ID not found — new message posted at {datetime.datetime.now()}")
        except Exception as e:
            print(f"❌ Failed to fetch or update radar message: {e}")
    else:
        try:
            await radar_message.edit(embed=embed)
            print(f"✅ Radar updated at {datetime.datetime.now()}")
        except Exception as e:
            print(f"❌ Failed to update radar: {e}")

async def radar_updater(bot):
    """Looping task to refresh radar every UPDATE_INTERVAL seconds."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        try:
            await radar_task(bot)
        except Exception as e:
            print(f"❌ Unhandled error in radar updater loop: {e}")
        await asyncio.sleep(UPDATE_INTERVAL)

