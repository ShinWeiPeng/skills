"""One deterministic, source-located projection of a split SPEC document set."""

from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
import yaml
from document_updates import (
    safe_path,
    assert_complete,
    digest,
    document_lock,
    locked_documents,
    reference_bytes,
)
from functools import wraps


def locked_spec(function):
    @wraps(function)
    def run(path, *args, **kwargs):
        path = Path(path)
        if path.parent.name == "specs":
            with document_lock(path.parent.parent):
                return function(path, *args, **kwargs)
        return function(path, *args, **kwargs)

    return run


PARTS = {
    "requirements.md": {"User Stories", "Requirements"},
    "acceptance.md": {"Acceptance Criteria", "Acceptance Mapping"},
    "discussion.md": {
        "Decisions",
        "Discussion Context",
        "Open Decisions",
        "Revision History",
        "Decision History",
        "Pending Discussion",
        "Completeness Gaps",
        "Discussion History",
        "Question Record",
        "Implementation Plan",
    },
}
MAIN = {
    "Problem",
    "Solution",
    "Relationships",
    "Out of Scope",
    "Routing/Gates",
    "Current Specification",
}
MARKER = "<!-- document-bundle:1 -->"


class DocumentError(ValueError):
    pass


def strict_yaml(text, location):
    class Loader(yaml.SafeLoader):
        pass

    def mapping(loader, node):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node)
            if not isinstance(key, str) or key in result:
                raise DocumentError(
                    f"{location}:{key_node.start_mark.line + 1}: duplicate or non-text key"
                )
            result[key] = loader.construct_object(value_node)
        return result

    Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    try:
        return yaml.load(text, Loader=Loader)
    except yaml.YAMLError as error:
        raise DocumentError(f"{location}: {error}") from error


def _sections(text, location):
    # SPEC audit is retained verbatim with the discussion source.
    matches = list(re.finditer(r"(?m)^## ([^\n]+)\n", text))
    sections = {}
    for index, match in enumerate(matches):
        name = match.group(1).strip()
        if name in sections:
            raise DocumentError(
                f"{location}:{text[: match.start()].count(chr(10)) + 1}: duplicate section {name}"
            )
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections[name] = text[match.start() : end]
    prefix = text[: matches[0].start()] if matches else text
    return prefix, sections


def split_spec(text, canonical_relative, *, design_refs=None):
    """Prepare create/update content. No filesystem effects and no authority inference."""
    path = Path(canonical_relative)
    if path.parent.as_posix() != "specs" or not re.fullmatch(
        r"SPEC-\d{4}-.+\.md", path.name
    ):
        raise DocumentError("invalid canonical SPEC path")
    prefix, sections = _sections(text, canonical_relative)
    unknown = set(sections) - MAIN - set().union(*PARTS.values())
    if unknown:
        raise DocumentError("undefined SPEC sections: " + ", ".join(sorted(unknown)))
    directory = path.name[:9]
    files = {}
    order = []
    parts = {key: "" for key in PARTS}
    main = prefix
    for name, content in sections.items():
        owner = next((p for p, names in PARTS.items() if name in names), None)
        if owner:
            parts[owner] += content
            relative = f"specs/{directory}/{owner}"
        else:
            main += content
            relative = canonical_relative
        order.append({"section": name, "path": relative})
    if design_refs:
        binding = digest(
            json.dumps(design_refs, sort_keys=True, separators=(",", ":")).encode()
        )
        marker = "<!-- fixed-design-collection:" + binding + " -->"
        if marker not in main:
            main = re.sub(
                r"<!-- fixed-design-collection:[a-f0-9]{64} -->", marker, main
            )
            if marker not in main:
                main = main.replace(
                    "## Solution\n", "## Solution\n\n" + marker + "\n", 1
                )
    # A marker preceding the metadata leaves the canonical projection unchanged.
    navigation = "<!-- document-navigation:start -->\n"
    navigation += (
        " | ".join(
            f"[{label}]({directory}/{name})"
            for label, name in [
                ("需求", "requirements.md"),
                ("驗收", "acceptance.md"),
                ("討論與決策", "discussion.md"),
                ("固定設計引用", "references.yaml"),
            ]
        )
        + "\n<!-- document-navigation:end -->\n"
    )
    files[canonical_relative] = MARKER + "\n" + navigation + main
    for name, content in parts.items():
        files[f"specs/{directory}/{name}"] = content
    refs = {
        "format_version": 1,
        "canonical": canonical_relative,
        "sections": order,
        "designs": design_refs or [],
    }
    files[f"specs/{directory}/references.yaml"] = yaml.safe_dump(
        refs, sort_keys=False, allow_unicode=True
    )
    return files


