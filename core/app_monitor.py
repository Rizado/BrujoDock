# core/app_monitor.py (минимальная версия)
import gi

gi.require_version('Wnck', '3.0')
from gi.repository import Wnck
import os


def get_exe_path(pid):
    """Возвращает путь к исполняемому файлу по PID или None"""
    if pid <= 0:
        return None
    try:
        exe_path = os.readlink(f"/proc/{pid}/exe")
        return exe_path
    except (OSError, IOError):
        return None


class AppMonitor:
    def __init__(self, on_app_added, on_app_removed):
        self.on_app_added = on_app_added
        self.on_app_removed = on_app_removed

        # Сначала инициализируем active_apps
        self.active_apps = {}
        self.groups = {}
        self.window_to_key = {}  # ← но

        # Потом настраиваем WNCK
        self.screen = Wnck.Screen.get_default()
        self.screen.force_update()
        self.screen.connect("window-opened", self._on_window_opened)
        self.screen.connect("window-closed", self._on_window_closed)

        # Теперь можно обрабатывать существующие окна
        for window in self.screen.get_windows():
            self._on_window_opened(self.screen, window)

    def _on_window_opened(self, screen, window):
        if window.get_pid() == os.getpid():
            return
        wtype = window.get_window_type()
        if wtype in (Wnck.WindowType.DESKTOP, Wnck.WindowType.DOCK, Wnck.WindowType.SPLASHSCREEN):
            return

        app = window.get_application()
        if not app:
            return

        pid = window.get_pid()
        exe_key = get_exe_path(pid)

        # Fallback на WM_CLASS, если PID недоступен
        if not exe_key:
            try:
                cg = window.get_class_group()
                exe_key = cg.get_name() if cg else "unknown"
            except:
                exe_key = "unknown"

        # Сохраняем связь окна → ключ
        self.window_to_key[window] = exe_key

        app = window.get_application()
        if not app:
            return

        if exe_key not in self.groups:
            self.groups[exe_key] = {'app': app, 'exe_key': exe_key}

        # ВСЕГДА берём актуальные окна
        self.groups[exe_key]['windows'] = app.get_windows()
        self.on_app_added(app, self.groups[exe_key]['windows'], exe_key)

    def _on_window_closed(self, screen, window):
        exe_key = self.window_to_key.get(window, "unknown")
        if window in self.window_to_key:
            del self.window_to_key[window]

        if exe_key in self.groups:
            app = self.groups[exe_key]['app']
            windows = app.get_windows()

            if not windows:
                del self.groups[exe_key]
                self.on_app_removed(exe_key)
            else:
                self.groups[exe_key]['windows'] = windows
                self.on_app_added(app, windows, exe_key)

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