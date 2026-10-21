# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# A toolbox that runs INSIDE Blender (the runner b03_render_jobs.py imports it). It holds two things the study needs:
#   1. LIGHTING: five named ways of lighting the street, so every test can be drawn under the same set of conditions (the LIGHTING TEST SET of the study):
#        A  dusk lamps       the street exactly as the film lights it (gas lamps, lit windows, the two dim sky lights; in the lockout shot file also the brazier)
#        B  brazier glare    the lockout shot as the film lights it (it is A in the lockout file; B only means "look at the brazier's glare")
#        C  low side light   the lamps are switched off; one low sun (10 degrees above the horizon) shines across the street from the right. The houses' shadows are
#                            switched off for this one (a real low sun would be blocked by the houses and the road would be dark), so this is an artificial test of
#                            how the road's relief looks under raking light.
#        D  flat overhead    the lamps are switched off; one sun almost straight above (88 degrees). Almost no side shading: the hardest light for a relief picture.
#        E  light from behind  A as it is, plus one strong low light at the far end of the street, shining toward the camera: a glare on every shiny surface.
#      The strength of the sun in C and D is chosen so that the DRY road is about as bright as in A (calibration in the study note), so that a difference in how well
#      the joints show comes from the kind of light, not from how much.
#   2. VARIANTS: one-at-a-time changes to the road material (the diagnosis: change one thing, draw, measure) and the "solutions" tested in the study (a joint picture
#      that keeps the joints dark and dull; real geometry). Each variant is a function that changes the road and RETURNS an "undo" function.
# Nothing here saves any file. Run only through the runner.
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'tools'))      # street_wet/tools: apply_wetness_to_set.py and wetness_layer.py
sys.dont_write_bytecode = True
import apply_wetness_to_set as aw  # noqa: E402

STUDY_WORK = os.path.abspath(os.path.join(HERE, '..', 'work'))

# ------------------------------------------------------------------------------------------------------------------------------- lighting
RIG = {
    # name: (azimuth degrees from +x toward +y, elevation degrees, colour, strength in sun watts per square metre)
    'C': dict(azimuth=-15.0, elevation=10.0, colour=(1.0, 0.86, 0.70), strength=1.0),
    'D': dict(azimuth=0.0, elevation=88.0, colour=(1.0, 0.92, 0.82), strength=0.4),
}
BACK_LIGHT = dict(location=(0.0, 66.0, 5.9), colour=(1.0, 0.78, 0.5), watts=30000.0, radius=0.35)
HOUSE_PREFIXES = ('right_row', 'left_row', 'heapstead', 'engine_house', 'second_winding', 'colliery_chimney', 'headframe', 'spoil_heap')
_ORIGINAL = {}


def _remember():
    if _ORIGINAL:
        return
    for obj in bpy.context.scene.objects:
        if obj.type == 'LIGHT':
            _ORIGINAL[obj.name] = obj.hide_render
        elif obj.type == 'MESH' and obj.name.startswith(HOUSE_PREFIXES):
            _ORIGINAL[obj.name] = obj.visible_shadow


def _rig_object(name, kind):
    obj = bpy.data.objects.get(name)
    if obj is None:
        data = bpy.data.lights.new(name, kind)
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
    return obj


def set_lighting(name, overrides=None):
    """Lights the scene as A, B, C, D or E (see the note at the top). 'B' is the same as 'A'. overrides: {'strength': ...} for the sun rigs."""
    _remember()
    scene = bpy.context.scene
    for obj_name, original in _ORIGINAL.items():
        obj = scene.objects.get(obj_name)
        if obj is None:
            continue
        if obj.type == 'LIGHT':
            obj.hide_render = original
        else:
            obj.visible_shadow = original
    sun = _rig_object('study_sun', 'SUN')
    back = _rig_object('study_back_light', 'POINT')
    sun.hide_render = True
    back.hide_render = True
    if name in ('A', 'B'):
        return
    if name in ('C', 'D'):
        spec = dict(RIG[name])
        spec.update(overrides or {})
        for obj_name in list(_ORIGINAL):
            obj = scene.objects.get(obj_name)
            if obj is not None and obj.type == 'LIGHT' and obj_name not in ('dusk_skylight', 'afterglow'):
                obj.hide_render = True
        if name == 'C':
            for obj_name in list(_ORIGINAL):
                obj = scene.objects.get(obj_name)
                if obj is not None and obj.type == 'MESH':
                    obj.visible_shadow = False
        az, el = math.radians(spec['azimuth']), math.radians(spec['elevation'])
        direction_to_sun = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))
        sun.rotation_euler = direction_to_sun.to_track_quat('Z', 'Y').to_euler()
        sun.data.energy = spec['strength']
        sun.data.color = spec['colour']
        sun.data.angle = math.radians(0.6)
        sun.hide_render = False
        return
    if name == 'E':
        back.location = BACK_LIGHT['location']
        back.data.energy = (overrides or {}).get('watts', BACK_LIGHT['watts'])
        back.data.color = BACK_LIGHT['colour']
        back.data.shadow_soft_size = BACK_LIGHT['radius']
        back.hide_render = False
        return
    raise ValueError('unknown lighting ' + name)


