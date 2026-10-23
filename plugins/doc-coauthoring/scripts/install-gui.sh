#!/bin/sh
# Desktop terminal wrapper; keep the installer's result visible without changing it.
set -u

status=0
root=$(CDPATH='' cd "$(dirname "$0")/.." && pwd) || status=$?
if [ "$status" -eq 0 ]; then
    sh "$root/Install Doc Coauthoring.sh" "$@" || status=$?
fi

printf '\n'
if [ "$status" -eq 0 ]; then
    printf '%s\n' 'Installation completed successfully.'
else
    printf '%s\n' 'Installation failed; inspect the diagnostic above.'
fi
printf 'Exit code: %s\n' "$status"
printf '%s' 'Press Enter to close this window...'
IFS= read -r answer || :
exit "$status"
