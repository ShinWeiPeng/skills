"""Composition entrypoint injecting project validation into existing skill CLIs."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "spec-governance/scripts"))
from project_validation_adapter import assess_project_validation
import managed_delivery
import spec_delivery


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["spec", "managed", "admission"])
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
    previous = sys.argv
    try:
        sys.argv = [previous[0], *arguments]
        selected = {
            "spec": spec_delivery.run_spec_cli,
            "managed": managed_delivery.main,
            "admission": spec_delivery.main,
        }[args.operation]
        return selected(validation_assessor=assess_project_validation)
    finally:
        sys.argv = previous


if __name__ == "__main__":
    raise SystemExit(main())
