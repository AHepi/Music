#!/bin/bash
# What this does: runs the checker's two job files on the rented machine, one after the other, and brings the pictures back.
python3 -I proc-work/street_wet/relief_and_rubbish/rubbish/tools/rent_run.py proc-work/street_wet/relief_and_rubbish/check_round_1/run_a/jobs_street.json > proc-work/street_wet/relief_and_rubbish/check_round_1/run_a_log.txt 2>&1
python3 -I proc-work/street_wet/relief_and_rubbish/rubbish/tools/rent_run.py proc-work/street_wet/relief_and_rubbish/check_round_1/run_b/jobs_lockout.json > proc-work/street_wet/relief_and_rubbish/check_round_1/run_b_log.txt 2>&1
echo done > proc-work/street_wet/relief_and_rubbish/check_round_1/run_all_done.txt
