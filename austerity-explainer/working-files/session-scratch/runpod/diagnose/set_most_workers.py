# What this does: sets the most workers the pay-per-second endpoint may run. 0 switches it fully off (no worker can start, nothing can
# bill); 3 is the normal setting for rendering. Usage: python3 -I set_most_workers.py 0   or   python3 -I set_most_workers.py 3
# The endpoint keeps its id, store, cards and settings. Never prints the key or any id.
import json, os, sys, time, urllib.request
HOME = os.path.expanduser('~/.runpod')
AUTH = open(os.path.join(HOME, 'auth_header')).read().strip().split(': ', 1)[1]
SETTINGS = json.load(open(os.path.join(HOME, 'cached_machine.json')))
ENDPOINT = SETTINGS['serverless_endpoint_id']
ROMANIA = next(store['volume_id'] for store in SETTINGS['stores'] if store.get('data_center') == 'EU-RO-1')
QUERY = 'mutation($input: EndpointInput!) { saveEndpoint(input: $input) { name workersMax workersMin } }'
most_workers = int(sys.argv[1])
endpoint = {'id': ENDPOINT, 'name': 'blender-render-per-second', 'templateId': SETTINGS['serverless_template_id'],
            'gpuIds': 'ADA_24,ADA_32_PRO,AMPERE_24', 'idleTimeout': 5, 'locations': 'EU-RO-1', 'networkVolumeId': ROMANIA,
            'scalerType': 'QUEUE_DELAY', 'scalerValue': 1, 'workersMax': most_workers, 'workersMin': 0,
            'executionTimeoutMs': 3600000, 'flashBootType': 'FLASHBOOT'}
request = urllib.request.Request('https://api.runpod.io/graphql', method='POST',
                                 data=json.dumps({'query': QUERY, 'variables': {'input': endpoint}}).encode(),
                                 headers={'Authorization': AUTH, 'Content-Type': 'application/json', 'User-Agent': 'render-client/1.0'})
with urllib.request.urlopen(request, timeout=60) as response:
    answer = json.loads(response.read())
print(time.strftime('%H:%M:%S'), json.dumps(answer.get('errors') or answer.get('data')).replace(ENDPOINT, '<endpoint>')[:300])
