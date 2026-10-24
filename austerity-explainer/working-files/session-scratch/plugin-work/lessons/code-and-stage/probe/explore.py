import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
mesh = bpy.data.meshes.new('m'); mesh.from_pydata([(0,0,0),(1,0,0),(0,1,0)],[],[(0,1,2)])
obj = bpy.data.objects.new('probe', mesh); bpy.context.scene.collection.objects.link(obj)
tree = bpy.data.node_groups.new('probe group', 'GeometryNodeTree')
tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
sock = tree.interface.new_socket('Size', in_out='INPUT', socket_type='NodeSocketFloat')
tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
i = tree.nodes.new('NodeGroupInput'); o = tree.nodes.new('NodeGroupOutput')
tree.links.new(i.outputs[0], o.inputs[0])
mod = obj.modifiers.new('probe', 'NODES'); mod.node_group = tree
print('identifier', sock.identifier)
print('mod keys skipped')
print('has properties', hasattr(mod, 'properties'))
if hasattr(mod, 'properties'):
    p = mod.properties
    print('properties type', type(p), [a for a in dir(p) if not a.startswith('_')][:40])
    if hasattr(p, 'inputs'):
        ins = p.inputs
        print('inputs type', type(ins), [a for a in dir(ins) if not a.startswith('_')][:60])
        try:
            print('getattr', getattr(ins, sock.identifier))
            item = getattr(ins, sock.identifier)
            print('item dir', [a for a in dir(item) if not a.startswith('_')])
        except Exception as e:
            print('getattr failed', e)
try:
    mod[sock.identifier] = 3.5
    print('item set ok', mod[sock.identifier])
except Exception as e:
    print('item set failed', type(e).__name__, e)
# light linking
coll = bpy.data.collections.new('receivers'); bpy.context.scene.collection.children.link(coll)
a = bpy.data.objects.new('A', mesh); b = bpy.data.objects.new('B', mesh)
coll.objects.link(a); coll.objects.link(b)
ld = bpy.data.lights.new('L','POINT'); lo = bpy.data.objects.new('L', ld); bpy.context.scene.collection.objects.link(lo)
lo.light_linking.receiver_collection = coll
co = coll.collection_objects
print('collection_objects', len(co), [type(x) for x in co])
print('entry dir', [a for a in dir(co[0]) if not a.startswith('_')])
print('ll dir', [a for a in dir(co[0].light_linking) if not a.startswith('_')])
co[1].light_linking.link_state = 'EXCLUDE'
print('states', [x.light_linking.link_state for x in co], [o.name for o in coll.objects])
