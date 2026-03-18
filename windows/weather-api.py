import os
import json
import subprocess
from typing import Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

try:
    import requests  # type: ignore
except Exception:  # noqa: BLE001
    requests = None
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"


class WeatherAPIError(Exception):
    pass


def _http_json_request(url: str, params: dict, timeout: int = 10) -> tuple[int, dict]:
    query = urlencode(params)
    full_url = f"{url}?{query}" if query else url
    backend = os.getenv("WEATHER_HTTP_BACKEND", "auto").strip().lower()
    if os.name == "nt" and backend == "powershell":
        status, raw = _http_json_request_powershell(full_url, timeout)
    elif requests is not None:
        try:
            resp = requests.get(
                full_url,
                headers={"User-Agent": "WeatherDashboard/1.0", "Accept": "application/json"},
                timeout=timeout,
            )
            status = resp.status_code
            raw = resp.content or b""
        except requests.RequestException as exc:
            raise WeatherAPIError(f"Network/API error: {exc}") from exc
    else:
        request = Request(
            full_url,
            headers={
                "User-Agent": "WeatherDashboard/1.0",
                "Accept": "application/json",
            },
        )

        status = 0
        raw = b""
        try:
            with urlopen(request, timeout=timeout) as response:
                status = response.getcode() or 200
                raw = response.read()
        except HTTPError as exc:
            status = exc.code
            raw = exc.read()
        except URLError as exc:
            # Windows firewall/AV sometimes blocks Python sockets; fall back to PowerShell.
            if os.name == "nt" and "WinError 10013" in str(exc.reason):
                status, raw = _http_json_request_powershell(full_url, timeout)
            else:
                raise WeatherAPIError(f"Network/API error: {exc.reason}") from exc
        except OSError as exc:
            raise WeatherAPIError(f"Network/API error: {exc}") from exc

    if not raw:
        return status, {}

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WeatherAPIError("API returned invalid JSON response.") from exc

    return status, payload


def _http_json_request_powershell(full_url: str, timeout: int) -> tuple[int, bytes]:
    ps = (
        "try { "
        f"$r=Invoke-WebRequest -UseBasicParsing -Uri '{full_url}' -TimeoutSec {timeout}; "
        "if ($r.StatusCode -ge 400) { throw ('HTTP ' + $r.StatusCode) }; "
        "$r.Content"
        "} catch { "
        "Write-Output $_.Exception.Message; exit 1 }"
    )
    try:
        completed = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps],
            text=True,
            capture_output=True,
            timeout=timeout + 5,
            check=False,
        )
    except Exception as psex:  # noqa: BLE001
        raise WeatherAPIError(f"Network/API error: {psex}") from psex

    if completed.returncode != 0:
        msg = (completed.stdout or "").strip() or (completed.stderr or "").strip()
        raise WeatherAPIError(f"Network/API error: {msg}")

    return 200, (completed.stdout or "").encode("utf-8")


def _weather_code_to_text(code: int | None) -> str:
    mapping = {
        0: "Clear Sky",
        1: "Mainly Clear",
        2: "Partly Cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing Rime Fog",
        51: "Light Drizzle",
        53: "Moderate Drizzle",
        55: "Dense Drizzle",
        56: "Freezing Drizzle",
        57: "Freezing Drizzle",
        61: "Slight Rain",
        63: "Moderate Rain",
        65: "Heavy Rain",
        66: "Freezing Rain",
        67: "Freezing Rain",
        71: "Slight Snow",
        73: "Moderate Snow",
        75: "Heavy Snow",
        77: "Snow Grains",
        80: "Rain Showers",
        81: "Rain Showers",
        82: "Violent Rain Showers",
        85: "Snow Showers",
        86: "Snow Showers",
        95: "Thunderstorm",
        96: "Thunderstorm with Hail",
        99: "Thunderstorm with Hail",
    }
    return mapping.get(code, "Unknown")


class OpenMeteoClient:
    def _geocode(self, city: str) -> Dict:
        status_code, payload = _http_json_request(
            OPEN_METEO_GEOCODE_URL,
            {"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        if status_code >= 400:
            raise WeatherAPIError(f"Open-Meteo geocoding failed (HTTP {status_code}).")

        results = payload.get("results") or []
        if not results:
            raise WeatherAPIError(f"City not found: {city}")

        top = results[0]
        return {
            "name": top.get("name", city),
            "country": top.get("country", ""),
            "latitude": top.get("latitude"),
            "longitude": top.get("longitude"),
        }

    def _forecast(self, latitude: float, longitude: float, units: str) -> Dict:
        temp_unit = "fahrenheit" if units == "imperial" else "celsius"
        wind_unit = "mph" if units == "imperial" else "kmh"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": "auto",
            "temperature_unit": temp_unit,
            "wind_speed_unit": wind_unit,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,weather_code",
            "forecast_days": 5,
        }

        status_code, payload = _http_json_request(OPEN_METEO_FORECAST_URL, params, timeout=10)
        if status_code >= 400:
            raise WeatherAPIError(f"Open-Meteo forecast failed (HTTP {status_code}).")
        return payload

    def current_weather(self, city: str, units: str = "imperial") -> Dict:
        location = self._geocode(city)
        data = self._forecast(location["latitude"], location["longitude"], units)

        current = data.get("current", {})
        daily = data.get("daily", {})
        min_list = daily.get("temperature_2m_min", [])
        max_list = daily.get("temperature_2m_max", [])

        city_label = location["name"]
        if location.get("country"):
            city_label = f"{city_label}, {location['country']}"

        return {
            "city": city_label,
            "temp": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "temp_min": min_list[0] if min_list else None,
            "temp_max": max_list[0] if max_list else None,
            "humidity": current.get("relative_humidity_2m"),
            "wind": current.get("wind_speed_10m"),
            "description": _weather_code_to_text(current.get("weather_code")),
        }

    def five_day_forecast(self, city: str, units: str = "imperial") -> List[Dict]:
        location = self._geocode(city)
        data = self._forecast(location["latitude"], location["longitude"], units)
        daily = data.get("daily", {})

        dates = daily.get("time", [])
        min_list = daily.get("temperature_2m_min", [])
        max_list = daily.get("temperature_2m_max", [])
        code_list = daily.get("weather_code", [])

        out = []
        for i, date_str in enumerate(dates[:5]):
            low = min_list[i] if i < len(min_list) else None
            high = max_list[i] if i < len(max_list) else None
            avg = None
            if low is not None and high is not None:
                avg = (low + high) / 2

            code = code_list[i] if i < len(code_list) else None
            out.append(
                {
                    "date": date_str,
                    "temp": avg,
                    "temp_min": low,
                    "temp_max": high,
                    "description": _weather_code_to_text(code),
                }
            )

        return out


class WeatherClient:
    def __init__(self, provider: str | None = None, api_key: str | None = None):
        self.provider = (provider or os.getenv("WEATHER_PROVIDER") or "open-meteo").lower()
        self.client = OpenMeteoClient()

    def current_weather(self, city: str, units: str = "imperial") -> Dict:
        return self.client.current_weather(city, units)

    def five_day_forecast(self, city: str, units: str = "imperial") -> List[Dict]:
        return self.client.five_day_forecast(city, units)
