# What this does (plain words)
# --------------------------------------------------------------------------------------------------------------------------------------------
# Trial 22d, step 3. Opens street_litter.blend (the street copy plus the litter modifier), exports it with the export skill's presets, lets the skill
# re-import the file in a second background Blender and compare it with the scene, and reads the file's own list of parts (glb_summary).
# One STEP per run (so each is timed on its own):
#   web_instances     the "web" preset (GLB, meshopt compression, WebP pictures), litter left as instances (Realize off)
#   web_realized      the same with the litter's Realize switch ON (instances turned into real mesh before the export)
#   web_realized_cams the same plus the two overrides the film's stage needs (cameras and extras kept)
#   gltf_realized     the plain "gltf" preset (no compression, pictures as they are) for a size comparison
#   webp_only_cams    the "web" preset with the mesh squeezing (meshopt) switched OFF, WebP pictures kept, cameras and extras kept (an override the skill allows)
# Nothing is written into the street files. Run:
#   xvfb-run -a blender -b --disable-autoexec --factory-startup --python-exit-code 1 set_copy/street_litter.blend -P scripts/30_export.py -- STEP OUT_FOLDER
import json
import os
import sys
import time

sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-expert/scripts')
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-export/scripts')
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-geometry-nodes/scripts')
import bpy  # noqa: E402

import bx_export as bxe  # noqa: E402
import bx_gn as G  # noqa: E402

step, out_dir = sys.argv[sys.argv.index('--') + 1:][:2]
os.makedirs(out_dir, exist_ok=True)
host = bpy.data.objects['gutter_litter']
md = host.modifiers['Gutter Litter']
realize = step != 'web_instances'
G.set_inputs(md, {'Realize': realize})
preset = 'gltf' if step.startswith('gltf') else 'web'
over = {'export_cameras': True, 'export_extras': True} if step.endswith('cams') else {}
if step == 'webp_only_cams':
    over['export_meshopt_compression_enable'] = False
path = os.path.join(out_dir, f'street_litter_{step}.glb')
objs = [o.name for o in bpy.context.scene.objects if o.visible_get()]
print('STEP', step, 'preset', preset, 'overrides', over, 'objects', len(objs), 'realize', realize)

t0 = time.time()
before = bxe.inspect_scene(objs)
exp = bxe.export(path, preset, objs, **over)
t_export = round(time.time() - t0, 1)
summ = bxe.glb_summary(path)

import struct  # noqa: E402


def glb_json(p):
    d = open(p, 'rb').read()
    n, _k = struct.unpack_from('<I4s', d, 12)
    return json.loads(d[20:20 + n])


gj = glb_json(path)
node = next((n for n in gj['nodes'] if n.get('name') == 'gutter_litter'), None)
litter_node = {'present': node is not None, 'has_mesh': bool(node and 'mesh' in node)}
if node and 'mesh' in node:
    m = gj['meshes'][node['mesh']]
    litter_node['triangles'] = sum(gj['accessors'][pr['indices']]['count'] // 3 for pr in m['primitives'] if 'indices' in pr)
    litter_node['materials'] = sorted({gj['materials'][pr['material']]['name'] for pr in m['primitives'] if 'material' in pr})
t1 = time.time()
rt_error = None
try:
    rt = bxe.round_trip(path, objs, preset=preset, **over)
except Exception as exc:   # the skill's own comparison can fail (see the report); keep going without the litter host
    rt_error = f'{type(exc).__name__}: {exc}'
    print('ROUND TRIP FAILED', rt_error)
    rt = bxe.round_trip(path, [o for o in objs if o != 'gutter_litter'], preset=preset, **over)
t_round = round(time.time() - t1, 1)
res = {
    'step': step, 'preset': preset, 'overrides': over, 'bytes': exp['bytes'], 'export_seconds': t_export, 'round_trip_seconds': t_round,
    'settings_used': exp['settings'], 'glb_summary': summ,
    'litter_node_in_file': litter_node, 'round_trip_error_with_host': rt_error,
    'round_trip_pass': rt['pass'], 'round_trip_diffs': rt['diffs'][:60], 'round_trip_diff_count': len(rt['diffs']),
    'before_mesh_objects': sum(1 for v in before['objects'].values() if v['type'] == 'MESH'),
    'before_tris': sum(v.get('tris', 0) for v in before['objects'].values()),
    'after_mesh_objects': sum(1 for v in rt['after']['objects'].values() if v['type'] == 'MESH'),
    'after_tris': sum(v.get('tris', 0) for v in rt['after']['objects'].values()),
    'after_other_objects': sorted({v['type'] for v in rt['after']['objects'].values()}),
    'litter_host_before': before['objects'].get('gutter_litter'), 'litter_host_after': rt['after']['objects'].get('gutter_litter'),
}
with open(os.path.join(out_dir, f'result_{step}.json'), 'w') as f:
    json.dump(res, f, indent=1, default=str)
print('RESULT', json.dumps({k: v for k, v in res.items() if k not in ('settings_used', 'round_trip_diffs', 'glb_summary')}, default=str))
print('SUMMARY', json.dumps(summ))
print('DIFFS', json.dumps(rt['diffs'][:12]))
