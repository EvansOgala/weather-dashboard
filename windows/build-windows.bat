@echo off
setlocal

py -m pip install --upgrade pip pyinstaller
py -m pip install PySide6
py -m pip install requests
py -m pip install Pillow

if not exist "app_icon.ico" (
  if exist "org.evans.Weather.png" (
    py -c "from PIL import Image; im=Image.open('org.evans.Weather.png'); im.save('app_icon.ico', sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])"
  )
)

py -m PyInstaller --noconfirm --clean WeatherDashboard.spec

echo.
echo Build complete. Output: dist\WeatherDashboard\
endlocal
