import discord
import datetime
import asyncio

# ======== CONFIGURATION ========
from config import RADAR_CHANNEL_ID  # Target channel ID
RADAR_URL = 'https://radar.weather.gov/ridge/standard/KSJT_loop.gif'  # Radar image URL
UPDATE_INTERVAL = 300  # Update every 5 minutes (300 seconds)
# =================================

radar_message = None  # Global to keep track of the radar message

async def radar_task(bot):
    """Posts and updates the live radar in the radar channel."""
    global radar_message

    channel = bot.get_channel(RADAR_CHANNEL_ID)
    if channel is None:
        print("Radar channel not found.")
        return

    if radar_message is None:
        # First time: send a new message
        embed = discord.Embed(
            title="🌩️ Live West/Central Texas Radar",
            description=f"Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            color=discord.Color.blue()
        )
        embed.set_image(url=f"{RADAR_URL}?{datetime.datetime.now().timestamp()}")

        radar_message = await channel.send(embed=embed)
        print(f"Radar initially posted at {datetime.datetime.now()}")
    else:
        # Update existing message
        embed = discord.Embed(
            title="🌩️ Live West/Central Texas Radar",
            description=f"Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            color=discord.Color.blue()
        )
        embed.set_image(url=f"{RADAR_URL}?{datetime.datetime.now().timestamp()}")

        try:
            await radar_message.edit(embed=embed)
            print(f"Radar updated at {datetime.datetime.now()}")
        except Exception as e:
            print(f"Failed to update radar: {e}")

async def radar_updater(bot):
    """Looping task to refresh radar every UPDATE_INTERVAL seconds."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        await radar_task(bot)
        await asyncio.sleep(UPDATE_INTERVAL)
