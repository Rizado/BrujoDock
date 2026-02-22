import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib
from .settings import load_core
from .strut_manager import StrutManager
from .utils import init_logger, log
from .i18n import init_i18n, _, get_available_languages


class BrujoDock:
    VERSION = "26.2"

    def __init__(self):
        self._plugin_rects = []  # (plugin, x, y, w, h)
        self.settings = load_core()
        init_logger(self)
        init_i18n(self.settings.get("language", None), dock=self)

        log([lang[0] for lang in get_available_languages()])

        max_radius = max(self.settings.get("dock_padding_x", 16), self.settings.get("dock_padding_y", 4))
        radius = self.settings.get("corner_radius", 4)

        self.settings["corner_radius"] = max(0, min(max_radius, radius))

        self.window = Gtk.Window(
            type=Gtk.WindowType.TOPLEVEL,
            decorated=False,
            skip_taskbar_hint=True,
            skip_pager_hint=True,
            resizable=False,
            app_paintable=True,
        )
        screen = self.window.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.window.set_visual(visual)
        else:
            log("[WARN] Compositing is not available - transparency is disabled")

        self.window.set_keep_below(True)
        self.window.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.window.stick()

        self.window.set_title("BrujoDock")

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.connect("draw", self.on_draw)
        self.drawing_area.set_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        self.strut_manager = StrutManager(self)

        self.window.add(self.drawing_area)
        self.window.show_all()

        self.load_plugins()
        self.drawing_area.connect("button-press-event", self.on_button_press)
        self.update_geometry()

    def update_geometry(self):
        visual = [p for p in self.plugins if p.enabled]
        if not visual:
            total_w = self.settings["dock_padding_x"] * 2
            total_h = self.settings["default_height"] + self.settings["dock_padding_y"] * 2
        else:
            total_w = self.settings["dock_padding_x"]
            max_h = 0
            for i, p in enumerate(visual):
                w, h = p.get_preferred_size()
                max_h = max(max_h, h)
                total_w += w
                if i < len(visual) - 1:
                    total_w += self.settings["dock_spacing"]
            total_w += self.settings["dock_padding_x"]
            total_h = max_h + self.settings["dock_padding_y"] * 2

        self.window.set_size_request(total_w, total_h)

        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor()
        geom = monitor.get_geometry()
        x = geom.x + (geom.width - total_w) // 2
        y = geom.y + geom.height - total_h - 1
        self.window.move(x, y)

        self.strut_manager.update(total_h)

    def on_draw(self, widget, cr):
        total_w = widget.get_allocated_width()
        total_h = widget.get_allocated_height()

        cr.set_source_rgba(0, 0, 0, 0.666)
        radius = self.settings.get("corner_radius", 0)
        self._draw_rounded_rectangle(cr, 0, 0, total_w, total_h, radius)
        cr.fill()

        for plugin, x, y, w, h in self._get_plugin_layout(total_w, total_h):
            self._plugin_rects.append((plugin, x, y, w, h))
            cr.save()
            cr.rectangle(x, y, w, h)
            cr.translate(x, y)
            cr.clip()
            plugin.on_draw(cr, w, h)
            cr.restore()

    def on_button_press(self, widget, event):
        target_plugin = None
        for plugin, x, y, w, h in self._plugin_rects:
            if x <= event.x <= x + w and y <= event.y <= y + h:
                target_plugin = plugin
                break

        if event.button == 3:
            if event.state & Gdk.ModifierType.CONTROL_MASK:
                self.show_context_menu(event, target_plugin)
            else:
                if target_plugin and hasattr(target_plugin, 'on_right_click'):
                    target_plugin.on_right_click(event)
            return True
        return False

    def show_context_menu(self, event, plugin=None):
        menu = Gtk.Menu()

        about = Gtk.MenuItem(label=_("About"))
        about.connect("activate", lambda _: self.show_about())
        menu.append(about)

        settings = Gtk.MenuItem(label=_("Settings"))
        settings.connect("activate", lambda _: self.show_settings())
        menu.append(settings)

        if plugin is not None:
            settings_item = Gtk.MenuItem(label=f'{_("Settings")}: {plugin.description}')
            settings_item.connect("activate", lambda _: self.open_plugin_settings(plugin))
            menu.append(settings_item)

        quit_item = Gtk.MenuItem(label=_("Quit"))
        quit_item.connect("activate", lambda _: Gtk.main_quit())
        menu.append(quit_item)

        menu.show_all()
        menu.popup_at_pointer(event)

    def show_about(self):
        dialog = Gtk.AboutDialog()

        dialog.set_program_name("BrujoDock")
        dialog.set_version("26.2")
        dialog.set_comments("A universal dock for Linux")
        dialog.set_authors(["Vitalii Chubatyi"])
        dialog.set_website("https://chubatyi.name/")
        dialog.set_website_label("Personal site")

        dialog.set_position(Gtk.WindowPosition.CENTER)

        dialog.set_transient_for(self.window)
        dialog.run()
        dialog.destroy()

    def show_settings(self):
        from core.settings_dock import SettingsDialog

        dialog = SettingsDialog(self)
        dialog.run()
        dialog.destroy()

    def load_plugins(self):
        import os
        import importlib.util

        plugins_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")
        plugins_config = self.settings.get("plugins", {})

        self.plugins = []

        for plugin_name, config in plugins_config.items():
            enabled = config.get("enabled", True)

            if not enabled:
                log(f"[PLUGIN] Skipped (disabled): {plugin_name}")
                continue

            try:
                plugin_path = os.path.join(plugins_dir, plugin_name, "plugin.py")
                spec = importlib.util.spec_from_file_location(f"plugins.{plugin_name}.plugin", plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                plugin = module.Plugin(self)
                self.plugins.append(plugin)
                log(f"[PLUGIN] Loaded: {plugin.name} v{plugin.version}")
            except Exception as e:
                log(f"[PLUGIN] Load error: {plugin_name}: {e}")

    def reload_plugins(self):
        log("[PLUGIN] Plugins reloading...")

        for plugin in self.plugins:
            try:
                if hasattr(plugin, '__del__'):
                    plugin.__del__()
            except:
                pass
        self.plugins.clear()

        self.drawing_area.queue_draw()

        self.load_plugins()

        self.update_geometry()
        self.drawing_area.queue_draw()

        log("[PLUGIN] Plugins reloaded")

    def _get_plugin_layout(self, total_w: int, total_h: int):
        visual = [p for p in self.plugins if p.enabled]
        if not visual:
            return []

        max_h = max(p.get_preferred_size()[1] for p in visual)
        pad_y = self.settings["dock_padding_y"]
        actual_h = max_h + pad_y * 2

        layout = []
        x = self.settings["dock_padding_x"]
        for i, plugin in enumerate(visual):
            w, h = plugin.get_preferred_size()
            y = (actual_h - h) // 2
            layout.append((plugin, x, y, w, h))
            x += w
            if i < len(visual) - 1:
                x += self.settings["dock_spacing"]
        return layout

    def open_plugin_settings(self, plugin):
        plugin.show_settings_dialog()

    def _draw_rounded_rectangle(self, cr, x, y, width, height, radius):
        radius = max(0, min(radius, width / 2, height / 2))

        if radius == 0:
            cr.rectangle(x, y, width, height)
            return
        cr.move_to(x + radius, y)
        cr.line_to(x + width - radius, y)
        cr.arc(x + width - radius, y + radius, radius, 3.14159 * 1.5, 3.14159 * 2.0)
        cr.line_to(x + width, y + height - radius)
        cr.arc(x + width - radius, y + height - radius, radius, 0, 3.14159 * 0.5)
        cr.line_to(x + radius, y + height)
        cr.arc(x + radius, y + height - radius, radius, 3.14159 * 0.5, 3.14159)
        cr.line_to(x, y + radius)
        cr.arc(x + radius, y + radius, radius, 3.14159, 3.14159 * 1.5)
        cr.close_path()

    def save_settings(self):
        import json
        import os

        config_dir = os.path.expanduser("~/.config/BrujoDock")
        config_path = os.path.join(config_dir, "core.json")

        os.makedirs(config_dir, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(self.settings, f, indent=2)

        log(f"[SETTINGS] Saved: {config_path}")

