# Plugin distribution

The repository has one editable Skill source: `skills/engineering` and
`skills/productivity`. The tracked directory at
`plugins/governed-engineering-skills` is only the Plugin shell and intentionally
contains no `skills/` directory.

Assembly removes Claude's `disable-model-invocation: true` frontmatter only from
the OpenAI Plugin copy. The root source keeps Claude's field, while
`agents/openai.yaml` remains the OpenAI invocation-policy authority. This is a
deterministic packaging normalization, not a second editable Skill source.

Build the complete local artifact and personal Marketplace candidate with:

```powershell
python scripts/assemble_plugin.py assemble --marketplace-publication
python scripts/validate_distribution.py
python scripts/assemble_plugin.py validate
```

The command writes ignored outputs at `dist/governed-engineering-skills` and
`dist/marketplace-release`. The publication tree contains only the Marketplace
catalog, complete Plugin package, and `publication-record.json`. Its record is
validated by `distribution/personal-marketplace-publication.schema.json` and is
bound to the Plugin version, source tag and commit, artifact fingerprint, tree
fingerprint, sparse paths, and rollback target.

## User installation

Add the Marketplace separately in ChatGPT Work web and Codex Desktop:

- Source: `https://github.com/ShinWeiPeng/skills.git`
- Git reference: `marketplace-release`
- Sparse paths: `.agents/plugins` and `plugins/governed-engineering-skills`

Then install **Governed Engineering Skills** and start a fresh chat or task.
Installation state is owned independently by each surface; matching repository,
ref, branch commit, Plugin version, and content fingerprint prove that both use
the same release.

The `.agents/plugins/marketplace.json` file on `main` points at a local build and
exists only for deliberate maintainer testing. It is not the supported user
installation channel. The repository ships no one-click local installer.

## Publication and acceptance

The release workflow regenerates and validates the candidate after every local
release gate. Only a stable release with no pending version change may replace
the generated `marketplace-release` branch. Pull-request validation never
publishes it, and the prior branch commit is recorded as the rollback target.

`distribution/personal-marketplace-release-evidence.json` intentionally begins
in `pending` state. Its accepted form is governed by
`distribution/personal-marketplace-release-evidence.schema.json`. After
independently installing the published branch, record
the branch and artifact identity plus four repository-contained evidence files:
one engineering and one productivity invocation from each surface. Release
acceptance fails closed until those hashes and identities match the publication.

`skill-compatibility.json` is the release inventory. A `cross-product` Skill may
be used for the four representative checks. A `codex-only` Skill depends on
repository, terminal, architecture-governance, or device-evidence capabilities
not promised on ChatGPT Work web. A `blocked` entry prevents release until its
dependency is removed or the target surface supplies it.
