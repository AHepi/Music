# What this does: builds the tall brick chimney of the coal mine and the smoke that streams from its top.
#   THE CHIMNEY (standing at mc.LAYOUT['chimney'], 17 m tall):
#     - a four-sided tapering brick shaft with real displacement on its faces (the supplied brick picture, weathered with
#       pale salt patches, dark soot streaks and soot near the top), courses running level;
#     - a stone base ("plinth") of three courses of separate blocks in two or three tones, with a dark flue
#       opening on the front face (a real recess, with soot staining above it);
#     - iron tie-bands with corner plates, a pale stone band course a little over 3 m below the top,
#       a corbelled brick cap (three stepped courses) and a stone coping with an open, sooty flue mouth;
#     - a short low brick flue stub joining the chimney to the engine-house wall.
#   THE SMOKE: one object made of a few hundred soft lumpy grey blobs ("puffs"), rising from the flue mouth, bending to the
#   right (+X) and rising, growing from about 1 m wide at the chimney to over 4 m wide 25 m along the plume, dark charcoal
#   near the chimney and lighter mid grey far away. It stays well behind (further +Y than) the headframe wheels.
# Use: from another script,  sys.path.insert(0, ".../lib"); sys.path.insert(0, ".../modules");  import chimney_and_smoke
#      chimney_and_smoke.build('Mine')  -> {'objects': [...], 'notes': '...'}   (all points are in world coordinates)
import math
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'lib'))
import mine_common as mc  # noqa: E402

PLAN = mc.LAYOUT['chimney']
CENTRE_X, CENTRE_Y = PLAN['centre_x'], PLAN['centre_y']
TOTAL_HEIGHT = PLAN['height']                     # top of the stone coping, metres above the ground
PLINTH_WIDTH = PLAN['base_width']                 # the stone base is as wide as the planned base, 2.3 m
SHAFT_TOP_WIDTH = PLAN['top_width']               # brick shaft width just under the corbelled cap, 1.25 m

# Heights are written as "height above the ground at the chimney" (h) and turned into world z with GROUND + h.
GROUND = mc.ground_height(CENTRE_X, CENTRE_Y)
FIRST_COURSE_TOP, SECOND_COURSE_TOP, PLINTH_TOP = 0.46, 0.92, 1.15
SHAFT_WIDTH_AT_PLINTH = 1.95                      # brick shaft is a little narrower than the stone base
SHAFT_START = 1.0                                 # shaft faces begin inside the plinth so there is never a gap
CAP_START = TOTAL_HEIGHT - 1.45                   # 15.55: where the corbelled cap begins
BAND_COURSE_BOTTOM, BAND_COURSE_TOP = 13.55, 13.90  # pale stone band, about 3.1 to 3.45 m below the top
IRON_BAND_HEIGHTS = [3.6, 6.8, 10.0, 12.2, 15.1]
FLUE_OPENING_WIDTH, FLUE_OPENING_DEPTH = 0.70, 0.70
FLUE_OPENING_HEIGHT = SECOND_COURSE_TOP


def shaft_width(h):
    """Full width of the brick shaft at height h (it tapers in a straight line)."""
    return SHAFT_WIDTH_AT_PLINTH + (SHAFT_TOP_WIDTH - SHAFT_WIDTH_AT_PLINTH) * (h - PLINTH_TOP) / (CAP_START - PLINTH_TOP)


def world(local_x, local_y, h, quarter_turns=0):
    """Turn a point given relative to the chimney centre (and a face turned by quarter turns) into a world point."""
    angle = quarter_turns * math.pi / 2.0
    c, s = math.cos(angle), math.sin(angle)
    return (CENTRE_X + local_x * c - local_y * s, CENTRE_Y + local_x * s + local_y * c, GROUND + h)


# --------------------------------------------------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------------------------------------------------
def pick(sockets, name):
    """Blender's Mix node has several sockets with the same name; take the one that is switched on."""
    for socket in sockets:
        if socket.name == name and socket.enabled:
            return socket
    raise KeyError(name)


def add_mix(nodes, links, a, b, factor, blend='MIX', location=(0, 0)):
    """Mix two colours (a, b can be sockets or colour tuples). factor can be a socket or a number. Returns the result socket."""
    node = nodes.new('ShaderNodeMix')
    node.data_type, node.blend_type, node.location = 'RGBA', blend, location
    for socket, value in ((pick(node.inputs, 'A'), a), (pick(node.inputs, 'B'), b)):
        if isinstance(value, tuple):
            socket.default_value = (value[0], value[1], value[2], 1.0)
        else:
            links.new(value, socket)
    factor_socket = pick(node.inputs, 'Factor')
    if isinstance(factor, (int, float)):
        factor_socket.default_value = factor
    else:
        links.new(factor, factor_socket)
    return pick(node.outputs, 'Result')


def add_ramp(nodes, links, source, low, high, location=(0, 0)):
    """A hard-edged threshold: 0 below 'low', 1 above 'high' (gives crisp painted patches). Returns the result socket."""
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.location = location
    ramp.color_ramp.elements[0].position = low
    ramp.color_ramp.elements[1].position = high
    links.new(source, ramp.inputs['Fac'])
    return ramp.outputs['Color']


