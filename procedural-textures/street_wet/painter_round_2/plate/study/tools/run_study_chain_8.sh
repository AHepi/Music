#!/bin/bash
# What this does (plain words): waits for chain 7 (the rubbish prototype), then draws the WHOLE lighting test set ("full": 32 pictures) with the joint picture mild1 on the road, in the street file and in the
# film's lockout shot file, measures it, and prints the PASS / FAIL report. This is also the first real use of the test set's own scripts.
S=proc-work/street_wet
R=$S/relief_and_rubbish/study
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $S
until grep -q "CHAIN 7 DONE" $R/work/logs/chain7.log 2>/dev/null; do sleep 15; done
free_gb() { df --output=avail -BM / | tail -1 | tr -dc 0-9; }
mkdir -p $R/work/r07
for kind in street lockout; do
  if [ "$(free_gb)" -lt 1250 ]; then echo "STOP: disk below 1.25 GB" >> $R/work/logs/chain8.log; exit 1; fi
  if [ $kind = street ]; then FILE=set_copy/street.blend; else FILE=/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend; fi
  xvfb-run -a $B -b --disable-autoexec -t 2 $FILE --python $R/tools/b03_render_jobs.py -- $R/work/r07_jobs/jobs_$kind.json $R/work/r07 > $R/work/logs/full_mild1_$kind.log 2>&1
  python3 -I $R/tools/b05_measure_folder.py $R/work/r07 $R/work/r07_jobs/jobs_$kind.json --convert >> $R/work/logs/full_mild1_measure.log 2>&1
  echo "full set mild1 $kind finished $(date +%T)" >> $R/work/logs/chain8.log
done
python3 -I $R/tools/b09_lighting_test_set.py report full $R/work/r07 > $R/work/logs/full_mild1_report.txt 2>&1
echo "CHAIN 8 DONE $(date +%T)" >> $R/work/logs/chain8.log
