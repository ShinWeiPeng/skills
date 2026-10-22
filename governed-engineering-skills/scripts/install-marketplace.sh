#!/bin/sh
set -eu

MARKETPLACE=governed-engineering
REPOSITORY=https://github.com/ShinWeiPeng/skills.git
REF=marketplace-release
PLUGIN=governed-engineering-skills
CODEX_VERSION=0.147.0
NON_INTERACTIVE=0
CODEX_WORKDIR=${TMPDIR:-/tmp}

log() { printf '%s\n' "$*"; }
fail() { log "ERROR: $*" >&2; exit 1; }
run_codex() { (CDPATH='' cd -- "$CODEX_WORKDIR" && codex "$@"); }
codex_version() {
  run_codex --version 2>/dev/null | sed -n 's/.*\([0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -n 1
}
version_at_least() {
  awk -v actual="$1" -v required="$2" 'BEGIN {
    split(actual, a, "."); split(required, r, ".")
    for (i = 1; i <= 3; i++) {
      if ((a[i] + 0) > (r[i] + 0)) exit 0
      if ((a[i] + 0) < (r[i] + 0)) exit 1
    }
    exit 0
  }'
}
run_root() {
  if [ "$(id -u)" -eq 0 ]; then "$@"; return; fi
  [ "$NON_INTERACTIVE" -eq 0 ] || fail "--non-interactive requires existing root privilege for system packages."
  command -v sudo >/dev/null 2>&1 || fail "sudo is required to install system packages."
  sudo "$@"
}

for arg in "$@"; do
  case "$arg" in
    --non-interactive) NON_INTERACTIVE=1 ;;
    *) fail "Unknown option: $arg" ;;
  esac
done

[ -r /etc/os-release ] || fail "Unsupported Linux distribution: /etc/os-release is missing."
# shellcheck disable=SC1091
. /etc/os-release
case "${ID:-}" in
  ubuntu|debian)
    PROVIDER=apt
    INSTALL="apt-get install -y git nodejs npm"
    ;;
  fedora|rhel|centos|rocky|almalinux)
    PROVIDER=dnf
    INSTALL="dnf install -y git nodejs npm"
    ;;
  *) fail "Unsupported Linux distribution '${ID:-unknown}'. Supported: Ubuntu, Debian, Fedora, RHEL." ;;
esac

if ! command -v git >/dev/null 2>&1 || ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  log "Installing prerequisites with $PROVIDER."
  # The command is selected from the fixed provider contract above, never user input.
  # shellcheck disable=SC2086
  run_root $INSTALL
fi

CURRENT_CODEX_VERSION=
if command -v codex >/dev/null 2>&1; then
  CURRENT_CODEX_VERSION=$(codex_version)
fi
if [ -z "$CURRENT_CODEX_VERSION" ] || ! version_at_least "$CURRENT_CODEX_VERSION" "$CODEX_VERSION"; then
  log "Installing Codex $CODEX_VERSION."
  run_root npm install --global "@openai/codex@$CODEX_VERSION"
fi
CURRENT_CODEX_VERSION=$(codex_version)
[ -n "$CURRENT_CODEX_VERSION" ] || fail "Codex is installed but does not report a semantic version."
version_at_least "$CURRENT_CODEX_VERSION" "$CODEX_VERSION" \
  || fail "Codex $CURRENT_CODEX_VERSION is older than required $CODEX_VERSION after installation."

if ! run_codex login status >/dev/null 2>&1; then
  [ "$NON_INTERACTIVE" -eq 0 ] || fail "Codex authentication is required before a non-interactive install."
  run_codex login --device-auth || fail "Codex device authentication failed."
fi

MARKETPLACE_JSON=$(run_codex plugin marketplace list --json) \
  || fail "Codex Marketplace inventory could not be read."
MARKETPLACE_STATE=$(printf '%s\n' "$MARKETPLACE_JSON" | node -e '
const fs = require("fs");
const marketplace = process.argv[1];
const repository = process.argv[2];
const payload = JSON.parse(fs.readFileSync(0, "utf8"));
const matches = (payload.marketplaces || []).filter(item => item.name === marketplace);
const exact = matches.filter(item => item.marketplaceSource &&
  item.marketplaceSource.sourceType === "git" &&
  item.marketplaceSource.source === repository);
process.stdout.write(matches.length === 0 ? "missing" :
  (matches.length === 1 && exact.length === 1 ? "matching" : "conflict"));
' "$MARKETPLACE" "$REPOSITORY") || fail "Codex Marketplace inventory could not be validated."

case "$MARKETPLACE_STATE" in
  matching) run_codex plugin marketplace upgrade "$MARKETPLACE" ;;
  missing) run_codex plugin marketplace add "$REPOSITORY" --ref "$REF" \
    --sparse .agents/plugins --sparse plugins/governed-engineering-skills
    ;;
  conflict) fail "Marketplace '$MARKETPLACE' conflicts with the required Git Marketplace '$REPOSITORY'. Remove or rename the conflicting source, then rerun." ;;
  *) fail "Unexpected Marketplace validation state '$MARKETPLACE_STATE'." ;;
esac

run_codex plugin add "$PLUGIN@$MARKETPLACE"
run_codex plugin list --json | grep -q '"pluginId"[[:space:]]*:[[:space:]]*"governed-engineering-skills@governed-engineering"' \
  || fail "Codex did not report the expected installed Plugin."
log "READY: $PLUGIN is installed from $MARKETPLACE. Start a new Codex task."
