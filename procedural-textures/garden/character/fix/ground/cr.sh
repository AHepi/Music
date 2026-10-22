#!/bin/bash
# usage: cr.sh "command" [timeout]  -> runs the command on the card, waits, prints the log tail
export PYTHONDONTWRITEBYTECODE=1
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod
D=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/fix/ground
out=$(python3 -I $R/render_client_serverless.py run "$1" --cwd $D --timeout ${2:-1500} 2>&1 | tail -1)
echo "job: $out"
python3 -I $R/render_client_serverless.py wait "$out" --limit ${2:-1500} 2>&1 > /tmp/cr_last.json
python3 - <<'PY'
import json
d = json.load(open('/tmp/cr_last.json'))
print(d.get('state'), 'rc', d.get('return_code'), 'secs', d.get('seconds'), 'billed_ms', d.get('billed_work_ms'))
print(d.get('log_tail', '')[-6000:])
PY
