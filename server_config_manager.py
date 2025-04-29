import json
import os

CONFIG_FILE = "server_configs.json"

default_config = {
    "radar_channel": None,
    "forecast_channel": None,
    "alerts_channel": None,
    "system_channel": None,
    "severe_role": None
}

def load_all_server_configs():
    """Load all server configs from file."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Failed to load server config: {e}")
        return {}

def save_all_server_configs(configs):
    """Save all server configs to file."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(configs, f, indent=4)
        print("✅ Server configs saved successfully.")
    except Exception as e:
        print(f"❌ Failed to save server configs: {e}")

def get_server_config(guild_id):
    configs = load_all_server_configs()
    return configs.get(str(guild_id), default_config.copy())

def set_server_config(guild_id, radar_channel=None, forecast_channel=None, alerts_channel=None, system_channel=None, severe_role=None):
    configs = load_all_server_configs()
    config = configs.get(str(guild_id), default_config.copy())

    if radar_channel is not None:
        config["radar_channel"] = radar_channel
    if forecast_channel is not None:
        config["forecast_channel"] = forecast_channel
    if alerts_channel is not None:
        config["alerts_channel"] = alerts_channel
    if system_channel is not None:
        config["system_channel"] = system_channel
    if severe_role is not None:
        config["severe_role"] = severe_role

    configs[str(guild_id)] = config
    save_all_server_configs(configs)

def ensure_server_config(guild_id):
    configs = load_all_server_configs()
    if str(guild_id) not in configs:
        configs[str(guild_id)] = default_config.copy()
        save_all_server_configs(configs)
