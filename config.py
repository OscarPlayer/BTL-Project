import json
import os

CONFIG_FILE = "config.json"

def load():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    # NOVO: adiciona "theme" no config padrão
    return {
        "minecraft_directory": None, 
        "ram": 4,
        "theme": "dark"  # padrão é dark (mais bonito haha)
    }

def save(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)  # indent pra ficar legível
