# Checker tool: reads the endpoint health through the sanctioned client's own call(), WITHOUT the ping job that
# the client's 'status' action sends (that ping wakes and bills a worker). Prints counts only, no ids or keys.
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location('rcs', '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/runpod/render_client_serverless.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
h = m.call('GET', '/health')
print(json.dumps(h, indent=1))
