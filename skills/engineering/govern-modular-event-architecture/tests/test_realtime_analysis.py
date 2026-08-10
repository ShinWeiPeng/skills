from __future__ import annotations

import sys
import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from realtime_analysis import analyze_realtime_profile


TEST_WORKLOADS = {
    "test-workload": {
        "flow": "test-flow",
        "timing_class": "hard-real-time",
    }
}


def analyze(
    candidate: dict,
    units: dict,
    mappings: dict,
    channels: dict,
    flow_chains: list[dict] | None = None,
    *,
    workloads: dict | None = None,
    analysis_method: str = "rate-monotonic-rta",
) -> dict:
    effective_workloads = workloads or {
        key: dict(value) for key, value in TEST_WORKLOADS.items()
    }
    chain_flows = {
        str(chain.get("flow"))
        for chain in flow_chains or []
        if isinstance(chain, dict) and chain.get("flow")
    }
    if workloads is None and len(chain_flows) == 1:
        effective_workloads["test-workload"]["flow"] = next(iter(chain_flows))
    return analyze_realtime_profile(
        candidate,
        units,
        mappings,
        channels,
        effective_workloads,
        flow_chains,
        analysis_method=analysis_method,
    )


def profile(profile_id: str = "candidate-a", *, cores: int = 1) -> dict:
    return {
        "id": profile_id,
        "status": "proposed",
        "execution_model": "bare-metal",
        "analysis_phase": "provisional",
        "scheduler": {
            "model": "partitioned-fixed-priority",
            "priority_assignment": "rate-monotonic",
            "preemption": "fully-preemptive",
            "migration": "forbidden",
            "core_count": cores,
            "priority_higher_value_wins": True,
            "timer_resolution_ns": 1_000,
            "resource_access_protocol": "priority-ceiling",
        },
        "overheads": {
            "context_switch_ns": 10_000,
            "dispatch_ns": 5_000,
            "preemption_ns": 10_000,
            "timer_interrupt_ns": 5_000,
        },
    }


def task(
    task_id: str,
    profile_id: str,
    mapping_id: str,
    *,
    period_ns: int,
    deadline_ns: int,
    budget_ns: int,
    priority: int,
    core: int = 0,
    kind: str = "periodic",
) -> tuple[dict, dict]:
    activation: dict = {"kind": kind}
    if kind == "periodic":
        activation["period_ns"] = period_ns
    elif kind == "sporadic":
        activation["minimum_interarrival_ns"] = period_ns
    else:
        activation.update(
            {
                "server_type": "sporadic",
                "budget_ns": budget_ns,
                "replenishment_period_ns": period_ns,
            }
        )
    unit = {
        "id": task_id,
        "profile": profile_id,
        "kind": "dedicated-task",
        "priority": priority,
            "realtime_task": {
            "core": core,
            "activation": activation,
            "relative_deadline_ns": deadline_ns,
            "release_jitter_ns": 0,
            "blocking_ns": 0,
            "demand_components": [
                {"mapping": mapping_id, "budget_ns": budget_ns}
            ],
        },
    }
    mapping = {
        "id": mapping_id,
        "profile": profile_id,
        "workload": "test-workload",
        "units": [task_id],
    }
    return unit, mapping


