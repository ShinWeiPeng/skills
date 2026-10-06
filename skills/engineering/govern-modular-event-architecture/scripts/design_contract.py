"""Structured implementation designs in the existing manifest, not parallel files."""

from __future__ import annotations

import json

MODULE_FIELDS = (
    "identity_scope",
    "responsibility",
    "public_contracts",
    "invariants",
    "variants",
    "type_state_ownership",
    "implementation_method",
    "dependencies",
    "execution_synchronization",
    "resource_timing",
    "error_lifecycle",
    "traceability",
)
INTERFACE_FIELDS = (
    "identity_purpose",
    "call_conditions",
    "parameters",
    "access_lifetime",
    "completion_result",
    "state_effects",
    "failure_progress",
    "resource_timing",
    "verification",
)
FLOW_FIELDS = (
    "identity_purpose",
    "trigger_completion",
    "steps",
    "data_correlation",
    "ownership_buffers",
    "execution_timing",
    "transport_coordination",
    "failure_stop_verification",
)


def validate_designs(manifest):
    """Validate optional v1 adoption; unknowns cannot be promoted to verified."""
    design = manifest.get("implementation_design")
    if "implementation_design" not in manifest:
        return []  # legacy schema; coding-standards workflow requires migration
    errors = []

    def issue(path, message):
        errors.append(
            {
                "rule_id": "DESIGN001",
                "severity": "MUST",
                "location": path,
                "message": message,
                "configuration": True,
                "disposition": "active",
            }
        )

    if (
        not isinstance(design, dict)
        or type(design.get("version")) is not int
        or design.get("version") != 1
    ):
        issue("implementation_design", "expected implementation design version 1")
        return errors
    known = {}
    for key in ("modules", "flows", "types", "state_objects", "ports", "events"):
        rows = manifest.get(key, [])
        if not isinstance(rows, list):
            issue(key, "expected a catalog list")
            rows = []
        known[key] = {
            row["id"]
            for row in rows
            if isinstance(row, dict) and isinstance(row.get("id"), str)
        }
    if set(design) - {"version", "modules", "interfaces", "flows"}:
        issue("implementation_design", "unknown design collection")
    for kind, fields in (
        ("modules", MODULE_FIELDS),
        ("interfaces", INTERFACE_FIELDS),
        ("flows", FLOW_FIELDS),
    ):
        records = design.get(kind)
        if not isinstance(records, dict):
            issue(kind, "expected ID-keyed design records")
            continue
        if kind in known and set(records) != known[kind]:
            issue(kind, "design coverage must match declared IDs exactly")
        for identity, record in records.items():
            path = f"implementation_design.{kind}.{identity}"
            if (
                not isinstance(identity, str)
                or not identity
                or not isinstance(record, dict)
            ):
                issue(path, "invalid design record")
                continue
            if set(record) != {"status", "groups", "module_ref", "evidence_refs"}:
                issue(path, "expected status, groups, module_ref and evidence_refs")
            if (
                not isinstance(record.get("module_ref"), str)
                or record["module_ref"] not in known["modules"]
            ):
                issue(path, "unknown module owner")
            if kind == "modules" and record.get("module_ref") != identity:
                issue(path, "module design must reference its own owner")
            status = record.get("status")
            if not isinstance(status, str) or status not in {
                "planned",
                "implemented",
                "verified",
            }:
                issue(path, "invalid implementation status")
            evidence = record.get("evidence_refs")
            if not isinstance(evidence, list) or any(
                not isinstance(x, str) or not x for x in evidence
            ):
                issue(path, "invalid evidence references")
            elif status == "verified" and not evidence:
                issue(
                    path,
                    "verified requires explicit evidence references, independently reviewed",
                )
            groups = record.get("groups")
            if not isinstance(groups, dict) or set(groups) != set(fields):
                issue(path, "missing or unknown design groups")
                continue
            for name, group in groups.items():
                location = path + "." + name
                if not isinstance(group, dict) or set(group) - {
                    "applicability",
                    "value",
                    "reason",
                    "refs",
                }:
                    issue(location, "invalid design group")
                    continue
                try:
                    json.dumps(group, sort_keys=True, allow_nan=False)
                except (TypeError, ValueError):
                    issue(
                        location,
                        "design values must be JSON-compatible; quote dates and use string keys",
                    )
                    continue
                applicability = group.get("applicability")
                if not isinstance(applicability, str) or applicability not in {
                    "applicable",
                    "not-applicable",
                    "unknown",
                }:
                    issue(location, "invalid applicability")
                    continue
                if applicability == "unknown":
                    issue(location, "unresolved design fact")
                if applicability == "applicable" and group.get("value") in (
                    None,
                    "",
                    [],
                    {},
                ):
                    issue(location, "applicable group requires a value")
                if applicability in {"not-applicable", "unknown"} and (
                    not isinstance(group.get("reason"), str)
                    or not group["reason"].strip()
                ):
                    issue(location, "non-applicable or unknown group requires a reason")
                refs = group.get("refs", {})
                if not isinstance(refs, dict):
                    issue(location, "refs must map a catalog to IDs")
                    continue
                interfaces = design.get("interfaces", {})
                catalogs = known | {
                    "interfaces": set(interfaces)
                    if isinstance(interfaces, dict)
                    else set()
                }
                for catalog, ids in refs.items():
                    if (
                        catalog not in catalogs
                        or not isinstance(ids, list)
                        or any(
                            not isinstance(value, str) or value not in catalogs[catalog]
                            for value in ids
                        )
                    ):
                        issue(location, "unknown or invalid catalog reference")
                if (
                    kind == "modules"
                    and name == "error_lifecycle"
                    and applicability == "applicable"
                ):
                    value = group.get("value")
                    if not isinstance(value, dict):
                        issue(
                            location,
                            "declare a state-transition subtable or reasoned not-applicable result",
                        )
                    elif "transitions" in value:
                        transitions = value["transitions"]
                        transition_fields = {
                            "state_object_ref",
                            "from_state",
                            "to_state",
                            "trigger",
                            "guard",
                            "effects",
                        }
                        if not isinstance(transitions, list) or not transitions:
                            issue(location, "expected nonempty state transitions")
                        else:
                            for transition in transitions:
                                if (
                                    not isinstance(transition, dict)
                                    or not transition_fields <= set(transition)
                                    or any(
                                        not isinstance(transition[key], str)
                                        or not transition[key].strip()
                                        for key in transition_fields
                                    )
                                ):
                                    issue(
                                        location,
                                        "missing or invalid state transition fields",
                                    )
                                elif (
                                    transition["state_object_ref"]
                                    not in known["state_objects"]
                                ):
                                    issue(
                                        location, "unknown state object in transition"
                                    )
                    elif (
                        value.get("transitions_applicability") != "not-applicable"
                        or not isinstance(value.get("transitions_reason"), str)
                        or not value["transitions_reason"].strip()
                    ):
                        issue(location, "missing state-transition applicability reason")
                if applicability == "applicable" and (kind, name) in {
                    ("flows", "steps"),
                    ("interfaces", "parameters"),
                }:
                    value = group.get("value")
                    required = (
                        {
                            "id",
                            "producer",
                            "consumer",
                            "interface_ref",
                            "interaction",
                            "completion",
                            "handoff",
                            "failure",
                        }
                        if kind == "flows"
                        else {"name", "type", "meaning", "passing", "nullability"}
                    )
                    if not isinstance(value, list) or not value:
                        issue(location, "expected a nonempty ordered contract subtable")
                        continue
                    seen = set()
                    for row in value:
                        if (
                            not isinstance(row, dict)
                            or not required <= set(row)
                            or any(
                                not isinstance(row[key], str) or not row[key].strip()
                                for key in required
                            )
                        ):
                            issue(location, "missing or invalid subtable fields")
                            continue
                        identity_key = row["id" if kind == "flows" else "name"]
                        if identity_key in seen:
                            issue(location, "duplicate subtable identity")
                        seen.add(identity_key)
                        if kind == "flows" and (
                            row["producer"] not in known["modules"]
                            or row["consumer"] not in known["modules"]
                            or row["interface_ref"] not in catalogs["interfaces"]
                        ):
                            issue(
                                location,
                                "unknown participant or interface in flow step",
                            )
    return errors


def render_designs(manifest):
    """A deterministic projection of the manifest's design records."""
    if "implementation_design" not in manifest:
        return None
    if validate_designs(manifest):
        return None
    rows = [
        "<!-- Generated from architecture/manifest.yaml; do not edit. -->",
        "# Implementation designs",
        "",
        "Schema validity does not establish implementation or runtime compliance.",
        "",
    ]
    design = manifest["implementation_design"]
    for kind in ("modules", "interfaces", "flows"):
        for identity, record in sorted(design.get(kind, {}).items()):
            rows += [
                f"## {kind}: {identity}",
                "",
                "```json",
                json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True),
                "```",
                "",
            ]
    return "\n".join(rows)
