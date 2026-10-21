#!/bin/bash
# What this does (plain words): runs the street job file and then the lockout job file of one folder on the rented machine and brings the pictures back. Use: bash run_both.sh FOLDER   (a folder under plate/rubbish/work)
T=proc-work/street_wet/painter_round_2/plate
F=$T/rubbish/work/$1
rm -f $F/all_done.txt
python3 -I $T/rubbish/tools/rent_run.py $F/jobs_street.json > $F/rent_street_out.txt 2>&1
python3 -I $T/rubbish/tools/rent_run.py $F/jobs_lockout.json --no-upload --keep > $F/rent_lockout_out.txt 2>&1
echo done > $F/all_done.txt
