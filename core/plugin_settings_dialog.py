from gi.repository import Gtk
from .utils import log


class PluginSettingsDialog:
    def __init__(self, plugin):
        from .i18n import _

        self.plugin = plugin
        self.settings = plugin.settings
        self.settings_form = plugin.SETTINGS_FORM

        self.dialog = Gtk.Dialog(
            title=f"{_("Settings")}: {plugin.name.replace('_', ' ').title()}",
            transient_for=plugin.dock.window,
            flags=Gtk.DialogFlags.MODAL
        )
        self.dialog.set_default_size(450, 350)
        self.dialog.set_position(Gtk.WindowPosition.CENTER)

        content = self.dialog.get_content_area()
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(0)
        content.set_spacing(0)

        self._create_settings_form(content)

        self._create_action_buttons(content)

        self.dialog.connect("response", self._on_response)

    def destroy(self):
        self.dialog.destroy()

    def _create_settings_form(self, container):
        from .i18n import _

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_spacing(12)
        main_box.set_margin_start(8)
        main_box.set_margin_end(8)
        main_box.set_margin_top(8)
        main_box.set_margin_bottom(8)

        self.spin_widgets = {}
        self.switch_widgets = {}
        self.entry_widgets = {}
        self.text_widgets = {}

        for field in self.settings_form:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            row_box.set_spacing(12)

            label_text = field.get("label", field["key"])
            translated_text = _(label_text)

            field_type = field.get("type", "spin")
            key = field["key"]
            default = field.get("default", self.settings.get(key, 0))
            current = self.settings.get(key, default)

            label = Gtk.Label(label=translated_text)
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)
            row_box.pack_start(label, True, True, 0)

            if field_type == "spin":
                min_val = field.get("min", 0)
                max_val = field.get("max", 100)
                step = field.get("step", 1)

                spin = Gtk.SpinButton.new_with_range(min_val, max_val, step)
                spin.set_value(current)
                spin.set_size_request(60, -1)
                row_box.pack_end(spin, False, False, 0)

                self.spin_widgets[key] = spin

            elif field_type == "switch":
                switch = Gtk.Switch()
                switch.set_active(current)
                row_box.pack_end(switch, False, False, 0)

                self.switch_widgets[key] = switch

            elif field_type == "entry":
                entry = Gtk.Entry()
                entry.set_text(str(current))
                entry.set_width_chars(20)
                row_box.pack_end(entry, False, False, 0)

                self.entry_widgets[key] = entry

            elif field_type == "text":
                scrolled = Gtk.ScrolledWindow()
                scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
                scrolled.set_min_content_height(80)
                scrolled.set_min_content_width(200)

                text_view = Gtk.TextView()
                text_buffer = text_view.get_buffer()

                if isinstance(current, list):
                    text_buffer.set_text("\n".join(current))
                else:
                    text_buffer.set_text(str(current))

                scrolled.add(text_view)
                row_box.pack_end(scrolled, False, False, 0)

                self.text_widgets[key] = text_buffer

            main_box.pack_start(row_box, False, False, 0)

        container.add(main_box)

    def _create_action_buttons(self, container):
        from .i18n import _

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_spacing(8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_valign(Gtk.Align.END)
        button_box.set_margin_top(16)
        button_box.set_margin_bottom(8)
        button_box.set_margin_end(8)

        btn_apply = Gtk.Button(label=_("Apply"))
        btn_apply.connect("clicked", self._on_apply)
        button_box.pack_end(btn_apply, False, False, 0)

        btn_cancel = Gtk.Button(label=_("Cancel"))
        btn_cancel.connect("clicked", self._on_cancel)
        button_box.pack_end(btn_cancel, False, False, 0)

        btn_ok = Gtk.Button(label=_("OK"))
        btn_ok.get_style_context().add_class("suggested-action")
        btn_ok.connect("clicked", self._on_ok)
        button_box.pack_end(btn_ok, False, False, 0)

        container.pack_end(button_box, False, False, 0)

    def _on_ok(self, button):
        self._save_settings()
        self.dialog.destroy()

    def _on_apply(self, button):
        self._save_settings()

    def _on_cancel(self, button):
        self.dialog.destroy()

    def _on_response(self, dialog, response):
        pass

    def _save_settings(self):
        for key, spin in self.spin_widgets.items():
            self.plugin.settings[key] = int(spin.get_value())

        for key, switch in self.switch_widgets.items():
            self.plugin.settings[key] = switch.get_active()

        for key, entry in self.entry_widgets.items():
            self.plugin.settings[key] = entry.get_text()

        for key, text_buffer in self.text_widgets.items():
            start, end = text_buffer.get_bounds()
            text = text_buffer.get_text(start, end, False)

            lines = [line.strip() for line in text.split("\n")]
            lines = [line for line in lines if line]

            self.plugin.settings[key] = lines

        self.plugin.save_settings()

        self.plugin.dock.reload_plugins()

        log(f"[{self.plugin.name}] Settings were applied")

    def run(self):
        self.dialog.show_all()
        self.dialog.run()