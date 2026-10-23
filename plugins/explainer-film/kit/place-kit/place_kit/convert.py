"""What this does: finds everything in a scene that is DRAWN but is not a mesh, and turns it into meshes, so that the surface and wear pass (which only works on meshes) cannot
be escaped by building a rope from a bevelled curve, a sign from text, a blob from a metaball, or a prop by instancing a collection. Four kinds are handled:
  curve, text, nurbs surface, metaball: the shape Blender draws (after bevel and extrusion) is copied into a new mesh object with the same place, collections, materials and custom
    properties (place_role, place_owner). A curve with no bevel or extrusion draws nothing and is left alone (it is reported as "draws nothing").
  an empty that instances a collection: every mesh object of the collection is copied into the scene (with its own copy of the mesh) at the place the instance shows it, and
    the empty is hidden.
The new mesh has its touching points joined (a text mesh comes out as loose caps and sides, and a loose cap would float in the construction check). The original object is kept, hidden (not drawn, not in the viewport) and marked pk_converted_to, and the new object is marked pk_made and pk_converted_from, so `undo` removes the
new object and shows the original again. Objects tagged with a never role (helpers, lights, sky) are left alone on purpose. Running it twice changes nothing (the originals are
hidden, so they are not found again). It needs Blender (bpy).
A concrete example: a rope made from a bevelled curve "rope 1" becomes the mesh object "rope 1" (the curve is kept as "rope 1 (curve)" and hidden); an empty "Barrel instance"
that instances the collection "barrel" becomes one mesh object per object in that collection.
"""
import bmesh
import bpy
from mathutils import Matrix

from . import names, roles as roles_module, scene_read, settings_file

CONVERTIBLE_TYPES = ('CURVE', 'FONT', 'SURFACE', 'META')
OTHER_DRAWN_TYPES = ('CURVES', 'POINTCLOUD', 'VOLUME', 'GREASEPENCIL')     # drawn, but not turned into meshes by this kit: reported


def _facts_of(obj):
    materials = [slot.material.name for slot in obj.material_slots if slot.material is not None]
    return {'name': obj.name, 'collections': [c.name for c in obj.users_collection], 'materials': materials, 'properties': scene_read.custom_properties(obj)}


def _is_never(obj, rules, table):
    return roles_module.is_never(roles_module.tag_object(_facts_of(obj), rules, table)['role'] or '')


