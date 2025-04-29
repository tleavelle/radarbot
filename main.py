import discord
from discord.ext import commands
import asyncio
import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from alerts_watcher import process_alerts, clear_status
from daily_forecast import post_forecast
from daily_spc_outlook import post_spc_outlook
from radar_updater import radar_updater
from commands import setup_commands  # Slash command setup

# ======== CONFIGURATION ========
from config import DISCORD_TOKEN
from config import SYSTEM_MESSAGES_CHANNEL_ID, GUILD_ID
# =================================

# --- INTENTS ---
intents = discord.Intents.default()
intents.message_content = True  # Required to edit messages

# --- CREATE BOT ---
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
scheduler = AsyncIOScheduler()

# --- FUNCTIONS ---
async def send_heartbeat(bot):
    """Post a heartbeat message to the system messages channel."""
    channel = bot.get_channel(SYSTEM_MESSAGES_CHANNEL_ID)
    if channel:
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        await channel.send(f"✅ **Radarbot Heartbeat:** All systems operational as of {now} UTC.")
        print(f"💓 Heartbeat sent at {now} UTC")
    else:
        print("⚠️ Could not find the system messages channel to send heartbeat.")

# --- EVENTS ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    # Setup slash command handlers BEFORE syncing
    setup_commands(bot)

    # Register slash commands ONLY for your guild
    try:
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"🛡️ Slash commands synced to guild ID: {GUILD_ID}")
    except Exception as e:
        print(f"⚠️ Failed to sync slash commands: {e}")

    # Schedule the daily 7-day forecast at 7:00 AM
    scheduler.add_job(post_forecast, 'cron', hour=7, minute=0, args=[bot])

    # Schedule the daily SPC outlook at 7:05 AM
    scheduler.add_job(post_spc_outlook, 'cron', hour=7, minute=5, args=[bot])

    # Schedule alert checking every 2 minutes
    scheduler.add_job(process_alerts, 'interval', minutes=2, args=[bot])

    # Schedule quiet "all clear" check every 30 minutes
    scheduler.add_job(clear_status, 'interval', minutes=30, args=[bot])

    # Schedule bot heartbeat every 24 hours
    scheduler.add_job(send_heartbeat, 'interval', hours=24, args=[bot])

    # Start radar updater auto-loop
    bot.loop.create_task(radar_updater(bot))

    # Start the scheduler
    scheduler.start()

    print("🗓️ Scheduler and radar updater started.")

# --- RUN BOT ---
bot.run(DISCORD_TOKEN)
