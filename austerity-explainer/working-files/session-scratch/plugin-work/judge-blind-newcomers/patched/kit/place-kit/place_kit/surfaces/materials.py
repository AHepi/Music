"""What this does: the SURFACE PASS, the first and biggest piece of the treatment. For every object it writes UVs first, then gives it a real material made from its
role's surface recipe (data/surfaces.json): a soft height picture turned into a real OpenGL normal map (Non-Color, tangent space, wired UV Map to Mapping to
Image to Normal Map to the Principled node), colour that varies across the surface and from object to object, roughness that varies, a second look-up at another
scale blended in by slow noise so the repeat does not show, real displacement where the role says (roads, mud, thatch, rock ground) on a mesh fine enough to
show it, and rounded edges (bevel with hardened normals). Plain-colour materials are replaced by these (the original is kept, with a fake user, and remembered
on the object so undo can put it back); materials that already carry their own maps (a downloaded prop) are kept and only get what they lack later.
Geometry and normal maps lead; the wear layers (the next pass) stay calm on top (decision D6 of the 1.4.0 design).
A material is shared by every object with the same role and surface, named "PK <role> / <surface>"; running the pass twice rebuilds the same materials in place.
It needs Blender (bpy) and numpy. A concrete example: give_surfaces(settings) turns the plain "wall_mat" of a hut into "PK wall.plaster / plaster_lime" with a
normal map of fine plaster blotches at 1.5 m tile, and the audit then finds normal_map, roughness_variation and colour_variation on it.
"""
import json
import os

import numpy as np

import bpy

from .. import house_numbers, names, roles as roles_module, run_record, scene_read, settings_file
from ..wear import hook, seed as seed_module
from ..wear.nodes import Net
from . import bevel, displacement, heights, normals, uvs

MATERIAL_VERSION = 3
SURFACE_TILT_DEGREES = 30.0


def surface_for_role(role, settings, roles_table, override=None):
    """The surface id for a role: a settings rule's surface, else the role's own, else a generic fallback by class."""
    if override:
        return override
    spec = roles_table['roles'].get(role)
    if spec and spec.get('surface'):
        return spec['surface']
    klass = roles_module.role_class(role)
    return {'timber': 'generic_wood', 'stone': 'generic_stone', 'iron': 'generic_metal', 'prop': 'generic_stone'}.get(klass, 'generic_stone')


def rule_surface(settings, role, name):
    """A role rule of the settings may name a surface for the objects it matches."""
    for rule in settings.get('roles') or []:
        if rule.get('role') == role and rule.get('surface'):
            return rule['surface']
    return None


def should_replace(material):
    """True for a missing material, a kit material (rebuilt in place) or a plain one; False for a material that already carries its own maps (a prop)."""
    if material is None:
        return True
    if material.name.startswith(names.MATERIAL_PREFIX):
        return True
    if material.node_tree is None:
        return True
    from ..checks import material_inspect
    facts = material_inspect.inspect_material(material)
    if not facts.get('principled'):
        return True
    if facts['normal_map']['has']:
        return False
    principled = material_inspect.principled_of(material)
    from_image = any(n.type == 'TEX_IMAGE' for n in material_inspect.upstream_nodes(principled.inputs['Base Color']))
    return not from_image


def make_maps(surface_id, spec, size, quick=False):
    """The surface's two pictures in Blender: the OpenGL normal map and the height picture (0..1). Returns (normal image, height image, height array, normal array).
    Pictures of the same size already in the file are reused (idempotent)."""
    recipe = spec['height_recipe']
    tile = settings_file.number(spec['tile_metres'])
    seed = abs(hash_text(surface_id)) % 10000
    nor_name, height_name = names.normal_image_name(surface_id), names.height_image_name(surface_id)
    existing_nor, existing_height = bpy.data.images.get(nor_name), bpy.data.images.get(height_name)
    if existing_nor is not None and existing_height is not None and tuple(existing_nor.size) == (size, size) and tuple(existing_height.size) == (size, size) and existing_nor.get('pk_recipe') == recipe:
        return existing_nor, existing_height, None, None
    tilt = float(np.mean(house_numbers.value('place_surfaces.steepest_one_percent_tilt_degrees')))
    height = heights.make_height(recipe, size, seed, tile)
    blur = house_numbers.value('place_surfaces.height_blur_pixels_at_2048')
    height = heights.blur(height, float(np.mean(blur)) * size / 2048.0)
    calibrated = heights.calibrate_height(height, tilt)
    normal = normals.height_to_normal(calibrated, 1.0, tile=True)
    nor_image = normals.make_normal_image(nor_name, normal)
    nor_image['pk_recipe'] = recipe
    height_image = normals.make_height_image(height_name, heights.normalise_unit(height))
    height_image['pk_recipe'] = recipe
    normals.pack(nor_image)
    normals.pack(height_image)
    return nor_image, height_image, height, normal


def hash_text(text):
    return int.from_bytes(__import__('hashlib').md5(text.encode()).digest()[:4], 'big')


