"""wood_mats.py - the wood builder's materials (bpy). All named 'G6 wood / ...'. Colours come from the garden palette (style note section 3).
Every colour below is given as sRGB hex and converted to linear for the node values."""
import os
import bpy
import numpy as np

# NOTE: the palette of the style note (#9b8476 silvered, #8e6958 warm, #5c4a3e end grain, moss #6a6a2e lit) names colours of the RENDERED
# picture. The values below are the ALBEDO colours that give those rendered colours under the garden's dusk light (calibrated 22 October on
# the hero crop: sunlit plank today = rgb 146,121,107 in the picture).
PAL = dict(silver='#9c9690', warm='#957f6e', end='#5a5249', moss_lit='#4e5a2e', moss_dark='#2a301f', moss_rim='#626b36',
           mould='#2f3430', iron='#4a3226', iron_edge='#6c4c3a', peg='#b8a48e', post='#8d8a80', post_wet='#34352f', algae='#4a5428',
           stone='#8b8579', stone_wet='#4a4a42')


def lin(hexs):
    h = hexs.lstrip('#')
    c = np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return (float(c[0]), float(c[1]), float(c[2]), 1.0)


class NB:
    """tiny node builder"""
    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.x = 0

    def n(self, bl, label=None, loc=(0, 0), **props):
        node = self.nt.nodes.new(bl)
        for k, v in props.items():
            setattr(node, k, v)
        node.location = loc
        if label:
            node.label = label
            node.name = label
        return node

    def link(self, a, ao, b, bi):
        sa = a.outputs[ao] if not isinstance(ao, bpy.types.NodeSocket) else ao
        sb = b.inputs[bi] if not isinstance(bi, bpy.types.NodeSocket) else bi
        self.nt.links.new(sa, sb)

    def math(self, op, a=None, b=None, c=None, loc=(0, 0), clamp=False):
        m = self.n('ShaderNodeMath', loc=loc, operation=op)
        m.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, bpy.types.NodeSocket):
                self.nt.links.new(v, m.inputs[i])
            else:
                m.inputs[i].default_value = v
        return m

    def mix(self, fac, a, b, loc=(0, 0), blend='MIX'):
        m = self.n('ShaderNodeMix', loc=loc, data_type='RGBA', blend_type=blend)
        for sock, v in ((m.inputs['Factor'], fac), (m.inputs['A'], a), (m.inputs['B'], b)):
            if isinstance(v, bpy.types.NodeSocket):
                self.nt.links.new(v, sock)
            elif v is not None:
                sock.default_value = v
        return m

    def maprange(self, v, a0, a1, b0=0.0, b1=1.0, loc=(0, 0), clamp=True):
        m = self.n('ShaderNodeMapRange', loc=loc)
        m.clamp = clamp
        self.nt.links.new(v, m.inputs['Value']) if isinstance(v, bpy.types.NodeSocket) else None
        m.inputs['From Min'].default_value = a0
        m.inputs['From Max'].default_value = a1
        m.inputs['To Min'].default_value = b0
        m.inputs['To Max'].default_value = b1
        return m


def attr(nb, name, loc):
    return nb.n('ShaderNodeAttribute', label='A ' + name, loc=loc, attribute_type='GEOMETRY', attribute_name=name)


def load_image(path, colour='Non-Color'):
    name = os.path.basename(path)
    img = bpy.data.images.get(name)
    if img is not None and img.source == 'FILE' and os.path.abspath(bpy.path.abspath(img.filepath)) == os.path.abspath(path):
        return img
    if img is not None:
        bpy.data.images.remove(img)
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = colour        # loaded from a file: the colour space may be set right away (pixels are read lazily)
    img.alpha_mode = 'NONE' if colour == 'Non-Color' else img.alpha_mode
    return img


def image_node(nb, img, loc, mapping_out):
    t = nb.n('ShaderNodeTexImage', loc=loc, interpolation='Cubic', extension='REPEAT')
    t.image = img
    nb.link(mapping_out[0], mapping_out[1], t, 'Vector')
    return t


PARAMS = dict(moss_lo=0.88, moss_hi=0.92, mould_lo=0.78, mould_hi=0.86)


