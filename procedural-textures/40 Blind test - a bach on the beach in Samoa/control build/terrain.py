import bpy, math, random
import numpy as np
from lib import *

def shore_x(y):
    y = np.asarray(y, dtype=float)
    return -9 + 0.10 * y + 0.9 * np.sin(0.11 * y + 0.5) + 0.35 * np.sin(0.41 * y + 2.0)

def height(x, y):
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    d = x - shore_x(y)
    # land
    dl = np.maximum(d, 0)
    zl = 1.05 * (1 - np.exp(-dl / 7.0))
    zl += 0.16 * (fbm2(x * 0.08, y * 0.08, 3, 5) - 0.5) * smoothstep(1, 8, dl)
    hill = 120 * smoothstep(20, 220, dl) ** 1.25 * (0.55 + 0.9 * fbm2(x * 0.012, y * 0.012, 4, 9))
    zl += hill
    # sea
    a = np.maximum(-d, 0)
    a2 = a + 3.0 * np.sin(0.045 * y + 1.0)
    zs = -1.9 * (1 - np.exp(-a / 8.0))
    zs += 1.6 * smoothstep(52, 72, a2) - 14 * smoothstep(80, 100, a2)
    zs += 0.25 * (fbm2(x * 0.05, y * 0.05, 3, 21) - 0.5) * smoothstep(5, 20, a)
    return np.where(d >= 0, zl, zs)

def ground(x, y):
    return float(height(np.array([x]), np.array([y]))[0])

def axis(lo, hi, fine_lo, fine_hi, step, grow=1.06):
    pts = list(np.arange(fine_lo, fine_hi + 1e-6, step))
    v = fine_hi; s = step
    while v < hi:
        s *= grow; v += s; pts.append(v)
    v = fine_lo; s = step
    while v > lo:
        s *= grow; v -= s; pts.insert(0, v)
    return np.array(pts)

def grid_mesh(name, xs, ys, zfun, mat, attrs=None):
    X, Y = np.meshgrid(xs, ys)
    Z = zfun(X, Y)
    nx, ny = len(xs), len(ys)
    verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    idx = np.arange(nx * ny).reshape(ny, nx)
    faces = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts.tolist(), [], faces.tolist()); me.update()
    for p in me.polygons: p.use_smooth = True
    if attrs:
        for an, arr in attrs.items():
            ca = me.color_attributes.new(an, 'FLOAT_COLOR', 'POINT')
            ca.data.foreach_set('color', np.asarray(arr, dtype=np.float32).ravel())
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    me.materials.append(mat)
    return ob, X, Y, Z

