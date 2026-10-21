#!/bin/bash
# What this does (plain words): waits for chain 5 (the first, failed try of the rubbish prototype), then runs the third solution tests (milder joint pictures across the lightings,
# and the texture filter test). One Blender run at a time.
S=proc-work/street_wet
R=$S/relief_and_rubbish/study
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
J=$R/work/jobs
cd $S
until grep -q "CHAIN 5 DONE" $R/work/logs/chain5.log 2>/dev/null; do sleep 15; done
free_gb() { df --output=avail -BM / | tail -1 | tr -dc 0-9; }
if [ "$(free_gb)" -lt 1250 ]; then echo "STOP: disk below 1.25 GB" >> $R/work/logs/chain6.log; exit 1; fi
xvfb-run -a $B -b --disable-autoexec -t 2 set_copy/street.blend --python $R/tools/b03_render_jobs.py -- $J/sol3_street.json $R/work/r06 > $R/work/logs/sol3_street.log 2>&1
python3 -I $R/tools/b05_measure_folder.py $R/work/r06 $J/sol3_street.json --convert >> $R/work/logs/sol3_street_measure.log 2>&1
echo "CHAIN 6 DONE $(date +%T)" >> $R/work/logs/chain6.log
