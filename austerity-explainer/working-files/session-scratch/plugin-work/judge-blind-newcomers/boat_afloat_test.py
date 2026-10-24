"""Tiny test: how does the construction check treat a hull afloat on a flat water plane? Hulls: touching, sunk 0.3 m, hovering 3 cm, and one on the mud."""
import sys, bpy, bmesh
KIT = '/home/user/Music/plugins/explainer-film/kit/place-kit'
sys.path.insert(0, KIT)
from place_kit import settings_file, names
from place_kit.checks import construction

def box(name, x0, x1, y0, y1, z0, z1, role):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 if v.co.x < 0 else x1; v.co.y = y0 if v.co.y < 0 else y1; v.co.z = z0 if v.co.z < 0 else z1
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    obj[names.ROLE] = role; obj[names.OWNER] = 'test'; return obj

def plane(name, x0, x1, y0, y1, z, role):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))]
    bm.faces.new(vs)
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    obj[names.ROLE] = role; obj[names.OWNER] = 'test'; return obj

for o in list(bpy.data.objects): bpy.data.objects.remove(o)
box('seabed', -10, 30, -10, 10, -3.5, -3.0, 'ground.earth')
plane('sea', -10, 30, -10, 10, -0.6, 'water.sea')
box('hull touching water', 0, 4, 0, 1.5, -0.6, 0.4, 'prop.boat')
box('hull sunk 0.3 m', 6, 10, 0, 1.5, -0.9, 0.1, 'prop.boat')
box('hull hovering 3 cm', 12, 16, 0, 1.5, -0.57, 0.43, 'prop.boat')
box('hull on mud', 18, 22, 0, 1.5, -3.0, -2.0, 'prop.boat')
result = construction.check_construction({})
for name, facts in result['objects'].items():
    print('BOAT', name, 'carried=%s floating=%s gap_mm=%s via=%s' % (facts.get('carried'), facts.get('floating'), facts.get('gap_mm'), facts.get('via')))
print('BOAT summary', {k: v for k, v in result['summary'].items() if k in ('floating', 'parts', 'carried')})
