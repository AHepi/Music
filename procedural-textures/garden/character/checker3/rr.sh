#!/bin/bash
# usage: rr.sh job_script.sh [timeout] -> uploads my scripts+jobs, runs one RunPod job, waits, prints the tail of its log
RC=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod/render_client_serverless.py
C=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker3
python3 -I $RC upload $C/scripts --remote $C/scripts >/dev/null 2>&1
python3 -I $RC upload $C/jobs --remote $C/jobs >/dev/null 2>&1
JID=$(python3 -I $RC run "bash $C/jobs/$1" --cwd $C --timeout ${2:-900} 2>&1 | tail -1)
echo "job: $JID"
python3 -I $RC wait $JID --limit ${2:-900} 2>&1 | python3 -I -c "
import sys,json
t=sys.stdin.read()
try:
    d=json.loads(t[t.index('{'):])
    print('state',d.get('state'),'rc',d.get('return_code'),'billed_ms',d.get('billed_work_ms'))
    print(d.get('log_tail','')[-4000:])
except Exception as e:
    print(t[-2500:])
"