def build_terrain():
    xs = axis(-400, 400, -26, 50, 0.55, 1.07)
    ys = axis(-40, 2500, -20, 46, 0.55, 1.07)
    def zf(X, Y): return height(X, Y)
    X, Y = np.meshgrid(xs, ys)
    d = X - shore_x(Y)
    Z = height(X, Y)
    n = fbm2(X * 0.6, Y * 0.6, 3, 3)
    wet = 1 - smoothstep(-0.4, 3.0 + 1.5 * n, d)
    wet *= smoothstep(-30, -0.5, d)
    foam = smoothstep(-0.2, 0.2, d) * (1 - smoothstep(0.2, 1.1 + 0.7 * np.sin(Y * 0.7), d))
    grass = smoothstep(9 + 5 * n, 13 + 5 * n, d)
    jung = smoothstep(32, 55, d + 18 * n)
    under = smoothstep(0, -2, d)
    rgb = np.zeros(X.shape + (4,), dtype=np.float32)
    tide = np.exp(-((d - (3.3 + 0.5 * np.sin(Y * 0.5))) / 0.28) ** 2) * smoothstep(0.35, 0.6, fbm2(X * 1.5, Y * 1.5, 3, 11))
    rgb[..., 0] = wet; rgb[..., 1] = grass; rgb[..., 2] = jung; rgb[..., 3] = tide
    rgb2 = np.zeros(X.shape + (4,), dtype=np.float32)
    rgb2[..., 0] = foam; rgb2[..., 1] = under; rgb2[..., 2] = np.clip(-Z / 3, 0, 1); rgb2[..., 3] = 1
    mat = new_mat('terrain'); nb = NB(mat)
    A1 = nb.n('ShaderNodeAttribute', attribute_name='masks'); A1.attribute_type = 'GEOMETRY'
    A2 = nb.n('ShaderNodeAttribute', attribute_name='masks2'); A2.attribute_type = 'GEOMETRY'
    sepA = nb.n('ShaderNodeSeparateColor'); nb.link(A1.outputs['Color'], sepA.inputs[0])
    sepB = nb.n('ShaderNodeSeparateColor'); nb.link(A2.outputs['Color'], sepB.inputs[0])
    obj = nb.coord('Object')
    # sand colours
    sn = nb.noise(obj, 3.0, 5, 0.55)
    sand_dry = nb.ramp(sn.outputs['Fac'], [(0.35, (0.55, 0.45, 0.30)), (0.65, (0.72, 0.62, 0.45))])
    gn = nb.noise(obj, 90, 3, 0.7)
    grains = nb.mix(nb.math('MULTIPLY', gn.outputs['Fac'], 0.5), sand_dry.outputs[0], (0.35, 0.28, 0.18, 1))
    wet_c = (0.16, 0.12, 0.08, 1)
    tide_c = nb.mix(A1.outputs['Alpha'], grains, (0.12, 0.09, 0.05, 1))
    sand = nb.mix(sepA.outputs[0], tide_c, wet_c)
    # under-water sand is paler, patches of dark coral/seagrass
    pn = nb.noise(nb.mapping(obj, (0.5, 0.5, 0.5)), 1.0, 4, 0.6, distort=0.6)
    patch = nb.ramp(pn.outputs['Fac'], [(0.50, (0, 0, 0)), (0.58, (1, 1, 1))])
    patch_f = nb.math('MULTIPLY', patch.outputs[0], nb.math('MULTIPLY', sepB.outputs[1], nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', sepB.outputs[2], 0.0))))
    deepc = nb.mix(nb.math('MULTIPLY', sepB.outputs[2], 0.8), (0.45, 0.42, 0.32, 1), (0.22, 0.26, 0.18, 1))
    seabed = nb.mix(patch_f, deepc, (0.07, 0.10, 0.05, 1))
    sand = nb.mix(sepB.outputs[1], sand, seabed)
    # grass / jungle
    gl = nb.noise(obj, 0.4, 4, 0.6)
    grass_c = nb.ramp(gl.outputs['Fac'], [(0.3, (0.07, 0.20, 0.03)), (0.7, (0.20, 0.38, 0.06))])
    gf = nb.noise(obj, 25, 3, 0.6)
    grass_c2 = nb.mix(nb.math('MULTIPLY', gf.outputs['Fac'], 0.5), grass_c.outputs[0], (0.04, 0.12, 0.02, 1))
    jn = nb.noise(obj, 0.15, 5, 0.6)
    jung_c = nb.ramp(jn.outputs['Fac'], [(0.3, (0.012, 0.055, 0.015)), (0.7, (0.05, 0.15, 0.03))])
    jf = nb.noise(obj, 3.0, 4, 0.6)
    jung_c2 = nb.mix(nb.math('MULTIPLY', jf.outputs['Fac'], 0.6), jung_c.outputs[0], (0.01, 0.04, 0.01, 1))
    col = nb.mix(sepA.outputs[1], sand, grass_c2)
    col = nb.mix(sepA.outputs[2], col, jung_c2)
    # foam lace on sand
    fn = nb.noise(nb.mapping(obj, (1.5, 1.5, 1.5)), 3.0, 4, 0.6, distort=1.2)
    lace = nb.ramp(fn.outputs['Fac'], [(0.42, (0, 0, 0)), (0.50, (1, 1, 1))])
    ff = nb.math('MULTIPLY', lace.outputs[0], sepB.outputs[0])
    col = nb.mix(ff, col, (0.9, 0.92, 0.9, 1))
    # roughness: wet sand glossy
    rough = nb.mix(sepA.outputs[0], 0.95, 0.2, 'FLOAT')
    # bump
    b1 = nb.noise(obj, 110, 3, 0.6)
    rp = nb.noise(nb.mapping(obj, (2.0, 7.0, 1)), 1.0, 3, 0.5, distort=0.8)
    cb = nb.noise(obj, 1.2, 6, 0.65)
    hs = nb.math('ADD', nb.math('MULTIPLY', b1.outputs['Fac'], 0.5), nb.math('MULTIPLY', rp.outputs['Fac'], 1.2))
    hm = nb.mix(nb.math('MAXIMUM', sepA.outputs[1], sepA.outputs[2]), hs, nb.math('MULTIPLY', cb.outputs['Fac'], 3.0), 'FLOAT')
    bump = nb.bump(hm, 0.5, 0.05)
    p = nb.principled(col, rough, Normal=bump)
    p.inputs['Specular IOR Level'].default_value = 0.3
    nb.out(p.outputs[0])
    ob, *_ = grid_mesh('terrain', xs, ys, height, mat)
    me = ob.data
    for an, arr in (('masks', rgb), ('masks2', rgb2)):
        ca = me.color_attributes.new(an, 'FLOAT_COLOR', 'POINT')
        ca.data.foreach_set('color', arr.ravel())
    return ob

def build_water():
    xs = axis(-4000, 120, -130, 40, 1.2, 1.12)
    ys = axis(-60, 6000, -40, 120, 1.2, 1.12)
    X, Y = np.meshgrid(xs, ys)
    Zt = height(X, Y)
    # beyond the terrain mesh edge the sea is deep
    depth = np.clip(-Zt, 0, 30)
    depth = np.where((X < -400) | (Y > 2500), 30, depth)
    # keep the water surface flat at z=0
    rgb = np.zeros(X.shape + (4,), dtype=np.float32)
    rgb[..., 0] = depth; rgb[..., 3] = 1
    mat = new_mat('water'); nb = NB(mat)
    A = nb.n('ShaderNodeAttribute', attribute_name='depth'); A.attribute_type = 'GEOMETRY'
    sepA = nb.n('ShaderNodeSeparateColor'); nb.link(A.outputs['Color'], sepA.inputs[0])
    dep = sepA.outputs[0]
    obj = nb.coord('Object')
    # wave bump (long crests parallel to shore, plus small ripples)
    w1 = nb.noise(nb.mapping(obj, (0.9, 0.12, 1)), 1.2, 3, 0.5, distort=0.5)
    w2 = nb.noise(nb.mapping(obj, (2.5, 0.8, 1)), 3.0, 3, 0.5)
    w3 = nb.noise(nb.mapping(obj, (12, 5, 1)), 3.0, 2, 0.5)
    hh = nb.math('ADD', nb.math('MULTIPLY', w1.outputs['Fac'], 1.0), nb.math('ADD', nb.math('MULTIPLY', w2.outputs['Fac'], 0.35), nb.math('MULTIPLY', w3.outputs['Fac'], 0.12)))
    bump = nb.bump(hh, 0.55, 0.12)
    # colour by depth: shallow aqua -> deep blue
    cdeep = nb.ramp(nb.math('DIVIDE', dep, 6.0, clamp=True), [(0.0, (0.03, 0.62, 0.52)), (0.25, (0.01, 0.42, 0.50)), (0.6, (0.0, 0.14, 0.34)), (1.0, (0.0, 0.04, 0.14))])
    # how see-through: shallow clear, deeper opaque
    opac = nb.math('SUBTRACT', 1.0, nb.math('POWER', 2.718, nb.math('MULTIPLY', dep, -1.2)), clamp=True)
    opac = nb.math('MAXIMUM', opac, 0.18)
    opac = nb.math('MAXIMUM', opac, nb.math('MULTIPLY', nb.math('SUBTRACT', dep, 5), 0.5, clamp=True))
    body = nb.n('ShaderNodeBsdfDiffuse'); body.inputs['Color'].default_value = (0, 0, 0, 1)
    nb.link(cdeep.outputs[0], body.inputs['Color'])
    trans = nb.n('ShaderNodeBsdfTransparent'); trans.inputs['Color'].default_value = (0.55, 0.95, 0.88, 1)
    interior = nb.n('ShaderNodeMixShader')
    nb.link(opac, interior.inputs[0]); nb.link(trans.outputs[0], interior.inputs[1]); nb.link(body.outputs[0], interior.inputs[2])
    glossy = nb.n('ShaderNodeBsdfGlossy'); glossy.inputs['Roughness'].default_value = 0.05; glossy.inputs['Color'].default_value = (0.72, 0.9, 0.95, 1)
    nb.link(bump, glossy.inputs['Normal'])
    fr = nb.n('ShaderNodeFresnel'); fr.inputs['IOR'].default_value = 1.33
    nb.link(bump, fr.inputs['Normal'])
    surf = nb.n('ShaderNodeMixShader')
    nb.link(fr.outputs[0], surf.inputs[0]); nb.link(interior.outputs[0], surf.inputs[1]); nb.link(glossy.outputs[0], surf.inputs[2])
    # foam: very shallow water, and the reef crest band
    fstreak = nb.noise(nb.mapping(obj, (0.9, 0.09, 1)), 2.0, 5, 0.65, distort=1.0)
    fcell = nb.noise(nb.mapping(obj, (3.5, 0.6, 1)), 3.0, 4, 0.6, distort=0.8)
    near = nb.math('SUBTRACT', 1.0, nb.math('DIVIDE', dep, 0.35, clamp=True))
    reef_band = nb.math('MULTIPLY', nb.math('SUBTRACT', 1.0, nb.math('DIVIDE', nb.math('ABSOLUTE', nb.math('SUBTRACT', dep, 0.6)), 0.55, clamp=True)), 1.0)
    reef_zone = nb.math('MULTIPLY', reef_band, nb.math('ADD', nb.math('MULTIPLY', fstreak.outputs['Fac'], 1.6), -0.55))
    ffac = nb.math('ADD', nb.math('MULTIPLY', near, nb.math('ADD', nb.math('MULTIPLY', fcell.outputs['Fac'], 2.2), -0.8)), reef_zone)
    ffac = nb.ramp(nb.math('MAXIMUM', ffac, 0.0), [(0.15, (0, 0, 0)), (0.5, (1, 1, 1))]).outputs[0]
    foamb = nb.n('ShaderNodeBsdfDiffuse'); foamb.inputs['Color'].default_value = (0.85, 0.9, 0.9, 1)
    fin = nb.n('ShaderNodeMixShader')
    nb.link(ffac, fin.inputs[0]); nb.link(surf.outputs[0], fin.inputs[1]); nb.link(foamb.outputs[0], fin.inputs[2])
    nb.out(fin.outputs[0])
    ob, *_ = grid_mesh('water', xs, ys, lambda X, Y: np.zeros_like(X), mat)
    ca = ob.data.color_attributes.new('depth', 'FLOAT_COLOR', 'POINT')
    ca.data.foreach_set('color', rgb.ravel())
    return ob
