#!/bin/sh
# Run from a checkout/downloaded package, or bootstrap the Python installer over HTTPS.
set -eu
python_command=
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 &&
       "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
        python_command=$candidate
        break
    fi
done
if [ -z "$python_command" ]; then
    printf '%s\n' 'Python 3.9 or newer is required. Install Python 3 and run this installer again.' >&2
    exit 1
fi
script_directory=$(CDPATH= cd "$(dirname "$0")" 2>/dev/null && pwd)
installer="$script_directory/scripts/install.py"
temporary=
trap 'if [ -n "$temporary" ]; then rm -f -- "$temporary"; fi' EXIT HUP INT TERM
if [ ! -f "$installer" ] || [ ! -f "$0" ]; then
    temporary=$(mktemp)
    url='https://raw.githubusercontent.com/ShinWeiPeng/skills/main/doc-coauthoring/scripts/install.py'
    if command -v curl >/dev/null 2>&1; then
        curl --fail --location --silent --show-error "$url" -o "$temporary"
    elif command -v wget >/dev/null 2>&1; then
        wget -q "$url" -O "$temporary"
    else
        printf '%s\n' 'Install curl or wget, or download and extract the repository ZIP first.' >&2
        exit 1
    fi
    installer=$temporary
fi
"$python_command" "$installer" "$@"
