# What this does: asks RunPod's GraphQL service how the pay-per-second endpoint is set up (cards, worker limits, store, region) and
# which cards are in stock in the store's data centre. Never prints the key or any id.
import json, os, sys, urllib.request
HOME = os.path.expanduser('~/.runpod')
AUTH = open(os.path.join(HOME, 'auth_header')).read().strip().split(': ', 1)[1]
ENDPOINT = json.load(open(os.path.join(HOME, 'cached_machine.json')))['serverless_endpoint_id']

def graphql(query):
    request = urllib.request.Request('https://api.runpod.io/graphql', method='POST', data=json.dumps({'query': query}).encode(),
                                     headers={'Authorization': AUTH, 'Content-Type': 'application/json', 'User-Agent': 'render-client/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        return {'http_error': error.code, 'body': error.read().decode(errors='replace')[:400]}

def hide(text):
    return str(text).replace(ENDPOINT, '<endpoint>')

part = sys.argv[1] if len(sys.argv) > 1 else 'endpoint'
if part == 'endpoint':
    answer = graphql('{ myself { endpoints { id name gpuIds workersMin workersMax idleTimeout locations networkVolumeId scalerType scalerValue gpuCount } } }')
    if 'data' in answer and answer['data']:
        for endpoint in answer['data']['myself']['endpoints']:
            if endpoint['id'] == ENDPOINT:
                endpoint = {k: v for k, v in endpoint.items() if k not in ('id', 'networkVolumeId')}
                print(json.dumps(endpoint, indent=1))
    else:
        print(hide(json.dumps(answer)[:800]))
elif part == 'stock':
    data_centre = sys.argv[2] if len(sys.argv) > 2 else 'EU-RO-1'
    answer = graphql('{ gpuTypes { id displayName memoryInGb lowestPrice(input: {gpuCount: 1, dataCenterId: "%s", secureCloud: true}) { stockStatus uninterruptablePrice } } }' % data_centre)
    if 'data' in answer and answer['data']:
        for gpu in answer['data']['gpuTypes']:
            price = gpu.get('lowestPrice') or {}
            if price.get('stockStatus'):
                print(gpu['displayName'], gpu['memoryInGb'], 'GB', price.get('stockStatus'), price.get('uninterruptablePrice'))
    else:
        print(json.dumps(answer)[:800])
