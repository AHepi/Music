"""
headstone: a leaning graveyard headstone of about 1860-1900: a dressed stone slab with a rounded, shouldered or
pointed top, a raised blank panel on its face (no words), standing on a plinth sunk a little in the ground. Weathered:
soot from the town's chimneys gathered on its shoulders, green damp climbing from the foot, and a lean to one side.
Its face is towards -Y.

Options:
    shape    'round' (default): a half-round top; 'shouldered': small square shoulders and a round head between
             them; 'pointed': a Gothic point
    lean     degrees it leans back (+) or forward (-), about its foot (default 4)
    height   metres from the ground to the top of the slab, before the lean (default 1.0)
    seed     the lean's sideways part, the stone's chips, where the soot and damp lie

Where it came from: '/home/claude/build-51-chapel/work/render_final.py', headstone() (line 511): a box, a half
cylinder and a base, in a plain grey; and the soot and damp stains the second builder laid in front of the stones in
'/home/claude/build-51-chapel/dress/dress_block.py' (headstone soot / headstone damp, near line 395). Rebuilt here as
one dressed slab with a panel, a plinth, and the soot and damp in the stone itself.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402

PART = 'headstone'
SHAPES = ('round', 'shouldered', 'pointed')

CARD = {
    'name': PART,
    'what': 'a leaning Victorian headstone: a dressed slab with a round, shouldered or pointed top, a blank panel, on a plinth; '
            'soot on its shoulders, green damp at its foot',
    'size_m': (0.68, 0.24, 1.05),
    'options': {
        'shape': "'round' (default), 'shouldered' or 'pointed': the top of the slab",
        'lean': 'degrees it leans back (+) or forward (-) (default 4)',
        'height': 'metres from the ground to the top of the slab (default 1.0)',
        'seed': 'the sideways part of the lean, chips, where the soot and damp lie (default 0)',
    },
    'materials': ['PART • headstone: weathered stone'],
    'source': "'/home/claude/build-51-chapel/work/render_final.py', headstone() (line 511); the soot and damp stains in "
              "'/home/claude/build-51-chapel/dress/dress_block.py' (near line 395)",
    'views': 'reads from every side; the panel is on the front (-Y) only',
    'trap': 'the plinth is sunk into the ground: its lowest point is 1.5 to 3 cm below z = 0 (the lean decides); on a hard floor lift the part 3 cm',
}


def weathered_stone():
    """Dressed stone, dark and cool (a grey sandstone gone dark in the rain), its colour broken by grain and pale
    mineral patches, pitted in the bump; soot gathering towards the top and running down in streaks, green damp
    climbing from the foot. Reads the object's own number 'stone_height' (the whole stone's height; a point number
    on the mesh does not do, as it is smeared across the slab's big faces) so the stains know where the top is. Made once per file: 'PART • headstone: weathered stone'."""
    def maker(m, nodes, links, principled):
        vec = shapes.own_coordinates(nodes)
        split = nodes.new('ShaderNodeSeparateXYZ')
        links.new(vec, split.inputs['Vector'])
        height = nodes.new('ShaderNodeAttribute')         # the object's own number 'stone_height'
        height.attribute_type = 'OBJECT'
        height.attribute_name = 'stone_height'
        fraction = shapes.math_node(nodes, links, 'DIVIDE', split.outputs['Z'], height.outputs['Fac'])
        # the stone itself
        grain = shapes.noise_fac(nodes, links, vec, 9.0, detail=5.0, roughness=0.6)
        crust = shapes.noise_fac(nodes, links, vec, 2.2, detail=3.0, roughness=0.7)
        pits = shapes.noise_fac(nodes, links, vec, 40.0, detail=3.0, roughness=0.7)
        base = (0.042, 0.048, 0.056)
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, grain, 0.3, 0.7), tuple(c * 0.7 for c in base), tuple(c * 1.3 for c in base))
        colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, crust, 0.58, 0.72, 0.0, 0.7), colour, (0.085, 0.085, 0.08))
        # soot: from about 55 % of the height up, broken by grain, and streaks running down from it
        streaks = nodes.new('ShaderNodeMapping')
        streaks.inputs['Scale'].default_value = (18.0, 18.0, 1.5)
        links.new(vec, streaks.inputs['Vector'])
        runs = shapes.noise_fac(nodes, links, streaks.outputs['Vector'], 1.0, detail=3.0)
        soot_band = shapes.map_range(nodes, links, fraction, 0.5, 0.92, 0.0, 1.0)
        soot = shapes.math_node(nodes, links, 'MULTIPLY', soot_band, shapes.map_range(nodes, links, grain, 0.38, 0.6, 0.55, 1.0))
        run_down = shapes.math_node(nodes, links, 'MULTIPLY', shapes.map_range(nodes, links, fraction, 0.3, 0.9),
                                    shapes.map_range(nodes, links, runs, 0.5, 0.62, 0.0, 0.8))
        soot = shapes.math_node(nodes, links, 'MAXIMUM', soot, run_down)
        colour = shapes.mix_colour(nodes, links, shapes.math_node(nodes, links, 'MULTIPLY', soot, 0.95, clamp=True), colour, (0.010, 0.010, 0.012))
        # damp: from the foot to about 40 % up, green-black, broken by grain
        damp_band = shapes.map_range(nodes, links, fraction, 0.42, 0.02, 0.0, 1.0)
        damp = shapes.math_node(nodes, links, 'MULTIPLY', damp_band, shapes.map_range(nodes, links, grain, 0.4, 0.58, 0.3, 1.0))
        colour = shapes.mix_colour(nodes, links, shapes.math_node(nodes, links, 'MULTIPLY', damp, 0.9, clamp=True), colour, (0.018, 0.034, 0.014))
        links.new(colour, principled.inputs['Base Color'])
        rough = shapes.map_range(nodes, links, grain, 0.3, 0.7, 0.75, 0.9)
        links.new(shapes.mix_float(nodes, links, damp, rough, 0.3), principled.inputs['Roughness'])      # damp is glossier
        principled.inputs['Specular IOR Level'].default_value = 0.35
        pitting = shapes.bump(nodes, links, pits, 0.25, 0.004)
        links.new(shapes.bump(nodes, links, crust, 0.3, 0.01, normal=pitting), principled.inputs['Normal'])
        m.diffuse_color = (0.09, 0.095, 0.1, 1.0)
    return shapes.part_material(PART, 'weathered stone', maker)


