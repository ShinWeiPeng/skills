# Skills

Two independently released skill packages in one repository.

| Package | Purpose | Installation |
| --- | --- | --- |
| [governed-engineering-skills](./governed-engineering-skills/README.md) | Governed engineering workflows for Codex and the existing Claude plugin | Double-click the root Windows installer, or run the root shell installer. |
| doc-coauthoring | Collaborative document writing for Codex and Claude | Added in the following package PR. |

Clone once with `git clone https://github.com/ShinWeiPeng/skills.git`. Each package owns its version, changesets, changelog, Version PR, immutable tags and generated publication branch. Downloading the repository does not install both packages.

Feature PRs record the affected package release intent. After merge, automation creates that package's Version PR. A reviewed Version PR merge publishes only that package. Root navigation documentation does not bump either package. Shared release configuration checks both packages without forcing both to release.

Engineering installation identities and `marketplace-release` remain compatible. The root installers delegate to the engineering package; canonical specifications remain under `specs/`.
