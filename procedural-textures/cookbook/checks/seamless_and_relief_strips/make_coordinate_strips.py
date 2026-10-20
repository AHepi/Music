# What this does: renders the small "what does this setting do" squares for the guide
# "06 Guide - seamless tiles and coordinates.md", for the tools that had no sweep picture yet:
#   1. voronoi_cells_across  - the seamless (4D donut) Voronoi with 2, 3, 4, 8, 16 cells across the tile
#   2. warp_keeps_tiling     - wavy bands bent by a seamless noise (warp 0, 0.05, 0.15, 0.3) and, as the failure, by plain noise
#   3. stretch_trap          - what happens when you scale the coordinate BEFORE the donut (repeats, or a seam) against the right way
#                              (a different feature count across and up)
#   4. area_or_repeat        - "the tile repeated 2 x 2" against "one area of new content with the tile count doubled"
#   5. texture_coordinate    - the same plain 3D noise fed by UV, Object, Generated, nothing connected, and UV with height 0.5
# Each square is a plain photograph of the tile (no rolling). The plain-Python script finish_strips.py rolls them by half a tile
# (so a seam shows as a cross in the middle), joins them into strips and measures the numbers quoted in the guide.
# Run (Blender 5.2):
#   blender -b --disable-autoexec -t 2 --python make_coordinate_strips.py
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
sys.path.insert(0, os.path.join(PROC, 'lib', 'contrib'))
import sweep_tools as sweeps  # noqa: E402
import builder as recipe_builder  # noqa: E402

WORK = os.path.join(HERE, 'work')
TILE_PIXELS = 256


def grey(builder, value):
    return builder.grey_to_colour(value)


# ---------------------------------------------------------------- 1. seamless Voronoi: cells across the tile
def build_voronoi(cells_across):
    builder = recipe_builder.Builder(f'voronoi cells {cells_across}')
    cells = builder.tvoronoi(cells_across, cells_across, seed=3.0)
    return builder.finish(colour=cells.outputs['Color'], height=0.5)


# ---------------------------------------------------------------- 2. warp that keeps tiling (and one that does not)
def build_warp(setting):
    kind, warp_amount = setting
    builder = recipe_builder.Builder(f'warp {kind} {warp_amount}')
    u, v = builder.uv_xy()
    if kind == 'seamless':
        noise_value = builder.tnoise(3.0, 3.0, detail=2.0, seed=1.7)
    else:
        noise_value = builder.noise(vector=builder.vec(u, v, 0.0), scale=3.0, detail=2.0).outputs['Factor']
    bent_u = builder.add(u, builder.mul(builder.sub(noise_value, 0.5), warp_amount))
    wave = builder.node('ShaderNodeTexWave', wave_type='BANDS', bands_direction='X', wave_profile='SIN')
    builder._put(wave, 'Vector', builder.vec(bent_u, v, 0.0))
    builder._put(wave, 'Scale', 6 * math.pi / 10)   # Scale = k x pi / 10 puts k = 6 whole bands across the tile
    builder._put(wave, 'Distortion', 0.0)
    return builder.finish(colour=wave.outputs['Color'], height=0.5)


# ---------------------------------------------------------------- 3. the stretch trap
def mapped_coordinates(builder, scale_up):
    """A real Mapping node (type Point) with Scale (1, scale_up, 1) on the tile coordinate; returns its u and v."""
    mapping = builder.node('ShaderNodeMapping', vector_type='POINT')
    builder._put(mapping, 'Vector', builder.uv())
    mapping.inputs['Scale'].default_value = (1.0, scale_up, 1.0)
    x, y, z = builder.xyz(mapping.outputs['Vector'])
    return x, y


