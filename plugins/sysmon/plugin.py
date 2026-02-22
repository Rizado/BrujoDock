import gi
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo, GLib
from core.plugin_base import PluginBase
import psutil
import cairo

class Plugin(PluginBase):
    name = "SysMon"
    description = "System Monitor"
    version = "0.2.0"

    default_settings = {
        "cpu_label": "CPU",
        "ram_label": "RAM",
        "temp_label": "T",
        "show_cpu": True,
        "show_ram": True,
        "show_temp": True,
        "font_face": "DejaVu Sans Mono Book",
        "font_size": 10,
        "text_color": [1.0, 1.0, 1.0],
        "update_interval_ms": 1000
    }

    def __init__(self, dock):
        super().__init__(dock)
        self._cached_text = ""
        self._last_width = 0
        self._read_data()
        interval = self.settings.get("update_interval_ms", 1000)
        GLib.timeout_add(interval, self._update)

    def _update(self):
        old_text = self._cached_text
        old_width = self._text_width

        self._read_data()

        if self._cached_text != old_text or self._text_width != old_width:
            self.dock.update_geometry()
            self.dock.drawing_area.queue_draw()

        return GLib.SOURCE_CONTINUE

    def _read_data(self):
        parts = []

        if self.settings.get("show_cpu", True):
            cpu = psutil.cpu_percent(interval=None)
            label = self.settings.get("cpu_label", "CPU")
            parts.append(f"{label}: {int(cpu):3}%")

        if self.settings.get("show_ram", True):
            ram = psutil.virtual_memory().percent
            label = self.settings.get("ram_label", "RAM")
            parts.append(f"{label}: {int(ram):3}%")

        if self.settings.get("show_temp", True):
            temp = self._get_cpu_temp()
            if temp is not None:
                label = self.settings.get("temp_label", "T")
                parts.append(f"{label}: {int(temp):3}°")

        self._cached_text = " | ".join(parts)

        if self._cached_text.strip():
            dummy_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
            dummy_cr = cairo.Context(dummy_surface)
            layout = PangoCairo.create_layout(dummy_cr)
            font_desc = Pango.FontDescription()
            font_desc.set_family(self.settings["font_face"])
            font_desc.set_size(int(self.settings["font_size"]) * Pango.SCALE)
            layout.set_font_description(font_desc)
            layout.set_text(self._cached_text, -1)
            self._text_width = layout.get_pixel_size()[0] + 16
        else:
            self._text_width = 160

    def _get_cpu_temp(self):
        try:
            temps = psutil.sensors_temperatures()
            if 'coretemp' in temps:
                return int(temps['coretemp'][0].current)
            elif 'k10temp' in temps:  # AMD
                return int(temps['k10temp'][0].current)
            else:
                for name, entries in temps.items():
                    if entries:
                        return int(entries[0].current)
        except Exception:
            pass
        return None

    def get_preferred_size(self) -> tuple[int, int]:
        width = max(16, self._text_width)
        height = self.settings.get("font_size", 10) + 8
        return (width, height)

    def on_draw(self, cr, width: int, height: int):
        if not self._cached_text.strip():
            return

        color = self.settings.get("text_color", [1.0, 1.0, 1.0])
        cr.set_source_rgb(*color[:3])

        layout = PangoCairo.create_layout(cr)
        font_desc = Pango.FontDescription()
        font_desc.set_family(self.settings["font_face"])
        font_desc.set_size(int(self.settings["font_size"]) * Pango.SCALE)
        layout.set_font_description(font_desc)
        layout.set_text(self._cached_text, -1)

        text_w, text_h = layout.get_pixel_size()
        x = max(0, (width - text_w) // 2)
        y = max(0, (height - text_h) // 2)

        cr.move_to(x, y)
        PangoCairo.show_layout(cr, layout)