def _wood_colour(nb, kind, maps_dir, uvmap='UVMap', loc0=(0, 0), params=None, tile=(1.0, 0.25), pal=None):
    """returns dict with 'color', 'rough', 'normal', 'bump_height' sockets for the timber material of a plank face."""
    P = dict(PARAMS)
    if params:
        P.update(params)
    pal = dict(PAL, **(pal or {}))
    x0, y0 = loc0
    A_wear = attr(nb, 'wear', (x0, y0 + 900))
    A_damp = attr(nb, 'damp', (x0, y0 + 780))
    A_id = attr(nb, 'plank_id', (x0, y0 + 660))
    A_tone = attr(nb, 'plank_tone', (x0, y0 + 540))
    geo = nb.n('ShaderNodeNewGeometry', loc=(x0, y0 + 400))
    uv = nb.n('ShaderNodeUVMap', loc=(x0, y0 + 250), uv_map=uvmap)
    mp = nb.n('ShaderNodeMapping', label='NM Mapping', loc=(x0 + 200, y0 + 250))
    mp.inputs['Scale'].default_value = (1.0 / tile[0], 1.0 / tile[1], 1.0)
    nb.link(uv, 'UV', mp, 'Vector')
    img_n = image_node(nb, load_image(os.path.join(maps_dir, 'plank_top_normal.png' if kind != 'end' else 'end_grain_normal.png')), (x0 + 400, y0 + 300), (mp, 'Vector'))
    img_n.label = img_n.name = 'NM Image'
    nm = nb.n('ShaderNodeNormalMap', label='NM Normal Map', loc=(x0 + 700, y0 + 300), space='TANGENT', uv_map=uvmap)
    nm.inputs['Strength'].default_value = {'top': 1.5, 'side': 1.0, 'end': 0.9}[kind]
    nb.link(img_n, 'Color', nm, 'Color')
    if kind == 'end':
        mp.inputs['Scale'].default_value = (4.0, 4.0, 1.0)
    # cavity (grooves darker)
    cav_f = None
    if kind in ('top', 'side'):
        img_c = image_node(nb, load_image(os.path.join(maps_dir, 'plank_top_cavity.png')), (x0 + 400, y0 + 60), (mp, 'Vector'))
        cav_f = nb.maprange(img_c.outputs['Color'], 0.0, 1.0, 0.68 if kind == 'top' else 0.84, 1.0, loc=(x0 + 700, y0 + 60))
        cav_f.inputs['Value'].default_value = 1.0
        nb.nt.links.new(img_c.outputs['Color'], cav_f.inputs['Value'])
    # --- base colour
    base_sil = nb.n('ShaderNodeRGB', label='silver', loc=(x0 + 400, y0 + 700)); base_sil.outputs[0].default_value = lin(pal['silver'])
    base_wrm = nb.n('ShaderNodeRGB', label='warm', loc=(x0 + 400, y0 + 600)); base_wrm.outputs[0].default_value = lin(pal['warm'])
    c = nb.mix(A_tone.outputs['Fac'], base_sil.outputs[0], base_wrm.outputs[0], loc=(x0 + 650, y0 + 650))
    if kind == 'end':
        endc = nb.n('ShaderNodeRGB', label='end grain', loc=(x0 + 400, y0 + 500)); endc.outputs[0].default_value = lin(PAL['end'])
        warm_end = nb.mix(A_tone.outputs['Fac'], lin(PAL['end']), lin('#6e4f3f'), loc=(x0 + 650, y0 + 520))
        c = warm_end
    # per-plank value variation +-6 percent
    var = nb.math('MULTIPLY_ADD', A_id.outputs['Fac'], 0.22, 0.89, loc=(x0 + 650, y0 + 760))
    c2 = nb.mix(1.0, c.outputs['Result'], c.outputs['Result'], loc=(x0 + 880, y0 + 650), blend='MULTIPLY')
    nb.nt.links.new(var.outputs[0], c2.inputs['B']) if False else None
    vcol = nb.n('ShaderNodeCombineColor', loc=(x0 + 880, y0 + 760))
    for ch in ('Red', 'Green', 'Blue'):
        nb.nt.links.new(var.outputs[0], vcol.inputs[ch])
    c2 = nb.mix(1.0, c.outputs['Result'], vcol.outputs['Color'], loc=(x0 + 1080, y0 + 650), blend='MULTIPLY')
    # walking line lighter
    wl = nb.math('MULTIPLY_ADD', A_wear.outputs['Fac'], 0.36 if kind == 'top' else 0.0, 1.0, loc=(x0 + 880, y0 + 880))
    wcol = nb.n('ShaderNodeCombineColor', loc=(x0 + 1080, y0 + 880))
    for ch in ('Red', 'Green', 'Blue'):
        nb.nt.links.new(wl.outputs[0], wcol.inputs[ch])
    c3 = nb.mix(1.0, c2.outputs['Result'], wcol.outputs['Color'], loc=(x0 + 1280, y0 + 700), blend='MULTIPLY')
    col = c3
    if cav_f is not None:
        ccol = nb.n('ShaderNodeCombineColor', loc=(x0 + 1280, y0 + 540))
        for ch in ('Red', 'Green', 'Blue'):
            nb.nt.links.new(cav_f.outputs['Result'], ccol.inputs[ch])
        col = nb.mix(1.0, c3.outputs['Result'], ccol.outputs['Color'], loc=(x0 + 1480, y0 + 700), blend='MULTIPLY')
    # --- moss and mould masks (soft rounded blobs from low noise + the damp attribute)
    nmoss = nb.n('ShaderNodeTexNoise', label='moss noise', loc=(x0 + 400, y0 - 250), noise_dimensions='3D')
    nmoss.inputs['Scale'].default_value = 7.5 if kind != 'side' else 18.0
    nmoss.inputs['Detail'].default_value = 2.0
    nmoss.inputs['Roughness'].default_value = 0.5
    nb.link(geo, 'Position', nmoss, 'Vector')
    dm = nb.math('SUBTRACT', A_damp.outputs['Fac'], 0.45, loc=(x0 + 650, y0 - 160))
    fld = nb.math('ADD', nmoss.outputs['Fac'], nb.math('MULTIPLY', dm.outputs[0], 0.9 if kind != 'side' else 1.0).outputs[0], loc=(x0 + 900, y0 - 250))
    mm = nb.n('ShaderNodeMapRange', label='moss mask', loc=(x0 + 1150, y0 - 250))
    nb.link(fld, 'Value', mm, 'Value')
    mm.inputs['From Min'].default_value = P['moss_lo'] if kind != 'side' else P['moss_lo'] - 0.03
    mm.inputs['From Max'].default_value = P['moss_hi'] if kind != 'side' else P['moss_hi'] - 0.03
    nmould = nb.n('ShaderNodeTexNoise', label='mould noise', loc=(x0 + 400, y0 - 450), noise_dimensions='3D')
    nmould.inputs['Scale'].default_value = 4.0
    nmould.inputs['Detail'].default_value = 3.0
    nmould.inputs['Roughness'].default_value = 0.6
    nb.link(geo, 'Position', nmould, 'Vector')
    fld2 = nb.math('ADD', nmould.outputs['Fac'], nb.math('MULTIPLY', dm.outputs[0], 0.7).outputs[0], loc=(x0 + 900, y0 - 450))
    mo = nb.n('ShaderNodeMapRange', label='mould mask', loc=(x0 + 1150, y0 - 450))
    nb.link(fld2, 'Value', mo, 'Value')
    mo.inputs['From Min'].default_value = P['mould_lo']
    mo.inputs['From Max'].default_value = P['mould_hi']
    mo.inputs['To Max'].default_value = 0.75
    # moss colour: interior olive, lighter rim; variation from a second noise
    nmv = nb.n('ShaderNodeTexNoise', label='moss tone noise', loc=(x0 + 1150, y0 - 650), noise_dimensions='3D')
    nmv.inputs['Scale'].default_value = 22.0
    nmv.inputs['Detail'].default_value = 1.0
    nb.link(geo, 'Position', nmv, 'Vector')
    rim = nb.math('MULTIPLY', nb.math('MULTIPLY', mm.outputs['Result'], nb.math('SUBTRACT', 1.0, mm.outputs['Result']).outputs[0]).outputs[0], 3.6, clamp=True, loc=(x0 + 1400, y0 - 300))
    mcol1 = nb.mix(nmv.outputs['Fac'], lin(PAL['moss_dark']), lin(PAL['moss_lit']), loc=(x0 + 1400, y0 - 520))
    mcol = nb.mix(rim.outputs[0], mcol1.outputs['Result'], lin(PAL['moss_rim']), loc=(x0 + 1650, y0 - 450))
    with_mould = nb.mix(mo.outputs['Result'], col.outputs['Result'], lin(PAL['mould']), loc=(x0 + 1800, y0 + 400))
    final = nb.mix(mm.outputs['Result'], with_mould.outputs['Result'], mcol.outputs['Result'], loc=(x0 + 2050, y0 + 300))
    # roughness 0.76 .. 0.9 (matt, painted)
    rough = nb.math('MULTIPLY_ADD', mm.outputs['Result'], 0.14, 0.78, loc=(x0 + 1700, y0 - 150))
    # bump height from the moss (soft pillows) 
    bh = nb.math('MULTIPLY', mm.outputs['Result'], nb.math('MULTIPLY_ADD', nmv.outputs['Fac'], 0.5, 0.6).outputs[0], loc=(x0 + 1700, y0 - 700))
    return dict(color=final.outputs['Result'], rough=rough.outputs[0], normal=nm.outputs['Normal'], bump_h=bh.outputs[0],
                moss=mm.outputs['Result'], mould=mo.outputs['Result'], wear=A_wear.outputs['Fac'], nodes=dict(mm=mm, mo=mo))