def parse_state(state):
    """'dry' 'wet' 'heavy' or 'w0.85p0.3' (wetness 0.85, puddle dial 0.3)."""
    table = {'dry': (0.0, 0.0), 'wet': (0.85, 0.5), 'heavy': (1.0, 0.8)}
    if state in table:
        return table[state]
    wet, pud = state[1:].split('p')
    return float(wet), float(pud)


# ------------------------------------------------------------------------------------------------------------------------------- road material helpers
def road_group():
    return aw.APPLIED['street_setts'][0]


def road_tree():
    return bpy.data.materials['street_setts'].node_tree


def _set_inputs(group, **values):
    saved = {}
    for key, value in values.items():
        socket = group.inputs[key.replace('_', ' ').title().replace('Ior', 'IOR')]
        saved[socket.name] = socket.default_value
        socket.default_value = value

    def undo():
        for name, value in saved.items():
            group.inputs[name].default_value = value
    return undo


def _normal_map_nodes():
    return [n for n in road_tree().nodes if n.type == 'NORMAL_MAP']


def _mix_float(tree, fac, a, b):
    node = tree.nodes.new('ShaderNodeMix')
    node.data_type = 'FLOAT'
    _feed(tree, node.inputs[0], fac)
    _feed(tree, node.inputs[2], a)
    _feed(tree, node.inputs[3], b)
    return node.outputs[0], [node]


def _feed(tree, socket, value):
    if isinstance(value, bpy.types.NodeSocket):
        tree.links.new(value, socket)
    else:
        socket.default_value = value


def _math(tree, operation, a, b=None):
    node = tree.nodes.new('ShaderNodeMath')
    node.operation = operation
    _feed(tree, node.inputs[0], a)
    if b is not None:
        _feed(tree, node.inputs[1], b)
    return node.outputs[0], node


# ------------------------------------------------------------------------------------------------------------------------------- variants
VARIANTS = {}


def variant(function):
    VARIANTS[function.__name__] = function
    return function


@variant
def baseline(**kw):
    """Round 2 exactly as it is."""
    return lambda: None


@variant
def normal_strength(strength=3.0, **kw):
    """Normal map strength (the road has 1.4): all normal map nodes of the road."""
    nodes = _normal_map_nodes()
    saved = [(n, n.inputs['Strength'].default_value) for n in nodes]
    for n in nodes:
        n.inputs['Strength'].default_value = strength

    def undo():
        for n, v in saved:
            n.inputs['Strength'].default_value = v
    return undo


@variant
def relief_kept(**kw):
    """No Relief Flatten, no Grain Fill: the wet road keeps the sharp dry relief picture at full strength."""
    return _set_inputs(road_group(), relief_flatten=0.0, grain_fill=0.0)


@variant
def relief_flatten_only(**kw):
    return _set_inputs(road_group(), relief_flatten=0.0)


@variant
def grain_fill_off(**kw):
    return _set_inputs(road_group(), grain_fill=0.0)


@variant
def no_film(**kw):
    """No water film and no extra shine: Film Coat 0, Specular Boost 0 (the road keeps wet roughness 0.3 and wet colour)."""
    return _set_inputs(road_group(), film_coat=0.0, specular_boost=0.0)


