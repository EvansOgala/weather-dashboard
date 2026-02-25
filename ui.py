import importlib.util
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from settings import load_settings, save_settings


def _load_weather_module():
    path = Path(__file__).with_name("weather-api.py")
    spec = importlib.util.spec_from_file_location("weather_api_local", path)
    module = importlib.util.module_from_spec(spec)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load weather-api.py")
    spec.loader.exec_module(module)
    return module


weather_api = _load_weather_module()
WeatherClient = weather_api.WeatherClient
WeatherAPIError = weather_api.WeatherAPIError

UI_FONT = "Adwaita Sans"
MONO_FONT = "Adwaita Mono"


THEMES = {
    "dark": {
        "root_bg": "#0f172a",
        "panel_bg": "#111827",
        "panel_border": "#1f2937",
        "card_bg": "#0b1220",
        "title_fg": "#e2e8f0",
        "text_fg": "#cbd5e1",
        "muted_fg": "#94a3b8",
        "status_fg": "#bfdbfe",
        "input_bg": "#0b1220",
        "input_fg": "#dbeafe",
        "input_border": "#334155",
        "button_bg": "#2563eb",
        "button_hover": "#3b82f6",
        "button_press": "#1d4ed8",
        "button_fg": "#eff6ff",
        "button_disabled": "#475569",
        "select_bg": "#2563eb",
        "header_bg": "#1e293b",
        "header_fg": "#e2e8f0",
    },
    "light": {
        "root_bg": "#f1f5f9",
        "panel_bg": "#ffffff",
        "panel_border": "#dbe3ee",
        "card_bg": "#f8fafc",
        "title_fg": "#0f172a",
        "text_fg": "#1e293b",
        "muted_fg": "#475569",
        "status_fg": "#1d4ed8",
        "input_bg": "#ffffff",
        "input_fg": "#0f172a",
        "input_border": "#cbd5e1",
        "button_bg": "#2563eb",
        "button_hover": "#3b82f6",
        "button_press": "#1d4ed8",
        "button_fg": "#eff6ff",
        "button_disabled": "#94a3b8",
        "select_bg": "#93c5fd",
        "header_bg": "#dbeafe",
        "header_fg": "#0f172a",
    },
}


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, width=108, height=34, radius=14, font=(UI_FONT, 10, "bold")):
        super().__init__(
            parent,
            width=width,
            height=height,
            bd=0,
            highlightthickness=0,
            relief="flat",
            cursor="hand2",
        )
        self.command = command
        self.text = text
        self.width = width
        self.height = height
        self.radius = radius
        self.font = font
        self.enabled = True
        self.pressed = False
        self.colors = {
            "bg": "#2563eb",
            "hover": "#3b82f6",
            "press": "#1d4ed8",
            "fg": "#eff6ff",
            "disabled": "#64748b",
            "container": "#0f172a",
        }

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self._draw()

    def configure_theme(self, palette, container_bg):
        self.colors.update(
            {
                "bg": palette["button_bg"],
                "hover": palette["button_hover"],
                "press": palette["button_press"],
                "fg": palette["button_fg"],
                "disabled": palette["button_disabled"],
                "container": container_bg,
            }
        )
        self._draw()

    def set_text(self, text):
        self.text = text
        self._draw()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.config(cursor="hand2" if enabled else "arrow")
        self._draw()

    def _rounded_shape(self, color):
        w = self.width
        h = self.height
        r = self.radius
        self.create_arc(0, 0, 2 * r, 2 * r, start=90, extent=90, fill=color, outline=color)
        self.create_arc(w - 2 * r, 0, w, 2 * r, start=0, extent=90, fill=color, outline=color)
        self.create_arc(0, h - 2 * r, 2 * r, h, start=180, extent=90, fill=color, outline=color)
        self.create_arc(w - 2 * r, h - 2 * r, w, h, start=270, extent=90, fill=color, outline=color)
        self.create_rectangle(r, 0, w - r, h, fill=color, outline=color)
        self.create_rectangle(0, r, w, h - r, fill=color, outline=color)

    def _draw(self):
        self.delete("all")
        self.configure(bg=self.colors["container"])
        if not self.enabled:
            color = self.colors["disabled"]
        elif self.pressed:
            color = self.colors["press"]
        else:
            color = self.colors["bg"]
        self._rounded_shape(color)
        self.create_text(
            self.width // 2,
            self.height // 2,
            text=self.text,
            fill=self.colors["fg"],
            font=self.font,
        )

    def _on_enter(self, _event):
        if self.enabled and not self.pressed:
            self.delete("all")
            self.configure(bg=self.colors["container"])
            self._rounded_shape(self.colors["hover"])
            self.create_text(self.width // 2, self.height // 2, text=self.text, fill=self.colors["fg"], font=self.font)

    def _on_leave(self, _event):
        self.pressed = False
        self._draw()

    def _on_press(self, _event):
        if not self.enabled:
            return
        self.pressed = True
        self._draw()

    def _on_release(self, _event):
        if not self.enabled:
            return
        should_call = self.pressed
        self.pressed = False
        self._draw()
        if should_call:
            self.command()


class RoundedPanel(tk.Canvas):
    def __init__(self, parent, radius=16, inset=1):
        super().__init__(parent, bd=0, highlightthickness=0, relief="flat")
        self.radius = radius
        self.inset = inset
        self.fill = "#111827"
        self.border = "#1f2937"
        self.configure(bg="#0f172a")
        self.content = tk.Frame(self, bd=0, highlightthickness=0)
        self._window_id = self.create_window((inset, inset), window=self.content, anchor="nw")
        self.bind("<Configure>", self._redraw)

    def configure_theme(self, fill, border, outer_bg):
        self.fill = fill
        self.border = border
        self.configure(bg=outer_bg)
        self.content.configure(bg=fill)
        self._redraw()

    def _rounded_shape(self, x1, y1, x2, y2, r, fill, outline):
        tags = ("panel",)
        self.create_arc(
            x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, fill=fill, outline=outline, tags=tags
        )
        self.create_arc(
            x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, fill=fill, outline=outline, tags=tags
        )
        self.create_arc(
            x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, fill=fill, outline=outline, tags=tags
        )
        self.create_arc(
            x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, fill=fill, outline=outline, tags=tags
        )
        self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=fill, outline=outline, tags=tags)
        self.create_rectangle(x1, y1 + r, x2, y2 - r, fill=fill, outline=outline, tags=tags)

    def _redraw(self, _event=None):
        self.delete("panel")
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 8 or h < 8:
            return

        inset = self.inset
        x1, y1 = inset, inset
        x2, y2 = max(inset + 2, w - inset), max(inset + 2, h - inset)
        r = min(self.radius, max(4, (min(w, h) - 2 * inset) // 2))
        self._rounded_shape(x1, y1, x2, y2, r, self.fill, self.border)
        self.itemconfig(self._window_id, width=max(1, w - 2 * inset), height=max(1, h - 2 * inset))
        self.tag_lower("panel")


class WeatherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Weather Dashboard")
        self.root.geometry("820x590")
        self.root.minsize(740, 540)
        self.root.resizable(True, True)
        self.root.bind("<F11>", self.toggle_maximize)
        self.root.bind("<Escape>", self.restore_window)

        self.settings = load_settings()
        self.client = None
        self._request_token = 0
        self._loading_anim_id = None
        self._loading_step = 0
        self._loading_city = ""
        self._init_api_client()

        self.city_var = tk.StringVar(value=self.settings["city"])
        self.units_var = tk.StringVar(value=self.settings["units"])
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "dark"))
        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()
        self.apply_theme(self.theme_var.get())
        self.refresh_weather()

    def _init_api_client(self):
        try:
            self.client = WeatherClient()
        except WeatherAPIError as exc:
            messagebox.showerror("API Key Required", str(exc))

    def _build_ui(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        self.header = tk.Frame(self.root, padx=18, pady=16)
        self.header.pack(fill="x")
        self.title_label = tk.Label(
            self.header,
            text="Weather Dashboard",
            font=(UI_FONT, 21, "bold"),
        )
        self.title_label.pack(anchor="w")
        self.subtitle_label = tk.Label(
            self.header,
            text="Current conditions and a 5-day forecast",
            font=(UI_FONT, 10),
        )
        self.subtitle_label.pack(anchor="w", pady=(2, 0))

        self.top = tk.Frame(self.root, padx=18, pady=4)
        self.top.pack(fill="x")
        self.top.columnconfigure(1, weight=1)

        self.city_label = tk.Label(self.top, text="City")
        self.city_label.configure(font=(UI_FONT, 10, "bold"))
        self.city_label.grid(row=0, column=0, sticky="w")
        self.city_entry = ttk.Entry(self.top, textvariable=self.city_var, width=30, style="App.TEntry")
        self.city_entry.grid(row=0, column=1, padx=8, sticky="ew")
        self.city_entry.bind("<Return>", lambda _event: self.refresh_weather())

        self.units_label = tk.Label(self.top, text="Units")
        self.units_label.configure(font=(UI_FONT, 10, "bold"))
        self.units_label.grid(row=0, column=2, padx=(10, 4))
        self.unit_combo = ttk.Combobox(
            self.top,
            textvariable=self.units_var,
            values=("imperial", "metric"),
            width=10,
            state="readonly",
            style="App.TCombobox",
        )
        self.unit_combo.grid(row=0, column=3)

        self.theme_label = tk.Label(self.top, text="Theme")
        self.theme_label.configure(font=(UI_FONT, 10, "bold"))
        self.theme_label.grid(row=0, column=4, padx=(12, 4))
        self.theme_combo = ttk.Combobox(
            self.top,
            textvariable=self.theme_var,
            values=("dark", "light"),
            width=9,
            state="readonly",
            style="App.TCombobox",
        )
        self.theme_combo.grid(row=0, column=5)
        self.theme_combo.bind("<<ComboboxSelected>>", self.on_theme_change)

        self.button_row = tk.Frame(self.root, padx=18, pady=4)
        self.button_row.pack(fill="x", pady=(2, 2))

        self.refresh_btn = RoundedButton(self.button_row, "Refresh", self.refresh_weather, width=110)
        self.refresh_btn.pack(side="left")
        self.save_btn = RoundedButton(self.button_row, "Save City", self.save_city, width=110)
        self.save_btn.pack(side="left", padx=8)
        self.remove_btn = RoundedButton(self.button_row, "Remove City", self.remove_selected_city, width=122)
        self.remove_btn.pack(side="left")
        self.maximize_btn = RoundedButton(self.button_row, "Maximize", self.toggle_maximize, width=120)
        self.maximize_btn.pack(side="right")

        self.body = tk.Frame(self.root, padx=18, pady=8)
        self.body.pack(fill="both", expand=True)
        self.body.columnconfigure(0, weight=3)
        self.body.columnconfigure(1, weight=2)
        self.body.rowconfigure(0, weight=2)
        self.body.rowconfigure(1, weight=3)

        self.current_panel = RoundedPanel(self.body, radius=18, inset=1)
        self.current_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        self.current_title = tk.Label(
            self.current_panel.content,
            text="Current Weather",
            font=(UI_FONT, 13, "bold"),
            padx=12,
            pady=10,
        )
        self.current_title.pack(anchor="w")
        self.current_text = tk.Label(
            self.current_panel.content,
            text="Loading...",
            justify="left",
            anchor="w",
            padx=12,
            pady=8,
            font=(MONO_FONT, 11),
        )
        self.current_text.pack(fill="both", expand=True)

        self.favorites_panel = RoundedPanel(self.body, radius=18, inset=1)
        self.favorites_panel.grid(row=0, column=1, sticky="nsew", pady=(0, 10))
        self.favorites_title = tk.Label(
            self.favorites_panel.content,
            text="Favorites",
            font=(UI_FONT, 13, "bold"),
            padx=10,
            pady=10,
        )
        self.favorites_title.pack(anchor="w")
        self.favorites_content = tk.Frame(self.favorites_panel.content)
        self.favorites_content.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.favorites_list = tk.Listbox(
            self.favorites_content,
            height=8,
            highlightthickness=0,
            activestyle="none",
            borderwidth=0,
        )
        self.favorites_scroll = ttk.Scrollbar(
            self.favorites_content, orient="vertical", command=self.favorites_list.yview
        )
        self.favorites_list.config(yscrollcommand=self.favorites_scroll.set)
        self.favorites_list.pack(side="left", fill="both", expand=True)
        self.favorites_scroll.pack(side="right", fill="y")
        self.favorites_list.bind("<<ListboxSelect>>", self.on_favorite_select)

        self.forecast_panel = RoundedPanel(self.body, radius=18, inset=1)
        self.forecast_panel.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.forecast_title = tk.Label(
            self.forecast_panel.content,
            text="5-Day Forecast",
            font=(UI_FONT, 13, "bold"),
            padx=12,
            pady=10,
        )
        self.forecast_title.pack(anchor="w")

        self.tree_container = tk.Frame(self.forecast_panel.content)
        self.tree_container.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.forecast_tree = ttk.Treeview(
            self.tree_container,
            columns=("date", "condition", "temp", "range"),
            show="headings",
            height=7,
            style="App.Treeview",
        )
        self.forecast_tree.heading("date", text="Date")
        self.forecast_tree.heading("condition", text="Condition")
        self.forecast_tree.heading("temp", text="Midday Temp")
        self.forecast_tree.heading("range", text="Low / High")
        self.forecast_tree.column("date", width=120, minwidth=110, anchor="w", stretch=False)
        self.forecast_tree.column("condition", width=320, minwidth=180, anchor="w", stretch=True)
        self.forecast_tree.column("temp", width=120, minwidth=110, anchor="center", stretch=False)
        self.forecast_tree.column("range", width=140, minwidth=120, anchor="center", stretch=False)
        self.forecast_scroll = ttk.Scrollbar(self.tree_container, orient="vertical", command=self.forecast_tree.yview)
        self.forecast_tree.config(yscrollcommand=self.forecast_scroll.set)
        self.forecast_tree.pack(side="left", fill="both", expand=True)
        self.forecast_scroll.pack(side="right", fill="y")

        self.status = tk.Label(
            self.root,
            textvariable=self.status_var,
            anchor="w",
            padx=18,
            pady=10,
            font=(UI_FONT, 10, "bold"),
        )
        self.status.pack(fill="x")

        self._refresh_favorites_ui()
        self._update_maximize_label()

    def _apply_styles(self, palette):
        self.style.configure(
            "App.TEntry",
            fieldbackground=palette["input_bg"],
            foreground=palette["input_fg"],
            bordercolor=palette["input_border"],
            insertcolor=palette["input_fg"],
            lightcolor=palette["input_border"],
            darkcolor=palette["input_border"],
            padding=6,
            font=(UI_FONT, 10),
        )
        self.style.configure(
            "App.TCombobox",
            fieldbackground=palette["input_bg"],
            foreground=palette["input_fg"],
            bordercolor=palette["input_border"],
            arrowsize=14,
            padding=4,
            font=(UI_FONT, 10),
        )
        self.style.map(
            "App.TCombobox",
            fieldbackground=[("readonly", palette["input_bg"])],
            foreground=[("readonly", palette["input_fg"])],
        )
        self.style.configure(
            "Vertical.TScrollbar",
            background=palette["panel_border"],
            troughcolor=palette["card_bg"],
            bordercolor=palette["panel_border"],
            arrowcolor=palette["text_fg"],
        )
        self.style.configure(
            "App.Treeview",
            background=palette["card_bg"],
            fieldbackground=palette["card_bg"],
            foreground=palette["text_fg"],
            rowheight=30,
            borderwidth=0,
            font=(UI_FONT, 10),
        )
        self.style.map(
            "App.Treeview",
            background=[("selected", palette["select_bg"])],
            foreground=[("selected", palette["title_fg"])],
        )
        self.style.configure(
            "App.Treeview.Heading",
            background=palette["header_bg"],
            foreground=palette["header_fg"],
            relief="flat",
            font=(UI_FONT, 10, "bold"),
        )
        self.style.map("App.Treeview.Heading", background=[("active", palette["panel_border"])])

    def apply_theme(self, theme_name):
        theme_name = theme_name if theme_name in THEMES else "dark"
        self.theme_var.set(theme_name)
        self.settings["theme"] = theme_name
        save_settings(self.settings)

        palette = THEMES[theme_name]
        self.root.configure(bg=palette["root_bg"])
        self._apply_styles(palette)

        self.header.configure(bg=palette["root_bg"])
        self.title_label.configure(bg=palette["root_bg"], fg=palette["title_fg"])
        self.subtitle_label.configure(bg=palette["root_bg"], fg=palette["muted_fg"])

        self.top.configure(bg=palette["root_bg"])
        self.city_label.configure(bg=palette["root_bg"], fg=palette["title_fg"])
        self.units_label.configure(bg=palette["root_bg"], fg=palette["title_fg"])
        self.theme_label.configure(bg=palette["root_bg"], fg=palette["title_fg"])

        self.button_row.configure(bg=palette["root_bg"])
        for btn in (self.refresh_btn, self.save_btn, self.remove_btn, self.maximize_btn):
            btn.configure_theme(palette, palette["root_bg"])

        self.body.configure(bg=palette["root_bg"])

        for panel in (self.current_panel, self.favorites_panel, self.forecast_panel):
            panel.configure_theme(palette["panel_bg"], palette["panel_border"], palette["root_bg"])

        self.current_title.configure(bg=palette["panel_bg"], fg=palette["title_fg"])
        self.current_text.configure(bg=palette["panel_bg"], fg=palette["text_fg"])

        self.favorites_title.configure(bg=palette["panel_bg"], fg=palette["title_fg"])
        self.favorites_content.configure(bg=palette["panel_bg"])
        self.favorites_list.configure(
            bg=palette["card_bg"],
            fg=palette["text_fg"],
            selectbackground=palette["select_bg"],
            selectforeground=palette["title_fg"],
        )

        self.forecast_title.configure(bg=palette["panel_bg"], fg=palette["title_fg"])
        self.tree_container.configure(bg=palette["panel_bg"])

        self.status.configure(bg=palette["root_bg"], fg=palette["status_fg"])

    def on_theme_change(self, _event=None):
        self.apply_theme(self.theme_var.get())

    def _set_loading(self, is_loading):
        self.refresh_btn.set_enabled(not is_loading)
        self.save_btn.set_enabled(not is_loading)
        self.remove_btn.set_enabled(not is_loading)
        self.unit_combo.configure(state="disabled" if is_loading else "readonly")
        self.theme_combo.configure(state="disabled" if is_loading else "readonly")

    def _start_loading_animation(self, city):
        self._loading_city = city
        self._loading_step = 0
        if self._loading_anim_id:
            self.root.after_cancel(self._loading_anim_id)
            self._loading_anim_id = None
        self._tick_loading()

    def _tick_loading(self):
        dots = "." * ((self._loading_step % 3) + 1)
        self.status_var.set(f"Fetching weather for {self._loading_city}{dots}")
        self._loading_step += 1
        self._loading_anim_id = self.root.after(350, self._tick_loading)

    def _stop_loading_animation(self, final_status):
        if self._loading_anim_id:
            self.root.after_cancel(self._loading_anim_id)
            self._loading_anim_id = None
        self.status_var.set(final_status)

    def _is_zoomed(self):
        try:
            return self.root.state() == "zoomed"
        except tk.TclError:
            return False

    def _update_maximize_label(self):
        self.maximize_btn.set_text("Restore" if self._is_zoomed() else "Maximize")

    def toggle_maximize(self, _event=None):
        try:
            if self._is_zoomed():
                self.root.state("normal")
            else:
                self.root.state("zoomed")
        except tk.TclError:
            try:
                self.root.attributes("-zoomed", not bool(self.root.attributes("-zoomed")))
            except tk.TclError:
                pass
        self._update_maximize_label()

    def restore_window(self, _event=None):
        try:
            self.root.state("normal")
        except tk.TclError:
            try:
                self.root.attributes("-zoomed", False)
            except tk.TclError:
                pass
        self._update_maximize_label()

    def _refresh_favorites_ui(self):
        self.favorites_list.delete(0, tk.END)
        for city in self.settings.get("favorites", []):
            self.favorites_list.insert(tk.END, city)

    def on_favorite_select(self, _event):
        selected = self.favorites_list.curselection()
        if not selected:
            return
        city = self.favorites_list.get(selected[0])
        self.city_var.set(city)
        self.refresh_weather()

    def save_city(self):
        city = self.city_var.get().strip()
        if not city:
            return
        favorites = self.settings.setdefault("favorites", [])
        if city not in favorites:
            favorites.append(city)
            self._refresh_favorites_ui()
        self.settings["city"] = city
        self.settings["units"] = self.units_var.get()
        save_settings(self.settings)
        self.status_var.set(f"Saved settings for {city}")

    def remove_selected_city(self):
        selected = self.favorites_list.curselection()
        if not selected:
            return
        city = self.favorites_list.get(selected[0])
        favorites = self.settings.setdefault("favorites", [])
        if city in favorites:
            favorites.remove(city)
            save_settings(self.settings)
            self._refresh_favorites_ui()
            self.status_var.set(f"Removed {city} from favorites")

    def refresh_weather(self):
        if self.client is None:
            self.status_var.set("Set OPENWEATHER_API_KEY and restart the app.")
            return

        city = self.city_var.get().strip()
        units = self.units_var.get().strip()
        if not city:
            messagebox.showwarning("Missing City", "Please enter a city name.")
            return

        self._request_token += 1
        token = self._request_token
        self._set_loading(True)
        self._start_loading_animation(city)

        def task():
            try:
                current = self.client.current_weather(city, units)
                forecast = self.client.five_day_forecast(city, units)
                self.root.after(0, lambda: self._update_weather_ui(current, forecast, units, token))
            except WeatherAPIError as exc:
                error_message = str(exc)
                self.root.after(0, lambda msg=error_message: self._show_error(msg, token))

        threading.Thread(target=task, daemon=True).start()

    def _update_weather_ui(self, current, forecast, units, token):
        if token != self._request_token:
            return

        temp_unit = "F" if units == "imperial" else "C"
        wind_unit = "mph" if units == "imperial" else "m/s"

        def fmt(value):
            return "N/A" if value is None else f"{value:.1f}"

        self.current_text.config(
            text=(
                f"City         : {current['city']}\n"
                f"Condition    : {current['description']}\n"
                f"Temperature  : {fmt(current['temp'])} {temp_unit}\n"
                f"Feels Like   : {fmt(current['feels_like'])} {temp_unit}\n"
                f"Low / High   : {fmt(current['temp_min'])} / {fmt(current['temp_max'])} {temp_unit}\n"
                f"Humidity     : {current['humidity']}%\n"
                f"Wind Speed   : {fmt(current['wind'])} {wind_unit}"
            )
        )

        for item_id in self.forecast_tree.get_children():
            self.forecast_tree.delete(item_id)

        if not forecast:
            self.forecast_tree.insert("", "end", values=("N/A", "No forecast data", "-", "-"))
        else:
            for day in forecast:
                temp_value = f"{fmt(day['temp'])} {temp_unit}"
                range_value = f"{fmt(day['temp_min'])} / {fmt(day['temp_max'])} {temp_unit}"
                self.forecast_tree.insert("", "end", values=(day["date"], day["description"], temp_value, range_value))

        self.settings["city"] = self.city_var.get().strip()
        self.settings["units"] = units
        save_settings(self.settings)
        self._stop_loading_animation(f"Updated weather for {current['city']}")
        self._set_loading(False)

    def _show_error(self, message, token):
        if token != self._request_token:
            return
        self._stop_loading_animation("Failed to fetch weather")
        self._set_loading(False)
        messagebox.showerror("Weather Error", message)