def _finish_principled(nb, parts, loc=(2500, 300), bump_strength=0.25, spec=0.3):
    bsdf = nb.n('ShaderNodeBsdfPrincipled', loc=loc)
    bsdf.inputs['Specular IOR Level'].default_value = spec
    nb.link(parts['color'] if hasattr(parts['color'], 'node') else parts['color'].node, parts['color'], bsdf, 'Base Color') if False else nb.nt.links.new(parts['color'], bsdf.inputs['Base Color'])
    nb.nt.links.new(parts['rough'], bsdf.inputs['Roughness'])
    bump = nb.n('ShaderNodeBump', label='moss bump', loc=(loc[0] - 300, loc[1] - 450))
    bump.inputs['Strength'].default_value = bump_strength
    bump.inputs['Distance'].default_value = 0.004
    nb.nt.links.new(parts['bump_h'], bump.inputs['Height'])
    nb.nt.links.new(parts['normal'], bump.inputs['Normal'])
    nb.nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    out = nb.n('ShaderNodeOutputMaterial', loc=(loc[0] + 350, loc[1]))
    # debug view: moss (red) / mould (green) / wear (blue) as emission when 'G6 debug' value = 1
    dbg = nb.n('ShaderNodeValue', label='G6 debug', loc=(loc[0] - 300, loc[1] + 500))
    dbg.outputs[0].default_value = 0.0
    em = nb.n('ShaderNodeEmission', loc=(loc[0], loc[1] + 300))
    cc = nb.n('ShaderNodeCombineColor', loc=(loc[0] - 300, loc[1] + 300))
    nb.nt.links.new(parts['moss'], cc.inputs['Red'])
    nb.nt.links.new(parts['mould'], cc.inputs['Green'])
    nb.nt.links.new(parts['wear'], cc.inputs['Blue'])
    nb.nt.links.new(cc.outputs['Color'], em.inputs['Color'])
    mx = nb.n('ShaderNodeMixShader', loc=(loc[0] + 250, loc[1] + 150))
    nb.nt.links.new(dbg.outputs[0], mx.inputs['Fac'])
    nb.nt.links.new(bsdf.outputs['BSDF'], mx.inputs[1])
    nb.nt.links.new(em.outputs['Emission'], mx.inputs[2])
    nb.nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])
    return bsdf


