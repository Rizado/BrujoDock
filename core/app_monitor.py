# core/app_monitor.py (минимальная версия)
import gi

gi.require_version('Wnck', '3.0')
from gi.repository import Wnck


class AppMonitor:
    def __init__(self, on_app_added, on_app_removed):
        self.on_app_added = on_app_added
        self.on_app_removed = on_app_removed

        # Сначала инициализируем active_apps
        self.active_apps = {}

        # Потом настраиваем WNCK
        self.screen = Wnck.Screen.get_default()
        self.screen.force_update()
        self.screen.connect("window-opened", self._on_window_opened)
        self.screen.connect("window-closed", self._on_window_closed)

        # Теперь можно обрабатывать существующие окна
        for window in self.screen.get_windows():
            self._on_window_opened(self.screen, window)

    def _on_window_opened(self, screen, window):
        wtype = window.get_window_type()
        if wtype in (Wnck.WindowType.DESKTOP, Wnck.WindowType.DOCK, Wnck.WindowType.SPLASHSCREEN):
            return

        app = window.get_application()
        if not app:
            return

        # Получаем ВСЕ окна этого приложения
        windows = app.get_windows()

        if app not in self.active_apps:
            self.active_apps[app] = {'windows': windows}
            self.on_app_added(app, windows)
        else:
            # Обновляем список окон
            self.active_apps[app]['windows'] = windows
            self.on_app_added(app, windows)  # обновляем UI

    def _on_window_closed(self, screen, window):
        # Находим app по window
        for app, data in list(self.active_apps.items()):
            if window in data['windows']:
                # Обновляем список окон
                windows = app.get_windows()
                if windows:
                    self.active_apps[app]['windows'] = windows
                    self.on_app_added(app, windows)  # обновляем счётчик
                else:
                    del self.active_apps[app]
                    self.on_app_removed(app)
                break

    def _add_or_update_by_pid(self, pid, windows):
        app = self.pid_to_app[pid]

        # Находим основное приложение (по первому PID)
        main_app = None
        for a, pids in self.app_to_pids.items():
            if pid in pids:
                main_app = a
                break

        if main_app is None:
            # Новое приложение
            main_app = app
            self.app_to_pids[main_app] = {pid}
            self.active_apps[main_app] = {'windows': [], 'pids': {pid}}

        # Добавляем окна
        self.active_apps[main_app]['windows'].extend(windows)
        self.active_apps[main_app]['pids'].add(pid)

        # Убираем дубли окон
        self.active_apps[main_app]['windows'] = list({id(w): w for w in self.active_apps[main_app]['windows']}.values())

        self.on_app_added(main_app, self.active_apps[main_app]['windows'])