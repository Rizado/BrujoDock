from core.plugin_base import PluginBase


class Plugin(PluginBase):
    name = "Apps Menu"
    version = "0.1"

    def get_preferred_size(self) -> tuple[int, int]:
        return (40, 32)

    def on_draw(self, cr, width: int, height: int):
        cr.set_source_rgb(1, 1, 0)
        cr.rectangle(0, 0, width, height)
        cr.fill()
