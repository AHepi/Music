"""
What this file is: helpers shared by the town street's shop and window parts (shop_front, dormer, window_dressing,
boarded_window, window_box, sign_board, stair_door), made from the three street builders' script (log 55). It is not a
part (its name starts with '_', so the store does not list it). It adds to the chapel and barn helpers
(_shapes_chapel.py, imported here as `shapes`; _shapes_barn.py as `barn`):

    choice(name, value, allowed), flag(name, value)   check an option, with a plain message
    hidden_light(collection, name, location, power)   a small warm point light the camera does not see
    see_through_glass(part)        'PART • <part>: grimy window glass': real glass you see through, greyed and smeared;
                                   give the object visible_shadow = False so a light behind it gets out
    glow(part, what, colour, z0, z1, low, high)       a warm light-giving surface, brighter towards z1 (a lamp-lit back
                                   wall, a lit pane) and a little uneven
    cloth(part, what, colour, sheer, lit)             cloth: a weave in the bump, faded and sooted, see-through when
                                   sheer (net), lit through from the room when lit
    lead(part)                     old lead flashings: dull blue-grey with a pale bloom
    painted_board(part, what, paint)                  painted timber, faded, the paint peeling to grey wood
    goods(part)                    jars and tins on a shop's shelves, each its own colour (reads the face number 'tone')
    sash_window(wood, glass, ...)  a sash window into two Shapes: box frame, sill, two sashes with glazing bars; returns
                                   its panes so a caller can glaze, break or board them
    rust_run(shape, x0, x1, top, length, y, rng)      a rust run down a wall from an iron fixing (the 'fade' number for
                                   'MADE • rust stain'); make the layer first: barn.number_layers(shape, points=('fade',))
"""

import math

import bpy
from mathutils import Matrix, Vector

import _shapes_chapel as shapes
import _shapes_barn as barn

WOOD = 'WOOD • peeling dark painted doors'
IRON = 'IRON • soot-black lamp posts'
RUST = 'RUST • rain-aged iron'
NAILS = 'MADE • rusty nail heads'
STAIN = 'MADE • rust stain'
STONE = 'STONE • worn honey-grey architectural dressings'
SLATE = 'MADE • slate roof'
LIT_GLASS = 'GLASS • warm occupied interiors'
DARK_GLASS = 'GLASS • sleeping navy interiors'
RECESS = 'RECESSES • near-black blue'
BRASS = 'MADE • old brass'
WARM = (1.0, 0.62, 0.30)


def choice(name, value, allowed):
    if value not in allowed:
        raise ValueError('%s is one of %s, not %r' % (name, ', '.join(repr(a) for a in allowed), value))
    return value


def flag(name, value):
    if value not in (True, False):
        raise ValueError('%s is True or False, not %r' % (name, value))
    return bool(value)


def hidden_light(collection, name, location, power, colour=WARM, radius=0.08):
    """A small warm point light the camera does not see (it lights what is near it)."""
    obj = shapes.point_light(collection, name, location, power, colour=colour, radius=radius)
    obj.visible_camera = False
    return obj


# ---------------------------------------------------------------------------------------------------- materials

def see_through_glass(part, what='grimy window glass'):
    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        grime = shapes.noise_fac(nodes, links, vec, 5.0, detail=4.0, roughness=0.6)
        streak_map = nodes.new('ShaderNodeMapping')
        streak_map.inputs['Scale'].default_value = (18.0, 18.0, 1.5)
        links.new(vec, streak_map.inputs['Vector'])
        streak = shapes.noise_fac(nodes, links, streak_map.outputs['Vector'], 1.0, detail=3.0)
        dirt = shapes.math_node(nodes, links, 'MAXIMUM', shapes.map_range(nodes, links, grime, 0.45, 0.8),
                                shapes.map_range(nodes, links, streak, 0.5, 0.75, 0.0, 0.6))
        p.inputs['Base Color'].default_value = (0.72, 0.74, 0.70, 1.0)
        p.inputs['Transmission Weight'].default_value = 1.0
        p.inputs['IOR'].default_value = 1.45
        links.new(shapes.map_range(nodes, links, dirt, 0.0, 1.0, 0.02, 0.3), p.inputs['Roughness'])
        m.diffuse_color = (0.05, 0.07, 0.08, 1.0)
    return shapes.part_material(part, what, maker)


