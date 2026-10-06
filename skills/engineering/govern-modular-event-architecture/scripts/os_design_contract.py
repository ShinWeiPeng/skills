"""OS design checks by phase; documentary checks do not prove runtime behavior."""

from __future__ import annotations
import math

GROUPS = {
    "units": ["items"],
    "scheduling": ["items"],
    "channels": ["items"],
    "synchronization": [
        "shared_objects",
        "access_permissions",
        "protection",
        "holding_wait",
        "deadlock_avoidance",
        "priority_inversion",
        "failure_cleanup",
    ],
    "resources": [
        "capacities",
        "owners",
        "allocation",
        "budget_basis",
        "total_simultaneous",
        "os_overhead",
        "shared_accounting",
        "reclamation",
        "exhaustion",
    ],
    "lifecycle": [
        "coordinator",
        "states",
        "readiness",
        "initialization",
        "start",
        "stop",
        "cancel",
        "restart",
        "stale_activity",
        "failure_cleanup",
    ],
    "verification": [
        "rule_refs",
        "design_refs",
        "acceptance_refs",
        "methods",
        "required_evidence",
        "evidence_status",
    ],
}
SCHEDULE_FIELDS = [
    "trigger",
    "frequency_burst",
    "priority",
    "deadline",
    "execution_budget",
    "wait_budget",
    "core_assignment",
    "analysis",
]
CHANNEL_FIELDS = [
    "senders",
    "receivers",
    "purpose",
    "os_tool",
    "capacity",
    "call_environment",
    "ordering",
    "delivery_completion",
    "coalescing",
    "full_wait_timeout",
    "stop",
    "ownership",
]

CATEGORIES = [
    "environment",
    "units",
    "module_mapping",
    "scheduling_timing",
    "synchronization_channels",
    "resources",
    "lifecycle",
    "os_boundary",
    "verification",
]
PLATFORM_FIELDS = [
    "os",
    "cpu",
    "cores",
    "usable_ram",
    "capabilities",
    "call_limits",
    "scheduler",
]
OS_IDS = {
    "OS-CAP-001",
    "OS-EXEC-001",
    "OS-CHAN-001",
    "OS-SYNC-001",
    "OS-RES-001",
    "OS-TIME-001",
    "OS-LIFE-001",
}