def _resolve_design(root, row):
    if (
        not isinstance(row, dict)
        or set(row) != {"id", "version", "path", "sha256"}
        or not isinstance(row.get("id"), str)
        or not row["id"]
        or type(row.get("version")) is not int
        or row["version"] < 1
        or not isinstance(row.get("sha256"), str)
        or not re.fullmatch("[a-f0-9]{64}", row["sha256"])
    ):
        raise DocumentError("invalid fixed design reference")
    if not isinstance(row.get("path"), str) or not row["path"].startswith(
        ("architecture/designs/", "architecture/history/", "specs/")
    ):
        raise DocumentError("design reference outside maintained scope")
    path = safe_path(root, row["path"])
    from document_updates import reference_bytes

    try:
        actual = reference_bytes(path)
    except FileNotFoundError:
        actual = None
    if actual is None or digest(actual) != row["sha256"]:
        suffix = ".yaml" if row["id"] == "DESIGN-COLLECTION" else ".md"
        archived = safe_path(
            root,
            f"architecture/history/designs/{row['id']}/v{row['version']}-{row['sha256']}{suffix}",
        )
        if archived.exists():
            path = archived
            actual = reference_bytes(path)
    if actual is None or digest(actual) != row["sha256"]:
        raise DocumentError(row["path"] + ": missing design or content hash mismatch")
    design = (
        strict_yaml(actual.decode("utf-8"), row["path"])
        if row["id"] == "DESIGN-COLLECTION"
        else parse_design(actual.decode("utf-8"), row["path"])
    )
    if design.get("id") != row["id"] or design.get("version") != row["version"]:
        raise DocumentError(
            row["path"] + ": design ID/version differs from fixed reference"
        )
    if row["id"] == "DESIGN-COLLECTION" and (
        set(design) != {"format_version", "id", "version", "documents"}
        or design["format_version"] != 1
        or not isinstance(design["documents"], list)
    ):
        raise DocumentError(row["path"] + ": unsupported collection index")
    return path


