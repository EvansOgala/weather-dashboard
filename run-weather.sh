#!/usr/bin/env sh
set -eu

APP_DIR="/app/share/org.evans.Weather"
cd "$APP_DIR"

exec python3 main.py
