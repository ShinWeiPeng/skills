from __future__ import annotations

import hashlib
import json
import math
import operator
import re
import shlex
from pathlib import Path
from statistics import NormalDist
from typing import Any

import yaml

from .model import CriterionResult, Verdict, overall
from .profile import redact, required_samples
from .guided import profile_sha256


OPS = {"<": operator.lt, "<=": operator.le, ">": operator.gt, ">=": operator.ge, "==": operator.eq}


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _read_bounded(path: Path, max_bytes: int) -> bytes:
    data = bytearray()
    with path.open("rb") as source:
        while True:
            chunk = source.read(min(1048576, max_bytes - len(data) + 1))
            if not chunk:
                return bytes(data)
            data.extend(chunk)
            if len(data) > max_bytes:
                raise ValueError(f"{path} exceeds {max_bytes} bytes")


def _value(text: str) -> Any:
    lower = text.lower()
    if lower in {"true", "false"}:
        return lower == "true"
    try:
        return int(text, 0)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text


def parse_log(text: str) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    parse_errors: list[str] = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped.startswith("VAL_"):
            continue
        try:
            parts = shlex.split(stripped)
        except ValueError as exc:
            parse_errors.append(f"line {line_no}: {exc}")
            continue
        record: dict[str, Any] = {"type": parts[0], "line": line_no, "raw": raw}
        for token in parts[1:]:
            if "=" not in token:
                parse_errors.append(f"line {line_no}: token {token!r} is not key=value")
                continue
            key, value = token.split("=", 1)
            if key in record or key in {"type", "line", "raw"}:
                parse_errors.append(f"line {line_no}: duplicate or reserved key {key!r}")
                continue
            parsed_value = _value(value)
            if isinstance(parsed_value, float) and not math.isfinite(parsed_value):
                parse_errors.append(f"line {line_no}: non-finite numeric value for {key!r}")
                continue
            record[key] = parsed_value
        records.append(record)
    return {"records": records, "parse_errors": parse_errors}


