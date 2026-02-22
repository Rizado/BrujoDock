# core/strut_manager.py
from gi.repository import Gdk
from .utils import log


try:
    from Xlib import X, display as xdisplay
    HAS_XLIB = True
except ImportError:
    log("⚠️  python-xlib isn't installed. Strut is no available.")
    HAS_XLIB = False

class StrutManager:
    def __init__(self, dock):
        self.dock = dock

    def update(self, total_h = 48):
        if not HAS_XLIB:
            return

        try:
            gdk_window = self.dock.window.get_window()
            if not gdk_window or not hasattr(gdk_window, 'get_xid'):
                return

            xid = gdk_window.get_xid()
            d = xdisplay.Display()
            xlib_window = d.create_resource_object('window', xid)

            atom_strut = d.intern_atom("_NET_WM_STRUT")
            atom_cardinal = d.get_atom("CARDINAL")

            # Только высота дока — остальное 0
#            alloc = self.dock.window.get_allocation()
            strut = [0, 0, 0, total_h]  # left, right, top, bottom

            xlib_window.change_property(atom_strut, atom_cardinal, 32, strut)
            d.flush()

        except Exception as e:
            log(f"[STRUT] Error: {e}")