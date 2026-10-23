"""What this does: the SURFACE PASS, the first and biggest piece of the treatment. For every object it writes UVs first, then gives it a real material made from its
role's surface recipe (data/surfaces.json): a soft height picture turned into a real OpenGL normal map (Non-Color, tangent space, wired UV Map to Mapping to
Image to Normal Map to the Principled node), colour that varies across the surface and from object to object, roughness that varies, a second look-up at another
scale blended in by slow noise so the repeat does not show, real displacement where the role says (roads, mud, thatch, rock ground) on a mesh fine enough to
show it, and rounded edges (bevel with hardened normals). Plain-colour materials are replaced by these (the original is kept, with a fake user, and remembered
on the object so undo can put it back); materials that already carry their own maps (a downloaded prop, a lettered sign) are KEPT: their picture is never changed, but they get what they lack (roughness that varies,
a normal map from the role's surface) as extra nodes named "PK augment ..." that undo takes out again, and the wear pass adds its layers on top.
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
from . import bevel, displacement, heights, normals, scans, uvs

MATERIAL_VERSION = 4
BEVEL_CLASSES = ('wall', 'timber', 'iron', 'stone', 'prop', 'roof', 'floor')       # roles whose objects get rounded edges (ground, water, glass, plants and trees do not)
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
    from_image = any(node_in_chain.type == 'TEX_IMAGE' for node_in_chain in material_inspect.upstream_nodes(principled.inputs['Base Color']))
    return not from_image


AUGMENT_KEY = 'pk_augment'


def augment_kept_material(material, role, surface_id, spec, size, quick=False):
    """A kept material (it carries its own picture) keeps its picture, and gets what it lacks: roughness that varies (a noise across the surface, between the surface's own low and
    high roughness) when nothing varies its roughness, and a normal map from the surface's recipe when it has none (UV Map -> Mapping -> Image -> Normal Map -> Principled Normal).
    Every node added is marked pk_augment, so undo takes them out. Returns a list of plain sentences about what was added (empty when it already had both)."""
    from ..checks import material_inspect
    principled = material_inspect.principled_of(material)
    if principled is None or material.node_tree is None:
        return []
    facts = material_inspect.inspect_material(material)
    tree = material.node_tree
    before = set(node.name for node in tree.nodes)
    net = Net(tree)
    said = []
    tile = float(settings_file.number(spec['tile_metres']))
    if not facts['roughness_variation'] and not principled.inputs['Roughness'].links:
        macro = net.noise(_scale_vector(net, net.geometry().outputs['Position'], 1.0 / float(settings_file.number(spec['colour']['variation']['macro_scale_metres']))), scale=1.0, detail=4.0)
        low, high = float(settings_file.number(spec['roughness']['low'])), float(settings_file.number(spec['roughness']['high']))
        tree.links.new(net.map_range(net.clamp01(macro), 0.0, 1.0, low, high), principled.inputs['Roughness'])
        said.append(f'{material.name}: roughness now varies across the surface')
    if not facts['normal_map']['has'] and not principled.inputs['Normal'].links:
        nor_image, _height_image, _, _ = make_maps(surface_id, spec, size, quick)
        uv = net.new('ShaderNodeUVMap')
        uv.uv_map = 'UVMap'
        mapping = net.new('ShaderNodeMapping')
        mapping.inputs['Scale'].default_value = (1.0 / tile, 1.0 / tile, 1.0)
        tree.links.new(uv.outputs['UV'], mapping.inputs['Vector'])
        normal_map = net.new('ShaderNodeNormalMap')
        normal_map.space = 'TANGENT'
        normal_map.uv_map = 'UVMap'
        normal_map.inputs['Strength'].default_value = float(settings_file.number(spec['normal_strength']))
        tree.links.new(net.image(nor_image, mapping.outputs['Vector'], 'Non-Color', 'Cubic'), normal_map.inputs['Color'])
        tree.links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
        said.append(f'{material.name}: a normal map from the {surface_id} surface was added (its own picture is untouched)')
    for node in tree.nodes:
        if node.name not in before:
            node[AUGMENT_KEY] = 1
            node.label = 'PK augment'
    return said


def remove_augment(material):
    """Takes out every node augment_kept_material added (undo). Returns how many."""
    if material.node_tree is None:
        return 0
    found = [node for node in material.node_tree.nodes if AUGMENT_KEY in node.keys()]
    for node in found:
        material.node_tree.nodes.remove(node)
    return len(found)


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
    net = Net(tree)
    output = net.new('ShaderNodeOutputMaterial')
    output.is_active_output = True
    principled = net.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Coat Roughness'].default_value = COAT_ROUGHNESS
    tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    tile = float(settings_file.number(spec['tile_metres']))
    seed_value = net.attr(names.SEED)
    hiding = {k: house_numbers.value(f'place_surfaces.repeat_hiding.{k}') for k in ('second_scale', 'offset', 'blend_noise_scale')}

    uv = net.new('ShaderNodeUVMap')
    uv.uv_map = 'UVMap'

    def mapping(scale, extra_x=0.0, extra_y=0.0):
        node = net.new('ShaderNodeMapping')
        node.inputs['Scale'].default_value = (scale / tile, scale / tile, 1.0)
        tree.links.new(uv.outputs['UV'], node.inputs['Vector'])
        # each object starts at its own place in the picture (so two boards from one material do not match)
        shift = net.combine(net.math('ADD', net.math('MULTIPLY', seed_value, 7.31), extra_x), net.math('ADD', net.math('MULTIPLY', seed_value, 3.77), extra_y), 0.0)
        tree.links.new(shift, node.inputs['Location'])
        return node.outputs['Vector']

    first = mapping(1.0)
    second = mapping(float(hiding['second_scale']), float(hiding['offset'][0]), float(hiding['offset'][1]))
    slow = net.noise(first, scale=float(hiding['blend_noise_scale']) * 12.0, detail=1.0)
    blend = net.smoothstep(slow, 0.35, 0.65)
    normal_colour = net.mix_colour(blend, net.image(nor_image, first, 'Non-Color', 'Cubic'), net.image(nor_image, second, 'Non-Color', 'Cubic'))
    height_a = net.sep_rgb(net.image(height_image, first, 'Non-Color', 'Linear'))[0]
    height_b = net.sep_rgb(net.image(height_image, second, 'Non-Color', 'Linear'))[0]
    height_value = net.mix(blend, height_a, height_b)

    strength = float(settings_file.number(spec['normal_strength']))
    depth = settings_file.number(spec['displacement_depth_metres']) if (displace and spec.get('displacement_depth_metres')) else None
    if depth:
        strength *= house_numbers.value('place_surfaces.normal_strength_with_displacement_factor')
    normal_map = net.new('ShaderNodeNormalMap')
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
    position = net.geometry().outputs['Position']
    macro = net.noise(_scale_vector(net, position, 1.0 / macro_scale), scale=1.0, detail=3.0)
    fac = net.clamp01(net.math('ADD', net.math('MULTIPLY', macro, 0.55), net.math('MULTIPLY', height_value, 0.45)))
    stops = [(i / max(len(palette) - 1, 1), hex_to_linear(c)) for i, c in enumerate(palette)]
    colour = net.color_ramp(fac, stops)
    tinted = net.hue_saturation_value(colour, value=net.math('ADD', 1.0, net.math('MULTIPLY', net.math('SUBTRACT', seed_value, 0.5), 2.0 * per_object)))
    tree.links.new(tinted, principled.inputs['Base Color'])
    low, high = settings_file.number(spec['roughness']['low']), settings_file.number(spec['roughness']['high'])
    rough = net.map_range(net.clamp01(net.math('ADD', net.math('MULTIPLY', height_value, 0.5), net.math('MULTIPLY', macro, 0.5))), 0.0, 1.0, float(low), float(high))
    tree.links.new(rough, principled.inputs['Roughness'])
    if depth:
        displacement.set_displacement(material, height_value, float(depth), tree)
    else:
        material.displacement_method = 'BUMP'
    material[names.MADE] = 1
    mean_colour = [sum(c[i] for c in (hex_to_linear(h) for h in palette)) / max(len(palette), 1) for i in range(3)]
    for key, value in (('pk_surface', surface_id), ('pk_role', role), ('pk_size', size), ('pk_version', MATERIAL_VERSION), ('pk_source', 'made_in_code'),
                       ('pk_mean_colour', mean_colour)):
        material[key] = value
    return material


def _scale_vector(net, vector, factor):
    node = net.new('ShaderNodeVectorMath')
    node.operation = 'SCALE'
    net.tree.links.new(vector, node.inputs[0])
    node.inputs['Scale'].default_value = factor
    return node.outputs[0]


COAT_ROUGHNESS = 0.15          # a wet film is never a mirror (the Principled default of 0.03 over a bumpy surface made white sparkles in a damp place)


def build_scan_material(role, surface_id, spec, scan, pictures, displace, settings_quick=False):
    """Makes (or rebuilds in place) the material 'PK <role> / <surface>' from a PHOTOGRAPHED scan (scans.py): the scan's colour picture (with slow colour change
    across the surface and a little per object), its OpenGL normal map into a tangent Normal Map node, its roughness map, and its height map into real displacement
    where the role says. Each picture is read twice, at two sizes and offsets, blended by slow noise, so the repeat does not show; the tile is the scan's REAL size.
    The wear layers go on top of it in the next pass like on any other material. Returns the material."""
    name = names.material_name(role, surface_id)
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.use_nodes = True
    if hook.BASE_KEY in material.keys():
        del material[hook.BASE_KEY]
    tree = material.node_tree
    tree.nodes.clear()
    net = Net(tree)
    output = net.new('ShaderNodeOutputMaterial')
    output.is_active_output = True
    principled = net.new('ShaderNodeBsdfPrincipled')
    principled.inputs['Coat Roughness'].default_value = COAT_ROUGHNESS
    tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    tile = float(scan.get('metres') or settings_file.number(spec['tile_metres']))
    seed_value = net.attr(names.SEED)
    hiding = {k: house_numbers.value(f'place_surfaces.repeat_hiding.{k}') for k in ('second_scale', 'offset', 'blend_noise_scale')}
    turn = (spec.get('scan_grain') == 'v' and spec.get('uv_method') == 'plank')      # a plank's u runs along its length; this scan's grain runs up the picture
    uv = net.new('ShaderNodeUVMap')
    uv.uv_map = 'UVMap'

    def mapping(scale, extra_x=0.0, extra_y=0.0, angle=0.0):
        node = net.new('ShaderNodeMapping')
        node.inputs['Scale'].default_value = (scale / tile, scale / tile, 1.0)
        node.inputs['Rotation'].default_value = (0.0, 0.0, angle + (1.5707963 if turn else 0.0))
        tree.links.new(uv.outputs['UV'], node.inputs['Vector'])
        shift = net.combine(net.math('ADD', net.math('MULTIPLY', seed_value, 7.31), extra_x), net.math('ADD', net.math('MULTIPLY', seed_value, 3.77), extra_y), 0.0)
        tree.links.new(shift, node.inputs['Location'])
        return node.outputs['Vector']

    first = mapping(1.0)
    second = mapping(float(hiding['second_scale']), float(hiding['offset'][0]), float(hiding['offset'][1]), 0.0)
    slow = net.noise(first, scale=float(hiding['blend_noise_scale']) * 12.0, detail=1.0)
    blend = net.smoothstep(slow, 0.35, 0.65)
    colour = net.mix_colour(blend, net.image(pictures['colour'], first, 'sRGB', 'Linear'), net.image(pictures['colour'], second, 'sRGB', 'Linear'))
    normal_colour = net.mix_colour(blend, net.image(pictures['normal'], first, 'Non-Color', 'Linear'), net.image(pictures['normal'], second, 'Non-Color', 'Linear'))
    height_value = None
    if pictures.get('height') is not None:
        height_value = net.mix(blend, net.sep_rgb(net.image(pictures['height'], first, 'Non-Color', 'Linear'))[0],
                               net.sep_rgb(net.image(pictures['height'], second, 'Non-Color', 'Linear'))[0])
    strength = float(settings_file.number(spec['normal_strength']))
    depth = settings_file.number(spec['displacement_depth_metres']) if (displace and spec.get('displacement_depth_metres') and height_value is not None) else None
    if depth:
        strength *= house_numbers.value('place_surfaces.normal_strength_with_displacement_factor')
    normal_map = net.new('ShaderNodeNormalMap')
    normal_map.space = 'TANGENT'
    normal_map.uv_map = 'UVMap'
    normal_map.inputs['Strength'].default_value = strength
    tree.links.new(normal_colour, normal_map.inputs['Color'])
    tree.links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
    # colour: the photograph, a slow change of value across the surface and a little per object (the scan brings the detail; the place decides nothing else)
    per_object = float(settings_file.number(spec['colour']['variation']['per_object']))
    macro_scale = float(settings_file.number(spec['colour']['variation']['macro_scale_metres']))
    macro = net.noise(_scale_vector(net, net.geometry().outputs['Position'], 1.0 / macro_scale), scale=1.0, detail=3.0)
    mean_colour = list(pictures.get('colour_mean') or (0.2, 0.18, 0.15))
    pull = float(settings_file.number(spec['scan_colour_pull'])) if spec.get('scan_colour_pull') else 0.0
    if pull > 0:                 # the scene decides this surface's mean colour, the scan brings the detail (a grass scan is dry and olive; a living verge is greener)
        palette = settings_file.number(spec['colour']['palette'])
        target = [sum(hex_to_linear(h)[i] for h in palette) / max(len(palette), 1) for i in range(3)]
        factor = [(t / max(m, 1e-4)) ** pull for t, m in zip(target, mean_colour)]
        colour = net.mix_colour(1.0, colour, net.comb_rgb(*factor), blend='MULTIPLY')
        mean_colour = [m * f for m, f in zip(mean_colour, factor)]
    varied = net.hue_saturation_value(colour, value=net.math('ADD', net.math('ADD', 0.92, net.math('MULTIPLY', macro, 0.16)),
                                                             net.math('MULTIPLY', net.math('SUBTRACT', seed_value, 0.5), 2.0 * per_object)))
    tree.links.new(varied, principled.inputs['Base Color'])
    if pictures.get('roughness') is not None:
        rough_picture = net.sep_rgb(net.mix_colour(blend, net.image(pictures['roughness'], first, 'Non-Color', 'Linear'), net.image(pictures['roughness'], second, 'Non-Color', 'Linear')))[0]
        rough = net.clamp01(net.math('ADD', rough_picture, net.math('MULTIPLY', net.math('SUBTRACT', macro, 0.5), 0.1)))
    else:
        low, high = settings_file.number(spec['roughness']['low']), settings_file.number(spec['roughness']['high'])
        rough = net.map_range(net.clamp01(net.math('ADD', net.math('MULTIPLY', height_value if height_value is not None else macro, 0.5), net.math('MULTIPLY', macro, 0.5))), 0.0, 1.0, float(low), float(high))
    tree.links.new(rough, principled.inputs['Roughness'])
    if depth:
        displacement.set_displacement(material, height_value, float(depth), tree, midlevel=float(pictures.get('height_mean') or 0.5))
    else:
        material.displacement_method = 'BUMP'
    material[names.MADE] = 1
    for key, value in (('pk_surface', surface_id), ('pk_role', role), ('pk_size', int(pictures['normal'].size[0])), ('pk_version', MATERIAL_VERSION),
                       ('pk_source', f'{scan["source"]}:{scan["id"]}'), ('pk_scan_metres', tile), ('pk_mean_colour', mean_colour)):
        material[key] = value
    return material


def give_surfaces(settings, owner=None, map_size=None, quick=False, maps_folder=None):
    """The surface pass (see the note at the top). Returns a report: {'summary', 'materials': [names], 'map_size_pixels', 'bevelled', 'displacement', 'looks': [...]}."""
    table = settings_file.roles_table()
    rules = settings.rules_dict()
    size = int(map_size or house_numbers.value('place_surfaces.map_size_quick_pixels' if quick else 'place_surfaces.map_size_pixels'))
    objects = [o for o in scene_read.mesh_objects(only_visible=True) if not scene_read.is_scatter(o)]
    facts = [scene_read.object_facts(o) for o in objects]
    tagged = roles_module.tag_objects(facts, rules, table)['by_object']
    made, replaced, kept, uv_written, bevel_items, displaced, notes, kept_names = {}, 0, 0, 0, [], [], [], []
    chosen_scans, prepared, sources, fallbacks = {}, {}, {}, {}

    def scan_for(slot_role, surface_id, spec):
        """The photographed scan for a role and surface (the person's library, then Poly Haven), prepared once; (scan, pictures) or (None, None) with the reason kept."""
        key = (slot_role, surface_id)
        if key not in chosen_scans:
            scan, said = scans.choose_scan(slot_role, surface_id, spec, settings, quick=quick)
            pictures = None
            if scan is not None:
                try:
                    if scan['key'] not in prepared:
                        prepared[scan['key']] = scans.prepare_images(scan)
                    pictures = prepared[scan['key']]
                    if pictures.get('turned'):
                        notes.append(f'{scan["id"]}: its normal map pointed the other way along {", ".join(pictures["turned"])} (checked against its own height map); a corrected copy is used')
                except (scans.ScanUnavailable, RuntimeError, OSError) as problem:
                    said = f'the scan {scan["id"]} could not be read ({problem}), so the made-in-code surface is used'
                    scan, pictures = None, None
            chosen_scans[key] = (scan, pictures)
            if scan is None:
                fallbacks[f'{slot_role} / {surface_id}'] = said
        return chosen_scans[key]

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
            wants_bevel = bool(surface_id and (roles_module.role_class(slot_role) in BEVEL_CLASSES or spec.get('bevel_metres'))) and not roles_module.off_entries_for(slot_role, 'bevelled_edges', rules)
            if not should_replace(slot.material):
                kept += 1
                kept_names.append(slot.material.name)
                notes.extend(augment_kept_material(slot.material, slot_role, surface_id, spec, size, quick))
                if wants_bevel:                          # the object's edges are rounded whatever its material is
                    bevel_items.append((obj, surface_id))
                continue
            displace = bool(table['roles'].get(slot_role, {}).get('displace')) and not roles_module.off_entries_for(slot_role, 'displacement', rules)
            key = (slot_role, surface_id, displace)
            if key not in made:
                scan, pictures = scan_for(slot_role, surface_id, spec)
                if scan is not None:
                    made[key] = build_scan_material(slot_role, surface_id, spec, scan, pictures, displace, quick)
                    sources[made[key].name] = f'{scan["source"]}:{scan["id"]}'
                else:
                    made[key] = build_surface_material(slot_role, surface_id, spec, size, displace, quick)
                    sources[made[key].name] = 'made_in_code'
            if slot.material is not None and not slot.material.name.startswith(names.MATERIAL_PREFIX):
                if not slot.material.use_fake_user:
                    slot.material['pk_fake_added'] = 1
                slot.material.use_fake_user = True
            slot.material = made[key]
            replaced += 1
            displace_here = displace_here or displace
            if wants_bevel:                              # every hard-edged thing is rounded, not only the roles that REQUIRE it (steps, coping, crates and iron straps too)
                bevel_items.append((obj, surface_id))
        if displace_here:                        # the mesh is made fine BEFORE its UVs are written (a regraded ground starts with none)
            notes.append(displacement.prepare_mesh(obj))
            displaced.append(obj.name)
        if first_surface is not None:
            method = settings_file.surface(first_surface)['uv_method']
            layer, wrote = uvs.ensure_uvs(obj, method)
            uv_written += int(wrote)
    seed_module.write_object_values([o for o in objects if tagged[o.name]['role'] and not roles_module.is_never(tagged[o.name]['role'])])
    if str((settings.get('pack_surface_pictures', True))).lower() not in ('false', '0', 'no'):
        scans.pack_images([image for pictures in prepared.values() for image in (pictures['colour'], pictures['normal'], pictures['roughness'], pictures['height'])])
    for line in sorted(set(fallbacks.values())):
        notes.append('made-in-code surface: ' + line)
    run_record.write(map_size_pixels=size, quick=bool(quick) or bool(run_record.read().get('quick') and not run_record.read().get('finished')),
                     surface_sources=dict(sorted(sources.items())), surface_fallbacks=dict(sorted(fallbacks.items())))
    widths = bevel.bevel_objects(list({o.name: (o, s) for o, s in bevel_items}.values()))
    if maps_folder:
        os.makedirs(maps_folder, exist_ok=True)
        for image in [i for i in bpy.data.images if i.name.startswith('pk_') and (i.name.endswith('_nor') or i.name.endswith('_height'))]:
            array = normals.image_to_array(image)
            normals.write_png(os.path.join(maps_folder, image.name + '.png'), np.rint(array[..., :3] * 255).astype(np.uint8))
    bpy.context.view_layer.update()
    photographed = sorted({v for v in sources.values() if v != 'made_in_code'})
    in_code = sum(1 for v in sources.values() if v == 'made_in_code')
    summary = (f'{len(made)} material(s) made for {len({k[0] for k in made})} role(s): {len(made) - in_code} from photographed scans'
               + (f' ({", ".join(p.split(":", 1)[1] for p in photographed[:6])})' if photographed else '') + f', {in_code} made in code; '
               f'{replaced} slot(s) replaced, {kept} kept (they carry their own maps); '
               f'normal maps {size} px, {uv_written} object(s) got UVs, {sum(1 for w in widths.values() if w)} bevelled, displacement on {len(displaced)} object(s)'
               + (f'; kept (own picture): {", ".join(sorted(set(kept_names))[:6])}' if kept_names else ''))
    return {'summary': summary, 'materials': sorted(m.name for m in made.values()), 'map_size_pixels': size, 'bevelled': sorted(k for k, v in widths.items() if v),
            'displacement': displaced, 'looks': notes, 'replaced_slots': replaced, 'kept_slots': kept, 'kept_materials': sorted(set(kept_names)),
            'sources': dict(sorted(sources.items())), 'fallbacks': dict(sorted(fallbacks.items()))}
