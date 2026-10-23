"""What this does: runs INSIDE Blender (no Pillow there, and this script blocks it on purpose) and checks what model_kit.py makes of a bevelled box and of a textured material:
how much the shading jumps across the bevel (old flat-shaded bevel against the new hardened one), which modifiers the new bevel carries, that a normal map is saved as a PNG
and marked Non-Color, that a colour picture is a PNG when Pillow is missing, and that the .glb file still writes. It prints one line, RESULT followed by a JSON dictionary.
Run: blender -b --python check_bevel.py -- OUT_FOLDER [PICTURE.jpg]
"""
import json
import math
import os
import sys

sys.modules['PIL'] = None                                    # Blender has no Pillow; make this run show that nothing needs it
arguments = sys.argv[sys.argv.index('--') + 1:]
folder = arguments[0]
picture_path = arguments[1] if len(arguments) > 1 else None
sys.path.insert(0, os.environ['MODEL_KIT_FOLDER'])

import bpy  # noqa: E402
import numpy as np  # noqa: E402
import model_kit as mk  # noqa: E402


def biggest_jump_at_a_corner(obj):
    """The biggest angle, in degrees, between two shading normals that meet at the same corner point (a flat-shaded bevel jumps by 45 degrees between its strips)."""
    mesh = obj.data
    by_vertex = {}
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            by_vertex.setdefault(mesh.loops[loop_index].vertex_index, []).append(np.array(mesh.corner_normals[loop_index].vector))
    worst = 0.0
    for normals in by_vertex.values():
        for a in normals:
            for b in normals:
                worst = max(worst, math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(a, b)))))))
    return worst


result = {}
for hardened in (False, True):
    mk.reset()
    mk.HARDEN_BEVEL_NORMALS = hardened
    material = mk.material('slate')
    box = mk.box('block', (2, 2, 2), at=(0, 0, 1), material=material, bevel=0.1)
    names = [(m.type, m.name) for m in box.modifiers]
    harden_flag = [m.harden_normals for m in box.modifiers if m.type == 'BEVEL'][0]
    mk.apply_modifiers(box)
    big_top = max((p for p in box.data.polygons if p.normal.z > 0.99), key=lambda p: p.area)
    top_dots = [float(np.dot(np.array(box.data.corner_normals[l].vector), (0, 0, 1))) for l in big_top.loop_indices]
    result['hardened' if hardened else 'flat'] = {'modifiers_before_apply': names, 'harden_flag': harden_flag, 'jump_degrees': biggest_jump_at_a_corner(box), 'big_face_min_dot': min(top_dots),
                                                  'faces': len(box.data.polygons)}
    if hardened:
        images = {i.name: (os.path.splitext(i.filepath)[1], i.colorspace_settings.name) for i in bpy.data.images}
        result['images'] = images
        glb = os.path.join(folder, 'block.glb')
        mk.finish(glb)
        result['glb_bytes'] = os.path.getsize(glb)
        with open(glb, 'rb') as handle:
            data = handle.read()
        result['glb_has_png'] = b'image/png' in data
        result['glb_has_normals'] = b'NORMAL' in data

if picture_path:
    # a small close picture of the old and the new bevel side by side, a low sun grazing the faces, so a person can look at the difference
    mk.reset()
    scene = bpy.context.scene
    for index, hardened in enumerate((False, True)):
        mk.HARDEN_BEVEL_NORMALS = hardened
        block = mk.box(f'block {index}', (1.6, 1.6, 1.6), at=(index * 2.2 - 1.1, 0, 0.8), material=mk.material(None, name=f'plain {index}', colour=(0.55, 0.5, 0.45), roughness=0.6), bevel=0.12)
    mk.box('ground', (8, 6, 0.1), at=(0, 0, -0.05), material=mk.material(None, name='ground colour', colour=(0.3, 0.3, 0.3)))
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 3.0; sun.rotation_euler = (math.radians(70), 0, math.radians(35))
    scene.collection.objects.link(sun)
    camera = bpy.data.objects.new('camera', bpy.data.cameras.new('camera'))
    camera.location = (0.0, -6.5, 3.2); camera.rotation_euler = (math.radians(68), 0, 0)
    camera.data.lens = 50
    scene.collection.objects.link(camera); scene.camera = camera
    world = bpy.data.worlds.new('world'); world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.5, 0.55, 0.6, 1)
    scene.world = world
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = 480, 320
    scene.eevee.taa_render_samples = 8
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.filepath = picture_path
    bpy.ops.render.render(write_still=True)
    result['picture'] = picture_path

print('RESULT', json.dumps(result))