@variant
def dull_wet(**kw):
    """Wet colour only: roughness stays dry, no film, no extra shine."""
    return _set_inputs(road_group(), film_coat=0.0, specular_boost=0.0, roughness_effect=0.0, coat_effect=0.0)


@variant
def wet_roughness(value=0.9, **kw):
    return _set_inputs(road_group(), wet_roughness=value)


@variant
def dry_tops(value=1.0, **kw):
    return _set_inputs(road_group(), dry_tops=value)


@variant
def normal_off(**kw):
    """The relief picture removed (normal map strength 0 in every normal map node), nothing else changed."""
    return normal_strength(strength=0.0)


@variant
def colour_flat(**kw):
    """The colour picture replaced by its average colour: what is left of the joints comes from relief, wetness, light. (Run it with the dry state too.)"""
    numbers = json.load(open(os.path.join(STUDY_WORK, 'sett_numbers.json')))
    mean = numbers['mean_linear_rgb'] + [1.0]
    tree = road_tree()
    group = road_group()
    link = next(l for l in tree.links if l.to_socket == group.inputs['Colour'])
    mix_node = link.from_node
    colour_socket = next(s for s in mix_node.inputs if s.name == 'A' and s.type == 'RGBA')
    old_links = [(l.from_socket, l.to_socket) for l in tree.links if l.to_socket == colour_socket]
    for l in list(tree.links):
        if l.to_socket == colour_socket:
            tree.links.remove(l)
    old_default = tuple(colour_socket.default_value)
    colour_socket.default_value = mean

    def undo():
        colour_socket.default_value = old_default
        for a, b in old_links:
            tree.links.new(a, b)
    return undo


@variant
def joint_picture(colour_mult=0.45, rough_to=0.95, spec_keep=0.25, coat_keep=0.15, puddle_clear=0.8, picture='joint_cavity.png', **kw):
    """THE SOLUTION TESTED FIRST: a "cavity" picture (1 in the joints, falling to 0 about a centimetre into the stone; made by b01_make_joint_mask.py) laid on the road
    through the road's own texture coordinates, applied AFTER the wetness layer, so wetness cannot wash it out:
      colour  x  (1 down to colour_mult in the joints)          joints stay dark
      roughness  goes to rough_to in the joints                  joints stay dull: no reflection of the lamps or sky
      specular   x  (1 down to spec_keep in the joints)           joints do not shine
      coat       x  (1 down to coat_keep in the joints)           no water film shine in the joints (stone tops keep theirs)
    Inside a PUDDLE the water covers the joints: the dulling of roughness, specular and coat is cut by puddle_clear x the puddle mask (0.8 = almost gone in a puddle), but the
    colour stays dark (you see the dark joint through the water)."""
    tree = road_tree()
    group = road_group()
    principled = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    added = []
    old_links = {}
    for name in ('Base Color', 'Roughness', 'Specular IOR Level', 'Coat Weight'):
        link = next(l for l in tree.links if l.to_socket == principled.inputs[name])
        old_links[name] = (link.from_socket, link.to_socket)
    picture_image = bpy.data.images.load(os.path.join(STUDY_WORK, picture), check_existing=True)
    picture_image.colorspace_settings.name = 'Non-Color'
    image_node = tree.nodes.new('ShaderNodeTexImage')
    image_node.image = picture_image
    image_node.interpolation = 'Linear'
    separate = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(image_node.outputs['Color'], separate.inputs['Color'])
    added += [image_node, separate]
    cavity = separate.outputs['Red']
    surface_cavity = cavity            # the cavity as the SHINE sees it: weaker where a puddle covers the joint
    if puddle_clear:
        cleared, nc1 = _math(tree, 'MULTIPLY', group.outputs['Puddle Mask'], puddle_clear)
        keep_factor, nc2 = _math(tree, 'SUBTRACT', 1.0, cleared)
        surface_cavity, nc3 = _math(tree, 'MULTIPLY', cavity, keep_factor)
        added += [nc1, nc2, nc3]
    # colour (skipped when colour_mult is None)
    if colour_mult is None:
        colour_mult = 1.0
    darker, n1 = _math(tree, 'MULTIPLY', cavity, 1.0 - colour_mult)
    scale, n2 = _math(tree, 'SUBTRACT', 1.0, darker)
    combine = tree.nodes.new('ShaderNodeCombineColor')
    for channel in ('Red', 'Green', 'Blue'):
        tree.links.new(scale, combine.inputs[channel])
    multiplied = tree.nodes.new('ShaderNodeMix')
    multiplied.data_type = 'RGBA'
    multiplied.blend_type = 'MULTIPLY'
    multiplied.inputs[0].default_value = 1.0
    tree.links.new(group.outputs['Colour'], multiplied.inputs[6])
    tree.links.new(combine.outputs['Color'], multiplied.inputs[7])
    tree.links.new(multiplied.outputs[2], principled.inputs['Base Color'])
    added += [n1, n2, combine, multiplied]
    # roughness (skipped when rough_to is None)
    if rough_to is not None:
        rough, nodes = _mix_float(tree, surface_cavity, group.outputs['Roughness'], rough_to)
        tree.links.new(rough, principled.inputs['Roughness'])
        added += nodes
    # specular and coat (each skipped when its keep value is None)
    for output_name, socket_name, keep in (('Specular IOR Level', 'Specular IOR Level', spec_keep), ('Coat Weight', 'Coat Weight', coat_keep)):
        if keep is None:
            continue
        cut, a = _math(tree, 'MULTIPLY', surface_cavity, 1.0 - keep)
        factor, b = _math(tree, 'SUBTRACT', 1.0, cut)
        value, c = _math(tree, 'MULTIPLY', group.outputs[output_name], factor)
        tree.links.new(value, principled.inputs[socket_name])
        added += [a, b, c]

    def undo():
        for n in added:
            tree.nodes.remove(n)
        for name, (a, b) in old_links.items():
            tree.links.new(a, b)
    return undo


