"""Tiny test: objects named the way a newcomer names them, with NO role rule and NO place_role: what role does the kit guess and does the construction check pass?"""
import sys, bpy, bmesh
KIT = '/home/user/Music/plugins/explainer-film/kit/place-kit'
sys.path.insert(0, KIT)
from place_kit import settings_file, names, roles as roles_module, scene_read
from place_kit.checks import construction

def box(name, x0, x1, y0, y1, z0, z1, role=None):
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 if v.co.x < 0 else x1; v.co.y = y0 if v.co.y < 0 else y1; v.co.z = z0 if v.co.z < 0 else z1
    mesh = bpy.data.meshes.new(name); bm.to_mesh(mesh); bm.free()
    obj = bpy.data.objects.new(name, mesh); bpy.context.scene.collection.objects.link(obj)
    if role: obj[names.ROLE] = role
    return obj

for o in list(bpy.data.objects): bpy.data.objects.remove(o)
box('Bank earth', -10, 30, -10, 10, -0.5, 0.0, 'ground.earth')
box('Reeds on the bank', 0, 0.4, 0, 0.4, 0.0, 1.2)
box('Fish boxes stack', 3, 3.6, 0, 0.5, 0.0, 1.0)
box('Waterwheel', 6, 6.4, 0, 4.0, 0.0, 4.0)
settings = settings_file.Settings({})
table = settings_file.roles_table()
objs = [o for o in scene_read.mesh_objects(only_visible=True) if not o.name.startswith('Bank')]
tag = roles_module.tag_objects([scene_read.object_facts(o) for o in objs], {}, table)['by_object']
result = construction.check_construction({})
for o in objs:
    f = result['objects'][o.name]
    print('HINT %-20s role=%-14s carried=%s floating=%s gap_mm=%s' % (o.name, tag[o.name]['role'], f.get('carried'), f.get('floating'), f.get('gap_mm')))
