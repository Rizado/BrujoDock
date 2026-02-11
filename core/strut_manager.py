# core/strut_manager.py
from gi.repository import GdkX11

try:
    from Xlib import X, display as xdisplay
except ImportError:
    print("⚠️  python-xlib не установлен. Strut недоступен.")
    xdisplay = None


def set_strut(window, bottom_height):
    if not xdisplay:
        return False

    try:
        gdk_window = window.get_window()
        if not gdk_window or not hasattr(gdk_window, 'get_xid'):
            return False

        xid = gdk_window.get_xid()
        d = xdisplay.Display()
        xlib_window = d.create_resource_object('window', xid)

        atom_strut = d.intern_atom("_NET_WM_STRUT")
        atom_cardinal = d.get_atom("CARDINAL")
        strut = [0, 0, 0, bottom_height]

        # Без именованных аргументов!
        xlib_window.change_property(atom_strut, atom_cardinal, 32, strut)

        d.flush()
        return True

    except Exception as e:
        print(f"[WARN] Ошибка установки strut: {e}")
        return False