#!/bin/bash
# What this does (plain words): writes the lighting test set's job files (jobs_testset.py) and runs both of them on the rented machine, one after the other (the street copy, then the lockout shot file),
# measures every picture and brings the folder back. Use: bash run_testset.sh FOLDER_NAME [dial=value ...]
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 -I "$HERE/jobs_testset.py" "$@" > /dev/null
F="$HERE/../work/$1"
python3 -I "$HERE/rent_run.py" "$F/jobs_street.json" 2>&1 | tail -1
python3 -I "$HERE/rent_run.py" "$F/jobs_lockout.json" --no-upload --keep 2>&1 | tail -1
