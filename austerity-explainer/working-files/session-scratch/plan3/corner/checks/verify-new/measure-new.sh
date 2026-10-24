#!/usr/bin/env bash
# What this does: measures new broken copies of the notice corner (one Blender job at a time) and checks each with check_shot.py.
# Use: measure-new.sh NAME [extra Blender options]
set -u
V=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plan3/corner/checks/verify-new
K=/home/user/work/paper-pop-up-film-kit
B=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $K
name=$1; shift
DISPLAY=:96 timeout 600 $B -b assets/models/pit-village/street.blend --python paper-film/blender/pit-village/assemble_notice_corner.py \
  --python paper-film/blender/tests/break_scene.py --python paper-film/blender/shot_facts.py -- --view end \
  --check examples/notice-corner/shot-check.json --facts $V/$name "$@" > $V/$name.log 2>&1
echo "measured $name: $(grep -c 'shot_facts: done' $V/$name.log)"; grep break_scene $V/$name.log
python3 paper-film/tools/check_shot.py --check examples/notice-corner/shot-check.json --facts $V/$name --out $V/$name-report > /dev/null 2> $V/$name-report.err
echo "checked $name: $(head -3 $V/$name-report/report.md | tail -1)"
