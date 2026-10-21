#!/bin/bash
# What this does (plain words): waits for chain 6, then runs the RUBBISH PROTOTYPE (b11_rubbish_prototype.py) on the street (pieces only, muck + pieces, muck only, a close view, a dry one,
# a bigger close view for reading the pieces) and on the film's lockout shot file (with the lockout mask: fire drum, coal slack, dustbins). One Blender run at a time.
S=proc-work/street_wet
R=$S/relief_and_rubbish/study
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $S
until grep -q "CHAIN 6 DONE" $R/work/logs/chain6.log 2>/dev/null; do sleep 15; done
free_gb() { df --output=avail -BM / | tail -1 | tr -dc 0-9; }
if [ "$(free_gb)" -lt 1250 ]; then echo "STOP: disk below 1.25 GB" >> $R/work/logs/chain7.log; exit 1; fi
mkdir -p $R/work/r05
xvfb-run -a $B -b --disable-autoexec -t 2 set_copy/street.blend --python $R/tools/b11_rubbish_prototype.py -- $R/work/r05 "main:A:wet:0:1:540:960:16:main_A_wet_pieces_only,main:A:wet:1:1:540:960:16:main_A_wet_muck_pieces,main:A:wet:1:0:540:960:16:main_A_wet_muck_only,main:A:dry:1:1:540:960:16:main_A_dry_muck_pieces,close_road:A:wet:1:1:640:480:24:close_A_wet_muck_pieces,close_road:A:wet:1:1:1280:960:16:close_A_wet_muck_pieces_big" > $R/work/logs/rubbish_street.log 2>&1
echo "rubbish street finished $(date +%T)" >> $R/work/logs/chain7.log
RUBBISH_MASK=$R/work/rubbish_plan_mask_lockout.png xvfb-run -a $B -b --disable-autoexec -t 2 /home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend --python $R/tools/b11_rubbish_prototype.py -- $R/work/r05 "lockout:B:wet:1:1:540:960:16:lockout_B_wet_muck_pieces,lockout:B:dry:1:1:540:960:16:lockout_B_dry_muck_pieces" > $R/work/logs/rubbish_lockout.log 2>&1
echo "rubbish lockout finished $(date +%T)" >> $R/work/logs/chain7.log
echo "CHAIN 7 DONE $(date +%T)" >> $R/work/logs/chain7.log
