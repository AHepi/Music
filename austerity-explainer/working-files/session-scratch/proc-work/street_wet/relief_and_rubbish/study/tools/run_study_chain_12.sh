#!/bin/bash
# What this does (plain words): after chain 11, draws the lockout shot's puddle masks (wet and heavy), then measures the baseline (work/r01) and the joint picture mild1 (work/r07) pictures
# again with the dots under puddles left out. One Blender run at a time.
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet
R=$S/relief_and_rubbish/study
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $S
until grep -q "CHAIN 11 DONE" $R/work/logs/chain11.log 2>/dev/null; do sleep 15; done
mkdir -p $R/work/r12
xvfb-run -a $B -b --disable-autoexec -t 2 /home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend --python $R/tools/b03_render_jobs.py -- $R/work/jobs/puddle_masks_lockout.json $R/work/r12 > $R/work/logs/puddle_masks_lockout.log 2>&1
python3 -I $R/tools/b15_remeasure_with_puddles.py $R/work/r07 $R/work/r10 $R/work/r12 > $R/work/logs/remeasure_r07.log 2>&1
python3 -I $R/tools/b15_remeasure_with_puddles.py $R/work/r01 $R/work/r10 $R/work/r12 --rename-lockout > $R/work/logs/remeasure_r01.log 2>&1
python3 -I $R/tools/b09_lighting_test_set.py report full $R/work/r07 measurements_nopuddle.json > $R/work/logs/full_mild1_report_nopuddle.txt 2>&1
python3 -I $R/tools/b09_lighting_test_set.py report full $R/work/r01 measurements_nopuddle.json > $R/work/logs/full_baseline_report_nopuddle.txt 2>&1
echo "CHAIN 12 DONE $(date +%T)" >> $R/work/logs/chain12.log
