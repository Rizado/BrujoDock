#!/usr/bin/env python3
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from core.dock import BrujoDock

def main():
    dock = BrujoDock()
    Gtk.main()

if __name__ == "__main__":
    main()

