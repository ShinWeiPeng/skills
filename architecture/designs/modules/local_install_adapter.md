# local_install_adapter

## Identity

| Field | Value |
|---|---|
| format_version | 1 |
| id | local_install_adapter |
| version | 1 |
| kind | module |

## Design Data

<!-- design-data:1 -->
```yaml
manifest_record:
  id: local_install_adapter
  level: L3+
  role: adapter
  implementation_status: implemented
  paths:
  - plugins/governed-engineering-skills/scripts/install-local.ps1
  - scripts/install-marketplace.ps1
  - scripts/install-marketplace.sh
  - distribution/installer-providers.json
  parent: null
  depends_on: []
  implements_ports:
  - local-install.register
  public_headers: []
  description:
    purpose: Install the governed Plugin through a verified Codex Marketplace CLI.
      Support both the maintainer-only local artifact adapter and native Windows and
      Linux user installers that provision bounded dependencies and consume the generated
      governed Marketplace branch.
    diagram_summaries:
      zh-TW: 註冊本機 Marketplace、安裝外掛並開啟 Codex 詳情頁
    input_ports: []
    output_ports:
    - local-install.result
    emitted_events:
    - local-install.blocked
    owned_state: []
    side_effects:
    - description: Register the repository-local Marketplace in the current user's
        Codex configuration.
    - description: Install the governed Plugin into the current user's Codex cache
        after Marketplace registration succeeds.
    - description: Open the governed Plugin detail page after installation succeeds.
    - description: Install missing Git, Node.js, npm, or Codex dependencies through
        the platform provider declared in distribution/installer-providers.json.
    errors:
    - id: local_installation_failed
      condition: The assembled artifact is incomplete, no PATH or Codex Desktop runtime
        candidate can execute, Marketplace registration or Plugin installation fails,
        or the Desktop Plugin page cannot open.
      event: local-install.blocked
      handling: Return a stable non-zero exit code and write an actionable bounded
        log. If installation fails after registration, leave the local Marketplace
        registered for retry and do not request removal of a prior Plugin install.
    invariants:
    - Accept only the validated assembled Plugin under dist/governed-engineering-skills.
    - Resolve repository paths relative to the user-launched installer.
    - Accept only a local cache identity already produced by Plugin assembly.
    - Probe automatic Codex candidates with a side-effect-free version command before
      Marketplace registration; use an executable PATH candidate before any bundled
      Desktop runtime candidate.
    - Treat an explicitly injected Codex command as authoritative for maintainers
      and isolated contract tests.
    - Never report installation complete before Codex Plugin installation exits successfully.
    - Never require a remote Marketplace branch for local Codex installation.
    - Remote user installation never removes the previously installed Plugin before
      the governed Marketplace and replacement Plugin validate successfully.
    - Preserve Codex versions newer than the tracked minimum and fail closed when
      the installed command remains older after a provisioning attempt.
  entrypoints:
  - path: plugins/governed-engineering-skills/scripts/install-local.ps1
    symbol: install-local
    kind: script
  - path: scripts/install-marketplace.ps1
    symbol: install-marketplace
    kind: script
  - path: scripts/install-marketplace.sh
    symbol: install-marketplace
    kind: script
  public_symbols:
  - path: plugins/governed-engineering-skills/scripts/install-local.ps1
    symbol: install-local
    kind: script
```