def apply_variant(name, args=None):
    return VARIANTS[name](**(args or {}))


# ------------------------------------------------------------------------------------------------------------------------------- the masks (joint / stone / road)
def make_mask_material(cores_path):
    material = bpy.data.materials.new('study_joint_mask')
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    attribute = tree.nodes.new('ShaderNodeAttribute')
    attribute.attribute_type = 'GEOMETRY'
    attribute.attribute_name = 'UVMap'
    image_node = tree.nodes.new('ShaderNodeTexImage')
    image_node.image = bpy.data.images.load(cores_path, check_existing=True)
    image_node.image.colorspace_settings.name = 'Non-Color'
    image_node.interpolation = 'Linear'
    image_node.extension = 'REPEAT'
    tree.links.new(attribute.outputs['Vector'], image_node.inputs['Vector'])
    info = tree.nodes.new('ShaderNodeObjectInfo')
    is_road = tree.nodes.new('ShaderNodeMath')
    is_road.operation = 'COMPARE'
    is_road.inputs[1].default_value = 1.0
    is_road.inputs[2].default_value = 0.1
    tree.links.new(info.outputs['Object Index'], is_road.inputs[0])
    separate = tree.nodes.new('ShaderNodeSeparateColor')
    tree.links.new(image_node.outputs['Color'], separate.inputs['Color'])
    combine = tree.nodes.new('ShaderNodeCombineColor')
    for source, channel in (('Red', 'Red'), ('Green', 'Green')):
        product = tree.nodes.new('ShaderNodeMath')
        product.operation = 'MULTIPLY'
        tree.links.new(separate.outputs[source], product.inputs[0])
        tree.links.new(is_road.outputs[0], product.inputs[1])
        tree.links.new(product.outputs[0], combine.inputs[channel])
    tree.links.new(is_road.outputs[0], combine.inputs['Blue'])
    emission = tree.nodes.new('ShaderNodeEmission')
    tree.links.new(combine.outputs['Color'], emission.inputs['Color'])
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    return material