def hex_to_linear(hex_colour):
    text = hex_colour.lstrip('#')
    values = [int(text[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
    return (linear[0], linear[1], linear[2], 1.0)


def build_surface_material(role, surface_id, spec, size, displace, quick=False):
    """Makes (or rebuilds in place) the material 'PK <role> / <surface>' with the node graph described in the note at the top. Returns it."""
    name = names.material_name(role, surface_id)
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.use_nodes = True
    if hook.BASE_KEY in material.keys():       # the material is rebuilt from nothing, so what the hook remembered about it no longer applies
        del material[hook.BASE_KEY]
    tree = material.node_tree
    tree.nodes.clear()
    nor_image, height_image, _, _ = make_maps(surface_id, spec, size, quick)
    n = Net(tree)
    output = n.new('ShaderNodeOutputMaterial')
    output.is_active_output = True
    principled = n.new('ShaderNodeBsdfPrincipled')
    tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    tile = float(settings_file.number(spec['tile_metres']))
    seed_value = n.attr(names.SEED)
    hiding = {k: house_numbers.value(f'place_surfaces.repeat_hiding.{k}') for k in ('second_scale', 'offset', 'blend_noise_scale')}

    uv = n.new('ShaderNodeUVMap')
    uv.uv_map = 'UVMap'

    def mapping(scale, extra_x=0.0, extra_y=0.0):
        node = n.new('ShaderNodeMapping')
        node.inputs['Scale'].default_value = (scale / tile, scale / tile, 1.0)
        tree.links.new(uv.outputs['UV'], node.inputs['Vector'])
        # each object starts at its own place in the picture (so two boards from one material do not match)
        shift = n.combine(n.math('ADD', n.math('MULTIPLY', seed_value, 7.31), extra_x), n.math('ADD', n.math('MULTIPLY', seed_value, 3.77), extra_y), 0.0)
        tree.links.new(shift, node.inputs['Location'])
        return node.outputs['Vector']

    first = mapping(1.0)
    second = mapping(float(hiding['second_scale']), float(hiding['offset'][0]), float(hiding['offset'][1]))
    slow = n.noise(first, scale=float(hiding['blend_noise_scale']) * 12.0, detail=1.0)
    blend = n.smoothstep(slow, 0.35, 0.65)
    normal_colour = n.mix_colour(blend, n.image(nor_image, first, 'Non-Color', 'Cubic'), n.image(nor_image, second, 'Non-Color', 'Cubic'))
    height_a = n.sep_rgb(n.image(height_image, first, 'Non-Color', 'Linear'))[0]
    height_b = n.sep_rgb(n.image(height_image, second, 'Non-Color', 'Linear'))[0]
    height_value = n.mix(blend, height_a, height_b)

    strength = float(settings_file.number(spec['normal_strength']))
    depth = settings_file.number(spec['displacement_depth_metres']) if (displace and spec.get('displacement_depth_metres')) else None
    if depth:
        strength *= house_numbers.value('place_surfaces.normal_strength_with_displacement_factor')
    normal_map = n.new('ShaderNodeNormalMap')
    normal_map.space = 'TANGENT'
    normal_map.uv_map = 'UVMap'
    normal_map.inputs['Strength'].default_value = strength
    tree.links.new(normal_colour, normal_map.inputs['Color'])
    tree.links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])

    # colour: the palette, steered by slow world-space noise and by the height (cavities darker), then a little per object
    colour_spec = spec['colour']
    palette = settings_file.number(colour_spec['palette'])
    macro_scale = float(settings_file.number(colour_spec['variation']['macro_scale_metres']))
    per_object = float(settings_file.number(colour_spec['variation']['per_object']))
    position = n.geometry().outputs['Position']
    macro = n.noise(_scale_vector(n, position, 1.0 / macro_scale), scale=1.0, detail=3.0)
    fac = n.clamp01(n.math('ADD', n.math('MULTIPLY', macro, 0.55), n.math('MULTIPLY', height_value, 0.45)))
    stops = [(i / max(len(palette) - 1, 1), hex_to_linear(c)) for i, c in enumerate(palette)]
    colour = n.color_ramp(fac, stops)
    tinted = n.hsv(colour, value=n.math('ADD', 1.0, n.math('MULTIPLY', n.math('SUBTRACT', seed_value, 0.5), 2.0 * per_object)))
    tree.links.new(tinted, principled.inputs['Base Color'])
    low, high = settings_file.number(spec['roughness']['low']), settings_file.number(spec['roughness']['high'])
    rough = n.map_range(n.clamp01(n.math('ADD', n.math('MULTIPLY', height_value, 0.5), n.math('MULTIPLY', macro, 0.5))), 0.0, 1.0, float(low), float(high))
    tree.links.new(rough, principled.inputs['Roughness'])
    if depth:
        displacement.set_displacement(material, height_value, float(depth), tree)
    else:
        material.displacement_method = 'BUMP'
    material[names.MADE] = 1
    for key, value in (('pk_surface', surface_id), ('pk_role', role), ('pk_size', size), ('pk_version', MATERIAL_VERSION)):
        material[key] = value
    return material


def _scale_vector(n, vector, factor):
    node = n.new('ShaderNodeVectorMath')
    node.operation = 'SCALE'
    n.tree.links.new(vector, node.inputs[0])
    node.inputs['Scale'].default_value = factor
    return node.outputs[0]


def give_surfaces(settings, owner=None, map_size=None, quick=False, maps_folder=None):
    """The surface pass (see the note at the top). Returns a report: {'summary', 'materials': [names], 'map_size_pixels', 'bevelled', 'displacement', 'looks': [...]}."""
    table = settings_file.roles_table()
    rules = settings.rules_dict()
    size = int(map_size or house_numbers.value('place_surfaces.map_size_quick_pixels' if quick else 'place_surfaces.map_size_pixels'))
    objects = [o for o in scene_read.mesh_objects(only_visible=True) if not scene_read.is_scatter(o)]
    facts = [scene_read.object_facts(o) for o in objects]
    tagged = roles_module.tag_objects(facts, rules, table)['by_object']
    made, replaced, kept, uv_written, bevel_items, displaced, notes = {}, 0, 0, 0, [], [], []
    for obj in objects:
        if owner is not None and obj.get(names.OWNER) != owner and not (obj.get(names.ROLE) or '').startswith('ground.'):
            continue
        info = tagged[obj.name]
        role = info['role']
        if role is None or roles_module.is_never(role):
            continue
        slot_roles = info['slot_roles']
        if not obj.material_slots:
            obj.data.materials.append(None)
        if names.ORIGINAL_MATERIALS not in obj.keys():
            obj[names.ORIGINAL_MATERIALS] = json.dumps([s.material.name if s.material else None for s in obj.material_slots])
        if len(set(slot_roles)) > 1:
            obj[names.SLOT_ROLES] = json.dumps(slot_roles)
        first_surface = None
        displace_here = False
        for index, slot in enumerate(obj.material_slots):
            slot_role = slot_roles[index] if index < len(slot_roles) else role
            if roles_module.is_never(slot_role):
                continue
            surface_id = surface_for_role(slot_role, settings, table, rule_surface(settings, slot_role, obj.name))
            spec = settings_file.surface(surface_id)
            first_surface = first_surface or surface_id
            if not should_replace(slot.material):
                kept += 1
                continue
            displace = bool(table['roles'].get(slot_role, {}).get('displace')) and not roles_module.off_entries_for(slot_role, 'displacement', rules)
            key = (slot_role, surface_id, displace)
            if key not in made:
                made[key] = build_surface_material(slot_role, surface_id, spec, size, displace, quick)
            if slot.material is not None and not slot.material.name.startswith(names.MATERIAL_PREFIX):
                if not slot.material.use_fake_user:
                    slot.material['pk_fake_added'] = 1
                slot.material.use_fake_user = True
            slot.material = made[key]
            replaced += 1
            displace_here = displace_here or displace
            if surface_id and (table['roles'].get(slot_role, {}).get('class') in ('wall', 'timber', 'iron') or spec.get('bevel_metres')):
                if 'bevelled_edges' in roles_module.requirements(slot_role, table, rules)['required'] and not roles_module.off_entries_for(slot_role, 'bevelled_edges', rules):
                    bevel_items.append((obj, surface_id))
        if displace_here:                        # the mesh is made fine BEFORE its UVs are written (a regraded ground starts with none)
            notes.append(displacement.prepare_mesh(obj))
            displaced.append(obj.name)
        if first_surface is not None:
            method = settings_file.surface(first_surface)['uv_method']
            layer, wrote = uvs.ensure_uvs(obj, method)
            uv_written += int(wrote)
    seed_module.write_object_values([o for o in objects if tagged[o.name]['role'] and not roles_module.is_never(tagged[o.name]['role'])])
    run_record.write(map_size_pixels=size, quick=bool(quick) or bool(run_record.read().get('quick') and not run_record.read().get('finished')))
    widths = bevel.bevel_objects(list({o.name: (o, s) for o, s in bevel_items}.values()))
    if maps_folder:
        os.makedirs(maps_folder, exist_ok=True)
        for image in [i for i in bpy.data.images if i.name.startswith('pk_') and (i.name.endswith('_nor') or i.name.endswith('_height'))]:
            array = normals.image_to_array(image)
            normals.write_png(os.path.join(maps_folder, image.name + '.png'), np.rint(array[..., :3] * 255).astype(np.uint8))
    bpy.context.view_layer.update()
    summary = (f'{len(made)} material(s) made for {len({k[0] for k in made})} role(s), {replaced} slot(s) replaced, {kept} kept (they carry their own maps); '
               f'normal maps {size} px, {uv_written} object(s) got UVs, {sum(1 for w in widths.values() if w)} bevelled, displacement on {len(displaced)} object(s)')
    return {'summary': summary, 'materials': sorted(m.name for m in made.values()), 'map_size_pixels': size, 'bevelled': sorted(k for k, v in widths.items() if v),
            'displacement': displaced, 'looks': notes, 'replaced_slots': replaced, 'kept_slots': kept}
