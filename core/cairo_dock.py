# core/cairo_dock.py
import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GdkPixbuf
import cairo
import math
from core.strut_manager import set_strut


class CairoDock:
    def __init__(self, settings):
        self.settings = settings
        self.apps = {}  # app -> { 'icon_surface': ..., 'windows': [...], 'badge_surface': None }
        self.icon_size = 32
        self.spacing = 4
        self.padding = 16

        # Создаём окно
        self.window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        self.window.set_keep_below(True)
        self.window.set_skip_taskbar_hint(True)
        self.window.set_decorated(False)
        self.window.set_app_paintable(True)
        self.window.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.window.set_skip_pager_hint(True)

        # Прозрачность
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.window.set_visual(visual)

        # DrawingArea
        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", self.on_draw)
        self.drawing_area.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        self.drawing_area.connect("button-press-event", self.on_click)
        self.window.add(self.drawing_area)

        # Размер и позиция
        self.update_geometry()

        self.window.show_all()

    def update_geometry(self):
        width = max(1, len(self.apps) * (self.icon_size + self.spacing) + self.padding * 2)
        height = self.settings.get("height", 48)

        # Сначала устанавливаем размер
        self.window.set_default_size(width, height)
        self.window.resize(width, height)

        # Затем получаем актуальные геометрии
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geom = monitor.get_workarea()

        # Центрируем по ширине, но **оставляем высоту фиксированной**
        x = geom.x + (geom.width - width) // 2
        y = geom.y + geom.height - height  # ← всегда внизу

        self.window.move(x, y)
        self.drawing_area.queue_draw()

    def add_app(self, app, windows):
        """Добавляет или обновляет приложение"""
        if app in self.apps:
            # Обновляем список окон
            self.apps[app]['windows'] = windows
        else:
            # Новое приложение
            icon_surface = self.load_icon_surface(app)
            self.apps[app] = {
                'icon_surface': icon_surface,
                'windows': windows,
                'badge_surface': None
            }

        # Обновляем бейдж
        count = len(windows)
        self.apps[app]['badge_surface'] = self.create_badge_surface(count)

        self.update_geometry()

    def remove_app(self, app):
        """Удаляет приложение"""
        if app in self.apps:
            del self.apps[app]
            self.update_geometry()

    def load_icon_surface(self, app):
        """Загружает иконку через Wnck.Application.get_mini_icon()"""
        width = self.icon_size
        height = self.icon_size

        # Создаём Cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        ctx = cairo.Context(surface)

        # Очищаем фон
        ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)

        # Пробуем получить mini_icon из WNCK
        try:
            pixbuf = app.get_icon()
            if pixbuf:
                # Масштабируем под нужный размер
                if pixbuf.get_width() != width or pixbuf.get_height() != height:
                    pixbuf = pixbuf.scale_simple(width, height, GdkPixbuf.InterpType.BILINEAR)

                # Рисуем pixbuf на Cairo context
                Gdk.cairo_set_source_pixbuf(ctx, pixbuf, 0, 0)
                ctx.paint()
                return surface
        except Exception as e:
            print(f"[DEBUG] Ошибка get_mini_icon: {e}")
            pass

        # Fallback: буква
        name = app.get_name()
        letter = name[0].upper() if name else "?"

        ctx.set_source_rgba(0.2, 0.2, 0.4, 0.7)
        ctx.arc(width / 2, height / 2, min(width, height) / 2 - 2, 0, 2 * math.pi)
        ctx.fill()

        ctx.set_source_rgb(1, 1, 1)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(width * 0.6)
        text_extents = ctx.text_extents(letter)
        x = width / 2 - text_extents.width / 2 - text_extents.x_bearing
        y = height / 2 - text_extents.height / 2 - text_extents.y_bearing
        ctx.move_to(x, y)
        ctx.show_text(letter)

        return surface

    def create_badge_surface(self, count):
        """Создаёт поверхность для бейджа с количеством"""
        if count <= 1:
            return None

        badge_size = 16
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, badge_size, badge_size)
        ctx = cairo.Context(surface)

        # Фон кружка
        ctx.set_source_rgba(0.859, 0.141, 0.110, 1.0)  # #db241c (твой красный)
        ctx.arc(badge_size / 2, badge_size / 2, badge_size / 2 - 1, 0, 2 * math.pi)
        ctx.fill()

        # Текст
        ctx.set_source_rgb(1, 1, 1)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(badge_size * 0.6)
        text = str(count)
        text_extents = ctx.text_extents(text)
        x = badge_size / 2 - text_extents.width / 2 - text_extents.x_bearing
        y = badge_size / 2 - text_extents.height / 2 - text_extents.y_bearing
        ctx.move_to(x, y)
        ctx.show_text(text)

        return surface

    def draw_pixbuf_on_context(self, ctx, pixbuf, width, height):
        """Рисует GdkPixbuf на Cairo context"""
        gdk_window = self.window.get_window()
        if not gdk_window:
            return

        cr = Gdk.cairo_create(gdk_window)
        Gdk.cairo_set_source_pixbuf(cr, pixbuf, 0, 0)
        ctx.set_source(cr.get_source())
        ctx.paint()

    def draw_fallback_icon(self, ctx, letter, width, height):
        """Рисует fallback иконку с буквой"""
        # Фон
        ctx.set_source_rgba(0.2, 0.2, 0.4, 0.7)
        ctx.arc(width / 2, height / 2, min(width, height) / 2 - 2, 0, 2 * math.pi)
        ctx.fill()

        # Буква
        ctx.set_source_rgb(1, 1, 1)
        ctx.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(width * 0.6)
        text_extents = ctx.text_extents(letter)
        x = width / 2 - text_extents.width / 2 - text_extents.x_bearing
        y = height / 2 - text_extents.height / 2 - text_extents.y_bearing
        ctx.move_to(x, y)
        ctx.show_text(letter)

    def on_draw(self, widget, cr):
        """Основная отрисовка"""
        cr.set_source_rgba(0, 0, 0, 0.3)
        cr.paint()

        alloc = self.window.get_allocation()
        dock_height = alloc.height
        y_pos = (dock_height - self.icon_size) // 2

        x_offset = self.padding
        for app, data in self.apps.items():
            # Рисуем иконку
            icon_surface = data['icon_surface']
            if icon_surface:
                cr.set_source_surface(icon_surface, x_offset, y_pos)
                cr.paint()

                # Рисуем бейдж (если есть)
                badge_surface = data['badge_surface']
                if badge_surface:
                    badge_x = x_offset + self.icon_size - 16  # справа
                    badge_y = y_pos  # сверху
                    cr.set_source_surface(badge_surface, badge_x, badge_y)
                    cr.paint()

            x_offset += self.icon_size + self.spacing

    def on_click(self, widget, event):
        if event.button != 1:
            return

        alloc = self.window.get_allocation()
        dock_height = alloc.height
        icon_y = (dock_height - self.icon_size) // 2

        if event.y < icon_y or event.y > icon_y + self.icon_size:
            return

        x_offset = self.padding
        for app, data in self.apps.items():
            if x_offset <= event.x <= x_offset + self.icon_size:
                windows = data['windows']
                if len(windows) == 1:
                    windows[0].activate(Gdk.CURRENT_TIME)
                elif len(windows) > 1:
                    # Пока просто активируем первое
                    windows[0].activate(Gdk.CURRENT_TIME)
                break
            x_offset += self.icon_size + self.spacing

    def run(self):
        Gtk.main()