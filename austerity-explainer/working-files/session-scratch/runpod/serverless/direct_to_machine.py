# What this does: talks straight to the running storage machine's job server (bypassing RunPod's main system, for when that system
# is down). Reads the machine id and the secret code from ~/.runpod without printing them.
# Use: python3 -I direct_to_machine.py status | run "COMMAND" | wait JOB_ID [SECONDS] | upload LOCAL REMOTE
import json, os, sys, time, urllib.parse, urllib.request
home = os.path.expanduser('~/.runpod')
state = json.load(open(os.path.join(home, 'cached_machine.json')))
token = open(os.path.join(home, 'server_token')).read().strip()
base = f"https://{state['pod_id']}-8000.proxy.runpod.net"
def call(method, path, query=None, body=None, raw=False):
    url = base + path + ('?' + urllib.parse.urlencode(query) if query else '')
    request = urllib.request.Request(url, data=body, method=method, headers={'X-Token': token, 'Content-Type': 'application/octet-stream', 'User-Agent': 'render-client/1.0 (blender jobs)'})
    with urllib.request.urlopen(request, timeout=95) as response:
        data = response.read()
        return data if raw else json.loads(data)
action = sys.argv[1]
if action == 'status':
    print(json.dumps(call('GET', '/status'), indent=1))
elif action == 'run':
    print(call('POST', '/run', body=json.dumps({'command': sys.argv[2]}).encode())['id'])
elif action == 'wait':
    limit = float(sys.argv[3]) if len(sys.argv) > 3 else 600
    started = time.time()
    while True:
        job = call('GET', '/jobs/' + sys.argv[2], {'tail': 4000})
        if job['state'] != 'running' or time.time() - started > limit:
            print(job['state'], job.get('return_code')); print(job.get('log_tail', '')); break
        time.sleep(5)
elif action == 'upload':
    data = open(sys.argv[2], 'rb').read()
    print(call('POST', '/file', {'path': sys.argv[3], 'offset': 0}, body=data))
