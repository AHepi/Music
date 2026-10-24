#!/bin/bash
# What this does (plain words): the second solution tests (softer joint pictures, real geometry), close view, one Blender run; then measures and shrinks the pictures.
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet
R=$S/relief_and_rubbish/study
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
J=$R/work/jobs
cd $S
free_gb() { df --output=avail -BM / | tail -1 | tr -dc 0-9; }
if [ "$(free_gb)" -lt 1250 ]; then echo "STOP: disk below 1.25 GB" >> $R/work/logs/chain4.log; exit 1; fi
xvfb-run -a $B -b --disable-autoexec -t 2 set_copy/street.blend --python $R/tools/b03_render_jobs.py -- $J/sol2_street.json $R/work/r04 > $R/work/logs/sol2_street.log 2>&1
python3 -I $R/tools/b05_measure_folder.py $R/work/r04 $J/sol2_street.json --convert >> $R/work/logs/sol2_street_measure.log 2>&1
echo "CHAIN 4 DONE $(date +%T)" >> $R/work/logs/chain4.log
