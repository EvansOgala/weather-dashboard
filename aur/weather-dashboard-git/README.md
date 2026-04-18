# weather-dashboard-git AUR Staging Folder

This folder mirrors the package files intended for the AUR repository.

Files to publish:

- `PKGBUILD`
- `.SRCINFO`

Typical workflow:

```bash
git clone ssh://aur@aur.archlinux.org/weather-dashboard-git.git
cd weather-dashboard-git
cp /path/to/your/source/repo/aur/weather-dashboard-git/PKGBUILD .
cp /path/to/your/source/repo/aur/weather-dashboard-git/.SRCINFO .
git add PKGBUILD .SRCINFO
git commit -m "Initial import"
git push
```
