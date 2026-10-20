# What this does: ready-made SEAMLESS building blocks (Blender shader node groups) that go beyond lib/recipe_tools.py, found and tested in the seamless-tiles research:
#   tileable_bricks_group()  a brick wall (or planks, or tiles: set Offset 0 for a plain grid) whose brick numbers WRAP at the tile edge, so even the random value of the
#                            half brick on the right edge equals the one on the left edge. Plain Blender Brick texture cannot do this (its random colours break at the edge).
#   tileable_wave_group()    wavy bands (wood grain, ripples, stripes): a Wave texture with a WHOLE number of bands across the tile, bent by a tileable noise so it stays seamless.
# Use (inside Blender):  sys.path.insert(0, '<this folder>');  import tileable_pattern_groups as tpg;  node.node_tree = tpg.tileable_bricks_group()
# Tested with recipe_tiling_test.py (see test_recipes/bricks_recipe.py): every output repeats exactly when the coordinate moves by whole tiles.
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib'))
import recipe_tools as rt  # noqa: E402


def _math(w, name, operation, a, b=None):
    """Math node: a and b are numbers or (node_name, socket_name_or_index) pairs; returns (name, 0)."""
    node = w.math(name, operation, None, None)
    for index, value in enumerate((a, b)):
        if value is None:
            continue
        if isinstance(value, (int, float)):
            node.inputs[index].default_value = float(value)
        else:
            w.link(value[0], value[1], name, index)
    return (name, 0)


def tileable_bricks_group(name='Tileable Bricks'):
    """Inputs: Vector (tile coordinate 0..1), Bricks across (a WHOLE number, default 8), Rows (a WHOLE number, EVEN when Offset is not 0, default 16),
    Offset (0.5 = every second row shifted by half a brick; 0 = plain grid), Mortar width (full width in tile units, default 0.012), Seed.
    Outputs: Brick mask (1 on a brick, 0 on mortar), Random (0..1, one value per brick, the same for the two halves of a brick cut by the tile edge),
    Edge distance (distance to the nearest brick edge in tile units), Local x and Local y (0..1 across the brick), Brick number (0..Bricks-1) and Row number (0..Rows-1)."""
    existing = bpy.data.node_groups.get(name)
    if existing:
        return existing
    tree, w = rt.make_group_tree(name, [
        ('Vector', 'NodeSocketVector', (0, 0, 0)), ('Bricks across', 'NodeSocketFloat', 8.0), ('Rows', 'NodeSocketFloat', 16.0), ('Offset', 'NodeSocketFloat', 0.5),
        ('Mortar width', 'NodeSocketFloat', 0.012), ('Seed', 'NodeSocketFloat', 0.0)],
        [('Brick mask', 'NodeSocketFloat'), ('Random', 'NodeSocketFloat'), ('Edge distance', 'NodeSocketFloat'), ('Local x', 'NodeSocketFloat'),
         ('Local y', 'NodeSocketFloat'), ('Brick number', 'NodeSocketFloat'), ('Row number', 'NodeSocketFloat')])
    w.add('ShaderNodeSeparateXYZ', 'uv', x=-3)
    w.link('in', 'Vector', 'uv', 'Vector')
    y = _math(w, 'y', 'MULTIPLY', ('uv', 'Y'), ('in', 'Rows'))
    row = _math(w, 'row', 'FLOOR', y)
    fy = _math(w, 'fy', 'FRACT', y)
    odd = _math(w, 'odd', 'FLOORED_MODULO', row, 2.0)
    shift = _math(w, 'shift', 'MULTIPLY', odd, ('in', 'Offset'))
    x = _math(w, 'x', 'MULTIPLY', ('uv', 'X'), ('in', 'Bricks across'))
    xs = _math(w, 'xs', 'ADD', x, shift)
    col = _math(w, 'col', 'FLOOR', xs)
    fx = _math(w, 'fx', 'FRACT', xs)
    col_wrapped = _math(w, 'colw', 'FLOORED_MODULO', col, ('in', 'Bricks across'))      # the heart of it: brick number wraps round the tile
    row_wrapped = _math(w, 'roww', 'FLOORED_MODULO', row, ('in', 'Rows'))
    w.add('ShaderNodeCombineXYZ', 'id')
    w.link(col_wrapped[0], col_wrapped[1], 'id', 'X')
    w.link(row_wrapped[0], row_wrapped[1], 'id', 'Y')
    w.link('in', 'Seed', 'id', 'Z')
    w.add('ShaderNodeTexWhiteNoise', 'rand', noise_dimensions='3D')
    w.link('id', 'Vector', 'rand', 'Vector')
    dx = _math(w, 'dx', 'DIVIDE', _math(w, 'mx', 'MINIMUM', fx, _math(w, 'ifx', 'SUBTRACT', 1.0, fx)), ('in', 'Bricks across'))
    dy = _math(w, 'dy', 'DIVIDE', _math(w, 'my', 'MINIMUM', fy, _math(w, 'ify', 'SUBTRACT', 1.0, fy)), ('in', 'Rows'))
    edge = _math(w, 'edge', 'MINIMUM', dx, dy)
    half_mortar = _math(w, 'half', 'MULTIPLY', ('in', 'Mortar width'), 0.5)
    mask = _math(w, 'mask', 'GREATER_THAN', edge, half_mortar)
    w.link(mask[0], mask[1], 'out', 'Brick mask')
    w.link('rand', 'Value', 'out', 'Random')
    w.link(edge[0], edge[1], 'out', 'Edge distance')
    w.link(fx[0], fx[1], 'out', 'Local x')
    w.link(fy[0], fy[1], 'out', 'Local y')
    w.link(col_wrapped[0], col_wrapped[1], 'out', 'Brick number')
    w.link(row_wrapped[0], row_wrapped[1], 'out', 'Row number')
    return tree


