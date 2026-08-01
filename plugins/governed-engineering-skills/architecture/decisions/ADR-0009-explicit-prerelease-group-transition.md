# ADR-0009: Require an explicit prerelease-group transition

- **Status:** accepted
- **Date:** 2026-08-01

## Context

The existing isolated plugin SemVer policy treats beta-to-beta promotion as
another prerelease of the current release group. Consequently, a minor
changeset applied to `0.2.0-beta.1` normally produces `0.2.0-beta.2`, even when
the release owner intends to start the distinct `0.3.0` group.

## Decision

Keep the existing transition as the default. Add an explicit
`new_release_group` policy input to release intents and a corresponding CLI
flag. When it is true, only a major or minor transition into alpha or beta is
allowed, the base version is incremented, and the prerelease sequence starts
at one. A new changeset remains mandatory for the new release group.

Thus `0.2.0-beta.1` plus minor, beta, and `new_release_group: true` produces
`0.3.0-beta.1`; the same request without the flag still produces
`0.2.0-beta.2`.

## Alternatives considered

- Change every beta-to-beta minor promotion to a new group: rejected because it
  silently changes existing release behavior.
- Artificially promote through RC before opening `0.3.0`: rejected because it
  misrepresents release maturity.
- Hand-edit version metadata: rejected because it bypasses transition,
  fingerprint, changelog, and changeset governance.

## Benefits, costs, and tradeoffs

Release intent becomes unambiguous and the current safe default remains
compatible. The additional input must be recorded in release state and covered
by transition and repository-consistency tests.

## Risks and mitigations

Invalid use with patch or stable targets is rejected before mutation. Release
state records the explicit transition so later validation can reconstruct and
verify it. A new release group still requires an unapplied changeset.

## Compatibility and migration impact

Existing release intents without the field behave exactly as before. The
change affects plugin release tooling only and does not affect installed skill
runtime behavior or firmware composition.

## Validation

- Preserve the existing beta-to-beta progression test.
- Prove explicit `0.2.0-beta.1` to `0.3.0-beta.1`.
- Reject invalid patch and stable uses.
- Prove apply-intent archives the previous release group's applied changesets.
- Run version-governance, integration, architecture, fingerprint, and release
  gates.

## Approval

- **Approver:** human project owner
- **Approval date:** 2026-08-01
- **Approval reference:** Codex task approval of option 2 to allow an explicit `0.3.0-beta.1` release group
