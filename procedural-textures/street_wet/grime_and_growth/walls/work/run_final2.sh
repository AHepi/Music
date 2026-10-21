#!/bin/bash
cd proc-work/street_wet/grime_and_growth/walls
rm -rf out/tm_s out/tm_l out/fs_* out/cd1 out/f8_tmp
python3 work/drive.py tm_s work/jobs_tm_street.json street > work/log_tm_s.txt 2>&1
python3 work/drive.py tm_l work/jobs_tm_lockout.json lockout > work/log_tm_l.txt 2>&1
rm -f work/log_alldone.txt work/log_fs_done.txt
bash work/run_all_selftests.sh
echo ALLDONE > work/log_alldone2.txt
