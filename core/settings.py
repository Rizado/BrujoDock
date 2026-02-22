import os
import json

CONFIG_DIR = os.path.expanduser("~/.config/BrujoDock")
PLUGINS_DIR = os.path.join(CONFIG_DIR, "plugins")
CORE_PATH = os.path.join(CONFIG_DIR, "core.json")

DEFAULT_CORE = {
    "default_height": 32,
    "dock_padding_x": 16,
    "dock_padding_y": 4,
    "corner_radius": 12,
    "dock_spacing": 4,
    "log_mode": "none",
    "language": "en",
    "plugins": {
        "icon_panel": {"enabled": True},
        "sysmon": {"enabled": True},
        "battery_status": {"enabled": True},
        "clock": {"enabled": True}
    }
}

def _ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    os.makedirs(PLUGINS_DIR, exist_ok=True)

def ensure_core_config():
    _ensure_config_dir()
    if not os.path.exists(CORE_PATH):
        with open(CORE_PATH, 'w') as f:
            json.dump(DEFAULT_CORE, f, indent=2)

def load_core():
    ensure_core_config()
    with open(CORE_PATH, 'r') as f:
        user = json.load(f)
        result = DEFAULT_CORE.copy()
        result.update(user)
        return result

def save_core(data):
    _ensure_config_dir()
    with open(CORE_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def load_plugin(plugin_name: str) -> dict:
    _ensure_config_dir()
    path = os.path.join(PLUGINS_DIR, f"{plugin_name}.json")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}