def glow(part, what, colour, z0, z1, low, high, unevenness=0.3, scale=2.5):
    """A light-giving surface: emission from `low` at height z0 to `high` at z1 (in the object's own coordinates),
    broken by a soft noise; dark and rough underneath, so it is not a flat sheet of light."""
    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        sep = nodes.new('ShaderNodeSeparateXYZ')
        links.new(vec, sep.inputs[0])
        ramp = shapes.map_range(nodes, links, sep.outputs['Z'], z0, z1, low, high)
        n = shapes.noise_fac(nodes, links, vec, scale, detail=3.0)
        uneven = shapes.map_range(nodes, links, n, 0.3, 0.7, 1.0 - unevenness, 1.0 + unevenness)
        links.new(shapes.math_node(nodes, links, 'MULTIPLY', ramp, uneven), p.inputs['Emission Strength'])
        p.inputs['Emission Color'].default_value = tuple(colour) + (1.0,)
        p.inputs['Base Color'].default_value = tuple(c * 0.25 for c in colour) + (1.0,)
        p.inputs['Roughness'].default_value = 0.9
        m.diffuse_color = tuple(colour) + (1.0,)
    return shapes.part_material(part, what, maker)


def cloth(part, what, colour, sheer=False, lit=False, weave=260.0):
    """Cloth: a fine weave in the bump, faded in patches and greyed by soot; a sheer net lets the dark through in a
    lace of holes; lit, it glows warm where the room's light comes through it."""
    name = what + (', lit through' if lit else '')

    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        wave = nodes.new('ShaderNodeTexWave')
        wave.inputs['Scale'].default_value = weave
        wave.inputs['Distortion'].default_value = 1.5
        links.new(vec, wave.inputs['Vector'])
        fade = shapes.noise_fac(nodes, links, vec, 3.0, detail=4.0)
        base = tuple(colour)
        faded = tuple(min(1.0, c * 1.35 + 0.02) for c in base)
        sooted = tuple(c * 0.55 for c in base)
        col = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, fade, 0.35, 0.7), sooted, base)
        col = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, fade, 0.6, 0.8, 0.0, 0.7), col, faded)
        links.new(col, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.92
        p.inputs['Sheen Weight'].default_value = 0.3
        links.new(shapes.bump(nodes, links, wave.outputs['Fac'], 0.12, 0.001), p.inputs['Normal'])
        if sheer:
            lace = nodes.new('ShaderNodeTexVoronoi')
            lace.inputs['Scale'].default_value = 90.0
            links.new(vec, lace.inputs['Vector'])
            links.new(shapes.map_range(nodes, links, lace.outputs['Distance'], 0.15, 0.45, 0.35, 0.9), p.inputs['Alpha'])
        if lit:
            p.inputs['Emission Color'].default_value = (1.0, 0.45, 0.16, 1.0)
            links.new(shapes.map_range(nodes, links, fade, 0.2, 0.8, 0.22, 0.45), p.inputs['Emission Strength'])
        m.diffuse_color = tuple(base) + (1.0,)
    return shapes.part_material(part, name, maker)


def lead(part):
    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        bloom = shapes.noise_fac(nodes, links, vec, 9.0, detail=5.0, roughness=0.65)
        streak_map = nodes.new('ShaderNodeMapping')
        streak_map.inputs['Scale'].default_value = (22.0, 22.0, 2.0)
        links.new(vec, streak_map.inputs['Vector'])
        streak = shapes.noise_fac(nodes, links, streak_map.outputs['Vector'], 1.0, detail=3.0)
        col = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, bloom, 0.5, 0.75), (0.085, 0.092, 0.10), (0.20, 0.205, 0.20))
        col = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, streak, 0.45, 0.7, 0.0, 0.6), col, (0.03, 0.032, 0.035))
        links.new(col, p.inputs['Base Color'])
        p.inputs['Metallic'].default_value = 0.35
        links.new(shapes.map_range(nodes, links, bloom, 0.3, 0.8, 0.38, 0.75), p.inputs['Roughness'])
        links.new(shapes.bump(nodes, links, bloom, 0.25, 0.004), p.inputs['Normal'])
        m.diffuse_color = (0.1, 0.105, 0.11, 1.0)
    return shapes.part_material(part, 'old lead', maker)


PAINTS = {'cream': (0.30, 0.255, 0.165), 'green': (0.022, 0.05, 0.03), 'red': (0.17, 0.03, 0.02), 'black': (0.018, 0.018, 0.02),
          'brown': (0.07, 0.04, 0.022)}


