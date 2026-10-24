#!/bin/bash
# What this does (plain words): after chain 12, the SELF-TEST of the one-command lighting test set: run_lighting_test_set.sh on the QUICK set with the joint picture mild1, exactly as a later helper would
# run it. The report it prints is the proof that the script works from start to end.
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet
R=$S/relief_and_rubbish/study
cd $S
until grep -q "CHAIN 12 DONE" $R/work/logs/chain12.log 2>/dev/null; do sleep 15; done
started=$(date +%s)
bash $R/tools/run_lighting_test_set.sh quick $R/work/r13 --variant joint_picture --args '{"colour_mult":0.85,"rough_to":0.9,"spec_keep":0.65,"coat_keep":0.55,"picture":"joint_cavity_closed.png"}' > $R/work/logs/quick_selftest.txt 2>&1
echo "quick self-test took $(( $(date +%s) - started )) seconds" >> $R/work/logs/chain13.log
echo "CHAIN 13 DONE $(date +%T)" >> $R/work/logs/chain13.log
