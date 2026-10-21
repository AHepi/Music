# What this does (plain words)
# --------------------------------------------------------------------------------------------------------------------------------------------
# Trial 22d, step 3a. The export skill says: run the expert skill's delivery gate (bx_audit.deliverable) on the parts before exporting. This runs it
#   A. on the litter alone (realized into mesh, because the gate reads meshes, not instances),
#   B. on the litter together with the road band and the gutter stones it lies on,
#   C. on every mesh in the street (timed; the street is 374 parts, which the skill says to gate one by one).
# Reports pass/fail, the error and warning counts and the first messages. Saves nothing into the street files.
# Run: xvfb-run -a blender -b --disable-autoexec --factory-startup set_copy/street_litter.blend -P scripts/33_gate.py -- OUT_FOLDER WHICH(A|B|C)
import json
import os
import sys
import time

sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-expert/scripts')
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-geometry-nodes/scripts')
import bpy  # noqa: E402

import bx_audit  # noqa: E402
import bx_gn as G  # noqa: E402

out, which = sys.argv[sys.argv.index('--') + 1:][:2]
host = bpy.data.objects['gutter_litter']
G.set_inputs(host.modifiers['Gutter Litter'], {'Realize': True})
if which == 'A':
    parts = ['gutter_litter']
elif which == 'B':
    parts = ['gutter_litter', 'street_setts', 'street_channels']
else:
    parts = [o.name for o in bpy.context.scene.objects if o.type == 'MESH' and o.visible_get()]
t0 = time.time()
g = bx_audit.deliverable(parts, profile='game')
dt = round(time.time() - t0, 1)
msgs_err = list(g['errors'])
msgs_warn = list(g['warnings'])
res = {'which': which, 'parts': len(parts), 'seconds': dt, 'pass': g['pass'], 'errors': len(msgs_err), 'warnings': len(msgs_warn), 'first_errors': msgs_err[:8], 'first_warnings': msgs_warn[:8]}
with open(os.path.join(out, f'gate_{which}.json'), 'w') as f:
    json.dump(res, f, indent=1, default=str)
print('GATE', json.dumps(res, default=str)[:3500])
