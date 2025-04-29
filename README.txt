# ☁️ Radarbot

A live weather alert Discord bot that monitors radar, posts real-time watches and warnings, daily forecasts, and daily SPC severe weather outlooks!

Built for Central Texas monitoring, but can be customized for any NOAA region.  
**Developed and maintained by [Taylor Leavelle](https://github.com/tleavelle).**

---

## 🚀 Features

- 📡 **Live Radar Updates** every 5 minutes
- ⚡ **Automatic Watches and Warnings** posting (NOAA feed parsing)
- 🗓️ **Daily 7-Day Forecast** posting to a dedicated channel
- 🛡️ **Daily SPC Severe Weather Risk Map** posting
- 🕒 **Scheduled Tasks** using APScheduler
- 🧠 **No interaction needed** — fully automatic
- 🔒 **Private config file** for secure Discord token management

---

## 🛠 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/tleavelle/radarbot.git
cd radarbot

### 2. Install required libraries
```bash
pip install discord.py aiohttp feedparser apscheduler

### 3. Create your config.py file
```bash
sudo nano config.py

### 4. Put this inside "config.py":
DISCORD_TOKEN = "your-discord-bot-token-here"

### 5. Launch the bot
```bash
chmod +x launch.sh 
./launch.sh 

radarbot/
├── alerts_watcher.py     # Watches for NOAA alerts and warnings
├── daily_forecast.py     # Posts daily 7-day forecast
├── daily_spc_outlook.py  # Posts daily SPC severe outlook maps
├── radar_updater.py      # Live radar image updater
├── main.py               # Main bot runner and scheduler
├── launch.sh             # Easy manual startup script
├── .gitignore            # Ignores config.py and __pycache__
└── README.md             # This file!