import discord
import datetime
from alerts_watcher import process_alerts
from config import SYSTEM_MESSAGES_CHANNEL_ID, GUILD_ID
from daily_forecast import post_forecast
from location_manager import save_location, get_lat_lon, get_city_state, get_station_id
from nexrad_locator import get_nearest_station
from server_config_manager import set_server_config, get_server_config

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
        await process_alerts(bot)
        await interaction.response.send_message("📡 Manual alert check completed.", ephemeral=True)

    @bot.tree.command(name="status", description="Get Radarbot system status.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def status(interaction: discord.Interaction):
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        await interaction.response.send_message(f"✅ Radarbot is online. Current UTC time: `{now}`", ephemeral=True)

    @bot.tree.command(name="forecast", description="Manually post or update the 7-day forecast.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def forecast(interaction: discord.Interaction):
        await post_forecast(bot, interaction.guild.id)
        await interaction.response.send_message("🌤️ Forecast posted/updated successfully.", ephemeral=True)

    @bot.tree.command(name="ping", description="Check if Radarbot is alive and get current UTC time.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def ping(interaction: discord.Interaction):
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        await interaction.response.send_message(f"🏓 Pong! Radarbot is alive.\n🕒 Current UTC time: `{now}`", ephemeral=True)

    @bot.tree.command(name="setlocation", description="Set the bot's location using coordinates, city/state, or station ID.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setlocation(interaction: discord.Interaction,
                          lat: float = None,
                          lon: float = None,
                          city: str = None,
                          state: str = None,
                          station_id: str = None):
        guild_id = interaction.guild.id

        if station_id:
            save_location(guild_id, station_id=station_id.upper())
            await interaction.response.send_message(
                f"✅ Station override set to `{station_id.upper()}`.\n"
                f"Radarbot will now use this station directly.",
                ephemeral=True
            )

        elif lat is not None and lon is not None:
            save_location(guild_id, lat=lat, lon=lon)
            nearest_radar = get_nearest_station(lat, lon)
            await interaction.response.send_message(
                f"✅ Location set to coordinates: `{lat}, {lon}`\n"
                f"🛰️ Nearest Radar: `{nearest_radar}`",
                ephemeral=True
            )

        elif city and state:
            save_location(guild_id, city=city, state=state)
            lat, lon = get_lat_lon(guild_id)
            nearest_radar = get_nearest_station(lat, lon)
            await interaction.response.send_message(
                f"✅ Location set to: `{city}, {state}`\n"
                f"🛰️ Nearest Radar: `{nearest_radar}`",
                ephemeral=True
            )

        else:
            await interaction.response.send_message(
                "⚠️ You must provide one of the following:\n"
                "• `lat` + `lon`\n"
                "• `city` + `state`\n"
                "• `station_id` (e.g. `KJST`, `KDFW`)",
                ephemeral=True
            )

    @bot.tree.command(name="location", description="Show the bot's current saved location.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def location(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        lat, lon = get_lat_lon(guild_id)
        city, state = get_city_state(guild_id)
        station_id = get_station_id(guild_id)

        station_text = f"🛰️ **Using Overridden Radar Station:** `{station_id}`" if station_id else \
                       f"🛰️ Nearest Radar: `{get_nearest_station(lat, lon)}`"

        await interaction.response.send_message(
            f"📍 **Current Location Settings**\n"
            f"• City/State: `{city}, {state}`\n"
            f"• Coordinates: `{lat}, {lon}`\n"
            f"{station_text}",
            ephemeral=True
        )

    @bot.tree.command(name="setchannels", description="Set the Radarbot channels for this server.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setchannels(interaction: discord.Interaction,
                          radar_channel: discord.TextChannel,
                          forecast_channel: discord.TextChannel,
                          alerts_channel: discord.TextChannel,
                          system_channel: discord.TextChannel):
        guild_id = interaction.guild.id
        set_server_config(
            guild_id,
            radar_channel=radar_channel.id,
            forecast_channel=forecast_channel.id,
            alerts_channel=alerts_channel.id,
            system_channel=system_channel.id
        )
        await interaction.response.send_message("✅ Server channels updated successfully!", ephemeral=True)

    @bot.tree.command(name="setrole", description="Set the severe weather alert role for this server.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def setrole(interaction: discord.Interaction, severe_role: discord.Role):
        guild_id = interaction.guild.id
        set_server_config(guild_id, severe_role=severe_role.id)
        await interaction.response.send_message("✅ Severe role updated successfully!", ephemeral=True)

    @bot.tree.command(name="viewconfig", description="View the Radarbot configuration for this server.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def viewconfig(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        config = get_server_config(guild_id)

        embed = discord.Embed(
            title="📋 Radarbot Server Configuration",
            color=discord.Color.blue()
        )
        embed.add_field(name="Radar Channel", value=f"<#{config['radar_channel']}>" if config['radar_channel'] else "Not Set", inline=False)
        embed.add_field(name="Forecast Channel", value=f"<#{config['forecast_channel']}>" if config['forecast_channel'] else "Not Set", inline=False)
        embed.add_field(name="Alerts Channel", value=f"<#{config['alerts_channel']}>" if config['alerts_channel'] else "Not Set", inline=False)
        embed.add_field(name="System Messages Channel", value=f"<#{config['system_channel']}>" if config['system_channel'] else "Not Set", inline=False)
        embed.add_field(name="Severe Role", value=f"<@&{config['severe_role']}>" if config['severe_role'] else "Not Set", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="neareststation", description="Show the radar station currently in use.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def neareststation(interaction: discord.Interaction):
        guild_id = interaction.guild.id
        station_id = get_station_id(guild_id)

        if station_id:
            await interaction.response.send_message(
                f"🛰️ **Radar Station Override is Active**\n"
                f"Using manually set station: `{station_id}`",
                ephemeral=True
            )
        else:
            lat, lon = get_lat_lon(guild_id)
            nearest = get_nearest_station(lat, lon)
            await interaction.response.send_message(
                f"🛰️ **Nearest NEXRAD Station (based on coordinates):** `{nearest}`",
                ephemeral=True
            )

    @bot.tree.command(name="help", description="Show a list of all Radarbot commands.")
    @discord.app_commands.guilds(discord.Object(id=GUILD_ID))
    async def help(interaction: discord.Interaction):
        embed = discord.Embed(
            title="📖 Radarbot Command Reference",
            description="Here are the commands you can use with Radarbot:",
            color=discord.Color.green()
        )

        embed.add_field(
            name="/setlocation",
            value="Set the bot's location using coordinates, city/state, or station ID.",
            inline=False
        )
        embed.add_field(
            name="/location",
            value="View the currently saved location and radar source.",
            inline=False
        )
        embed.add_field(
            name="/neareststation",
            value="Show the radar station currently in use.",
            inline=False
        )
        embed.add_field(
            name="/forecast",
            value="Post or update the full 7-day forecast for this server.",
            inline=False
        )
        embed.add_field(
            name="/checkalerts",
            value="Manually check for severe weather alerts now.",
            inline=False
        )
        embed.add_field(
            name="/setchannels",
            value="Set where Radarbot posts radar, forecasts, and alerts.",
            inline=False
        )
        embed.add_field(
            name="/setrole",
            value="Set the role to ping for severe weather alerts.",
            inline=False
        )
        embed.add_field(
            name="/viewconfig",
            value="See your server's full Radarbot configuration.",
            inline=False
        )
        embed.add_field(
            name="/heartbeat",
            value="Manually trigger a bot heartbeat message.",
            inline=False
        )
        embed.add_field(
            name="/ping",
            value="Check if Radarbot is online and show the current UTC time.",
            inline=False
        )

        embed.set_footer(text="Radarbot by W5QX • Stay weather-aware! 🌩️")

        await interaction.response.send_message(embed=embed, ephemeral=True)