def render_mask(path, width, height, samples=32):
    """Draws R = joint, G = stone face, B = road (1 on the road, 0 elsewhere) for the current camera, then puts every setting back."""
    scene = bpy.context.scene
    view_layer = bpy.context.view_layer
    keep = dict(engine=scene.render.engine, dither=scene.render.dither_intensity, fmt=scene.render.image_settings.file_format, mode=scene.render.image_settings.color_mode,
                depth=scene.render.image_settings.color_depth, vt=scene.view_settings.view_transform, look=scene.view_settings.look, exposure=scene.view_settings.exposure,
                gamma=scene.view_settings.gamma, rx=scene.render.resolution_x, ry=scene.render.resolution_y, filepath=scene.render.filepath)
    background = scene.world.node_tree.nodes['Background']
    world_keep = (tuple(background.inputs['Color'].default_value), background.inputs['Strength'].default_value)
    road = bpy.data.objects['street_setts']
    old_index = road.pass_index
    road.pass_index = 1
    material = make_mask_material(os.path.join(STUDY_WORK, 'joint_cores.png'))
    aw.mask_settings(scene, width, height)
    scene.cycles.samples = samples
    scene.cycles.pixel_filter_type = 'BOX'
    scene.cycles.filter_width = 1.0
    view_layer.material_override = material
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    view_layer.material_override = None
    road.pass_index = old_index
    scene.render.engine = keep['engine']
    scene.render.dither_intensity = keep['dither']
    scene.render.image_settings.file_format = keep['fmt']
    scene.render.image_settings.color_mode = keep['mode']
    scene.render.image_settings.color_depth = keep['depth']
    scene.view_settings.view_transform = keep['vt']
    scene.view_settings.look = keep['look']
    scene.view_settings.exposure = keep['exposure']
    scene.view_settings.gamma = keep['gamma']
    scene.render.filepath = keep['filepath']
    background.inputs['Color'].default_value = world_keep[0]
    background.inputs['Strength'].default_value = world_keep[1]
    bpy.data.materials.remove(material)


def eevee_setup(width, height, samples, raytracing=True, shadow_rays=4, shadow_steps=16):
    """The plate settings of the round 2 recipe (section 7): ray tracing on, shadow rays 4, steps 16."""
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.eevee.taa_render_samples = samples
    scene.eevee.use_raytracing = raytracing
    scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = shadow_rays, shadow_steps
    if hasattr(scene.eevee, 'shadow_pool_size') and width > 1080:
        scene.eevee.shadow_pool_size = '1024'
        scene.eevee.shadow_resolution_scale = min(1.0, 1080 / width)


