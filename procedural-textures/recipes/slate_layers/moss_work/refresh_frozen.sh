#!/bin/bash
# What this does (plain words): copies the CURRENT moss.py into the frozen copy (moss_work/frozen/layers/moss.py), so the tests on the frozen copy use the latest MOSS and the
# frozen version of every other layer. Use: moss_work/refresh_frozen.sh
HERE="$(cd "$(dirname "$0")" && pwd)"
cp "$HERE/../layers/moss.py" "$HERE/frozen/layers/moss.py"
echo "copied moss.py into $HERE/frozen/layers"
