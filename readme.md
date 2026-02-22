# BrujoDock, v. 26.2

**A universal dock for Linux** — fast, customizable, plugin-based.

Released 22.02.26

## System dependencies

### Debian/Ubuntu/Mint

```bash
sudo apt update
sudo apt install python3-gi python3-gi-cairo python3-pytzdata gir1.2-gtk-3.0\
    gir1.2-wnck-3.0 gir1.2-gnomedesktop-3.0 libcairo2-dev
```

### Fedora

```bash
sudo dnf install python3-gobject python3-gobject-cairo python3-pytzdata \
    gtk3 libwnck3 cairo-devel
```

### Arch Linux

```bash
sudo pacman -S python-gobject python-cairo python-pytzdata gtk3 libwnck cairo
```

### OpenSUSE

```bash
sudo zypper install python3-gobject python3-gobject-cairo python3-pytzdata \
    gtk3 libwnck-3-0 cairo-devel
```

## Dependencies checking

```bash
python3 -c "from gi.repository import Gtk, Wnck; import cairo, pytz; print('✅ All dependencies were found')"
```

## Required versions

- Python: 3.9+
- PyGObject: 3.42.0+ 
- PyCairo: 1.20.0+
- pytz: 2022.0+

Tested on Linux Mint 22.3 Cinnamon with versions:

- Python: 3.12.3
- PyGObject: 3.48.2 
- PyCairo: 1.25.1
- pytz: 2024.1

## Languages

- English 
- Русский (Russian)
- Español (Spanish)

Change in: Settings → Advanced → Language

**Attention!** Log supports English language only.

## Settings

Ctrl + Right-click on dock → "Settings"

| Tab          | What                                |
|--------------|-------------------------------------|
| **General**  | Dock height, padding, corner radius |
| **Plugins**  | Enable/disable plugins, reorder     |
| **Advanced** | Language, log mode                  |

## Plugins

Now dock includes 4 plugins:

| Plugin             | Description                         |
|--------------------|-------------------------------------|
| **Icon Panel**     | Pinned apps, running apps indicator |
| **Clock**          | Time, date, multiple timezones      |
| **SysMon**         | CPU, RAM, temperature               |
| **Battery Status** | Battery level, charging status      |

## Troubleshooting

| Problem                    | Solution                                                            |
|----------------------------|---------------------------------------------------------------------|
| **Dock doesn't start**     | Check dependencies: ```python3 -c "from gi.repository import Gtk``` |
| **Icons not showing**      | Check if apps are installed                                         |
| **Clock shows wrong time** | Check system timezone                                               |
| **Plugin doesn't working** | Enable in Settings → Plugins                                        |

## Known issues

**When you pin AIMP icon sometimes you need dock restart for display this icon.**

AIMP for Linux now is in alpha testing. Please wait at least for release candidate.
