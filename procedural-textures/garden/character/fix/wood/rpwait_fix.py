"""rpwait_fix.py LABEL JOBID [LIMIT] - waits for a RunPod job (pay-per-second client), prints a short summary and the end of its log,
and appends 'label | id | billed_ms | wake_ms | rc | status' to jobs_ledger.txt in this folder."""
import subprocess, sys, json, os, time
RC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod/render_client_serverless.py'
L = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jobs_ledger.txt')
lab, jid = sys.argv[1], sys.argv[2]
limit = sys.argv[3] if len(sys.argv) > 3 else '1500'
t0 = time.time()
out = subprocess.run(['python3', '-I', RC, 'wait', jid, '--limit', limit], capture_output=True, text=True, cwd='/').stdout
try:
    d = json.loads(out)
except Exception:
    print('NO JSON', out[:800]); sys.exit(1)
open(L, 'a').write('%s | %s | billed_ms %s | wake_ms %s | rc %s | %s\n' % (lab, jid, d.get('billed_work_ms'), d.get('wake_up_ms'), d.get('return_code'), d.get('runpod_status')))
print(json.dumps({k: d.get(k) for k in ('runpod_status', 'return_code', 'seconds', 'wake_up_ms', 'billed_work_ms')}), 'waited %.0fs' % (time.time() - t0))
print((d.get('log_tail') or '')[-int(os.environ.get('TAIL', '3500')):])
