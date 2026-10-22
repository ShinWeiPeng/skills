# Doc Coauthoring

A shared document-writing skill for Codex and Claude, adapted from Anthropic. It guides context gathering, section-by-section refinement, and independent reader testing. See [UPSTREAM.md](UPSTREAM.md) for the pinned source, changes and license basis.

One editable source lives in [skills/doc-coauthoring/SKILL.md](skills/doc-coauthoring/SKILL.md). Codex and Claude load that same workflow; conditional references describe available tools and the manual fallback.

## Development and versions

Run commands from the repository root:

```sh
python -m pip install -r doc-coauthoring/requirements-release.txt
python doc-coauthoring/scripts/release.py check
python doc-coauthoring/scripts/release.py assemble
python doc-coauthoring/scripts/release.py validate
```

Add a `.changeset/<id>.md` and `.changeset/release-intent.json` for artifact changes. A feature PR does not change the formal version. After merge, automation opens `plugin-release/doc-coauthoring`; maintainers review and merge that Version PR before the immutable `doc-coauthoring@<version>` tag and `doc-coauthoring-release` consumer branch are published. Initial intent advances the bootstrap 0.0.0 to 0.1.0. The engineering version is independent.

## Installation candidate

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

Packaging and release contracts run in CI on Windows and Linux. Real authoring on a harness requires an installed, available Codex or Claude session; a static manifest check does not establish runtime compatibility. Record platform version, three stages and reader results when performing the acceptance cases in SPEC-0064.
