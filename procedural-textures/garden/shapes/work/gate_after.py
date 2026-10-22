# usage: blender -b courtyard_final.blend -P gate_after.py -- LOOK OUT.json [apply=1/0]
# Runs the Scenario delivery gate (profile render, 1 mm distances) like scene/scripts/run_gate_courtyard.py, after applying stage_shapes (or not).
import sys, json, time
sys.dont_write_bytecode = True
HERE = 'proc-work/garden/shapes'
sys.path.insert(0, HERE)
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-expert/scripts')
import bpy, bx_audit, stage_shapes
a = sys.argv[sys.argv.index('--') + 1:]
look, out = a[0], a[1]
do_apply = (a[2] == '1') if len(a) > 2 else True
if do_apply:
    stage_shapes.apply({'look': look})
bpy.context.view_layer.update()
dist = 0.001
LEAVE_OUT = ('Hills,', 'Dark plain', 'Courtyard ground source', 'CT / Ceramic pan prototype')
SCATTER = ('Maple leaves', 'Maple inner mass', 'Pine pads', 'Bamboo leaves', 'Fallen leaves', 'Lily pads', 'Lotus blossoms', 'Astra / moss grouped bodies', 'Astra / pebbles grouped bodies', 'Bamboo stalks')
meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render and not any(o.name.startswith(p) for p in LEAVE_OUT)]
main = [o.name for o in meshes if o.name not in SCATTER and o.name != 'Hall roof']
res = {'look': look, 'applied': do_apply, 'groups': {}}
def run(label, names):
    t = time.time()
    r = bx_audit.deliverable(names, profile='render', eps=dist, tol=dist, gap=dist)
    r['seconds'] = round(time.time() - t, 1); r['n_objects'] = len(names)
    res['groups'][label] = r
    print('GATE', label, 'objects', len(names), 'pass', r['pass'], 'errors', len(r['errors']), 'warnings', len(r['warnings']), 'sec', r['seconds'], flush=True)
    for e in r['errors'][:40]: print('    E', e[:230])
    for e in r['warnings'][:10]: print('    W', e[:230])
run('main', main)
roof = bpy.data.objects['Hall roof']
ng = roof.modifiers[0].node_group.copy()
nodes, links = ng.nodes, ng.links
outn = next(n for n in nodes if n.bl_idname == 'NodeGroupOutput')
src = outn.inputs[0].links[0].from_socket
rz = nodes.new('GeometryNodeRealizeInstances'); links.new(src, rz.inputs['Geometry']); links.new(rz.outputs['Geometry'], outn.inputs[0])
cp = roof.copy(); cp.data = roof.data.copy(); bpy.context.scene.collection.objects.link(cp)
cp.modifiers[0].node_group = ng; cp.name = 'ROOF_REALIZED_COPY'
bpy.context.view_layer.update()
carry = [n for n in ('Roof carrying frame', 'Hall beams', 'Hall posts', 'Hall plaster', 'Eave soffit') if n in bpy.data.objects]
run('roof_with_walls_and_beams', ['ROOF_REALIZED_COPY'] + carry)
json.dump(res, open(out, 'w'), indent=1, default=str)
