"""Single format owner for flat platform/unit/resource tables and nested YAML."""

import copy
import json

TABLES = {
    "Platform Facts": ("field", "status", "value", "unit", "basis", "reason"),
    "Execution Units": ("id", "kind", "responsibility", "call_environment"),
    "Resource Inventory": ("id", "kind", "quantity", "unit", "owner", "basis"),
}


def encode_tables(kind, data):
    data = copy.deepcopy(data)
    tables = {}
    if kind not in {"platform", "execution"}:
        return data, tables
    value = data.get("value")
    if not isinstance(value, dict):
        raise ValueError("expected domain data value")
    if kind == "platform":
        tables["Platform Facts"] = []
        refs = {}
        for field in ("os", "cpu", "cores", "usable_ram"):
            row = value.pop(field)
            tables["Platform Facts"].append(
                {
                    "field": field,
                    **{key: row.get(key) for key in TABLES["Platform Facts"][1:]},
                }
            )
            refs[field] = row.get("source_refs", [])
        value["fact_sources"] = refs
    else:
        groups = value["groups"]
        tables["Execution Units"] = []
        tables["Resource Inventory"] = []
        if groups["units"]["status"] == "applicable":
            rows = groups["units"]["details"].pop("items")
            for row in rows:
                tables["Execution Units"].append(
                    {key: row[key] for key in TABLES["Execution Units"]}
                )
            groups["units"]["details"]["module_refs"] = {
                row["id"]: row["module_refs"] for row in rows
            }
        if groups["resources"]["status"] == "applicable":
            rows = groups["resources"]["details"].pop("capacities")
            for row in rows:
                tables["Resource Inventory"].append(
                    {key: row[key] for key in TABLES["Resource Inventory"]}
                )
            groups["resources"]["details"]["source_refs"] = {
                row["id"]: row["source_refs"] for row in rows
            }
    return data, tables


def render_tables(tables):
    text = ""
    for name, rows in tables.items():
        columns = TABLES[name]
        text += (
            "\n## "
            + name
            + "\n\n| "
            + " | ".join(columns)
            + " |\n| "
            + " | ".join("---" for _ in columns)
            + " |\n"
        )
        for row in rows:
            text += (
                "| "
                + " | ".join(
                    json.dumps(row[c], ensure_ascii=True, allow_nan=False).replace(
                        "|", "\\u007c"
                    )
                    for c in columns
                )
                + " |\n"
            )
    return text


def decode_tables(kind, data, sections, location):
    expected = (
        {"Platform Facts"}
        if kind == "platform"
        else {"Execution Units", "Resource Inventory"}
        if kind == "execution"
        else set()
    )
    present = set(sections) & set(TABLES)
    if present != expected:
        raise ValueError(location + ": missing or unexpected fixed domain tables")
    parsed = {}
    for name in expected:
        lines = [line for line in sections[name].splitlines()[1:] if line.strip()]
        if len(lines) < 2:
            raise ValueError(location + ":" + name + ": missing table")
        cells = lambda line: [v.strip() for v in line.strip().strip("|").split("|")]
        if cells(lines[0]) != list(TABLES[name]) or any(
            v != "---" for v in cells(lines[1])
        ):
            raise ValueError(location + ":" + name + ": wrong table columns")
        rows = []
        seen = set()
        for number, line in enumerate(lines[2:], 3):
            values = cells(line)
            if len(values) != len(TABLES[name]):
                raise ValueError(f"{location}:{name}:{number}: wrong cell count")
            try:
                row = dict(zip(TABLES[name], map(json.loads, values)))
            except ValueError as error:
                raise ValueError(
                    f"{location}:{name}:{number}: invalid typed cell"
                ) from error
            if any(isinstance(v, (dict, list)) for v in row.values()):
                raise ValueError(
                    location + ":" + name + ": nested values belong in Design Data YAML"
                )
            identity = row[TABLES[name][0]]
            if not isinstance(identity, str) or not identity or identity in seen:
                raise ValueError(location + ":" + name + ": duplicate/invalid row ID")
            seen.add(identity)
            rows.append(row)
        parsed[name] = rows
    if not expected:
        return data
    data = copy.deepcopy(data)
    value = data.get("value")
    if not isinstance(value, dict):
        raise ValueError(location + ": expected domain data value")
    if kind == "platform":
        refs = value.pop("fact_sources", None)
        if (
            not isinstance(refs, dict)
            or set(refs) != {"os", "cpu", "cores", "usable_ram"}
            or {r["field"] for r in parsed["Platform Facts"]} != set(refs)
        ):
            raise ValueError(location + ": incomplete platform facts/sources")
        for row in parsed["Platform Facts"]:
            field = row.pop("field")
            if field in value:
                raise ValueError(
                    location + ": duplicate platform fact source: " + field
                )
            fact = {k: v for k, v in row.items() if v is not None}
            fact["source_refs"] = refs[field]
            value[field] = fact
    else:
        groups = value["groups"]
        for group, table, collection, nested in [
            ("units", "Execution Units", "items", "module_refs"),
            ("resources", "Resource Inventory", "capacities", "source_refs"),
        ]:
            details = groups[group]["details"]
            rows = parsed[table]
            if groups[group]["status"] != "applicable":
                if rows:
                    raise ValueError(location + ": not-applicable inventory has rows")
                continue
            if collection in details:
                raise ValueError(location + ": duplicate inventory source")
            refs = details.pop(nested, None)
            if not isinstance(refs, dict) or set(refs) != {r["id"] for r in rows}:
                raise ValueError(location + ": inventory reference coverage differs")
            for row in rows:
                row[nested] = refs[row["id"]]
            details[collection] = rows
    return data
