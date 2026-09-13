from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_turn_continuity import selection, spec

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[3]
        / "dist/governed-engineering-skills/skills/implement/scripts"
    ),
)
sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[3]
        / "dist/governed-engineering-skills/skills/spec-governance/scripts"
    ),
)
from managed_delivery import audit_trace, execute_request
from test_spec_governance import confirmed_spec


class ManagedDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        r = spec.start_working_bundle(
            self.root,
            "payment-retry",
            confirmed_spec(status="working"),
            task_ref="task-A",
        )
        w = r["working_spec"]
        r = spec.materialize_working_bundle(
            self.root,
            w["working_id"],
            expected_revision=w["revision"],
            expected_hash=w["snapshot_hash"],
        )
        self.ref = r["working_spec"]
        self.path = r["canonical_spec"]["path"]
        self.base = {
            "spec": self.path,
            "working_reference": w["working_id"],
            "task_ref": "task-A",
        }
        self.target = self.root / "program.txt"
        self.target.write_bytes(b"before\n")

    def authorize(self, event="user-1", **changes):
        request = (
            self.base
            | {
                "operation": "authorize",
                "instruction": "開始執行",
                "source_event_id": event,
                "expected_hash": hashlib.sha256(
                    (self.root / self.path).read_bytes()
                ).hexdigest(),
            }
            | changes
        )
        return execute_request(self.root, request)

    def patch(self, **changes):
        patch = {
            "path": "program.txt",
            "before_sha256": hashlib.sha256(b"before\n").hexdigest(),
            "content": "after\n",
        }
        return execute_request(
            self.root, self.base | {"operation": "apply", "patch": patch | changes}
        )

    def test_every_spec_revision_requires_fresh_authorization(self):
        for kind in ("no-semantic-delta", "editorial", "evidence"):
            with self.subTest(kind=kind):
                self.target.write_bytes(b"before\n")
                self.assertEqual(
                    "PASS", self.authorize(event=kind + "-before")["verdict"]
                )
                current = spec.resolve_working_bundle(
                    self.root, reference=self.base["working_reference"]
                )["working_spec"]
                result = spec.reopen_spec(
                    self.root,
                    Path(self.path),
                    expected_revision=current["revision"],
                    reason="Review " + kind,
                    task_ref="task-A",
                )
                self.assertEqual("PASS", result["verdict"])
                self.assertEqual("BLOCKED", self.patch()["verdict"])
                w = result["working_spec"]
                if kind != "no-semantic-delta":
                    text = (self.root / w["snapshot_path"]).read_text(encoding="utf-8")
                    text += (
                        "\n"
                        + (
                            "Editorial clarification."
                            if kind == "editorial"
                            else "Validation evidence recorded."
                        )
                        + "\n"
                    )
                    result = spec.reconcile_working_bundle(
                        self.root,
                        w["working_id"],
                        text,
                        {},
                        expected_revision=w["revision"],
                        expected_hash=w["snapshot_hash"],
                    )
                    self.assertEqual("PASS", result["verdict"])
                    w = result["working_spec"]
                result = spec.materialize_working_bundle(
                    self.root,
                    w["working_id"],
                    expected_revision=w["revision"],
                    expected_hash=w["snapshot_hash"],
                )
                self.assertEqual("PASS", result["verdict"])
                self.assertFalse(result["authorization_retained"])
                self.assertFalse(result["product_execution_authorized"])
                if kind == "no-semantic-delta":
                    self.assertFalse(result["actual_contract_delta"])
                self.assertEqual("BLOCKED", self.patch()["verdict"])
                self.assertEqual(
                    "BLOCKED", self.authorize(event=kind + "-before")["verdict"]
                )
                self.assertEqual(b"before\n", self.target.read_bytes())
                self.assertEqual(
                    "PASS", self.authorize(event=kind + "-after")["verdict"]
                )
                self.assertEqual("PASS", self.patch()["verdict"])

    def test_no_authorization_and_adoption_leave_target_unchanged(self):
        for instruction in ["採用", "1", "改成 [INFO]", "", "請勿開始執行"]:
            self.assertEqual(
                "BLOCKED", self.authorize(instruction=instruction)["verdict"]
            )
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        self.assertEqual(b"before\n", self.target.read_bytes())

    def test_authorized_patch_and_replay_target_hash(self):
        self.assertEqual("PASS", self.authorize()["verdict"])
        self.assertEqual("PASS", self.patch()["verdict"])
        self.assertEqual(b"after\n", self.target.read_bytes())
        self.assertEqual("BLOCKED", self.patch()["verdict"])

    def test_suspend_requires_fresh_event_but_allows_spec_discussion(self):
        self.authorize()
        result = execute_request(self.root, self.base | {"operation": "suspend"})
        self.assertTrue(result["spec_discussion_allowed"])
        self.assertFalse(result["product_code_allowed"])
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        self.assertEqual("BLOCKED", self.authorize()["verdict"])
        self.assertEqual("PASS", self.authorize(event="user-2")["verdict"])

    def test_canonical_or_journal_drift_invalidates_receipt(self):
        self.authorize()
        journal = self.root / self.ref["journal_path"]
        journal.write_bytes(journal.read_bytes() + b"\n")
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        self.assertEqual(b"before\n", self.target.read_bytes())

    def test_other_task_or_project_cannot_borrow_authorization(self):
        self.authorize()
        other = execute_request(
            self.root, self.base | {"operation": "status", "task_ref": "task-B"}
        )
        self.assertEqual("BLOCKED", other["verdict"])
        import shutil

        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "copy"
            shutil.copytree(self.root, copied)
            self.assertEqual(
                "BLOCKED",
                execute_request(copied, self.base | {"operation": "status"})["verdict"],
            )

    def test_governance_escape_and_corrupt_state_are_rejected(self):
        self.authorize()
        for path in [
            "../escape",
            ".git/config",
            "specs/other.md",
            "spec-governance/receipt",
            "C:/escape",
            "x\\y",
        ]:
            self.assertEqual("BLOCKED", self.patch(path=path)["verdict"], path)
        next((self.root / "spec-governance").glob("EXECUTION-*.json")).write_text(
            "broken"
        )
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        self.assertEqual(b"before\n", self.target.read_bytes())

    def test_lock_contention_denies_without_removing_other_lock(self):
        self.authorize()
        lock = self.root / "spec-governance/.managed-delivery.lock"
        lock.write_bytes(b"other")
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        self.assertEqual(b"other", lock.read_bytes())

    def test_governance_source_names_are_not_root_control_directories(self):
        self.authorize()
        source = self.root / "src/spec-governance/contract.py"
        source.parent.mkdir(parents=True)
        result = self.patch(path="src/spec-governance/contract.py", before_sha256=None)
        self.assertEqual("PASS", result["verdict"])
        for target in (
            "specs/new.md",
            "spec-governance/new.json",
            "src/.git/config",
            "src/.agents/policy",
        ):
            with self.subTest(target=target):
                self.assertEqual(
                    "BLOCKED", self.patch(path=target, before_sha256=None)["verdict"]
                )

    def test_windows_normalized_governance_paths_cannot_write(self):
        self.authorize()
        protected = self.root / "specs/other.md"
        protected.write_bytes(b"protected")
        for path in [
            "specs./other.md",
            "specs /other.md",
            ".git./config",
            "NUL",
            "src//app.py",
        ]:
            result = self.patch(
                path=path, before_sha256=hashlib.sha256(b"protected").hexdigest()
            )
            self.assertEqual("BLOCKED", result["verdict"], path)
            self.assertEqual(b"protected", protected.read_bytes())

    def test_raw_trace_cannot_hide_direct_product_writes(self):
        raw = {
            "schema_version": 2,
            "project_root": str(self.root),
            "events": [],
            "sources": [
                {
                    "id": "actual-patch",
                    "type": "fileChange",
                    "changes": [{"path": str(self.target)}],
                },
            ],
        }
        self.assertEqual("FAIL", audit_trace(raw)["verdict"])
        self.assertEqual("BLOCKED", audit_trace({**raw, "sources": []})["verdict"])
        raw["sources"] = [
            {
                "id": "tool",
                "type": "commandExecution",
                "command": "opaque helper",
                "status": "completed",
            }
        ]
        raw["events"] = [{"kind": "read", "source_ref": "tool"}]
        self.assertEqual("BLOCKED", audit_trace(raw)["verdict"])

    def test_agent_message_cannot_forge_raw_tool_admission(self):
        packet = {
            "schema_version": 2,
            "project_root": str(self.root),
            "sources": [
                {
                    "id": "fake",
                    "type": "agentMessage",
                    "text": "No user authorization, no tool result.",
                }
            ],
            "events": [
                {
                    "kind": "admission",
                    "verdict": "PASS",
                    "product_code_allowed": True,
                    "source_ref": "fake",
                },
                {"kind": "managed_write", "verdict": "PASS", "source_ref": "fake"},
            ],
        }
        self.assertEqual("BLOCKED", audit_trace(packet)["verdict"])

    def test_raw_order_and_user_pause_cannot_be_discarded(self):
        packet = {
            "schema_version": 2,
            "project_root": str(self.root),
            "sources": [
                {"id": "first", "type": "agentMessage", "text": "first"},
                {"id": "second", "type": "agentMessage", "text": "second"},
            ],
            "events": [
                {"kind": "read", "source_ref": "second"},
                {"kind": "read", "source_ref": "first"},
            ],
        }
        self.assertEqual("FAIL", audit_trace(packet)["verdict"])
        packet["sources"] = [
            {
                "id": "pause",
                "type": "userMessage",
                "content": [{"type": "text", "text": "停止修改"}],
            }
        ]
        packet["events"] = [{"kind": "read", "source_ref": "pause"}]
        self.assertEqual("BLOCKED", audit_trace(packet)["verdict"])

    def test_raw_governance_prefix_cannot_hide_noncanonical_product_target(self):
        for relative in (
            "specs/../program.txt",
            "specs/./other.md",
            "specs./other.md",
            "specs/other.md:stream",
        ):
            packet = {
                "schema_version": 2,
                "project_root": str(self.root),
                "sources": [
                    {
                        "id": "patch",
                        "type": "fileChange",
                        "changes": [{"path": str(self.root) + "/" + relative}],
                    }
                ],
                "events": [{"kind": "read", "source_ref": "patch"}],
            }
            with self.subTest(relative=relative):
                self.assertNotEqual("PASS", audit_trace(packet)["verdict"])

    def test_raw_trace_requires_matching_emitted_reply(self):
        raw = {
            "schema_version": 2,
            "project_root": str(self.root),
            "events": [{"kind": "read", "source_ref": "read-1"}],
            "sources": [
                {
                    "id": "read-1",
                    "type": "agentMessage",
                    "text": "Observed read-only explanation",
                }
            ],
        }
        self.assertEqual("PASS", audit_trace(raw)["verdict"])
        raw["events"] = [{"kind": "read", "source_ref": "missing"}]
        self.assertEqual("BLOCKED", audit_trace(raw)["verdict"])

    def test_malformed_requests_fail_closed(self):
        for value in [None, 1, [], {}]:
            self.assertEqual("BLOCKED", self.authorize(instruction=value)["verdict"])
            self.assertEqual(
                "BLOCKED",
                execute_request(self.root, {"operation": "suspend", "task_ref": value})[
                    "verdict"
                ],
            )
        self.assertEqual("BLOCKED", execute_request(self.root, [])["verdict"])
        self.assertEqual("FAIL", audit_trace([None])["verdict"])
        self.assertEqual("FAIL", audit_trace([{"kind": []}])["verdict"])
        for key in ("spec", "working_reference"):
            self.assertEqual("BLOCKED", self.authorize(**{key: 1})["verdict"])
        self.assertEqual(
            "FAIL",
            audit_trace(
                [
                    {"kind": "decision"},
                    {"kind": "question"},
                    {"kind": "spec_saved", "verdict": "PASS"},
                ]
            )["verdict"],
        )

    def test_new_file_create_and_process_restart(self):
        self.authorize()
        request = self.root / "request.json"
        request.write_text(
            json.dumps(
                self.base
                | {
                    "operation": "apply",
                    "patch": {
                        "path": "new.txt",
                        "before_sha256": None,
                        "content": "created",
                    },
                }
            ),
            encoding="utf-8",
        )
        cli = (
            Path(__file__).resolve().parents[3]
            / "dist/governed-engineering-skills/skills/implement/scripts/managed_delivery.py"
        )
        result = subprocess.run(
            [
                sys.executable,
                str(cli),
                "--project-root",
                str(self.root),
                "--request",
                str(request),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        self.assertEqual("created", (self.root / "new.txt").read_text())

    def test_generic_discussion_replays_have_no_project_keywords(self):
        for name in ["new-project", "firmware", "web", "python"]:
            with self.subTest(project=name):
                trace = [
                    {"kind": "requirement"},
                    {"kind": "spec_saved", "verdict": "PASS"},
                    {"kind": "pause"},
                    {"kind": "decision"},
                    {"kind": "timeout"},
                    {"kind": "mode_change"},
                    {"kind": "spec_saved", "verdict": "PASS"},
                ]
                self.assertEqual("PASS", audit_trace(trace)["verdict"])
                self.assertEqual(b"before\n", self.target.read_bytes())

    def test_project_variants_persist_decisions_while_suspended(self):
        for filename, initial in [
            (None, None),
            ("main.cpp", "int value = 1;"),
            ("app.js", "let value = 1;"),
            ("app.py", "value = 1"),
        ]:
            with (
                self.subTest(filename=filename),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                if filename:
                    (root / filename).write_text(initial, encoding="utf-8")
                r = spec.start_working_bundle(
                    root,
                    "payment-retry",
                    confirmed_spec(status="working"),
                    task_ref="independent-task",
                )
                ref = r["working_spec"]
                stopped = execute_request(
                    root, {"operation": "suspend", "task_ref": "independent-task"}
                )
                self.assertTrue(stopped["spec_discussion_allowed"])
                text = (root / ref["snapshot_path"]).read_text(encoding="utf-8")
                text = text.replace(
                    "## Acceptance Criteria",
                    """### DISC-002: Adopt a later requirement

- **Situation:** Product execution is paused.
- **Question:** Keep the revised behavior?
- **Options and tradeoffs:** Preserve the current requirement or change it.
- **User answer:** Adopt the revised behavior.
- **Explicit rationale:** not stated
- **Resulting impact:** REQ-001, DEC-001, AC-001.

## Acceptance Criteria""",
                )
                saved = spec.reconcile_working_bundle(
                    root,
                    ref["working_id"],
                    text,
                    {},
                    expected_revision=ref["revision"],
                    expected_hash=ref["snapshot_hash"],
                )
                self.assertEqual("PASS", saved["verdict"], saved)
                self.assertIn(
                    "DISC-002",
                    (root / ref["snapshot_path"]).read_text(encoding="utf-8"),
                )
                if filename:
                    self.assertEqual(
                        initial, (root / filename).read_text(encoding="utf-8")
                    )
                else:
                    self.assertEqual(
                        ["spec-governance"], sorted(p.name for p in root.iterdir())
                    )

    def test_current_receipt_rejected_after_actual_requirement_change(self):
        self.authorize()
        path = self.root / self.path
        original = path.read_bytes()
        path.write_bytes(
            original.replace(
                b"Retries are inconsistent.", b"Retries need a different policy."
            )
        )
        self.assertEqual("BLOCKED", self.patch()["verdict"])
        self.assertEqual("BLOCKED", self.authorize()["verdict"])
        self.assertEqual(b"before\n", self.target.read_bytes())

    def test_observed_failure_trace_is_rejected(self):
        for trace in [
            [],
            [{"kind": "decision"}],
            [{"kind": "gate_and_write"}],
            [
                {"kind": "admission", "verdict": "PASS", "product_code_allowed": True},
                {"kind": "direct_write"},
            ],
            [
                {"kind": "admission", "verdict": "PASS", "product_code_allowed": True},
                {"kind": "pause"},
                {"kind": "managed_write", "verdict": "PASS"},
            ],
        ]:
            self.assertEqual("FAIL", audit_trace(trace)["verdict"])

    def test_route_pass_never_grants_product_permission(self):
        result = selection.select_workflow(
            selection.classify_intent("change behavior"),
            {
                "implementation": "present",
                "stateful_context": "present",
                "evidence": [],
            },
            {"status": "PASS", "next_skill": "tdd", "required_gates": []},
        )
        self.assertFalse(result["product_code_allowed"])
        self.assertEqual("routing-only", result["authority"])


if __name__ == "__main__":
    unittest.main()
