#!/bin/bash
# What this does (plain words): after chain 10, the SECOND try of the rubbish prototype, on top of the joint picture: far fewer pieces (45 a square metre at most instead of 140, none beyond 32 m
# along the street), a stronger muck layer (1.5), on the main camera, the close camera, a bigger close view, and in the lockout shot. One Blender run at a time.
S=proc-work/street_wet
R=$S/relief_and_rubbish/study
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $S
until grep -q "CHAIN 10 DONE" $R/work/logs/chain10.log 2>/dev/null; do sleep 15; done
free_gb() { df --output=avail -BM / | tail -1 | tr -dc 0-9; }
if [ "$(free_gb)" -lt 1250 ]; then echo "STOP: disk below 1.25 GB" >> $R/work/logs/chain11.log; exit 1; fi
mkdir -p $R/work/r11
export RUBBISH_WITH_JOINT=1 RUBBISH_DENSITY=45 RUBBISH_YMAX=32 RUBBISH_MUCK=1.5
xvfb-run -a $B -b --disable-autoexec -t 2 set_copy/street.blend --python $R/tools/b11_rubbish_prototype.py -- $R/work/r11 "main:A:wet:1:1:540:960:16:main_A_wet_v2,close_road:A:wet:1:1:640:480:24:close_A_wet_v2,close_road:A:wet:1:1:1280:960:16:close_A_wet_v2_big,main:A:dry:1:1:540:960:16:main_A_dry_v2" > $R/work/logs/rubbish2_street.log 2>&1
echo "rubbish2 street finished $(date +%T)" >> $R/work/logs/chain11.log
RUBBISH_MASK=$R/work/rubbish_plan_mask_lockout.png xvfb-run -a $B -b --disable-autoexec -t 2 /home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend --python $R/tools/b11_rubbish_prototype.py -- $R/work/r11 "lockout:B:wet:1:1:540:960:16:lockout_B_wet_v2,lockout:B:dry:1:1:540:960:16:lockout_B_dry_v2" > $R/work/logs/rubbish2_lockout.log 2>&1
echo "CHAIN 11 DONE $(date +%T)" >> $R/work/logs/chain11.log
