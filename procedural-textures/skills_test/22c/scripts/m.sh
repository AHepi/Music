#!/bin/bash
# helper: m.sh SCRIPT_NAME OUTSUB [extra blender args after --]  -> uploads scripts, runs one Blender script on the rented machine, prints the tail of its log
C=scratchpad/runpod/render_client_cached.py
W=proc-work/skills_test/22c
S=$1; O=$2; shift 2
python3 -I $C upload $W/scripts > /dev/null 2>&1
J=$(python3 -I $C run "mkdir -p out/$O && /workspace/blender/blender -b --disable-autoexec --factory-startup set_copy/street.blend --python-exit-code 1 --python scripts/$S -- out/$O $* > out/$O/run_$S.log 2>&1; echo rc=\$?; grep -v 'Saved:' out/$O/run_$S.log | tail -30" --cwd $W | tail -1)
python3 -I $C wait $J --limit 500 | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['state'], 'rc', d['return_code'], d['seconds'], 's'); print(d['log_tail'])"
