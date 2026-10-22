#!/bin/sh
set -eu
ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
exec "$ROOT/governed-engineering-skills/Install Governed Engineering Skills.sh" "$@"