def pointed_outline(hw, spring, r, cx):
    """A Gothic arch outline in (x, z) from its foot at 0: straight sides at +-hw up to the spring line, then two arcs
    of radius r whose centres are at (-cx, spring) for the right arc and (cx, spring) for the left, meeting in a point
    at x = 0. An equilateral arch (the slab) has r = 2 hw and cx = hw; an outline inset from it by m keeps the same
    centres with r - m and hw - m, so the margin is even all round."""
    a_max = math.acos(cx / r)
    pts = [(-hw, 0.0), (hw, 0.0), (hw, spring)]
    for k in range(1, 12):
        a = a_max * k / 12
        pts.append((-cx + r * math.cos(a), spring + r * math.sin(a)))
    pts.append((0.0, spring + r * math.sin(a_max)))
    for k in range(11, 0, -1):
        a = a_max * k / 12
        pts.append((cx - r * math.cos(a), spring + r * math.sin(a)))
    pts.append((-hw, spring))
    return pts


def outline(shape, width, height, thickness):
    """The slab's face outline in (x, z), anticlockwise seen from the front, from its foot; its top at `height`."""
    hw = width / 2
    pts = [(-hw, 0.0), (hw, 0.0)]
    if shape == 'round':
        r = hw
        top = height - r
        pts.append((hw, top))
        for k in range(1, 16):
            a = math.pi * k / 16
            pts.append((r * math.cos(a), top + r * math.sin(a)))
        pts.append((-hw, top))
    elif shape == 'shouldered':
        shoulder = width * 0.14
        r = hw - shoulder
        rise = height - r
        pts += [(hw, rise - shoulder * 0.5), (hw - shoulder, rise - shoulder * 0.5), (hw - shoulder, rise)]
        for k in range(1, 14):
            a = math.pi * k / 14
            pts.append((r * math.cos(a), rise + r * math.sin(a)))
        pts += [(-hw + shoulder, rise), (-hw + shoulder, rise - shoulder * 0.5), (-hw, rise - shoulder * 0.5)]
    else:   # pointed: an equilateral Gothic arch, two arcs of radius `width` meeting in a point at `height`
        spring = height - width * math.sin(math.pi / 3)
        pts = pointed_outline(hw, spring, width, hw)
    return pts


