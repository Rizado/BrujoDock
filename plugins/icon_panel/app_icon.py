# plugins/icon_panel/app_icon.py

import os
from gi.repository import Gio, GLib
from .special_classes import normalize_identifier
from core.utils import log
import cairo


class AppIcon:
    def __init__(self, name="", icon_name="", desktop_path="", identifier="", app=None, pinned=False):
        self.name = name
        self.icon_name = icon_name
        self.gicon = None
        self.desktop_path = desktop_path
        self.pinned = pinned
        self.running_windows = []
        self.hovered = False
        self.active = False
        self.icon_surface = None
        self.identifier = identifier
        self.app = app

    @classmethod
    def from_desktop_file(cls, path, pinned=False):
        if not os.path.exists(path):
            return None
        try:
            keyfile = GLib.KeyFile()
            keyfile.load_from_file(path, GLib.KeyFileFlags.NONE)

            name = keyfile.get_string("Desktop Entry", "Name") or os.path.basename(path).replace(".desktop", "")
            icon_name = keyfile.get_string("Desktop Entry", "Icon") or "application-x-executable"

            identifier = ""
            try:
                identifier = keyfile.get_string("Desktop Entry", "StartupWMClass")
            except:
                pass

            if not identifier:
                identifier = os.path.basename(path).replace(".desktop", "")

            # Нормализуем
            from .special_classes import normalize_identifier
            identifier = normalize_identifier(identifier)

            return cls(
                name=name,
                icon_name=icon_name,
                desktop_path=path,
                identifier=identifier,  # ← убедись, что это есть
                pinned=pinned
            )
        except Exception as e:
            log(f"[ICON] Ошибка .desktop {path}: {e}")
            return None

    def is_running(self) -> bool:
        return len(self.running_windows) > 0

    def add_window(self, win):
        if win not in self.running_windows:
            self.running_windows.append(win)

    def has_window(self, win) -> bool:
        return win in self.running_windows

    def remove_window(self, win):
        if win in self.running_windows:
            self.running_windows.remove(win)

    def set_hovered(self, hovered: bool):
        self.hovered = hovered

    def load_icon(self, size=32):
        if self.icon_surface:
            return self.icon_surface

        try:
            theme = Gtk.IconTheme.get_default()
            pixbuf = theme.load_icon(self.name, size, Gtk.IconLookupFlags.FORCE_SIZE)
        except Exception:
            pass

        return self.icon_surface


    def load_icon_surface(self, size=32):
        if self.icon_surface is not None:
            return

        # Fallback — серый квадрат
        fallback = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
        cr_fallback = cairo.Context(fallback)
        cr_fallback.set_source_rgb(0.8, 0.8, 0.8)
        cr_fallback.rectangle(4, 4, size - 8, size - 8)
        cr_fallback.fill()
        self.icon_surface = fallback

        try:
            from gi.repository import Gtk, Gdk, GdkPixbuf
            icon_theme = Gtk.IconTheme.get_default()

            if self.app:
                try:
                    gicon = self.app.get_icon()
                    if gicon:
                        if hasattr(gicon, 'get_filename'):
                            self.icon_surface = Gdk.cairo_surface_create_from_pixbuf(gicon, 0, None)
                            return
                        else:
                            icon_info = icon_theme.lookup_by_gicon(gicon, size, Gtk.IconLookupFlags.FORCE_SIZE)
                            if icon_info:
                                pixbuf = icon_info.load_icon()
                                self.icon_surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf, 0, None)
                                return
                except Exception:
                    pass

            if self.icon_name and self.icon_name.startswith("/"):
                if os.path.exists(self.icon_name):
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(self.icon_name, size, size)
                    self.icon_surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf, 0, None)
                    return

            from .special_classes import get_icon_name_for_identifier

            icon_candidates = [
                self.icon_name,
                get_icon_name_for_identifier(self.identifier),
                self.identifier.split("-")[0],
                self.identifier,
            ]

            icon_candidates = list(dict.fromkeys([c for c in icon_candidates if c and " " not in c]))

            for icon_name in icon_candidates:
                try:
                    pixbuf = icon_theme.load_icon(icon_name, size, Gtk.IconLookupFlags.FORCE_SIZE)
                    self.icon_surface = Gdk.cairo_surface_create_from_pixbuf(pixbuf, 0, None)
                    return
                except Exception:
                    continue

        except Exception as e:
            log(f"[ICON] Ошибка загрузки: {e}")

    def _draw_badge(self, cr, x, y, settings):
        count = len(self.running_windows)
        icon_size = settings["icon_size"]
        pad_x = settings["icon_padding_x"]

        badge_x = pad_x + icon_size - 12
        badge_y = y + 4

        cr.set_source_rgb(0.81, 0.01, 0.10)
        cr.arc(badge_x + 6, badge_y + 6, 6, 0, 2 * 3.14159)
        cr.fill()

        cr.set_source_rgb(1, 1, 1)
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(8)

        text = str(count) if count < 10 else "9+"
        _, _, w, h = cr.text_extents(text)[:4]
        cr.move_to(badge_x + 6 - w / 2, badge_y + 6 + h / 2)
        cr.show_text(text)
