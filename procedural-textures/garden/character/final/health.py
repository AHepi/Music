import sys, json, time
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod')
import render_client_serverless as r
n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
for i in range(n):
    h = r.call('GET', '/health')
    print(time.strftime('%H:%M:%S'), json.dumps(h['jobs']), json.dumps(h['workers']), flush=True)
    if i + 1 < n:
        time.sleep(20)
