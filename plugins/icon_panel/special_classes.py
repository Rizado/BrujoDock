from core.utils import log

SPECIAL_RES_CLASSES = {
    "vivaldi-stable": "vivaldi",
    "vivaldi-snapshot": "vivaldi",
    "vivaldi-nightly": "vivaldi",
    "vivaldi": "vivaldi",
    "gnome-terminal-server": "gnome-terminal",
    "jetbrains-pycharm": "pycharm",
    "jetbrains-pycharm-ce": "pycharm",
    "jetbrains-idea": "idea",
    "jetbrains-clion": "clion",
    "thunderbird-bin": "thunderbird",
    "firefox-bin": "firefox",
    "google-chrome": "chrome",
    "chromium-browser": "chromium",
    "code": "vscode",
    "code-oss": "vscode",
    "doublecmd64": "doublecmd",
    "nemo": "nemo",
}

ICON_NAMES = {
    "libreoffice-writer": "libreoffice-writer",
    "libreoffice-calc": "libreoffice-calc",
    "libreoffice-impress": "libreoffice-impress",
    "libreoffice-draw": "libreoffice-draw",
    "libreoffice-base": "libreoffice-base",
    "libreoffice-math": "libreoffice-math",
    "libreoffice": "libreoffice",

    "libreoffice-calc-fallback": "libreoffice",
}


def get_icon_name_for_identifier(identifier: str) -> str:
    if identifier in ICON_NAMES:
        return ICON_NAMES[identifier]

    if identifier.startswith("libreoffice-"):
        return identifier
    elif identifier == "libreoffice":
        return "libreoffice"

    return identifier

def normalize_identifier(identifier: str) -> str:
    if not identifier:
        return ""
    key = identifier.lower()
    return SPECIAL_RES_CLASSES.get(key, key)

def get_chromium_identifier(window) -> str:
    try:
        pid = window.get_pid()
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmd = f.read().replace(b"\0", b" ").decode()
            if "--app=" in cmd:
                app = cmd.split("--app=")[-1].split()[0].strip('"')
                base = normalize_identifier(window.get_class_group().get_res_class())
                return f"{base}-{hash(app) % 1000}"
    except Exception:
        pass
    return normalize_identifier(window.get_class_group().get_res_class())


def get_libreoffice_identifier(window) -> str:
    try:
        cg = window.get_class_group()

        instance = cg.get_name().lower() if cg else ""
        res_class = cg.get_res_class().lower() if cg else ""
        title = window.get_name().lower()

        log(f"[LIBREOFFICE] instance='{instance}' | class='{res_class}' | title='{title}'")

        if "calc" in instance or "scalc" in instance:
            return "libreoffice-calc"
        elif "base" in instance or "sbase" in instance:
            return "libreoffice-base"
        elif "impress" in instance or "simpress" in instance:
            return "libreoffice-impress"
        elif "draw" in instance or "sdraw" in instance:
            return "libreoffice-draw"
        elif "math" in instance or "smath" in instance:
            return "libreoffice-math"
        elif "writer" in instance or "swriter" in instance:
            return "libreoffice-writer"

        if "calc" in title:
            return "libreoffice-calc"
        elif "base" in title:
            return "libreoffice-base"
        elif "impress" in title:
            return "libreoffice-impress"
        elif "draw" in title:
            return "libreoffice-draw"
        elif "math" in title:
            return "libreoffice-math"
        else:
            return "libreoffice-writer"

    except Exception as e:
        log(f"[LIBREOFFICE] Ошибка: {e}")
        return "libreoffice"