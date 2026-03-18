from __future__ import annotations

import os
import threading

from PySide6 import QtCore, QtGui, QtWidgets

from settings import load_settings, save_settings
from weather_api import WeatherAPIError, WeatherClient


_LIGHT_QSS = """
QWidget {
  font-family: "Segoe UI Variable", "Segoe UI", "Inter", sans-serif;
  font-size: 13px;
  color: #1c2433;
}

QMainWindow {
  background: #eef2f7;
}

QGroupBox {
  background: #ffffff;
  border: 1px solid rgba(27, 39, 64, 0.12);
  border-radius: 12px;
  margin-top: 10px;
  padding: 12px;
}

QGroupBox::title {
  subcontrol-origin: margin;
  left: 10px;
  padding: 0 6px 0 6px;
  color: #1c2433;
  font-weight: 600;
}

QLineEdit, QComboBox {
  border: 1px solid rgba(27, 39, 64, 0.16);
  border-radius: 10px;
  padding: 7px 10px;
  background: #ffffff;
}

QLineEdit:focus, QComboBox:focus {
  border: 1px solid #2b7cff;
}

QPushButton {
  border-radius: 18px;
  padding: 7px 16px;
  background: #2b7cff;
  color: white;
  font-weight: 600;
}

QPushButton:disabled {
  background: rgba(120, 140, 170, 0.5);
}

QListWidget, QTextEdit {
  border: 1px solid rgba(27, 39, 64, 0.12);
  border-radius: 10px;
  background: #ffffff;
  color: #1c2433;
}

QListWidget::item:selected {
  background: rgba(43, 124, 255, 0.15);
  color: #1c2433;
}
"""

_DARK_QSS = """
QWidget {
  font-family: "Segoe UI Variable", "Segoe UI", "Inter", sans-serif;
  font-size: 13px;
  color: #e6e9f2;
}

QMainWindow {
  background: #1b1f2a;
}

QGroupBox {
  background: #232a36;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  margin-top: 10px;
  padding: 12px;
}

QGroupBox::title {
  subcontrol-origin: margin;
  left: 10px;
  padding: 0 6px 0 6px;
  color: #e6e9f2;
  font-weight: 600;
}

QLineEdit, QComboBox {
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 10px;
  padding: 7px 10px;
  background: #1f2430;
  color: #e6e9f2;
}

QLineEdit:focus, QComboBox:focus {
  border: 1px solid #6aa2ff;
}

QPushButton {
  border-radius: 18px;
  padding: 7px 16px;
  background: #3f7bff;
  color: white;
  font-weight: 600;
}

QPushButton:disabled {
  background: rgba(120, 140, 170, 0.45);
}

QListWidget, QTextEdit {
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  background: #1f2430;
  color: #e6e9f2;
}

QListWidget::item:selected {
  background: rgba(63, 123, 255, 0.25);
  color: #e6e9f2;
}
"""