# ------------------------------------------------------------------------------------------------------------------------------- real geometry (the second solution tested)
@variant
def geometry(y_min=3.0, y_max=24.0, level=6, depth=0.025, normal_strength_value=None, picture='joint_cavity.png', **kw):
    """THE SECOND SOLUTION TESTED: real geometry. A Geometry Nodes modifier on the road cuts out the part of the road between y_min and y_max (metres along the street),
    cuts every face of it into 4**level small faces ("Subdivide Mesh", simple), and pushes every corner DOWN by depth x the cavity picture (1 in the joints) along the
    surface normal: real grooves between real stones, which catch the light and cast shadows. The rest of the road is left as it was. The material is unchanged (the
    normal map still applies, unless normal_strength_value is given, e.g. 0.0 or 1.4)."""
    road = bpy.data.objects['street_setts']
    tree = bpy.data.node_groups.new('study_geometry_road', 'GeometryNodeTree')
    tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = tree.nodes, tree.links
    group_in = nodes.new('NodeGroupInput')
    group_out = nodes.new('NodeGroupOutput')
    # which faces are near: the face's centre y between y_min and y_max
    position = nodes.new('GeometryNodeInputPosition')
    separate_xyz = nodes.new('ShaderNodeSeparateXYZ')
    links.new(position.outputs['Position'], separate_xyz.inputs[0])
    compare_low = nodes.new('FunctionNodeCompare')
    compare_low.data_type = 'FLOAT'
    compare_low.operation = 'GREATER_THAN'
    links.new(separate_xyz.outputs['Y'], compare_low.inputs[0])
    compare_low.inputs[1].default_value = y_min
    compare_high = nodes.new('FunctionNodeCompare')
    compare_high.data_type = 'FLOAT'
    compare_high.operation = 'LESS_THAN'
    links.new(separate_xyz.outputs['Y'], compare_high.inputs[0])
    compare_high.inputs[1].default_value = y_max
    both = nodes.new('FunctionNodeBooleanMath')
    both.operation = 'AND'
    links.new(compare_low.outputs[0], both.inputs[0])
    links.new(compare_high.outputs[0], both.inputs[1])
    split = nodes.new('GeometryNodeSeparateGeometry')
    split.domain = 'FACE'
    links.new(group_in.outputs[0], split.inputs['Geometry'])
    links.new(both.outputs[0], split.inputs['Selection'])
    subdivide = nodes.new('GeometryNodeSubdivideMesh')
    subdivide.inputs['Level'].default_value = level
    links.new(split.outputs['Selection'], subdivide.inputs['Mesh'])
    # how far down each corner goes: depth x cavity picture at the corner's texture coordinates
    uv = nodes.new('GeometryNodeInputNamedAttribute')
    uv.data_type = 'FLOAT_VECTOR'
    uv.inputs['Name'].default_value = 'UVMap'
    picture_image = bpy.data.images.load(os.path.join(STUDY_WORK, picture), check_existing=True)
    picture_image.colorspace_settings.name = 'Non-Color'
    image_node = nodes.new('GeometryNodeImageTexture')
    image_node.inputs['Image'].default_value = picture_image
    image_node.interpolation = 'Linear'
    image_node.extension = 'REPEAT'
    links.new(uv.outputs['Attribute'], image_node.inputs['Vector'])
    normal = nodes.new('GeometryNodeInputNormal')
    scale = nodes.new('ShaderNodeVectorMath')
    scale.operation = 'SCALE'
    links.new(normal.outputs['Normal'], scale.inputs[0])
    down = nodes.new('ShaderNodeMath')
    down.operation = 'MULTIPLY'
    separate_color = nodes.new('FunctionNodeSeparateColor')
    links.new(image_node.outputs['Color'], separate_color.inputs['Color'])
    links.new(separate_color.outputs['Red'], down.inputs[0])
    down.inputs[1].default_value = -depth
    links.new(down.outputs[0], scale.inputs['Scale'])
    set_position = nodes.new('GeometryNodeSetPosition')
    links.new(subdivide.outputs['Mesh'], set_position.inputs['Geometry'])
    links.new(scale.outputs['Vector'], set_position.inputs['Offset'])
    join = nodes.new('GeometryNodeJoinGeometry')
    links.new(split.outputs['Inverted'], join.inputs['Geometry'])
    links.new(set_position.outputs['Geometry'], join.inputs['Geometry'])
    links.new(join.outputs['Geometry'], group_out.inputs[0])
    modifier = road.modifiers.new('study_geometry', 'NODES')
    modifier.node_group = tree
    undo_strength = (lambda: None)
    if normal_strength_value is not None:
        undo_strength = normal_strength(strength=normal_strength_value)

    def undo():
        undo_strength()
        road.modifiers.remove(modifier)
        bpy.data.node_groups.remove(tree)
    return undo


@variant
def show_masks(**kw):
    """Checking view, not a look: the road drawn as plain light, R = the puddle mask, G = the wet mask, B = 0, in raw numbers (no colour look). Used with the state wanted
    (for example 'wet') to find how much of the joints lie under puddles."""
    scene = bpy.context.scene
    tree = road_tree()
    group = road_group()
    output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
    old_link = next(l for l in tree.links if l.to_socket == output.inputs['Surface'])
    old_from = old_link.from_socket
    emission = tree.nodes.new('ShaderNodeEmission')
    combine = tree.nodes.new('ShaderNodeCombineColor')
    tree.links.new(group.outputs['Puddle Mask'], combine.inputs['Red'])
    tree.links.new(group.outputs['Wet Mask'], combine.inputs['Green'])
    tree.links.new(combine.outputs['Color'], emission.inputs['Color'])
    tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
    keep = (scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, scene.view_settings.gamma)
    scene.view_settings.view_transform = 'Raw'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0

    def undo():
        tree.nodes.remove(emission)
        tree.nodes.remove(combine)
        tree.links.new(old_from, output.inputs['Surface'])
        scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure, scene.view_settings.gamma = keep
    return undo


@variant
def combo(parts=(), **kw):
    """Several variants at once: parts = [[variant name, {arguments}], ...]. They are undone in the opposite order."""
    undos = []
    for name, arguments in parts:
        undos.append(VARIANTS[name](**(arguments or {})))

    def undo():
        for u in reversed(undos):
            u()
    return undo
