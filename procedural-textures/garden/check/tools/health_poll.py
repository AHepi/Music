# Checker tool: polls endpoint health (read-only GET, no ping job) every 15 s for ~6 minutes; counts only.
import importlib.util, json, time, datetime
spec = importlib.util.spec_from_file_location('rcs', 'scratchpad/runpod/render_client_serverless.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for i in range(26):
    h = m.call('GET', '/health')
    w = h['workers']; j = h['jobs']
    print(datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S'), 'idle', w['idle'], 'ready', w['ready'], 'running', w['running'], 'init', w['initializing'], 'throttled', w['throttled'], '| inProgress', j['inProgress'], 'inQueue', j['inQueue'], 'completed', j['completed'], flush=True)
    time.sleep(15)
