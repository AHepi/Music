#!/bin/bash
export PYTHONDONTWRITEBYTECODE=1
G=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/ours
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
COURT=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/astra-work/out/courtyard_final.blend
cd $G/work
for v in kit_orig kit_patched; do
  s=$(date +%s)
  timeout 280 xvfb-run -a $BL -b --disable-autoexec --factory-startup --python-exit-code 1 $COURT -P preview_kit.py -- $G/$v $G/work/prev_$v > plog_$v.txt 2>&1
  echo "$v exit=$? seconds=$(( $(date +%s)-s ))" >> preview_status.txt
done
echo DONE >> preview_status.txt
