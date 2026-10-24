#!/usr/bin/env bash
# What this does: measures one scene (Blender, one at a time) and checks it, into this folder.
# Use: measure.sh NAME [extra Blender options...]
set -u
V=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/checks/verify-follow
K=/home/user/work/paper-pop-up-film-kit
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
name=$1; shift
cd $K
# wait while any other Blender job runs (never two at once on this machine)
for i in $(seq 1 120); do pgrep -f "blender-5.2.2-linux-x64/blender" >/dev/null || break; sleep 5; done
echo "$(date +%T) measuring $name: $*" | tee -a $V/commands.txt
printf '%q ' "$@" > $V/$name.args
DISPLAY=:96 timeout 600 $B -b assets/models/pit-village/street.blend --python paper-film/blender/pit-village/assemble_notice_corner.py \
  --python paper-film/blender/tests/break_scene.py --python paper-film/blender/shot_facts.py -- --view end \
  --check examples/notice-corner/shot-check.json --facts $V/$name "$@" > $V/$name.log 2>&1
echo "blender done: $(grep -c 'shot_facts: done' $V/$name.log); $(grep 'break_scene' $V/$name.log | tr '\n' ' ')"
python3 paper-film/tools/check_shot.py --check examples/notice-corner/shot-check.json --facts $V/$name --out $V/$name-report > $V/$name.checklog 2>&1
echo "check rc=$?"; sed -n '3p' $V/$name-report/report.md
