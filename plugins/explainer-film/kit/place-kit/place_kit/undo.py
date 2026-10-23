"""What this does: UNDO for the whole pass: removes everything the kit added and puts back what it replaced, using the marks it left (pk_made on what it created, pk_original_materials on
objects, pk_base on materials, pk_base_z on ground meshes, pk_original_mesh on regraded ground). Plain materials come back into their slots (the originals were kept with a fake user, because
Blender drops data nothing uses when a file is saved: 58 materials once vanished that way), the kit's materials, node groups, pictures, text blocks, textures, scattered pieces, lights and
the "PK made" collection go, kit modifiers come off, a leaned post stands as it did, shaped road ground is put back (and a regraded ground mesh is swapped for the one it replaced), and the
kit's per-object numbers and the scene record are cleared. What a builder made (the objects, their roles and owners) is never touched. Safe to run twice. It needs Blender (bpy).
A concrete example: after finish, undo_finish() leaves the hut with its original "wall_mat" colour materials, no extra node groups or images, and the same object list as before.
"""
import json

import bpy
from mathutils import Matrix

from . import convert, names, run_record
from .wear import hook


def _restore_slots(obj):
    """Puts back the materials an object had before the kit (its slots, in order). Returns True when it had a record."""
    raw = obj.get(names.ORIGINAL_MATERIALS)
    if not raw:
        return False
    originals = json.loads(raw)
    for slot, name in zip(obj.material_slots, originals):
        material = bpy.data.materials.get(name) if name else None
        if name is None or material is not None:
            slot.material = material
    return True


def _restore_materials(report):
    for obj in bpy.data.objects:
        if _restore_slots(obj):
            report['materials_restored'] += 1


def undo_finish():
    """Removes what the kit added and restores what it replaced (see the note at the top). Returns {'summary', counts}."""
    report = {'materials_restored': 0, 'objects_removed': 0, 'materials_removed': 0, 'groups_removed': 0, 'images_removed': 0, 'modifiers_removed': 0, 'ground_restored': 0, 'originals_shown': 0}
    # imported materials that got layers: take them off first
    from .surfaces import materials as surface_materials
    for material in bpy.data.materials:
        if material.node_tree is not None and hook.BASE_KEY in material.keys():
            hook.restore_base(material)
            del material[hook.BASE_KEY]
        if material.node_tree is not None:
            surface_materials.remove_augment(material)         # what a kept material was given (roughness variation, a normal map) goes again
    _restore_materials(report)
    for obj in list(bpy.data.objects):
        if obj.get(names.MADE):
            # read what is needed about the object's data BEFORE the object is removed: Blender may free a light's or a camera's data together with its object, and a freed
            # datablock cannot be read (this once crashed undo on a scene where the kit had added the sun)
            data_name = obj.data.name if obj.data is not None else None
            data_kind = obj.type
            bpy.data.objects.remove(obj, do_unlink=True)
            report['objects_removed'] += 1
            if data_name is None:
                continue
            collection = {'MESH': bpy.data.meshes, 'LIGHT': bpy.data.lights, 'CAMERA': bpy.data.cameras}.get(data_kind)
            leftover = collection.get(data_name) if collection is not None else None
            if leftover is not None and leftover.users == 0:
                collection.remove(leftover)
    report['originals_shown'] = convert.restore_originals()      # curves, text and instances the kit turned into meshes come back (the new meshes were pk_made and are gone)
    for obj in bpy.data.objects:
        for modifier in list(obj.modifiers):
            if modifier.name.startswith('PK '):
                obj.modifiers.remove(modifier)
                report['modifiers_removed'] += 1
        if names.SHAPE_DAMAGE in obj.keys() and 'pk_matrix_before_damage' in obj.keys():
            obj.matrix_world = Matrix(json.loads(obj['pk_matrix_before_damage']))
        if obj.type == 'MESH':
            original = obj.get('pk_original_mesh')
            if original and bpy.data.meshes.get(original) is not None and obj.data.name != original:
                graded = obj.data
                obj.data = bpy.data.meshes[original]
                obj.data.use_fake_user = False
                if graded.users == 0:
                    bpy.data.meshes.remove(graded)
                report['ground_restored'] += 1
                _restore_slots(obj)               # the mesh that comes back kept the kit's material in its slot: put the original there too
            mesh = obj.data
            if 'pk_base_z' in mesh.attributes:
                import numpy as np
                count = len(mesh.vertices)
                flat = np.empty(count * 3)
                mesh.vertices.foreach_get('co', flat)
                coords = flat.reshape(count, 3)
                base = np.empty(count, dtype=np.float32)
                mesh.attributes['pk_base_z'].data.foreach_get('value', base)
                coords[:, 2] = base
                mesh.vertices.foreach_set('co', coords.ravel())
                mesh.attributes.remove(mesh.attributes['pk_base_z'])
                if 'pk_rut' in mesh.attributes:
                    mesh.attributes.remove(mesh.attributes['pk_rut'])
                mesh.update()
        for key in [k for k in obj.keys() if k.startswith('pk_') and k != 'pk_fallback_role']:
            del obj[key]
        if obj.get('pk_fallback_role'):
            del obj['pk_fallback_role']
            if names.ROLE in obj.keys():
                del obj[names.ROLE]
    for material in list(bpy.data.materials):
        if names.is_kit_material(material.name) or material.get(names.MADE):
            bpy.data.materials.remove(material)
            report['materials_removed'] += 1
        elif material.get('pk_fake_added'):
            material.use_fake_user = False
            del material['pk_fake_added']
    for group in list(bpy.data.node_groups):
        if names.is_kit_node_group(group.name) or group.name.endswith('(old)'):
            bpy.data.node_groups.remove(group)
            report['groups_removed'] += 1
    for image in list(bpy.data.images):
        if names.is_kit_image(image.name) or image.get(names.MADE):
            bpy.data.images.remove(image)
            report['images_removed'] += 1
    for block in list(bpy.data.texts):
        if block.name.startswith('pk_roots_'):
            bpy.data.texts.remove(block)
    for texture in list(bpy.data.textures):
        if texture.name.startswith('PK Damage'):
            bpy.data.textures.remove(texture)
    for light in list(bpy.data.lights):
        if light.name.startswith('PK ') and light.users == 0:
            bpy.data.lights.remove(light)
    for world in list(bpy.data.worlds):
        if world.get(names.MADE):
            for scene in bpy.data.scenes:
                if scene.world == world:
                    scene.world = None
            bpy.data.worlds.remove(world)
    collection = bpy.data.collections.get(names.MADE_COLLECTION)
    if collection is not None and not collection.objects:
        bpy.data.collections.remove(collection)
    run_record.clear()
    report['summary'] = (f'{report["objects_removed"]} object(s), {report["materials_removed"]} material(s), {report["groups_removed"]} node group(s), {report["images_removed"]} picture(s) removed; '
                         f'{report["originals_shown"]} curve, text or instance original(s) shown again, '
                         f'{report["materials_restored"]} object(s) got their own materials back, {report["modifiers_removed"]} modifier(s) taken off, {report["ground_restored"]} ground mesh(es) swapped back')
    return report