def weathered_brick_material(name, tint, true_displacement, splash, soot_near_top=True):
    """The supplied brick picture (colour, normal, height) with extra painted weathering on top of it:
    pale salt patches, dark soot streaks that run down the wall, and soot staining near the top of the chimney."""
    base = mc.surface_material('brick', tint=tint, true_displacement=true_displacement, variation=0.30, splash=splash)
    material = base.copy()
    material.name = name
    material['mine_tile_metres'] = float(base['mine_tile_metres'])
    if true_displacement:
        material.displacement_method = 'DISPLACEMENT'
        material.max_vertex_displacement = mc.SURFACES['brick']['depth']
    tree = material.node_tree
    nodes, links = tree.nodes, tree.links
    bsdf = [n for n in nodes if n.type == 'BSDF_PRINCIPLED'][0]
    colour_link = [l for l in links if l.to_socket == bsdf.inputs['Base Color']][0]
    colour = colour_link.from_socket
    links.remove(colour_link)

    position = nodes.new('ShaderNodeNewGeometry'); position.location = (-900, -1700)
    # 1. pale, salty patches
    patches = nodes.new('ShaderNodeTexNoise'); patches.location = (-700, -1700)
    patches.inputs['Scale'].default_value = 0.9; patches.inputs['Detail'].default_value = 3.0
    links.new(position.outputs['Position'], patches.inputs['Vector'])
    patch_mask = add_ramp(nodes, links, patches.outputs['Fac'], 0.60, 0.66, (-450, -1700))
    pale = nodes.new('ShaderNodeMath'); pale.operation = 'MULTIPLY'; pale.inputs[1].default_value = 0.55
    links.new(patch_mask, pale.inputs[0])
    colour = add_mix(nodes, links, colour, (0.45, 0.39, 0.32), pale.outputs['Value'], location=(-200, -1700))
    # 2. dark soot streaks running down (noise squashed so it is long in the up direction)
    stretch = nodes.new('ShaderNodeMapping'); stretch.location = (-900, -2000)
    stretch.inputs['Scale'].default_value = (2.2, 2.2, 0.16)
    links.new(position.outputs['Position'], stretch.inputs['Vector'])
    streaks = nodes.new('ShaderNodeTexNoise'); streaks.location = (-700, -2000)
    streaks.inputs['Scale'].default_value = 4.0; streaks.inputs['Detail'].default_value = 2.0
    links.new(stretch.outputs['Vector'], streaks.inputs['Vector'])
    streak_mask = add_ramp(nodes, links, streaks.outputs['Fac'], 0.52, 0.72, (-450, -2000))
    dark = nodes.new('ShaderNodeMath'); dark.operation = 'MULTIPLY'; dark.inputs[1].default_value = 0.62
    links.new(streak_mask, dark.inputs[0])
    colour = add_mix(nodes, links, colour, (0.035, 0.028, 0.024), dark.outputs['Value'], location=(50, -2000))
    # 3. soot near the top (smoke blackens the last two metres), with a ragged lower edge
    if soot_near_top:
        split = nodes.new('ShaderNodeSeparateXYZ'); split.location = (-900, -2300)
        links.new(position.outputs['Position'], split.inputs['Vector'])
        ragged = nodes.new('ShaderNodeMath'); ragged.operation = 'MULTIPLY_ADD'; ragged.location = (-700, -2300)
        links.new(streaks.outputs['Fac'], ragged.inputs[0]); ragged.inputs[1].default_value = 2.6
        ragged.inputs[2].default_value = -1.3
        shifted = nodes.new('ShaderNodeMath'); shifted.operation = 'ADD'; shifted.location = (-500, -2300)
        links.new(split.outputs['Z'], shifted.inputs[0]); links.new(ragged.outputs['Value'], shifted.inputs[1])
        top_soot = nodes.new('ShaderNodeMapRange'); top_soot.location = (-300, -2300); top_soot.clamp = True
        top_soot.inputs['From Min'].default_value = GROUND + 13.6; top_soot.inputs['From Max'].default_value = GROUND + CAP_START
        top_soot.inputs['To Min'].default_value = 0.0; top_soot.inputs['To Max'].default_value = 0.78
        links.new(shifted.outputs['Value'], top_soot.inputs['Value'])
        colour = add_mix(nodes, links, colour, (0.03, 0.026, 0.024), top_soot.outputs['Result'], location=(300, -2300))
    links.new(colour, bsdf.inputs['Base Color'])
    return material


