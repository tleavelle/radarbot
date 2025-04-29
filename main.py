import discord
import asyncio
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from alerts_watcher import process_alerts, clear_status
from daily_forecast import post_forecast
from daily_spc_outlook import post_spc_outlook
from radar_updater import radar_updater

# ======== CONFIGURATION ========
from config import DISCORD_TOKEN  # Removed token from public view
from config import SYSTEM_MESSAGES_CHANNEL_ID
# =================================

intents = discord.Intents.default()
intents.message_content = True  # Important for message editing
bot = discord.Client(intents=intents)

scheduler = AsyncIOScheduler()

async def send_heartbeat(bot):
    """Post a heartbeat message to the system messages channel."""
    channel = bot.get_channel(SYSTEM_MESSAGES_CHANNEL_ID)
    if channel:
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        await channel.send(f"✅ **Radarbot Heartbeat:** All systems operational as of {now} UTC.")
        print(f"💓 Heartbeat sent at {now} UTC")

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    await post_spc_outlook(bot)  # TEMP: run SPC outlook once on startup


    # Schedule the daily 7-day forecast at 7:00 AM
    scheduler.add_job(post_forecast, 'cron', hour=7, minute=0, args=[bot])

    # Schedule the daily SPC outlook at 7:05 AM
    scheduler.add_job(post_spc_outlook, 'cron', hour=7, minute=5, args=[bot])

    # Schedule alert checking every 2 minutes
    scheduler.add_job(process_alerts, 'interval', minutes=2, args=[bot])

    # Schedule quiet "all clear" check every 30 minutes
    scheduler.add_job(clear_status, 'interval', minutes=30, args=[bot])

    # Schedule bot heartbeat every 1 hour
    scheduler.add_job(send_heartbeat, 'interval', hours=1, args=[bot])

    # Start radar updater auto-loop
    bot.loop.create_task(radar_updater(bot))

    # Start the scheduler
    scheduler.start()

# Run the bot
bot.run(DISCORD_TOKEN)

