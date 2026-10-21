#!/bin/bash
cd proc-work/street_wet/grime_and_growth/walls
H=$(pwd)
python3 work/run_selftest.py $H/work/tuned/street_set.json street $H/work/cfg_street.json fs_street > work/log_fs1.txt 2>&1
python3 work/run_selftest.py $H/work/tuned/street_set.json street $H/work/cfg_street_steps.json fs_steps > work/log_fs2.txt 2>&1
python3 work/run_selftest.py pit_village_street lockout $H/work/cfg_lockout.json fs_lockout > work/log_fs3.txt 2>&1
python3 work/run_selftest.py japanese_courtyard courtyard $H/work/cfg_courtyard.json fs_court > work/log_fs4.txt 2>&1
echo DONE > work/log_fs_done.txt
