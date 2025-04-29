import discord
import aiohttp
import datetime

# --- CONFIGURATION ---
FORECAST_CHANNEL_ID = 1366548989071200347

SPC_DAY1_IMAGE_URL = "https://www.spc.noaa.gov/products/outlook/day1otlk.png"
SPC_DAY2_IMAGE_URL = "https://www.spc.noaa.gov/products/outlook/day2otlk.png"

SPC_TEXT_URL_DAY1 = "https://www.spc.noaa.gov/products/outlook/day1otlk.txt"
SPC_TEXT_URL_DAY2 = "https://www.spc.noaa.gov/products/outlook/day2otlk.txt"

async def fetch_outlook_summary(url):
    """Fetch short risk summary from SPC text products."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            text = await resp.text()

    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith("...") and line.endswith("..."):
            return line.strip(".")  # Remove leading/trailing dots
    return "No risk summary available."

async def post_spc_outlook(bot):
    today_summary = await fetch_outlook_summary(SPC_TEXT_URL_DAY1)
    tomorrow_summary = await fetch_outlook_summary(SPC_TEXT_URL_DAY2)

    embed = discord.Embed(
        title="🌩️ SPC Severe Weather Outlook",
        description=(
            f"**Today:** {today_summary}\n"
            f"**Tomorrow:** {tomorrow_summary}"
        ),
        timestamp=datetime.datetime.utcnow(),
        color=0xFF9900  # Orange-ish color for SPC risk
    )
    embed.set_footer(text="Radarbot - SPC Risk Outlook")
    
    embed.set_image(url=SPC_DAY1_IMAGE_URL)
    embed.add_field(name="Tomorrow's Outlook:", value=f"[Click to view Day 2 Outlook Image]({SPC_DAY2_IMAGE_URL})", inline=False)

    channel = bot.get_channel(FORECAST_CHANNEL_ID)
    if channel:
        await channel.send(embed=embed)
