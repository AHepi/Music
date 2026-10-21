# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# It holds the new JOINTS layer for the road setts (Blender code; it runs only inside Blender). A "sett" is one squared stone of the road, a "joint" is the gap between two setts.
# The JOINTS layer is a small packaged recipe (a "node group", like the WETNESS layer) that sits AFTER the wetness layer on the road's material:
#
#      dry look  ->  WETNESS (round 2: water, shine, puddles)  ->  JOINTS (this file)  ->  the road's surface
#
# Because it comes after the wetness layer, the water can no longer wash the joints out: whatever the wetness layer says, the JOINTS layer makes the joints
#   * DARKER        (the colour of the joint is multiplied down; the stone's edge is a little darker too),
#   * DULLER        (the joint loses the water's shine: the roughness goes back toward chalk, the water film and the extra shine are cut), while the stone tops keep their wet shine,
#   * ROUNDED       (the stone's edge slopes down into the joint: a relief picture of a rounded groove is added to whatever relief the wetness layer left, so a stone edge that
#                    faces the light is brighter and one that faces away is darker, in every light; the water cannot smooth it away),
#   and in a PUDDLE the water covers the joint: the dulling and the groove are cut by "Puddle Cover" times the puddle mask, but the dark colour stays (you see the dark
#   joint through the water).
# All of it is driven by two flat pictures made by make_joint_pictures.py and laid on the road through the road's own texture coordinates (they line up dot for dot with the
# road's colour picture): sett_joints_clean.png (red = cavity, blue = halo) and sett_groove_normal_16bit.png (the rounded groove's relief picture).
#
# The controls of the group JOINTS (all numbers; the defaults are in DEFAULTS below):
#   Joint Strength  0..1  the master dial. 0 = the layer does nothing = round 2 exactly. 1 = full.
#   Joint Darkness  0..1  how much darker the middle of a joint is than the stone (0 = the same, 1 = black). The stone's colour is multiplied by 1 - Darkness x Cavity.
#   Joint Wet Darkening 0..1  extra darkness of a joint that is WET (added to Joint Darkness x how wet the spot is, 0 on a dry road): a wet joint holds dark water and mud.
#   Joint Shadow    0..1  how much of the LIGHT never reaches the floor of a joint (a narrow gap is in the shade of its two stones): the whole lit result of the joint, shine included, is
#                         multiplied by 1 - Shadow x Cavity. 0 = off (the default). Tried at 0.25 to 0.7: it makes joints much darker in every light (near contrast 0.6 to 0.9, which the
#                         study's pass line calls a harsh black grid) and cured the lockout shot's heavy-rain middle band only at 0.7, so it is a dial for deeper, blacker joints, not the answer.
#   Joint Dullness  0..1  how far a joint loses the water's shine (0 = keeps it, 1 = roughness back to Joint Dull Roughness, shine cut by Joint Spec Cut, water film cut by Joint Coat Cut).
#   Joint Spec Cut 0..1, Joint Coat Cut 0..1, Joint Dull Roughness 0..1   what 'fully dull' means (defaults 0.35, 0.45, 0.9; see the recipe for the values chosen)
#   Joint Relief    0..2  how steep the stone's rounded edge looks (0 = no groove relief; 1 = the picture as made: 8 mm deep, steepest 51 degrees).
#   Edge Shade      0..1  how much darker the stone's edge, a centimetre or two from the joint, is than the middle of the stone (the look of a stone seated in its bed).
#   Puddle Cover    0..1  how much a puddle's water hides the dulling and the groove (0 = not at all, 1 = fully; 0.8 means a full puddle keeps 20 %).
#   Relief Far Share 0..1, Relief Fade Start, Relief Fade End (metres from the camera)   far away the groove's slopes catch the lamps as single white ticks, so the groove relief is
#                   faded with the distance from the camera: full strength up to Fade Start, down to Far Share of it at Fade End and beyond (chosen 0.10, 5 m, 20 m in round 2; changed to 0.03, 4 m, 20 m for the round 2 plate: the middle distance showed short bright ticks with hooked ends). The dark, dull joint itself
#                   is NOT faded. Far Share 1 = no fade.
#   Photo Relief In Joints 0..1  how much of the PHOTO's own relief (the ragged moss and grit relief inside the joint) is taken away in the joint, so that the clean groove
#                   replaces it (0 = keep it all, 1 = take it all away in the middle of a joint). It stops the stone-edge scribbles of the ragged photo relief in strong glare.
#
# How to put it on: add_joints_to_material(material, wetness_node, ...) after the wetness layer is on (see apply_joints_to_set.py). It is also registered as the test variant
# 'joints_layer' (used by the lighting test set runner through register_variants.py).
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
SETTS = os.path.abspath(os.path.join(HERE, '..'))
ROOT = os.path.abspath(os.path.join(SETTS, '..', '..'))        # street_wet
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.dont_write_bytecode = True
import wetness_layer as wl  # noqa: E402

