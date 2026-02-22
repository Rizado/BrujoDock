import os
import json
import locale
from .utils import log

_translations = {}
_current_lang = "en"

def init_i18n(lang=None, dock=None):
    global _current_lang, _translations

    if lang is None:
        lang = _detect_language()

    _current_lang = lang

    _translations = _load_core_translations(lang)

    if dock:
        _translations.update(_load_plugin_translations(lang, dock))

    log(f"[I18N] Language: {lang}")

def _detect_language():
    try:
        loc = locale.getdefaultlocale()[0]
        if loc:
            lang = loc.split("_")[0].lower()
            if lang in [lang[0] for lang in get_available_languages()]:
                return lang
    except:
        pass

    return "en"


def _load_core_translations(lang):
    locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
    lang_file = os.path.join(locales_dir, f"{lang}.json")

    if not os.path.exists(lang_file):
        lang_file = os.path.join(locales_dir, "en.json")

    try:
        with open(lang_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"[I18N] Error loading core {lang_file}: {e}")
        return {}


def _load_plugin_translations(lang, dock):
    translations = {}

    plugins_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugins")

    if not os.path.exists(plugins_dir):
        log("Plugins folder not found", "WARNING")
        return translations

    log(f"Searching of the plugin translation: {lang}", "DEBUG")

    for plugin_name in os.listdir(plugins_dir):
        plugin_dir = os.path.join(plugins_dir, plugin_name)
        locales_dir = os.path.join(plugin_dir, "locales")
        lang_file = os.path.join(locales_dir, f"{lang}.json")

        if not os.path.exists(lang_file):
            lang_file = os.path.join(locales_dir, "en.json")
            log(f"There is no {lang}.json for {plugin_name}, use en.json", "DEBUG")

        if os.path.exists(lang_file):
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    plugin_translations = json.load(f)
                    translations.update(plugin_translations)
                    log(f"Plugin translation was loaded: {plugin_name} ({lang})", "INFO")
            except Exception as e:
                log(f"Loading error {lang_file}: {e}", "ERROR")
        else:
            log(f"There arr no translations for plugin: {plugin_name}", "DEBUG")

    return translations

def _(text):
    return _translations.get(text, text)

def get_current_lang():
    return _current_lang

def get_lang_name():
    return _translations.get("_lang_name", "English")

def get_lang_name_eng():
    return _translations.get("_lang_name_eng", "English")

def get_available_languages():
    locales_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "locales")
    languages = []

    if os.path.exists(locales_dir):
        for filename in os.listdir(locales_dir):
            if filename.endswith(".json"):
                lang_code = filename.replace(".json", "")

                try:
                    with open(os.path.join(locales_dir, filename), "r", encoding="utf-8") as f:
                        data = json.load(f)
                        native_name = data.get("_lang_name", lang_code)
                        english_name = data.get("_lang_name_eng", lang_code)
                        languages.append((lang_code, native_name, english_name))
                except:
                    languages.append((lang_code, lang_code, lang_code))

    return sorted(languages, key=lambda x: x[1])

def set_language(lang, dock=None):
    init_i18n(lang, dock)