import json
import os
from pathlib import Path

APP_ID = "org.evans.Weather"
LOCAL_SETTINGS_PATH = Path(__file__).with_name("settings.json")


def _get_settings_path() -> Path:
    xdg_config_home = os.getenv("XDG_CONFIG_HOME")
    if xdg_config_home:
        base = Path(xdg_config_home)
    else:
        base = Path.home() / ".config"

    return base / APP_ID / "settings.json"


SETTINGS_PATH = _get_settings_path()

DEFAULT_SETTINGS = {
    "city": "New York",
    "units": "imperial",  # imperial (F/mph) or metric (C/m/s)
    "theme": "dark",
    "favorites": ["New York", "Los Angeles", "Chicago"],
}


def load_settings() -> dict:
    source_path = SETTINGS_PATH if SETTINGS_PATH.exists() else LOCAL_SETTINGS_PATH
    if not source_path.exists():
        return DEFAULT_SETTINGS.copy()

    try:
        with source_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return DEFAULT_SETTINGS.copy()

    merged = DEFAULT_SETTINGS.copy()
    merged.update(data)
    return merged


def save_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
