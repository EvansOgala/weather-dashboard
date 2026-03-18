from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

APP_CSS = b"""
* {
  font-family: "Segoe UI Variable", "Segoe UI", "Inter", "Cantarell", sans-serif;
}

window,
.background {
  background-color: @window_bg_color;
}

button {
  border-radius: 999px;
  padding: 8px 14px;
  min-height: 36px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
}

button.suggested-action,
button.destructive-action {
  border-radius: 999px;
}

entry,
spinbutton,
dropdown,
combobox,
scrolledwindow,
textview,
list,
frame > border {
  border-radius: 14px;
}

frame > border {
  border: 1px solid alpha(@accent_bg_color, 0.18);
  background-color: alpha(@accent_bg_color, 0.04);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.12);
}

list row {
  border-radius: 12px;
  margin: 3px 4px;
  padding: 6px 10px;
}

list row:hover {
  background-color: alpha(@accent_bg_color, 0.09);
}

list row:selected {
  background-color: alpha(@accent_bg_color, 0.20);
}

.title-2 {
  letter-spacing: 0.02em;
}

.dim-label {
  opacity: 0.86;
}
"""


def install_material_smooth_css(window: Gtk.Window) -> Gtk.CssProvider:
    provider = Gtk.CssProvider()
    provider.load_from_data(APP_CSS)
    display = window.get_display()
    Gtk.StyleContext.add_provider_for_display(
        display,
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
    return provider