TREE_NAME = 'JOINTS'
MAPS = os.path.join(SETTS, 'maps')
JOINT_PICTURE = os.path.join(MAPS, 'sett_joints_clean.png')
GROOVE_PICTURE = os.path.join(MAPS, 'sett_groove_normal_16bit.png')
# fixed numbers inside the group (the dials above move how much of each is used)
DULL_ROUGHNESS = 0.9      # a fully dulled joint has this roughness (the dry road's own roughness)
SPEC_CUT = 0.35           # a fully dulled joint loses this share of the specular (shine)
COAT_CUT = 0.45           # ... and this share of the water film
DEFAULTS = dict(strength=1.0, darkness=0.30, dullness=1.0, relief=1.0, edge_shade=0.15, puddle_cover=0.8, photo_relief_in_joints=1.0, spec_cut=SPEC_CUT, coat_cut=COAT_CUT, dull_roughness=DULL_ROUGHNESS, shadow=0.0, wet_darkening=0.0, far_share=0.03, fade_start=3.0, fade_end=10.0)   # round 2 plate fix: was 0.10 / 5 m / 20 m. The checker saw short bright ticks with hooked ends in the middle distance; the checker's own numbers (0.03, 4 m, 20 m) left them, so the fade now starts at 3 m and ends at 10 m
DIAL_SOCKETS = dict(strength='Joint Strength', darkness='Joint Darkness', dullness='Joint Dullness', relief='Joint Relief', edge_shade='Edge Shade', puddle_cover='Puddle Cover',
                    photo_relief_in_joints='Photo Relief In Joints', shadow='Joint Shadow', wet_darkening='Joint Wet Darkening', spec_cut='Joint Spec Cut', coat_cut='Joint Coat Cut', dull_roughness='Joint Dull Roughness', far_share='Relief Far Share', fade_start='Relief Fade Start', fade_end='Relief Fade End')


