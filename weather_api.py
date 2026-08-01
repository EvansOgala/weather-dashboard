"""Importable wrapper for the historical ``weather-api.py`` module name."""

import importlib.util
from pathlib import Path

_path = Path(__file__).with_name("weather-api.py")
_spec = importlib.util.spec_from_file_location("weather_api_local", _path)
if _spec is None or _spec.loader is None:
    raise ImportError("Failed to load weather-api.py")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

WeatherAPIError = _module.WeatherAPIError
WeatherClient = _module.WeatherClient
