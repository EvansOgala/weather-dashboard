pkgname=weather-dashboard-git
pkgver=0.r15.g3c91ea6
pkgrel=1
pkgdesc="GTK4 weather desktop app with current conditions, forecast, and saved cities"
arch=('any')
url="https://github.com/EvansOgala/weather-dashboard"
license=('MIT')
options=('!strip' '!debug')
depends=(
  'python'
  'python-gobject'
  'gtk4'
)
makedepends=('git')
source=("$pkgname::git+https://github.com/EvansOgala/weather-dashboard.git")
sha256sums=('SKIP')

pkgver() {
  cd "$srcdir/$pkgname"
  printf "0.r%s.g%s" \
    "$(git rev-list --count HEAD)" \
    "$(git rev-parse --short HEAD)"
}

build() {
  cd "$srcdir/$pkgname"
  python3 -m PyInstaller --clean --noconfirm --log-level=ERROR WeatherDashboard.spec
}

package() {
  cd "$srcdir/$pkgname"

  install -d "$pkgdir/usr/lib/WeatherDashboard"
  cp -a dist/WeatherDashboard/. "$pkgdir/usr/lib/WeatherDashboard/"

  install -Dm755 /dev/stdin "$pkgdir/usr/bin/weather-dashboard" <<'LAUNCHER'
#!/bin/sh
exec /usr/lib/WeatherDashboard/WeatherDashboard "$@"
LAUNCHER

  install -Dm644 org.evans.Weather.desktop \
    "$pkgdir/usr/share/applications/org.evans.Weather.desktop"
  install -Dm644 org.evans.Weather.metainfo.xml \
    "$pkgdir/usr/share/metainfo/org.evans.Weather.metainfo.xml"
  install -Dm644 org.evans.Weather.svg \
    "$pkgdir/usr/share/icons/hicolor/scalable/apps/org.evans.Weather.png"
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
