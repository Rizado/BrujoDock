# core/plugin_manager.py
import os
import importlib
from .plugin_base import PluginBase

class PluginManager:
    def __init__(self, dock):
        self.dock = dock
        self.plugins: list[PluginBase] = []
        self.plugin_modules = {}

    def load_plugins(self, plugins_dir="plugins"):
        """Загружает все плагины из папки."""
        if not os.path.exists(plugins_dir):
            return

        for item in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, item)
            if os.path.isdir(plugin_path) and os.path.exists(os.path.join(plugin_path, "plugin.py")):
                try:
                    module = importlib.import_module(f"plugins.{item}.plugin")
                    if hasattr(module, "Plugin"):
                        plugin_class = module.Plugin
                        if issubclass(plugin_class, PluginBase):
                            plugin = plugin_class(self.dock)
                            plugin.on_init()
                            self.plugins.append(plugin)
                            self.plugin_modules[item] = plugin
                            print(f"[PLUGIN] Загружен: {plugin.name} v{plugin.version}")
                        else:
                            print(f"[PLUGIN] Ошибка: {item} не наследует PluginBase")
                    else:
                        print(f"[PLUGIN] Ошибка: {item} не содержит класс Plugin")
                except Exception as e:
                    print(f"[PLUGIN] Не удалось загрузить {item}: {e}")

    def call_plugins(self, method_name: str, *args, **kwargs):
        """Вызывает метод у всех включённых плагинов."""
        for plugin in self.plugins:
            if plugin.enabled:
                try:
                    method = getattr(plugin, method_name, None)
                    if method:
                        result = method(*args, **kwargs)
                        if result is True:  # событие перехвачено
                            return True
                except Exception as e:
                    print(f"[PLUGIN] Ошибка в {plugin.name}.{method_name}: {e}")
        return False

    def destroy_all(self):
        """Очистка всех плагинов."""
        for plugin in self.plugins:
            try:
                plugin.destroy()
            except Exception as e:
                print(f"[PLUGIN] Ошибка при уничтожении {plugin.name}: {e}")