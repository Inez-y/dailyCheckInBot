import json
import threading

data_lock = threading.Lock()
DATA_FILE = "checkins.json"

# Load check-in data
def load_checkin_data():
    try:
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save data
def save_checkin_data(data):
    with data_lock:
        with open(DATA_FILE, 'w') as file:
            json.dump(data, file, indent=4)

# Ensure guild data exists
def ensure_guild_data(guild_id, data):
    if guild_id not in data:
        data[guild_id] = {
            "current-month": {},
            "monthly_history": {}
        }
