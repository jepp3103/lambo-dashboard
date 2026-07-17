#!/usr/bin/env bash
# Installs the lambo-dashboard binary, the udev rule that grants access to
# the panel, and an optional auto-start systemd user service.
#
# Works in two contexts:
#   - run from a cloned repo after packaging/build.sh (finds ../dist/lambo-dashboard)
#   - run from an extracted release tarball (finds ./lambo-dashboard alongside it)
set -euo pipefail
cd "$(dirname "$0")"

if [ -f "./lambo-dashboard" ]; then
    BINARY="./lambo-dashboard"
elif [ -f "../dist/lambo-dashboard" ]; then
    BINARY="../dist/lambo-dashboard"
else
    echo "Could not find the lambo-dashboard binary."
    echo "If building from source, run packaging/build.sh first."
    exit 1
fi

echo "Installing binary to /usr/local/bin (requires sudo)..."
sudo install -Dm755 "$BINARY" /usr/local/bin/lambo-dashboard

echo "Installing udev rule (requires sudo)..."
sudo install -Dm644 ./99-lambo-dashboard.rules /etc/udev/rules.d/99-lambo-dashboard.rules
sudo udevadm control --reload-rules
sudo udevadm trigger

read -p "Set up auto-start on login via systemd user service? [y/N] " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
    mkdir -p ~/.config/systemd/user
    cp ./lambo-dashboard.service ~/.config/systemd/user/
    systemctl --user daemon-reload
    systemctl --user enable --now lambo-dashboard.service
    echo "Service enabled. Check status with: systemctl --user status lambo-dashboard"
fi

echo
echo "Installed. Unplug/replug the panel once so the new udev rule applies,"
echo "then run:"
echo "  lambo-dashboard"
