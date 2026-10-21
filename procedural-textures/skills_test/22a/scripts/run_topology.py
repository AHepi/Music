# What this does: runs the skill's per-object mesh audit (bx_audit.audit + verdict) on every mesh of the street copy except the sky dome and far hills,
# and writes a short table. verdict(deforming=False) because a street set does not bend. Changes and saves nothing in the .blend.
# Run: blender -b --disable-autoexec --factory-startup STREET.blend -P run_topology.py -- OUT.json
import sys, json, time, collections
sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-expert/scripts')
import bpy, bx_audit
out = sys.argv[sys.argv.index('--') + 1]
t = time.time(); rows = {}
for o in bpy.context.scene.objects:
    if o.type != 'MESH' or o.name.startswith(('sky_dome', 'moorland_hills')): continue
    r = bx_audit.audit(o)
    rows[o.name] = {k: r[k] for k in ('faces', 'tris', 'quads', 'ngons', 'quads_pct', 'poles_e3', 'poles_e5plus', 'valence_6plus', 'non_manifold_edges', 'loose_verts', 'loose_edges',
                                      'zero_area_faces', 'duplicate_verts', 'flipped_faces', 'self_intersections', 'boundary_loops', 'dimensions')}
    rows[o.name]['problems'] = bx_audit.verdict(r, deforming=False)
json.dump(rows, open(out, 'w'), indent=1)
c = collections.Counter(); 
for n, r in rows.items():
    for p in r['problems']: c[p.split(' ', 1)[1] if p.split(' ', 1)[0].isdigit() else p] += 1
print('TOPOLOGY objects', len(rows), 'seconds', round(time.time() - t, 1), 'objects with a problem', sum(1 for r in rows.values() if r['problems']), dict(c))
