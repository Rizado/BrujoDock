import sys
from datetime import datetime

_dock = None

def init_logger(dock):
    global _dock
    _dock = dock

def log(message, level="INFO"):
    if _dock is None:
        return

    log_mode = _dock.settings.get("log_mode", "none")

    if log_mode == "none":
        return

    elif log_mode == "console":
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    elif log_mode == "file":
        # TODO: create logging to file
        pass

    elif log_mode == "memory":
        # TODO: buffer in memory + writing many lines
        pass