class RealtimeAnalysisTests(unittest.TestCase):
    def test_periodic_sporadic_and_server_tasks_pass_rm_rta(self) -> None:
        candidate = profile()
        fast, fast_map = task(
            "fast", candidate["id"], "fast-map",
            period_ns=10_000_000, deadline_ns=10_000_000,
            budget_ns=1_000_000, priority=3,
        )
        event, event_map = task(
            "event", candidate["id"], "event-map",
            period_ns=20_000_000, deadline_ns=20_000_000,
            budget_ns=1_000_000, priority=2, kind="sporadic",
        )
        server, server_map = task(
            "server", candidate["id"], "server-map",
            period_ns=50_000_000, deadline_ns=50_000_000,
            budget_ns=2_000_000, priority=1, kind="server",
        )
        result = analyze(
            candidate,
            {item["id"]: item for item in (fast, event, server)},
            {item["id"]: item for item in (fast_map, event_map, server_map)},
            {},
        )
        self.assertEqual("PASS", result["verdict"], result)
        self.assertEqual(["fast", "event", "server"], result["cores"]["0"]["rm_order"])

    def test_invalid_periodic_sporadic_and_server_activations_are_blocked(self) -> None:
        cases = (
            ("periodic", {"kind": "periodic", "period_ns": 0}),
            ("sporadic", {"kind": "sporadic"}),
            (
                "server",
                {
                    "kind": "server",
                    "server_type": "sporadic",
                    "budget_ns": 0,
                    "replenishment_period_ns": 10_000_000,
                },
            ),
        )
        for kind, activation in cases:
            with self.subTest(kind=kind):
                candidate = profile()
                unit, mapping = task(
                    "worker",
                    candidate["id"],
                    "worker-map",
                    period_ns=10_000_000,
                    deadline_ns=10_000_000,
                    budget_ns=1_000_000,
                    priority=1,
                )
                unit["realtime_task"]["activation"] = activation
                result = analyze(
                    candidate,
                    {"worker": unit},
                    {"worker-map": mapping},
                    {},
                )
                self.assertEqual("BLOCKED", result["verdict"], result)

    def test_equal_rate_tie_breaks_by_deadline_then_id(self) -> None:
        candidate = profile()
        alpha, alpha_map = task(
            "alpha", candidate["id"], "alpha-map",
            period_ns=10_000_000, deadline_ns=9_000_000,
            budget_ns=500_000, priority=2,
        )
        beta, beta_map = task(
            "beta", candidate["id"], "beta-map",
            period_ns=10_000_000, deadline_ns=10_000_000,
            budget_ns=500_000, priority=1,
        )
        result = analyze(
            candidate,
            {"alpha": alpha, "beta": beta},
            {"alpha-map": alpha_map, "beta-map": beta_map},
            {},
        )
        self.assertEqual("PASS", result["verdict"], result)
        self.assertEqual(["alpha", "beta"], result["cores"]["0"]["rm_order"])

    def test_partitioned_cores_and_cross_core_cost_are_accounted(self) -> None:
        candidate = profile(cores=2)
        producer, producer_map = task(
            "producer", candidate["id"], "producer-map",
            period_ns=10_000_000, deadline_ns=10_000_000,
            budget_ns=1_000_000, priority=1, core=0,
        )
        consumer, consumer_map = task(
            "consumer", candidate["id"], "consumer-map",
            period_ns=10_000_000, deadline_ns=10_000_000,
            budget_ns=1_000_000, priority=1, core=1,
        )
        channel = {
            "id": "handoff",
            "profile": candidate["id"],
            "from_unit": "producer",
            "to_unit": "consumer",
            "realtime_timing": {
                "cross_core": True,
                "notification_latency_ns": 100_000,
                "release_jitter_ns": 50_000,
                "copy_cost_ns": 40_000,
                "cpu_cost_accounting": [
                    {"unit": "producer", "cost_ns": 20_000},
                    {"unit": "consumer", "cost_ns": 20_000},
                ],
            },
        }
        chain = {
            "id": "pipeline",
            "profile": candidate["id"],
            "flow": "control-flow",
            "ordered_units": ["producer", "consumer"],
            "ordered_channels": ["handoff"],
            "deadline_ns": 5_000_000,
        }
        result = analyze(
            candidate,
            {"producer": producer, "consumer": consumer},
            {"producer-map": producer_map, "consumer-map": consumer_map},
            {"handoff": channel},
            [chain],
        )
        self.assertEqual("PASS", result["verdict"], result)
        self.assertEqual(1_040_000, result["tasks"]["producer"]["execution_ns"])
        self.assertEqual("PASS", result["flows"]["pipeline"]["rta_verdict"])

    def test_invalid_cross_core_claim_is_blocked(self) -> None:
        candidate = profile()
        first, first_map = task(
            "first", candidate["id"], "first-map",
            period_ns=10_000_000, deadline_ns=10_000_000,
            budget_ns=500_000, priority=2,
        )
        second, second_map = task(
            "second", candidate["id"], "second-map",
            period_ns=20_000_000, deadline_ns=20_000_000,
            budget_ns=500_000, priority=1,
        )
        channel = {
            "id": "invalid-channel",
            "profile": candidate["id"],
            "from_unit": "first",
            "to_unit": "second",
            "realtime_timing": {
                "cross_core": True,
                "notification_latency_ns": 0,
                "release_jitter_ns": 0,
                "copy_cost_ns": 0,
                "cpu_cost_accounting": [],
            },
        }
        result = analyze(
            candidate,
            {"first": first, "second": second},
            {"first-map": first_map, "second-map": second_map},
            {"invalid-channel": channel},
        )
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertTrue(any("cross_core" in item for item in result["problems"]))

    def test_deadline_miss_and_flow_miss_fail(self) -> None:
        candidate = profile()
        overloaded, overloaded_map = task(
            "overloaded", candidate["id"], "overloaded-map",
            period_ns=10_000_000, deadline_ns=1_000_000,
            budget_ns=2_000_000, priority=1,
        )
        result = analyze(
            candidate,
            {"overloaded": overloaded},
            {"overloaded-map": overloaded_map},
            {},
        )
        self.assertEqual("FAIL", result["verdict"])
        self.assertEqual("FAIL", result["tasks"]["overloaded"]["rta_verdict"])

        feasible, feasible_map = task(
            "feasible", candidate["id"], "feasible-map",
            period_ns=10_000_000, deadline_ns=10_000_000,
            budget_ns=1_000_000, priority=1,
        )
        chain = {
            "id": "too-short-flow",
            "profile": candidate["id"],
            "flow": "control-flow",
            "ordered_units": ["feasible"],
            "ordered_channels": [],
            "deadline_ns": 500_000,
        }
        result = analyze(
            candidate,
            {"feasible": feasible},
            {"feasible-map": feasible_map},
            {},
            [chain],
        )
        self.assertEqual("FAIL", result["verdict"])
        self.assertEqual("PASS", result["tasks"]["feasible"]["rta_verdict"])
        self.assertEqual("FAIL", result["flows"]["too-short-flow"]["rta_verdict"])

    def test_soft_deadline_miss_is_risk_not_gate_failure(self) -> None:
        candidate = profile()
        overloaded, overloaded_map = task(
            "soft-worker",
            candidate["id"],
            "soft-map",
            period_ns=10_000_000,
            deadline_ns=500_000,
            budget_ns=1_000_000,
            priority=1,
        )
        overloaded_map["workload"] = "soft-workload"
        workloads = {
            "soft-workload": {
                "flow": "soft-flow",
                "timing_class": "soft-real-time",
            }
        }
        result = analyze(
            candidate,
            {"soft-worker": overloaded},
            {"soft-map": overloaded_map},
            {},
            workloads=workloads,
        )
        self.assertEqual("PASS", result["verdict"], result)
        self.assertEqual(
            "SOFT_RISK", result["tasks"]["soft-worker"]["rta_verdict"]
        )
        self.assertTrue(result["soft_risks"])
        self.assertFalse(result["failures"])

    def test_best_effort_deadline_miss_is_informational(self) -> None:
        candidate = profile()
        worker, worker_map = task(
            "background",
            candidate["id"],
            "background-map",
            period_ns=10_000_000,
            deadline_ns=500_000,
            budget_ns=1_000_000,
            priority=1,
        )
        worker_map["workload"] = "background-workload"
        result = analyze(
            candidate,
            {"background": worker},
            {"background-map": worker_map},
            {},
            workloads={
                "background-workload": {
                    "flow": "background-flow",
                    "timing_class": "best-effort",
                }
            },
        )
        self.assertEqual("PASS", result["verdict"], result)
        self.assertEqual("INFO", result["tasks"]["background"]["rta_verdict"])

    def test_best_effort_task_still_interferes_with_realtime_task(self) -> None:
        candidate = profile()
        controlled, controlled_map = task(
            "controlled",
            candidate["id"],
            "controlled-map",
            period_ns=10_000_000,
            deadline_ns=10_000_000,
            budget_ns=1_000_000,
            priority=1,
        )
        background, background_map = task(
            "background",
            candidate["id"],
            "background-map",
            period_ns=5_000_000,
            deadline_ns=5_000_000,
            budget_ns=500_000,
            priority=2,
        )
        background_map["workload"] = "background-workload"
        workloads = {
            "feature-workload": {
                "flow": "feature-flow",
                "timing_class": "hard-real-time",
            },
            "background-workload": {
                "flow": "background-flow",
                "timing_class": "best-effort",
            },
        }
        without_background = analyze(
            candidate,
            {"controlled": controlled},
            {"controlled-map": controlled_map},
            {},
            workloads=workloads,
        )
        with_background = analyze(
            candidate,
            {"controlled": controlled, "background": background},
            {
                "controlled-map": controlled_map,
                "background-map": background_map,
            },
            {},
            workloads=workloads,
        )
        self.assertGreater(
            with_background["tasks"]["controlled"]["response_ns"],
            without_background["tasks"]["controlled"]["response_ns"],
        )

    def test_mixed_task_uses_strictest_workload_criticality(self) -> None:
        candidate = profile()
        worker, hard_map = task(
            "mixed",
            candidate["id"],
            "hard-map",
            period_ns=10_000_000,
            deadline_ns=500_000,
            budget_ns=600_000,
            priority=1,
        )
        hard_map["workload"] = "hard-workload"
        soft_map = {
            "id": "soft-map",
            "profile": candidate["id"],
            "workload": "soft-workload",
            "units": ["mixed"],
        }
        worker["realtime_task"]["demand_components"].append(
            {"mapping": "soft-map", "budget_ns": 400_000}
        )
        result = analyze(
            candidate,
            {"mixed": worker},
            {"hard-map": hard_map, "soft-map": soft_map},
            {},
            workloads={
                "hard-workload": {
                    "flow": "mixed-flow",
                    "timing_class": "hard-real-time",
                },
                "soft-workload": {
                    "flow": "mixed-flow",
                    "timing_class": "soft-real-time",
                },
            },
        )
        self.assertEqual("FAIL", result["verdict"], result)
        self.assertEqual(
            "hard-real-time", result["tasks"]["mixed"]["timing_class"]
        )
        self.assertEqual("FAIL", result["tasks"]["mixed"]["rta_verdict"])

    def test_unsupported_analysis_method_is_blocked(self) -> None:
        candidate = profile()
        result = analyze(
            candidate,
            {},
            {},
            {},
            analysis_method="earliest-deadline-first",
        )
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertFalse(result["scheduler_compatible"])
        self.assertTrue(any("no installed analyzer" in item for item in result["problems"]))

    def test_utilization_bound_is_inconclusive_not_failure(self) -> None:
        candidate = profile()
        units = {}
        mappings = {}
        for index, period in enumerate((5_000_000, 10_000_000, 20_000_000), start=1):
            unit, mapping = task(
                f"task-{index}", candidate["id"], f"map-{index}",
                period_ns=period, deadline_ns=period,
                budget_ns=period * 28 // 100, priority=4 - index,
            )
            units[unit["id"]] = unit
            mappings[mapping["id"]] = mapping
        result = analyze(candidate, units, mappings, {})
        self.assertEqual("PASS", result["verdict"], result)
        self.assertFalse(result["cores"]["0"]["sufficient_bound_pass"])

    def test_final_analysis_requires_evidence(self) -> None:
        candidate = profile()
        candidate["analysis_phase"] = "final"
        unit, mapping = task(
            "task", candidate["id"], "mapping",
            period_ns=10_000_000, deadline_ns=10_000_000,
            budget_ns=1_000_000, priority=1,
        )
        result = analyze(
            candidate, {"task": unit}, {"mapping": mapping}, {}
        )
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertTrue(any("final_ns" in item for item in result["problems"]))

    def test_arbitrary_deadline_uses_multi_job_busy_period(self) -> None:
        candidate = profile()
        fast, fast_map = task(
            "fast", candidate["id"], "fast-map",
            period_ns=5_000_000, deadline_ns=5_000_000,
            budget_ns=1_000_000, priority=2,
        )
        slow, slow_map = task(
            "slow", candidate["id"], "slow-map",
            period_ns=10_000_000, deadline_ns=25_000_000,
            budget_ns=7_000_000, priority=1,
        )
        slow["realtime_task"]["blocking_ns"] = 2_000_000
        result = analyze(
            candidate,
            {"fast": fast, "slow": slow},
            {"fast-map": fast_map, "slow-map": slow_map},
            {},
        )
        self.assertEqual("PASS", result["verdict"], result)
        self.assertGreater(result["tasks"]["slow"]["response_ns"], 10_000_000)
        self.assertLessEqual(
            result["tasks"]["slow"]["response_ns"],
            slow["realtime_task"]["relative_deadline_ns"],
        )

    def test_blocking_jitter_and_overheads_increase_response(self) -> None:
        baseline_profile = profile()
        baseline_profile["overheads"] = {
            "context_switch_ns": 0,
            "dispatch_ns": 0,
            "preemption_ns": 0,
            "timer_interrupt_ns": 0,
        }
        fast, fast_map = task(
            "fast", baseline_profile["id"], "fast-map",
            period_ns=5_000_000, deadline_ns=5_000_000,
            budget_ns=500_000, priority=2,
        )
        slow, slow_map = task(
            "slow", baseline_profile["id"], "slow-map",
            period_ns=10_000_000, deadline_ns=10_000_000,
            budget_ns=1_000_000, priority=1,
        )
        baseline = analyze(
            baseline_profile,
            {"fast": fast, "slow": slow},
            {"fast-map": fast_map, "slow-map": slow_map},
            {},
        )
        stressed_profile = profile()
        fast["realtime_task"]["release_jitter_ns"] = 100_000
        slow["realtime_task"]["blocking_ns"] = 200_000
        stressed = analyze(
            stressed_profile,
            {"fast": fast, "slow": slow},
            {"fast-map": fast_map, "slow-map": slow_map},
            {},
        )
        self.assertEqual("PASS", baseline["verdict"], baseline)
        self.assertEqual("PASS", stressed["verdict"], stressed)
        self.assertGreater(
            stressed["tasks"]["slow"]["response_ns"],
            baseline["tasks"]["slow"]["response_ns"],
        )

    def test_priority_mismatch_and_copy_accounting_mismatch_are_blocked(self) -> None:
        candidate = profile()
        fast, fast_map = task(
            "fast", candidate["id"], "fast-map",
            period_ns=5_000_000, deadline_ns=5_000_000,
            budget_ns=500_000, priority=1,
        )
        slow, slow_map = task(
            "slow", candidate["id"], "slow-map",
            period_ns=10_000_000, deadline_ns=10_000_000,
            budget_ns=500_000, priority=2,
        )
        channel = {
            "id": "queue",
            "profile": candidate["id"],
            "from_unit": "fast",
            "to_unit": "slow",
            "realtime_timing": {
                "cross_core": False,
                "notification_latency_ns": 0,
                "release_jitter_ns": 0,
                "copy_cost_ns": 100_000,
                "cpu_cost_accounting": [
                    {"unit": "fast", "cost_ns": 10_000}
                ],
            },
        }
        result = analyze(
            candidate,
            {"fast": fast, "slow": slow},
            {"fast-map": fast_map, "slow-map": slow_map},
            {"queue": channel},
        )
        self.assertEqual("BLOCKED", result["verdict"])
        self.assertTrue(
            any("priorities do not match RM" in item for item in result["problems"])
        )
        self.assertTrue(
            any("does not equal copy_cost_ns" in item for item in result["problems"])
        )

    def test_isr_interference_is_explicit_and_increases_response(self) -> None:
        candidate = profile()
        unit, mapping = task(
            "task", candidate["id"], "mapping",
            period_ns=10_000_000, deadline_ns=10_000_000,
            budget_ns=1_000_000, priority=1,
        )
        baseline = analyze(
            candidate, {"task": unit}, {"mapping": mapping}, {}
        )
        isr = {
            "id": "uart-isr",
            "profile": candidate["id"],
            "kind": "interrupt",
            "interrupt_interference": {
                "core": 0,
                "wcet_ns": 100_000,
                "minimum_interarrival_ns": 1_000_000,
                "release_jitter_ns": 0,
            },
        }
        with_isr = analyze(
            candidate,
            {"task": unit, "uart-isr": isr},
            {"mapping": mapping},
            {},
        )
        self.assertEqual("PASS", with_isr["verdict"], with_isr)
        self.assertIn("uart-isr", with_isr["cores"]["0"]["interrupts"])
        self.assertGreater(
            with_isr["tasks"]["task"]["response_ns"],
            baseline["tasks"]["task"]["response_ns"],
        )

        del isr["interrupt_interference"]
        missing = analyze(
            candidate,
            {"task": unit, "uart-isr": isr},
            {"mapping": mapping},
            {},
        )
        self.assertEqual("BLOCKED", missing["verdict"])
        self.assertTrue(any("interrupt_interference" in item for item in missing["problems"]))


if __name__ == "__main__":
    unittest.main()
