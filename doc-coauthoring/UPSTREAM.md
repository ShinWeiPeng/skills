# Upstream and adaptation

- Repository: https://github.com/anthropics/skills
- Fixed commit: `00756142ab04c82a447693cf373c4e0c554d1005`
- Source: [skills/doc-coauthoring/SKILL.md](https://github.com/anthropics/skills/blob/00756142ab04c82a447693cf373c4e0c554d1005/skills/doc-coauthoring/SKILL.md)
- Upstream Git blob SHA-1: `a5a69839ef4a161131d80b6daef10037a9686f4a`
- Raw source SHA-256: `2e47d78846faeea4a56e9809c52700087a15a2155a3f293a3efbaded81398ef4`

The source blob was checked against upstream main on 2026-10-22 and is unchanged. Retrieve the fixed raw file and verify its Git blob and SHA-256 before comparing future updates. Do not edit a second vendored workflow here.

## Changes

Retain Context Gathering, Refinement & Structure, and Reader Testing; keep freeform and manual-reader fallbacks. Generalize assistant and tool names, add conditional Codex/Claude capabilities, require a reader without inherited context, avoid unsupported image/tool claims, reuse supplied context, and keep engineering governance responsible for engineering changes. Add only packaging, versioning and provenance around the shared workflow.

## License basis

The pinned [upstream README](https://github.com/anthropics/skills/blob/00756142ab04c82a447693cf373c4e0c554d1005/README.md) describes open-source examples as Apache 2.0 and identifies the distinct source-available processing skills (`docx`, `pdf`, `pptx`, `xlsx`). The pinned [marketplace](https://github.com/anthropics/skills/blob/00756142ab04c82a447693cf373c4e0c554d1005/.claude-plugin/marketplace.json) puts `doc-coauthoring` in `example-skills`, outside that processing group. Apache-2.0 for this example is an inference from these two upstream declarations: the doc-coauthoring directory has no separate license file or frontmatter license identifier. Preserve this qualification for maintainer review; the engineering package's MIT license is not the basis for this import.

`LICENSE` reproduces the standard Apache 2.0 terms; `NOTICE` attributes the upstream and marks local changes. It does not create or expand any grant from the upstream author.
