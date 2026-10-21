#!/bin/bash
# What this does (plain words): draws a LOOK run (jobs_look.py) on the rented machine for both files and brings the pictures back. Use: bash run_look.sh FOLDER_NAME [dial=value ...]
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 -I "$HERE/jobs_look.py" "$@" > /dev/null
F="$HERE/../work/$1"
python3 -I "$HERE/rent_run.py" "$F/jobs_street.json" 2>&1 | tail -1
python3 -I "$HERE/rent_run.py" "$F/jobs_lockout.json" --no-upload --keep 2>&1 | tail -1
