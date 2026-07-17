#!/usr/bin/env bash
# Quick check: is a compatible panel connected to this machine?
set -euo pipefail

echo "Scanning connected serial devices for the panel..."
FOUND=0
for dev in /sys/class/tty/ttyACM*; do
    [ -e "$dev" ] || continue
    name=$(basename "$dev")
    serial_file="$dev/device/../serial"
    if [ -f "$serial_file" ]; then
        serial=$(cat "$serial_file" 2>/dev/null || true)
        echo "  /dev/$name -> serial: ${serial:-<none>}"
        if [[ "$serial" == *"CT50INCH"* ]]; then
            echo "  ^ this looks like a compatible panel!"
            FOUND=1
        fi
    fi
done

if [ "$FOUND" -eq 0 ]; then
    echo
    echo "No device with serial number containing 'CT50INCH' was found."
    echo "This project targets the Turing 5\" panel family used in the"
    echo "Lian Li O11D EVO RGB Lamborghini Edition's rear display."
    echo "If your panel is connected but not detected, run:"
    echo "  sudo dmesg | tail -20"
    echo "after plugging it in and check what Manufacturer/Product/SerialNumber"
    echo "it reports -- open an issue with that info."
fi
