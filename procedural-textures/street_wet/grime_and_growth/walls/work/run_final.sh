#!/bin/bash
cd proc-work/street_wet/grime_and_growth/walls
rm -rf out/f3_* out/f4_* out/tm_s out/tm_l out/st* out/fs_*
python3 work/evalall.py f5 soot,runoff,foot,steps,wallcracks,wallgrowth > work/final_eval.txt 2>&1
echo DONE >> work/final_eval.txt
python3 work/drive.py tm_s work/jobs_tm_street.json street > work/log_tm_s.txt 2>&1
python3 work/drive.py tm_l work/jobs_tm_lockout.json lockout > work/log_tm_l.txt 2>&1
echo TIMING_DONE > work/log_timing_done.txt
bash work/run_all_selftests.sh
echo ALLDONE > work/log_alldone.txt
