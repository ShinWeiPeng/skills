#!/bin/sh
set -eu

MARKETPLACE=governed-engineering
REPOSITORY=https://github.com/ShinWeiPeng/skills.git
REF=marketplace-release
PLUGIN=governed-engineering-skills
CODEX_VERSION=0.147.0
NON_INTERACTIVE=0
TARGET=
CODEX_WORKDIR=${TMPDIR:-/tmp}
CLAUDE_MARKETPLACE=mattpocock
CLAUDE_SOURCE=ShinWeiPeng/skills
CLAUDE_PLUGIN=mattpocock-skills
CLAUDE_INSTALL_DOCS=https://code.claude.com/docs/en/setup

log() { printf '%s\n' "$*"; }
fail() { log "ERROR: $*" >&2; exit 1; }
run_codex() { (CDPATH='' cd -- "$CODEX_WORKDIR" && codex "$@"); }
run_claude() { (CDPATH='' cd -- "$CODEX_WORKDIR" && claude "$@"); }
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

while [ "$#" -gt 0 ]; do
  case "$1" in
    --non-interactive) NON_INTERACTIVE=1 ;;
    --target=*) TARGET=${1#--target=} ;;
    --target)
      [ "$#" -ge 2 ] || fail "--target requires codex, claude or both."
      shift
      TARGET=$1
      ;;
    *) fail "Unknown option: $1" ;;
  esac
  shift
done

if [ -z "$TARGET" ]; then
  if [ "$NON_INTERACTIVE" -eq 0 ] && [ -t 0 ]; then
    log "Install Governed Engineering Skills for:"
    log "  1) Codex Desktop and CLI"
    log "  2) Claude Code"
    log "  3) Both"
    while [ -z "$TARGET" ]; do
      printf 'Choose 1, 2 or 3 [1]: '
      IFS= read -r answer || answer=
      case "$answer" in
        ''|1) TARGET=codex ;;
        2) TARGET=claude ;;
        3) TARGET=both ;;
        *) log "Enter 1, 2 or 3." ;;
      esac
    done
  else
    TARGET=codex
  fi
fi
case "$TARGET" in
  codex) INSTALL_CODEX=1; INSTALL_CLAUDE=0 ;;
  claude) INSTALL_CODEX=0; INSTALL_CLAUDE=1 ;;
  both) INSTALL_CODEX=1; INSTALL_CLAUDE=1 ;;
  *) fail "Unknown target '$TARGET'. Use codex, claude or both." ;;
esac

[ -r /etc/os-release ] || fail "Unsupported Linux distribution: /etc/os-release is missing."
# shellcheck disable=SC1091
. /etc/os-release
case "${ID:-}" in
  ubuntu|debian)
    PROVIDER=apt
    INSTALL="apt-get install -y git"
    NODE_PACKAGES="nodejs npm"
    ;;
  fedora|rhel|centos|rocky|almalinux)
    PROVIDER=dnf
    INSTALL="dnf install -y git"
    NODE_PACKAGES="nodejs npm"
    ;;
  *) fail "Unsupported Linux distribution '${ID:-unknown}'. Supported: Ubuntu, Debian, Fedora, RHEL." ;;
esac

if [ "$INSTALL_CODEX" -eq 1 ]; then
  INSTALL="$INSTALL $NODE_PACKAGES"
fi
if ! command -v git >/dev/null 2>&1 || {
  [ "$INSTALL_CODEX" -eq 1 ] && { ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; }
}; then
  log "Installing prerequisites with $PROVIDER."
  # The command is selected from the fixed provider contract above, never user input.
  # shellcheck disable=SC2086
  run_root $INSTALL
fi

# Each target runs in a subshell so one failure is reported without hiding the other.
fail_target() { log "ERROR: $*" >&2; exit 1; }

