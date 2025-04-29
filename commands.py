import discord
import datetime
from alerts_watcher import process_alerts
from config import SYSTEM_MESSAGES_CHANNEL_ID
from daily_forecast import post_forecast

def setup_commands(bot):
    @bot.slash_command(name="heartbeat", description="Manually send a Radarbot heartbeat.")
    async def heartbeat(ctx):
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        channel = bot.get_channel(SYSTEM_MESSAGES_CHANNEL_ID)
        if channel:
            await channel.send(f"✅ **Radarbot Heartbeat:** Manual heartbeat as of {now} UTC.")
            await ctx.respond(f"💓 Heartbeat sent at {now} UTC!", ephemeral=True)
        else:
            await ctx.respond("⚠️ Could not find system messages channel.", ephemeral=True)

    @bot.slash_command(name="checkalerts", description="Manually check for severe weather alerts.")
    async def check_alerts(ctx):
        await process_alerts(bot)
        await ctx.respond("📡 Manual alert check completed.", ephemeral=True)

    @bot.slash_command(name="status", description="Get Radarbot system status.")
    async def status(ctx):
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        await ctx.respond(f"✅ Radarbot is online. Current UTC time: `{now}`", ephemeral=True)

    @bot.slash_command(name="forecast", description="Manually post or update the 7-day forecast.")
    async def forecast(ctx):
        await post_forecast(bot)
        await ctx.respond("🌤️ Forecast posted/updated successfully.", ephemeral=True)