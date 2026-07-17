#!/usr/bin/env bash
# Builds a single, self-contained Linux binary with everything -- code,
# fonts, and background art -- baked in via --add-data.
#
# Tip: for maximum distro compatibility, build inside an old base distro
# (e.g. a Debian 11 or Ubuntu 20.04 container/VM) so the binary's glibc
# requirement stays low and it runs on newer distros too.
set -euo pipefail
cd "$(dirname "$0")/.."

pip install --user pyserial pillow psutil numpy pyinstaller

pyinstaller --onefile \
  --add-data "res:res" \
  --add-data "library:library" \
  --name lambo-dashboard \
  lambo_dashboard.py

echo
echo "Binary built at: dist/lambo-dashboard"
echo "Run packaging/install.sh to install it system-wide."