def build_joints_group():
    existing = bpy.data.node_groups.get(TREE_NAME)
    if existing:
        return existing
    tree = bpy.data.node_groups.new(TREE_NAME, 'ShaderNodeTree')
    inputs = [('Colour', 'NodeSocketColor', (0.5, 0.5, 0.5, 1.0)), ('Roughness', 'NodeSocketFloat', 0.85), ('Specular IOR Level', 'NodeSocketFloat', 0.5),
              ('Coat Weight', 'NodeSocketFloat', 0.0), ('Normal', 'NodeSocketVector', (0.0, 0.0, 1.0)), ('Surface Normal', 'NodeSocketVector', (0.0, 0.0, 1.0)),
              ('Groove Normal', 'NodeSocketVector', (0.0, 0.0, 1.0)), ('Cavity', 'NodeSocketFloat', 0.0), ('Halo', 'NodeSocketFloat', 0.0), ('Puddle Mask', 'NodeSocketFloat', 0.0), ('Wet Mask', 'NodeSocketFloat', 0.0),
              ('Joint Strength', 'NodeSocketFloat', DEFAULTS['strength']), ('Joint Darkness', 'NodeSocketFloat', DEFAULTS['darkness']),
              ('Joint Dullness', 'NodeSocketFloat', DEFAULTS['dullness']), ('Joint Relief', 'NodeSocketFloat', DEFAULTS['relief']),
              ('Edge Shade', 'NodeSocketFloat', DEFAULTS['edge_shade']), ('Puddle Cover', 'NodeSocketFloat', DEFAULTS['puddle_cover']),
              ('Photo Relief In Joints', 'NodeSocketFloat', DEFAULTS['photo_relief_in_joints']), ('Joint Shadow', 'NodeSocketFloat', DEFAULTS['shadow']), ('Joint Wet Darkening', 'NodeSocketFloat', DEFAULTS['wet_darkening']), ('Joint Spec Cut', 'NodeSocketFloat', DEFAULTS['spec_cut']),
              ('Joint Coat Cut', 'NodeSocketFloat', DEFAULTS['coat_cut']), ('Joint Dull Roughness', 'NodeSocketFloat', DEFAULTS['dull_roughness']), ('Relief Far Share', 'NodeSocketFloat', DEFAULTS['far_share']),
              ('Relief Fade Start', 'NodeSocketFloat', DEFAULTS['fade_start']), ('Relief Fade End', 'NodeSocketFloat', DEFAULTS['fade_end'])]
    wl._add_sockets(tree, inputs, [('Colour', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Specular IOR Level', 'NodeSocketFloat'),
                                   ('Coat Weight', 'NodeSocketFloat'), ('Normal', 'NodeSocketVector'), ('Joint Shade', 'NodeSocketFloat')])
    for name in ('Surface Normal', 'Groove Normal'):
        next(s for s in tree.interface.items_tree if s.name == name and s.in_out == 'INPUT').hide_value = True
    group_in = tree.nodes.new('NodeGroupInput')
    group_out = tree.nodes.new('NodeGroupOutput')
    group_out.location = (3000, 0)
    g = lambda name: group_in.outputs[name]   # noqa: E731
    n = wl.Net(tree)
    strength = n.math('MULTIPLY', g('Joint Strength'), 1.0, clamp=True)
    cavity = n.math('MULTIPLY', n.math('MULTIPLY', g('Cavity'), strength), 1.0, clamp=True)
    # how far a puddle's water hides the joint (the dark colour stays; the dulling and the groove fade out)
    cover = n.math('SUBTRACT', 1.0, n.math('MULTIPLY', g('Puddle Cover'), g('Puddle Mask')), clamp=True)
    dull = n.math('MULTIPLY', n.math('MULTIPLY', cavity, g('Joint Dullness')), cover)
    # colour: darker in the joint, a little darker at the stone's edge
    # a wet joint is darker than a dry one (it holds dark water and mud): Joint Wet Darkening x the wetness there is added to the darkness
    darkness = n.math('ADD', g('Joint Darkness'), n.math('MULTIPLY', g('Joint Wet Darkening'), g('Wet Mask')), clamp=True)
    joint_scale = n.math('SUBTRACT', 1.0, n.math('MULTIPLY', darkness, cavity))
    edge_scale = n.math('SUBTRACT', 1.0, n.math('MULTIPLY', n.math('MULTIPLY', g('Edge Shade'), g('Halo')), strength))
    scale = n.math('MULTIPLY', joint_scale, edge_scale, clamp=True)
    grey = tree.nodes.new('ShaderNodeCombineColor')
    for channel in ('Red', 'Green', 'Blue'):
        tree.links.new(scale, grey.inputs[channel])
    colour = n.mix_colour(1.0, g('Colour'), grey.outputs['Color'], blend='MULTIPLY')
    # roughness: back toward chalk in the joint (never smoother than it already was)
    dull_target = n.math('MAXIMUM', g('Roughness'), g('Joint Dull Roughness'))
    roughness = n.mix(dull, g('Roughness'), dull_target)
    specular = n.math('MULTIPLY', g('Specular IOR Level'), n.math('SUBTRACT', 1.0, n.math('MULTIPLY', dull, g('Joint Spec Cut'))))
    coat = n.math('MULTIPLY', g('Coat Weight'), n.math('SUBTRACT', 1.0, n.math('MULTIPLY', dull, g('Joint Coat Cut'))))
    # normal: the wetness layer's normal plus the groove's lean, which the water cannot smooth away (a puddle covers it)
    lean = n.vector_math('SUBTRACT', g('Groove Normal'), g('Surface Normal'))
    lean = n.vector_math('SCALE', lean, None)
    relief_amount = n.math('MULTIPLY', n.math('MULTIPLY', g('Joint Relief'), strength), cover)
    # far away the groove's slopes catch the lamps as single white ticks: fade the slopes (not the darkness) with the distance from the camera, from 1 at Relief Fade Start metres
    # down to Relief Far Share at Relief Fade End metres and beyond
    camera = tree.nodes.new('ShaderNodeCameraData')
    fade = n.map_range(camera.outputs['View Distance'], g('Relief Fade Start'), g('Relief Fade End'), 0.0, 1.0, smooth=True)
    relief_amount = n.math('MULTIPLY', relief_amount, n.mix(fade, 1.0, g('Relief Far Share')))
    tree.links.new(relief_amount, lean.node.inputs['Scale'])          # (the Scale operation takes its number in a socket called Scale)
    # the photo's own relief inside the joint is ragged (moss, grit): take away Photo Relief In Joints (0..1) of it where the cavity is 1, so that the clean groove replaces it
    keep_photo = n.math('SUBTRACT', 1.0, n.math('MULTIPLY', n.math('MULTIPLY', g('Photo Relief In Joints'), cavity), cover), clamp=True)
    photo_normal = n.mix_vector(keep_photo, g('Surface Normal'), g('Normal'))
    normal = n.vector_math('ADD', photo_normal, lean)
    normal = n.vector_math('NORMALIZE', normal)
    # the share of the light that does not reach the joint floor (0 = all of it): used by a Mix Shader with black in the material, so it darkens shine and glare too. A puddle's water
    # surface is not in the shade of the joint, so a puddle cuts it like the dulling.
    shade = n.math('MULTIPLY', n.math('MULTIPLY', cavity, g('Joint Shadow')), cover, clamp=True)
    for name, socket in (('Colour', colour), ('Roughness', roughness), ('Specular IOR Level', specular), ('Coat Weight', coat), ('Normal', normal), ('Joint Shade', shade)):
        tree.links.new(socket, group_out.inputs[name])
    return tree


def _image(path, colour_space='Non-Color'):
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = colour_space
    return image


def add_joints_to_material(material, wetness_node, picture=JOINT_PICTURE, groove=GROOVE_PICTURE, **dials):
    """Puts the JOINTS group between the wetness layer and the Principled BSDF of a material that already has the wetness layer on. dials: the group's controls by short name
    (strength, darkness, dullness, relief, edge_shade, puddle_cover). Returns (group_node, undo): undo() takes the layer out again and puts the old links back."""
    tree = material.node_tree
    principled = next(n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED')
    names = ('Base Color', 'Roughness', 'Specular IOR Level', 'Coat Weight', 'Normal')
    old = {}
    for name in names:
        link = next(l for l in tree.links if l.to_socket == principled.inputs[name])
        old[name] = (link.from_socket, link.to_socket)
    added = []

    def new(kind):
        node = tree.nodes.new(kind)
        added.append(node)
        return node

    group_node = new('ShaderNodeGroup')
    group_node.node_tree = build_joints_group()
    group_node.name = 'JOINTS'
    group_node.location = (principled.location.x - 150, principled.location.y - 700)
    # the pictures, laid through the road's own texture coordinates (an image node with nothing in its Vector socket uses the active UV map)
    joint_node = new('ShaderNodeTexImage')
    joint_node.image = _image(picture)
    joint_node.interpolation = 'Linear'
    joint_node.extension = 'REPEAT'
    split = new('ShaderNodeSeparateColor')
    tree.links.new(joint_node.outputs['Color'], split.inputs['Color'])
    groove_node = new('ShaderNodeTexImage')
    groove_node.image = _image(groove)
    groove_node.interpolation = 'Linear'
    groove_node.extension = 'REPEAT'
    groove_map = new('ShaderNodeNormalMap')
    groove_map.inputs['Strength'].default_value = 1.0
    tree.links.new(groove_node.outputs['Color'], groove_map.inputs['Color'])
    geometry = new('ShaderNodeNewGeometry')
    tree.links.new(split.outputs['Red'], group_node.inputs['Cavity'])
    tree.links.new(split.outputs['Blue'], group_node.inputs['Halo'])
    tree.links.new(groove_map.outputs['Normal'], group_node.inputs['Groove Normal'])
    tree.links.new(geometry.outputs['Normal'], group_node.inputs['Surface Normal'])
    for group_name, key in (('Colour', 'Base Color'), ('Roughness', 'Roughness'), ('Specular IOR Level', 'Specular IOR Level'), ('Coat Weight', 'Coat Weight'), ('Normal', 'Normal')):
        tree.links.new(old[key][0], group_node.inputs[group_name])
        tree.links.new(group_node.outputs[group_name], principled.inputs[key])
    tree.links.new(wetness_node.outputs['Puddle Mask'], group_node.inputs['Puddle Mask'])
    tree.links.new(wetness_node.outputs['Wet Mask'], group_node.inputs['Wet Mask'])
    values = dict(DEFAULTS)
    values.update(dials)
    # the shade (only when Joint Shadow is above 0 at the time the layer is put on): Principled BSDF -> Mix Shader (with a black Emission, factor = Joint Shade) -> Material Output.
    # With Joint Shadow 0 the material's graph is not changed at all, so the baking tools and the glb exporter see the same graph as before.
    old_surface = None
    if values['shadow'] > 0.0:
        output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
        surface_link = next(l for l in tree.links if l.to_socket == output.inputs['Surface'])
        old_surface = (surface_link.from_socket, surface_link.to_socket)
        black = new('ShaderNodeEmission')
        black.inputs['Color'].default_value = (0.0, 0.0, 0.0, 1.0)
        black.inputs['Strength'].default_value = 0.0
        mix = new('ShaderNodeMixShader')
        tree.links.new(group_node.outputs['Joint Shade'], mix.inputs['Fac'])
        tree.links.new(old_surface[0], mix.inputs[1])
        tree.links.new(black.outputs['Emission'], mix.inputs[2])
        tree.links.new(mix.outputs['Shader'], output.inputs['Surface'])
    for key, socket_name in DIAL_SOCKETS.items():
        group_node.inputs[socket_name].default_value = values[key]

    def undo():
        for node in added:
            tree.nodes.remove(node)
        for key, (source, target) in old.items():
            tree.links.new(source, target)
        if old_surface:
            tree.links.new(*old_surface)
    return group_node, undo


# ------------------------------------------------------------------------------------------------------------------------------- real geometry (optional, near road only)
def add_real_groove_geometry(road, picture=JOINT_PICTURE, y_min=0.0, y_full=10.0, y_max=22.0, level=6, depth=0.008):
    """Cuts the part of the road between y_min and y_max (metres along the street) into very small faces and presses every joint DOWN by `depth` metres (full depth up to y_full,
    then fading smoothly to nothing at y_max, so that there is no visible edge where the real grooves end), using the green channel
    (the groove profile: 1 on the joint floor, 0 on the stone top, rounded edge) of the joint picture, looked up through the road's own texture coordinates. Real stones with real
    grooves that catch the lamps' light and cast shadows. Plate only: it lives in the street copy as a modifier, it cannot go into the glb. Returns an undo function."""
    tree = bpy.data.node_groups.new('JOINTS REAL GROOVES', 'GeometryNodeTree')
    tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = tree.nodes, tree.links
    group_in, group_out = nodes.new('NodeGroupInput'), nodes.new('NodeGroupOutput')
    position = nodes.new('GeometryNodeInputPosition')
    xyz = nodes.new('ShaderNodeSeparateXYZ')
    links.new(position.outputs['Position'], xyz.inputs[0])
    low = nodes.new('FunctionNodeCompare')
    low.data_type, low.operation = 'FLOAT', 'GREATER_THAN'
    links.new(xyz.outputs['Y'], low.inputs[0])
    low.inputs[1].default_value = y_min
    high = nodes.new('FunctionNodeCompare')
    high.data_type, high.operation = 'FLOAT', 'LESS_THAN'
    links.new(xyz.outputs['Y'], high.inputs[0])
    high.inputs[1].default_value = y_max
    both = nodes.new('FunctionNodeBooleanMath')
    both.operation = 'AND'
    links.new(low.outputs[0], both.inputs[0])
    links.new(high.outputs[0], both.inputs[1])
    split = nodes.new('GeometryNodeSeparateGeometry')
    split.domain = 'FACE'
    links.new(group_in.outputs[0], split.inputs['Geometry'])
    links.new(both.outputs[0], split.inputs['Selection'])
    subdivide = nodes.new('GeometryNodeSubdivideMesh')
    subdivide.inputs['Level'].default_value = level
    links.new(split.outputs['Selection'], subdivide.inputs['Mesh'])
    uv = nodes.new('GeometryNodeInputNamedAttribute')
    uv.data_type = 'FLOAT_VECTOR'
    uv.inputs['Name'].default_value = 'UVMap'
    image_node = nodes.new('GeometryNodeImageTexture')
    image_node.inputs['Image'].default_value = _image(picture)
    image_node.interpolation, image_node.extension = 'Linear', 'REPEAT'
    links.new(uv.outputs['Attribute'], image_node.inputs['Vector'])
    separate = nodes.new('FunctionNodeSeparateColor')
    links.new(image_node.outputs['Color'], separate.inputs['Color'])
    normal = nodes.new('GeometryNodeInputNormal')
    fade = nodes.new('ShaderNodeMapRange')
    fade.interpolation_type, fade.clamp = 'SMOOTHSTEP', True
    links.new(xyz.outputs['Y'], fade.inputs['Value'])
    fade.inputs['From Min'].default_value, fade.inputs['From Max'].default_value = y_full, y_max
    fade.inputs['To Min'].default_value, fade.inputs['To Max'].default_value = 1.0, 0.0
    profile_depth = nodes.new('ShaderNodeMath')
    profile_depth.operation = 'MULTIPLY'
    links.new(separate.outputs['Green'], profile_depth.inputs[0])
    links.new(fade.outputs['Result'], profile_depth.inputs[1])
    down = nodes.new('ShaderNodeMath')
    down.operation = 'MULTIPLY'
    links.new(profile_depth.outputs[0], down.inputs[0])
    down.inputs[1].default_value = -depth
    scale = nodes.new('ShaderNodeVectorMath')
    scale.operation = 'SCALE'
    links.new(normal.outputs['Normal'], scale.inputs[0])
    links.new(down.outputs[0], scale.inputs['Scale'])
    set_position = nodes.new('GeometryNodeSetPosition')
    links.new(subdivide.outputs['Mesh'], set_position.inputs['Geometry'])
    links.new(scale.outputs['Vector'], set_position.inputs['Offset'])
    last = set_position.outputs['Geometry']
    try:
        smooth = nodes.new('GeometryNodeSetShadeSmooth')
        links.new(last, smooth.inputs['Geometry'])
        last = smooth.outputs['Geometry']
    except Exception as error:                      # not fatal: the faces are 8 mm
        print('no Set Shade Smooth node:', error, flush=True)
    join = nodes.new('GeometryNodeJoinGeometry')
    links.new(split.outputs['Inverted'], join.inputs['Geometry'])
    links.new(last, join.inputs['Geometry'])
    links.new(join.outputs['Geometry'], group_out.inputs[0])
    modifier = road.modifiers.new('JOINTS REAL GROOVES', 'NODES')
    modifier.node_group = tree

    def undo():
        road.modifiers.remove(modifier)
        bpy.data.node_groups.remove(tree)
    return undo


# ------------------------------------------------------------------------------------------------------------------------------- the test variants
def register_variants(lv, aw):
    """Registers 'joints_layer' (the JOINTS group alone) and 'joints_geometry' (the JOINTS group plus real grooves on the near road) in the study's variant table (lv.VARIANTS).
    Arguments = the group's dials by short name, plus optional 'picture' and 'groove' file names inside setts/maps; for 'joints_geometry' also y_min, y_full, y_max, level, depth.
    Used by register_variants.py."""
    def joints_layer(picture=None, groove=None, **dials):
        wetness_node = aw.APPLIED['street_setts'][0]
        kwargs = {}
        if picture:
            kwargs['picture'] = os.path.join(MAPS, picture)
        if groove:
            kwargs['groove'] = os.path.join(MAPS, groove)
        node, undo = add_joints_to_material(bpy.data.materials['street_setts'], wetness_node, **kwargs, **dials)
        return undo

    def joints_geometry(y_min=0.0, y_full=10.0, y_max=22.0, level=6, depth=0.008, picture=None, groove=None, **dials):
        dials.setdefault('relief', 0.0)          # the real grooves give the slopes: no extra normal-map groove on top (unless asked)
        undo_layer = joints_layer(picture=picture, groove=groove, **dials)
        undo_geometry = add_real_groove_geometry(bpy.data.objects['street_setts'], picture=os.path.join(MAPS, picture) if picture else JOINT_PICTURE,
                                                 y_min=y_min, y_full=y_full, y_max=y_max, level=level, depth=depth)

        def undo():
            undo_geometry()
            undo_layer()
        return undo
    lv.VARIANTS['joints_layer'] = joints_layer
    lv.VARIANTS['joints_geometry'] = joints_geometry
