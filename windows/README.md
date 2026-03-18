# Weather Dashboard

GTK4 weather desktop app with current conditions, 5-day forecast, and saved cities.

## Features

- Current weather view with temperature, wind, humidity, and condition summary
- 5-day forecast panel
- Saved cities list with quick reload
- Unit switcher (imperial/metric)
- Open-Meteo support out of the box

## Dependencies

### Runtime

- Python 3.11+
- Network access for weather APIs

Optional:

- `WEATHER_PROVIDER` can be set to `open-meteo` (default)

### Linux (GTK4 + PyGObject)

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

### Windows (PySide6 / Qt)

```powershell
py -m pip install --upgrade pip
py -m pip install PySide6
py -m pip install requests
```

## Run from source

### Linux

```bash
cd /home/'your username'/Documents/weather-dashboard
python3 main.py
```

### Windows

```powershell
cd C:\Users\your-username\Documents\weather-dashboard
py main.py
```

Optional provider override:

```bash
export WEATHER_PROVIDER=open-meteo
python3 main.py
```

### Windows network fallback

If Python networking is blocked on Windows, enable PowerShell transport:

```powershell
$env:WEATHER_HTTP_BACKEND="powershell"
py main.py
```

## Build AppImage (Linux)

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

## Build Windows (PyInstaller)

### Build requirements

```powershell
py -m pip install --upgrade pip pyinstaller
py -m pip install PySide6
py -m pip install requests
```

### Build command

```powershell
cd C:\Users\your-username\Documents\weather-dashboard
build-windows.bat
```

The executable is emitted into `dist\WeatherDashboard\`.
