# Weather Dashboard

GTK4 weather desktop app with current conditions, 5-day forecast, and saved cities.

## Features

- Current weather view with temperature, wind, humidity, and condition summary
- 5-day forecast panel
- Saved cities list with quick reload
- Unit switcher (imperial/metric)
- Open-Meteo support out of the box
- Optional OpenWeather support through API key

## Dependencies

### Runtime

- Python 3.11+
- GTK4 + PyGObject
- Network access for weather APIs

Optional:

- `OPENWEATHER_API_KEY` environment variable for OpenWeather provider

### Install dependencies by distro

#### Arch Linux / Nyarch

```bash
sudo pacman -S --needed python python-gobject gtk4
```

#### Debian / Ubuntu

```bash
sudo apt update
sudo apt install -y python3 python3-gi gir1.2-gtk-4.0
```

#### Fedora

```bash
sudo dnf install -y python3 python3-gobject gtk4
```

## Run from source

```bash
cd /home/'your username'/Documents/weather-dashboard
python3 main.py
```

Optional provider overrides:

```bash
export WEATHER_PROVIDER=open-meteo
# or: export WEATHER_PROVIDER=openweather
export OPENWEATHER_API_KEY='your_api_key_if_needed'
python3 main.py
```

## Build AppImage

### Build requirements

```bash
python3 -m pip install --user pyinstaller
```

Install `appimagetool` in `PATH`, or place one of these files in `./tools/`:

- `appimagetool.AppImage`
- `appimagetool-x86_64.AppImage`

### Build command

```bash
cd /home/'your username'/Documents/weather-dashboard
chmod +x build-appimage.sh
./build-appimage.sh
```

The script outputs an `.AppImage` file in the project root.
