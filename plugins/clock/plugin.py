# plugins/clock/plugin.py
from core.plugin_base import PluginBase
import datetime
import cairo


class Plugin(PluginBase):
    name = "Clock display in dock"
    version = "0.1"
    enabled = True

    def on_init(self):
        self._text_width = 0
        self.clock_text = ["", ""]
        self.update_clock()
        from gi.repository import GLib
        GLib.timeout_add(100, self.update_clock)

    def update_clock(self):
        now = datetime.datetime.now()
        t = now.strftime("%-I:%M:%S %p")
        d = now.strftime("%d.%m.%y")

        if self.clock_text != [t, d]:
            self.clock_text = [t, d]

            # Измеряем ширину текста
            cr = cairo.Context(cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1))
            cr.select_font_face("DejaVu Sans Mono Book", 0, 0)
            cr.set_font_size(12)
            w1 = cr.text_extents(t).width
            w2 = cr.text_extents(d).width
            new_width = int(max(w1, w2) + 16)  # + отступы слева/справа

            if new_width != self._text_width:
                self._text_width = new_width
                self.dock.reserve_right_space(self.name, self._text_width)

            self.dock.drawing_area.queue_draw()

        return True

    def on_draw(self, cr, width: int, height: int):
        if not self.enabled:
            return

        cr.select_font_face("DejaVu Sans Mono Book", 0, 0)
        cr.set_font_size(12.0)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.85)

        # Фиксированный отступ от правого края — чтобы не перекрывать иконки
        y_offset = (height - 24) // 2
        x0 = width - cr.text_extents(self.clock_text[0]).width - 8
        x1 = width - cr.text_extents(self.clock_text[1]).width - 8

        cr.set_source_rgba(1.0, 1.0, 1.0, 0.85)

        cr.move_to(x0, y_offset + 10)
        cr.show_text(self.clock_text[0])

        cr.move_to(x1, y_offset + 24)
        cr.show_text(self.clock_text[1])
