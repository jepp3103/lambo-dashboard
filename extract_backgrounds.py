#!/usr/bin/env python3
"""
One-time helper: pulls a clean background frame from each of the 16 original
Lambo dashboard clips and saves them as PNGs for lambo_dashboard.py to use.

Usage:
    python3 extract_backgrounds.py /path/to/mp4/folder
"""
import subprocess
import sys
from pathlib import Path

NAME_MAP = {
    "01": "cpu_c1", "02": "cpu_c2", "03": "cpu_c3", "04": "cpu_c4",
    "05": "cpu_c5", "06": "cpu_c6", "07": "cpu_c7", "08": "cpu_c8",
    "11": "gpu_c1", "12": "gpu_c2", "13": "gpu_c3", "14": "gpu_c4",
    "15": "gpu_c5", "16": "gpu_c6", "17": "gpu_c7", "18": "gpu_c8",
}


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} /path/to/mp4/folder")
        sys.exit(1)

    src_dir = Path(sys.argv[1])
    out_dir = Path(__file__).parent / "res" / "backgrounds"
    out_dir.mkdir(parents=True, exist_ok=True)

    for src, out in NAME_MAP.items():
        src_file = src_dir / f"{src}.mp4"
        if not src_file.exists():
            print(f"skip: {src_file} not found")
            continue
        subprocess.run([
            "ffmpeg", "-y", "-i", str(src_file),
            "-vf", "select=eq(n\\,0)", "-vframes", "1",
            str(out_dir / f"{out}.png"),
        ], check=True)
        print(f"extracted {out}.png")


if __name__ == "__main__":
    main()
