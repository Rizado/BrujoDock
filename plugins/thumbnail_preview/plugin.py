# plugin.py
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
import cairo
import os
from core.utils import format_window_count
from core.plugin_base import PluginBase


class Plugin(PluginBase):
    name = "Thumbnail Preview"
    version = "0.1"
    def on_init(self):
        # self.dock = dock
        self.hovered_group = None
        self.thumbnail_window = None
        self.enabled = True  # можно переключать через settings

        da = self.dock.drawing_area

        da.set_has_tooltip(True)  # ← ВАЖНО: здесь!

        # Подключаем события
        da.add_events(
            Gdk.EventMask.ENTER_NOTIFY_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        da.connect("enter-notify-event", self.on_enter)
        da.connect("leave-notify-event", self.on_leave)
        da.connect("motion-notify-event", self.on_motion)

    def on_enter(self, widget, event):
        print("[DEBUG] on_enter")
        # return

        self.update_hover(event.x)

    def on_motion(self, widget, event):
        print("[DEBUG] on_motion")
        # return

        self.update_hover(event.x)

    def on_leave(self, widget, event):
        self.hide_thumbnail()

    def update_hover(self, x):
        hovered_group = None
        x_offset = self.dock.padding
        for group_key, data in self.dock.groups.items():
            if x_offset <= x <= x_offset + self.dock.icon_size:
                hovered_group = group_key
                break
            x_offset += self.dock.icon_size + self.dock.spacing

        if hovered_group != self.hovered_group:
            self.hovered_group = hovered_group

            if not self.enabled:
                if hovered_group and hovered_group in self.dock.groups:
                    data = self.dock.groups[hovered_group]
                    app_name = data['app'].get_name() or "Безымянное окно"
                    count = len(data['windows'])
                    tooltip_text = f"{app_name} ({format_window_count(count)})"
                    self.dock.drawing_area.set_tooltip_text(tooltip_text)
                else:
                    self.dock.drawing_area.set_tooltip_text(None)
            else:
                # Активный плагин → скрываем tooltip, показываем превью
                self.dock.drawing_area.set_tooltip_text(None)  # ← КЛЮЧЕВАЯ СТРОКА
                if hovered_group and hovered_group in self.dock.groups:
                    self.show_tooltip_or_thumbnail(self.dock.groups[hovered_group], x_offset)
                else:
                    self.hide_thumbnail()

    def show_tooltip_or_thumbnail(self, data, icon_x_offset):
        windows = data['windows']
        count = len(windows)
        app = data['app']
        app_name = app.get_name() or "Безымянное окно"

        if not self.enabled or count == 0:
            # Устанавливаем tooltip вместо print
            tooltip_text = f"{app_name} ({format_window_count(count)})"
            return

        # Берём иконку приложения
        try:
            icon = app.get_icon()
            if icon:
                thumb_pixbuf = self.scale_to_square(icon, 240)
                if thumb_pixbuf:
                    self.show_thumbnail(thumb_pixbuf, app_name, count, icon_x_offset)
                    return
        except Exception as e:
            print(f"[THUMB] Ошибка иконки: {e}")

        # Последний fallback
        print(f"[HOVER] {app_name} ({format_window_count(count)})")

    def get_scaled_thumbnail(self, window, max_size=240):
        try:
            name = window.get_name()
            print(f"[THUMB] Имя окна: {name}")
        except Exception as e:
            print(f"[THUMB] Ошибка имени: {e}")
            return None

        try:
            thumb = window.get_thumbnail(max_size * 2, max_size * 2)
            print(f"[THUMB] Превью получено: {thumb is not None}")
            if not thumb:
                return None
        except Exception as e:
            print(f"[THUMB] Ошибка превью: {e}")
            return None

        print("[THUMB] Всё ок, возвращаем заглушку")
        return None  # ← не рисуем, только проверяем вызовы

    def show_thumbnail(self, pixbuf, app_name, count, icon_x_offset):
        if not pixbuf:
            self.hide_thumbnail()
            return

        self.hide_thumbnail()

        try:
            self.thumbnail_window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
            self.thumbnail_window.set_decorated(False)
            self.thumbnail_window.set_keep_above(True)
            self.thumbnail_window.set_type_hint(Gdk.WindowTypeHint.UTILITY)
            self.thumbnail_window.set_skip_taskbar_hint(True)
            self.thumbnail_window.set_skip_pager_hint(True)

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            label = Gtk.Label(label=f"{app_name} ({format_window_count(count)})")
            label.set_margin_bottom(4)
            label.set_halign(Gtk.Align.CENTER)
            vbox.pack_start(label, False, False, 0)
            vbox.pack_start(Gtk.Image.new_from_pixbuf(pixbuf), True, True, 0)

            self.thumbnail_window.add(vbox)
            self.thumbnail_window.show_all()  # ← сначала показываем

            # ← Затем откладываем позиционирование
            from gi.repository import GLib
            GLib.idle_add(self._position_thumbnail, icon_x_offset)

        except Exception as e:
            print(f"[SHOW] Ошибка: {e}")
            self.hide_thumbnail()

    def _position_thumbnail(self, icon_x_offset):
        if not self.thumbnail_window:
            return

        # Получаем геометрию монитора
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        monitor_geom = monitor.get_geometry()

        # Размеры дока
        dock_alloc = self.dock.window.get_allocation()
        dock_width = dock_alloc.width
        dock_height = dock_alloc.height

        # Позиция дока (как в update_geometry)
        dock_x = monitor_geom.x + (monitor_geom.width - dock_width) // 2
        dock_y = monitor_geom.y + monitor_geom.height - dock_height

        # Позиция иконки
        icon_x = dock_x + icon_x_offset
        icon_y = dock_y + (dock_height - self.dock.icon_size) // 2

        # Превью над иконкой
        thumb_w, thumb_h = 240, 240
        thumb_x = icon_x + self.dock.icon_size // 2 - thumb_w // 2
        thumb_y = icon_y - thumb_h - 8

        # Клип к экрану
        max_x = monitor_geom.x + monitor_geom.width - thumb_w
        max_y = monitor_geom.y + monitor_geom.height - thumb_h
        thumb_x = max(monitor_geom.x, min(thumb_x, max_x))
        thumb_y = max(monitor_geom.y, min(thumb_y, max_y))

        self.thumbnail_window.move(thumb_x, thumb_y)

    def show_tooltip(self, text, windows):
        self.hide_thumbnail()
        # Можно сделать tooltip через Gtk.Tooltip, но проще — временный label
        # Для простоты пока просто лог — в будущем добавим красивый tooltip
        print(f"[HOVER] {text}")

    def hide_thumbnail(self):
        if self.thumbnail_window:
            self.thumbnail_window.destroy()
            self.thumbnail_window = None
        self.hovered_group = None
        self.dock.drawing_area.set_tooltip_text(None)  # ← убираем tooltip при уходе

    def scale_icon_to_square(self, pixbuf, size):
        """Масштабирует иконку под квадратный холст"""
        if not pixbuf:
            return None
        orig_w, orig_h = pixbuf.get_width(), pixbuf.get_height()
        scale = min(size / orig_w, size / orig_h)
        new_w, new_h = int(orig_w * scale), int(orig_h * scale)
        scaled = pixbuf.scale_simple(new_w, new_h, GdkPixbuf.InterpType.BILINEAR)

        canvas = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, size, size)
        canvas.fill(0x1a1a1a99)

        x = (size - new_w) // 2
        y = (size - new_h) // 2
        scaled.composite(canvas, x, y, new_w, new_h, 0, 0, 1.0, 1.0, GdkPixbuf.InterpType.BILINEAR, 255)
        return canvas

    def scale_to_square(self, pixbuf, size):
        """Масштабирует Pixbuf под квадратный холст с центрированием"""
        if not pixbuf:
            return None

        orig_w = pixbuf.get_width()
        orig_h = pixbuf.get_height()

        scale = min(size / orig_w, size / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)

        scaled = pixbuf.scale_simple(new_w, new_h, GdkPixbuf.InterpType.BILINEAR)

        # Создаём холст
        canvas = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, size, size)
        canvas.fill(0x1a1a1a99)  # тёмный фон с прозрачностью

        # Копируем изображение в центр
        x = (size - new_w) // 2
        y = (size - new_h) // 2

        # ИСПОЛЬЗУЕМ copy_area вместо composite!
        scaled.copy_area(0, 0, new_w, new_h, canvas, x, y)

        return canvas