def _completeness(parsed: dict[str, Any], scenario: dict[str, Any], expected_run_id: str | None = None) -> list[CriterionResult]:
    records = parsed["records"]
    results: list[CriterionResult] = []
    if parsed["parse_errors"]:
        results.append(CriterionResult("log-parse", Verdict.BLOCKED, "; ".join(parsed["parse_errors"])))
    begins = [r for r in records if r["type"] == "VAL_SESSION_BEGIN" and r.get("scenario") == scenario["id"]]
    ends = [r for r in records if r["type"] == "VAL_SESSION_END"]
    if len(begins) != 1 or len(ends) != 1:
        results.append(CriterionResult("session-window", Verdict.BLOCKED, "exactly one matching session begin and end are required"))
        return results
    begin, end = begins[0], ends[0]
    if expected_run_id is not None and begin.get("run") != expected_run_id:
        results.append(CriterionResult("expected-run", Verdict.BLOCKED, "session run ID does not match the guided/expected run ID"))
    if records[0] is not begin or records[-1] is not end:
        results.append(CriterionResult("session-boundary", Verdict.BLOCKED, "session begin and end must be the first and last validation records"))
    if begin.get("run") != end.get("run"):
        results.append(CriterionResult("session-run", Verdict.BLOCKED, "session run IDs do not match"))
    seqs = [r.get("seq") for r in records]
    if any(type(value) is not int for value in seqs):
        results.append(CriterionResult("sequence", Verdict.BLOCKED, "every validation record requires integer seq"))
    elif seqs != list(range(seqs[0], seqs[0] + len(seqs))):
        results.append(CriterionResult("sequence", Verdict.BLOCKED, "validation sequence contains a gap or reorder", {"seq": seqs}))
    times = [r.get("t_ms") for r in records]
    if any(not isinstance(value, (int, float)) for value in times):
        results.append(CriterionResult("monotonic-time", Verdict.BLOCKED, "every validation record requires numeric t_ms"))
    elif any(current < previous for previous, current in zip(times, times[1:])):
        results.append(CriterionResult("monotonic-time", Verdict.BLOCKED, "validation timestamps are not monotonic", {"t_ms": times}))
    if end.get("dropped") != 0:
        results.append(CriterionResult("dropped-records", Verdict.BLOCKED, "session reports dropped records", {"dropped": end.get("dropped")}))
    if end.get("records") != len(records):
        results.append(CriterionResult("record-count", Verdict.BLOCKED, "reported record count does not match parsed validation records", {"reported": end.get("records"), "parsed": len(records)}))
    expected_reason = scenario.get("completion", {}).get("session_end_reason")
    if end.get("reason") != expected_reason:
        results.append(CriterionResult("session-reason", Verdict.BLOCKED, "session end reason does not match the scenario completion contract", {"actual": end.get("reason"), "required": expected_reason}))
    if scenario.get("warmup_required", False):
        warmup_begins = [r for r in records if r["type"] == "VAL_PHASE" and r.get("name") == "warmup" and r.get("state") == "begin"]
        warmup_ends = [r for r in records if r["type"] == "VAL_PHASE" and r.get("name") == "warmup" and r.get("state") == "end"]
        first_stat_line = min((r["line"] for r in records if r["type"] == "VAL_STATS"), default=math.inf)
        if len(warmup_begins) != 1 or len(warmup_ends) != 1:
            results.append(CriterionResult("warmup-window", Verdict.BLOCKED, "exactly one warmup begin and end are required"))
        elif not begin["line"] < warmup_begins[0]["line"] < warmup_ends[0]["line"] < first_stat_line:
            results.append(CriterionResult("warmup-window", Verdict.BLOCKED, "warmup must be inside the session and end before steady-state statistics"))
    duration = end.get("duration_ms")
    if not isinstance(duration, (int, float)):
        results.append(CriterionResult("session-duration", Verdict.BLOCKED, "session end requires numeric duration_ms"))
    elif duration > float(scenario["max_duration_ms"]):
        results.append(CriterionResult("session-duration", Verdict.BLOCKED, "session exceeded max_duration_ms", {"duration_ms": duration, "max_duration_ms": scenario["max_duration_ms"]}))
    elif isinstance(begin.get("t_ms"), (int, float)) and isinstance(end.get("t_ms"), (int, float)) and duration != end["t_ms"] - begin["t_ms"]:
        results.append(CriterionResult("session-duration", Verdict.BLOCKED, "reported duration_ms does not match monotonic session timestamps"))
    if not results:
        results.append(CriterionResult("evidence-completeness", Verdict.PASS, "session framing, monotonic time, sequence, and drop counters are complete"))
    return results


