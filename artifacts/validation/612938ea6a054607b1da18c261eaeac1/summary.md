# SPEC-0028 implementation evidence

**Overall acceptance: BLOCKED.** Implementation and Windows checks are recorded below; the SPEC remains confirmed, not implemented.

530 Python tests passed on Windows / Python 3.12.14. Both Windows installer/access suites passed.

## Completed checks

- Whole-project layout
- Architecture development and release gates
- Generated architecture views
- Single-source assembly (287 files)
- Distribution validator
- Assembled integration validation
- Windows installer and artifact-access contracts
- 39-file formatter check
- 90 migration destinations, 13 unchanged legacy files, 15 support relocations

## Outstanding validation

- Linux host runtime is unavailable; Linux execution has not been demonstrated.
- The complete 38-test distribution suite remains failed (2 failures, 8 errors): the index-free snapshot has no Git checkout for Git-index/rehearsal cases; temporary Git initialization failed on this host; Linux shell entrypoints cannot execute as Win32 programs. No source-repository staging, commit or publication was performed to work around this.

## Review and limits

Standards and Spec reviewers confirmed closure of the concrete admission, immutable-write, race, stale-source, metadata-binding and subtree-pruning findings. This is not a full SPEC acceptance PASS.

- No device/hardware evidence claimed.
- Runtime case isolation and unsupported-language release isolation are not proved by layout inspection. Required unsupported capabilities remain BLOCKED.
- No whole-tool-trace compliance PASS is asserted; migrations/generator operations used their authorized native entrypoints.

- Gitignore/attributes unchanged
- env_sensing was not modified
- No automatic retention deletion
- Historical evidence was not rebound as a new run

## Fixed run references

| Scenario | Outcome | Selected | Manifest |
|---|---|---|---|
| architecture | PASS | True | [manifest](../../tests/bd9e0c82cafa4056baa6c0a0c2ca590e/manifest.json) |
| device-tools | PASS | True | [manifest](../../tests/8a115df4b3ac4d208c58509c0b505e0c/manifest.json) |
| verification-ladder | PASS | True | [manifest](../../tests/afa866290d274bcd9542312ecda4c538/manifest.json) |
| layout-contracts | PASS | True | [manifest](../../tests/c8a11000128c429a87295b1346401fd9/manifest.json) |
| run-storage-contracts | PASS | True | [manifest](../../tests/61d8a101301e4498b4411fc3d3d6f052/manifest.json) |
| clean-plugin-contracts | PASS | True | [manifest](../../tests/120007170b024f0c8321613a2b282298/manifest.json) |
| proposal-contracts | PASS | True | [manifest](../../tests/91b720623da64c4c90f5a660e64fa537/manifest.json) |
| explanation-contracts | PASS | True | [manifest](../../tests/0b2e0bec4bb7484a84ead1aa4950dc94/manifest.json) |
| diagnosis-contracts | PASS | True | [manifest](../../tests/5a86d63629c2469981ed6f2880f844f5/manifest.json) |
| distribution-validation | PASS | True | [manifest](../../tests/18fa9e9dcfef4004b2b70cc45e454600/manifest.json) |
| plugin-integration | PASS | True | [manifest](../../tests/edf1de80c89142a389d0cffad88534a6/manifest.json) |
| architecture-development | PASS | True | [manifest](../../tests/e33f9d59fe4c480bb15cd6f3d3b6f65f/manifest.json) |
| architecture-release | PASS | True | [manifest](../../tests/530a7fadb3a24aa39189f0ed2c9904bd/manifest.json) |
| formatting-migration-policy | PASS | True | [manifest](../../tests/0810e0edb4334b57b1bede86163693e0/manifest.json) |
| test_windows_artifact_access-host-env | PASS | True | [manifest](../../tests/1e3f0137c0f047cda52b5813767efd3d/manifest.json) |
| test_install_local-host-env | PASS | True | [manifest](../../tests/e0727f5be7df4be99ba3e0885eec05a3/manifest.json) |
| plugin-integration | FAIL | False | [manifest](../../tests/61097fc37a474d58a74a487993a5cb12/manifest.json) |
| plugin-contracts | FAIL | False | [manifest](../../tests/acbd56a459e1494caf68177d14dea8fa/manifest.json) |
| clean-distribution-contracts | FAIL | False | [manifest](../../tests/4d526184173a4194a779a19cca2b5461/manifest.json) |
| test_install_local | FAIL | False | [manifest](../../tests/936dd6b0db3e47ab93e46978d34e95cb/manifest.json) |
| test_windows_artifact_access | FAIL | False | [manifest](../../tests/db1be9aa324442129ecab7a6ae529a54/manifest.json) |
