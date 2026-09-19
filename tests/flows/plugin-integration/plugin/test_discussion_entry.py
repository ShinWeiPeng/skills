"""SPEC-0029 owner and host-adapter contracts; these are not desktop evidence."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "CLAUDE.md").is_file())
sys.path.insert(0, str(ROOT / "skills/engineering/spec-governance/scripts"))
sys.path.insert(0, str(ROOT / "skills/engineering/implement/scripts"))
from discussion_hook import handle_hook
from discussion_state import discussion_request
from spec_contract import (
    assess_turn_context,
    finish_discussion_turn,
    reconcile_working_bundle,
)


class DiscussionEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = {"task_ref": "task-a", "turn_id": "turn-1"}

    def call(self, operation, **values):
        return discussion_request(
            self.root, {**self.base, "operation": operation, **values}
        )

    def enter(self, prompt="提出量測方案", **values):
        return self.call(
            "enter",
            prompt=prompt,
            source_ref="fixture-user-1",
            engineering=True,
            **values,
        )

    def save(self, reply="實際答覆", **values):
        binding = self.call("status")["binding"]
        return self.call(
            "record",
            summary="Saved actual goal and known facts; no adoption.",
            source_ref="fixture-reply-1",
            reply_text=reply,
            binding=binding,
            **values,
        )

    def test_single_file_views_and_noop_reconcile(self):
        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        self.assertEqual(ref["snapshot_path"], ref["journal_path"])
        text = (self.root / ref["snapshot_path"]).read_text(encoding="utf-8")
        for heading in (
            "Current Specification",
            "Decision History",
            "Pending Discussion",
            "Completeness Gaps",
        ):
            self.assertIn("## " + heading, text)
        result = reconcile_working_bundle(
            self.root,
            ref["working_id"],
            text,
            {},
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertEqual(ref["revision"], result["working_spec"]["revision"])
        self.assertFalse(list((self.root / "spec-governance").glob("WORKING*")))

    def test_implemented_history_does_not_block_new_discussion(self):
        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        path = self.root / ref["snapshot_path"]
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "status: working", "status: implemented", 1
            ),
            encoding="utf-8",
        )
        historical = path.read_bytes()
        self.base = {"task_ref": "task-b", "turn_id": "turn-2"}
        self.assertEqual("PASS", self.enter()["verdict"])
        self.assertEqual(historical, path.read_bytes())

    def test_legacy_migration_preserves_events_and_budget(self):
        import spec_contract as contract

        self.enter()
        self.call("stop", reply_text="missing")
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        canonical = self.root / ref["snapshot_path"]
        text = canonical.read_text(encoding="utf-8")
        events, continuity = contract._read_journal(canonical)
        self.assertEqual("continuous", continuity)
        legacy = self.root / "spec-governance" / (ref["working_id"] + ".md")
        journal = legacy.with_suffix(".journal.jsonl")
        legacy.write_text(
            text.split("\n<!-- spec-audit:start -->")[0], encoding="utf-8"
        )
        journal.write_text(
            "\n".join(json.dumps(e, ensure_ascii=False) for e in events) + "\n",
            encoding="utf-8",
        )
        # A duplicate canonical/legacy identity must not silently select either copy.
        self.assertEqual(
            "invalid",
            contract.resolve_working_bundle(self.root, reference=ref["working_id"])[
                "state"
            ],
        )
        result = contract._migrate_flat_bundle(self.root, ref["working_id"])
        self.assertEqual("PASS", result["verdict"], result)
        migrated, _ = contract._read_journal(canonical)
        self.assertEqual(events, migrated[:-1])
        self.assertFalse(legacy.exists())
        self.assertTrue(legacy.with_name(legacy.name + ".migrated").exists())
        self.assertTrue(self.call("status")["repair_used"])

    def test_migration_conflict_keeps_originals(self):
        import spec_contract as contract

        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        canonical = self.root / ref["snapshot_path"]
        text = canonical.read_text(encoding="utf-8")
        events, _ = contract._read_journal(canonical)
        legacy = self.root / "spec-governance" / (ref["working_id"] + ".md")
        journal = legacy.with_suffix(".journal.jsonl")
        legacy.write_text(
            text.split("\n<!-- spec-audit:start -->")[0], encoding="utf-8"
        )
        journal.write_text(
            "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8"
        )
        canonical.write_text(
            text.replace("revision: 1", "revision: 9"), encoding="utf-8"
        )
        before = [path.read_bytes() for path in (canonical, legacy, journal)]
        self.assertEqual(
            "BLOCKED",
            contract._migrate_flat_bundle(self.root, ref["working_id"])["verdict"],
        )
        self.assertEqual(
            before, [path.read_bytes() for path in (canonical, legacy, journal)]
        )

    def test_malformed_acceptance_mapping_does_not_lose_saved_discussion(self):
        import spec_contract as contract

        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        directory = self.root / "validation"
        directory.mkdir()
        (directory / ("acceptance-" + ref["spec_id"] + ".json")).write_text(
            '{"acceptance":{"AC-001":null}}', encoding="utf-8"
        )
        self.save()
        current = contract.resolve_working_bundle(
            self.root, reference=ref["working_id"]
        )["working_spec"]
        self.assertEqual("BLOCKED", current["validation_planning"]["verdict"])
        self.assertEqual("PASS", self.call("stop", reply_text="實際答覆")["verdict"])

    def test_layout_callability_is_separate_from_failed_check(self):
        from unittest.mock import patch

        from project_validation_adapter import assess_project_validation

        (self.root / "architecture").mkdir()
        (self.root / "architecture/manifest.yaml").write_text(
            "schema_version: 2", encoding="utf-8"
        )
        for verdict, code in (("PASS", 0), ("FAIL", 1), ("BLOCKED", 2)):
            with self.subTest(verdict=verdict):
                results = [
                    subprocess.CompletedProcess(
                        [], 0, json.dumps({"verdict": "PASS", "required_gates": []}), ""
                    ),
                    subprocess.CompletedProcess(
                        [],
                        code,
                        json.dumps({"verdict": verdict, "diagnostics": []}),
                        "",
                    ),
                ]
                with patch(
                    "project_validation_adapter.subprocess.run", side_effect=results
                ) as run:
                    result = assess_project_validation(self.root, phase="acceptance")
                self.assertEqual(2, run.call_count)
                self.assertTrue(
                    result["capabilities"]["test-validation-layout"]["callable"]
                )
                self.assertEqual(verdict, result["verdict"])

    def test_validation_faults_remain_distinct(self):
        from unittest.mock import patch

        from project_validation_adapter import assess_project_validation

        cases = [
            (subprocess.CompletedProcess([], 0, "bad", ""), "malformed-output"),
            (
                subprocess.CompletedProcess([], 2, '{"verdict":"PASS"}', ""),
                "exit-code-mismatch",
            ),
            (
                subprocess.CompletedProcess([], 1, "", "ModuleNotFoundError: missing"),
                "dependency-load-failure",
            ),
            (subprocess.TimeoutExpired("fixture", 30), "timeout"),
        ]
        for value, category in cases:
            with self.subTest(category=category):
                kw = (
                    {"side_effect": value}
                    if isinstance(value, Exception)
                    else {"return_value": value}
                )
                with patch("project_validation_adapter.subprocess.run", **kw):
                    result = assess_project_validation(self.root)
                self.assertEqual("BLOCKED", result["verdict"])
                self.assertEqual(category, result["diagnoses"][0]["category"])

    def test_acceptance_delta_survives_reload_until_mapping_rebound(self):
        import spec_contract as contract
        from test_spec_governance import confirmed_spec

        (self.root / "validation").mkdir()
        started = contract.start_working_bundle(
            self.root,
            "payment-retry",
            confirmed_spec(status="working"),
            task_ref="mapping",
        )
        ref = started["working_spec"]
        path = self.root / ref["snapshot_path"]
        mapping = self.root / "validation" / ("acceptance-" + ref["spec_id"] + ".json")
        mapping.write_text('{"acceptance":{"AC-001":{}}}', encoding="utf-8")
        current = path.read_text(encoding="utf-8")
        changed = current.replace(
            "A fourth attempt is never made.",
            "A fourth attempt is denied and recorded.",
        )
        result = contract.reconcile_working_bundle(
            self.root,
            ref["working_id"],
            changed,
            {},
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertEqual("PASS", result["verdict"], result)
        planning = contract.resolve_working_bundle(
            self.root, reference=ref["working_id"]
        )["working_spec"]["validation_planning"]
        self.assertEqual(["AC-001"], planning["changed"])
        self.assertEqual("BLOCKED", planning["verdict"])
        mapping.write_text(
            json.dumps(
                {
                    "acceptance": {
                        "AC-001": {
                            "criterion_sha256": planning["criterion_hashes"]["AC-001"]
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(
            "PASS",
            contract.resolve_working_bundle(self.root, reference=ref["working_id"])[
                "working_spec"
            ]["validation_planning"]["verdict"],
        )

    def test_complete_adopted_contract_confirms_in_same_file_with_sourced_review(self):
        import spec_contract as contract
        from test_spec_governance import confirmed_spec

        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        text = confirmed_spec(status="working")
        result = contract.reconcile_working_bundle(
            self.root,
            ref["working_id"],
            text,
            {},
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertEqual("PASS", result["verdict"], result)
        review = {
            name: {
                "source_ref": "fixture-reviewed-spec",
                "evidence": "Reviewed explicit "
                + name
                + " against the adopted retry contract",
            }
            for name in ("goal", "scope", "behavior", "exceptions", "acceptance")
        }
        saved = self.save(completeness_review=review)
        self.assertEqual("PASS", saved["confirmation"]["verdict"])
        after = saved["confirmation"]["working_spec"]
        self.assertEqual(ref["snapshot_path"], after["snapshot_path"])
        self.assertEqual(ref["spec_id"], after["spec_id"])
        self.assertEqual("confirmed", after["status"])
        self.assertFalse(saved["product_code_allowed"])

    def test_blank_contract_cannot_confirm_even_with_review(self):
        import spec_contract as contract
        from test_spec_governance import confirmed_spec

        text = (
            confirmed_spec()
            .replace("Retries are inconsistent.", "")
            .replace("Use one bounded retry policy.", "")
            .replace("Retry at most three times.", "")
            .replace("A fourth attempt is never made.", "")
        )
        gaps = contract._contract_completeness_gaps(self.root, text)
        self.assertTrue(any("problem" in gap for gap in gaps), gaps)
        self.assertTrue(any("REQ-001" in gap for gap in gaps), gaps)
        self.assertTrue(any("AC-001" in gap for gap in gaps), gaps)

    def test_top_level_nonobject_mapping_remains_planning_block(self):
        import spec_contract as contract

        self.enter()
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        directory = self.root / "validation"
        directory.mkdir()
        for value in ("[]", "null"):
            (directory / ("acceptance-" + ref["spec_id"] + ".json")).write_text(
                value, encoding="utf-8"
            )
            self.save()
            loaded = contract.resolve_working_bundle(
                self.root, reference=ref["working_id"]
            )
            self.assertEqual(
                "BLOCKED", loaded["working_spec"]["validation_planning"]["verdict"]
            )

    def test_entry_precedes_answer_and_has_no_formal_spec(self):
        self.enter()
        context = assess_turn_context(self.root, task_ref="task-a")
        self.assertEqual("ready", context["state"])
        self.assertEqual("SPEC-0001", context["working_spec"]["spec_id"])
        self.assertIn(
            "提出量測方案",
            (self.root / context["working_spec"]["snapshot_path"]).read_text(
                encoding="utf-8"
            ),
        )
        self.assertEqual(
            "working",
            assess_turn_context(self.root, task_ref="task-a")["working_spec"]["status"],
        )
        self.assertEqual("BLOCKED", self.call("status")["verdict"])
        self.save()
        self.assertEqual("PASS", self.call("stop", reply_text="實際答覆")["verdict"])

    def test_same_working_pair_across_mixed_and_short_answers(self):
        first = self.enter()["working_id"]
        for index, prompt in enumerate(["1", "採用 1，另問現況", "只解釋原因"]):
            self.base["turn_id"] = str(index + 2)
            self.assertEqual(first, self.enter(prompt)["working_id"])
        self.assertEqual(1, len(list((self.root / "specs").glob("SPEC*.md"))))

    def test_nonengineering_does_not_create_working_spec(self):
        self.call("enter", prompt="寫一首詩", source_ref="fixture-user")
        self.call(
            "classify", kind="non-engineering", reason="Standalone creative writing"
        )
        self.assertEqual("PASS", self.call("stop", reply_text="詩")["verdict"])
        self.assertEqual([], list((self.root / "spec-governance").glob("WORKING*.md")))

    def test_unknown_is_not_silently_exempt(self):
        self.call(
            "enter",
            prompt="Investigate this unexplained behavior",
            source_ref="fixture-user",
        )
        self.assertEqual("block", self.call("stop")["decision"])

    def test_one_repair_survives_continuation_restart_and_general_recovery(self):
        self.enter()
        repair = self.call("stop", reply_text="missing")
        self.assertEqual("block", repair["decision"])
        self.base["turn_id"] = "continuation-2"
        self.call("enter", prompt=repair["reason"], source_ref="host-continuation")
        self.call("resume")  # fresh process loads the same persisted state
        for _ in range(3):
            result = self.call("stop", reply_text="still missing")
            self.assertTrue(result["continue"])
            self.assertNotIn("decision", result)
        self.save("direct recovery remains available")
        self.assertEqual("PASS", self.call("status")["verdict"])
        self.assertTrue(self.call("status")["repair_used"])

    def test_duplicate_prompt_cannot_reset_consumed_budget(self):
        self.enter()
        self.call("stop")
        self.enter()
        self.assertTrue(self.call("stop")["continue"])

    def test_wrong_task_stale_binding_and_missing_journal_fail(self):
        self.enter()
        binding = self.call("status")["binding"]
        binding["snapshot_hash"] = "wrong"
        with self.assertRaises(ValueError):
            self.call(
                "record",
                summary="x",
                source_ref="source",
                reply_text="reply",
                binding=binding,
            )
        with self.assertRaises(ValueError):
            discussion_request(
                self.root, {**self.base, "task_ref": "other", "operation": "status"}
            )
        self.save()
        path = next((self.root / "specs").glob("SPEC*.md"))
        path.write_text(
            path.read_text(encoding="utf-8").split("\n<!-- spec-audit:start -->")[0],
            encoding="utf-8",
        )
        self.assertFalse(self.call("stop")["verdict"] == "PASS")

    def test_candidate_deferral_does_not_adopt_or_block_completion(self):
        self.enter()
        self.save(
            candidates=[
                {
                    "id": "candidate-1",
                    "status": "deferred",
                    "source_ref": "assistant-1",
                    "user_source_ref": "user-2",
                    "reason": "Optional optimization",
                    "impact": "Additional code scope",
                }
            ]
        )
        self.assertEqual("PASS", self.call("stop", reply_text="實際答覆")["verdict"])
        self.assertEqual(
            "working",
            assess_turn_context(self.root, task_ref="task-a")["working_spec"]["status"],
        )

    def test_host_detects_model_omitted_calls_and_consumes_once(self):
        base = {"cwd": str(self.root), "session_id": "task-a", "turn_id": "turn-1"}
        handle_hook(
            {**base, "hook_event_name": "UserPromptSubmit", "prompt": "debug a crash"}
        )
        first = handle_hook(
            {**base, "hook_event_name": "Stop", "last_assistant_message": "unsaved"}
        )
        self.assertEqual("block", first["decision"])
        final = handle_hook(
            {
                **base,
                "hook_event_name": "Stop",
                "last_assistant_message": "unsaved",
                "stop_hook_active": True,
            }
        )
        self.assertNotIn("continue", final)
        self.assertIn("systemMessage", final)
        denied = handle_hook(
            {
                **base,
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {"command": "patch"},
            }
        )
        self.assertEqual("deny", denied["hookSpecificOutput"]["permissionDecision"])

    def test_reply_wording_is_audit_only(self):
        self.enter()
        self.save("prepared text")
        self.assertEqual(
            "PASS", self.call("stop", reply_text="different actual reply")["verdict"]
        )

    def test_single_continuation_can_save_successfully(self):
        self.enter()
        repair = self.call("stop")
        self.base["turn_id"] = "continuation"
        self.call("enter", prompt=repair["reason"], source_ref="host-continuation")
        self.save("saved")
        self.assertEqual("PASS", self.call("stop", reply_text="saved")["verdict"])
        self.assertTrue(self.call("status")["repair_used"])

    def test_candidate_fields_are_redacted(self):
        self.enter()
        self.save(
            candidates=[
                {
                    "id": "c1",
                    "status": "candidate",
                    "source_ref": "assistant",
                    "reason": "api_key=fixture-secret",
                    "impact": "Optional",
                }
            ]
        )
        for path in (self.root / "spec-governance").glob("*"):
            if path.suffix != ".lock":
                self.assertNotIn("fixture-secret", path.read_text(encoding="utf-8"))

    def test_saved_current_revision_restores_entry_admission(self):
        self.enter()
        context = assess_turn_context(self.root, task_ref="task-a")
        ref = context["working_spec"]
        text = (self.root / ref["snapshot_path"]).read_text(encoding="utf-8")
        reconcile_working_bundle(
            self.root,
            ref["working_id"],
            text.replace("Engineering discussion", "Engineering facts"),
            {"added_ids": [], "changed_ids": [], "removed_ids": []},
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertFalse(self.call("status")["entry_saved"])
        self.save()
        self.assertTrue(self.call("status")["entry_saved"])
        context = assess_turn_context(self.root, task_ref="task-a")
        result = finish_discussion_turn(
            self.root,
            reference=ref["working_id"],
            task_ref="task-a",
            observation={
                "turn_id": "turn-1",
                "reply_text": "實際答覆",
                "working_spec": context["working_spec"],
            },
        )
        self.assertEqual("PASS", result["verdict"])

    def test_host_topic_change_can_be_nonengineering(self):
        self.enter()
        base = {"cwd": str(self.root), "session_id": "task-a", "turn_id": "poetry"}
        handle_hook(
            {**base, "hook_event_name": "UserPromptSubmit", "prompt": "寫一首詩"}
        )
        self.base["turn_id"] = "poetry"
        self.call("classify", kind="non-engineering", reason="Standalone poetry")
        self.assertEqual("PASS", self.call("stop", reply_text="詩")["verdict"])

    def test_manifest_command_runs_from_unrelated_directory(self):
        plugin = self.root / "中文候選"
        for skill in ("spec-governance", "implement", "engineering-risk-routing"):
            shutil.copytree(
                ROOT / "skills/engineering" / skill,
                plugin / "skills" / skill,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        config = json.loads(
            (ROOT / "plugins/governed-engineering-skills/hooks/hooks.json").read_text()
        )
        command = config["hooks"]["UserPromptSubmit"][0]["hooks"][0]["command"]
        self.assertTrue(command.startswith('python3 -c "'))
        python_code = command[len('python3 -c "') : -1]
        payload = {
            "cwd": str(self.root),
            "session_id": "launch-task",
            "turn_id": "launch-turn",
            "hook_event_name": "UserPromptSubmit",
            "prompt": "提出量測方案",
        }
        run = subprocess.run(
            [sys.executable, "-c", python_code],
            input=json.dumps(payload),
            text=True,
            encoding="utf-8",
            capture_output=True,
            cwd=self.root,
            env=os.environ | {"PLUGIN_ROOT": str(plugin), "PYTHONIOENCODING": "utf-8"},
        )
        self.assertEqual(0, run.returncode, run.stderr)
        output = json.loads(run.stdout)
        self.assertIn("hookSpecificOutput", output)
        self.assertNotIn("continue", output)
        if os.name == "nt":
            (plugin / "hooks").mkdir()
            launcher = plugin / "hooks/run-windows.ps1"
            shutil.copyfile(
                ROOT / "plugins/governed-engineering-skills/hooks/run-windows.ps1",
                launcher,
            )
            env = os.environ | {
                "PLUGIN_ROOT": str(plugin),
                "GOVERNED_ENGINEERING_PYTHON": sys.executable,
            }
            payload["turn_id"] = "windows-launch-turn"
            env.pop("PYTHONUTF8", None)
            env.pop("PYTHONIOENCODING", None)
            windows_command = config["hooks"]["UserPromptSubmit"][0]["hooks"][0][
                "commandWindows"
            ]
            run = subprocess.run(
                windows_command,
                input=json.dumps(payload, ensure_ascii=False),
                text=True,
                encoding="utf-8",
                capture_output=True,
                cwd=self.root,
                env=env,
                timeout=15,
            )
            self.assertEqual(0, run.returncode, run.stderr)
            self.assertIn("hookSpecificOutput", json.loads(run.stdout))
            state = discussion_request(
                self.root, {"operation": "resume", "task_ref": "launch-task"}
            )["state"]
            self.assertEqual(
                payload["prompt"], state["turns"]["windows-launch-turn"]["prompt"]
            )

            # Real Windows adapter processes, not proof of Codex host hook firing.
            def adapter(event, **data):
                run = subprocess.run(
                    windows_command,
                    input=json.dumps(
                        {**payload, "hook_event_name": event, **data},
                        ensure_ascii=False,
                    ),
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    cwd=self.root,
                    env=env,
                    timeout=15,
                )
                self.assertEqual(0, run.returncode, run.stderr)
                return json.loads(run.stdout)

            self.assertEqual(
                "block", adapter("Stop", last_assistant_message="missing")["decision"]
            )
            stopped = adapter(
                "Stop", last_assistant_message="still missing", stop_hook_active=True
            )
            self.assertIn("systemMessage", stopped)
            self.assertNotIn("continue", stopped)
            owner = plugin / "skills/spec-governance/scripts/discussion_state.py"
            request_path = (
                self.root / "spec-governance/DISCUSSION-REQUEST-windows-save.json"
            )
            owner_base = {"task_ref": "launch-task", "turn_id": "windows-launch-turn"}

            def owner_call(operation, **values):
                request_path.write_text(
                    json.dumps({**owner_base, "operation": operation, **values}),
                    encoding="utf-8",
                )
                command = f'& "{sys.executable}" -X utf8 "{owner}" --project-root "{self.root}" --request "{request_path}"'
                allowed = adapter(
                    "PreToolUse", tool_name="exec_command", tool_input={"cmd": command}
                )
                self.assertNotEqual(
                    "deny",
                    allowed.get("hookSpecificOutput", {}).get("permissionDecision"),
                )
                run = subprocess.run(
                    [
                        sys.executable,
                        "-X",
                        "utf8",
                        str(owner),
                        "--project-root",
                        str(self.root),
                        "--request",
                        str(request_path),
                    ],
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    cwd=self.root,
                    env=env,
                    timeout=15,
                )
                response = json.loads(run.stdout)
                if operation != "status":
                    self.assertEqual(0, run.returncode, response)
                return response

            owner_call(
                "classify", kind="engineering", reason="Windows fault/recovery fixture"
            )
            binding = owner_call("status")["binding"]
            owner_call(
                "record",
                binding=binding,
                summary="Saved actual Windows test discussion",
                source_ref="fixture-windows-user",
                reply_text="prepared wording",
            )
            self.assertEqual(
                {}, adapter("Stop", last_assistant_message="equivalent revised wording")
            )
            env["GOVERNED_ENGINEERING_PYTHON"] = str(self.root / "missing-python.exe")
            run = subprocess.run(
                windows_command,
                input=json.dumps(payload),
                text=True,
                encoding="utf-8",
                capture_output=True,
                cwd=self.root,
                env=env,
                timeout=15,
            )
            self.assertNotIn("continue", json.loads(run.stdout))
            self.assertIn("systemMessage", json.loads(run.stdout))

    def test_killed_process_releases_lock_without_resetting_repair(self):
        self.enter()
        self.call("stop")
        code = "import sys,os;sys.path.insert(0,sys.argv[1]);import discussion_state as d;from pathlib import Path;d._operate=lambda *a:os._exit(3);d.discussion_request(Path(sys.argv[2]),{'operation':'resume','task_ref':'task-a'})"
        run = subprocess.run(
            [
                sys.executable,
                "-c",
                code,
                str(ROOT / "skills/engineering/spec-governance/scripts"),
                str(self.root),
            ],
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(3, run.returncode, run.stderr)
        self.assertTrue(self.call("status")["repair_used"])
        self.assertTrue(self.call("stop")["continue"])

    def test_steered_input_same_turn_is_saved_without_budget_reset(self):
        self.enter()
        self.call("stop")
        self.enter("增加限制：不能修改硬體")
        files = "".join(
            p.read_text(encoding="utf-8")
            for p in (self.root / "spec-governance").glob("*.json*")
        )
        self.assertIn("增加限制", files)
        self.assertTrue(self.call("status")["repair_used"])

    def test_invalid_save_after_retry_does_not_poison_valid_save(self):
        self.enter()
        self.call("stop")
        self.save("reply A")
        with self.assertRaises(ValueError):
            self.call(
                "record", binding={}, summary="bad", reply_text="bad", source_ref="bad"
            )
        self.assertEqual("PASS", self.call("verify", reply_text="reply B")["verdict"])

    def test_failed_unknown_turn_can_be_classified_after_exhaustion(self):
        self.call("enter", prompt="hello", source_ref="fixture-user")
        self.call("stop")
        self.call("stop")
        self.call("classify", kind="non-engineering", reason="greeting")
        self.assertEqual("PASS", self.call("status")["verdict"])

    def test_previous_turn_cannot_finish_unsaved_current_turn(self):
        self.enter()
        self.save("reply A")
        previous = self.base["turn_id"]
        self.base["turn_id"] = "turn-2"
        self.enter("請繼續說明")
        context = assess_turn_context(self.root, task_ref="task-a")
        result = finish_discussion_turn(
            self.root,
            reference=context["working_spec"]["working_id"],
            task_ref="task-a",
            observation={
                "turn_id": previous,
                "reply_text": "reply A",
                "working_spec": context["working_spec"],
            },
        )
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertTrue(result["can_end_turn"])
        self.assertFalse(result["product_code_allowed"])

    def test_candidate_cannot_store_unbounded_nested_fields(self):
        self.enter()
        with self.assertRaisesRegex(ValueError, "unsupported candidate fields"):
            self.save(
                candidates=[
                    {
                        "id": "C1",
                        "status": "candidate",
                        "source_ref": "fixture",
                        "reason": "reason",
                        "impact": "impact",
                        "metadata": {"password": "fixture-secret"},
                    }
                ]
            )
        files = "".join(
            p.read_text(encoding="utf-8")
            for p in (self.root / "spec-governance").glob("*.json*")
        )
        self.assertNotIn("fixture-secret", files)

    def test_changed_spec_can_be_rechecked_after_exhaustion(self):
        self.enter()
        self.call("stop")
        self.call("stop")
        ref = assess_turn_context(self.root, task_ref="task-a")["working_spec"]
        text = (self.root / ref["snapshot_path"]).read_text(encoding="utf-8")
        result = reconcile_working_bundle(
            self.root,
            ref["working_id"],
            text.replace("Engineering discussion", "Repaired discussion"),
            {},
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        self.assertEqual("PASS", result["verdict"])
        self.assertEqual("block", self.call("stop")["decision"])
        self.assertNotIn("decision", self.call("stop"))
        self.save()
        self.assertEqual("PASS", self.call("status")["verdict"])

    def test_new_turn_id_alone_does_not_repeat_automatic_repair(self):
        self.enter()
        self.call("stop")
        self.base["turn_id"] = "replayed-under-another-id"
        self.enter()
        result = self.call("stop")
        self.assertNotIn("decision", result)
        self.assertTrue(result["continue"])
        self.save()
        self.assertEqual("PASS", self.call("status")["verdict"])

    def test_v1_failed_state_migrates_without_erasing_history(self):
        self.enter()
        self.call("stop")
        self.call("stop")
        path = next((self.root / "spec-governance").glob("DISCUSSION-*.json"))
        state = json.loads(path.read_text(encoding="utf-8"))
        state["schema_version"] = 1
        state["turns"]["turn-1"].pop("repair_keys", None)
        path.write_text(json.dumps(state), encoding="utf-8")
        self.assertNotIn("decision", self.call("stop"))
        self.save()
        current = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(2, current["schema_version"])
        self.assertTrue(current["turns"]["turn-1"]["legacy_repair"]["repair_failed"])
        self.assertEqual("PASS", self.call("status")["verdict"])

    def test_native_windows_owner_command_is_recovery_not_arbitrary_python(self):
        from discussion_hook import _recovery_or_read, SKILLS

        owner = SKILLS / "spec-governance/scripts/discussion_state.py"
        request = "spec-governance/DISCUSSION-REQUEST-save.json"
        command = f'& "{sys.executable}" -X utf8 "{owner}" --project-root "{self.root}" --request {request}'
        payload = {
            "cwd": str(self.root),
            "tool_name": "exec_command",
            "tool_input": {"cmd": command},
        }
        self.assertTrue(_recovery_or_read(payload))
        for bad in (
            command + "; echo unsafe",
            command.replace(
                str(owner),
                str(self.root / "spec-governance/scripts/discussion_state.py"),
            ),
            command.replace(request, "src/request.json"),
        ):
            with self.subTest(command=bad):
                self.assertFalse(
                    _recovery_or_read({**payload, "tool_input": {"cmd": bad}})
                )

    def test_recovery_allowed_even_when_discussion_store_is_corrupt(self):
        from discussion_hook import _failure

        self.enter()
        path = next((self.root / "spec-governance").glob("DISCUSSION-*.json"))
        path.write_text("not-json", encoding="utf-8")
        base = {
            "cwd": str(self.root),
            "session_id": "task-a",
            "turn_id": "turn-1",
            "hook_event_name": "PreToolUse",
        }
        allowed = handle_hook({**base, "tool_name": "Read", "tool_input": {}})
        self.assertNotIn("permissionDecision", allowed["hookSpecificOutput"])
        failed = _failure(
            {
                **base,
                "tool_name": "apply_patch",
                "tool_input": {"input": "product patch"},
            },
            "corrupt",
        )
        self.assertEqual("deny", failed["hookSpecificOutput"]["permissionDecision"])
        self.assertEqual("not-json", path.read_text(encoding="utf-8"))

    def test_request_patch_absolute_path_allowed_but_mixed_product_patch_denied(self):
        from discussion_hook import _recovery_or_read

        request = self.root / "spec-governance/DISCUSSION-REQUEST-save.json"
        patch = f"*** Begin Patch\n*** Add File: {request}\n+{{}}\n*** End Patch"
        payload = {
            "cwd": str(self.root),
            "tool_name": "apply_patch",
            "tool_input": {"input": patch},
        }
        self.assertTrue(_recovery_or_read(payload))
        payload["tool_input"]["input"] = patch.replace(
            "*** End Patch", "*** Add File: src/product.py\n+unsafe\n*** End Patch"
        )
        self.assertFalse(_recovery_or_read(payload))

    def test_malformed_hook_payload_warns_without_terminating_task(self):
        script = ROOT / "skills/engineering/implement/scripts/discussion_hook.py"
        for raw in ("{", "[]", '{"hook_event_name":"Stop"}'):
            run = subprocess.run(
                [sys.executable, str(script)],
                input=raw,
                text=True,
                encoding="utf-8",
                capture_output=True,
            )
            self.assertEqual(0, run.returncode, run.stderr)
            result = json.loads(run.stdout)
            self.assertIn("systemMessage", result)
            self.assertNotIn("continue", result)

    def test_product_authority_is_independent_of_historical_repair_failure(self):
        import hashlib
        import spec_contract as contract
        from managed_delivery import execute_request
        from test_spec_governance import confirmed_spec

        started = contract.start_working_bundle(
            self.root,
            "payment-retry",
            confirmed_spec(status="working"),
            task_ref="task-a",
        )
        ref = started["working_spec"]
        confirmed = contract.materialize_working_bundle(
            self.root,
            ref["working_id"],
            expected_revision=ref["revision"],
            expected_hash=ref["snapshot_hash"],
        )
        ref = confirmed["working_spec"]
        self.enter(working_reference=ref["working_id"])
        self.call("stop")
        self.call("stop")
        self.save()
        base = {
            "task_ref": "task-a",
            "spec": ref["snapshot_path"],
            "working_reference": ref["working_id"],
        }
        target = self.root / "product.txt"
        target.write_text("before", encoding="utf-8")
        patch = {
            **base,
            "operation": "apply",
            "patch": {
                "path": "product.txt",
                "before_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "content": "after",
            },
        }
        self.assertEqual("BLOCKED", execute_request(self.root, patch)["verdict"])
        authorized = execute_request(
            self.root,
            {
                **base,
                "operation": "authorize",
                "instruction": "開始執行",
                "source_event_id": "fixture-explicit-authorization",
                "expected_hash": hashlib.sha256(
                    (self.root / ref["snapshot_path"]).read_bytes()
                ).hexdigest(),
            },
        )
        self.assertEqual("PASS", authorized["verdict"], authorized)
        state_path = next((self.root / "spec-governance").glob("DISCUSSION-*.json"))
        original_state = state_path.read_text(encoding="utf-8")
        incomplete = json.loads(original_state)
        incomplete["turns"]["turn-1"]["saved"] = None
        state_path.write_text(json.dumps(incomplete), encoding="utf-8")
        pending = self.call("status")
        self.assertTrue(pending["entry_saved"])
        self.assertEqual("BLOCKED", pending["verdict"])
        self.assertEqual("BLOCKED", execute_request(self.root, patch)["verdict"])
        self.assertEqual("before", target.read_text(encoding="utf-8"))
        state_path.write_text(original_state, encoding="utf-8")
        self.assertEqual("PASS", execute_request(self.root, patch)["verdict"])
        self.assertEqual("after", target.read_text(encoding="utf-8"))
        # A new saved audit changes the receipt binding; recovery cannot revive it.
        self.save("additional sourced observation")
        patch["patch"]["before_sha256"] = hashlib.sha256(
            target.read_bytes()
        ).hexdigest()
        patch["patch"]["content"] = "must-not-write"
        blocked = execute_request(self.root, patch)
        self.assertEqual("BLOCKED", blocked["verdict"])
        self.assertEqual("after", target.read_text(encoding="utf-8"))

    def test_router_keeps_read_only_support_when_persistence_is_unavailable(self):
        from unittest.mock import patch

        sys.path.insert(
            0, str(ROOT / "skills/engineering/engineering-risk-routing/scripts")
        )
        import guided_workflow_router as router

        (self.root / "app.py").write_text('print("hello")', encoding="utf-8")
        with patch.object(
            router,
            "manage_delivery_discussion",
            side_effect=ValueError("fixture store unavailable"),
        ):
            result = router.route(
                "Explain this code",
                self.root,
                explicit_skill="explain-code-flow",
                task_ref="task-a",
                turn_ref="turn-1",
                source_ref="fixture-input",
                turn_kind="read-only",
            )
        self.assertTrue(result["discussion_recovery"]["discussion_allowed"])
        self.assertEqual(result["supporting_skill"], result["selected_skill"])
        self.assertFalse(result["product_code_allowed"])

    def test_corrupt_state_shapes_do_not_terminate_hook_or_overwrite_store(self):
        self.enter()
        state_path = next((self.root / "spec-governance").glob("DISCUSSION-*.json"))
        script = ROOT / "skills/engineering/implement/scripts/discussion_hook.py"
        payload = {
            "cwd": str(self.root),
            "session_id": "task-a",
            "turn_id": "turn-1",
            "hook_event_name": "Stop",
        }
        for bad in (
            "null",
            "[]",
            '{"schema_version":2,"task_ref":"task-a","turns":{"turn-1":null}}',
        ):
            state_path.write_text(bad, encoding="utf-8")
            run = subprocess.run(
                [sys.executable, str(script)],
                input=json.dumps(payload),
                text=True,
                encoding="utf-8",
                capture_output=True,
            )
            self.assertEqual(0, run.returncode, run.stderr)
            response = json.loads(run.stdout)
            self.assertIn("systemMessage", response)
            self.assertNotIn("continue", response)
            self.assertEqual(bad, state_path.read_text(encoding="utf-8"))

    def test_recovery_does_not_ignore_exec_workdir_override(self):
        from discussion_hook import _recovery_or_read, SKILLS

        owner = SKILLS / "spec-governance/scripts/discussion_state.py"
        command = f'"{sys.executable}" "{owner}" --project-root . --request spec-governance/DISCUSSION-REQUEST-x.json'
        payload = {
            "cwd": str(self.root),
            "tool_name": "exec_command",
            "tool_input": {"cmd": command, "workdir": str(self.root)},
        }
        self.assertTrue(_recovery_or_read(payload))
        payload["tool_input"]["workdir"] = str(self.root / "other")
        self.assertFalse(_recovery_or_read(payload))
        payload["tool_input"] = {"cmd": "Get-Content (New-Item unsafe.txt)"}
        self.assertFalse(_recovery_or_read(payload))

    def test_missing_v2_repair_history_is_not_reset(self):
        self.enter()
        self.call("stop")
        path = next((self.root / "spec-governance").glob("DISCUSSION-*.json"))
        state = json.loads(path.read_text(encoding="utf-8"))
        state["turns"]["turn-1"].pop("repair_keys")
        bad = json.dumps(state)
        path.write_text(bad, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "repair input history"):
            self.call("stop")
        self.assertEqual(bad, path.read_text(encoding="utf-8"))

    def test_pending_sync_hook_denies_product_but_allows_recovery(self):
        from unittest.mock import patch

        pending = {
            "kind": "engineering",
            "entry_saved": True,
            "repair_used": True,
            "verdict": "BLOCKED",
            "sync_status": "pending",
        }
        payload = {
            "cwd": str(self.root),
            "session_id": "task-a",
            "turn_id": "turn-1",
            "hook_event_name": "PreToolUse",
        }
        with patch("discussion_hook.manage_delivery_discussion", return_value=pending):
            denied = handle_hook(
                {
                    **payload,
                    "tool_name": "apply_patch",
                    "tool_input": {
                        "patch": "*** Begin Patch\n*** Add File: src/x.py\n+x\n*** End Patch"
                    },
                }
            )
            self.assertEqual("deny", denied["hookSpecificOutput"]["permissionDecision"])
            allowed = handle_hook({**payload, "tool_name": "Read", "tool_input": {}})
            self.assertNotEqual(
                "deny", allowed.get("hookSpecificOutput", {}).get("permissionDecision")
            )


if __name__ == "__main__":
    unittest.main()
