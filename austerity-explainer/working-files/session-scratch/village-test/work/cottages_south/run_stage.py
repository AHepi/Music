import sys, json, time
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/stages')
import importlib
t = time.time()
import stage_cottages_south as st
import os
opts = json.loads(os.environ.get('COTT_OPTS', '{}'))
f = st.apply(opts)
print('FACTS', json.dumps(f, default=str)[:3000])
print('SECONDS', round(time.time() - t, 1))
import bpy
if os.environ.get('COTT_SAVE'):
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=os.environ['COTT_SAVE'])
