"""Rebuild the listening examples and their beginner-friendly diagrams."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


from square_wave_lab import VERSIONS, render, save_wav


from tools.illustrations import build_illustrations


def main():
    for version, (filename, _) in VERSIONS.items():
        save_wav(ROOT / filename, render(version))
        print(f"Built {filename}", flush=True)
    build_illustrations(ROOT / "docs")


if __name__ == "__main__":
    main()