DECK_PAL = dict(silver='#82796f', warm='#735745', end='#4d443b')


def make_plank_materials(maps_dir, params=None, prefix='plank', pal=None, label=None):
    mats = {}
    nm = {'top': 'G6 wood / %s top' % prefix, 'side': 'G6 wood / %s side' % prefix, 'end': 'G6 wood / %s end grain' % prefix}
    for kind, name in nm.items():
        m = bpy.data.materials.new(name)
        nb = NB(m)
        parts = _wood_colour(nb, kind, maps_dir, params=params, tile=(1.0, 0.25) if kind != 'end' else (0.25, 0.25), pal=pal)
        if kind == 'end':
            # end grain is darker and only a little moss: lower both masks
            pass
        _finish_principled(nb, parts, bump_strength=0.25)
        m['garden_owner'] = 'wood'
        mats[kind] = m
    return mats


def make_flat_material(name, colour, rough=0.72, edge=None, spec=0.25, noise=0.0, extra_rough_var=0.0):
    m = bpy.data.materials.new(name)
    nb = NB(m)
    bsdf = nb.n('ShaderNodeBsdfPrincipled', loc=(600, 0))
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Specular IOR Level'].default_value = spec
    col_src = None
    rgb = nb.n('ShaderNodeRGB', loc=(0, 0))
    rgb.outputs[0].default_value = lin(colour)
    col_src = rgb.outputs[0]
    if edge:
        lw = nb.n('ShaderNodeLayerWeight', loc=(0, -200))
        lw.inputs['Blend'].default_value = 0.5
        mx = nb.mix(lw.outputs['Facing'], lin(edge), lin(colour), loc=(300, 0))
        # Facing = 1 at grazing: edge colour there
        nb.nt.links.new(lw.outputs['Facing'], mx.inputs['Factor'])
        col_src = mx.outputs['Result']
        nb.nt.links.new(rgb.outputs[0], mx.inputs['B'])
        mx.inputs['A'].default_value = lin(colour)
        mx.inputs['B'].default_value = lin(edge)
        nb.nt.links.new(rgb.outputs[0], mx.inputs['A'])
    nb.nt.links.new(col_src, bsdf.inputs['Base Color'])
    out = nb.n('ShaderNodeOutputMaterial', loc=(900, 0))
    nb.nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    m['garden_owner'] = 'wood'
    return m


