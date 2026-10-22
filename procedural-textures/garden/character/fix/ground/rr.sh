#!/bin/bash
# usage: rr.sh JOBFILE [script]  -> runs the render harness on the card with that job, waits, prints the log tail
export PYTHONDONTWRITEBYTECODE=1
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/ground
SC=${2:-render_ground.py}
mkdir -p $D/logs
id=$(python3 -I $R/render_client_serverless.py run "mkdir -p $D/logs; /workspace/blender/blender -b --disable-autoexec -P $D/$SC -- $D/jobs/$1 > $D/logs/$1.log 2>&1; grep -a 'PREVIEW_DONE\|FINAL_\|FIX_RENDER_ALL\|CHARACTER_RENDER_ALL\|Traceback\|Error\|G6 \|STAGE\|rror' $D/logs/$1.log | cut -c1-400 | tail -60" --cwd $D --timeout 3000 2>&1 | tail -1)
echo "job: $id"
python3 -I $R/render_client_serverless.py wait "$id" --limit 3000 > /tmp/rr_last.json 2>&1
python3 - <<'PY'
import json
try:
    d = json.load(open('/tmp/rr_last.json'))
    print(d.get('state'), 'rc', d.get('return_code'), 'secs', d.get('seconds'), 'billed_ms', d.get('billed_work_ms'))
    print(d.get('log_tail', '')[-7000:])
except Exception as e:
    print('parse error', e); print(open('/tmp/rr_last.json').read()[-3000:])
PY
