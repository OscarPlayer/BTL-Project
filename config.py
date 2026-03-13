import json
import os

CONFIG_FILE = "config.json"

def load():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {
        "minecraft_directory": None, 
        "ram": 4,
        "theme": "dark",
        "last_username": "",
        "last_version": ""
    }

def save(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)