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

The engineering installers at this root preserve the existing `governed-engineering` marketplace and consumer branch. Engineering source and development commands now live inside its package; shared architecture, specifications and validation definitions remain at the Git root.

The root Claude marketplace retains its legacy name `mattpocock` and catalogs both packages. Dedicated generated consumer branches each contain only their own package. Follow each package README for installation and validation status. The doc package's initial intent proposes 0.1.0 through a Version PR; source bootstrap metadata remains 0.0.0 until that PR is reviewed.

Each package has its own license/provenance records. The doc workflow derives from the pinned Anthropic example; review [its upstream attribution and license basis](doc-coauthoring/UPSTREAM.md). General document writing uses the doc workflow; engineering changes continue to enter through the engineering router.
