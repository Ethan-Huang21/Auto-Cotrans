"""Remembers the last-used Cotrans options between runs."""

import json
import os

from cotrans import DEFAULT_OPTIONS, OPTION_TABLES

SETTINGS_PATH = os.path.join(os.path.expanduser("~"), ".auto-cotrans.json")


def load_settings():
    settings = dict(DEFAULT_OPTIONS, move_originals=True, last_folder="")
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            saved = json.load(f)
    except (OSError, ValueError):
        return settings
    for key, value in saved.items():
        # Ignore options that are no longer valid.
        if key in OPTION_TABLES and value not in OPTION_TABLES[key]:
            continue
        if key in settings:
            settings[key] = value
    return settings


def save_settings(settings):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except OSError:
        pass