def drawn_mesh_for(obj):
    """A new mesh with what Blender draws for this object (bevel, extrusion and modifiers applied), or None when it draws no faces."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, preserve_all_data_layers=True, depsgraph=depsgraph)
    if mesh is None or len(mesh.polygons) == 0:
        if mesh is not None:
            bpy.data.meshes.remove(mesh)
        return None
    # text and curves come out with their caps and sides as loose pieces (a cap that is not joined to its sides would be judged on its own, and float): join what touches
    work = bmesh.new()
    work.from_mesh(mesh)
    bmesh.ops.remove_doubles(work, verts=work.verts, dist=1e-4)
    work.to_mesh(mesh)
    work.free()
    mesh.update()
    return mesh


def instancing_empties(scene=None):
    scene = scene or bpy.context.scene
    return [o for o in scene.objects if o.type == 'EMPTY' and o.instance_type == 'COLLECTION' and o.instance_collection is not None and scene_read.is_visible(o)]


def find_unconverted(settings, scene=None):
    """The visible things that are drawn but are not meshes and carry no never role: [{'name', 'type', 'what'}]. A curve that draws nothing is not listed."""
    scene = scene or bpy.context.scene
    rules, table = settings.rules_dict(), settings_file.roles_table()
    found = []
    for obj in scene.objects:
        if not scene_read.is_visible(obj) or obj.get(names.MADE):
            continue
        if obj.type in CONVERTIBLE_TYPES:
            if _is_never(obj, rules, table):
                continue
            mesh = drawn_mesh_for(obj)
            if mesh is None:
                continue
            bpy.data.meshes.remove(mesh)
            found.append({'name': obj.name, 'type': obj.type.lower(), 'what': f'a {obj.type.lower()} object that draws faces'})
        elif obj.type in OTHER_DRAWN_TYPES:
            if not _is_never(obj, rules, table):
                found.append({'name': obj.name, 'type': obj.type.lower(), 'what': f'a {obj.type.lower()} object (this kit cannot turn it into a mesh: convert it yourself or tag it never.helper)'})
        elif obj.type == 'EMPTY' and obj.instance_type == 'COLLECTION' and obj.instance_collection is not None:
            if not _is_never(obj, rules, table):
                found.append({'name': obj.name, 'type': 'instance', 'what': f'an empty that instances the collection "{obj.instance_collection.name}"'})
    return found


def _copy_properties(source, target):
    for key in source.keys():
        if key.startswith('_'):
            continue
        value = source[key]
        if isinstance(value, (int, float, str, bool)):
            target[key] = value


def _hide(obj, converted_to):
    obj.hide_render = True
    obj.hide_viewport = True
    obj['pk_converted_to'] = converted_to
    try:
        obj.hide_set(True)
    except RuntimeError:
        pass


def convert_to_meshes(settings, scene=None):
    """Turns every drawn non-mesh object into meshes (see the note at the top). Returns {'converted': [names], 'realized': [names], 'left': [{'name', 'why'}], 'summary': text}."""
    scene = scene or bpy.context.scene
    rules, table = settings.rules_dict(), settings_file.roles_table()
    converted, realized, left = [], [], []
    bpy.context.view_layer.update()
    for obj in list(scene.objects):
        if obj.get(names.MADE) or not scene_read.is_visible(obj):
            continue
        if obj.type in CONVERTIBLE_TYPES:
            if _is_never(obj, rules, table):
                continue
            mesh = drawn_mesh_for(obj)
            if mesh is None:
                left.append({'name': obj.name, 'why': 'draws nothing (no bevel, extrusion or fill), so there is no surface to give'})
                continue
            original_name = obj.name
            new = bpy.data.objects.new(original_name, mesh)
            for collection in obj.users_collection:
                collection.objects.link(new)
            if obj.parent is not None:
                new.parent = obj.parent
                new.matrix_parent_inverse = obj.matrix_parent_inverse.copy()
            new.matrix_world = obj.matrix_world.copy()
            for slot_material in obj.data.materials if hasattr(obj.data, 'materials') else []:
                if slot_material is not None and slot_material.name not in [m.name for m in mesh.materials if m]:
                    mesh.materials.append(slot_material)
            _copy_properties(obj, new)
            new[names.MADE] = 1
            new['pk_converted_from'] = original_name
            obj.name = original_name + ' (' + obj.type.lower() + ')'
            new.name = original_name
            _hide(obj, new.name)
            converted.append(new.name)
        elif obj.type == 'EMPTY' and obj.instance_type == 'COLLECTION' and obj.instance_collection is not None:
            if _is_never(obj, rules, table):
                continue
            collection = obj.instance_collection
            offset = Matrix.Translation(-collection.instance_offset)
            made_here = 0
            for source in collection.all_objects:
                if source.type != 'MESH':
                    continue
                copy = source.copy()
                copy.data = source.data.copy()
                for key in [k for k in copy.keys() if k.startswith('pk_')]:
                    del copy[key]
                for linked in list(copy.users_collection):
                    linked.objects.unlink(copy)
                for linked in obj.users_collection:
                    linked.objects.link(copy)
                copy.parent = None
                copy.matrix_world = obj.matrix_world @ offset @ source.matrix_world
                _copy_properties(obj, copy)
                copy[names.MADE] = 1
                copy['pk_converted_from'] = obj.name
                copy.name = f'{obj.name} {source.name}'
                copy.hide_render = False
                copy.hide_viewport = False
                realized.append(copy.name)
                made_here += 1
            if made_here:
                _hide(obj, f'{made_here} object(s)')
            else:
                left.append({'name': obj.name, 'why': f'its collection "{collection.name}" holds no mesh object'})
    bpy.context.view_layer.update()
    summary = f'{len(converted)} curve, text or metaball object(s) turned into meshes, {len(realized)} instanced object(s) copied into the scene' + (f', {len(left)} left alone' if left else '')
    return {'converted': converted, 'realized': realized, 'left': left, 'summary': summary}


def restore_originals():
    """For undo: shows again every original that convert_to_meshes hid, and returns how many. (The new objects are pk_made, so undo removes them itself.)"""
    count = 0
    for obj in bpy.data.objects:
        if 'pk_converted_to' in obj.keys():
            obj.hide_render = False
            obj.hide_viewport = False
            try:
                obj.hide_set(False)
            except RuntimeError:
                pass
            if obj.name.endswith(')') and ' (' in obj.name:
                base = obj.name[:obj.name.rindex(' (')]
                if bpy.data.objects.get(base) is None:
                    obj.name = base
            del obj['pk_converted_to']
            count += 1
    return count
