"""Compatibility entrypoint for the relocated engineering package."""

import runpy
from pathlib import Path


def main():
    runpy.run_path(
        str(
            Path(__file__).resolve().parents[1]
            / "governed-engineering-skills/scripts/validate_distribution.py"
        ),
        run_name="__main__",
    )


if __name__ == "__main__":
    main()