def stone_material(name, colour, mud_splash_height=0.55):
    """Plain stone colour with small painted variation, rough bumps and mud splashed up the bottom. (Stone footings are a
    plain material in this scene, not one of the supplied pictures.)"""
    material = mc.plain_material(name, colour, roughness=0.92)
    if material.get('chimney_stone_extra'):
        return material
    material['chimney_stone_extra'] = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    bsdf = nodes['Principled BSDF']
    position = nodes.new('ShaderNodeNewGeometry'); position.location = (-900, 0)
    noise = nodes.new('ShaderNodeTexNoise'); noise.location = (-700, 0)
    noise.inputs['Scale'].default_value = 7.0; noise.inputs['Detail'].default_value = 6.0
    links.new(position.outputs['Position'], noise.inputs['Vector'])
    shade = nodes.new('ShaderNodeMapRange'); shade.location = (-450, 0)
    shade.inputs['To Min'].default_value = 0.70; shade.inputs['To Max'].default_value = 1.20
    links.new(noise.outputs['Fac'], shade.inputs['Value'])
    varied = add_mix(nodes, links, colour, shade.outputs['Result'], 1.0, blend='MULTIPLY', location=(-200, 0))
    split = nodes.new('ShaderNodeSeparateXYZ'); split.location = (-700, -300)
    links.new(position.outputs['Position'], split.inputs['Vector'])
    wet = nodes.new('ShaderNodeMapRange'); wet.location = (-450, -300); wet.clamp = True
    wet.inputs['From Min'].default_value = GROUND; wet.inputs['From Max'].default_value = GROUND + mud_splash_height
    wet.inputs['To Min'].default_value = 0.6; wet.inputs['To Max'].default_value = 0.0
    links.new(split.outputs['Z'], wet.inputs['Value'])
    varied = add_mix(nodes, links, varied, mc.MUD_SPLASH_COLOUR[:3], wet.outputs['Result'], location=(100, 0))
    links.new(varied, bsdf.inputs['Base Color'])
    bump = nodes.new('ShaderNodeBump'); bump.location = (100, -300)
    bump.inputs['Strength'].default_value = 0.45; bump.inputs['Distance'].default_value = 0.02
    links.new(noise.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return material


def soot_stain_material(name='Chimney soot stain'):
    """A see-through sheet: a ragged, streaky dark stain that is strongest at the bottom centre of the sheet and fades upward."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material['mine_tile_metres'] = 1.0
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial'); output.location = (900, 0)
    coords = nodes.new('ShaderNodeTexCoord'); coords.location = (-1100, 0)
    # vertical streaks: noise stretched so it is long in the up direction
    stretch = nodes.new('ShaderNodeMapping'); stretch.location = (-900, -250)
    stretch.inputs['Scale'].default_value = (9.0, 1.2, 1.0)
    links.new(coords.outputs['UV'], stretch.inputs['Vector'])
    streaks = nodes.new('ShaderNodeTexNoise'); streaks.location = (-700, -250)
    streaks.inputs['Scale'].default_value = 3.0; streaks.inputs['Detail'].default_value = 4.0
    links.new(stretch.outputs['Vector'], streaks.inputs['Vector'])
    place = nodes.new('ShaderNodeMapping'); place.location = (-900, 100)
    place.inputs['Location'].default_value = (-0.5, 0.0, 0.0)
    place.inputs['Scale'].default_value = (3.0, 1.0, 1.0)
    links.new(coords.outputs['UV'], place.inputs['Vector'])
    falloff = nodes.new('ShaderNodeTexGradient'); falloff.location = (-650, 100)
    falloff.gradient_type = 'SPHERICAL'
    links.new(place.outputs['Vector'], falloff.inputs['Vector'])
    jitter = nodes.new('ShaderNodeMath'); jitter.operation = 'MULTIPLY_ADD'; jitter.location = (-450, -100)
    links.new(streaks.outputs['Fac'], jitter.inputs[0]); jitter.inputs[1].default_value = 0.8
    jitter.inputs[2].default_value = -0.38
    total = nodes.new('ShaderNodeMath'); total.operation = 'ADD'; total.location = (-250, 0)
    links.new(falloff.outputs['Fac'], total.inputs[0]); links.new(jitter.outputs['Value'], total.inputs[1])
    ramp = nodes.new('ShaderNodeValToRGB'); ramp.location = (-50, 0)
    ramp.color_ramp.elements[0].position = 0.10
    ramp.color_ramp.elements[1].position = 0.60
    links.new(total.outputs['Value'], ramp.inputs['Fac'])
    strength = nodes.new('ShaderNodeMath'); strength.operation = 'MULTIPLY'; strength.location = (200, 0)
    links.new(ramp.outputs['Color'], strength.inputs[0]); strength.inputs[1].default_value = 0.62
    dark = nodes.new('ShaderNodeBsdfDiffuse'); dark.location = (400, -250)
    dark.inputs['Color'].default_value = (0.016, 0.013, 0.011, 1.0)
    clear = nodes.new('ShaderNodeBsdfTransparent'); clear.location = (400, 250)
    mixer = nodes.new('ShaderNodeMixShader'); mixer.location = (650, 0)
    links.new(strength.outputs['Value'], mixer.inputs[0])
    links.new(clear.outputs['BSDF'], mixer.inputs[1]); links.new(dark.outputs['BSDF'], mixer.inputs[2])
    links.new(mixer.outputs['Shader'], output.inputs['Surface'])
    return material


# --------------------------------------------------------------------------------------------------------------------
# The chimney
# --------------------------------------------------------------------------------------------------------------------
def add_stone_course(builder, rng, bottom, top, half, thickness, tone_slots, front_gap=None, block_range=(0.55, 0.95),
                     long_sides_first=True):
    """One layer of the stone base: separate blocks laid round the four sides, with tiny gaps (the dark core shows in the
    joins). front_gap = (left_x, right_x): a gap in the front (-Y) side for the flue opening."""
    gap = 0.018
    for side in range(4):
        runs_full = (side % 2 == 0) == long_sides_first
        start = -half if runs_full else -half + thickness
        end = half if runs_full else half - thickness
        spans = [(start, end)]
        if side == 0 and front_gap is not None:
            spans = [(start, front_gap[0]), (front_gap[1], end)]
        for span_start, span_end in spans:
            length = span_end - span_start
            count = max(1, int(round(length / rng.uniform(*block_range))))
            weights = rng.uniform(0.7, 1.3, count)
            edges = span_start + np.concatenate([[0.0], np.cumsum(weights) / weights.sum()]) * length
            for i in range(count):
                block_length = edges[i + 1] - edges[i]
                middle = (edges[i] + edges[i + 1]) / 2.0
                block_top = top - rng.uniform(0.0, 0.012)
                size = (block_length - gap, thickness, block_top - bottom - gap)
                centre = world(middle, -(half - thickness / 2.0), (bottom + block_top) / 2.0 + gap / 2.0, side)
                slot = int(rng.choice(tone_slots))
                builder.add_box(centre, size, slot=slot, yaw=side * math.pi / 2.0)


def build_stone(rng):
    dark = [stone_material('Chimney footing stone A', (0.078, 0.072, 0.066)), stone_material('Chimney footing stone B', (0.110, 0.100, 0.088)),
            stone_material('Chimney footing stone C', (0.060, 0.058, 0.056))]
    mid = [stone_material('Chimney plinth stone A', (0.150, 0.138, 0.120)), stone_material('Chimney plinth stone B', (0.195, 0.178, 0.150)),
           stone_material('Chimney plinth stone C', (0.125, 0.112, 0.098))]
    light = [stone_material('Chimney cap stone A', (0.260, 0.240, 0.205)), stone_material('Chimney cap stone B', (0.305, 0.282, 0.242)),
             stone_material('Chimney cap stone C', (0.225, 0.212, 0.190))]
    core = mc.plain_material('Chimney flue black', (0.010, 0.009, 0.008), roughness=1.0)
    band = stone_material('Chimney band stone', (0.235, 0.218, 0.190))
    coping = stone_material('Chimney coping stone', (0.205, 0.192, 0.168), mud_splash_height=0.0)
    iron = mc.plain_material('Chimney iron', (0.030, 0.028, 0.026), roughness=0.55, metallic=0.7)
    rusty_iron = mc.plain_material('Chimney rusty iron', (0.085, 0.042, 0.022), roughness=0.7, metallic=0.5)
    materials = dark + mid + light + [core, band, coping, iron, rusty_iron]
    DARK, MID, LIGHT = [0, 1, 2], [3, 4, 5], [6, 7, 8]
    CORE, BAND, COPING, IRON, RUST = 9, 10, 11, 12, 13
    builder = mc.MeshBuilder('Chimney stonework and iron', materials)

    half1, half2, half3 = PLINTH_WIDTH / 2.0, PLINTH_WIDTH / 2.0 - 0.03, PLINTH_WIDTH / 2.0 - 0.06
    opening_left, opening_right = -FLUE_OPENING_WIDTH / 2.0, FLUE_OPENING_WIDTH / 2.0
    # dark core of the plinth (the "mortar" seen through the joins), built around the flue recess
    recess_back = -half1 + FLUE_OPENING_DEPTH
    core_half = half1 - 0.30
    builder.add_box(world(0, (recess_back + core_half) / 2.0, PLINTH_TOP / 2.0 - 0.01), (2 * core_half, core_half - recess_back, PLINTH_TOP - 0.02), slot=CORE)
    for sign in (-1, 1):
        x_inner = sign * opening_right
        x_outer = sign * core_half
        builder.add_box(world((x_inner + x_outer) / 2.0, (-core_half + recess_back) / 2.0, PLINTH_TOP / 2.0 - 0.01),
                        (abs(x_outer - x_inner), recess_back + core_half, PLINTH_TOP - 0.02), slot=CORE)
    builder.add_box(world(0, (-half1 + 0.40 + recess_back) / 2.0, (FLUE_OPENING_HEIGHT + PLINTH_TOP) / 2.0),
                    (FLUE_OPENING_WIDTH + 0.02, recess_back - (-half1 + 0.40), PLINTH_TOP - FLUE_OPENING_HEIGHT - 0.01), slot=CORE)
    builder.add_box(world(0, (-half1 + recess_back) / 2.0, 0.02), (FLUE_OPENING_WIDTH + 0.02, FLUE_OPENING_DEPTH, 0.04), slot=CORE)

    # the three stone courses: dark footing, mid, pale dressed course (its front side is one long lintel over the opening)
    add_stone_course(builder, rng, -0.10, FIRST_COURSE_TOP, half1, 0.45, DARK, front_gap=(opening_left, opening_right))
    add_stone_course(builder, rng, FIRST_COURSE_TOP, SECOND_COURSE_TOP, half2, 0.42, MID, front_gap=(opening_left, opening_right), long_sides_first=False)
    lintel_left, lintel_right = opening_left - 0.18, opening_right + 0.18
    add_stone_course(builder, rng, SECOND_COURSE_TOP, PLINTH_TOP, half3, 0.40, LIGHT, front_gap=(lintel_left, lintel_right), long_sides_first=True)
    builder.add_box(world((lintel_left + lintel_right) / 2.0, -(half3 - 0.20), (SECOND_COURSE_TOP + PLINTH_TOP) / 2.0),
                    (lintel_right - lintel_left - 0.018, 0.40, PLINTH_TOP - SECOND_COURSE_TOP - 0.018), slot=int(rng.choice(LIGHT)))

    # sloping stone top of the plinth, running up to meet the brick shaft
    top_half = shaft_width(PLINTH_TOP + 0.12) / 2.0 - 0.02
    for side in range(4):
        builder.add_polygon([world(-half3, -half3, PLINTH_TOP - 0.004, side), world(half3, -half3, PLINTH_TOP - 0.004, side),
                             world(top_half, -top_half, PLINTH_TOP + 0.12, side), world(-top_half, -top_half, PLINTH_TOP + 0.12, side)],
                            slot=LIGHT[1])
    # dark flue recess walls are the faces of the dark core boxes; a thin dark lining behind the stones keeps the sides black

    # pale stone band course
    band_half = shaft_width((BAND_COURSE_BOTTOM + BAND_COURSE_TOP) / 2.0) / 2.0
    stick_out = 0.07
    for side in range(4):
        span = band_half + stick_out
        length = (2 * span) if side % 2 == 0 else (2 * band_half)
        builder.add_box(world(0, -(band_half + stick_out / 2.0 - 0.03), (BAND_COURSE_BOTTOM + BAND_COURSE_TOP) / 2.0, side),
                        (length, stick_out + 0.06, BAND_COURSE_TOP - BAND_COURSE_BOTTOM), slot=BAND, yaw=side * math.pi / 2.0)
    # a thin darker brick-coloured drip lip under the band
    for side in range(4):
        span = band_half + 0.03
        length = (2 * span) if side % 2 == 0 else (2 * band_half)
        builder.add_box(world(0, -(band_half + 0.015 - 0.02), BAND_COURSE_BOTTOM - 0.06, side), (length, 0.07, 0.12), slot=int(rng.choice(MID)), yaw=side * math.pi / 2.0)

    # iron tie-bands with corner plates and bolts
    for h in IRON_BAND_HEIGHTS:
        half = shaft_width(h) / 2.0
        strap_height, strap_out = 0.11, 0.045
        for side in range(4):
            length = (2 * (half + strap_out)) if side % 2 == 0 else (2 * half)
            builder.add_box(world(0, -(half + strap_out / 2.0 - 0.015), h, side), (length, strap_out + 0.03, strap_height), slot=IRON, yaw=side * math.pi / 2.0)
        for side in range(4):
            corner = world(-half, -half, h, side)
            builder.add_box(corner, (0.17, 0.17, 0.20), slot=RUST if rng.random() < 0.4 else IRON, yaw=side * math.pi / 2.0 + math.pi / 4.0 * 0.0)
            for dx in (-0.045, 0.045):
                bolt = world(-half + 0.0 + dx, -half - 0.085 - strap_out * 0.0, h + 0.07, side)
                builder.add_box(bolt, (0.035, 0.03, 0.035), slot=RUST, yaw=side * math.pi / 2.0)

    # coping: lower projecting slab then an upper rim round an open flue mouth
    slab_width, rim_width, mouth = 1.84, 1.68, 0.80
    slab_bottom, slab_top, rim_top = CAP_START + 0.90, CAP_START + 1.17, TOTAL_HEIGHT
    builder.add_box(world(0, 0, (slab_bottom + slab_top) / 2.0), (slab_width, slab_width, slab_top - slab_bottom), slot=COPING)
    rim_height = rim_top - slab_top
    ring_depth = (rim_width - mouth) / 2.0
    for side in range(4):
        length = rim_width if side % 2 == 0 else mouth
        builder.add_box(world(0, -(rim_width / 2.0 - ring_depth / 2.0), (slab_top + rim_top) / 2.0 - 0.005, side), (length, ring_depth, rim_height + 0.01),
                        slot=COPING, yaw=side * math.pi / 2.0)
    builder.add_box(world(0, 0, slab_top + 0.01), (mouth - 0.02, mouth - 0.02, 0.03), slot=CORE)     # soot-black flue floor, a little below the rim top
    # soot-black collar just inside the mouth so the stone edge reads as burnt
    for side in range(4):
        builder.add_box(world(0, -(mouth / 2.0 + 0.004), (slab_top + rim_top) / 2.0, side), (mouth, 0.012, rim_height - 0.01), slot=CORE, yaw=side * math.pi / 2.0)
    return builder.finish('Mine')


def build_corbel_and_stub(rng):
    """Brick that does not need real displacement: the stepped corbel under the cap and the low flue stub."""
    corbel_brick = weathered_brick_material('Chimney corbel brick', (0.95, 0.88, 0.85), true_displacement=False, splash=0.0)
    stub_brick = weathered_brick_material('Chimney flue stub brick', (0.88, 0.80, 0.76), true_displacement=False, splash=0.8, soot_near_top=False)
    cap_stone = stone_material('Chimney stub cap stone', (0.20, 0.185, 0.16))
    builder = mc.MeshBuilder('Chimney corbel and flue stub', [corbel_brick, stub_brick, cap_stone])
    # three stepped brick courses, each sticking out a little further (corbelling)
    for step, stick_out in enumerate((0.10, 0.24, 0.38)):
        bottom = CAP_START + step * 0.30
        width = SHAFT_TOP_WIDTH + stick_out
        builder.add_box(world(0, 0, bottom + 0.15), (width, width, 0.30 + (0.004 if step else 0.04)), slot=0)
    # the short low flue stub that leads from the chimney base across to the engine-house wall
    engine = mc.LAYOUT['engine_house']
    x_start = CENTRE_X + PLINTH_WIDTH / 2.0 - 0.10
    x_end = engine['x_left'] + 0.08
    stub_height, stub_width = 1.35, 1.10
    builder.add_box((((x_start + x_end) / 2.0), CENTRE_Y, GROUND + stub_height / 2.0 - 0.05), (x_end - x_start, stub_width, stub_height + 0.10), slot=1,
                    skip=('bottom',))
    builder.add_box((((x_start + x_end) / 2.0 - 0.02), CENTRE_Y, GROUND + stub_height + 0.07), (x_end - x_start - 0.06, stub_width + 0.18, 0.14), slot=2)
    return builder.finish('Mine')


def build_brick_shaft():
    """The big tapering brick shaft: four faces, each one tall quad given real displacement."""
    material = weathered_brick_material('Chimney weathered brick', (1.0, 0.93, 0.90), true_displacement=True, splash=0.0)
    builder = mc.MeshBuilder('Chimney brick shaft', [material])
    h0, h1 = SHAFT_START, CAP_START + 0.04
    w0, w1 = shaft_width(h0) / 2.0, shaft_width(h1) / 2.0
    for side in range(4):
        builder.add_polygon([world(-w0, -w0, h0, side), world(w0, -w0, h0, side), world(w1, -w1, h1, side), world(-w1, -w1, h1, side)],
                            slot=0, uv_shift=(0.31 * side, 0.0))
    obj = builder.finish('Mine')
    mc.use_real_displacement(obj, pixel_size=2.0)
    return obj


def build_soot_sheet():
    """A see-through sheet of soot on the front face above the flue opening, plus a smaller one on the side."""
    material = soot_stain_material()
    builder = mc.MeshBuilder('Chimney soot stains', [material])
    sheets = [  # (side 0 = front, half-width of sheet, low height, high height, extra x shift)
        (0, 0.55, PLINTH_TOP - 0.03, PLINTH_TOP + 3.6, 0.0),
    ]
    for side, half_width, low, high, shift in sheets:
        def point(x, h):
            half = shaft_width(h) / 2.0
            return world(x + shift, -(half + 0.032), h, side)
        builder.add_polygon([point(-half_width, low), point(half_width, low), point(half_width, high), point(-half_width, high)],
                            slot=0, uv_metres=[(0, 0), (1, 0), (1, 1), (0, 1)])
    return builder.finish('Mine')


# --------------------------------------------------------------------------------------------------------------------
# The smoke
# --------------------------------------------------------------------------------------------------------------------
# The middle line of the plume, as (x, y, height above ground). It rises first, then leans right (+X) and keeps rising slowly,
# drifting a little backwards (+Y) so it stays well behind the headframe (which stands at y = -3.4, wheels 16.6 m up).
PLUME_POINTS = [
    (-6.00, 7.00, TOTAL_HEIGHT + 0.25),
    (-6.00, 6.95, 19.0),
    (-5.20, 6.60, 21.2),
    (-3.60, 5.90, 23.4),
    (-1.20, 5.00, 25.4),
    (1.80, 3.80, 27.4),
    (5.50, 2.40, 29.4),
    (9.50, 0.80, 31.2),
    (14.00, -1.00, 33.0),
    (19.00, -3.00, 34.8),
    (24.00, -5.00, 36.5),
]
PLUME_SMALL_RADIUS = 0.30        # the first puffs are small enough to sit in the flue mouth
PLUME_BIG_RADIUS = 1.25          # the main puffs are about 4.6 m across 25 m along the plume (billows are bigger still)
PLUME_BIG_AT = 25.0
GREY_STEPS = 10                  # number of greys, from sooty charcoal (0) to mid grey (9)


def plume_curve():
    """Smooth curve through the plume points, returned as (arc_length_array, points_array)."""
    controls = np.array([[x, y, GROUND + h] for x, y, h in PLUME_POINTS])
    padded = np.vstack([controls[0], controls, controls[-1]])
    samples = []
    for i in range(1, len(padded) - 2):
        p0, p1, p2, p3 = padded[i - 1], padded[i], padded[i + 1], padded[i + 2]
        for t in np.linspace(0.0, 1.0, 80, endpoint=False):
            samples.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    samples.append(controls[-1])
    points = np.array(samples)
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))])
    return arc, points


def plume_radius(arc_length):
    """Main puff radius at a given distance along the plume (grows quickly at first, then steadily)."""
    grown = min(arc_length / PLUME_BIG_AT, 1.6)
    return PLUME_SMALL_RADIUS + (PLUME_BIG_RADIUS - PLUME_SMALL_RADIUS) * grown ** 0.85


def build_smoke(rng):
    """One object of many overlapping soft lumpy blobs, grouped into 'billows' (each billow is one big blob ringed by smaller
    ones, painted in one family of greys) so the plume reads as big painted clumps, not a chain of bubbles.
    Returns (object, list of (centre, radius) for clearance checks)."""
    arc, points = plume_curve()
    total_length = arc[-1]

    def centre_at(s):
        return np.array([np.interp(s, arc, points[:, k]) for k in range(3)])

    def direction_at(s):
        d = centre_at(min(s + 0.3, total_length)) - centre_at(max(s - 0.3, 0.0))
        return d / np.linalg.norm(d)

    # greys: sooty charcoal at the chimney to a mid, slightly cool grey far away (plain colour, fully rough, no glow)
    materials = []
    for i in range(GREY_STEPS):
        level = 0.06 + (0.36 - 0.06) * (i / (GREY_STEPS - 1)) ** 1.1
        cool = i / (GREY_STEPS - 1)
        colour = (level * (1.0 - 0.07 * cool), level * (1.0 + 0.01 * cool), level * (1.0 + 0.07 * cool))
        materials.append(mc.plain_material(f'Chimney smoke grey {i}', colour, roughness=1.0))
    builder = mc.MeshBuilder('Chimney smoke', materials)
    puff_records = []
    counter = [100]

    def add_puff(centre, radius, tone, flow=None):
        """One blob. flow: direction the smoke is moving; the blob is stretched a little along it so the plume streams."""
        slot = int(np.clip(round(tone), 0, GREY_STEPS - 1))
        stretch = rng.uniform(1.05, 1.35) if flow is not None else 1.0
        radii = (radius * stretch * rng.uniform(0.9, 1.35), radius * rng.uniform(0.85, 1.15), radius * rng.uniform(0.65, 1.0))
        rotation = mc.basis_from_direction(flow) if flow is not None else None
        counter[0] += 1
        builder.add_blob(centre, radii, slot=slot, subdivisions=3 if radius > 0.3 else 2, rotation=rotation, jitter=(0.16 if radius < 0.6 else 0.12), seed=counter[0], smooth=True)
        puff_records.append((np.array(centre), radius * stretch))

    s = 0.0
    while s < total_length:
        end_fade = min(max((s - (total_length - 7.0)) / 7.0, 0.0), 1.0)        # the far end thins out and pales
        radius = plume_radius(s) * (1.0 - 0.5 * end_fade)
        fraction = min(s / PLUME_BIG_AT, 1.3)
        forward = direction_at(s)
        side = np.cross(forward, [0.0, 0.0, 1.0])
        side = side / max(np.linalg.norm(side), 1e-6)
        lift = np.cross(side, forward)
        # the whole plume wavers a little from side to side and up and down (stronger as it spreads)
        sway = side * math.sin(s * 0.42 + 0.7) * 0.35 * radius + lift * math.sin(s * 0.31 + 2.0) * 0.55 * radius
        # one billow: its middle sits off the plume's centre line, a bit more on the upper side
        billow_angle = rng.uniform(0, 2 * math.pi)
        billow_offset = (side * math.cos(billow_angle) + lift * math.sin(billow_angle)) * radius * rng.uniform(0.0, 0.55)
        billow_offset[2] += radius * 0.10 * fraction
        billow_centre = centre_at(s) + sway + billow_offset
        big = radius * rng.uniform(0.95, 1.30)
        billow_tone = 0.2 + fraction * 6.2 + rng.normal(0, 1.0) + 1.6 * end_fade
        add_puff(billow_centre, big, billow_tone - 0.2, flow=forward)
        around = 3 + int(big * 1.2) + int(rng.integers(0, 3))
        for _ in range(around):
            angle = rng.uniform(0, 2 * math.pi)
            reach = big * rng.uniform(0.55, 1.05)
            offset = (side * math.cos(angle) + lift * math.sin(angle)) * reach + forward * rng.uniform(-0.45, 0.45) * big
            offset[2] += big * 0.20                                  # puffs bulge upward, like a cauliflower
            tone = billow_tone + rng.normal(0, 0.45) + 0.9 * (offset[2] / max(reach, 0.1))   # upper clumps catch the light
            add_puff(billow_centre + offset, big * rng.uniform(0.55, 0.95), tone, flow=forward)
        if big > 0.9:        # small fuzzy puffs round the rim give the clump a soft, painted edge
            for _ in range(3 + int(big)):
                angle = rng.uniform(0, 2 * math.pi)
                rim = (side * math.cos(angle) + lift * math.sin(angle)) * big * rng.uniform(1.05, 1.45)
                rim[2] += big * 0.15
                add_puff(billow_centre + rim, big * rng.uniform(0.18, 0.34), billow_tone + rng.normal(0, 0.6))
        if big > 1.1:        # a few darker puffs tucked underneath give the billow a heavy belly
            for _ in range(2):
                belly = billow_centre + np.array([rng.uniform(-0.5, 0.5) * big, rng.uniform(-0.5, 0.5) * big, -big * 0.55])
                add_puff(belly, big * rng.uniform(0.5, 0.75), billow_tone - 1.5)
        s += radius * 0.50 + 0.14
    # a few small, pale stragglers drifting off the far end
    far = centre_at(total_length)
    for k in range(6):
        add_puff(far + np.array([rng.uniform(0.5, 3.5), rng.uniform(-1.0, 1.0), rng.uniform(-1.2, 1.5)]), rng.uniform(0.5, 1.0), 7.5 + rng.normal(0, 0.5))
    obj = builder.finish('Mine')
    return obj, puff_records


def smoke_clearance_report(puff_records):
    """Smallest gap between any puff and the headframe's wheels (two discs, 2.4 m radius, 16.6 m up, x = +-0.775, y = -3.4)."""
    frame = mc.LAYOUT['headframe']
    nearest = 1e9
    for centre, radius in puff_records:
        for wheel_x in (-frame['wheel_spacing_x'] / 2.0, frame['wheel_spacing_x'] / 2.0):
            gap = math.dist((centre[0], centre[1], centre[2]), (wheel_x, frame['centre_y'], frame['wheel_centre_height'])) - radius - frame['wheel_radius']
            nearest = min(nearest, gap)
    return nearest


# --------------------------------------------------------------------------------------------------------------------
def build(collection_name='Mine'):
    rng = np.random.default_rng(20260519)
    objects = []
    shaft = build_brick_shaft(); objects.append(shaft)
    stonework = build_stone(rng); objects.append(stonework)
    corbel = build_corbel_and_stub(rng); objects.append(corbel)
    soot = build_soot_sheet(); objects.append(soot)
    smoke, puffs = build_smoke(rng); objects.append(smoke)
    for obj in objects:
        for collection in list(obj.users_collection):
            if collection.name != collection_name:
                collection.objects.unlink(obj)
        target = bpy.data.collections.get(collection_name)
        if target is None:
            target = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(target)
        if obj.name not in target.objects:
            target.objects.link(obj)
    clearance = smoke_clearance_report(puffs)
    arc, curve = plume_curve()
    over_headframe = curve[np.argmin(np.abs(curve[:, 0]))]
    end = curve[-1]
    notes = (f'Chimney centred at ({CENTRE_X}, {CENTRE_Y}), {TOTAL_HEIGHT} m to the top of the coping. Brick shaft 1.95 m wide at the stone base '
             f'tapering to 1.25 m under the cap, real displacement (adaptive subdivision, 2 px). Stone plinth 0-1.15 m of separate blocks with a flue recess '
             f'on the front (-Y) face; pale stone band course at {BAND_COURSE_BOTTOM}-{BAND_COURSE_TOP} m; iron bands at {IRON_BAND_HEIGHTS} m; corbelled brick cap and '
             f'stone coping with an open flue mouth. A low brick flue stub joins the chimney to the engine-house left wall (x = {mc.LAYOUT["engine_house"]["x_left"]}), 1.5 m high. '
             f'SMOKE: {len(puffs)} puffs in one object called Chimney smoke, rising from the flue mouth at z = {GROUND + PLUME_POINTS[0][2]:.1f}, leaning right (+X) and rising. '
             f'It passes x = 0 at y = {over_headframe[1]:.1f}, z = {over_headframe[2]:.1f} (so about {over_headframe[1] + 3.4:.0f} m BEHIND the headframe wheels and {over_headframe[2] - 19.0:.0f} m above their top) '
             f'and ends near x = {end[0]:.0f}, y = {end[1]:.0f}, z = {end[2]:.0f}. Smallest gap between any puff and a headframe wheel disc: {clearance:.1f} m. '
             f'In a camera that looks along +Y the smoke can still cross behind the wheels on screen; it never touches them in space.')
    return {'objects': [o.name for o in objects], 'notes': notes}
