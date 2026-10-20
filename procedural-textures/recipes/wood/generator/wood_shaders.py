# What this does (plain words): the SHADER part of the wood generator (it runs inside Blender). It builds one reusable node group, "Wood Grain Gain", that makes the
# FINE hand-painted structure of the wood: thin horizontal light and dark "dry brush" streaks and hair-thin dark lines between splinters. Its output is a
# brightness factor (1.0 = leave the colour alone, above 1 = lighter streak, below 1 = darker streak or line) that the generator multiplies into the colour of the
# flat shapes. It is made of three Blender tools:
#   - seamless stretched noise (Blender's own Noise texture is not seamless, so it is read from the surface of a 4-D donut; different numbers of features
#     across and up stretch it into long thin streaks)            -> light and dark streaks by cutting the noise at two levels (hard cut = painted look)
#   - seamless stretched Voronoi cells, "Distance to Edge" -> thin lines along the borders of long thin cells = hairline cracks between splinter strips
#   - Math / Map Range nodes that turn those into one brightness factor.
# Every number comes from the description file (maps.grain), nothing is read from a picture.
import math

import bpy

import recipe_tools as rt


def _donut(w, name, scale_u, scale_v, seed, x=0, y=0):
    """Tile coordinate (u, v) -> 4 numbers that go round in circles (so the pattern repeats exactly), with `scale_u` features across the tile and `scale_v` up it."""
    w.add('ShaderNodeSeparateXYZ', name + ' split', x=x, y=y)
    w.link('uv in', 0, name + ' split', 'Vector')
    for axis, label in (('X', 'u'), ('Y', 'v')):
        w.math(f'{name} turns {label}', 'MULTIPLY', None, 2 * math.pi, x=x + 1, y=y)
        w.link(name + ' split', axis, f'{name} turns {label}', 0)
        w.math(f'{name} cos {label}', 'COSINE', x=x + 2, y=y + 1)
        w.link(f'{name} turns {label}', 0, f'{name} cos {label}', 0)
        w.math(f'{name} sin {label}', 'SINE', x=x + 2, y=y - 1)
        w.link(f'{name} turns {label}', 0, f'{name} sin {label}', 0)
    ru, rv = scale_u / (2 * math.pi), scale_v / (2 * math.pi)
    parts = {}
    for key, source, radius in (('x', 'cos u', ru), ('y', 'sin u', ru), ('z', 'cos v', rv), ('w0', 'sin v', rv)):
        w.math(f'{name} {key}', 'MULTIPLY', None, radius, x=x + 3, y=y)
        w.link(f'{name} {source}', 0, f'{name} {key}', 0)
        parts[key] = f'{name} {key}'
    w.math(f'{name} w', 'ADD', None, seed, x=x + 4, y=y)
    w.link(parts['w0'], 0, f'{name} w', 0)
    w.add('ShaderNodeCombineXYZ', f'{name} xyz', x=x + 4, y=y + 1)
    for key, socket in (('x', 'X'), ('y', 'Y'), ('z', 'Z')):
        w.link(parts[key], 0, f'{name} xyz', socket)
    return f'{name} xyz', f'{name} w'


def grain_gain_group(grain, name='Wood Grain Gain'):
    """Build (once) the node group. grain = {'hatch': {...}, 'hair': {...}} (see the description format). Input 'Vector' = tile coordinate, output 'Gain' (float)."""
    existing = bpy.data.node_groups.get(name)
    if existing:
        bpy.data.node_groups.remove(existing)
    tree, w = rt.make_group_tree(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Gain', 'NodeSocketFloat')])
    w.nodes['uv in'] = w.nodes['in']
    gain_source = None
    hatch, hair = grain.get('hatch'), grain.get('hair')
    pieces = []
    if hatch:
        vec, wcoord = _donut(w, 'hatch', hatch['u'], hatch['v'], hatch.get('seed', 3.0), x=-6, y=3)
        w.add('ShaderNodeTexNoise', 'hatch noise', x=0, y=3, noise_dimensions='4D', noise_type='FBM', normalize=True, Scale=1.0, Detail=hatch.get('detail', 1.5),
              Roughness=hatch.get('roughness', 0.55))
        w.link(vec, 0, 'hatch noise', 'Vector')
        w.link(wcoord, 0, 'hatch noise', 'W')
        # light streaks: noise above light_cut -> 1 (hard step); dark streaks: noise below dark_cut -> 1
        w.add('ShaderNodeMapRange', 'hatch light', x=1, y=4, clamp=True, From__Min=hatch['light_cut'], From__Max=hatch['light_cut'] + hatch.get('softness', 0.004), To__Min=0.0, To__Max=hatch['light_gain'] - 1.0)
        w.link('hatch noise', 'Fac', 'hatch light', 'Value')
        w.add('ShaderNodeMapRange', 'hatch dark', x=1, y=2, clamp=True, From__Min=hatch['dark_cut'], From__Max=hatch['dark_cut'] - hatch.get('softness', 0.004), To__Min=0.0, To__Max=1.0 - hatch['dark_gain'])
        w.link('hatch noise', 'Fac', 'hatch dark', 'Value')
        w.math('hatch gain', 'SUBTRACT', x=2, y=3)
        w.link('hatch light', 'Result', 'hatch gain', 0)
        w.link('hatch dark', 'Result', 'hatch gain', 1)
        w.math('hatch gain plus one', 'ADD', None, 1.0, x=3, y=3)
        w.link('hatch gain', 0, 'hatch gain plus one', 0)
        pieces.append('hatch gain plus one')
    if hair:
        # hair-thin dark lines: where a long thin seamless noise crosses the level 0.5 (the contour lines of a noise stretched along x are long wavy horizontal lines)
        vec, wcoord = _donut(w, 'hair', hair['u'], hair['v'], hair.get('seed', 5.0), x=-6, y=-3)
        w.add('ShaderNodeTexNoise', 'hair noise', x=0, y=-3, noise_dimensions='4D', noise_type='FBM', normalize=True, Scale=1.0, Detail=hair.get('detail', 2.0), Roughness=0.5)
        w.link(vec, 0, 'hair noise', 'Vector')
        w.link(wcoord, 0, 'hair noise', 'W')
        w.math('hair centred', 'SUBTRACT', None, hair.get('level', 0.5), x=1, y=-3)
        w.link('hair noise', 'Fac', 'hair centred', 0)
        w.math('hair distance', 'ABSOLUTE', x=2, y=-3)
        w.link('hair centred', 0, 'hair distance', 0)
        w.add('ShaderNodeMapRange', 'hair line', x=3, y=-3, clamp=True, From__Min=hair['thickness'], From__Max=hair['thickness'] * 0.5, To__Min=0.0, To__Max=1.0 - hair['gain'])
        w.link('hair distance', 0, 'hair line', 'Value')
        w.math('hair factor', 'SUBTRACT', 1.0, None, x=4, y=-3)
        w.link('hair line', 'Result', 'hair factor', 1)
        pieces.append('hair factor')
    if not pieces:
        w.math('no grain', 'ADD', 1.0, 0.0, x=3, y=0)
        pieces.append('no grain')
    last = pieces[0]
    for i, piece in enumerate(pieces[1:]):
        w.math(f'combine {i}', 'MULTIPLY', x=4 + i, y=0)
        w.link(last, 0, f'combine {i}', 0)
        w.link(piece, 0, f'combine {i}', 1)
        last = f'combine {i}'
    w.link(last, 0, 'out', 'Gain')
    return tree
