import discord
import datetime
from alerts_watcher import process_alerts
from config import SYSTEM_MESSAGES_CHANNEL_ID, GUILD_ID
from daily_forecast import post_forecast

def setup_commands(bot):
    @bot.tree.command(name="heartbeat", description="Manually send a Radarbot heartbeat.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def heartbeat(interaction: discord.Interaction):
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        channel = bot.get_channel(SYSTEM_MESSAGES_CHANNEL_ID)
        if channel:
            await channel.send(f"✅ **Radarbot Heartbeat:** Manual heartbeat as of {now} UTC.")
            await interaction.response.send_message(f"💓 Heartbeat sent at {now} UTC!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Could not find system messages channel.", ephemeral=True)

    @bot.tree.command(name="checkalerts", description="Manually check for severe weather alerts.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def check_alerts(interaction: discord.Interaction):
        await process_alerts(bot)  # Pass the bot correctly
        await interaction.response.send_message("📡 Manual alert check completed.", ephemeral=True)

    @bot.tree.command(name="status", description="Get Radarbot system status.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def status(interaction: discord.Interaction):
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        await interaction.response.send_message(f"✅ Radarbot is online. Current UTC time: `{now}`", ephemeral=True)

    @bot.tree.command(name="forecast", description="Manually post or update the 7-day forecast.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def forecast(interaction: discord.Interaction):
        await post_forecast(bot)
        await interaction.response.send_message("🌤️ Forecast posted/updated successfully.", ephemeral=True)
