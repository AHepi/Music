# What this does: runs the Scenario expert skill's delivery check (bx_audit.deliverable) on the courtyard scene, in groups, because the skill
#   says to gate separate props one by one and skips the floating checks above 5000 loose pieces (the leaf scatters have far more).
#   Leaves out the three hazy hill ridges, the 400 m dark plain, the hidden ground source and the hidden roof-tile prototype (the street try-out's lesson),
#   and sets the three distances (z-fight, touch, float) to the same value (default 1 mm). Changes and saves nothing in the .blend.
#   The roof is made of 688 instanced tiles that the check cannot see, so a throwaway copy of the roof gets a "Realize Instances" node (in memory only).
# Run: xvfb-run -a blender -b --disable-autoexec --factory-startup FILE.blend -P run_gate_courtyard.py -- OUT.json PROFILE DIST_M
import sys, json, time
sys.dont_write_bytecode = True
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-expert/scripts')
import bpy, bx_audit
a = sys.argv[sys.argv.index('--') + 1:]
out, profile = a[0], a[1]
dist = None if a[2] == '-' else float(a[2])

LEAVE_OUT = ('Hills,', 'Dark plain', 'Courtyard ground source', 'CT / Ceramic pan prototype')
SCATTER = ('Life / moss at feet and damp edges', 'Life / pebble fringe', 'Life / tufts', 'Maple leaves', 'Maple inner mass', 'Pine pads', 'Bamboo leaves', 'Fallen leaves', 'Lily pads', 'Lotus blossoms',
           'Astra / moss grouped bodies', 'Astra / pebbles grouped bodies', 'Bamboo stalks')
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render and not any(o.name.startswith(p) for p in LEAVE_OUT)]
main = [o.name for o in meshes if o.name not in SCATTER and o.name != 'Hall roof']
res = {'profile': profile, 'dist_m': dist, 'groups': {}}

def run(label, names):
    t = time.time()
    r = bx_audit.deliverable(names, profile=profile, eps=dist, tol=dist, gap=dist)
    r['seconds'] = round(time.time() - t, 1); r['n_objects'] = len(names)
    res['groups'][label] = r
    print('GATE', label, 'objects', len(names), 'pass', r['pass'], 'errors', len(r['errors']), 'warnings', len(r['warnings']), 'sec', r['seconds'], flush=True)

run('main', main)

# the roof: realize the instanced tiles on a throwaway copy
roof = bpy.data.objects['Hall roof']
ng = roof.modifiers[0].node_group.copy()
nodes, links = ng.nodes, ng.links
outn = next(n for n in nodes if n.bl_idname == 'NodeGroupOutput')
src = outn.inputs[0].links[0].from_socket
rz = nodes.new('GeometryNodeRealizeInstances'); links.new(src, rz.inputs['Geometry']); links.new(rz.outputs['Geometry'], outn.inputs[0])
cp = roof.copy(); cp.data = roof.data.copy(); bpy.context.scene.collection.objects.link(cp)
cp.modifiers[0].node_group = ng; cp.name = 'ROOF_REALIZED_COPY'
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
me = cp.evaluated_get(dg).to_mesh()
print('roof realized: verts', len(me.vertices), 'faces', len(me.polygons), 'materials', [m.name if m else None for m in me.materials])
cp.evaluated_get(dg).to_mesh_clear()
run('roof_realized_copy', ['ROOF_REALIZED_COPY'])
run('roof_with_walls_and_beams', ['ROOF_REALIZED_COPY', 'Hall beams', 'Hall posts', 'Hall plaster', 'Eave soffit'])

for n in SCATTER:
    if n in bpy.data.objects: run('scatter: ' + n, [n])

json.dump(res, open(out, 'w'), indent=1, default=str)
print('GATE_DONE', out)
