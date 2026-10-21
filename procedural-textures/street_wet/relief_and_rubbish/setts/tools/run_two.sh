#!/bin/bash
# What this does (plain words): runs two job files one after the other on the rented machine (the street file's job list, then the lockout shot's), by rent_and_render.py.
# Use: bash run_two.sh FOLDER      (FOLDER holds jobs_street.json and jobs_lockout.json)
HERE="$(cd "$(dirname "$0")" && pwd)"
for K in street lockout; do
  [ -f "$1/jobs_$K.json" ] && python3 -I "$HERE/rent_and_render.py" "$1/jobs_$K.json"
done
