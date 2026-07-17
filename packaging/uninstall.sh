#!/usr/bin/env bash
# Reverses everything install.sh does: stops/disables the service, removes
# the binary, udev rule, and systemd unit. Does not touch your dashboard
# assets if you customized them elsewhere.
set -euo pipefail

echo "Stopping and disabling the service (if running)..."
systemctl --user disable --now lambo-dashboard.service 2>/dev/null || true

echo "Removing systemd user service file..."
rm -f ~/.config/systemd/user/lambo-dashboard.service
systemctl --user daemon-reload

echo "Removing binary (requires sudo)..."
sudo rm -f /usr/local/bin/lambo-dashboard

echo "Removing udev rule (requires sudo)..."
sudo rm -f /etc/udev/rules.d/99-lambo-dashboard.rules
sudo udevadm control --reload-rules
sudo udevadm trigger

echo
echo "Done. lambo-dashboard has been fully removed."
