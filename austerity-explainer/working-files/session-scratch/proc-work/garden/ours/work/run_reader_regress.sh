#!/bin/bash
export PYTHONDONTWRITEBYTECODE=1
G=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/ours
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
STREET=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/set_copy/street.blend
LOCK=/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/lockout.blend
cd $G/work
for v in kit_orig kit_copy; do
  for sc in "street $STREET" "lockout $LOCK"; do
    set -- $sc
    s=$(date +%s)
    timeout 500 xvfb-run -a $BL -b --disable-autoexec --factory-startup --python-exit-code 1 $2 --python $G/$v/masks/reader.py -- pit_village_street $1 $G/work/rp_${v}_$1 $G/work/rr_${v}_$1 --no-shade > rlog_${v}_$1.txt 2>&1
    echo "$v $1 exit=$? seconds=$(( $(date +%s)-s ))" >> regress_status.txt
  done
done
echo DONE >> regress_status.txt