def make_post_material(maps_dir, name='G6 wood / post timber', params=None):
    m = bpy.data.materials.new(name)
    nb = NB(m)
    geo = nb.n('ShaderNodeNewGeometry', loc=(0, 300))
    A_damp = attr(nb, 'damp', (0, 700))
    A_id = attr(nb, 'plank_id', (0, 580))
    uv = nb.n('ShaderNodeUVMap', loc=(0, 100), uv_map='UVMap')
    mp = nb.n('ShaderNodeMapping', label='NM Mapping', loc=(200, 100))
    mp.inputs['Scale'].default_value = (1.0 / 0.28, 1.0 / 0.56, 1.0)
    nb.link(uv, 'UV', mp, 'Vector')
    img = image_node(nb, load_image(os.path.join(maps_dir, 'post_timber_normal.png')), (400, 100), (mp, 'Vector'))
    img.label = img.name = 'NM Image'
    nm = nb.n('ShaderNodeNormalMap', label='NM Normal Map', loc=(700, 100), space='TANGENT', uv_map='UVMap')
    nm.inputs['Strength'].default_value = 0.9
    nb.link(img, 'Color', nm, 'Color')
    sep = nb.n('ShaderNodeSeparateXYZ', loc=(200, 300))
    nb.link(geo, 'Position', sep, 'Vector')
    # dry timber colour, darker and damper towards the water
    dry = nb.mix(nb.math('MULTIPLY_ADD', A_id.outputs['Fac'], 0.12, 0.94).outputs[0], lin(PAL['post']), lin(PAL['post']), loc=(500, 500), blend='MIX')
    dcol = nb.n('ShaderNodeCombineColor', loc=(500, 640))
    v = nb.math('MULTIPLY_ADD', A_id.outputs['Fac'], 0.14, 0.93)
    for ch in ('Red', 'Green', 'Blue'):
        nb.nt.links.new(v.outputs[0], dcol.inputs[ch])
    dry = nb.mix(1.0, lin(PAL['post']), dcol.outputs['Color'], loc=(700, 500), blend='MULTIPLY')
    wet = nb.maprange(sep.outputs['Z'], 0.20, -0.10, 0.0, 1.0, loc=(500, 300))      # 0 high up .. 1 at the waterline
    wet_d = nb.mix(wet.outputs['Result'], dry.outputs['Result'], lin(PAL['post_wet']), loc=(900, 450))
    band = nb.maprange(sep.outputs['Z'], -0.24, -0.18, 0.0, 1.0, loc=(500, 100))      # algae band just under the waterline
    band2 = nb.maprange(sep.outputs['Z'], -0.11, -0.05, 1.0, 0.0, loc=(500, -80))
    bm = nb.math('MULTIPLY', band.outputs['Result'], band2.outputs['Result'], loc=(700, 0))
    nz = nb.n('ShaderNodeTexNoise', loc=(500, -300), noise_dimensions='3D'); nz.inputs['Scale'].default_value = 9.0; nz.inputs['Detail'].default_value = 1.0
    nb.link(geo, 'Position', nz, 'Vector')
    bmn = nb.maprange(nb.math('ADD', bm.outputs[0], nb.math('MULTIPLY', nb.math('SUBTRACT', nz.outputs['Fac'], 0.5).outputs[0], 0.6).outputs[0]).outputs[0], 0.25, 0.4, 0.0, 1.0, loc=(900, -100))
    alg = nb.mix(bmn.outputs['Result'], wet_d.outputs['Result'], lin(PAL['algae']), loc=(1150, 300))
    # a little mould at the top of each post foot region and from the damp attribute
    mold = nb.maprange(nb.math('ADD', nz.outputs['Fac'], nb.math('MULTIPLY', A_damp.outputs['Fac'], 0.0).outputs[0]).outputs[0], 0.62, 0.7, 0.0, 0.6, loc=(900, -300))
    fin = nb.mix(mold.outputs['Result'], alg.outputs['Result'], lin(PAL['mould']), loc=(1400, 300))
    bsdf = nb.n('ShaderNodeBsdfPrincipled', loc=(1700, 300))
    bsdf.inputs['Specular IOR Level'].default_value = 0.25
    rough = nb.math('MULTIPLY_ADD', wet.outputs['Result'], 0.0, 0.8)
    bsdf.inputs['Roughness'].default_value = 0.8
    nb.nt.links.new(fin.outputs['Result'], bsdf.inputs['Base Color'])
    nb.nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    out = nb.n('ShaderNodeOutputMaterial', loc=(2000, 300))
    nb.nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    m['garden_owner'] = 'wood'
    return m


