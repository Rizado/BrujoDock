from .app_icon import AppIcon
from .special_classes import normalize_identifier, get_chromium_identifier, get_libreoffice_identifier
from  core.utils import log


class AppIconList:
    def __init__(self, pinned_paths):
        self.icons = []
        self.pinned_paths = pinned_paths
        # Предзагружаем закреплённые иконки
        for path in pinned_paths:
            icon = AppIcon.from_desktop_file(path, pinned=True)
            if icon:
                log(f"[PINNED] {icon.name} | identifier='{icon.identifier}'")
                self.icons.append(icon)

    def add_window(self, wm_class, app, window):
        if "libreoffice" in wm_class.lower() or "soffice" in wm_class.lower():
            identifier = get_libreoffice_identifier(window)
        else:
            identifier = normalize_identifier(wm_class)

        for icon in self.icons:
            if icon.identifier == identifier:
                icon.add_window(window)
                return

        new_icon = AppIcon(
            name=window.get_name() or identifier,
            icon_name=identifier,
            identifier=identifier,
            app=app,
            pinned=False
        )
        new_icon.add_window(window)
        self.icons.append(new_icon)

    def remove_window(self, window_ref):
        for icon in self.icons[:]:
            if icon.has_window(window_ref):
                icon.remove_window(window_ref)
                if not icon.is_running() and not icon.pinned:
                    self.icons.remove(icon)
                break

    def _find_icon_by_wm_class(self, wm_class_norm: str):
        if not wm_class_norm:
            return None

        # Сначала ищем по wm_class
        for icon in self.icons:
            if icon and icon.wm_class:
                if icon.wm_class.strip().lower() == wm_class_norm:
                    return icon

        # Fallback: ищем по имени (нормализованному)
        name_norm = wm_class_norm
        for icon in self.icons:
            if icon and icon.name:
                if icon.name.strip().lower() == name_norm:
                    return icon

        return None

    def _create_icon_from_wm_class(self, wm_class: str):
        # Пока просто создаём анонимную иконку
        return AppIcon(name=wm_class or "Unknown", pinned=False)

    def _find_icon_by_desktop_file(self, desktop_file):
        for icon in self.icons:
            if icon and icon.desktop_file == desktop_file:
                return icon
        return None