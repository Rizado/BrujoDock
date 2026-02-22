# BrujoDock, v. 26.2

**Un dock universal para Linux** — rápido, personalizable, basado en complementos.

Lanzado 22.02.26

## Dependencias del sistema

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

## Comprobación de dependencias

```bash
python3 -c "from gi.repository import Gtk, Wnck; import cairo, pytz; print('Se encontraron todas las dependencias')"
```

## Versiones requeridas

- Python: 3.9+
- PyGObject: 3.42.0+ 
- PyCairo: 1.20.0+
- pytz: 2022.0+

Probado en Linux Mint 22.3 Cinnamon con versiones:

- Python: 3.12.3
- PyGObject: 3.48.2 
- PyCairo: 1.25.1
- pytz: 2024.1

## Idiomas

- Inglés (English) 
- Русский (Ruso)
- Español

Cambiar en: Configuración → Avanzado → Idioma

**¡Atención!** Log soporte sólo el idioma inglés.

## Configuración

Clic derecho en el dock → Configuración

| Pestaña          | Qué                                       |
|------------------|-------------------------------------------|
| **General**      | Altura del dock, márgenes, radio de borde |
| **Complementos** | Activar/desactivar, ordenar               |
| **Avanzado**     | Idioma, modo de registro                  |

## Complementos

Ahora el dock incluye 4 complementos:

| Complemento         | Descripción                                  |
|---------------------|----------------------------------------------|
| **Icon Panel**      | Aplicaciones fijadas, indicador de ejecución |
| **Clock**           | Hora, fecha, múltiples zonas horarias        |
| **SysMon**          | CPU, RAM, temperatura                        |
| **Battery Status**  | Nivel de batería, estado de cargando         |

## Troubleshooting

| Problem                              | Solution                                                                |
|--------------------------------------|-------------------------------------------------------------------------|
| **El dock no inicia**                | Verifique dependencias: ```python3 -c "from gi.repository import Gtk``` |
| **Los íconos no se muestran**        | Verifique si las aplicaciones están instaladas                          |
| **El reloj muestra hora incorrecta** | Verifique la zona horaria del sistema                                   |
| **El complemento no funciona**       | Active en Configuración → Complementos                                  |

## Problemas conocidos

**Al fijar el icono de AIMP, a veces es necesario reiniciar el dock para que aparezca.**

AIMP para Linux se encuentra actualmente en fase alfa. Espere al menos la versión candidata.