def make_stone_material(maps_dir, name='G6 wood / footing stone'):
    m = bpy.data.materials.new(name)
    nb = NB(m)
    geo = nb.n('ShaderNodeNewGeometry', loc=(0, 300))
    uv = nb.n('ShaderNodeUVMap', loc=(0, 100), uv_map='UVMap')
    mp = nb.n('ShaderNodeMapping', label='NM Mapping', loc=(200, 100))
    nb.link(uv, 'UV', mp, 'Vector')
    img = image_node(nb, load_image(os.path.join(maps_dir, 'footing_stone_normal.png')), (400, 100), (mp, 'Vector'))
    img.label = img.name = 'NM Image'
    nm = nb.n('ShaderNodeNormalMap', label='NM Normal Map', loc=(700, 100), space='TANGENT', uv_map='UVMap')
    nm.inputs['Strength'].default_value = 0.8
    nb.link(img, 'Color', nm, 'Color')
    nz = nb.n('ShaderNodeTexNoise', loc=(300, 400), noise_dimensions='3D'); nz.inputs['Scale'].default_value = 3.0; nz.inputs['Detail'].default_value = 2.0
    nb.link(geo, 'Position', nz, 'Vector')
    base = nb.mix(nz.outputs['Fac'], lin(PAL['stone_wet']), lin(PAL['stone']), loc=(600, 400))
    n2 = nb.n('ShaderNodeTexNoise', loc=(300, 600), noise_dimensions='3D'); n2.inputs['Scale'].default_value = 6.0; n2.inputs['Detail'].default_value = 2.0
    nb.link(geo, 'Position', n2, 'Vector')
    gm = nb.maprange(n2.outputs['Fac'], 0.52, 0.62, 0.0, 0.7, loc=(600, 600))
    col = nb.mix(gm.outputs['Result'], base.outputs['Result'], lin(PAL['algae']), loc=(900, 450))
    bsdf = nb.n('ShaderNodeBsdfPrincipled', loc=(1200, 300))
    bsdf.inputs['Roughness'].default_value = 0.82
    bsdf.inputs['Specular IOR Level'].default_value = 0.25
    nb.nt.links.new(col.outputs['Result'], bsdf.inputs['Base Color'])
    nb.nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    out = nb.n('ShaderNodeOutputMaterial', loc=(1500, 300))
    nb.nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    m['garden_owner'] = 'wood'
    return m


