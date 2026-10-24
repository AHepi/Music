#!/bin/bash
# What this does (plain words): (1) the rest of the first solution tests on the street (finished pictures are skipped), (2) the lockout camera's MASK picture (the first lockout run used
# the street's mask by mistake: both were called "main"), then re-measures the lockout baseline pictures against it. One Blender run at a time.
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet
R=$S/relief_and_rubbish/study
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
J=$R/work/jobs
cd $S
free_gb() { df --output=avail -BM / | tail -1 | tr -dc 0-9; }
if [ "$(free_gb)" -lt 1250 ]; then echo "STOP: disk below 1.25 GB" >> $R/work/logs/chain3.log; exit 1; fi
xvfb-run -a $B -b --disable-autoexec -t 2 set_copy/street.blend --python $R/tools/b03_render_jobs.py -- $J/sol1_street.json $R/work/r02 > $R/work/logs/sol1_street_b.log 2>&1
python3 -I $R/tools/b05_measure_folder.py $R/work/r02 $J/sol1_street.json --convert >> $R/work/logs/sol1_street_measure.log 2>&1
echo "sol1 (rest) finished $(date +%T)" >> $R/work/logs/chain3.log
mkdir -p $R/work/r03
xvfb-run -a $B -b --disable-autoexec -t 2 /home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend --python $R/tools/b03_render_jobs.py -- $J/lockout_mask_only.json $R/work/r03 > $R/work/logs/lockout_mask.log 2>&1
echo "lockout mask finished $(date +%T)" >> $R/work/logs/chain3.log
echo "CHAIN 3 DONE $(date +%T)" >> $R/work/logs/chain3.log
