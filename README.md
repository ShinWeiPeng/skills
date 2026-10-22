# Skills

Clone this repository once to obtain both independently versioned packages:

```text
skills/
├── governed-engineering-skills/  # Engineering workflows and existing history
└── doc-coauthoring/              # Document coauthoring for Codex and Claude
```

```sh
git clone https://github.com/ShinWeiPeng/skills.git
```

| Package | Purpose | Version PR branch | Published consumer branch |
| --- | --- | --- | --- |
| [governed-engineering-skills](governed-engineering-skills/README.md) | Governed engineering workflows | `plugin-release/main` | `marketplace-release` |
| [doc-coauthoring](doc-coauthoring/README.md) | Context gathering, refinement and independent reader testing | `plugin-release/doc-coauthoring` | `doc-coauthoring-release` |

Changes to one package go through its own feature PR, changeset, Version PR, changelog and `<package>@<version>` tag. Both packages may appear in a feature PR; each version change is reviewed independently. Automation publishes only after the respective Version PR is merged. Root navigation documents do not bump either package; shared release or CI changes validate both. See [release-packages.json](release-packages.json) for exact package boundaries.

Engineering installation and development commands live in `governed-engineering-skills/`. Open that folder to use its Windows `.cmd`, Linux `.sh` or Linux `.desktop` installer; assembly and validation use its `scripts/` directory. The legacy root launchers and root `scripts/` aliases have been removed. For installation, assembly and distribution-validation examples in engineering package documentation, including older references to “repository root”, use `governed-engineering-skills/` as the working directory. Plugin version-metadata commands use its `plugins/governed-engineering-skills/` directory. The `governed-engineering` marketplace and consumer branch are unchanged. Shared architecture and specifications remain at the Git root; CI definitions live under `.github/validation/`.

The root Claude marketplace retains its legacy name `mattpocock` and catalogs both packages. Dedicated generated consumer branches each contain only their own package. Follow each package README for installation and validation status. Package manifests and release-state files record their independently reviewed versions.

Each package has its own license/provenance records. The doc workflow derives from the pinned Anthropic example; review [its upstream attribution and license basis](doc-coauthoring/UPSTREAM.md). General document writing uses the doc workflow; engineering changes continue to enter through the engineering router.

## Repository maintenance files

`.github/workflows/` and `.github/scripts/` maintain reviewed releases. `.github/tests/` holds the cross-package release contracts; `.github/validation/` holds their authored validation definitions and platform cases. The root `.agents/plugins/marketplace.json` and `.claude-plugin/marketplace.json` are the Codex and Claude catalogs, not private session state.

Before running repository architecture/layout commands in a fresh checkout:

```sh
python .github/scripts/prepare_validation.py
python -m unittest discover -s .github/tests/flows/plugin-integration/monorepo -p "test_*.py" -v
```

The preparation command creates ignored `validation/` compatibility copies for existing governance tools. It updates only unchanged generated files or adopts byte-identical existing settings; it refuses to overwrite a human edit. Edit `.github/validation/`, then rerun preparation.

Execution state stays in local `spec-governance/`, test and validation reports stay in local `artifacts/`, and generated acceptance projections/copies stay in local `validation/`. These directories are ignored and excluded from new commits; existing local files are retained. Necessary skill sources, release metadata, CI tests/settings, and reviewed specifications remain tracked. Existing published tags and historical Git commits remain unchanged.
