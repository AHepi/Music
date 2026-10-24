#!/bin/bash
# What this does (plain words): runs the study's first three Blender runs ONE AFTER THE OTHER (never two at once): the baseline street pictures, the one-setting-at-a-time
# diagnosis pictures, and the baseline lockout pictures; after each run it measures the pictures and shrinks them to JPEG. Safe to run again: finished pictures are skipped.
# Run: bash run_study_chain_1.sh   (from anywhere; writes work/r01/ and work/logs/)
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet
R=$S/relief_and_rubbish/study
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
J=$R/work/jobs
cd $S
free_gb() { df --output=avail -BM / | tail -1 | tr -dc 0-9; }
run() {   # run FILE JOBFILE OUT TAG
  if [ "$(free_gb)" -lt 1250 ]; then echo "STOP: disk below 1.25 GB" >> $R/work/logs/chain1.log; exit 1; fi
  xvfb-run -a $B -b --disable-autoexec -t 2 "$1" --python $R/tools/b03_render_jobs.py -- $2 $3 > $R/work/logs/$4.log 2>&1
  python3 -I $R/tools/b05_measure_folder.py $3 $2 --convert >> $R/work/logs/$4_measure.log 2>&1
  echo "$4 finished $(date +%T)" >> $R/work/logs/chain1.log
}
mkdir -p $R/work/r01
run set_copy/street.blend $J/base_street.json $R/work/r01 base_street
run set_copy/street.blend $J/diag_street.json $R/work/r01 diag_street
run /home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend $J/base_lockout.json $R/work/r01 base_lockout
echo "CHAIN 1 DONE $(date +%T)" >> $R/work/logs/chain1.log
