#!/usr/bin/env python3
"""Validate raw HackMD notes using native [TOC] and ###### tags: syntax."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TAG_LINE_RE = re.compile(r"^######\s+tags:\s*(.*?)\s*$")
INLINE_TAGS_RE = re.compile(r"(?:`[^`\r\n]+`\s*)+")
MANUAL_TOC_LINK_RE = re.compile(r"^\s*[-*+]\s+\[[^\]]+\]\(#[^)]+\)\s*$")


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    line: int


def reject_outer_fence(text: str, errors: list[str]) -> str:
    lines = text.splitlines()

    first = next((line.strip() for line in lines if line.strip()), "")
    last = next((line.strip() for line in reversed(lines) if line.strip()), "")

    if re.fullmatch(r"`{3,}(?:markdown|md|text)?", first, re.IGNORECASE):
        errors.append(
            "Remove the opening outer code fence. The note must begin directly with `# Document title`."
        )

    if re.fullmatch(r"`{3,}", last):
        errors.append(
            "Remove the closing outer code fence. The native tags line must be the final content."
        )

    return text


def parse_visible_lines(
    body: str,
    errors: list[str],
) -> tuple[list[Heading], list[tuple[int, str]]]:
    headings: list[Heading] = []
    visible_lines: list[tuple[int, str]] = []
    in_fence = False
    fence_token = ""

    for line_no, line in enumerate(body.splitlines(), start=1):
        stripped = line.strip()
        fence_match = re.match(r"^(`{3,})(.*)$", stripped)

        if fence_match:
            token = fence_match.group(1)
            suffix = fence_match.group(2).strip()

            if not in_fence:
                in_fence = True
                fence_token = token
                if len(token) != 3:
                    errors.append(
                        f"Line {line_no}: internal code fences must use exactly three backticks."
                    )
                if not suffix:
                    errors.append(
                        f"Line {line_no}: opening code fence should include a language label."
                    )
            elif stripped == fence_token:
                in_fence = False
                fence_token = ""
            continue

        if in_fence:
            continue

        visible_lines.append((line_no, line))

        if TAG_LINE_RE.fullmatch(stripped):
            continue

        match = HEADING_RE.match(line)
        if match:
            headings.append(
                Heading(
                    level=len(match.group(1)),
                    text=match.group(2).strip(),
                    line=line_no,
                )
            )

    if in_fence:
        errors.append("An internal code fence is not closed.")

    return headings, visible_lines


def non_empty_visible_lines(
    visible_lines: list[tuple[int, str]],
) -> list[tuple[int, str]]:
    return [
        (line_no, line.strip())
        for line_no, line in visible_lines
        if line.strip()
    ]


def validate_title_and_headings(
    headings: list[Heading],
    visible_lines: list[tuple[int, str]],
    errors: list[str],
) -> None:
    h1s = [heading for heading in headings if heading.level == 1]

    if len(h1s) != 1:
        errors.append(f"Expected exactly one level-1 heading, found {len(h1s)}.")

    visible = non_empty_visible_lines(visible_lines)
    if not visible:
        errors.append("The note contains no visible Markdown content.")
        return

    first_line_no, first_text = visible[0]
    if not first_text.startswith("# ") or first_text.startswith("## "):
        errors.append(
            f"Line {first_line_no}: the first visible content line must be the level-1 title."
        )

    for heading in headings:
        normalized = heading.text.strip().upper()
        if normalized == "TOC":
            errors.append(
                f"Line {heading.line}: do not create a TOC heading; use [TOC]."
            )
        if normalized == "TAG":
            errors.append(
                f"Line {heading.line}: do not create a TAG heading; use ###### tags:."
            )

    previous: Heading | None = None
    for heading in headings:
        if previous and heading.level > previous.level + 1:
            errors.append(
                f"Line {heading.line}: heading level jumps from H{previous.level} "
                f"to H{heading.level}."
            )
        previous = heading


def validate_native_toc(
    headings: list[Heading],
    visible_lines: list[tuple[int, str]],
    errors: list[str],
) -> None:
    visible = non_empty_visible_lines(visible_lines)
    toc_lines = [(line_no, text) for line_no, text in visible if text == "[TOC]"]

    if len(toc_lines) != 1:
        errors.append(
            f"Expected exactly one native [TOC] directive, found {len(toc_lines)}."
        )

    if len(visible) >= 2 and visible[1][1] != "[TOC]":
        errors.append(
            f"Line {visible[1][0]}: [TOC] must be the first non-empty content line after the title."
        )
    elif len(visible) < 2:
        errors.append("[TOC] is missing after the title.")

    if not toc_lines:
        return

    toc_line_no = toc_lines[0][0]
    first_major_line = min(
        (heading.line for heading in headings if heading.level == 2),
        default=10**9,
    )

    for line_no, line in visible_lines:
        if toc_line_no < line_no < first_major_line:
            if MANUAL_TOC_LINK_RE.fullmatch(line.strip()):
                errors.append(
                    f"Line {line_no}: remove the manual TOC entry; HackMD builds it from [TOC]."
                )


def validate_native_tags(
    visible_lines: list[tuple[int, str]],
    errors: list[str],
) -> None:
    visible = non_empty_visible_lines(visible_lines)
    tag_lines: list[tuple[int, str, str]] = []

    for line_no, text in visible:
        match = TAG_LINE_RE.fullmatch(text)
        if match:
            tag_lines.append((line_no, text, match.group(1)))

    if len(tag_lines) != 1:
        errors.append(
            f"Expected exactly one native `###### tags:` line, found {len(tag_lines)}."
        )
        return

    line_no, _, payload = tag_lines[0]

    if visible[-1][0] != line_no:
        errors.append(
            f"Line {line_no}: the native tags line must be the final non-empty content line."
        )

    if not payload:
        errors.append(f"Line {line_no}: add at least one tag.")
        return

    if not INLINE_TAGS_RE.fullmatch(payload):
        errors.append(
            f"Line {line_no}: every tag must use inline-code syntax, "
            "for example `HackMD` `Skill`."
        )
        return

    tags = re.findall(r"`([^`\r\n]+)`", payload)
    for tag in tags:
        normalized = tag.strip()
        if not normalized:
            errors.append(f"Line {line_no}: empty tags are not allowed.")
        if normalized.startswith("#"):
            errors.append(
                f"Line {line_no}: tag `{tag}` must not start with #; "
                f"use `{normalized.lstrip('#')}`."
            )


def validate(path: Path) -> list[str]:
    errors: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [f"Unable to read UTF-8 file: {exc}"]

    body = reject_outer_fence(text, errors)
    headings, visible_lines = parse_visible_lines(body, errors)

    validate_title_and_headings(headings, visible_lines, errors)
    validate_native_toc(headings, visible_lines, errors)
    validate_native_tags(visible_lines, errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate raw HackMD Markdown using native [TOC] and "
            "###### tags: syntax without an outer code fence."
        )
    )
    parser.add_argument("note", type=Path, help="Path to the Markdown note.")
    args = parser.parse_args()

    errors = validate(args.note)

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
