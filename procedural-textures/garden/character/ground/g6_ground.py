"""GROUND builder, step 2: the ground itself. Material 'Moss and earth' keeps its mottled olive-and-brown look and gets
 (1) WORN PATHS from a top-down mask picture (bare reddish earth with ragged grass edges, a few pebble specks),
 (2) a real soft normal map (clods, 3 m tile) in place of the scan's bump as the main relief, plus a slight footfall dish on the paths.
UV maps: 'UVMap' planar (x, y) / 3 m, 'MaskUV' (x, y) / (22, 21) with the ground's corner at 0,0 of the mask.
"""
import os
import bpy
from mathutils import Vector
from g6_common import (N, link, load_image, normal_chain, unlink_input, set_default, hex_lin, planar_uv, track_uv, PFX)

GROUND_OBJECTS = ('Astra / Courtyard receiving ground', 'Courtyard ground source')


def new_mix_color(nt, name, loc):
    n = N(nt, 'ShaderNodeMix', name, loc)
    n.data_type = 'RGBA'
    n.blend_type = 'MIX'
    n.clamp_factor = True
    return n


def new_mix_float(nt, name, loc):
    n = N(nt, 'ShaderNodeMix', name, loc)
    n.data_type = 'FLOAT'
    n.clamp_factor = True
    return n


def mixout(n):
    return next(o for o in n.outputs if o.enabled)


MIX_FAC, MIX_A_F, MIX_B_F, MIX_A_C, MIX_B_C = 0, 2, 3, 6, 7


def add_ground_uvs():
    for nm in GROUND_OBJECTS:
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        for lay, tile, off in (('UVMap', (3.0, 3.0), (0.0, 0.0)), ('MaskUV', (22.0, 21.0), (0.5, 8.5 / 21.0))):
            track_uv(ob, lay)
            planar_uv(ob.data, lay, tile, off, matrix=ob.matrix_world)