def build(collection, seed=0, shape='round', lean=4.0, height=1.0):
    if shape not in SHAPES:
        raise ValueError("headstone shape is one of %s, not %r" % (', '.join(repr(s) for s in SHAPES), shape))
    rng = shapes.rng_for(PART, seed)
    stone = weathered_stone()
    objects = []
    height = float(height)
    width = min(0.62, max(0.42, height * 0.56 + rng.uniform(-0.02, 0.02)))
    thickness = 0.09 + rng.uniform(-0.005, 0.01)
    sink = 0.015                                  # the plinth sunk into the grass (its lowest point stays within 3 cm of z = 0, see the end)
    plinth_h = 0.14
    plinth_top = plinth_h - sink
    slab_h = height - plinth_top

    def finish(piece, name):
        """The piece is built in the part's frame, so its own Z is height; the object carries the whole height."""
        obj = piece.finish(name, collection, stone, smooth=True, sharp=30, chamfer=0.004, chamfer_segments=2)
        obj['stone_height'] = height
        return obj

    # the slab: its outline in (x, z) given thickness along y
    face = outline(shape, width, slab_h, thickness)
    to_xz = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))    # (x, y) outline -> (x, z) plane, thickness along y
    slab = shapes.Shape()
    slab.prism(face, -thickness / 2, thickness / 2, Matrix.Translation((0, 0, plinth_top)) @ to_xz)
    objects.append(finish(slab, 'headstone slab'))
    # the raised blank panel on the face: a frame of four strips and the tablet inside, proud of the slab
    panel_w = width * 0.74
    panel_bottom = slab_h * 0.12
    y_face = -thickness / 2
    panel = shapes.Shape()
    strip = 0.03
    proud = 0.006
    if shape == 'pointed':
        # the panel follows the point: a pointed border (proud) with a pointed tablet standing on it (prouder), both
        # inset evenly from the slab's own arch (the same arc centres, smaller radii)
        margin = (width - panel_w) / 2
        spring = slab_h - width * math.sin(math.pi / 3) - panel_bottom
        border = pointed_outline(panel_w / 2, spring, width - margin, width / 2)
        tablet = pointed_outline(panel_w / 2 - strip, spring, width - margin - strip, width / 2)
        lift = Matrix.Translation((0, 0, plinth_top + panel_bottom)) @ to_xz
        panel.prism(border, y_face - proud, y_face + 0.002, lift)
        panel.prism(tablet, y_face - proud - 0.006, y_face, lift)
    else:
        panel_top = (slab_h - width / 2) * 0.92
        panel.box((0.0, y_face - proud / 2, plinth_top + (panel_top + panel_bottom) / 2), (panel_w, proud, panel_top - panel_bottom))
        frame_pts = [((-panel_w / 2 + strip / 2), (panel_top + panel_bottom) / 2, strip, panel_top - panel_bottom),
                     ((panel_w / 2 - strip / 2), (panel_top + panel_bottom) / 2, strip, panel_top - panel_bottom),
                     (0.0, panel_top - strip / 2, panel_w - 2 * strip, strip), (0.0, panel_bottom + strip / 2, panel_w - 2 * strip, strip)]
        for (x, z, w, h) in frame_pts:
            panel.box((x, y_face - proud - 0.003, plinth_top + z), (w, 0.006, h))
    objects.append(finish(panel, 'headstone panel'))
    # the plinth: a block wider than the slab, its top edge chamfered, sunk a little
    plinth = shapes.Shape()
    pw, pd = width + 0.14, thickness + 0.14
    plinth.frustum((0.0, 0.0, -sink), (pw / 2, pd / 2), (pw / 2 - 0.02, pd / 2 - 0.02), plinth_h)
    objects.append(finish(plinth, 'headstone plinth'))

    # lean: back (+) about X at the foot, with a smaller sideways part
    side = math.radians(rng.uniform(-2.5, 2.5))
    shapes.tilt_all(objects, rx=-math.radians(float(lean)), ry=side, pivot=(0.0, 0.0, 0.0))
    # the lean drops one corner of the sunk plinth further: keep the lowest point within 3 cm of the ground
    bpy.context.view_layer.update()
    lowest = min((obj.matrix_world @ v.co).z for obj in objects for v in obj.data.vertices)
    if lowest < -0.03:
        for obj in objects:
            obj.matrix_world = Matrix.Translation((0.0, 0.0, -0.03 - lowest)) @ obj.matrix_world
    return objects
