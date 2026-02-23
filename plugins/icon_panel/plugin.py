from core.plugin_base import PluginBase
import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck, Gdk, Gtk, GLib
from .app_icon_list import AppIconList
from core.utils import log
import os
from core.i18n import _


class Plugin(PluginBase):
    name = "Icon Panel"
    description = "Application launcher and window switcher"
    version = "0.2.0"

    default_settings = {
        "pinned": [
            "/usr/share/applications/vivaldi-stable.desktop",
            "/usr/share/applications/org.gnome.Terminal.desktop"
        ],
        "icon_size": 32,
        "panel_padding_x": 4,
        "icon_padding_x": 2,
        "icon_spacing": 2,
        "icon_padding_top": 2,
        "icon_padding_bottom": 6,
        "icon_highlight_color": "#00cc00",
        "icon_highlight_height": 4,
        "hint_mode": 1,
    }

    def __init__(self, dock):
        super().__init__(dock)
        pinned_paths = self.settings.get("pinned", [])
        log(f"[ICON_PANEL] Загружаем pinned: {pinned_paths}")
        self.icon_list = AppIconList(self._load_pinned())
        self._setup_window_monitoring()
        self._setup_hover_handler()
        self._setup_active_window_handler()
        self._setup_click_handler()

    def _setup_window_monitoring(self):
        screen = Wnck.Screen.get_default()
        screen.connect("window-opened", self._on_window_opened)
        screen.connect("window-closed", self._on_window_closed)
        screen.force_update()
        for window in screen.get_windows():
            self._on_window_opened(screen, window)

    def _on_window_opened(self, screen, window):
        if window.get_pid() == os.getpid():
            return
        wtype = window.get_window_type()
        if wtype in (Wnck.WindowType.DESKTOP, Wnck.WindowType.DOCK, Wnck.WindowType.SPLASHSCREEN):
            return

        app = window.get_application()
        if not app:
            return

        class_group = window.get_class_group()
        wm_class = class_group.get_res_class() if class_group else ""

        if self._is_main_window(window):
            self.icon_list.add_window(wm_class, app, window)
        self.dock.update_geometry()
        self.dock.drawing_area.queue_draw()

    def _on_window_closed(self, screen, window):
        self.icon_list.remove_window(window)
        self.dock.update_geometry()
        self.dock.drawing_area.queue_draw()

    def _is_main_window(self, window):
        if window is None:
            return False

        window_type = window.get_window_type()
        if window_type != Wnck.WindowType.NORMAL:
            return False

        if window.get_transient():
            return False

        return True

    def get_preferred_size(self) -> tuple[int, int]:
        n = max(1, len(self.icon_list.icons))
        s = self.settings
        icon_size = s.get("icon_size", 32)
        panel_pad_x = s.get("panel_padding_x", 4)
        icon_pad_x = s.get("icon_padding_x", 2)
        spacing = s.get("icon_spacing", 2)
        pad_top = s.get("icon_padding_top", 2)
        pad_bottom = s.get("icon_padding_bottom", 6)

        width = panel_pad_x * 2 + (icon_size + 2 * icon_pad_x) * n + spacing * (n - 1)
        height = pad_top + icon_size + pad_bottom
        return (width, height)

    def _load_pinned(self):
        return self.settings.get("pinned", [])

    def on_draw(self, cr, width: int, height: int):
        s = self.settings
        icon_size = s.get("icon_size", 32)
        panel_pad_x = s.get("panel_padding_x", 4)
        icon_pad_x = s.get("icon_padding_x", 2)
        spacing = s.get("icon_spacing", 2)
        pad_top = s.get("icon_padding_top", 2)
        pad_bottom = s.get("icon_padding_bottom", 6)
        highlight_h = s.get("icon_highlight_height", 4)
        highlight_color = s.get("icon_highlight_color", "#00cc00")
        r = int(highlight_color[1:3], 16) / 255.0
        g = int(highlight_color[3:5], 16) / 255.0
        b = int(highlight_color[5:7], 16) / 255.0

        x = panel_pad_x
        for app_icon in self.icon_list.icons:
            total_w = icon_size + 2 * icon_pad_x
            cell_height = pad_top + icon_size + pad_bottom  # ← полная высота
            y = pad_top

            cr.save()
            cr.rectangle(x, 0, total_w, height)
            cr.clip()
            cr.translate(x, 0)

            if app_icon.active:
                cr.set_source_rgba(0.5, 0.5, 0.5, 0.8)
                cr.rectangle(0, 0, total_w, cell_height)
                cr.fill()

            if app_icon.hovered:
                cr.set_source_rgba(0, 0, 0, 0.8)
                cr.rectangle(0, 0, total_w, cell_height)
                cr.fill()

            if app_icon.is_running():
                h = min(highlight_h, pad_bottom)
                cr.set_source_rgb(r, g, b)
                cr.rectangle(0, cell_height - h, total_w, h)
                cr.fill()

            if app_icon.icon_surface is None:
                app_icon.load_icon_surface(icon_size)
            if app_icon.icon_surface:
                cr.set_source_surface(app_icon.icon_surface, icon_pad_x, y)
                cr.paint()

            if len(app_icon.running_windows) > 1:
                app_icon._draw_badge(cr, x, y, s)

            cr.restore()
            x += total_w + spacing

    def _setup_hover_handler(self):
        self.dock.drawing_area.connect("motion-notify-event", self._on_motion)
        self.dock.drawing_area.connect("leave-notify-event", self._on_leave)
        self.dock.drawing_area.add_events(
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        self._last_hovered_index = None

    def _on_motion(self, widget, event):
        settings = self.settings
        icon_size = settings.get("icon_size", 32)
        panel_pad_x = settings.get("panel_padding_x", 4)
        icon_pad_x = settings.get("icon_padding_x", 2)
        spacing = settings.get("icon_spacing", 2)

        x = event.x - self.get_plugin_xpos()
        index = 0
        current_x = panel_pad_x

        for icon in self.icon_list.icons:
            icon_w = icon_size + 2 * icon_pad_x
            if current_x <= x <= current_x + icon_w:
                if index != self._last_hovered_index:
                    for i, ic in enumerate(self.icon_list.icons):
                        ic.set_hovered(i == index)

                    hint_mode = settings.get("hint_mode", 1)
                    if hint_mode == 1:
                        hint_text = self._get_hint_text(icon)
                        widget.set_tooltip_text(hint_text)
                    else:
                        widget.set_tooltip_text("")

                    self._last_hovered_index = index
                    self.dock.drawing_area.queue_draw()
                return
            current_x += icon_w + spacing
            index += 1

        if self._last_hovered_index is not None:
            for ic in self.icon_list.icons:
                ic.set_hovered(False)
            self._last_hovered_index = None
            widget.set_tooltip_text("")
            self.dock.drawing_area.queue_draw()

    def _get_hint_text(self, icon) -> str:
        if not icon.running_windows:
            return icon.name

        titles = [w.get_name() for w in icon.running_windows[:5]]
        if len(icon.running_windows) > 5:
            titles.append(f"... и ещё {len(icon.running_windows) - 5}")

        return "\n".join(titles)

    def _on_leave(self, widget, event):
        for ic in self.icon_list.icons:
            ic.set_hovered(False)
        self._last_hovered_index = None
        widget.set_tooltip_text("")
        self.dock.drawing_area.queue_draw()
        return False

    def _setup_active_window_handler(self):
        screen = Wnck.Screen.get_default()
        screen.connect("active-window-changed", self._on_active_window_changed)
        self._on_active_window_changed(screen, None)

    def _on_active_window_changed(self, screen, previous_window):
        active_window = screen.get_active_window()
        if active_window is None:
            for icon in self.icon_list.icons:
                icon.active = False
            return

        if not self._is_main_window(active_window):
            return

        for icon in self.icon_list.icons:
            icon.active = False

        if active_window:
            for icon in self.icon_list.icons:
                if active_window in icon.running_windows:
                    icon.active = True
                    break

        self.dock.drawing_area.queue_draw()

    def _setup_click_handler(self):
        self.dock.drawing_area.connect("button-press-event", self._on_button_press)
        self.dock.drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

    def _on_button_press(self, widget, event):
        settings = self.settings
        icon_size = settings.get("icon_size", 32)
        panel_pad_x = settings.get("panel_padding_x", 4)
        icon_pad_x = settings.get("icon_padding_x", 2)
        spacing = settings.get("icon_spacing", 2)
        x = event.x - self.get_plugin_xpos()
        button = event.button
        index = 0
        current_x = panel_pad_x

        icon_w = icon_size + 2 * icon_pad_x
        for icon in self.icon_list.icons:
            if current_x <= x <= current_x + icon_w:
                if button == 1:
                    self._on_left_click(icon, event)
                elif button == 3:
                    log("[RIGHT CLICK HANDLER CALLED]")

                    self._on_right_click(widget, event, icon)
                return True
            current_x += icon_w + spacing
            index += 1

        return False

    def _on_left_click(self, icon, event):
        windows = icon.running_windows

        if len(windows) == 0:
            if icon.pinned and icon.desktop_path:
                self._launch_application(icon.desktop_path)
        elif len(windows) == 1:
            self._toggle_window(windows[0])
        else:
            self._show_window_menu(icon, event)

    def _launch_application(self, desktop_path):
        try:
            from gi.repository import Gio
            app_info = Gio.DesktopAppInfo.new_from_filename(desktop_path)
            if app_info:
                app_info.launch([], None)
        except Exception as e:
            log(f"[LAUNCH] Ошибка запуска {desktop_path}: {e}")

    def _toggle_window(self, window):
        screen = Wnck.Screen.get_default()
        active = screen.get_active_window()

        if window == active:
            window.minimize()
        else:
            window.activate(Gdk.CURRENT_TIME)

    def _show_window_menu(self, icon, event):
        menu = Gtk.Menu()

        for window in icon.running_windows:
            title = window.get_name() or _("Nameless")
            item = Gtk.MenuItem(label=title)
            item.connect("activate", lambda w, win=window: self._toggle_window(win))
            menu.append(item)

        menu.show_all()

        menu.popup_at_pointer(event)

    def _on_right_click(self, widget, event, icon):
        menu = Gtk.Menu()

        if icon.pinned:
            item = Gtk.MenuItem(label=_("Unpin"))
            item.connect("activate", lambda w: self._unpin_icon(icon))
        else:
            item = Gtk.MenuItem(label=_("Pin"))
            item.connect("activate", lambda w: self._pin_icon(icon))
        menu.append(item)

        if icon.running_windows:
            sep = Gtk.SeparatorMenuItem()
            menu.append(sep)

            close_item = Gtk.MenuItem(label=_("Close All"))
            close_item.connect("activate", lambda w: self._close_all_windows(icon))
            menu.append(close_item)

        sep2 = Gtk.SeparatorMenuItem()
        menu.append(sep2)

        settings_item = Gtk.MenuItem(label=_("Settings"))
        settings_item.connect("activate", lambda w: self._open_settings())
        menu.append(settings_item)

        menu.show_all()
        menu.popup_at_pointer(event)

    def _close_all_windows(self, icon):
        timestamp = Gtk.get_current_event_time()
        for window in icon.running_windows[:]:
            window.close(timestamp)

    def _pin_icon(self, icon):
        desktop_path = icon.desktop_path
        if not desktop_path and icon.identifier:
            desktop_path = self._find_desktop_path(icon.identifier)
            icon.desktop_path = desktop_path

        if desktop_path and desktop_path not in self.settings["pinned"]:
            self.settings["pinned"].append(desktop_path)
            self.save_settings()
            icon.pinned = True
            self.dock.drawing_area.queue_draw()
            log(f"[PIN] Закреплён: {desktop_path}")
        else:
            log(f"[PIN] Не удалось найти .desktop для {icon.name} (identifier={icon.identifier})")

    def _unpin_icon(self, icon):
        if icon.desktop_path in self.settings["pinned"]:
            self.settings["pinned"].remove(icon.desktop_path)
            self.save_settings()
            icon.pinned = False

            if not icon.running_windows:
                self.icon_list.icons.remove(icon)
                self.dock.update_geometry()

            self.dock.drawing_area.queue_draw()

    def _open_settings(self):
        log("[SETTINGS] Open settings dialog")
        # TODO: реализовать диалог настроек

    def _find_desktop_path(self, identifier):
        if not identifier:
            return None

        desktop_paths = [
            os.path.expanduser("~/.local/share/applications"),
            "/usr/share/applications",
            "/usr/local/share/applications",
            GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP),
        ]

        desktop_paths = [p for p in desktop_paths if p]

        for base_path in desktop_paths:
            if not os.path.exists(base_path):
                continue

            for filename in os.listdir(base_path):
                if filename.endswith(".desktop"):
                    filepath = os.path.join(base_path, filename)
                    try:
                        keyfile = GLib.KeyFile()
                        keyfile.load_from_file(filepath, GLib.KeyFileFlags.NONE)

                        try:
                            wm_class = keyfile.get_string("Desktop Entry", "StartupWMClass")
                            if wm_class and wm_class.lower() == identifier.lower():
                                return filepath
                        except:
                            pass

                        if filename.replace(".desktop", "").lower() == identifier.lower():
                            return filepath

                    except:
                        continue

        return None