def tileable_wave_group(name='Tileable Wave'):
    """Inputs: Vector, Bands (a WHOLE number of bands across the tile, default 6), Warp (how far the tileable noise bends the bands, in tile widths, default 0.08),
    Warp scale (features of the bending noise per tile, default 3), Detail (default 3), Seed, Sharpness 1 = sine profile (smooth). Output: Fac (0..1).
    The bands run up and down the picture (across x). Rotating the bands is NOT supported (a tilted wave does not repeat per tile unless its tilt is a whole number of bands)."""
    existing = bpy.data.node_groups.get(name)
    if existing:
        return existing
    tree, w = rt.make_group_tree(name, [
        ('Vector', 'NodeSocketVector', (0, 0, 0)), ('Bands', 'NodeSocketFloat', 6.0), ('Warp', 'NodeSocketFloat', 0.08), ('Warp scale', 'NodeSocketFloat', 3.0),
        ('Detail', 'NodeSocketFloat', 3.0), ('Seed', 'NodeSocketFloat', 0.0)], [('Fac', 'NodeSocketFloat')])
    w.add('ShaderNodeSeparateXYZ', 'uv', x=-3)
    w.link('in', 'Vector', 'uv', 'Vector')
    noise = w.add('ShaderNodeGroup', 'warp noise')
    noise.node_tree = rt.tileable_noise_group()
    w.link('in', 'Vector', 'warp noise', 'Vector')
    w.link('in', 'Warp scale', 'warp noise', 'Scale')
    w.link('in', 'Detail', 'warp noise', 'Detail')
    w.link('in', 'Seed', 'warp noise', 'Seed')
    centred = _math(w, 'centred', 'SUBTRACT', ('warp noise', 'Fac'), 0.5)
    bend = _math(w, 'bend', 'MULTIPLY', centred, ('in', 'Warp'))
    bent_u = _math(w, 'bent u', 'ADD', ('uv', 'X'), bend)
    w.add('ShaderNodeCombineXYZ', 'bent')
    w.link(bent_u[0], bent_u[1], 'bent', 'X')
    w.link('uv', 'Y', 'bent', 'Y')
    w.add('ShaderNodeTexWave', 'wave', wave_type='BANDS', bands_direction='X', wave_profile='SIN', Distortion=0.0, Detail=0.0, Phase__Offset=0.0)
    w.link('bent', 'Vector', 'wave', 'Vector')
    scale = _math(w, 'scale', 'MULTIPLY', ('in', 'Bands'), math.pi / 10.0)                  # Wave: one band is 2*pi/20 in scaled units
    w.link(scale[0], scale[1], 'wave', 'Scale')
    w.link('wave', 'Factor', 'out', 'Fac')
    return tree
