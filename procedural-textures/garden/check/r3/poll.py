# Checker round 3: read-only endpoint health every 30 s (GET /health through the client's own call; no ping job).
import importlib.util, time, datetime, sys
spec = importlib.util.spec_from_file_location('rcs', 'scratchpad/runpod/render_client_serverless.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
end = time.time() + float(sys.argv[1])
while time.time() < end:
    try:
        h = m.call('GET', '/health', attempts=2)
        w, j = h['workers'], h['jobs']
        print(datetime.datetime.utcnow().strftime('%H:%M:%S'), 'idle', w.get('idle'), 'ready', w.get('ready'), 'running', w.get('running'), 'init', w.get('initializing'), '| inProgress', j.get('inProgress'), 'inQueue', j.get('inQueue'), 'completed', j.get('completed'), flush=True)
    except Exception as e:
        print('error', str(e)[:80], flush=True)
    time.sleep(30)
