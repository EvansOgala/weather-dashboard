from __future__ import annotations

import importlib.util
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk

from settings import load_settings, save_settings
from gtk_style import install_material_smooth_css


def _load_weather_module():
    path = Path(__file__).with_name("weather-api.py")
    spec = importlib.util.spec_from_file_location("weather_api_local", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load weather-api.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


weather_api = _load_weather_module()
WeatherClient = weather_api.WeatherClient
WeatherAPIError = weather_api.WeatherAPIError


class WeatherApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.evans.Weather")
        self.window: Gtk.ApplicationWindow | None = None

        self.settings = load_settings()
        self.theme_values = ["dark", "light"]
        self.units_values = ["imperial", "metric"]
        self.css_provider = None

        self.client = None
        self._request_token = 0

        self.city_entry: Gtk.Entry | None = None
        self.units_dropdown: Gtk.DropDown | None = None
        self.theme_dropdown: Gtk.DropDown | None = None

        self.refresh_btn: Gtk.Button | None = None
        self.save_btn: Gtk.Button | None = None
        self.remove_btn: Gtk.Button | None = None

        self.current_label: Gtk.Label | None = None
        self.forecast_list: Gtk.ListBox | None = None
        self.favorites_list: Gtk.ListBox | None = None
        self.status_label: Gtk.Label | None = None

        self._init_client()

    def do_activate(self):
        if self.window is None:
            self._build_ui()
            self._refresh_favorites_ui()
            city = self.settings.get("city", "New York")
            if self.city_entry is not None:
                self.city_entry.set_text(city)
            if self.client is not None:
                self.refresh_weather()
        self.window.present()

    def _init_client(self):
        try:
            self.client = WeatherClient()
        except WeatherAPIError:
            self.client = None

    def _build_ui(self):
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("Weather Dashboard")
        self.window.set_default_size(1100, 760)
        self.css_provider = install_material_smooth_css(self.window)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        root.set_margin_top(12)
        root.set_margin_bottom(12)
        root.set_margin_start(12)
        root.set_margin_end(12)
        self.window.set_child(root)

        title = Gtk.Label(label="Weather Dashboard")
        title.set_xalign(0.0)
        title.add_css_class("title-2")
        root.append(title)

        subtitle = Gtk.Label(label="Current weather, 5-day forecast, and saved favorites")
        subtitle.set_xalign(0.0)
        subtitle.add_css_class("dim-label")
        root.append(subtitle)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        root.append(controls)

        self.city_entry = Gtk.Entry()
        self.city_entry.set_hexpand(True)
        self.city_entry.set_placeholder_text("Enter city")
        self.city_entry.connect("activate", lambda _e: self.refresh_weather())
        controls.append(self.city_entry)

        self.refresh_btn = Gtk.Button(label="Refresh")
        self.refresh_btn.connect("clicked", lambda _b: self.refresh_weather())
        controls.append(self.refresh_btn)

        self.save_btn = Gtk.Button(label="Save City")
        self.save_btn.connect("clicked", lambda _b: self.save_city())
        controls.append(self.save_btn)

        self.remove_btn = Gtk.Button(label="Remove Saved")
        self.remove_btn.connect("clicked", lambda _b: self.remove_selected_city())
        controls.append(self.remove_btn)

        options = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        root.append(options)

        options.append(Gtk.Label(label="Units"))
        self.units_dropdown = Gtk.DropDown.new_from_strings(self.units_values)
        self._set_dropdown_value(self.units_dropdown, self.units_values, self.settings.get("units", "imperial"))
        self.units_dropdown.connect("notify::selected", self._on_units_changed)
        options.append(self.units_dropdown)

        options.append(Gtk.Label(label="Theme"))
        self.theme_dropdown = Gtk.DropDown.new_from_strings(self.theme_values)
        self._set_dropdown_value(self.theme_dropdown, self.theme_values, self.settings.get("theme", "dark"))
        self.theme_dropdown.connect("notify::selected", self._on_theme_changed)
        options.append(self.theme_dropdown)

        body = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        body.set_hexpand(True)
        body.set_vexpand(True)
        root.append(body)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        left.set_margin_end(8)
        body.set_start_child(left)

        current_frame = Gtk.Frame(label="Current")
        left.append(current_frame)

        current_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        current_box.set_margin_top(10)
        current_box.set_margin_bottom(10)
        current_box.set_margin_start(10)
        current_box.set_margin_end(10)
        current_frame.set_child(current_box)

        self.current_label = Gtk.Label(label="No data yet")
        self.current_label.set_xalign(0.0)
        self.current_label.set_yalign(0.0)
        self.current_label.set_selectable(False)
        self.current_label.set_wrap(True)
        current_box.append(self.current_label)

        forecast_frame = Gtk.Frame(label="5-Day Forecast")
        left.append(forecast_frame)

        forecast_scroller = Gtk.ScrolledWindow()
        forecast_scroller.set_hexpand(True)
        forecast_scroller.set_vexpand(True)
        forecast_frame.set_child(forecast_scroller)

        self.forecast_list = Gtk.ListBox()
        self.forecast_list.set_selection_mode(Gtk.SelectionMode.NONE)
        forecast_scroller.set_child(self.forecast_list)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.set_margin_start(8)
        body.set_end_child(right)

        favorites_frame = Gtk.Frame(label="Saved Cities")
        right.append(favorites_frame)

        fav_scroller = Gtk.ScrolledWindow()
        fav_scroller.set_hexpand(True)
        fav_scroller.set_vexpand(True)
        favorites_frame.set_child(fav_scroller)

        self.favorites_list = Gtk.ListBox()
        self.favorites_list.connect("row-activated", self.on_favorite_select)
        fav_scroller.set_child(self.favorites_list)

        self.status_label = Gtk.Label(label="Ready")
        self.status_label.set_xalign(0.0)
        self.status_label.add_css_class("dim-label")
        root.append(self.status_label)

        self._apply_theme(self.settings.get("theme", "dark"))

        if self.client is None:
            self._set_status("Open-Meteo fallback is active; OPENWEATHER_API_KEY is optional.")

    def _set_status(self, text: str):
        if self.status_label is not None:
            self.status_label.set_text(text)

    def _set_loading(self, is_loading: bool):
        for button in (self.refresh_btn, self.save_btn, self.remove_btn):
            if button is not None:
                button.set_sensitive(not is_loading)
        if self.units_dropdown is not None:
            self.units_dropdown.set_sensitive(not is_loading)
        if self.theme_dropdown is not None:
            self.theme_dropdown.set_sensitive(not is_loading)

    def _refresh_favorites_ui(self):
        if self.favorites_list is None:
            return
        self._clear_listbox(self.favorites_list)
        for city in self.settings.get("favorites", []):
            row = Gtk.ListBoxRow()
            row.set_child(Gtk.Label(label=city, xalign=0.0))
            self.favorites_list.append(row)

    def on_favorite_select(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow):
        child = row.get_child()
        if not isinstance(child, Gtk.Label):
            return
        city = child.get_text()
        if self.city_entry is not None:
            self.city_entry.set_text(city)
        self.refresh_weather()

    def _on_units_changed(self, dropdown: Gtk.DropDown, _param):
        value = self._get_dropdown_value(dropdown, self.units_values)
        self.settings["units"] = value
        save_settings(self.settings)

    def _on_theme_changed(self, dropdown: Gtk.DropDown, _param):
        value = self._get_dropdown_value(dropdown, self.theme_values)
        self._apply_theme(value)

    def _apply_theme(self, theme_name: str):
        if theme_name not in {"dark", "light"}:
            theme_name = "dark"

        self.settings["theme"] = theme_name
        save_settings(self.settings)

        gtk_settings = Gtk.Settings.get_default()
        if gtk_settings is not None:
            gtk_settings.set_property("gtk-application-prefer-dark-theme", theme_name == "dark")

    def save_city(self):
        if self.city_entry is None:
            return
        city = self.city_entry.get_text().strip()
        if not city:
            return

        favorites = self.settings.setdefault("favorites", [])
        if city not in favorites:
            favorites.append(city)

        if self.units_dropdown is not None:
            self.settings["units"] = self._get_dropdown_value(self.units_dropdown, self.units_values)
        self.settings["city"] = city
        save_settings(self.settings)

        self._refresh_favorites_ui()
        self._set_status(f"Saved city: {city}")

    def remove_selected_city(self):
        if self.favorites_list is None:
            return
        row = self.favorites_list.get_selected_row()
        if row is None:
            self._set_status("Select a city in Saved Cities first")
            return

        child = row.get_child()
        if not isinstance(child, Gtk.Label):
            return
        city = child.get_text()

        favorites = self.settings.setdefault("favorites", [])
        if city in favorites:
            favorites.remove(city)
            save_settings(self.settings)
            self._refresh_favorites_ui()
            self._set_status(f"Removed city: {city}")

    def refresh_weather(self):
        if self.city_entry is None or self.units_dropdown is None:
            return

        city = self.city_entry.get_text().strip()
        units = self._get_dropdown_value(self.units_dropdown, self.units_values)
        if not city:
            self._set_status("Enter a city first")
            return

        self._set_loading(True)
        self._set_status(f"Fetching weather for {city}...")

        self._request_token += 1
        token = self._request_token

        if self.client is None:
            self._init_client()
            if self.client is None:
                self._set_loading(False)
                self._set_status("No weather provider could be initialized")
                return

        def task():
            try:
                current = self.client.current_weather(city, units)
                forecast = self.client.five_day_forecast(city, units)
                GLib.idle_add(self._on_weather_ready, token, current, forecast, units)
            except WeatherAPIError as exc:
                GLib.idle_add(self._on_weather_error, token, str(exc))

        threading.Thread(target=task, daemon=True).start()

    def _on_weather_ready(self, token: int, current: dict, forecast: list[dict], units: str):
        if token != self._request_token:
            return False

        temp_unit = "F" if units == "imperial" else "C"
        wind_unit = "mph" if units == "imperial" else "km/h"

        def fmt(value):
            return "N/A" if value is None else f"{float(value):.1f}"

        summary = (
            f"City: {current['city']}\n"
            f"Condition: {current['description']}\n"
            f"Temperature: {fmt(current['temp'])} {temp_unit}\n"
            f"Feels Like: {fmt(current['feels_like'])} {temp_unit}\n"
            f"Low / High: {fmt(current['temp_min'])} / {fmt(current['temp_max'])} {temp_unit}\n"
            f"Humidity: {current['humidity']}%\n"
            f"Wind: {fmt(current['wind'])} {wind_unit}"
        )

        if self.current_label is not None:
            self.current_label.set_text(summary)

        if self.forecast_list is not None:
            self._clear_listbox(self.forecast_list)
            for day in forecast:
                row = Gtk.ListBoxRow()
                line = (
                    f"{day['date']}  |  {day['description']}  |  "
                    f"{fmt(day['temp_min'])}/{fmt(day['temp_max'])} {temp_unit}"
                )
                row.set_child(Gtk.Label(label=line, xalign=0.0))
                self.forecast_list.append(row)

        self.settings["city"] = current.get("city", self.city_entry.get_text().strip())
        self.settings["units"] = units
        save_settings(self.settings)

        self._set_loading(False)
        self._set_status(f"Updated weather for {current['city']}")
        return False

    def _on_weather_error(self, token: int, message: str):
        if token != self._request_token:
            return False
        self._set_loading(False)
        self._set_status(f"Weather error: {message}")
        return False

    @staticmethod
    def _set_dropdown_value(dropdown: Gtk.DropDown, values: list[str], value: str):
        try:
            idx = values.index(value)
        except ValueError:
            idx = 0
        dropdown.set_selected(idx)

    @staticmethod
    def _get_dropdown_value(dropdown: Gtk.DropDown, values: list[str]) -> str:
        idx = int(dropdown.get_selected())
        if 0 <= idx < len(values):
            return values[idx]
        return values[0]

    @staticmethod
    def _clear_listbox(box: Gtk.ListBox):
        child = box.get_first_child()
        while child is not None:
            nxt = child.get_next_sibling()
            box.remove(child)
            child = nxt
