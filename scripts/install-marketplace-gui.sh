#!/bin/sh
set -u

ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
status=0
"$ROOT/Install Governed Engineering Skills.sh" "$@" || status=$?

printf '\n'
if [ "$status" -eq 0 ]; then
  printf 'Installation completed successfully.\n'
else
  printf 'Installation failed.\n'
fi
printf 'Exit code: %s\n' "$status"
printf 'Press Enter to close this window...'
IFS= read -r _ || :

exit "$status"
