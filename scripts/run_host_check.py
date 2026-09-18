"""Run one host check and retain immutable evidence under artifacts/tests/."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import yaml

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[1]
        / "skills/engineering/verification-ladder/scripts"
    ),
)
from run_storage import allocate_run, finalize_run, source_snapshot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--module")
    parser.add_argument("--flow")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--spec")
    parser.add_argument("--run-id")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.project_root.resolve()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if bool(args.module) == bool(args.flow) or not command:
        parser.error("one --module/--flow and a command after -- are required")
    manifest = yaml.safe_load(
        (root / "architecture/manifest.yaml").read_text(encoding="utf-8")
    )
    kind, owner = ("module", args.module) if args.module else ("flow", args.flow)
    if owner not in {item["id"] for item in manifest[kind + "s"]}:
        parser.error("unknown target owner")
    metadata = {
        "target": {kind: owner},
        "scenario": args.scenario,
        "tool": {"name": "run_host_check", "version": "1"},
        "command": command,
        "source": source_snapshot(root),
        "inputs": {},
    }
    if args.spec:
        metadata["spec"] = args.spec
    run = allocate_run(root, "tests", args.run_id, metadata)
    report = run / "reports"
    report.mkdir()
    try:
        with (report / "command.log").open("xb") as stream:
            completed = subprocess.run(
                command, cwd=root, stdout=stream, stderr=subprocess.STDOUT, check=False
            )
        code = completed.returncode
        outcome = "PASS" if code == 0 else "FAIL"
    except OSError as exc:
        code, outcome = 2, "BLOCKED"
        (report / "launch-error.txt").write_text(str(exc), encoding="utf-8")
    (report / "result.json").write_text(
        json.dumps({"returncode": code, "outcome": outcome}), encoding="utf-8"
    )
    finalize_run(root, run, outcome)
    print(
        json.dumps(
            {
                "verdict": outcome,
                "manifest": (run / "manifest.json").relative_to(root).as_posix(),
            }
        )
    )
    return code if code >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
