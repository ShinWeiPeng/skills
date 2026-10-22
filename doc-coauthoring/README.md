# Doc Coauthoring

A shared document-writing skill for Codex and Claude, adapted from Anthropic. It guides context gathering, section-by-section refinement, and independent reader testing. See [UPSTREAM.md](UPSTREAM.md) for the pinned source, changes and license basis.

One editable source lives in [skills/doc-coauthoring/SKILL.md](skills/doc-coauthoring/SKILL.md). Codex and Claude load that same workflow; conditional references describe available tools and the manual fallback.

## Direct installation (Windows and Linux)

Python 3.9 or newer is required. No plugin, marketplace, administrator account, or global configuration change is needed.

On Windows, download and extract the repository ZIP (or use a checkout), open `doc-coauthoring/`, and double-click **Install Doc Coauthoring.cmd**. Choose Codex, Claude Code, or both. Keep the accompanying `scripts/` directory next to the launcher.

On a Linux desktop that supports launching desktop entry files, extract the complete package and double-click **Install Doc Coauthoring.desktop**. Keep the accompanying shell launcher and scripts directory in place. If prompted, first mark the desktop entry executable and use the desktop environment's **Allow Launching** or equivalent trust action. The launcher opens a terminal, offers Codex, Claude Code or both, displays the result and original exit code, and waits for Enter before closing. Desktop launch trust and terminal availability depend on the desktop environment; the terminal command remains available for headless systems.

The desktop entry finds its accompanying installer from its own location, including local paths/file URIs containing spaces or Unicode, rather than the current working directory. It uses the same direct installer and version store as the terminal entry; it does not register a plugin or install a GUI toolkit.

On Linux terminals, run from a checkout:

```sh
sh "doc-coauthoring/Install Doc Coauthoring.sh" install --target both
```

After this change reaches the public main branch, installation without a checkout is also available as one command:

```sh
(installer=$(mktemp) && trap 'rm -f "$installer"' EXIT && curl -fsSL "https://raw.githubusercontent.com/ShinWeiPeng/skills/main/doc-coauthoring/Install%20Doc%20Coauthoring.sh" -o "$installer" && sh "$installer" install --target both --version latest)
```

Use `--target codex`, `--target claude`, or `--target both`. The checkout/package launchers use their accompanying local package by default; `--version latest` downloads the latest independently published Doc Coauthoring release. `--version MAJOR.MINOR.PATCH` downloads that package's immutable version tag. Network failures stop installation with a diagnostic.

The personal installation locations are:

- Codex: `~/.agents/skills/doc-coauthoring/`
- Claude Code: `~/.claude/skills/doc-coauthoring/`
- Retained versions and installer records: `~/.doc-coauthoring/`

Each tool exposes one active skill named `doc-coauthoring`; retained versions stay outside skill discovery. The installer includes the shared workflow, platform references, Codex metadata, and upstream/license material. It adjusts the installed upstream-document link without creating another editable workflow source.

### Versions, switching, and recovery

Use Python 3 (on Windows, replace `python3` below with `py -3`):

```sh
python3 doc-coauthoring/scripts/install.py list
python3 doc-coauthoring/scripts/install.py install --target both --version latest
python3 doc-coauthoring/scripts/install.py switch 0.1.0 --target codex
python3 doc-coauthoring/scripts/install.py rollback --target claude
```

The switch example requires that version to appear in `list`. Each tool may activate a different retained version. Rollback selects that tool's previously active version. Reinstalling identical content leaves skill files unchanged, even when only the package version changes. Different content under an already retained version number is rejected.

Modified or unrecognized existing skills are preserved: inspect the reported directory and keep or move your custom copy before retrying. Installation and switching validate all selected targets first and restore earlier activations if a later target fails. Retained versions are not automatically deleted. A concurrent installer lock stops a second run; inspect a leftover `~/.doc-coauthoring/.install.lock` before removing it after an interrupted process.

For an isolated development test, use `--source PATH_TO_PACKAGE --home TEMPORARY_HOME`. The `--home` override contains both the version store and selected tool directories; do not point tests at your real profile.

## Development and versions

Run commands from the repository root:

```sh
python -m pip install -r doc-coauthoring/requirements-release.txt
python doc-coauthoring/scripts/release.py check
python doc-coauthoring/scripts/release.py assemble
python doc-coauthoring/scripts/release.py validate
```

Add a `.changeset/<id>.md` and `.changeset/release-intent.json` for artifact changes. A feature PR does not change the formal version. After merge, automation opens `plugin-release/doc-coauthoring`; maintainers review and merge that Version PR before the immutable `doc-coauthoring@<version>` tag and `doc-coauthoring-release` consumer branch are published. The formal version advances only in that Version PR. The engineering version is independent.

## Optional plugin installation

Copy or link `skills/doc-coauthoring/` into the skill directory supported by your harness, or load this package's plugin manifest. After the first Version PR is merged, the dedicated consumer branch provides a Codex marketplace and a Claude marketplace containing only this package. Root Claude marketplace discovery also exposes this package alongside the engineering suite.

For a local Codex candidate, assemble it first, then run:

```sh
codex plugin marketplace add ./doc-coauthoring/dist/doc-coauthoring-release
codex plugin add doc-coauthoring@doc-coauthoring
```

After the feature PR reaches main, Claude can use the preserved root marketplace:

```text
/plugin marketplace add ShinWeiPeng/skills
/plugin install doc-coauthoring@mattpocock
```

Invoke `$doc-coauthoring` in Codex, or ask Claude to use doc-coauthoring. A useful request includes document type, audience, desired decision and any existing material. When isolated reader tools are unavailable, finish the manual fresh-conversation reader test before calling Reader Testing complete.

## Validation status

Packaging, direct-install CLI behavior and launcher contracts run in CI on Windows and Linux. Linux desktop checks cover desktop-entry syntax, actual GLib parsing, wrapper status and PTY interaction. A real graphical-session desktop launch is separate evidence; shell/PTY success alone does not prove desktop launch. macOS support is outside this change set. Real authoring on a harness requires an installed, available Codex or Claude session; a static manifest check does not establish runtime compatibility. Record platform version, three stages and reader results when performing the acceptance cases in SPEC-0064.
