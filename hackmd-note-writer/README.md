# HackMD Note Writer

Turn technical discussions and supplied notes into copyable HackMD Markdown with native `[TOC]`, tags and MathJax. One editable skill source lives in [skills/hackmd-note-writer/SKILL.md](skills/hackmd-note-writer/SKILL.md).

## Direct installation (Windows and Linux)

Python 3.9 or newer is required. Download/extract the complete repository or use a checkout, then open `hackmd-note-writer/`. Keep the accompanying `scripts/` and `skills/` directories in place.

- **Windows:** double-click **Install HackMD Note Writer.cmd**. Choose Codex, Claude Code or both. The launcher displays the result and waits before closing.
- **Linux desktop:** double-click **Install HackMD Note Writer.desktop**. On desktops that require it, mark the desktop entry executable and use **Allow Launching** or the equivalent trust action. It opens a terminal, offers the same choices, displays the original exit code and waits for Enter. A terminal and desktop-entry support are required.
- **Linux terminal:** from the repository root, run:

```sh
sh "hackmd-note-writer/Install HackMD Note Writer.sh" install --target both
```

Use `--target codex`, `--target claude` or `--target both`. The accompanying local package is the default source. Installation copies the inner skill directory into personal discovery locations; it does not register a plugin, require administrator rights or edit global configuration.

Personal locations:

| Purpose | Directory |
| --- | --- |
| Codex active skill | `~/.agents/skills/hackmd-note-writer/` |
| Claude Code active skill | `~/.claude/skills/hackmd-note-writer/` |
| Retained versions and installer records | `~/.hackmd-note-writer/` |

Each tool exposes one active skill named `hackmd-note-writer`; retained versions remain outside discovery. Invoke `$hackmd-note-writer` or ask to turn the discussion into a HackMD note.

## Versions, switching and recovery

Run from the repository root. On Windows, replace `python3` with `py -3`:

```sh
python3 hackmd-note-writer/scripts/install.py list
python3 hackmd-note-writer/scripts/install.py switch 0.1.0 --target codex
python3 hackmd-note-writer/scripts/install.py rollback --target claude
```

Switch requires a version already shown by `list`; rollback selects that tool's previously active version. Codex and Claude may use different versions. Installing identical content preserves active files and timestamps, even if only the package version changes. Different content under an already retained version number is rejected.

Modified or unrecognized existing skills are preserved. This includes a same-name skill previously copied manually: inspect and keep or move your custom copy before retrying. Installation and switching validate all selected targets first and restore earlier activations if a later target fails. Retained versions are not deleted automatically. A concurrent installer lock stops a second run; inspect a leftover `~/.hackmd-note-writer/.install.lock` before removing it after an interrupted process.

The CLI also supports `--source PATH_TO_PACKAGE`, `--home TEMPORARY_HOME`, and `--version MAJOR.MINOR.PATCH` or `--version latest`. The version-download interface uses HackMD's own release tag and publication branch. **No HackMD release has been published or registered in this repository's automated release process by this change; use the accompanying local package for installation.** Remote version installation requires an actual future HackMD release; download failures stop with a diagnostic.

## Source layout and validation

```text
hackmd-note-writer/
├── package.json
├── README.md
├── Install HackMD Note Writer.cmd
├── Install HackMD Note Writer.sh
├── Install HackMD Note Writer.desktop
├── scripts/                         # Package installers and terminal wrapper
└── skills/
    └── hackmd-note-writer/          # Skill, metadata, assets and note validator
```

From this package directory, validate raw note content before adding its outer copyable Markdown fence:

```sh
python3 skills/hackmd-note-writer/scripts/validate_hackmd_note.py path/to/note.md
```

For an isolated installation test, use `--source PATH_TO_PACKAGE --home TEMPORARY_HOME`. The `--home` override contains both the version store and selected tool directories; do not point development tests at a real profile.

Run installer and launcher contracts from the repository root:

```sh
python3 -m unittest discover -s .github/tests/flows/plugin-integration/monorepo -p 'test_hackmd_*.py' -v
```

Windows and available POSIX-shell tests verify CLI, files, recovery and wrapper status. Linux desktop syntax, GLib parsing and interactive PTY tests run only when their platform capabilities are available; skipped tests are not passing evidence. A real graphical-session desktop launch remains separate from shell/PTY validation.
