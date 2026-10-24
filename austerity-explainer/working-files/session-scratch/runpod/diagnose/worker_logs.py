# What this does: lists the pay-per-second endpoint's workers and prints the end of each worker's log (RunPod REST v2), plus the store's
# size, so a stuck endpoint can be diagnosed. Never prints the key; ids are shortened to their first 4 characters.
import json, os, re, sys, urllib.request
HOME = os.path.expanduser('~/.runpod')
AUTH = open(os.path.join(HOME, 'auth_header')).read().strip().split(': ', 1)[1]
SETTINGS = json.load(open(os.path.join(HOME, 'cached_machine.json')))
ENDPOINT = SETTINGS['serverless_endpoint_id']
SECRETS = [ENDPOINT, SETTINGS.get('serverless_template_id', ''), SETTINGS.get('volume_id', '')] + [s.get('volume_id', '') for s in SETTINGS.get('stores', [])]

def get(path):
    request = urllib.request.Request('https://api.runpod.io' + path, headers={'Authorization': AUTH, 'User-Agent': 'render-client/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read() or b'null')
    except urllib.error.HTTPError as error:
        return {'http_error': error.code, 'body': error.read().decode(errors='replace')[:300]}

def hide(text):
    text = str(text)
    for secret in SECRETS:
        if secret:
            text = text.replace(secret, secret[:4] + '…')
    return text

workers = get(f'/v2/serverless/{ENDPOINT}/workers')
print(hide(json.dumps(workers)[:1500]))
items = workers if isinstance(workers, list) else (workers.get('workers') or workers.get('data') or []) if isinstance(workers, dict) else []
for worker in items[:4]:
    worker_id = worker.get('id') or worker.get('workerId')
    logs = get(f'/v2/serverless/{ENDPOINT}/workers/{worker_id}/logs')
    text = json.dumps(logs)
    print('==== worker', str(worker_id)[:4], '…')
    print(hide(text[-int(sys.argv[1]) if len(sys.argv) > 1 else -3000:]))
volumes = get('/v2/network-volumes')
print('==== stores', hide(json.dumps(volumes)[:800]))
