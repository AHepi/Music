"""What this does: a tiny measured check, no picture drawn. It builds three small scenes of plain boxes with the plugin's own
construction check (the same way the plugin's probe_place.py does): a gallery beam resting on two posts 3.0 m apart, a hall
tie beam resting on two wall blocks 7.0 m apart, and a beam on posts 2.0 m apart as a control, and prints the free span the check
measured and the role's limit, to see whether ordinary real spans fail the check."""
import sys, json
import bpy, bmesh
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
from place_kit import commands
from place_kit.checks import construction

def reset():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    mesh = bpy.data.meshes.new('Ground')
    mesh.from_pydata([(-12, -12, 0), (12, -12, 0), (12, 12, 0), (-12, 12, 0)], [], [(0, 1, 2, 3)])
    bpy.context.scene.collection.objects.link(bpy.data.objects.new('Ground', mesh))

def box(name, size, location):
    mesh = bpy.data.meshes.new(name)
    builder = bmesh.new()
    bmesh.ops.create_cube(builder, size=1.0)
    for vertex in builder.verts:
        vertex.co.x *= size[0]; vertex.co.y *= size[1]; vertex.co.z *= size[2]
    builder.to_mesh(mesh); builder.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    return obj

def run(roles_by_name):
    bpy.context.view_layer.update()
    settings = commands.read_settings(None)
    settings.data['roles'] = [{'role': role, 'match': {'names': ['^' + name + '$']}} for name, role in roles_by_name.items()]
    settings.data['roles'].append({'role': 'ground.earth', 'match': {'names': ['^Ground$']}})
    return construction.check_construction(settings)['objects']

def report(label, objects, beam_name):
    found = objects.get(beam_name) if isinstance(objects, dict) else next((o for o in objects if o.get('name') == beam_name), None)
    found = found or {}
    print('RESULT', label, json.dumps({k: v for k, v in found.items() if 'span' in k or k in ('carried', 'carried_by', 'rests_on', 'framed_in')}, default=str))

for label, gap in (('control: beam on posts 2.0 m apart', 2.0), ('gallery beam on posts 3.0 m apart', 3.0)):
    reset()
    box('post 1', (0.2, 0.2, 2.5), (-gap / 2, 0, 1.25))
    box('post 2', (0.2, 0.2, 2.5), (gap / 2, 0, 1.25))
    box('beam 1', (gap + 0.3, 0.2, 0.25), (0, 0, 2.625))
    report(label, run({'post 1': 'timber.post', 'post 2': 'timber.post', 'beam 1': 'timber.beam'}), 'beam 1')
reset()
box('wall 1', (0.8, 4.0, 4.0), (-3.9, 0, 2.0))
box('wall 2', (0.8, 4.0, 4.0), (3.9, 0, 2.0))
box('beam 1', (8.4, 0.25, 0.3), (0, 0, 4.15))
report('hall tie beam on walls 7.0 m apart', run({'wall 1': 'wall.stone', 'wall 2': 'wall.stone', 'beam 1': 'timber.beam'}), 'beam 1')
