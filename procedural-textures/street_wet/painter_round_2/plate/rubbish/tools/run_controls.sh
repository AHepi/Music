#!/bin/bash
# What this does (plain words): runs the control pictures (jobs_controls.py) on both files on the rented machine. Use: bash run_controls.sh FOLDER_NAME
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 -I "$HERE/jobs_controls.py" "$@" > /dev/null
F="$HERE/../work/$1"
python3 -I "$HERE/rent_run.py" "$F/jobs_street.json" 2>&1 | tail -1
python3 -I "$HERE/rent_run.py" "$F/jobs_lockout.json" --no-upload --keep 2>&1 | tail -1
