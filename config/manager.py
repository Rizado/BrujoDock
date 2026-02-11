# config/manager.py
import os
import json

CONFIG_DIR = os.path.expanduser("~/.config/BrujoDock")
SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")
PINNED_PATH = os.path.join(CONFIG_DIR, "pinned.json")

DEFAULT_SETTINGS = {
    "height": 40,
    "position": "bottom-center",
    "clock_format": "%H:%M %d.%m"
}

DEFAULT_PINNED = [
    "vivaldi-stable.desktop",
    "nemo.desktop",
    "org.gnome.Terminal.desktop"
]


def ensure_config():
    """Создаёт конфиги, если их нет"""
    os.makedirs(CONFIG_DIR, exist_ok=True)

    if not os.path.exists(SETTINGS_PATH):
        with open(SETTINGS_PATH, 'w') as f:
            json.dump(DEFAULT_SETTINGS, f, indent=2)

    if not os.path.exists(PINNED_PATH):
        with open(PINNED_PATH, 'w') as f:
            json.dump(DEFAULT_PINNED, f, indent=2)


def load_settings():
    """Загружает настройки"""
    ensure_config()
    with open(SETTINGS_PATH, 'r') as f:
        return {**DEFAULT_SETTINGS, **json.load(f)}


def load_pinned():
    """Загружает закреплённые приложения"""
    ensure_config()
    with open(PINNED_PATH, 'r') as f:
        return json.load(f)