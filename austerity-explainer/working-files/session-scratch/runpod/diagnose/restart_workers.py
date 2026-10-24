# What this does: restarts the pay-per-second endpoint's workers when they are stuck (jobs wait in line, workers say "idle" but never
# start). It sets the most workers allowed to 0, which removes the stuck workers, waits, then sets it back to 3 so RunPod makes fresh
# ones. The endpoint keeps its id, store, cards and settings. Never prints the key or any id.
import json, os, sys, time, urllib.request
HOME = os.path.expanduser('~/.runpod')
AUTH = open(os.path.join(HOME, 'auth_header')).read().strip().split(': ', 1)[1]
SETTINGS = json.load(open(os.path.join(HOME, 'cached_machine.json')))
ENDPOINT = SETTINGS['serverless_endpoint_id']
ROMANIA = next(store['volume_id'] for store in SETTINGS['stores'] if store.get('data_center') == 'EU-RO-1')
QUERY = 'mutation($input: EndpointInput!) { saveEndpoint(input: $input) { name gpuIds workersMax workersMin locations } }'

def graphql(variables):
    request = urllib.request.Request('https://api.runpod.io/graphql', method='POST',
                                     data=json.dumps({'query': QUERY, 'variables': variables}).encode(),
                                     headers={'Authorization': AUTH, 'Content-Type': 'application/json', 'User-Agent': 'render-client/1.0'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read())

def save(most_workers):
    endpoint = {'id': ENDPOINT, 'name': 'blender-render-per-second', 'templateId': SETTINGS['serverless_template_id'],
                'gpuIds': 'ADA_24,ADA_32_PRO,AMPERE_24', 'idleTimeout': 5, 'locations': 'EU-RO-1', 'networkVolumeId': ROMANIA,
                'scalerType': 'QUEUE_DELAY', 'scalerValue': 1, 'workersMax': most_workers, 'workersMin': 0,
                'executionTimeoutMs': 3600000, 'flashBootType': 'FLASHBOOT'}
    answer = graphql({'input': endpoint})
    text = json.dumps(answer.get('errors') or answer.get('data'))
    print(time.strftime('%H:%M:%S'), 'workersMax', most_workers, '->', text.replace(ENDPOINT, '<endpoint>')[:400], flush=True)

save(0)
time.sleep(int(sys.argv[1]) if len(sys.argv) > 1 else 20)
save(3)
