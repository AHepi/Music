# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# OPTIONAL part of the painted look: the add-on's own pigment tool (apply_pigment) on the hall's wood and plaster. Used only when stage_surfaces.apply gets
# options['addon_dir'] (the unpacked add-on 0.2.1 folder, read only). What the tool does to an object (tested on Blender 5.2.2, 21 October): it swaps the object's mesh for a
# private copy with identical geometry, gives the object a private material 'PF / <name>' (pigment field on Base Color), and adds one hidden 'Astra / pigment restore handle'
# empty. This stage tags every new object (garden_owner = surfaces, garden_role = handle) and puts them in the collection 'G3 surfaces'.
# It needs the ORIGINAL noise-colour materials (Dark timber, Beam timber, Plaster wall), so stage_surfaces leaves those three alone in the painted look when the tool is used.
import bpy
import os
import sys

TARGETS = [   # object, material it starts from, kind, grain axis, strength
    ('Hall posts', 'timber', 'Z', 0.65), ('Hall beams', 'timber', 'X', 0.65), ('Shoji bars', 'timber', 'Z', 0.55), ('Hall plaster', 'plaster', 'Z', 0.6),
]
ORIGINAL_MATERIALS = ('Dark timber', 'Beam timber', 'Plaster wall')


def ramp_mean(mat):
    """Mean of the colour ramp that feeds the original material (the palette mean 'at today's colour')."""
    if mat is None or mat.node_tree is None:
        return (0.1, 0.06, 0.03)
    for n in mat.node_tree.nodes:
        if n.bl_idname == 'ShaderNodeValToRGB':
            cols = [e.color[:3] for e in n.color_ramp.elements]
            return tuple(sum(c[i] for c in cols) / len(cols) for i in range(3))
    return (0.1, 0.06, 0.03)


def apply(addon_dir, opt):
    sys.dont_write_bytecode = True
    loader_dir = opt.get('loader_dir') or os.path.dirname(os.path.abspath(__file__))     # astra_loader.py is copied next to this file
    if loader_dir not in sys.path:
        sys.path.insert(0, loader_dir)
    from astra_loader import load_astra, apply_blender_52_shim
    api = load_astra(addon_dir)
    apply_blender_52_shim(api)
    collection = bpy.data.collections.get('G3 surfaces') or bpy.data.collections.new('G3 surfaces')
    if collection.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(collection)
    done, failed = [], {}
    for name, kind, axis, strength in TARGETS:
        ob = bpy.data.objects.get(name)
        if ob is None:
            failed[name] = 'object not found'
            continue
        if ob.get('garden_pigment'):
            done.append(name + ' (already)')
            continue
        mat = ob.material_slots[0].material if ob.material_slots else None
        palette = ramp_mean(mat)
        before = {o.name for o in bpy.data.objects}
        try:
            api.apply_pigment(ob, 0, kind, axis, 41, strength, palette_mean=palette)
        except Exception as error:
            failed[name] = repr(error)[:300]
            continue
        ob['garden_pigment'] = 1
        for o in bpy.data.objects:
            if o.name not in before:
                o['garden_owner'] = 'surfaces'
                o['garden_role'] = 'handle'
                for c in list(o.users_collection):
                    c.objects.unlink(o)
                collection.objects.link(o)
        mat_after = ob.material_slots[0].material
        if mat_after is not None:
            mat_after['garden_owner'] = 'surfaces'
            mat_after['garden_family'] = 'pigment.' + kind
            mat_after['garden_look'] = 'painted'
        done.append(name)
    return {'pigment_done': done, 'pigment_failed': failed}