def _metric(parsed: dict[str, Any], name: str) -> tuple[dict[str, Any] | None, list[dict[str, Any]], dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    stats_records = [r for r in parsed["records"] if r["type"] == "VAL_STATS" and r.get("metric") == name]
    buckets = [r for r in parsed["records"] if r["type"] == "VAL_BUCKET" and r.get("metric") == name]
    meta_records = [r for r in parsed["records"] if r["type"] == "VAL_STATS_META" and r.get("metric") == name]
    end_records = [r for r in parsed["records"] if r["type"] == "VAL_STATS_END" and r.get("metric") == name]
    errors: list[str] = []
    if len(stats_records) > 1:
        errors.append("multiple VAL_STATS snapshots for the same metric/window are ambiguous")
    if len(meta_records) > 1:
        errors.append("multiple VAL_STATS_META records for the same metric/window are ambiguous")
    if len(end_records) > 1:
        errors.append("multiple VAL_STATS_END records for the same metric/window are ambiguous")
    return (
        stats_records[0] if len(stats_records) == 1 else None,
        buckets,
        meta_records[0] if len(meta_records) == 1 else None,
        end_records[0] if len(end_records) == 1 else None,
        errors,
    )


def _compare(actual: float, op: str, expected: float) -> bool:
    return OPS[op](actual, expected)


def _percentile(buckets: list[dict[str, Any]], n: int, percentile: float) -> float | None:
    if not buckets or n <= 0:
        return None
    target = math.ceil(percentile * n)
    cumulative = 0
    for bucket in sorted(buckets, key=lambda item: float(item["le"])):
        cumulative += int(bucket.get("count", 0))
        if cumulative >= target:
            return float(bucket["le"])
    return None


def _wilson_upper(errors: int, n: int, confidence: float) -> float:
    if n <= 0:
        return 1.0
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    p = errors / n
    denom = 1 + z * z / n
    center = p + z * z / (2 * n)
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return (center + margin) / denom


def _validate_statistic(stats: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    n = stats.get("n")
    minimum = stats.get("min")
    maximum = stats.get("max")
    total = stats.get("sum")
    squares = stats.get("sum_sq")
    errors = stats.get("errors")
    if type(n) is not int or n <= 0:
        problems.append("n must be a positive integer")
        return problems
    if not _finite(minimum) or not _finite(maximum) or minimum > maximum:
        problems.append("min/max are invalid")
    if errors is not None and (type(errors) is not int or errors < 0 or errors > n):
        problems.append("errors must be between zero and n")
    if not _finite(total):
        problems.append("sum must be numeric")
    if not _finite(squares):
        problems.append("sum_sq must be numeric")
    if isinstance(total, (int, float)) and isinstance(minimum, (int, float)) and isinstance(maximum, (int, float)):
        if not minimum * n <= total <= maximum * n:
            problems.append("sum is inconsistent with n and min/max")
    if isinstance(squares, (int, float)) and isinstance(total, (int, float)) and squares + 1e-9 < total * total / n:
        problems.append("sum_sq is inconsistent with sum and n")
    return problems


def evaluate(profile: dict[str, Any], scenario_id: str, raw_text: str, native: dict[str, Any] | None = None, verified_source_trace_sha256: str | None = None, expected_run_id: str | None = None) -> tuple[dict[str, Any], list[CriterionResult], Verdict]:
    parsed = parse_log(raw_text)
    scenario = next((item for item in profile["scenarios"] if item["id"] == scenario_id), None)
    if scenario is None:
        result = CriterionResult("scenario", Verdict.BLOCKED, f"scenario {scenario_id!r} is not declared")
        return parsed, [result], Verdict.BLOCKED
    results = _completeness(parsed, scenario, expected_run_id)
    window_complete = all(item.verdict == Verdict.PASS for item in results)
    completion = scenario["completion"]
    trigger_ids = set(completion["trigger_criteria"])
    for pattern in scenario.get("forbidden_patterns", []):
        if re.search(pattern, raw_text, flags=re.MULTILINE):
            results.append(CriterionResult(f"forbidden:{pattern}", Verdict.FAIL, "forbidden pattern was observed"))
    events = [str(r.get("name")) for r in parsed["records"] if r["type"] == "VAL_EVENT"]
    observations = [r for r in parsed["records"] if r["type"] == "VAL_OBSERVATION"]
    session_begin = next((r for r in parsed["records"] if r["type"] == "VAL_SESSION_BEGIN"), {})
    if native is not None:
        if type(native.get("lost_events")) is not int:
            results.append(CriterionResult("native-trace-loss", Verdict.BLOCKED, "native trace must explicitly report lost_events"))
        elif native["lost_events"] != 0:
            results.append(CriterionResult("native-trace-loss", Verdict.BLOCKED, "native trace reports lost events", {"lost_events": native.get("lost_events")}))
        if native.get("run_id") != session_begin.get("run"):
            results.append(CriterionResult("native-correlation", Verdict.BLOCKED, "native trace and application log run IDs do not match"))
        trace_hash = native.get("source_trace_sha256")
        if not isinstance(trace_hash, str) or re.fullmatch(r"[0-9a-fA-F]{64}", trace_hash) is None:
            results.append(CriterionResult("native-source-trace", Verdict.BLOCKED, "normalized native evidence must bind the original trace SHA-256"))
        elif verified_source_trace_sha256 is None or trace_hash.lower() != verified_source_trace_sha256.lower():
            results.append(CriterionResult("native-source-trace", Verdict.BLOCKED, "original native trace was not supplied or its computed SHA-256 does not match"))

    for criterion in scenario["criteria"]:
        cid = criterion["id"]
        ctype = criterion["type"]
        if ctype == "event_sequence":
            expected = [str(x) for x in criterion["events"]]
            cursor = 0
            for event in events:
                if cursor < len(expected) and event == expected[cursor]:
                    cursor += 1
            verdict = Verdict.PASS if cursor == len(expected) else (Verdict.BLOCKED if cid in trigger_ids or not window_complete else Verdict.FAIL)
            results.append(CriterionResult(cid, verdict, "ordered events matched" if verdict == Verdict.PASS else "ordered events did not match or the window is incomplete", {"expected": expected, "observed": events}))
            continue
        if ctype == "observation":
            match = next((r for r in observations if r.get("code") == criterion.get("code") and r.get("step") == criterion.get("step") and r.get("observer") == "user"), None)
            if match is None:
                results.append(CriterionResult(cid, Verdict.BLOCKED, "required operator observation is missing"))
            else:
                expected = criterion.get("result", "pass")
                verdict = Verdict.PASS if match.get("result") == expected else Verdict.FAIL
                results.append(CriterionResult(cid, verdict, "operator observation matched" if verdict == Verdict.PASS else "operator observation failed", {"line": match["line"], "source": "operator"}))
            continue
        if ctype == "native_metric":
            actual_provider = profile.get("target", {}).get("provider")
            if native is not None:
                correlation = native.get("correlation")
                max_error = float(criterion["max_alignment_error_ns"])
                if not isinstance(correlation, dict) or correlation.get("marker") != session_begin.get("run") or not _finite(correlation.get("alignment_error_ns")) or correlation["alignment_error_ns"] < 0 or correlation["alignment_error_ns"] > max_error:
                    results.append(CriterionResult(cid, Verdict.BLOCKED, "native/application monotonic correlation is missing or outside its alignment budget"))
                    continue
                if native.get("provider") != actual_provider:
                    results.append(CriterionResult(cid, Verdict.BLOCKED, "native evidence provider does not match the selected profile provider"))
                    continue
                native_window = native.get("window")
                if not isinstance(native_window, dict) or native_window.get("complete") is not True:
                    results.append(CriterionResult(cid, Verdict.BLOCKED, "native observation window is not explicitly complete"))
                    continue
                minimum = required_samples(criterion["sample_plan"])
                if type(native_window.get("n")) is not int or native_window["n"] < minimum:
                    results.append(CriterionResult(cid, Verdict.BLOCKED, "native observation window has insufficient samples", {"n": native_window.get("n"), "required": minimum, "sample_plan": criterion["sample_plan"]}))
                    continue
                if not _finite(native_window.get("duration_ms")) or native_window["duration_ms"] < 0 or native_window["duration_ms"] > float(criterion["max_duration_ms"]):
                    results.append(CriterionResult(cid, Verdict.BLOCKED, "native observation window exceeded max_duration_ms"))
                    continue
                metric = native.get("metrics", {}).get(criterion["metric"])
                semantics = criterion["native_semantics"]
                if not isinstance(metric, dict) or metric.get("n") != native_window["n"] or metric.get("unit") != criterion["native_unit"] or any(metric.get(key) != semantics[key] for key in ("start_event", "end_event", "clock")):
                    results.append(CriterionResult(cid, Verdict.BLOCKED, "native metric is not sample- and semantics-bound to its observation window"))
                    continue
                field = criterion.get("field", "max")
                actual = metric.get(field) if isinstance(metric, dict) else None
                if not _finite(actual):
                    results.append(CriterionResult(cid, Verdict.BLOCKED, "required native metric field is missing"))
                    continue
                expected = float(criterion.get("threshold", 0))
                op = str(criterion.get("operator", "<="))
                verdict = Verdict.PASS if _compare(float(actual), op, expected) else Verdict.FAIL
                results.append(CriterionResult(cid, verdict, "native metric threshold matched" if verdict == Verdict.PASS else "native metric threshold was violated", {"provider": native.get("provider"), "actual": actual, "operator": op, "threshold": expected, "alignment_error_ns": correlation["alignment_error_ns"]}))
                continue
            results.append(CriterionResult(cid, Verdict.BLOCKED, "native OS resource evidence is required; structured-log fallback cannot satisfy this criterion"))
            continue

        stats, buckets, meta, stats_end, metric_errors = _metric(parsed, criterion["metric"])
        if metric_errors:
            results.append(CriterionResult(cid, Verdict.BLOCKED, "; ".join(metric_errors)))
            continue
        if stats is None:
            results.append(CriterionResult(cid, Verdict.BLOCKED, "required statistic is missing"))
            continue
        if scenario.get("warmup_required", False) and ctype == "statistic" and stats.get("phase") != "steady":
            results.append(CriterionResult(cid, Verdict.BLOCKED, "post-warmup statistic must declare phase=steady"))
            continue
        if scenario.get("warmup_required", False) and ctype == "statistic":
            warmup_end = next((r for r in parsed["records"] if r["type"] == "VAL_PHASE" and r.get("name") == "warmup" and r.get("state") == "end"), None)
            if warmup_end is None or not isinstance(stats.get("window_start_ms"), (int, float)) or stats["window_start_ms"] < warmup_end.get("t_ms", math.inf):
                results.append(CriterionResult(cid, Verdict.BLOCKED, "steady-state statistic window starts before warmup completed"))
                continue
        if scenario.get("warmup_required", False) and ctype == "hard_limit" and stats.get("scope") != "all_phases":
            results.append(CriterionResult(cid, Verdict.BLOCKED, "warmup hard-limit statistic must declare scope=all_phases"))
            continue
        session_end = next((r for r in parsed["records"] if r["type"] == "VAL_SESSION_END"), {})
        if scenario.get("warmup_required", False) and ctype == "hard_limit" and (stats.get("window_start_ms") != session_begin.get("t_ms") or stats_end is None or stats_end.get("t_ms") != session_end.get("t_ms")):
            results.append(CriterionResult(cid, Verdict.BLOCKED, "all-phases hard-limit window must span the full session timestamps"))
            continue
        consistency = _validate_statistic(stats)
        if consistency:
            results.append(CriterionResult(cid, Verdict.BLOCKED, "; ".join(consistency)))
            continue
        if buckets:
            limits = [item.get("le") for item in buckets]
            counts = [item.get("count") for item in buckets]
            if any(not isinstance(value, (int, float)) for value in limits) or len(set(limits)) != len(limits) or any(not isinstance(value, int) or value < 0 for value in counts):
                results.append(CriterionResult(cid, Verdict.BLOCKED, "histogram limits must be unique numbers and counts must be non-negative integers"))
                continue
        ordered_metric_records = [stats, *buckets, *([meta] if meta else []), *([stats_end] if stats_end else [])]
        if stats_end is not None and (not isinstance(stats.get("window_start_ms"), (int, float)) or not isinstance(stats_end.get("elapsed_ms"), (int, float)) or stats_end["elapsed_ms"] < 0 or stats["window_start_ms"] > stats.get("t_ms", -math.inf) or any(left["line"] >= right["line"] for left, right in zip(ordered_metric_records, ordered_metric_records[1:]))):
            results.append(CriterionResult(cid, Verdict.BLOCKED, "metric window timestamps or record order are impossible"))
            continue
        if stats.get("saturated") not in (None, 0) or (meta and meta.get("saturated") not in (None, 0)):
            results.append(CriterionResult(cid, Verdict.BLOCKED, "statistic accumulator saturated"))
            continue
        n = int(stats["n"])
        if ctype in {"statistic", "hard_limit"}:
            if stats_end is None or stats_end.get("dropped") != 0 or stats_end.get("n") != n:
                results.append(CriterionResult(cid, Verdict.BLOCKED, "metric window end is missing, dropped, or has a mismatched sample count"))
                continue
            elapsed = stats_end.get("elapsed_ms")
            if not isinstance(elapsed, (int, float)) or not isinstance(stats.get("window_start_ms"), (int, float)) or elapsed != stats_end.get("t_ms") - stats.get("window_start_ms", 0):
                results.append(CriterionResult(cid, Verdict.BLOCKED, "metric elapsed_ms does not match its monotonic window timestamps"))
                continue
        if ctype == "statistic":
            minimum = required_samples(criterion["sample_plan"])
            if n < minimum:
                results.append(CriterionResult(cid, Verdict.BLOCKED, "minimum sample count was not reached", {"n": n, "required": minimum, "sample_plan": criterion["sample_plan"]}))
                continue
            elapsed = stats_end.get("elapsed_ms")
            if not isinstance(elapsed, (int, float)) or elapsed > float(criterion["max_duration_ms"]):
                results.append(CriterionResult(cid, Verdict.BLOCKED, "statistical window did not complete within max_duration_ms", {"elapsed_ms": elapsed, "max_duration_ms": criterion["max_duration_ms"]}))
                continue
            if not window_complete:
                results.append(CriterionResult(cid, Verdict.BLOCKED, "statistical result cannot be judged from an incomplete session window"))
                continue
        if criterion.get("timing", False):
            budget = criterion["instrumentation_budget"]
            if meta is None:
                results.append(CriterionResult(cid, Verdict.BLOCKED, "timing statistic lacks instrumentation metadata"))
                continue
            exceeded = {key: {"actual": meta.get(key), "limit": limit} for key, limit in budget.items() if not isinstance(meta.get(key), (int, float)) or float(meta[key]) > float(limit)}
            clock = criterion["clock"]
            if meta.get("clock") != clock["source"] or meta.get("clock_hz") != clock["hz"] or meta.get("resolution_ns") != clock["resolution_ns"]:
                exceeded["clock"] = {"actual": {"source": meta.get("clock"), "hz": meta.get("clock_hz"), "resolution_ns": meta.get("resolution_ns")}, "required": clock}
            if exceeded:
                results.append(CriterionResult(cid, Verdict.BLOCKED, "instrumentation exceeded its budget or used the wrong clock", exceeded))
                continue
        method = criterion.get("method", "field")
        total = float(stats.get("sum", 0))
        squares = stats.get("sum_sq")
        if method == "mean":
            actual = total / n
        elif method == "mean_upper_ci":
            if n < 30 or not isinstance(squares, (int, float)):
                results.append(CriterionResult(cid, Verdict.BLOCKED, "mean_upper_ci requires at least 30 samples and sum_sq"))
                continue
            mean = total / n
            variance = max(0.0, (float(squares) - total * total / n) / (n - 1))
            z = NormalDist().inv_cdf((1 + float(criterion["sample_plan"].get("confidence", criterion.get("confidence", 0.95)))) / 2)
            actual = mean + z * math.sqrt(variance / n)
        elif method == "percentile":
            if sum(int(item.get("count", 0)) for item in buckets) != n:
                results.append(CriterionResult(cid, Verdict.BLOCKED, "histogram bucket total does not equal n"))
                continue
            confidence = float(criterion["sample_plan"].get("confidence", criterion.get("confidence", 0.95)))
            epsilon = math.sqrt(math.log(2 / (1 - confidence)) / (2 * n))
            requested = min(1.0, float(criterion.get("percentile", 0.95)) + epsilon)
            actual = _percentile(buckets, n, requested)
            if actual is None:
                results.append(CriterionResult(cid, Verdict.BLOCKED, "histogram cannot resolve the confidence-adjusted percentile"))
                continue
        elif method == "wilson_upper":
            if type(stats.get("errors")) is not int:
                results.append(CriterionResult(cid, Verdict.BLOCKED, "wilson_upper requires an explicit integer errors counter"))
                continue
            actual = _wilson_upper(int(stats["errors"]), n, float(criterion["sample_plan"].get("confidence", criterion.get("confidence", 0.95))))
        else:
            field = criterion.get("field", "max")
            actual = stats.get(field)
            if not isinstance(actual, (int, float)):
                results.append(CriterionResult(cid, Verdict.BLOCKED, f"statistic field {field!r} is missing"))
                continue
            actual = float(actual)
        expected = float(criterion.get("threshold", criterion.get("max", 0)))
        op = str(criterion.get("operator", "<="))
        verdict = Verdict.PASS if _compare(float(actual), op, expected) else Verdict.FAIL
        results.append(CriterionResult(cid, verdict, "statistical threshold matched" if verdict == Verdict.PASS else "statistical threshold was violated", {"actual": actual, "operator": op, "threshold": expected, "n": n, "required_samples": required_samples(criterion["sample_plan"]), "method": method, "confidence": criterion["sample_plan"].get("confidence", criterion.get("confidence", 0.95))}))
    by_id = {item.criterion_id: item for item in results}
    trigger_complete = all(by_id.get(criterion_id) is not None and by_id[criterion_id].verdict == Verdict.PASS for criterion_id in completion["trigger_criteria"])
    if not trigger_complete:
        for item in results:
            if item.criterion_id in completion["required_criteria"] and item.verdict == Verdict.FAIL:
                item.verdict = Verdict.BLOCKED
                item.reason = "required behavior cannot be judged because the declared trigger was not proven"
        by_id = {item.criterion_id: item for item in results}
    completion_ids = list(dict.fromkeys([*completion["trigger_criteria"], *completion["required_criteria"]]))
    incomplete = [criterion_id for criterion_id in completion_ids if criterion_id not in by_id or by_id[criterion_id].verdict != Verdict.PASS]
    results.append(CriterionResult("scenario-completion", Verdict.PASS if not incomplete else Verdict.BLOCKED, "all declared trigger and required criteria completed" if not incomplete else "scenario completion criteria are incomplete", {"phase": scenario["phase"], "evidence_mode": scenario["evidence_mode"], "incomplete": incomplete}))
    return parsed, results, overall(results)


def write_bundle(output_dir: Path, profile: dict[str, Any], scenario_id: str, raw_path: Path, provider: dict[str, Any], upload_actor: str = "user", native_path: Path | None = None, approvals: set[str] | None = None, native_source_path: Path | None = None, expected_run_id: str | None = None, guided_artifacts: dict[str, Any] | None = None, prerequisite_results: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    if upload_actor == "user" and not expected_run_id:
        result = {"scenario": scenario_id, "verdict": "BLOCKED", "reason": "user-uploaded evidence is not bound to an expected run ID", "upload_actor": upload_actor, "upload_verified_by_gpt": False}
        (output_dir / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return result
    max_bytes = int(profile.get("transport", {}).get("max_bytes", 1048576))
    try:
        raw = _read_bounded(raw_path, max_bytes)
    except ValueError as exc:
        result = {"scenario": scenario_id, "verdict": "BLOCKED", "reason": str(exc), "max_bytes": max_bytes, "upload_actor": upload_actor, "upload_verified_by_gpt": False if upload_actor == "user" else None}
        (output_dir / "capability.json").write_text(json.dumps(provider, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (output_dir / "permission-decisions.json").write_text(json.dumps({"approved_risks": sorted(approvals or set())}, indent=2) + "\n", encoding="utf-8")
        (output_dir / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return result
    raw_text = raw.decode("utf-8", errors="replace")
    native_raw = None
    native = None
    if native_path is not None:
        try:
            native_raw = _read_bounded(native_path, max_bytes)
            native = json.loads(native_raw.decode("utf-8"), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-standard JSON number {value}")))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            result = {"scenario": scenario_id, "verdict": "BLOCKED", "reason": f"invalid or oversized normalized native evidence: {exc}", "upload_actor": upload_actor, "upload_verified_by_gpt": False if upload_actor == "user" else None}
            (output_dir / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return result
    verified_trace_hash = None
    if native_source_path is not None:
        native_limit = int(profile.get("target", {}).get("native_max_bytes", 4294967296))
        if native_source_path.stat().st_size > native_limit:
            result = {"scenario": scenario_id, "verdict": "BLOCKED", "reason": "native source trace exceeds target.native_max_bytes", "upload_actor": upload_actor, "upload_verified_by_gpt": False if upload_actor == "user" else None}
            (output_dir / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            return result
        digest = hashlib.sha256()
        source_bytes = 0
        with native_source_path.open("rb") as source:
            for chunk in iter(lambda: source.read(1048576), b""):
                source_bytes += len(chunk)
                if source_bytes > native_limit:
                    result = {"scenario": scenario_id, "verdict": "BLOCKED", "reason": "native source trace grew beyond target.native_max_bytes while hashing", "upload_actor": upload_actor, "upload_verified_by_gpt": False if upload_actor == "user" else None}
                    (output_dir / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                    return result
                digest.update(chunk)
        verified_trace_hash = digest.hexdigest()
    parsed, criteria, verdict = evaluate(profile, scenario_id, raw_text, native, verified_trace_hash, expected_run_id)
    scenario = next(item for item in profile["scenarios"] if item["id"] == scenario_id)
    prerequisites = prerequisite_results or []
    current_profile_hash = profile_sha256(profile)
    prerequisite_ids = {
        item.get("scenario")
        for item in prerequisites
        if item.get("phase") == "enablement"
        and item.get("verdict") == "PASS"
        and item.get("profile_sha256") == current_profile_hash
    }
    missing_prerequisites = sorted(set(scenario.get("prerequisites", [])) - prerequisite_ids)
    if scenario.get("phase") == "acceptance" and missing_prerequisites:
        criteria.append(CriterionResult("validation-enablement", Verdict.BLOCKED, "acceptance requires PASS evidence from every declared enablement scenario", {"missing": missing_prerequisites}))
        verdict = overall(criteria)
    if provider.get("status") != "PASS":
        criteria.append(CriterionResult("capability", Verdict.BLOCKED, "selected evidence provider is unavailable and no allowed fallback is active", provider))
        verdict = overall(criteria)
    (output_dir / "raw.log").write_bytes(raw)
    (output_dir / "raw.sha256").write_text(hashlib.sha256(raw).hexdigest() + "\n", encoding="utf-8")
    (output_dir / "profile.snapshot.yaml").write_text(yaml.safe_dump(redact(profile), sort_keys=False, allow_unicode=True), encoding="utf-8")
    (output_dir / "capability.json").write_text(json.dumps(provider, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output_dir / "permission-decisions.json").write_text(json.dumps({"approved_risks": sorted(approvals or set())}, indent=2) + "\n", encoding="utf-8")
    if native_path:
        assert native_raw is not None
        (output_dir / "native-evidence.json").write_bytes(native_raw)
        (output_dir / "native-evidence.sha256").write_text(hashlib.sha256(native_raw).hexdigest() + "\n", encoding="utf-8")
        (output_dir / "source-trace.sha256").write_text((verified_trace_hash or "UNVERIFIED") + "\n", encoding="utf-8")
    guided_manifest: list[dict[str, Any]] = []
    guided_review: dict[str, Any] | None = None
    if guided_artifacts is not None:
        guided_dir = output_dir / "guided"
        guided_dir.mkdir(parents=True, exist_ok=True)
        sources: list[tuple[str, Path]] = [("session.json", Path(guided_artifacts["session"]))]
        sources.extend((f"response.r{index}.json", Path(path)) for index, path in enumerate(guided_artifacts.get("responses", []), 1))
        if guided_artifacts.get("review"):
            sources.append(("review.json", Path(guided_artifacts["review"])))
        if guided_artifacts.get("review_markdown"):
            sources.append(("review.md", Path(guided_artifacts["review_markdown"])))
        try:
            for name, source in sources:
                data = _read_bounded(source, max_bytes)
                digest = hashlib.sha256(data).hexdigest()
                expected_digest = guided_artifacts.get("expected_sha256", {}).get(str(source.resolve()))
                if expected_digest is not None and digest != expected_digest:
                    raise ValueError(f"guided artifact changed after validation: {source}")
                (guided_dir / name).write_bytes(data)
                (guided_dir / f"{name}.sha256").write_text(digest + "\n", encoding="utf-8")
                guided_manifest.append({"name": name, "sha256": digest, "bytes": len(data)})
            if guided_artifacts.get("review"):
                guided_review = json.loads((guided_dir / "review.json").read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            criteria.append(CriterionResult("guided-artifacts", Verdict.BLOCKED, f"guided evidence could not be preserved: {exc}"))
            verdict = overall(criteria)
        (guided_dir / "manifest.json").write_text(json.dumps(guided_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output_dir / "parse-result.json").write_text(json.dumps(parsed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    criterion_json = [{"id": r.criterion_id, "verdict": r.verdict.label, "reason": r.reason, "evidence": r.evidence} for r in criteria]
    (output_dir / "criteria-result.json").write_text(json.dumps(criterion_json, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    result = {
        "scenario": scenario_id,
        "phase": scenario["phase"],
        "gate": {"enablement": "Validation Enablement", "acceptance": "Final Runtime Acceptance"}.get(scenario["phase"]),
        "scenario_evidence_mode": scenario["evidence_mode"],
        "profile_sha256": current_profile_hash,
        "verdict": verdict.label,
        "evidence_mode": provider.get("actual_provider"),
        "requested_provider": provider.get("requested_provider"),
        "fallback_reason": provider.get("fallback_reason"),
        "upload_actor": upload_actor,
        "upload_verified_by_gpt": False if upload_actor == "user" else None,
        "guided_review_confirmed": guided_review.get("confirmation", {}).get("confirmed") if guided_review else None,
        "guided_response_revision": guided_review.get("revision") if guided_review else None,
        "prerequisites": prerequisites,
        "criteria": criterion_json,
    }
    (output_dir / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result