def upgrade_ground_material(maps_dir, opts):
    mat = bpy.data.materials['Moss and earth']
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    gm = nt.nodes['WK groundmoss']
    img_mask = load_image(os.path.join(maps_dir, 'path_mask.png'), 'G6 path_mask', non_color=True)
    img_nrm = load_image(os.path.join(maps_dir, 'ground_normal.png'), 'G6 ground_normal', non_color=True)

    # ---- the path mask: R bare earth, G footfall dish, B pebble specks (UV = MaskUV)
    uvm = N(nt, 'ShaderNodeUVMap', 'mask UV', (-1700, -900))
    uvm.uv_map = 'MaskUV'
    tm = N(nt, 'ShaderNodeTexImage', 'path mask', (-1500, -900))
    tm.image = img_mask
    tm.interpolation = 'Linear'
    tm.extension = 'EXTEND'
    link(nt, uvm, 'UV', tm, 'Vector')
    sep = N(nt, 'ShaderNodeSeparateColor', 'mask split', (-1250, -900))
    link(nt, tm, 'Color', sep, 'Color')

    # ---- crisp, ragged edge at any distance: the 1 cm picture is bent by a fine noise and re-sharpened (no stair-steps up close)
    geo0 = N(nt, 'ShaderNodeNewGeometry', 'edge geo', (-1700, -1050))
    ez = N(nt, 'ShaderNodeTexNoise', 'edge noise', (-1500, -1050))
    ez.noise_dimensions = '3D'
    ez.inputs['Scale'].default_value = 38.0
    ez.inputs['Detail'].default_value = 3.0
    ez.inputs['Roughness'].default_value = 0.55
    link(nt, geo0, 'Position', ez, 'Vector')
    ea = N(nt, 'ShaderNodeMath', 'edge bend', (-1250, -1050))
    ea.operation = 'ADD'
    link(nt, sep, 'Red', ea, 0)
    eb = N(nt, 'ShaderNodeMath', 'edge noise centred', (-1250, -1200))
    eb.operation = 'MULTIPLY_ADD'
    eb.inputs[1].default_value = 0.42
    eb.inputs[2].default_value = -0.21
    link(nt, ez, 'Fac', eb, 0)
    link(nt, eb, 0, ea, 1)
    bare = N(nt, 'ShaderNodeMapRange', 'bare earth', (-1050, -1050))
    bare.interpolation_type = 'SMOOTHSTEP'
    bare.inputs['From Min'].default_value = 0.34
    bare.inputs['From Max'].default_value = 0.62
    link(nt, ea, 0, bare, 'Value')
    BARE = bare.outputs['Result']

    # ---- bare earth colour: reddish brown with soft blotches (darker than the raked gravel)
    geo = N(nt, 'ShaderNodeNewGeometry', 'earth geo', (-1700, -1250))
    nz = N(nt, 'ShaderNodeTexNoise', 'earth blotch', (-1500, -1250))
    nz.noise_dimensions = '3D'
    nz.inputs['Scale'].default_value = 1.7
    nz.inputs['Detail'].default_value = 2.0
    nz.inputs['Roughness'].default_value = 0.5
    link(nt, geo, 'Position', nz, 'Vector')
    ramp = N(nt, 'ShaderNodeValToRGB', 'earth ramp', (-1250, -1250))
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[1].position = 0.70
    ramp.color_ramp.elements[0].color = (*opts['earth_dark'], 1.0)
    ramp.color_ramp.elements[1].color = (*opts['earth_light'], 1.0)
    link(nt, nz, 'Fac', ramp, 'Fac')
    # pebble specks: pale warm grey, only inside the bare earth
    spk = new_mix_color(nt, 'earth specks', (-1000, -1250))
    spk.inputs[MIX_B_C].default_value = (*opts['speck'], 1.0)
    link(nt, sep, 'Blue', spk, MIX_FAC)
    link(nt, ramp, 'Color', spk, MIX_A_C)

    # ---- colour: grass colour -> earth by the mask
    ca = new_mix_color(nt, 'path colour', (-300, -700))
    unlink_input(mat, 'Principled BSDF', 'Base Color')
    link(nt, gm, 'Colour', ca, MIX_A_C)
    link(nt, mixout(spk), ca, MIX_B_C)
    link(nt, BARE, ca, MIX_FAC)
    link(nt, mixout(ca), bsdf, 'Base Color')
    # ---- roughness: earth is matte
    cr = new_mix_float(nt, 'path roughness', (-300, -900))
    unlink_input(mat, 'Principled BSDF', 'Roughness')
    link(nt, gm, 'Roughness', cr, MIX_A_F)
    cr.inputs[MIX_B_F].default_value = 0.94
    link(nt, BARE, cr, MIX_FAC)
    link(nt, mixout(cr), bsdf, 'Roughness')

    # ---- normal: soft clods (real normal map) -> footfall dish -> the scan's bump (reduced) -> the weathering kit chain (unchanged)
    nm, mp = normal_chain(nt, 'ground', img_nrm, 'UVMap', opts['normal_strength'], (1.0, 1.0, 1.0), loc=(-1700, -300))
    # one Bump (the scan's own relief, kept near its old strength but fed by the real normal map) whose height is the scan height, flattened on
    # the paths, minus a footfall dish. Dish depth 4 mm; Bump distance 0.03 m.
    grp = nt.nodes['Group']
    bump = nt.nodes['Bump']
    flat = N(nt, 'ShaderNodeMath', 'path flatten', (-1250, -700))          # 1 - 0.75 * bare
    flat.operation = 'MULTIPLY_ADD'
    flat.inputs[1].default_value = -0.75
    flat.inputs[2].default_value = 1.0
    link(nt, BARE, flat, 0)
    sc = N(nt, 'ShaderNodeMath', 'scan height flat', (-1000, -700))
    sc.operation = 'MULTIPLY'
    link(nt, grp, 'Height', sc, 0)
    link(nt, flat, 0, sc, 1)
    dish = N(nt, 'ShaderNodeMath', 'dish term', (-1000, -850))           # - 0.14 * footfall (scaled by the bump distance)
    dish.operation = 'MULTIPLY'
    dish.inputs[1].default_value = -opts['dish_depth']
    link(nt, sep, 'Green', dish, 0)
    tot = N(nt, 'ShaderNodeMath', 'height total', (-760, -760))
    tot.operation = 'ADD'
    link(nt, sc, 0, tot, 0)
    link(nt, dish, 0, tot, 1)
    unlink_input(mat, 'Bump', 'Height')
    link(nt, tot, 0, bump, 'Height')
    link(nt, nm, 'Normal', bump, 'Normal')
    set_default(mat, 'Bump', 'Strength', opts['scan_bump'])
    return mat


def default_options():
    return dict(
        earth_dark=hex_lin('#664d3b', 0.55),        # albedo (linear); tuned on the hero picture so the path reads reddish brown and darker than the gravel
        earth_light=hex_lin('#84684d', 0.62),
        speck=hex_lin('#7e7062', 0.7),
        normal_strength=1.0,
        dish_depth=0.16,
        scan_bump=0.50,
    )
