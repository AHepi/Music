#!/bin/bash
# What this does (plain words): after chain 8 (the whole lighting test set with the joint picture), (a) the fourth solution tests (texture filter, hybrid geometry, 1080 x 1920) and
# (b) the rubbish prototype ON TOP of the joint picture (chained layers), street and lockout. One Blender run at a time.
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet
R=$S/relief_and_rubbish/study
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
J=$R/work/jobs
cd $S
until grep -q "CHAIN 8 DONE" $R/work/logs/chain8.log 2>/dev/null; do sleep 15; done
free_gb() { df --output=avail -BM / | tail -1 | tr -dc 0-9; }
if [ "$(free_gb)" -lt 1250 ]; then echo "STOP: disk below 1.25 GB" >> $R/work/logs/chain9.log; exit 1; fi
xvfb-run -a $B -b --disable-autoexec -t 2 set_copy/street.blend --python $R/tools/b03_render_jobs.py -- $J/sol4_street.json $R/work/r08 > $R/work/logs/sol4_street.log 2>&1
python3 -I $R/tools/b05_measure_folder.py $R/work/r08 $J/sol4_street.json --convert >> $R/work/logs/sol4_street_measure.log 2>&1
echo "sol4 finished $(date +%T)" >> $R/work/logs/chain9.log
if [ "$(free_gb)" -lt 1250 ]; then echo "STOP: disk below 1.25 GB" >> $R/work/logs/chain9.log; exit 1; fi
mkdir -p $R/work/r09
RUBBISH_WITH_JOINT=1 xvfb-run -a $B -b --disable-autoexec -t 2 set_copy/street.blend --python $R/tools/b11_rubbish_prototype.py -- $R/work/r09 "main:A:wet:1:1:540:960:16:main_A_wet_joint_muck_pieces,close_road:A:wet:1:1:640:480:24:close_A_wet_joint_muck_pieces,main:E:wet:1:1:540:960:16:main_E_wet_joint_muck_pieces" > $R/work/logs/rubbish_joint_street.log 2>&1
echo "rubbish+joint street finished $(date +%T)" >> $R/work/logs/chain9.log
RUBBISH_WITH_JOINT=1 RUBBISH_MASK=$R/work/rubbish_plan_mask_lockout.png xvfb-run -a $B -b --disable-autoexec -t 2 /home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend --python $R/tools/b11_rubbish_prototype.py -- $R/work/r09 "lockout:B:wet:1:1:540:960:16:lockout_B_wet_joint_muck_pieces" > $R/work/logs/rubbish_joint_lockout.log 2>&1
echo "rubbish+joint lockout finished $(date +%T)" >> $R/work/logs/chain9.log
echo "CHAIN 9 DONE $(date +%T)" >> $R/work/logs/chain9.log