@locked_spec
def read_spec_document(path, *, preserve_newlines=False):
    """All callers share this reader; flat sources are input to migration projection."""
    path = Path(path)
    text = reference_bytes(path).decode("utf-8").replace("\r\n", "\n")
    if path.parent.name != "specs" or not re.fullmatch(r"SPEC-\d{4}-.+\.md", path.name):
        return text
    text = reference_bytes(path).decode("utf-8")
    if MARKER not in text:
        return text if preserve_newlines else text.replace("\r\n", "\n")
    if not text.startswith(MARKER + "\n") or path.parent.name != "specs":
        raise DocumentError(f"{path}: invalid bundle marker or canonical location")
    root = path.parent.parent.resolve()
    relative = "specs/" + path.name
    reference = f"specs/{path.name[:9]}/references.yaml"
    ref_path = safe_path(root, reference)
    refs = strict_yaml(reference_bytes(ref_path).decode("utf-8"), reference)
    if (
        not isinstance(refs, dict)
        or set(refs) != {"format_version", "canonical", "sections", "designs"}
        or refs["format_version"] != 1
        or refs["canonical"] != relative
    ):
        raise DocumentError(
            f"{reference}: unsupported or invalid document-set contract"
        )
    if not isinstance(refs["sections"], list) or not isinstance(refs["designs"], list):
        raise DocumentError(f"{reference}: sections and designs must be lists")
    all_paths = {relative, reference}
    all_paths.update(
        row.get("path", "") for row in refs["sections"] if isinstance(row, dict)
    )
    all_paths.update(
        row.get("path", "") for row in refs["designs"] if isinstance(row, dict)
    )
    assert_complete(root, all_paths)
    main_text = text[len(MARKER) + 1 :]
    if main_text.startswith("<!-- document-navigation:start -->"):
        match = re.match(
            r"<!-- document-navigation:start -->\n[^\n]*\n<!-- document-navigation:end -->\n",
            main_text,
        )
        if not match:
            raise DocumentError("invalid generated document navigation")
        main_text = main_text[match.end() :]
    prefix, main = _sections(main_text, relative)
    owners = {relative: main}
    seen = set()
    result = prefix
    for row in refs["sections"]:
        if not isinstance(row, dict) or set(row) != {"section", "path"}:
            raise DocumentError(f"{reference}: invalid section reference")
        name, target = row["section"], row["path"]
        expected = next(
            (
                f"specs/{path.name[:9]}/{p}"
                for p, names in PARTS.items()
                if name in names
            ),
            relative if name in MAIN else None,
        )
        if target != expected or name in seen:
            raise DocumentError(
                f"{reference}: duplicate, undefined or misplaced section {name}"
            )
        seen.add(name)
        if target not in owners:
            source = safe_path(root, target)
            try:
                raw = reference_bytes(source)
            except FileNotFoundError as error:
                raise DocumentError(f"{target}: missing SPEC part") from error
            part_prefix, content = _sections(raw.decode("utf-8"), target)
            if part_prefix.strip():
                raise DocumentError(
                    f"{target}: undeclared content outside fixed sections"
                )
            owners[target] = content
        if name not in owners[target]:
            raise DocumentError(f"{target}: missing section {name}")
        result += owners[target][name]
    if set().union(*(set(value) for value in owners.values())) != seen:
        raise DocumentError(f"{reference}: unreferenced sections")
    markers = re.findall(r"<!-- fixed-design-collection:([a-f0-9]{64}) -->", result)
    expected = (
        digest(
            json.dumps(refs["designs"], sort_keys=True, separators=(",", ":")).encode()
        )
        if refs["designs"]
        else None
    )
    if markers != ([expected] if expected else []):
        raise DocumentError(
            str(reference)
            + ": design collection differs from the confirmed authored binding"
        )
    identities = set()
    for row in refs["designs"]:
        _resolve_design(root, row)
        if row["id"] in identities:
            raise DocumentError(f"{reference}: duplicate design ID")
        identities.add(row["id"])
    return result if preserve_newlines else result.replace("\r\n", "\n")


def read_spec_bytes(path):
    path = Path(path)
    data = path.read_bytes()
    return (
        read_spec_document(path, preserve_newlines=True).encode("utf-8")
        if data.startswith(MARKER.encode())
        else data
    )


@locked_spec
def spec_hash(path):
    """Bind the projection plus fixed referenced designs, excluding unrelated files."""
    path = Path(path)
    data = read_spec_bytes(path)
    if reference_bytes(path).startswith(MARKER.encode()):
        reference = path.parent / path.name[:9] / "references.yaml"
        refs = strict_yaml(reference_bytes(reference).decode("utf-8"), str(reference))
        if refs["designs"]:
            data += json.dumps(
                refs["designs"], sort_keys=True, separators=(",", ":")
            ).encode()
    return digest(data)


@locked_spec
def design_binding(path):
    path = Path(path)
    if not reference_bytes(path).startswith(MARKER.encode()):
        return None
    read_spec_document(path)
    refs = strict_yaml(
        reference_bytes(path.parent / path.name[:9] / "references.yaml").decode(
            "utf-8"
        ),
        str(path),
    )
    return (
        digest(
            json.dumps(refs["designs"], sort_keys=True, separators=(",", ":")).encode()
        )
        if refs["designs"]
        else None
    )