install_codex() (
  set -e
  CURRENT_CODEX_VERSION=
  if command -v codex >/dev/null 2>&1; then
    CURRENT_CODEX_VERSION=$(codex_version)
  fi
  if [ -z "$CURRENT_CODEX_VERSION" ] || ! version_at_least "$CURRENT_CODEX_VERSION" "$CODEX_VERSION"; then
    log "Installing Codex $CODEX_VERSION."
    run_root npm install --global "@openai/codex@$CODEX_VERSION"
  fi
  CURRENT_CODEX_VERSION=$(codex_version)
  [ -n "$CURRENT_CODEX_VERSION" ] || fail_target "Codex is installed but does not report a semantic version."
  version_at_least "$CURRENT_CODEX_VERSION" "$CODEX_VERSION" \
    || fail_target "Codex $CURRENT_CODEX_VERSION is older than required $CODEX_VERSION after installation."

  if ! run_codex login status >/dev/null 2>&1; then
    [ "$NON_INTERACTIVE" -eq 0 ] || fail_target "Codex authentication is required before a non-interactive install."
    run_codex login --device-auth || fail_target "Codex device authentication failed."
  fi

  MARKETPLACE_JSON=$(run_codex plugin marketplace list --json) \
    || fail_target "Codex Marketplace inventory could not be read."
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
  ' "$MARKETPLACE" "$REPOSITORY") || fail_target "Codex Marketplace inventory could not be validated."

  case "$MARKETPLACE_STATE" in
    matching) run_codex plugin marketplace upgrade "$MARKETPLACE" ;;
    missing) run_codex plugin marketplace add "$REPOSITORY" --ref "$REF" \
      --sparse .agents/plugins --sparse plugins/governed-engineering-skills
      ;;
    conflict) fail_target "Marketplace '$MARKETPLACE' conflicts with the required Git Marketplace '$REPOSITORY'. Remove or rename the conflicting source, then rerun." ;;
    *) fail_target "Unexpected Marketplace validation state '$MARKETPLACE_STATE'." ;;
  esac

  run_codex plugin add "$PLUGIN@$MARKETPLACE"
  run_codex plugin list --json | grep -q '"pluginId"[[:space:]]*:[[:space:]]*"governed-engineering-skills@governed-engineering"' \
    || fail_target "Codex did not report the expected installed Plugin."
  log "READY: $PLUGIN is installed from $MARKETPLACE. Start a new Codex task."
)

claude_marketplace_state() {
  # Entries are flat objects with string values; compact them, then isolate each object.
  objects=$(printf '%s' "$1" | tr -d '\n\r\t ' | grep -o '{[^{}]*}' || :)
  named=$(printf '%s\n' "$objects" | grep "\"name\":\"$CLAUDE_MARKETPLACE\"" || :)
  if [ -z "$named" ]; then
    printf 'missing'
  elif [ "$(printf '%s\n' "$named" | wc -l | tr -d ' ')" -eq 1 ] && {
    printf '%s' "$named" | grep -q "\"repo\":\"$CLAUDE_SOURCE\"" ||
      printf '%s' "$named" | grep -Eq "\"url\":\"https://github.com/$CLAUDE_SOURCE(\.git)?\""
  }; then
    printf 'matching'
  else
    printf 'conflict'
  fi
}

install_claude() (
  set -e
  command -v claude >/dev/null 2>&1 \
    || fail_target "Claude Code CLI 'claude' was not found on PATH. Install Claude Code from $CLAUDE_INSTALL_DOCS, open a new terminal, then rerun this installer."
  CLAUDE_MARKETPLACES=$(run_claude plugin marketplace list --json) \
    || fail_target "Claude Code Marketplace inventory could not be read. Update Claude Code, then rerun."
  case "$(claude_marketplace_state "$CLAUDE_MARKETPLACES")" in
    matching) run_claude plugin marketplace update "$CLAUDE_MARKETPLACE" \
      || fail_target "Claude Code could not update Marketplace '$CLAUDE_MARKETPLACE'." ;;
    missing) run_claude plugin marketplace add "$CLAUDE_SOURCE" \
      || fail_target "Claude Code could not add Marketplace '$CLAUDE_SOURCE'." ;;
    *) fail_target "Claude Code marketplace '$CLAUDE_MARKETPLACE' conflicts with the required source '$CLAUDE_SOURCE'. Remove it with 'claude plugin marketplace remove $CLAUDE_MARKETPLACE', then rerun." ;;
  esac
  run_claude plugin install "$CLAUDE_PLUGIN@$CLAUDE_MARKETPLACE" --scope user \
    || fail_target "Claude Code could not install $CLAUDE_PLUGIN@$CLAUDE_MARKETPLACE."
  run_claude plugin list --json | tr -d '\n\r\t ' | grep -q "\"id\":\"$CLAUDE_PLUGIN@$CLAUDE_MARKETPLACE\"" \
    || fail_target "Claude Code did not report the expected installed Plugin."
  log "READY: $CLAUDE_PLUGIN is installed from $CLAUDE_MARKETPLACE. Start a new Claude Code session."
)

# Call each target as a plain command: a `||` context would disable `set -e` inside it.
STATUS=0
set +e
if [ "$INSTALL_CODEX" -eq 1 ]; then
  install_codex
  [ "$?" -eq 0 ] || { STATUS=1; log "ERROR: Codex installation failed." >&2; }
fi
if [ "$INSTALL_CLAUDE" -eq 1 ]; then
  install_claude
  [ "$?" -eq 0 ] || { STATUS=1; log "ERROR: Claude Code installation failed." >&2; }
fi
exit "$STATUS"