def painted_board(part, what, paint):
    """Painted timber, faded by the weather, the paint cracked and peeling in patches to grey wood, grime gathered low."""
    colour = PAINTS[paint] if isinstance(paint, str) else paint

    def maker(m, nodes, links, p):
        vec = shapes.own_coordinates(nodes)
        peel = shapes.noise_fac(nodes, links, vec, 3.5, detail=6.0, roughness=0.66)
        fade = shapes.noise_fac(nodes, links, vec, 2.0, detail=3.0)
        grain_map = nodes.new('ShaderNodeMapping')
        grain_map.inputs['Scale'].default_value = (2.0, 60.0, 60.0)
        links.new(vec, grain_map.inputs['Vector'])
        grain = shapes.noise_fac(nodes, links, grain_map.outputs['Vector'], 1.0, detail=4.0)
        paint_col = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, fade, 0.3, 0.7), tuple(c * 0.75 for c in colour),
                                      tuple(min(1.0, c * 1.3 + 0.015) for c in colour))
        wood = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, grain, 0.3, 0.7), (0.06, 0.055, 0.045), (0.12, 0.11, 0.09))
        bare = shapes.map_range(nodes, links, peel, 0.56, 0.585)
        col = shapes.mix_colour(nodes, links, bare, paint_col, wood)
        links.new(col, p.inputs['Base Color'])
        links.new(shapes.map_range(nodes, links, bare, 0.0, 1.0, 0.55, 0.85), p.inputs['Roughness'])
        edge = shapes.bump(nodes, links, bare, -0.4, 0.002)
        links.new(shapes.bump(nodes, links, grain, 0.15, 0.002, normal=edge), p.inputs['Normal'])
        m.diffuse_color = tuple(colour) + (1.0,)
    return shapes.part_material(part, what, maker)


GOODS_COLOURS = [(0.0, (0.16, 0.025, 0.02)), (0.18, (0.03, 0.045, 0.11)), (0.34, (0.26, 0.20, 0.10)), (0.5, (0.22, 0.13, 0.025)),
                 (0.64, (0.03, 0.07, 0.035)), (0.78, (0.08, 0.035, 0.015)), (0.9, (0.30, 0.27, 0.21))]