class WeatherWindow(QtWidgets.QMainWindow):
    weather_ready = QtCore.Signal(object, object, object, object)
    weather_error = QtCore.Signal(object, object)
    network_test_done = QtCore.Signal(object, object, object)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Weather Dashboard")
        self.resize(1100, 760)
        icon_path = os.path.join(os.path.dirname(__file__), "org.evans.Weather.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

        self.settings = load_settings()
        self.client = WeatherClient()
        self._request_token = 0
        self._net_test_token = 0
        self._active_weather_token: int | None = None
        self._active_net_test_token: int | None = None

        self.weather_ready.connect(self._on_weather_ready)
        self.weather_error.connect(self._on_weather_error)
        self.network_test_done.connect(self._on_network_test_done)

        self._build_ui()
        self._apply_settings()

    def _build_ui(self):
        root = QtWidgets.QWidget()
        self.setCentralWidget(root)

        outer = QtWidgets.QVBoxLayout(root)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(10)

        self.title_label = QtWidgets.QLabel("Weather Dashboard")
        self.title_label.setStyleSheet("font-size: 26px; font-weight: 700;")
        self.subtitle_label = QtWidgets.QLabel("Current conditions, 5-day outlook, and saved cities")

        outer.addWidget(self.title_label)
        outer.addWidget(self.subtitle_label)

        controls = QtWidgets.QHBoxLayout()
        outer.addLayout(controls)

        self.city_entry = QtWidgets.QLineEdit()
        self.city_entry.setPlaceholderText("Enter city")
        self.city_entry.returnPressed.connect(self.refresh_weather)
        controls.addWidget(self.city_entry, 1)

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_weather)
        controls.addWidget(self.refresh_btn)

        self.net_test_btn = QtWidgets.QPushButton("Network Test")
        self.net_test_btn.clicked.connect(self.run_network_test)
        controls.addWidget(self.net_test_btn)

        self.save_btn = QtWidgets.QPushButton("Save City")
        self.save_btn.clicked.connect(self.save_city)
        controls.addWidget(self.save_btn)

        self.remove_btn = QtWidgets.QPushButton("Remove Saved")
        self.remove_btn.clicked.connect(self.remove_selected_city)
        controls.addWidget(self.remove_btn)

        units_label = QtWidgets.QLabel("Units")
        controls.addWidget(units_label)

        self.units_box = QtWidgets.QComboBox()
        self.units_box.addItems(["imperial", "metric"])
        self.units_box.currentIndexChanged.connect(self._on_units_changed)
        controls.addWidget(self.units_box)

        theme_label = QtWidgets.QLabel("Theme")
        controls.addWidget(theme_label)

        self.theme_box = QtWidgets.QComboBox()
        self.theme_box.addItems(["light", "dark"])
        self.theme_box.currentIndexChanged.connect(self._on_theme_changed)
        controls.addWidget(self.theme_box)

        self.ps_checkbox = QtWidgets.QCheckBox("Use PowerShell HTTP")
        self.ps_checkbox.stateChanged.connect(self._on_http_backend_changed)
        controls.addWidget(self.ps_checkbox)

        body = QtWidgets.QHBoxLayout()
        outer.addLayout(body, 1)

        left = QtWidgets.QVBoxLayout()
        body.addLayout(left, 2)

        self.current_box = QtWidgets.QGroupBox("Current")
        current_layout = QtWidgets.QVBoxLayout(self.current_box)
        self.current_text = QtWidgets.QTextEdit()
        self.current_text.setReadOnly(True)
        current_layout.addWidget(self.current_text)
        left.addWidget(self.current_box)

        self.forecast_box = QtWidgets.QGroupBox("5-Day Forecast")
        forecast_layout = QtWidgets.QVBoxLayout(self.forecast_box)
        self.forecast_list = QtWidgets.QListWidget()
        forecast_layout.addWidget(self.forecast_list)
        left.addWidget(self.forecast_box, 1)

        right = QtWidgets.QVBoxLayout()
        body.addLayout(right, 1)

        self.favorites_box = QtWidgets.QGroupBox("Saved Cities")
        favorites_layout = QtWidgets.QVBoxLayout(self.favorites_box)
        self.favorites_list = QtWidgets.QListWidget()
        self.favorites_list.itemActivated.connect(self._on_favorite_selected)
        favorites_layout.addWidget(self.favorites_list)
        right.addWidget(self.favorites_box, 1)

        self.status_label = QtWidgets.QLabel("Ready")
        outer.addWidget(self.status_label)

    def _apply_settings(self):
        city = self.settings.get("city", "New York")
        self.city_entry.setText(city)

        units = self.settings.get("units", "imperial")
        idx = 0 if units == "imperial" else 1
        self.units_box.setCurrentIndex(idx)

        theme = self.settings.get("theme", "light")
        self.theme_box.setCurrentIndex(0 if theme == "light" else 1)
        self._apply_theme(theme)

        backend = self.settings.get("http_backend", "auto")
        self.ps_checkbox.setChecked(backend == "powershell")
        self._apply_http_backend(backend)

        self._refresh_favorites_ui()
        self.refresh_weather()

    def _set_status(self, text: str):
        self.status_label.setText(text)

    def _set_loading(self, is_loading: bool):
        for btn in (self.refresh_btn, self.save_btn, self.remove_btn):
            btn.setEnabled(not is_loading)
        self.units_box.setEnabled(not is_loading)
        self.theme_box.setEnabled(not is_loading)
        self.net_test_btn.setEnabled(True)

    def _refresh_favorites_ui(self):
        self.favorites_list.clear()
        for city in self.settings.get("favorites", []):
            self.favorites_list.addItem(city)

    def _on_favorite_selected(self, item: QtWidgets.QListWidgetItem):
        city = item.text().strip()
        if city:
            self.city_entry.setText(city)
            self.refresh_weather()

    def _on_units_changed(self):
        self.settings["units"] = self.units_box.currentText()
        save_settings(self.settings)

    def _on_theme_changed(self):
        theme = self.theme_box.currentText()
        self._apply_theme(theme)
        self.settings["theme"] = theme
        save_settings(self.settings)

    def _on_http_backend_changed(self):
        backend = "powershell" if self.ps_checkbox.isChecked() else "auto"
        self._apply_http_backend(backend)
        self.settings["http_backend"] = backend
        save_settings(self.settings)

    def _apply_http_backend(self, backend: str):
        if backend == "powershell":
            os.environ["WEATHER_HTTP_BACKEND"] = "powershell"
        else:
            os.environ.pop("WEATHER_HTTP_BACKEND", None)
        self.client = WeatherClient()

    def _apply_theme(self, theme: str):
        app = QtWidgets.QApplication.instance()
        if app is None:
            return
        if theme == "dark":
            app.setStyle("Fusion")
            app.setStyleSheet(_DARK_QSS)
            self.title_label.setStyleSheet("font-size: 26px; font-weight: 700; color: #e6e9f2;")
            self.subtitle_label.setStyleSheet("color: rgba(230, 233, 242, 0.7);")
            self.status_label.setStyleSheet("color: rgba(230, 233, 242, 0.65);")
        else:
            app.setStyle("Fusion")
            app.setStyleSheet(_LIGHT_QSS)
            self.title_label.setStyleSheet("font-size: 26px; font-weight: 700; color: #1f2a44;")
            self.subtitle_label.setStyleSheet("color: rgba(30, 40, 60, 0.7);")
            self.status_label.setStyleSheet("color: rgba(30, 40, 60, 0.65);")

    def save_city(self):
        city = self.city_entry.text().strip()
        if not city:
            return
        favorites = self.settings.setdefault("favorites", [])
        if city not in favorites:
            favorites.append(city)
        self.settings["city"] = city
        self.settings["units"] = self.units_box.currentText()
        save_settings(self.settings)
        self._refresh_favorites_ui()
        self._set_status(f"Saved city: {city}")

    def remove_selected_city(self):
        item = self.favorites_list.currentItem()
        if item is None:
            self._set_status("Select a city in Saved Cities first")
            return
        city = item.text()
        favorites = self.settings.setdefault("favorites", [])
        if city in favorites:
            favorites.remove(city)
        save_settings(self.settings)
        self._refresh_favorites_ui()
        self._set_status(f"Removed city: {city}")

    def refresh_weather(self):
        city = self.city_entry.text().strip()
        if not city:
            self._set_status("Enter a city first")
            return
        units = self.units_box.currentText()
        backend = "powershell" if self.ps_checkbox.isChecked() else "auto"

        self._set_loading(True)
        backend_label = "PowerShell" if backend == "powershell" else "Python"
        self._set_status(f"Fetching weather for {city} via {backend_label}...")

        self._request_token += 1
        token = self._request_token
        self._active_weather_token = token
        timeout_token = token
        timeout_ms = 25000 if backend == "powershell" else 12000
        QtCore.QTimer.singleShot(timeout_ms, lambda: self._on_weather_timeout(timeout_token))

        def task():
            try:
                current = self.client.current_weather(city, units)
                forecast = self.client.five_day_forecast(city, units)
                self.weather_ready.emit(token, current, forecast, units)
            except WeatherAPIError as exc:
                self.weather_error.emit(token, str(exc))
            except Exception as exc:  # noqa: BLE001
                self.weather_error.emit(token, str(exc))

        threading.Thread(target=task, daemon=True).start()

    def _on_weather_timeout(self, token: int):
        if token != self._active_weather_token:
            return
        self._active_weather_token = None
        self._set_loading(False)
        message = "Weather request timed out. Network or firewall may be blocking Python."
        self._set_status(message)
        self.current_text.setText(f"Weather error:\n{message}")
        self.forecast_list.clear()
        QtWidgets.QMessageBox.warning(self, "Weather Timeout", message)

    def run_network_test(self):
        self._set_loading(True)
        backend = "powershell" if self.ps_checkbox.isChecked() else "auto"
        backend_label = "PowerShell" if backend == "powershell" else "Python"
        self._set_status(f"Running network test via {backend_label}...")

        self._net_test_token += 1
        token = self._net_test_token
        self._active_net_test_token = token
        timeout_ms = 25000 if backend == "powershell" else 12000
        QtCore.QTimer.singleShot(timeout_ms, lambda: self._on_network_test_timeout(token))

        def task():
            try:
                current = self.client.current_weather("Lagos", self.units_box.currentText())
                self.network_test_done.emit(
                    True,
                    f"Open-Meteo reachable. Sample: {current.get('city', 'Lagos')}",
                    token,
                )
            except Exception as exc:  # noqa: BLE001
                self.network_test_done.emit(False, str(exc), token)

        threading.Thread(target=task, daemon=True).start()

    def _on_network_test_done(self, ok: bool, message: str, token: int):
        if token != self._active_net_test_token:
            return
        self._active_net_test_token = None
        self._set_loading(False)
        if ok:
            self._set_status("Network test ok")
            QtWidgets.QMessageBox.information(self, "Network Test", message)
        else:
            self._set_status("Network test failed")
            QtWidgets.QMessageBox.warning(self, "Network Test Failed", message)

    def _on_network_test_timeout(self, token: int):
        if token != self._active_net_test_token:
            return
        self._active_net_test_token = None
        self._set_loading(False)
        message = "Network test timed out. Python may be blocked from outbound connections."
        self._set_status("Network test failed")
        QtWidgets.QMessageBox.warning(self, "Network Test Timeout", message)

    def _on_weather_ready(self, token: int, current: dict, forecast: list[dict], units: str):
        if token != self._active_weather_token:
            return
        self._active_weather_token = None

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

        self.current_text.setText(summary)
        self.forecast_list.clear()
        for day in forecast:
            line = (
                f"{day['date']}  |  {day['description']}  |  "
                f"{fmt(day['temp_min'])}/{fmt(day['temp_max'])} {temp_unit}"
            )
            self.forecast_list.addItem(line)

        self.settings["city"] = current.get("city", city := self.city_entry.text().strip())
        self.settings["units"] = units
        save_settings(self.settings)

        self._set_loading(False)
        self._set_status(f"Updated weather for {current['city']}")

    def _on_weather_error(self, token: int, message: str):
        if token != self._active_weather_token:
            return
        self._active_weather_token = None
        self._set_loading(False)
        self._set_status(f"Weather error: {message}")
        self.current_text.setText(f"Weather error:\n{message}")
        self.forecast_list.clear()
        QtWidgets.QMessageBox.warning(self, "Weather Error", message)


class WeatherQtApp:
    @staticmethod
    def run_app():
        app = QtWidgets.QApplication([])
        app.setStyle("Fusion")
        app.setStyleSheet(_LIGHT_QSS)
        window = WeatherWindow()
        window.show()
        app.exec()
