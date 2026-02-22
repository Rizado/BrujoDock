# plugins/clock/plugin.py

import datetime
import cairo
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gdk, Gtk, Pango, PangoCairo, GLib
from core.plugin_base import PluginBase
from core.utils import log
from core.i18n import _


class Plugin(PluginBase):
    name = "Clock"
    description = "Displays clock in dock"
    version = "0.2.0"

    SETTINGS_FORM = [
        {"label": "Time Format", "key": "time_format", "type": "entry", "default": "%-I:%M:%S %P"},
        {"label": "Date Format", "key": "date_format", "type": "entry", "default": "%d.%m.%y"},
        {"label": "Font Size", "key": "font_size", "type": "spin", "min": 8, "max": 48, "default": 14},
        {"label": "Horizontal Padding", "key": "padding_x", "type": "spin", "min": 0, "max": 64, "default": 8},
        {"label": "Timezones\n(one per line)", "key": "timezones", "type": "text", "default": []},
    ]

    default_settings = {
        "time_format": "%-I:%M:%S %p",
        "date_format": "%d.%m.%y",
        "font_face": "DejaVu Sans Mono Book",
        "font_size": 10,
        "text_color": [1.0, 1.0, 1.0],
        "timezones": ["America/Buenos_Aires"],
    }

    def __init__(self, dock):
        super().__init__(dock)
        self._text_width = 0
        self.clock_text = ["", ""]
        self._setup_hover_handler()
        self.update_clock()
        GLib.timeout_add(100, self.update_clock)

    def update_clock(self):
        now = datetime.datetime.now()
        time_fmt = self.settings.get("time_format", "%-I:%M:%S %P")
        date_fmt = self.settings.get("date_format", "%d.%m.%y")

        t = self._format_time_with_ampm(now, time_fmt)
        d = now.strftime(date_fmt)

        if self.clock_text != [t, d]:
            self.clock_text = [t, d]

            dummy_surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
            dummy_cr = cairo.Context(dummy_surface)
            layout = PangoCairo.create_layout(dummy_cr)
            font_desc = Pango.FontDescription()
            font_desc.set_family(self.settings["font_face"])
            font_desc.set_size(int(self.settings["font_size"]) * Pango.SCALE)
            layout.set_font_description(font_desc)

            layout.set_text(t, -1)
            w1 = layout.get_pixel_size()[0]
            layout.set_text(d, -1)
            w2 = layout.get_pixel_size()[0]

            new_width = int(max(w1, w2) + 16)

            if new_width != self._text_width:
                self._text_width = new_width
                self.dock.update_geometry()
                self.dock.drawing_area.queue_draw()

            self.dock.drawing_area.queue_draw()

        return True

    def _format_time_with_ampm(self, now, time_fmt):
        if "%p" in time_fmt or "%P" in time_fmt:
            hour = int(now.strftime("%-H"))
            ampm_upper = "AM" if hour < 12 else "PM"
            ampm_lower = "am" if hour < 12 else "pm"

            time_fmt = time_fmt.replace("%p", ampm_upper)
            time_fmt = time_fmt.replace("%P", ampm_lower)

        return now.strftime(time_fmt)

    def _get_timezone_time(self, tz_name):
        try:
            import pytz

            if tz_name == "local":
                return datetime.datetime.now()

            tz = pytz.timezone(tz_name)

            local_dt = datetime.datetime.now().astimezone()

            target_dt = local_dt.astimezone(tz)
            return target_dt
        except Exception as e:
            log(f"[CLOCK] Timezone error {tz_name}: {e}")
            return datetime.datetime.now()

    def _setup_hover_handler(self):
        self.dock.drawing_area.connect("motion-notify-event", self._on_motion)
        self.dock.drawing_area.connect("leave-notify-event", self._on_leave)
        self.dock.drawing_area.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        self._last_hovered = False

    def _on_motion(self, widget, event):
        dock_width = self.dock.drawing_area.get_allocated_width()
        dock_pad_x = self.dock.settings.get("dock_padding_x", 16)

        clock_x = dock_width - self._text_width - dock_pad_x
        clock_w = self._text_width

        x_relative = event.x - dock_pad_x

        if clock_x <= x_relative <= clock_x + clock_w:
            if not self._last_hovered:
                self._last_hovered = True
                self._show_timezone_tooltip(widget)
        else:
            if self._last_hovered:
                self._last_hovered = False
                widget.set_tooltip_text("")

    def _on_leave(self, widget, event):
        self._last_hovered = False
        widget.set_tooltip_text("")

    def _get_local_timezone_name(self):
        try:
            with open('/etc/timezone', 'r') as f:
                return f.read().strip()
        except:
            from datetime import datetime
            return datetime.now().astimezone().strftime('%Z')

    def _show_timezone_tooltip(self, widget):
        from datetime import datetime

        time_fmt = self.settings.get("time_format", "%-I:%M:%S %P")
        date_fmt = self.settings.get("date_format", "%d.%m.%y")
        timezones = self.settings.get("timezones", [])

        lines = []

        local_dt = datetime.now()
        local_date = local_dt.strftime(date_fmt)
        local_time = self._format_time_with_ampm(local_dt, time_fmt)
        lines.append(f"<b>{local_date}, {local_time}</b> ({_("local time")} - {self._get_local_timezone_name()})")
        lines.append("<span color='#cccccc'>" + "─" * 48 + "</span>")

        for tz_name in timezones:
            try:
                tz_dt = self._get_timezone_time(tz_name)
                tz_date = tz_dt.strftime(date_fmt)
                tz_time = self._format_time_with_ampm(tz_dt, time_fmt)
                lines.append(f"<b>{tz_date}, {tz_time}</b> ({tz_name})")
            except Exception as e:
                pass

        tooltip_text = "\n".join(lines).replace("_", " ")
        widget.set_tooltip_markup(tooltip_text)

    def _hide_popover(self):
        if self._popover:
            self._popover.destroy()
            self._popover = None

    def on_draw(self, cr, width: int, height: int):
        if not self.enabled:
            return

        font_face = self.settings.get("font_face", "DejaVu Sans Mono Book")
        font_size = self.settings.get("font_size", 8)
        color = self.settings.get("text_color", [1.0, 1.0, 1.0])

        cr.set_source_rgba(*color[:3], 1)

        layout_time = PangoCairo.create_layout(cr)
        font_desc = Pango.FontDescription()
        font_desc.set_family(font_face)
        font_desc.set_size(int(font_size) * Pango.SCALE)
        layout_time.set_font_description(font_desc)
        layout_time.set_text(self.clock_text[0], -1)

        layout_date = PangoCairo.create_layout(cr)
        layout_date.set_font_description(font_desc)
        layout_date.set_text(self.clock_text[1], -1)

        tw, th = layout_time.get_pixel_size()
        dw, dh = layout_date.get_pixel_size()

        x0 = width - tw - 8
        x1 = width - dw - 8
        y0 = 0
        y1 = 32 - dh

        cr.move_to(x0, y0)
        PangoCairo.show_layout(cr, layout_time)

        cr.move_to(x1, y1)
        PangoCairo.show_layout(cr, layout_date)


    def get_preferred_size(self) -> tuple[int, int]:
        width = self._text_width or 80
        height = self.dock.settings.get("default_height", 32)
        return (width, height)
