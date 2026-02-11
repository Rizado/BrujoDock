# main.py
# !/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.manager import load_settings
from core.app_monitor import AppMonitor
from core.cairo_dock import CairoDock


class DockApp:
    def __init__(self):
        self.settings = load_settings()
        self.dock = CairoDock(self.settings)
        self.monitor = AppMonitor(self.on_app_added, self.on_app_removed)

    def on_app_added(self, app, windows):
        self.dock.add_app(app, windows)

    def on_app_removed(self, app):
        self.dock.remove_app(app)

    def run(self):
        self.dock.run()


def main():
    app = DockApp()
    app.run()


if __name__ == "__main__":
    main()