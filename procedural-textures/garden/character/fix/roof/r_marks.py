"""Generic mark builder for the stone-like materials (ridge caps, eave discs, lantern, rocks, basin, caps).
Plain words: takes a COPY of one of the garden's scan materials and adds, after the weathering kit's colour, a few big designed marks:
soft warm-grey blotches, a darker wet band at the waterline, soft olive moss blobs on top faces, pale lichen dots, and a tangent-space
normal map (the old scan bump stays, weaker, and is fed by the normal map)."""
import bpy
from r_common import *

DEBUG_WET = False
MOSS_LIT = '#4f5f2b'
MOSS_DARK = '#232c1b'
MOSS_HIGH = '#6a7835'
LICHEN = '#b8a47c'


def _bsdf(nt):
    return [n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0]


def build_marks(mat, nrm_img=None, nrm_scale=1.0, nrm_strength=0.8, uv='UVMap', bump_strength=0.25, moss=None, lichen=None,
                blotch=0.0, wet=False, tone=0.0, rough_mul=1.0, drip=None, blocks=0.0):
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    bsdf = _bsdf(nt)
    bump = N.get('Bump')
    col_in = bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].links else None
    rough_in = bsdf.inputs['Roughness'].links[0].from_socket if bsdf.inputs['Roughness'].links else None
    geo = nnew(nt, 'ShaderNodeNewGeometry', 'G6 geo')
    sep = nnew(nt, 'ShaderNodeSeparateXYZ', 'G6 pos')
    L.new(geo.outputs['Position'], sep.inputs['Vector'])
    z = sep.outputs['Z']
    oi = [n for n in N if n.bl_idname == 'ShaderNodeObjectInfo']
    oi = oi[0] if oi else nnew(nt, 'ShaderNodeObjectInfo', 'G6 objinfo')
    rnd = oi.outputs['Random']
    offs = nnew(nt, 'ShaderNodeCombineXYZ', 'G6 offs')
    L.new(math_node(nt, 'MULTIPLY', rnd, 23.7).outputs[0], offs.inputs['X'])
    L.new(math_node(nt, 'MULTIPLY', rnd, 11.3).outputs[0], offs.inputs['Y'])
    pos = vmath(nt, 'ADD', geo.outputs['Position'])
    L.new(offs.outputs['Vector'], pos.inputs[1])
    col = col_in
    if col is not None:
        if tone:
            col = vmath(nt, 'SCALE', col)
            L.new(math_node(nt, 'ADD', math_node(nt, 'MULTIPLY', math_node(nt, 'SUBTRACT', rnd, 0.5).outputs[0], tone).outputs[0], 1.0).outputs[0], col.inputs['Scale'])
            col = col.outputs[0]
        if blotch:
            nb = nnew(nt, 'ShaderNodeTexNoise', 'G6 blotch noise', noise_dimensions='3D')
            nb.inputs['Scale'].default_value = 3.2
            nb.inputs['Detail'].default_value = 1.0
            nb.inputs['Roughness'].default_value = 0.5
            L.new(pos.outputs[0], nb.inputs['Vector'])
            tint = mix_rgb(nt, nb.outputs['Fac'], (1 - 0.35 * blotch, 1 - 0.2 * blotch, 1 - 0.1 * blotch, 1), (1 + 0.1 * blotch, 1 + 0.08 * blotch, 1 - 0.12 * blotch, 1))
            col = vmath(nt, 'MULTIPLY', col, mix_out(tint)).outputs[0]
        if blocks:
            # FIX ROUND: soft VALUE BLOCKS - a few big planes of slightly lighter and darker stone (cells of about 50 cm, blended softly),
            # painted, not scanned: the stone reads as 4 to 6 planes instead of a surface covered in lines
            vb = nnew(nt, 'ShaderNodeTexVoronoi', 'G6 value blocks', voronoi_dimensions='3D', feature='SMOOTH_F1')
            vb.inputs['Scale'].default_value = 2.0
            vb.inputs['Smoothness'].default_value = 0.55
            vb.inputs['Randomness'].default_value = 1.0
            L.new(pos.outputs[0], vb.inputs['Vector'])
            sc_ = nnew(nt, 'ShaderNodeSeparateColor', 'G6 value blocks sep')
            L.new(vb.outputs['Color'], sc_.inputs['Color'])
            fb = smoothstep_node(nt, sc_.outputs['Red'], 0.25, 0.75)
            btint = mix_rgb(nt, fb.outputs[0], (1 - 0.15 * blocks, 1 - 0.13 * blocks, 1 - 0.10 * blocks, 1), (1 + 0.10 * blocks, 1 + 0.09 * blocks, 1 + 0.06 * blocks, 1))
            col = vmath(nt, 'MULTIPLY', col, mix_out(btint)).outputs[0]
        if wet:
            wm = smoothstep_node(nt, z, -0.075, -0.1)
            if DEBUG_WET:
                cw = nnew(nt, 'ShaderNodeCombineXYZ', 'G6 wet debug')
                for ax in ('X', 'Y', 'Z'):
                    L.new(wm.outputs[0], cw.inputs[ax])
                L.new(cw.outputs['Vector'], bsdf.inputs['Emission Color'])
                bsdf.inputs['Emission Strength'].default_value = 2.0
            col = mix_out(mix_rgb(nt, math_node(nt, 'MULTIPLY', wm.outputs[0], 0.5).outputs[0], col, hex_lin('#3a3b34')))
            if rough_in is not None:
                rm = nnew(nt, 'ShaderNodeMix', 'G6 wet rough', data_type='FLOAT')
                L.new(wm.outputs[0], sid(rm.inputs, 'Factor_Float'))
                L.new(rough_in, sid(rm.inputs, 'A_Float'))
                rn = math_node(nt, 'MULTIPLY', rough_in, 0.78)
                L.new(rn.outputs[0], sid(rm.inputs, 'B_Float'))
                rough_in = rm.outputs['Result']
        nsep = None
        if moss or lichen:
            nrm = nnew(nt, 'ShaderNodeNewGeometry', 'G6 geo n')
            nsep = nnew(nt, 'ShaderNodeSeparateXYZ', 'G6 n sep')
            L.new(nrm.outputs['Normal'], nsep.inputs['Vector'])
        if lichen:
            vor = nnew(nt, 'ShaderNodeTexVoronoi', 'G6 lichen dots', voronoi_dimensions='3D', feature='F1')
            vor.inputs['Scale'].default_value = lichen.get('dots', 30.0)
            L.new(pos.outputs[0], vor.inputs['Vector'])
            nz = nnew(nt, 'ShaderNodeTexNoise', 'G6 lichen zone', noise_dimensions='3D')
            nz.inputs['Scale'].default_value = lichen.get('zone', 2.2)
            L.new(pos.outputs[0], nz.inputs['Vector'])
            dots = math_node(nt, 'SUBTRACT', 1.0, smoothstep_node(nt, vor.outputs['Distance'], 0.28, 0.48).outputs[0])
            zone = smoothstep_node(nt, nz.outputs['Fac'], lichen.get('lo', 0.55), lichen.get('lo', 0.55) + 0.1)
            lm = math_node(nt, 'MULTIPLY', dots.outputs[0], zone.outputs[0])
            col = mix_out(mix_rgb(nt, math_node(nt, 'MULTIPLY', lm.outputs[0], 0.85).outputs[0], col, hex_lin(LICHEN)))
        if moss:
            nm_ = nnew(nt, 'ShaderNodeTexNoise', 'G6 moss blobs', noise_dimensions='3D')
            nm_.inputs['Scale'].default_value = moss.get('scale', 7.0)
            nm_.inputs['Detail'].default_value = 1.0
            nm_.inputs['Roughness'].default_value = 0.5
            L.new(pos.outputs[0], nm_.inputs['Vector'])
            lo = moss.get('lo', 0.58)
            top = smoothstep_node(nt, nsep.outputs['Z'], moss.get('top', 0.45), moss.get('top', 0.45) + 0.3)
            outer = smoothstep_node(nt, nm_.outputs['Fac'], lo, lo + 0.035)
            inner = smoothstep_node(nt, nm_.outputs['Fac'], lo + 0.025, lo + 0.1)
            high = smoothstep_node(nt, nm_.outputs['Fac'], lo + 0.08, lo + 0.17)
            mask = math_node(nt, 'MULTIPLY', outer.outputs[0], top.outputs[0])
            mc = mix_rgb(nt, inner.outputs[0], hex_lin(MOSS_DARK), hex_lin(MOSS_LIT))
            mc = mix_rgb(nt, math_node(nt, 'MULTIPLY', high.outputs[0], 0.7).outputs[0], mix_out(mc), hex_lin(MOSS_HIGH))
            col = mix_out(mix_rgb(nt, math_node(nt, 'MULTIPLY', mask.outputs[0], 0.95).outputs[0], col, mix_out(mc)))
            if rough_in is not None:
                rm = nnew(nt, 'ShaderNodeMix', 'G6 moss rough', data_type='FLOAT')
                L.new(mask.outputs[0], sid(rm.inputs, 'Factor_Float'))
                L.new(rough_in, sid(rm.inputs, 'A_Float'))
                sid(rm.inputs, 'B_Float').default_value = 0.95
                rough_in = rm.outputs['Result']
        L.new(col, bsdf.inputs['Base Color'])
    if rough_in is not None and rough_mul != 1.0:
        rr = math_node(nt, 'MULTIPLY', rough_in, rough_mul)
        rough_in = rr.outputs[0]
    if rough_in is not None:
        L.new(rough_in, bsdf.inputs['Roughness'])
    if nrm_img is not None:
        uvn = nnew(nt, 'ShaderNodeUVMap', 'G6 UV', uv_map=uv)
        mp = nnew(nt, 'ShaderNodeMapping', 'G6 NM mapping')
        mp.inputs['Scale'].default_value = (nrm_scale, nrm_scale, nrm_scale)
        L.new(uvn.outputs['UV'], mp.inputs['Vector'])
        tx = nnew(nt, 'ShaderNodeTexImage', 'G6 NM image')
        tx.image = nrm_img
        tx.interpolation = 'Cubic'
        tx.extension = 'REPEAT'
        L.new(mp.outputs['Vector'], tx.inputs['Vector'])
        nmn = nnew(nt, 'ShaderNodeNormalMap', 'G6 NM', space='TANGENT', uv_map=uv)
        nmn.inputs['Strength'].default_value = nrm_strength
        L.new(tx.outputs['Color'], nmn.inputs['Color'])
        if bump is not None:
            L.new(nmn.outputs['Normal'], bump.inputs['Normal'])
            bump.inputs['Strength'].default_value = bump_strength
        else:
            L.new(nmn.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def add_attr_tint(mat, attr_name, hex_colour, strength=0.8):
    """FIX ROUND: darken (tint) the base colour by a vertex attribute (0..1) - used for the drip stains on the eave discs"""
    nt = mat.node_tree
    bsdf = _bsdf(nt)
    if not bsdf.inputs['Base Color'].links:
        return
    src = bsdf.inputs['Base Color'].links[0].from_socket
    at = nnew(nt, 'ShaderNodeAttribute', 'G6 attr ' + attr_name, attribute_type='GEOMETRY', attribute_name=attr_name)
    c = mix_rgb(nt, math_node(nt, 'MULTIPLY', at.outputs['Fac'], strength).outputs[0], src, hex_lin(hex_colour))
    nt.links.new(mix_out(c), bsdf.inputs['Base Color'])
