# Plugin distribution

The repository has one editable Skill source: `skills/engineering` and
`skills/productivity`. The tracked `plugins/governed-engineering-skills`
directory is only the Plugin shell and intentionally contains no `skills/`
directory.

Assembly removes Claude's `disable-model-invocation: true` frontmatter only from
the OpenAI Plugin copy. The root source keeps Claude's field, while
`agents/openai.yaml` remains the Codex invocation-policy authority. This is a
deterministic packaging normalization, not a second editable Skill source.

## User installation

Run the native launcher for the current platform from the repository root:

- Windows: double-click `Install Governed Engineering Skills.cmd`.
- Ubuntu, Debian, Fedora, or RHEL with GNOME, KDE Plasma, or Xfce:
  double-click `Install Governed Engineering Skills.desktop`. Honor any
  first-launch trust prompt; the launcher intentionally does not bypass desktop
  security. Its terminal reports the installer exit code and waits for Enter
  before closing.
- Linux terminal: run `./Install\ Governed\ Engineering\ Skills.sh`.

Cinnamon, MATE, and other Freedesktop-compatible desktops are best-effort GUI
targets. The desktop entry uses `Terminal=true` and does not probe or hard-code a
terminal emulator.

The launcher performs this fail-closed sequence:

1. Install missing Git, Node.js/npm, and Codex dependencies using `winget`,
   `apt`, or `dnf` for the supported operating system.
2. Preserve a compatible newer Codex version or install the tracked minimum.
3. Verify Codex authentication, using device authentication only interactively.
4. Add or upgrade the `governed-engineering` Git Marketplace from
   `marketplace-release`.
5. Install and verify
   `governed-engineering-skills@governed-engineering` without first removing an
   older working Plugin.

The provider and minimum-version policy is tracked in
`distribution/installer-providers.json`. A non-interactive Linux run never
prompts for `sudo`; it fails when system privileges are required.

ChatGPT web does not expose Git Marketplace installation for this personal
account and is not supported by this distribution. No Workspace administrator,
web publication record, or cross-surface invocation evidence is required.

## Marketplace publication

Maintainers may also build the deterministic Codex Marketplace candidate:

```powershell
python scripts/assemble_plugin.py assemble --marketplace-publication
python scripts/validate_distribution.py
python scripts/assemble_plugin.py validate
```

This writes ignored outputs at `dist/governed-engineering-skills` and
`dist/marketplace-release`. The optional publication tree contains the
Marketplace catalog, complete Plugin package, and `publication-record.json`.
The release workflow publishes it to `marketplace-release`; it is generated and
never becomes an editable Skill source.

`skill-compatibility.json` is the Codex capability inventory. A
`codex-compatible` entry names any repository, terminal, tracker, device, or
runtime dependencies. A `blocked` entry prevents release until its dependency
is available or removed.
