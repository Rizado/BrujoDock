import json
import os
from gi.repository import Gtk, Gdk
from .utils import log
from core.i18n import _, get_available_languages
from core.i18n import set_language


class SettingsDialog:
    def __init__(self, dock):
        self.dock = dock
        self.settings = dock.settings
        self.plugins_order = self.settings.get("plugins_order", [])
        self.plugins_enabled = self.settings.get("plugins_enabled", {})

        # Создаём диалог
        self.dialog = Gtk.Dialog(
            title=_("BrujoDock Settings"),
            transient_for=dock.window,
            flags=Gtk.DialogFlags.MODAL
        )
        self.dialog.set_default_size(500, 450)
        self.dialog.set_position(Gtk.WindowPosition.CENTER)

        content = self.dialog.get_content_area()
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(0)  # ← Убрали отступ снизу (кнопки сами имеют margin)
        content.set_spacing(0)  # ← Убрали spacing (кнопки сами имеют margin_top)

        # Вкладки (Notebook)
        notebook = Gtk.Notebook()
        notebook.set_margin_bottom(0)  # ← Убрали отступ

        # Вкладка 1: Основные настройки
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_margin_bottom(0)
        self._create_settings_form(main_box)
        notebook.append_page(main_box, Gtk.Label(label=_("General")))

        # Вкладка 2: Плагины
        plugins_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        plugins_box.set_margin_bottom(0)
        self._create_plugins_tab(plugins_box)
        notebook.append_page(plugins_box, Gtk.Label(label=_("Plugins")))

        # Вкладка 3: Технические
        tech_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        tech_box.set_margin_bottom(8)
        self._create_technical_tab(tech_box)
        notebook.append_page(tech_box, Gtk.Label(label=_("Advanced")))

        content.add(notebook)

        # Кнопки действий
        self._create_action_buttons(content)

        self.dialog.connect("response", self._on_response)

    def destroy(self):
        """Уничтожает диалог"""
        self.dialog.destroy()

    def _create_settings_form(self, container):
        """Создаёт форму настроек"""
        # ← Вертикальный Box для всех строк
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_spacing(12)
        main_box.set_margin_start(8)
        main_box.set_margin_end(8)
        main_box.set_margin_top(8)
        main_box.set_margin_bottom(8)

        # ← Список настроек (название, ключ, min, max, default)
        settings_list = [
            (_("Item Height:"), "default_height", 16, 128, 32),
            (_("Dock Padding (Horizontal):"), "dock_padding_x", 0, 64, 16),
            (_("Dock Padding (Vertical):"), "dock_padding_y", 0, 64, 4),
            (_("Corner Radius:"), "corner_radius", 0, 32, 8),
            (_("Item Spacing:"), "dock_spacing", 0, 32, 2),
        ]

        for label_text, key, min_val, max_val, default_val in settings_list:
            # ← Горизонтальный Box для каждой строки
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            row_box.set_spacing(12)

            # ← Label (растягивается)
            label = Gtk.Label(label=label_text)
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)  # ← Растягивается, толкает спин вправо
            row_box.pack_start(label, True, True, 0)

            # ← SpinButton (не растягивается)
            spin = Gtk.SpinButton.new_with_range(min_val, max_val, 1)
            spin.set_value(self.settings.get(key, default_val))
            spin.set_name(key)
            spin.set_size_request(60, -1)  # ← Фиксированная ширина
            row_box.pack_end(spin, False, False, 0)  # ← Pack_end для надёжности

            main_box.pack_start(row_box, False, False, 0)

        container.add(main_box)

    def _create_plugins_tab(self, container):
        """Создаёт вкладку управления плагинами"""
        # Список плагинов
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)  # ← Для кнопок Вверх/Вниз
        listbox.get_style_context().add_class("frame")

        # Скролл
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        scrolled.add(listbox)

        container.pack_start(scrolled, True, True, 0)

        # Загружаем плагины
        self._load_plugins_list(listbox)

        # Кнопки управления
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_spacing(8)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(8)

        btn_up = Gtk.Button(label=_("↑ Up"))
        btn_up.connect("clicked", self._on_plugin_up)
        btn_up.set_name("btn_plugin_up")

        btn_down = Gtk.Button(label=_("↓ Down"))
        btn_down.connect("clicked", self._on_plugin_down)
        btn_down.set_name("btn_plugin_down")

        button_box.pack_start(btn_up, False, False, 0)
        button_box.pack_start(btn_down, False, False, 0)

        container.pack_start(button_box, False, False, 0)

        self.plugins_listbox = listbox

    def _create_technical_tab(self, container):
        """Создаёт вкладку технических настроек"""
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_spacing(12)
        main_box.set_margin_start(8)
        main_box.set_margin_end(8)
        main_box.set_margin_top(8)
        main_box.set_margin_bottom(8)

        # ← Language (dynamic from files)
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        label = Gtk.Label(label=_("Language:"))
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        row_box.pack_start(label, True, True, 0)

        # ← Динамический список из файлов
        combo = Gtk.ComboBoxText()

        available_langs = get_available_languages()  # ← Читает файлы!
        for code, native_name, eng_name in available_langs:
            combo.append(code, f"{native_name} ({eng_name})")

        current_lang = self.settings.get("language", "en")
        combo.set_active_id(current_lang)
        combo.set_name("language")

        row_box.pack_end(combo, False, False, 0)
        main_box.pack_start(row_box, False, False, 0)

        self.language_combo = combo

        # ← Режим лога (выпадающий список)
        row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        row_box.set_spacing(12)

        label = Gtk.Label(label=_("Log Mode:"))
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        row_box.pack_start(label, True, True, 0)

        # Выпадающий список
        combo = Gtk.ComboBoxText()
        combo.append("none", _("None"))
        combo.append("console", _("Console"))
        # combo.append("file", _("Файл")  # ← Задел на будущее

        current_mode = self.settings.get("log_mode", "none")
        combo.set_active_id(current_mode)
        combo.set_name("log_mode")
        combo.set_size_request(150, -1)

        row_box.pack_end(combo, False, False, 0)
        main_box.pack_start(row_box, False, False, 0)

        # ← Описание (серым цветом)
        desc_label = Gtk.Label()
        desc_label.set_markup(
            "<span color='#888888' size='small'>" +
            _("«None» — logging disabled") + "\n" +
            _("«Console» — output to terminal") + "\n" +
            _("«File» — write to file (WIP)") +
            "</span>"
        )
        desc_label.set_halign(Gtk.Align.START)
        desc_label.set_margin_top(8)
        main_box.pack_start(desc_label, False, False, 0)

        container.add(main_box)

        # Сохраняем ссылку для чтения настроек
        self.log_mode_combo = combo

    def _load_plugins_list(self, listbox):
        """Загружает список плагинов в ListBox"""
        import os

        # Очищаем список
        for row in listbox.get_children():
            row.destroy()

        # Путь к плагинам
        plugins_dir = os.path.join(os.path.dirname(__file__), "../plugins")

        # Получаем доступные плагины
        available_plugins = []
        if os.path.exists(plugins_dir):
            for item in os.listdir(plugins_dir):
                item_path = os.path.join(plugins_dir, item)
                if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "plugin.py")):
                    available_plugins.append(item)

        # Получаем настройки из конфига
        plugins_config = self.settings.get("plugins", {})

        # ← Порядок из конфига + новые плагины
        ordered_plugins = []

        # Сначала из конфига (сохраняем порядок)
        for name in plugins_config.keys():
            if name in available_plugins:
                ordered_plugins.append(name)
                available_plugins.remove(name)

        # Новые плагины добавляем в конец (enabled=False)
        for name in available_plugins:
            ordered_plugins.append(name)
            plugins_config[name] = {"enabled": False}

        # Обновляем конфиг
        self.settings["plugins"] = plugins_config

        # Создаём строки списка
        for plugin_name in ordered_plugins:
            row = self._create_plugin_row(plugin_name)
            listbox.add(row)

    def _create_plugin_row(self, plugin_name):
        """Создаёт строку списка для плагина"""
        row = Gtk.ListBoxRow()
        row.plugin_name = plugin_name  # ✅ Атрибут Python

        # Box для содержимого
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.set_margin_start(8)
        box.set_margin_end(8)
        box.set_margin_top(4)
        box.set_margin_bottom(4)
        box.set_spacing(12)

        # Кнопка настроек (шестерёнка)
        btn_settings = Gtk.Button()
        icon = Gtk.Image.new_from_icon_name("emblem-system-symbolic", Gtk.IconSize.BUTTON)
        btn_settings.add(icon)
        btn_settings.set_tooltip_text(_("Plugin Settings"))
        btn_settings.connect("clicked", self._on_plugin_settings, plugin_name)
        box.pack_start(btn_settings, False, False, 0)

        # Название плагина
        label = Gtk.Label(label=plugin_name.replace("_", " ").title())
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(True)
        box.pack_start(label, True, True, 0)

        # Switch для включения
        plugins_config = self.settings.get("plugins", {})
        plugin_config = plugins_config.get(plugin_name, {"enabled": False})

        switch = Gtk.Switch()
        switch.set_active(plugin_config.get("enabled", False))
        switch.connect("notify::active", self._on_plugin_toggled, plugin_name)
        box.pack_end(switch, False, False, 0)

        row.add(box)
        return row

    def _on_plugin_settings(self, button, plugin_name):
        """Открывает настройки плагина"""
        # Находим плагин в доке
        for plugin in self.dock.plugins:
            if plugin.get_plugin_name() == plugin_name:
                if hasattr(plugin, 'show_settings_dialog'):
                    plugin.show_settings_dialog()
                else:
                    log(f"[{plugin_name}] There is no settings dialog")
                break

    def _on_plugin_toggled(self, switch, param, plugin_name):
        """Обработчик переключения плагина"""
        plugins_config = self.settings.get("plugins", {})
        if plugin_name in plugins_config:
            plugins_config[plugin_name]["enabled"] = switch.get_active()
        log(f"[PLUGIN] {plugin_name}: {'enabled' if switch.get_active() else 'disabled'}")

    def _on_plugin_up(self, button):
        """Перемещает плагин вверх"""
        self._swap_plugins(-1)

    def _on_plugin_down(self, button):
        """Перемещает плагин вниз"""
        self._swap_plugins(1)

    def _swap_plugins(self, direction):
        """Меняет местами плагины"""
        selected = self.plugins_listbox.get_selected_row()
        if not selected:
            return

        # ← 1. Сохраняем имя плагина до перемещения
        plugin_name = selected.plugin_name

        plugins_config = self.settings.get("plugins", {})
        plugin_keys = list(plugins_config.keys())

        idx = plugin_keys.index(plugin_name) if plugin_name in plugin_keys else -1
        if idx == -1:
            return

        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(plugin_keys):
            return

        # Меняем порядок в словаре
        keys_list = list(plugins_config.items())
        keys_list[idx], keys_list[new_idx] = keys_list[new_idx], keys_list[idx]

        self.settings["plugins"] = dict(keys_list)

        # Перезагружаем список
        self._load_plugins_list(self.plugins_listbox)
        self.plugins_listbox.show_all()

        # ← 2. Восстанавливаем выделение
        self._select_plugin_row(plugin_name)

    def _select_plugin_row(self, plugin_name):
        """Находит и выделяет строку с указанным плагином"""
        for row in self.plugins_listbox.get_children():
            if hasattr(row, 'plugin_name') and row.plugin_name == plugin_name:
                self.plugins_listbox.select_row(row)
                break

    def _create_action_buttons(self, container):
        """Создаёт кнопки действий в нижней части окна"""
        # ← Убрали сепаратор (красная линия)

        # Box для кнопок
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_spacing(8)
        button_box.set_halign(Gtk.Align.END)  # ← Прижат вправо
        button_box.set_valign(Gtk.Align.END)  # ← Прижат к низу
        button_box.set_margin_top(16)  # ← Отступ сверху (как от "Применить" до правого края)
        button_box.set_margin_bottom(8)  # ← Отступ снизу (как от "Применить" до правого края)
        button_box.set_margin_end(8)  # ← Отступ справа

        # Кнопка Применить
        btn_apply = Gtk.Button(label=_("Apply"))
        btn_apply.connect("clicked", self._on_apply)
        button_box.pack_end(btn_apply, False, False, 0)

        # Кнопка Отмена
        btn_cancel = Gtk.Button(label=_("Cancel"))
        btn_cancel.connect("clicked", self._on_cancel)
        button_box.pack_end(btn_cancel, False, False, 0)

        # Кнопка OK
        btn_ok = Gtk.Button(label=_("OK"))
        btn_ok.get_style_context().add_class("suggested-action")
        btn_ok.connect("clicked", self._on_ok)
        button_box.pack_end(btn_ok, False, False, 0)

        container.pack_end(button_box, False, False, 0)  # ← Pack_end для привязки к низу

    def _on_ok(self, button):
        """Сохраняет настройки и закрывает диалог"""
        self._save_settings()
        self.dialog.destroy()

    def _on_apply(self, button):
        """Сохраняет настройки без закрытия"""
        self._save_settings()

    def _on_cancel(self, button):
        """Закрывает без сохранения"""
        self.dialog.destroy()

    def _on_response(self, dialog, response):
        """Обрабатывает стандартные ответы (на всякий случай)"""
        pass  # Теперь используем свои кнопки

    def _save_settings(self):
        """Сохраняет настройки из виджетов"""
        content = self.dialog.get_content_area()

        # ← 1. Находим Notebook (первый уровень)
        notebook = None
        for widget in content.get_children():
            if isinstance(widget, Gtk.Notebook):
                notebook = widget
                break

        if not notebook:
            log("[SETTINGS] Notebook not found!")
            return

        # ← 2. Вкладка "Основные" (индекс 0)
        page_main = notebook.get_nth_page(0)
        if page_main:
            for child in page_main.get_children():
                if isinstance(child, Gtk.Box):  # main_box
                    for row_child in child.get_children():
                        if isinstance(row_child, Gtk.Box):  # row_box
                            for item in row_child.get_children():
                                if isinstance(item, Gtk.SpinButton):
                                    name = item.get_name()
                                    value = int(item.get_value())
                                    self.settings[name] = value

        # ← 3. Вкладка "Технические" (индекс 2)
        page_tech = notebook.get_nth_page(2)
        if page_tech:
            for child in page_tech.get_children():
                if isinstance(child, Gtk.Box):  # main_box
                    for row_child in child.get_children():
                        if isinstance(row_child, Gtk.Box):  # row_box
                            for item in row_child.get_children():
                                if isinstance(item, Gtk.ComboBoxText) and item.get_name() == "language":
                                    self.settings["language"] = item.get_active_id()
                                elif isinstance(item, Gtk.ComboBoxText) and item.get_name() == "log_mode":
                                    self.settings["log_mode"] = item.get_active_id()

        # ← 4. Сохраняем
        self.dock.save_settings()

        # ← 5. Применяем язык
        set_language(self.settings.get("language", "en"), dock=self.dock)

        # ← 6. Обновляем док
        self.dock.update_geometry()
        self.dock.drawing_area.queue_draw()
        self.dock.reload_plugins()

        log(f"[SETTINGS] Applied: language={self.settings.get('language')}")

    def run(self):
        """Показывает диалог"""
        self.dialog.show_all()
        self.dialog.run()