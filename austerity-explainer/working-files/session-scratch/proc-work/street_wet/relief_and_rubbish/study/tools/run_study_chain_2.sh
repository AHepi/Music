#!/bin/bash
# What this does (plain words): waits for chain 1 to finish (never two Blender runs at once), then runs (a) the two quick "plan probes" that read where doors, walls and props stand,
# and (b) the first solution tests on the street (a joint picture and real geometry). Pictures are measured and shrunk after each run.
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet
R=$S/relief_and_rubbish/study
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
J=$R/work/jobs
cd $S
until grep -q "CHAIN 1 DONE" $R/work/logs/chain1.log 2>/dev/null; do sleep 15; done
free_gb() { df --output=avail -BM / | tail -1 | tr -dc 0-9; }
if [ "$(free_gb)" -lt 1250 ]; then echo "STOP: disk below 1.25 GB" >> $R/work/logs/chain2.log; exit 1; fi
xvfb-run -a $B -b --disable-autoexec -t 2 set_copy/street.blend --python $R/tools/b07_probe_street_plan.py -- $R/work/plan_street.json > $R/work/logs/probe_street.log 2>&1
xvfb-run -a $B -b --disable-autoexec -t 2 /home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend --python $R/tools/b07_probe_street_plan.py -- $R/work/plan_lockout.json > $R/work/logs/probe_lockout.log 2>&1
echo "probes finished $(date +%T)" >> $R/work/logs/chain2.log
if [ "$(free_gb)" -lt 1250 ]; then echo "STOP: disk below 1.25 GB" >> $R/work/logs/chain2.log; exit 1; fi
xvfb-run -a $B -b --disable-autoexec -t 2 set_copy/street.blend --python $R/tools/b03_render_jobs.py -- $J/sol1_street.json $R/work/r02 > $R/work/logs/sol1_street.log 2>&1
python3 -I $R/tools/b05_measure_folder.py $R/work/r02 $J/sol1_street.json --convert >> $R/work/logs/sol1_street_measure.log 2>&1
echo "sol1 finished $(date +%T)" >> $R/work/logs/chain2.log
echo "CHAIN 2 DONE $(date +%T)" >> $R/work/logs/chain2.log