def parse_design(text, location):
    """Flat metadata belongs in one table; nested data belongs in one named block."""
    prefix, sections = _sections(text, location)
    from design_table_format import TABLES, decode_tables

    if not {"Identity", "Design Data"} <= set(sections) or set(sections) - {
        "Identity",
        "Design Data",
    } - set(TABLES):
        raise DocumentError(f"{location}: expected Identity and Design Data sections")
    rows = {}
    for line in sections["Identity"].splitlines()[1:]:
        if not line.strip():
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells == ["Field", "Value"] or all(
            re.fullmatch(r":?-+:?", c) for c in cells
        ):
            continue
        if len(cells) != 2 or cells[0] in rows:
            raise DocumentError(f"{location}: invalid or duplicate identity row")
        rows[cells[0]] = cells[1]
    if (
        set(rows) != {"format_version", "id", "version", "kind"}
        or rows["format_version"] != "1"
        or not re.fullmatch(r"[1-9]\d*", rows["version"])
        or rows["kind"]
        not in {"platform", "execution", "module", "interface", "flow", "catalog"}
    ):
        raise DocumentError(f"{location}: invalid design identity/version/kind")
    match = re.fullmatch(
        r"## Design Data\n\s*<!-- design-data:1 -->\n```yaml\n(.*?)\n```\s*",
        sections["Design Data"],
        re.S,
    )
    if not match:
        raise DocumentError(
            f"{location}: expected exactly one designated design-data YAML block"
        )
    data = strict_yaml(match.group(1), location + ":Design Data")
    if not isinstance(data, dict) or set(data) & set(rows):
        raise DocumentError(
            f"{location}: data must be a mapping without duplicate identity fields"
        )
    try:
        json.dumps(data, allow_nan=False, sort_keys=True)
    except (ValueError, TypeError) as error:
        raise DocumentError(
            f"{location}: quote dates, use text keys and finite numbers"
        ) from error
    data = decode_tables(rows["kind"], data, sections, location)
    json.dumps(data, allow_nan=False)
    return {
        "format_version": 1,
        "id": rows["id"],
        "version": int(rows["version"]),
        "kind": rows["kind"],
        "data": data,
    }


def render_design(identity, version, kind, data):
    from design_table_format import encode_tables, render_tables

    data, tables = encode_tables(kind, data)
    text = f"# {identity}\n\n## Identity\n\n| Field | Value |\n|---|---|\n| format_version | 1 |\n| id | {identity} |\n| version | {version} |\n| kind | {kind} |\n\n## Design Data\n\n<!-- design-data:1 -->\n```yaml\n"
    text += (
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True).rstrip() + "\n```\n"
    )
    text += render_tables(tables)
    parse_design(text, identity)
    return text


@locked_documents
def pin_design_references(root, refs):
    """Return immutable snapshots and exact references for owner-managed confirmation."""
    files = {}
    pinned = []
    for row in refs:
        path = _resolve_design(root, row)
        suffix = ".yaml" if row["id"] == "DESIGN-COLLECTION" else ".md"
        history = f"architecture/history/designs/{row['id']}/v{row['version']}-{row['sha256']}{suffix}"
        target = safe_path(root, history)
        data = path.read_bytes()
        if target.exists() and target.read_bytes() != data:
            raise DocumentError("immutable confirmed design conflict")
        files[history] = data.decode("utf-8")
        pinned.append(row | {"path": history})
    return files, pinned


@locked_documents
def assert_current_designs(root, spec_path):
    """Historical reads remain valid; current product writes require current dependent designs."""
    root = Path(root).resolve()
    path = Path(spec_path)
    if not reference_bytes(path).startswith(MARKER.encode()):
        return
    read_spec_document(path)
    refs = strict_yaml(
        reference_bytes(path.parent / path.name[:9] / "references.yaml").decode(),
        str(path),
    )["designs"]
    expected = [
        r
        for r in refs
        if not r["id"].startswith(("BASE-", "REMOVE-"))
        and r["id"] != "DESIGN-COLLECTION"
    ]
    if not expected:
        return
    index = safe_path(root, "architecture/designs/index.yaml")
    if not index.is_file():
        raise DocumentError("current design sources require migration")
    records = {}
    for relative in strict_yaml(index.read_text(encoding="utf-8"), str(index))[
        "documents"
    ]:
        source = safe_path(root, relative)
        record = parse_design(source.read_text(encoding="utf-8"), relative)
        if record["id"] in records:
            raise DocumentError("duplicate current design identity")
        records[record["id"]] = (record["version"], digest(source.read_bytes()))
    for row in expected:
        if records.get(row["id"]) != (row["version"], row["sha256"]):
            raise DocumentError(
                "current design differs from confirmed dependency: "
                + row["id"]
                + "; reconcile the affected design before product writes"
            )
