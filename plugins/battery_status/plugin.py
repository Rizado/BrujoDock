import os
import cairo
from gi.repository import GLib
from core.plugin_base import PluginBase
from core.i18n import _

class Plugin(PluginBase):
    name = "battery_status"
    description = _("Display the battery status")
    version = "0.2.0"

    default_settings = {
        "height": 32,
        "font_face": "DejaVu Sans Mono Book",
        "font_size": 14,
        "padding_x": 8,
        "update_interval_ms": 1000  # ms
    }

    def __init__(self, dock):
        super().__init__(dock)
        self._level_text = ""
        self._status_text = ""
        self._surface_width = 0
        self._source_id = None
        info = self._get_battery_info()
        self._status_text, self._level_text = self._format_text(info)
        self._recalculate_width()
        self.dock.update_geometry()
        interval = self.settings.get("update_interval_ms", 1000)
        self._source_id = GLib.timeout_add(interval, self._update)

    def __del__(self):
        if self._source_id:
            GLib.source_remove(self._source_id)

    def _update(self):
        info = self._get_battery_info()
        _new_status, _new_level  = self._format_text(info)
        if _new_level != self._level_text:
            self._level_text = _new_level
            self._status_text = _new_status
            self._recalculate_width()
            self.dock.update_geometry()
            self.dock.drawing_area.queue_draw()

        return GLib.SOURCE_CONTINUE

    def _recalculate_width(self):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
        cr = cairo.Context(surface)
        cr.select_font_face(self.settings["font_face"], cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(self.settings["font_size"])
        _, _, level_width, _, _, _ = cr.text_extents(self._level_text)
        _, _, status_width, _, _, _ = cr.text_extents(self._status_text)
        self._surface_width = int(max(level_width, status_width)) + 2 * self.settings["padding_x"]

    def get_preferred_size(self):
        return (self._surface_width, self.settings["height"])

    def _get_battery_info(self):
        power_supply = "/sys/class/power_supply"
        if not os.path.exists(power_supply):
            return None
        for item in os.listdir(power_supply):
            if item.startswith("BAT"):
                path = os.path.join(power_supply, item)
                try:
                    with open(os.path.join(path, "capacity"), "r") as f:
                        cap = int(f.read().strip())
                    with open(os.path.join(path, "status"), "r") as f:
                        status = f.read().strip()
                    return {"capacity": cap, "status": status}
                except (OSError, ValueError, FileNotFoundError):
                    continue
        return None

    def _format_text(self, info):
        if info is None:
            return _("There is no battery"), "0"

        return _("Charging") if info["status"].lower() == "charging" else _("Discharging") , f"{info['capacity']}%"

    def on_draw(self, cr, width, height):
        info = self._get_battery_info()

        cr.select_font_face(self.settings["font_face"], cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(self.settings["font_size"])

        if info is None:
            r, g, b = 0.7, 0.7, 0.7
            cr.set_source_rgb(r, g, b)
            x_bearing, y_bearing, txt_width, txt_height = cr.text_extents(self._status_text)[:4]
            x = self.settings["padding_x"]
            y = (height + txt_height) / 2
            cr.move_to(x, y)
            cr.show_text(self._status_text)
        else:
            if info["status"].lower() == "charging":
                r, g, b = 0.29, 0.56, 0.88
            else:
                r, g, b = 0.8, 0.8, 0.8
            cr.set_source_rgb(r, g, b)
            x_bearing, y_bearing, txt_width, txt_height = cr.text_extents(self._status_text)[:4]
            x = (self._surface_width - txt_width) / 2
            y = txt_height
            cr.move_to(x, y)
            cr.show_text(self._status_text)

            if info["capacity"] >= 40:
                r, g, b = 0.49, 0.83, 0.13
            elif info["capacity"] >= 20:
                r, g, b = 0.96, 0.65, 0.14
            else:
                r, g, b = 0.81, 0.01, 0.10
            cr.set_source_rgb(r, g, b)
            x_bearing, y_bearing, txt_width, txt_height = cr.text_extents(self._level_text)[:4]
            x = (self._surface_width - txt_width) / 2
            y = 30
            cr.move_to(x, y)
            cr.show_text(self._level_text)