def validate_os_designs(manifest, phase="design", source_versions=None):
    errors = []

    def issue(location, message):
        errors.append(
            {
                "rule_id": "OS-DESIGN-001",
                "severity": "MUST",
                "configuration": True,
                "disposition": "active",
                "location": location,
                "message": message,
            }
        )

    phase = {"development": "implementation"}.get(phase, phase)
    if phase not in {"design", "implementation", "acceptance", "release"}:
        raise ValueError("unsupported OS check phase")
    rules = manifest.get("coding_rules")
    selection = rules.get("applicability", {}) if isinstance(rules, dict) else {}
    if not isinstance(selection, dict):
        selection = {}
    needed = any(
        isinstance(selection.get(i), dict)
        and selection[i].get("status") == "applicable"
        for i in OS_IDS
    )
    platform = manifest.get("platform_design")
    execution = manifest.get("execution_design")
    if platform is None and execution is None and not needed:
        return errors

    def envelope(value, path, fields):
        if (
            not isinstance(value, dict)
            or set(value) != {"id", "version", "data"}
            or not isinstance(value.get("id"), str)
            or not value["id"]
            or type(value.get("version")) is not int
            or value["version"] < 1
            or not isinstance(value.get("data"), dict)
            or set(value["data"]) != set(fields)
        ):
            issue(
                path, "expected stable id/version and exactly the declared data fields"
            )
            return None
        return value["data"]

    facts = envelope(platform, "platform_design", PLATFORM_FIELDS)
    ed = envelope(
        execution,
        "execution_design",
        ["platform_ref", "design_refs", "applicability", "groups", "evidence"],
    )

    def decision(value, path):
        if (
            not isinstance(value, dict)
            or set(value)
            - {"status", "reason", "value", "unit", "basis", "source_refs"}
            or value.get("status") not in {"known", "unknown", "not-applicable"}
            or not isinstance(value.get("reason"), str)
            or not value["reason"].strip()
        ):
            issue(path, "expected fact status and reason")
            return False
        if value["status"] == "unknown":
            issue(path, "unknown fact blocks dependent OS design")
            return False
        if value["status"] == "known" and (
            "value" not in value
            or not value.get("basis")
            or not isinstance(value.get("source_refs"), list)
            or not value["source_refs"]
        ):
            issue(path, "known facts require value, basis and source references")
            return False
        return value["status"] == "known"

    if facts:
        for key, row in facts.items():
            if decision(row, "platform_design.data." + key) and key in {
                "cores",
                "usable_ram",
            }:
                if (
                    type(row.get("value"))
                    not in ({int} if key == "cores" else {int, float})
                    or not math.isfinite(row["value"])
                    or row["value"] <= 0
                    or row.get("unit")
                    not in ({"count"} if key == "cores" else {"B", "KiB", "MiB", "GiB"})
                ):
                    issue(
                        "platform_design.data." + key,
                        "numeric capacity needs a positive number and supported unit",
                    )
    if not ed:
        return errors
    ref = ed["platform_ref"]
    if (
        not isinstance(ref, dict)
        or set(ref) != {"id", "version"}
        or not isinstance(platform, dict)
        or ref != {k: platform.get(k) for k in ("id", "version")}
    ):
        issue(
            "execution_design.data.platform_ref", "platform version reference mismatch"
        )
    refs = ed["design_refs"]
    if not isinstance(refs, list) or any(
        not isinstance(r, dict)
        or set(r) != {"id", "version"}
        or not isinstance(r.get("id"), str)
        or type(r.get("version")) is not int
        or r["version"] < 1
        for r in refs
    ):
        issue(
            "execution_design.data.design_refs",
            "expected ID/version references; fixed paths and hashes are checked by the shared source owner",
        )
    else:
        known = source_versions or {}
        for r in refs:
            if known.get(r["id"], {}).get("version") != r["version"]:
                issue(
                    "execution_design.data.design_refs",
                    "unresolved design ID/version: " + r["id"],
                )
    applicability = ed["applicability"]
    if not isinstance(applicability, dict) or set(applicability) != set(CATEGORIES):
        issue(
            "execution_design.data.applicability",
            "nine applicability categories required",
        )
    else:
        for key, row in applicability.items():
            if (
                not isinstance(row, dict)
                or set(row) != {"status", "reason"}
                or row.get("status") not in {"applicable", "not-applicable", "unknown"}
                or not isinstance(row.get("reason"), str)
                or not row["reason"].strip()
            ):
                issue(
                    "execution_design.data.applicability." + key,
                    "expected applicability status and reason",
                )
            elif row["status"] == "unknown":
                issue(
                    "execution_design.data.applicability." + key,
                    "unknown is not not-applicable",
                )
    groups = ed["groups"]
    if not isinstance(groups, dict) or set(groups) != set(GROUPS):
        issue("execution_design.data.groups", "seven execution design groups required")
    else:
        for key, fields in GROUPS.items():
            row = groups[key]
            path = "execution_design.data.groups." + key
            if (
                not isinstance(row, dict)
                or set(row) != {"status", "reason", "details"}
                or row.get("status") not in {"applicable", "not-applicable", "unknown"}
                or not isinstance(row.get("reason"), str)
                or not row["reason"].strip()
            ):
                issue(path, "expected group status, reason and details")
                continue
            if row["status"] == "unknown":
                issue(path, "unresolved design")
                continue
            details = row["details"]
            if row["status"] == "not-applicable":
                if details != {}:
                    issue(
                        path,
                        "not-applicable group must not contain an alternative design",
                    )
                continue
            if (
                not isinstance(details, dict)
                or set(details) != set(fields)
                or any(
                    v is None or v == "" or v == [] or v == {} for v in details.values()
                )
            ):
                issue(path, "missing concrete design fields: " + ", ".join(fields))
                continue
            if key == "units":
                items = details["items"]
                if not isinstance(items, list) or not items:
                    issue(path, "expected execution-unit inventory")
                else:
                    seen = set()
                    for unit in items:
                        if (
                            not isinstance(unit, dict)
                            or set(unit)
                            != {
                                "id",
                                "kind",
                                "responsibility",
                                "module_refs",
                                "call_environment",
                            }
                            or unit.get("kind")
                            not in {
                                "Task",
                                "Thread",
                                "ISR",
                                "EventLoop",
                                "Worker",
                                "Main",
                            }
                            or not isinstance(unit.get("id"), str)
                            or not unit["id"]
                            or unit["id"] in seen
                        ):
                            issue(path, "invalid or duplicate execution unit")
                            continue
                        seen.add(unit["id"])
                        rs = unit["module_refs"]
                        if (
                            not isinstance(rs, list)
                            or not rs
                            or any(
                                not isinstance(r, dict)
                                or set(r) != {"id", "version"}
                                or (source_versions or {}).get(r.get("id"))
                                != {"version": r.get("version"), "kind": "module"}
                                for r in rs
                            )
                        ):
                            issue(path, "unresolved module ID/version")

            def quantity(value, location, units):
                if (
                    not isinstance(value, dict)
                    or set(value) != {"value", "unit", "basis", "source_refs"}
                    or type(value.get("value")) not in {int, float}
                    or not math.isfinite(value["value"])
                    or value["value"] < 0
                    or value.get("unit") not in units
                    or not isinstance(value.get("basis"), str)
                    or not value["basis"]
                    or not isinstance(value.get("source_refs"), list)
                    or not value["source_refs"]
                ):
                    issue(
                        location,
                        "expected numeric value, supported unit, basis and source references",
                    )

            if key in {"scheduling", "channels"}:
                units_group = groups.get("units", {})
                unit_items = (
                    units_group.get("details", {}).get("items", [])
                    if isinstance(units_group, dict)
                    else []
                )
                unit_ids = (
                    {
                        r["id"]
                        for r in unit_items
                        if isinstance(r, dict) and isinstance(r.get("id"), str)
                    }
                    if isinstance(unit_items, list)
                    else set()
                )
                records = details["items"]
                if not isinstance(records, list) or not records:
                    issue(
                        path + ".items",
                        "expected a per-unit scheduling or per-channel inventory",
                    )
                    continue
                seen = set()
                for index, record in enumerate(records):
                    location = path + ".items[" + str(index) + "]"
                    fields = SCHEDULE_FIELDS if key == "scheduling" else CHANNEL_FIELDS
                    identity = "unit_ref" if key == "scheduling" else "id"
                    if (
                        not isinstance(record, dict)
                        or set(record) != set(fields) | {identity}
                        or not isinstance(record.get(identity), str)
                        or not record[identity]
                        or record[identity] in seen
                        or any(
                            v is None or v == "" or v == [] or v == {}
                            for v in record.values()
                        )
                    ):
                        issue(
                            location,
                            "invalid/duplicate inventory identity or missing concrete row fields",
                        )
                        continue
                    seen.add(record[identity])
                    if key == "scheduling":
                        if record["unit_ref"] not in unit_ids:
                            issue(
                                location + ".unit_ref", "unresolved execution-unit ID"
                            )
                        for name in ("deadline", "execution_budget", "wait_budget"):
                            quantity(
                                record[name],
                                location + "." + name,
                                {"ns", "us", "ms", "s"},
                            )
                        rates = record["frequency_burst"]
                        if not isinstance(rates, dict) or set(rates) != {
                            "frequency",
                            "burst",
                        }:
                            issue(
                                location + ".frequency_burst",
                                "expected frequency and burst bounds",
                            )
                        else:
                            quantity(
                                rates["frequency"], location + ".frequency", {"Hz"}
                            )
                            quantity(rates["burst"], location + ".burst", {"count"})
                    else:
                        quantity(
                            record["capacity"],
                            location + ".capacity",
                            {"count", "B", "KiB", "MiB"},
                        )
                        if (
                            isinstance(record["capacity"], dict)
                            and type(record["capacity"].get("value")) in {int, float}
                            and record["capacity"]["value"] <= 0
                        ):
                            issue(
                                location + ".capacity",
                                "channel capacity must be positive",
                            )
                        for side in ("senders", "receivers"):
                            refs = record[side]
                            if (
                                not isinstance(refs, list)
                                or not refs
                                or any(
                                    not isinstance(r, str) or r not in unit_ids
                                    for r in refs
                                )
                            ):
                                issue(
                                    location + "." + side,
                                    "unresolved execution-unit IDs",
                                )
                if key == "scheduling" and seen != unit_ids:
                    issue(
                        path + ".items",
                        "every execution unit requires its own scheduling contract",
                    )
            if key == "resources":
                quantity(
                    details["total_simultaneous"],
                    path + ".total_simultaneous",
                    {"B", "KiB", "MiB", "GiB"},
                )
                quantity(
                    details["os_overhead"],
                    path + ".os_overhead",
                    {"B", "KiB", "MiB", "GiB"},
                )
                capacities = details["capacities"]
                if not isinstance(capacities, list) or not capacities:
                    issue(path + ".capacities", "expected resource inventory")
                else:
                    seen = set()
                    for resource in capacities:
                        if (
                            not isinstance(resource, dict)
                            or set(resource)
                            != {
                                "id",
                                "kind",
                                "quantity",
                                "unit",
                                "owner",
                                "basis",
                                "source_refs",
                            }
                            or not isinstance(resource.get("id"), str)
                            or resource["id"] in seen
                            or type(resource.get("quantity")) not in {int, float}
                            or resource["quantity"] < 0
                            or resource.get("unit")
                            not in {"count", "B", "KiB", "MiB", "GiB"}
                            or not resource.get("basis")
                            or not resource.get("source_refs")
                        ):
                            issue(
                                path + ".capacities",
                                "invalid or duplicate typed resource",
                            )
                        else:
                            seen.add(resource["id"])
    evidence = ed["evidence"]
    if not isinstance(evidence, dict) or set(evidence) != {
        "design",
        "implementation",
        "acceptance",
    }:
        issue("execution_design.data.evidence", "separate phase evidence required")
    else:
        phases = (
            ["design"]
            if phase == "design"
            else ["design", "implementation"]
            if phase == "implementation"
            else ["design", "implementation", "acceptance"]
        )
        for name in phases:
            row = evidence[name]
            path = "execution_design.data.evidence." + name
            if (
                not isinstance(row, dict)
                or set(row) != {"status", "method", "refs", "environment"}
                or row.get("status") not in {"pass", "pending", "not-applicable"}
                or not isinstance(row.get("method"), str)
                or not row["method"]
                or not isinstance(row.get("refs"), list)
                or not isinstance(row.get("environment"), str)
            ):
                issue(path, "expected phase status, method, references and environment")
                continue
            if row["status"] == "pending":
                issue(path, "required phase evidence pending")
            elif row["status"] == "pass" and (
                not row["refs"] or not row["environment"]
            ):
                issue(
                    path, "passing phase requires inspectable evidence and environment"
                )
    return errors