def goods(part):
    """Tins and jars on shop shelves: each item its own colour from the face number 'tone' (0..1): red, blue, buff,
    mustard, green, brown, cream paper labels; tins a little shiny."""
    def maker(m, nodes, links, p):
        tone = nodes.new('ShaderNodeAttribute')
        tone.attribute_type = 'GEOMETRY'
        tone.attribute_name = 'tone'
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.interpolation = 'CONSTANT'
        elements = ramp.color_ramp.elements
        elements[0].position, elements[0].color = GOODS_COLOURS[0][0], GOODS_COLOURS[0][1] + (1.0,)
        elements[1].position, elements[1].color = GOODS_COLOURS[1][0], GOODS_COLOURS[1][1] + (1.0,)
        for pos, col in GOODS_COLOURS[2:]:
            e = elements.new(pos)
            e.color = col + (1.0,)
        links.new(tone.outputs['Fac'], ramp.inputs['Fac'])
        links.new(ramp.outputs['Color'], p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.42
        p.inputs['Metallic'].default_value = 0.25
        m.diffuse_color = (0.12, 0.06, 0.03, 1.0)
    return shapes.part_material(part, 'tins and jars', maker)


def jar_glass(part):
    """Sweet jars and bottles: dark glass with something in it, glossy."""
    def maker(m, nodes, links, p):
        tone = nodes.new('ShaderNodeAttribute')
        tone.attribute_type = 'GEOMETRY'
        tone.attribute_name = 'tone'
        col = shapes.mix_colour(nodes, links, tone.outputs['Fac'], (0.20, 0.07, 0.015), (0.05, 0.08, 0.03))
        links.new(col, p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = 0.08
        p.inputs['Specular IOR Level'].default_value = 0.8
        p.inputs['Coat Weight'].default_value = 0.6
        m.diffuse_color = (0.15, 0.06, 0.02, 1.0)
    return shapes.part_material(part, 'jars, glass', maker)


# ---------------------------------------------------------------------------------------------------- a sash window

def sash_window(wood, glass, cx, y0, z0, w, h, bars=1, frame_w=0.075, depth=0.13, sill=True):
    """A box-framed sash window filling an opening `w` x `h` whose outer face is the plane y = y0 (outside towards -Y),
    its foot at z0: jambs, head and (if `sill`) a sloped timber sill into `wood`; an upper sash in the outer runway and a
    lower sash 4 cm further in, each with `bars` upright glazing bars, into `wood`; the glass of each pane into `glass`
    (a Shape) unless glass is None. Returns the panes as dicts: x0, x1, z0, z1, y (the glass plane), sash
    ('upper' or 'lower')."""
    x_l, x_r = cx - w / 2, cx + w / 2
    wood.box((x_l + frame_w / 2, y0 + depth / 2, z0 + h / 2), (frame_w, depth, h))
    wood.box((x_r - frame_w / 2, y0 + depth / 2, z0 + h / 2), (frame_w, depth, h))
    wood.box((cx, y0 + depth / 2, z0 + h - frame_w / 2), (w, depth - 0.006, frame_w))      # 3 mm in from the jambs' faces
    sill_h = 0.06
    if sill:
        # the sill, sloping out and standing proud, its nose throwing the rain off
        rot = Matrix.Rotation(math.radians(-8), 3, 'X')
        wood.box((cx, y0 + depth / 2 - 0.035, z0 + sill_h / 2), (w + 0.07, depth + 0.07, sill_h), rotation=rot)
    ix0, ix1 = x_l + frame_w, x_r - frame_w
    iz0, iz1 = z0 + sill_h, z0 + h - frame_w
    mid = (iz0 + iz1) / 2
    stile, top_rail, bottom_rail, meet, bar_w = 0.045, 0.05, 0.075, 0.035, 0.022
    panes = []
    for sash, (sz0, sz1, y) in (('upper', (mid - meet / 2, iz1, y0 + 0.03)), ('lower', (iz0, mid + meet / 2, y0 + 0.07))):
        t = 0.04
        wood.box((ix0 + stile / 2, y + t / 2, (sz0 + sz1) / 2), (stile, t, sz1 - sz0))
        wood.box((ix1 - stile / 2, y + t / 2, (sz0 + sz1) / 2), (stile, t, sz1 - sz0))
        low_rail = meet if sash == 'upper' else bottom_rail
        high_rail = top_rail if sash == 'upper' else meet
        # rails 2 mm shallower than the stiles on each face: faces lying in one plane where members cross draw black
        wood.box(((ix0 + ix1) / 2, y + t / 2, sz0 + low_rail / 2), (ix1 - ix0, t - 0.004, low_rail))
        wood.box(((ix0 + ix1) / 2, y + t / 2, sz1 - high_rail / 2), (ix1 - ix0, t - 0.004, high_rail))
        gx0, gx1 = ix0 + stile, ix1 - stile
        gz0, gz1 = sz0 + low_rail, sz1 - high_rail
        cells = bars + 1
        cell = (gx1 - gx0 - bars * bar_w) / cells
        for k in range(bars):
            bx = gx0 + (k + 1) * cell + k * bar_w + bar_w / 2
            wood.box((bx, y + t / 2, (gz0 + gz1) / 2), (bar_w, t * 0.8, gz1 - gz0))
        for k in range(cells):
            px0 = gx0 + k * (cell + bar_w)
            pane = {'x0': px0, 'x1': px0 + cell, 'z0': gz0, 'z1': gz1, 'y': y + t / 2, 'sash': sash}
            panes.append(pane)
            if glass is not None:
                glass.box(((pane['x0'] + pane['x1']) / 2, pane['y'], (gz0 + gz1) / 2), (cell + 0.01, 0.004, gz1 - gz0 + 0.01))
    return panes


# ---------------------------------------------------------------------------------------------------- rust

def rust_run(shape, x0, x1, top, length, y, rng, low=0.0, cols=10, rows=6, full=False):
    """A rust run down a wall in the plane y (facing -Y), from x0..x1 at `top`, running down about `length` metres in
    uneven fingers, never below `low`; `full`: the middle finger runs the whole length (so the run's foot is known).
    Writes the point number 'fade' (make the layer first)."""
    fade_layer = shape.bm.verts.layers.float['fade']
    runs = [rng.uniform(0.35, 1.0) * length for _ in range(cols + 1)]
    if full:
        runs[cols // 2] = length
    grid = []
    for i in range(cols + 1):
        x = x0 + (x1 - x0) * i / cols
        column = []
        for j in range(rows + 1):
            z = max(low, top - runs[i] * j / rows)
            v = shape.bm.verts.new((x, y, z))
            edge = min(i, cols - i) / 2.0
            v[fade_layer] = min(1.0, j / rows + max(0.0, 1.0 - edge) * 0.6)
            column.append(v)
        grid.append(column)
    for i in range(cols):
        for j in range(rows):
            shape._face([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]])
