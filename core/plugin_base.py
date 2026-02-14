# core/plugin_base.py
from abc import ABC
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from gi.repository import Gtk, Gdk
    from .brujo_dock import BrujoDock

class PluginBase(ABC):
    name: str = "Unnamed Plugin"
    version: str = "0.1"
    enabled: bool = True

    def __init__(self, dock: 'BrujoDock'):
        self.dock = dock
        self.settings: Dict[str, Any] = {}

    def on_init(self) -> None:
        """Вызывается после создания плагина."""
        pass

    def destroy(self) -> None:
        """Очистка ресурсов."""
        pass

    def on_draw(self, cr, width: int, height: int) -> None:
        """Рисование поверх дока (cairo context)."""
        pass

    def on_click(self, event: 'Gdk.EventButton') -> bool:
        """Обработка клика. Вернуть True, если событие перехвачено."""
        return False

    def on_hover(self, x: float, y: float) -> None:
        """Курсор над доком."""
        pass

    def on_leave(self) -> None:
        """Курсор покинул док."""
        pass

    def on_tick(self) -> None:
        """Вызывается раз в секунду."""
        pass

    def get_settings_widget(self) -> Optional['Gtk.Widget']:
        """Возвращает виджет для вкладки настроек."""
        return None

    def on_settings_changed(self, new_settings: Dict[str, Any]) -> None:
        """Вызывается при изменении настроек."""
        self.settings.update(new_settings)
