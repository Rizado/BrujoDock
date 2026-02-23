import os
import json
from .settings import load_plugin, PLUGINS_DIR
from .utils import log


class PluginBase:
    name = "Unnamed Plugin"
    description = "No description"
    version = "0.0.0"
    SETTINGS_FORM = []
    default_settings = {}

    def __init__(self, dock):
        self.dock = dock
        self.enabled = True
        self.settings = {}
        self._load_settings()

    def get_plugin_name(self) -> str:
        return self.name.lower().replace(" ", "_")

    def get_description(self) -> str:
        return self.description

    def get_plugin_xpos(self) -> int:
        for i, plugin in enumerate(self.dock.plugins):
            if plugin.name == self.name:
                offset = self.dock.settings.get("dock_padding_x", 16)
                for j in range(i):
                    prev_plugin = self.dock.plugins[j]
                    offset += prev_plugin.get_preferred_size()[0]
                    offset += self.dock.settings.get("plugin_spacing", 8)
                return offset
        return 0

    def _load_settings(self):
        config_dir = os.path.expanduser("~/.config/BrujoDock/plugins")
        config_path = os.path.join(config_dir, f"{self.get_plugin_name()}.json")

        self.settings = dict(self.default_settings)

        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    plugin_settings = json.load(f)
                    self.settings.update(plugin_settings)
                    log(f"[{self.name}] Loaded: {config_path}")
            except Exception as e:
                log(f"[{self.name}] Loading error: {e}")
        else:
            log(f"[{self.name}] There is no config, creating: {config_path}", "INFO")
            self.save_settings()

    def save_settings(self):
        config_dir = os.path.expanduser("~/.config/BrujoDock/plugins")
        config_path = os.path.join(config_dir, f"{self.get_plugin_name()}.json")

        os.makedirs(config_dir, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(self.settings, f, indent=2)

        log(f"[{self.name}] Saved: {config_path}")

    def show_settings_dialog(self):
        from core.plugin_settings_dialog import PluginSettingsDialog

        dialog = PluginSettingsDialog(self)
        dialog.run()
        dialog.destroy()

    def _open_settings(self):
        self.show_settings_dialog()

    def on_draw(self, cr, width, height):
        pass

    def get_preferred_size(self):
        return (0, 0)
