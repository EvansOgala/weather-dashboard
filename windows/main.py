import os

if os.name == "nt":
    from pyside_ui import WeatherQtApp
else:
    from ui import WeatherApp


def main():
    if os.name == "nt":
        WeatherQtApp.run_app()
    else:
        app = WeatherApp()
        app.run(None)


if __name__ == "__main__":
    main()