def build_stretch(setting):
    builder = recipe_builder.Builder(f'stretch {setting}')
    if setting == 'plain':
        value = builder.tnoise(4.0, 4.0, detail=3.0, seed=2.0)
    elif setting == 'mapping_4':
        value = builder.tnoise(4.0, 4.0, detail=3.0, seed=2.0, coords=mapped_coordinates(builder, 4.0))
    elif setting == 'mapping_2_5':
        value = builder.tnoise(4.0, 4.0, detail=3.0, seed=2.0, coords=mapped_coordinates(builder, 2.5))
    elif setting == 'two_counts':
        value = builder.tnoise(4.0, 16.0, detail=3.0, seed=2.0)
    else:
        raise ValueError(setting)
    return builder.finish(colour=grey(builder, builder.maprange(value, 0.3, 0.7)), height=0.5)


# ---------------------------------------------------------------- 4. the tile repeated, or one bigger area
def build_area(setting):
    builder = recipe_builder.Builder(f'area {setting}')
    if setting == 'repeated':
        # the coordinate times 2 before the donut: the same 4-feature tile drawn 2 x 2 times
        mapping = builder.node('ShaderNodeMapping', vector_type='POINT')
        builder._put(mapping, 'Vector', builder.uv())
        mapping.inputs['Scale'].default_value = (2.0, 2.0, 1.0)
        x, y, z = builder.xyz(mapping.outputs['Vector'])
        value = builder.tnoise(4.0, 4.0, detail=4.0, seed=5.0, coords=(x, y))
    else:
        # tile count 2: twice the features across the same 0..1 square = 2 x 2 tiles of NEW content (still seamless as a whole)
        value = builder.tnoise(8.0, 8.0, detail=4.0, seed=5.0)
    return builder.finish(colour=grey(builder, builder.maprange(value, 0.3, 0.7)), height=0.5)


# ---------------------------------------------------------------- 5. Texture Coordinate outputs into plain 3D noise
def build_texture_coordinate(setting):
    builder = recipe_builder.Builder(f'coordinate {setting}')
    noise = builder.node('ShaderNodeTexNoise', noise_dimensions='3D', noise_type='FBM', normalize=True)
    builder._put(noise, 'Scale', 5.0)
    builder._put(noise, 'Detail', 2.0)
    if setting in ('UV', 'Object', 'Generated'):
        coordinates = builder.node('ShaderNodeTexCoord')
        builder._put(noise, 'Vector', coordinates.outputs[setting])
    elif setting == 'UV_height_half':
        coordinates = builder.node('ShaderNodeTexCoord')
        x, y, z = builder.xyz(coordinates.outputs['UV'])
        builder._put(noise, 'Vector', builder.vec(x, y, 0.5))
    elif setting == 'unconnected':
        pass
    else:
        raise ValueError(setting)
    return builder.finish(colour=grey(builder, builder.maprange(noise.outputs['Factor'], 0.3, 0.7)), height=0.5)


def main():
    jobs = [
        ('voronoi_cells_across', build_voronoi, [2, 3, 4, 8, 16],
         ['2 cells across', '3 cells across', '4 cells across', '8 cells across', '16 cells across'], TILE_PIXELS),
        ('warp_keeps_tiling', build_warp,
         [('seamless', 0.0), ('seamless', 0.05), ('seamless', 0.15), ('seamless', 0.3), ('plain', 0.15)],
         ['warp 0', 'warp 0.05', 'warp 0.15', 'warp 0.3', 'warp 0.15 PLAIN noise'], TILE_PIXELS),
        ('stretch_trap', build_stretch, ['plain', 'mapping_4', 'mapping_2_5', 'two_counts'],
         ['4 x 4 features', 'Mapping y x 4 first', 'Mapping y x 2.5 first', '4 across, 16 up'], TILE_PIXELS),
        ('area_or_repeat', build_area, ['repeated', 'area'],
         ['tile repeated 2 x 2', 'tile count 2: new area'], 512),
        ('texture_coordinate', build_texture_coordinate, ['UV', 'Object', 'Generated', 'unconnected', 'UV_height_half'],
         ['UV', 'Object', 'Generated', 'nothing connected', 'UV with z = 0.5'], TILE_PIXELS),
    ]
    only = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for name, build, values, labels, pixels in jobs:
        if only and name not in only:
            continue
        sweeps.render_sweep(build, values, os.path.join(WORK, name), channel='Colour', size=pixels, labels=labels)
        print('[strips] made', name)


main()
