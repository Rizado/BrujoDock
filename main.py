# main.py
# !/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.manager import load_settings
from core.app_monitor import AppMonitor
from core.brujo_dock import BrujoDock

__version__ = "0.1.0"

class DockApp:
    def __init__(self):
        self.settings = load_settings()
        self.dock = BrujoDock(self.settings)
        self.monitor = AppMonitor(self.on_app_added, self.on_app_removed)

    def on_app_added(self, app, windows, group_key):
        self.dock.add_app(app, windows, group_key)

    def on_app_removed(self, group_key):
        self.dock.remove_group(group_key)

    def run(self):
        self.dock.run()


def main():
    app = DockApp()
    app.run()


if __name__ == "__main__":
    main()