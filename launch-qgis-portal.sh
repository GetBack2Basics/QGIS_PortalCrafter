#!/usr/bin/env bash
set -euo pipefail

# Force Qt/WebKit/QGIS to a safe POSIX locale so Chinese flag/SVG resources are never looked up.
export LANGUAGE=C
export LC_ALL=C
export LANG=C
export QT_TRANSLATE_NOOP=1

exec qgis "$@"