def add_normal_to_chain(mat, image_path, uvmap='UVMap', strength=0.8, scale=(1, 1, 1), nm_tag='NM'):
    """In an existing (owned) material: add UV -> Mapping -> Image(Non-Color) -> Normal Map(Tangent) and feed it into the Bump node(s)' Normal input
    (or the Principled Normal when there is no Bump). The old Bump keeps its height but now sits on top of the normal map. Idempotent."""
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.name.startswith(nm_tag + ' '):
            nt.nodes.remove(n)
    img = load_image(image_path)
    uv = nt.nodes.new('ShaderNodeUVMap'); uv.uv_map = uvmap; uv.name = uv.label = nm_tag + ' UV'
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = scale; mp.name = mp.label = nm_tag + ' Mapping'
    tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img; tx.interpolation = 'Cubic'; tx.extension = 'REPEAT'; tx.name = tx.label = nm_tag + ' Image'
    nm = nt.nodes.new('ShaderNodeNormalMap'); nm.space = 'TANGENT'; nm.uv_map = uvmap; nm.inputs['Strength'].default_value = strength; nm.name = nm.label = nm_tag + ' Normal Map'
    nt.links.new(uv.outputs['UV'], mp.inputs['Vector'])
    nt.links.new(mp.outputs['Vector'], tx.inputs['Vector'])
    nt.links.new(tx.outputs['Color'], nm.inputs['Color'])
    bumps = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeBump']
    if bumps:
        for b in bumps:
            nt.links.new(nm.outputs['Normal'], b.inputs['Normal'])
            b.inputs['Strength'].default_value = min(b.inputs['Strength'].default_value, 0.3)
    else:
        bsdf = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
        nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    for i, n in enumerate((uv, mp, tx, nm)):
        n.location = (-1800 + i * 220, -1400)
    return nm


def darken_near_floor(mat, node_name='Vector Math.002', z_lo=0.55, z_hi=0.95, amount=0.34):
    """Posts darker and damper near the deck: multiply the colour that leaves `node_name` by 1 - amount at z <= z_lo (fading out by z_hi)."""
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.name.startswith('G6 dark '):
            nt.nodes.remove(n)
    src = nt.nodes.get(node_name)
    if src is None:
        return False
    outs = [l for l in nt.links if l.from_node == src]
    geo = nt.nodes.new('ShaderNodeNewGeometry'); geo.name = 'G6 dark geo'
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); sep.name = 'G6 dark sep'
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.name = 'G6 dark range'
    mr.inputs['From Min'].default_value = z_hi; mr.inputs['From Max'].default_value = z_lo
    mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = 1.0 - amount
    mx = nt.nodes.new('ShaderNodeMix'); mx.name = 'G6 dark mix'; mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'
    mx.inputs['Factor'].default_value = 1.0
    cc = nt.nodes.new('ShaderNodeCombineColor'); cc.name = 'G6 dark col'
    nt.links.new(geo.outputs['Position'], sep.inputs['Vector'])
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    # slightly cool/green and darker: R, G, B multipliers
    nt.links.new(mr.outputs['Result'], cc.inputs['Red'])
    m2 = nt.nodes.new('ShaderNodeMath'); m2.name = 'G6 dark g'; m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = 1.0
    nt.links.new(mr.outputs['Result'], m2.inputs[0])
    nt.links.new(m2.outputs[0], cc.inputs['Green'])
    nt.links.new(mr.outputs['Result'], cc.inputs['Blue'])
    nt.links.new(src.outputs[0], mx.inputs['A'])
    nt.links.new(cc.outputs['Color'], mx.inputs['B'])
    for l in outs:
        nt.links.new(mx.outputs['Result'], l.to_socket)
    return True
