"""
Builds and draws "a military base": a British army camp at dusk after rain, 1915.
Run:  python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png
Everything (scene, light, haze, finishing) is made here; textures come from the kit's surfaces shelf.
"""
import sys, math, random, os
import bpy
import bmesh
from mathutils import Vector, Euler, Matrix

W, H, SAMPLES, OUT = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
SURF = '/home/claude/kit-military-2/place-brief/surfaces'
random.seed(7)
DR = random.Random(2026)  # the dressing has its own dice, so the layout's dice are untouched
HAZE_D = float(os.environ.get('HAZE_D', '0.0025'))
SKY_CAM = float(os.environ.get('SKY_CAM', '0.65'))
SKY_LIGHT = float(os.environ.get('SKY_LIGHT', '0.9'))
HAZE_H = float(os.environ.get('HAZE_H', '9'))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------------------------------------------------------------- materials
def new_mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    return m, nt

_img = {}
def load_img(sset, kind, nc=False):
    key = (sset, kind)
    if key in _img:
        return _img[key]
    p = '%s/%s/%s_%s_2k.jpg' % (SURF, sset, sset, kind)
    im = bpy.data.images.load(p)
    im.colorspace_settings.name = 'Non-Color' if nc else 'sRGB'
    _img[key] = im
    return im

def surf(name, sset, size_m, tint=(1, 1, 1), dark=0.5, rough=1.0, bump=0.4, rot=0.0,
         grime=0.5, patch=0.35, metal=0.0, spec=0.3, foot=0.0, seams=0, fine=0.0, edge=0.0, wfoot=0.0, edgecol=(0.30, 0.25, 0.20), polish=0.0, rust=0.0, wet=0.0):
    m, nt = new_mat(name)
    N = nt.nodes
    L = nt.links
    out = N.new('ShaderNodeOutputMaterial')
    bsdf = N.new('ShaderNodeBsdfPrincipled')
    L.new(bsdf.outputs[0], out.inputs[0])
    tc = N.new('ShaderNodeTexCoord')
    mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / size_m,) * 3
    mp.inputs['Rotation'].default_value = (0, 0, rot)
    L.new(tc.outputs['Object'], mp.inputs[0])

    def tex(kind, nc):
        t = N.new('ShaderNodeTexImage')
        t.image = load_img(sset, kind, nc)
        t.projection = 'BOX'
        t.projection_blend = 0.25
        L.new(mp.outputs[0], t.inputs[0])
        return t
    d = tex('diff', False)
    r = tex('rough', True)
    h = tex('disp', True)
    mix = N.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 1.0
    L.new(d.outputs['Color'], mix.inputs[6])
    mix.inputs[7].default_value = (tint[0] * dark, tint[1] * dark, tint[2] * dark, 1)
    # large patchy variation
    nz = N.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 0.9
    nz.inputs['Detail'].default_value = 5
    L.new(tc.outputs['Object'], nz.inputs['Vector'])
    ramp = N.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (1 - patch, 1 - patch, 1 - patch, 1)
    ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[1].color = (1, 1, 1, 1)
    L.new(nz.outputs['Fac'], ramp.inputs[0])
    mix2 = N.new('ShaderNodeMix')
    mix2.data_type = 'RGBA'
    mix2.blend_type = 'MULTIPLY'
    mix2.inputs[0].default_value = 1.0
    L.new(mix.outputs[2], mix2.inputs[6])
    L.new(ramp.outputs[0], mix2.inputs[7])
    if fine:
        nz2 = N.new('ShaderNodeTexNoise')
        nz2.inputs['Scale'].default_value = 7.0
        nz2.inputs['Detail'].default_value = 8
        L.new(tc.outputs['Object'], nz2.inputs['Vector'])
        rp2 = N.new('ShaderNodeValToRGB')
        rp2.color_ramp.elements[0].position = 0.3
        rp2.color_ramp.elements[0].color = (1 - fine, 1 - fine, 1 - fine * 0.8, 1)
        rp2.color_ramp.elements[1].position = 0.7
        rp2.color_ramp.elements[1].color = (1, 1, 1, 1)
        L.new(nz2.outputs['Fac'], rp2.inputs[0])
        mixf = N.new('ShaderNodeMix'); mixf.data_type = 'RGBA'; mixf.blend_type = 'MULTIPLY'; mixf.inputs[0].default_value = 1.0
        L.new(mix2.outputs[2], mixf.inputs[6]); L.new(rp2.outputs[0], mixf.inputs[7])
        mix2 = mixf
    # grime in hollows: ambient occlusion
    ao = N.new('ShaderNodeAmbientOcclusion')
    ao.inputs['Distance'].default_value = 0.5
    mix3 = N.new('ShaderNodeMix')
    mix3.data_type = 'RGBA'
    mix3.blend_type = 'MULTIPLY'
    mix3.inputs[0].default_value = grime
    L.new(mix2.outputs[2], mix3.inputs[6])
    L.new(ao.outputs['Color'], mix3.inputs[7])
    last = mix3
    if foot or seams:
        sp = N.new('ShaderNodeSeparateXYZ')
        L.new(tc.outputs['Object'], sp.inputs[0])
    if foot:
        mrf = N.new('ShaderNodeMapRange')
        mrf.inputs[1].default_value = 0.0; mrf.inputs[2].default_value = foot
        mrf.inputs[3].default_value = 0.30; mrf.inputs[4].default_value = 1.0
        mrf.clamp = True
        L.new(sp.outputs['Z'], mrf.inputs[0])
        fm = N.new('ShaderNodeMix'); fm.data_type = 'RGBA'; fm.blend_type = 'MULTIPLY'; fm.inputs[0].default_value = 1.0
        L.new(last.outputs[2], fm.inputs[6])
        # mud colour at the foot instead of plain black
        mc = N.new('ShaderNodeCombineColor')
        L.new(mrf.outputs[0], mc.inputs[0]); L.new(mrf.outputs[0], mc.inputs[1]); L.new(mrf.outputs[0], mc.inputs[2])
        L.new(mc.outputs[0], fm.inputs[7])
        last = fm
    if seams:
        at = N.new('ShaderNodeMath'); at.operation = 'ARCTAN2'
        L.new(sp.outputs['Y'], at.inputs[0]); L.new(sp.outputs['X'], at.inputs[1])
        am = N.new('ShaderNodeMath'); am.operation = 'MULTIPLY'; am.inputs[1].default_value = seams
        L.new(at.outputs[0], am.inputs[0])
        sn = N.new('ShaderNodeMath'); sn.operation = 'SINE'
        L.new(am.outputs[0], sn.inputs[0])
        ab = N.new('ShaderNodeMath'); ab.operation = 'ABSOLUTE'
        L.new(sn.outputs[0], ab.inputs[0])
        pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 25
        L.new(ab.outputs[0], pw.inputs[0])
        inv = N.new('ShaderNodeMath'); inv.operation = 'MULTIPLY_ADD'; inv.inputs[1].default_value = -0.45; inv.inputs[2].default_value = 1.0
        L.new(pw.outputs[0], inv.inputs[0])
        sm = N.new('ShaderNodeMix'); sm.data_type = 'RGBA'; sm.blend_type = 'MULTIPLY'; sm.inputs[0].default_value = 1.0
        L.new(last.outputs[2], sm.inputs[6])
        mc2 = N.new('ShaderNodeCombineColor')
        L.new(inv.outputs[0], mc2.inputs[0]); L.new(inv.outputs[0], mc2.inputs[1]); L.new(inv.outputs[0], mc2.inputs[2])
        L.new(mc2.outputs[0], sm.inputs[7])
        last = sm
    if wfoot:
        # mud climbs from the ground: world height, speckled edge
        geo = N.new('ShaderNodeNewGeometry')
        wsp = N.new('ShaderNodeSeparateXYZ')
        L.new(geo.outputs['Position'], wsp.inputs[0])
        wn = N.new('ShaderNodeTexNoise'); wn.inputs['Scale'].default_value = 14.0; wn.inputs['Detail'].default_value = 6
        L.new(geo.outputs['Position'], wn.inputs['Vector'])
        wl = N.new('ShaderNodeMath'); wl.operation = 'MULTIPLY_ADD'; wl.inputs[1].default_value = 1.1; wl.inputs[2].default_value = 0.45 * wfoot
        L.new(wn.outputs['Fac'], wl.inputs[0])
        wmr = N.new('ShaderNodeMapRange'); wmr.clamp = True
        wmr.inputs[1].default_value = 0.0
        wmr.inputs[3].default_value = 0.28; wmr.inputs[4].default_value = 1.0
        L.new(wsp.outputs['Z'], wmr.inputs[0]); L.new(wl.outputs[0], wmr.inputs[2])
        wc = N.new('ShaderNodeCombineColor')
        wb = N.new('ShaderNodeMath'); wb.operation = 'MULTIPLY'; wb.inputs[1].default_value = 0.88
        L.new(wmr.outputs[0], wb.inputs[0])
        L.new(wmr.outputs[0], wc.inputs[0]); L.new(wmr.outputs[0], wc.inputs[1]); L.new(wb.outputs[0], wc.inputs[2])
        wm = N.new('ShaderNodeMix'); wm.data_type = 'RGBA'; wm.blend_type = 'MULTIPLY'; wm.inputs[0].default_value = 1.0
        L.new(last.outputs[2], wm.inputs[6]); L.new(wc.outputs[0], wm.inputs[7])
        last = wm
    if rust:
        # rust blooms where paint has gone: noise blotches
        rn = N.new('ShaderNodeTexNoise'); rn.inputs['Scale'].default_value = 5.0; rn.inputs['Detail'].default_value = 7
        L.new(tc.outputs['Object'], rn.inputs['Vector'])
        rr_ = N.new('ShaderNodeMapRange'); rr_.clamp = True; rr_.inputs[1].default_value = 0.44; rr_.inputs[2].default_value = 0.60
        rr_.inputs[3].default_value = 0.0; rr_.inputs[4].default_value = rust
        L.new(rn.outputs['Fac'], rr_.inputs[0])
        rx = N.new('ShaderNodeMix'); rx.data_type = 'RGBA'; rx.blend_type = 'MIX'
        L.new(rr_.outputs[0], rx.inputs[0]); L.new(last.outputs[2], rx.inputs[6])
        rx.inputs[7].default_value = (0.20, 0.075, 0.03, 1)
        last = rx
    if polish:
        # boots polish the middle of the track: pale, broken up by noise, fading with distance
        pg = N.new('ShaderNodeNewGeometry')
        ps = N.new('ShaderNodeSeparateXYZ'); L.new(pg.outputs['Position'], ps.inputs[0])
        pa = N.new('ShaderNodeMath'); pa.operation = 'ABSOLUTE'; L.new(ps.outputs['X'], pa.inputs[0])
        pm_ = N.new('ShaderNodeMapRange'); pm_.clamp = True
        pm_.inputs[1].default_value = 0.04; pm_.inputs[2].default_value = 0.40; pm_.inputs[3].default_value = 1.0; pm_.inputs[4].default_value = 0.0
        L.new(pa.outputs[0], pm_.inputs[0])
        pp = N.new('ShaderNodeMath'); pp.operation = 'POWER'; pp.inputs[1].default_value = 1.6
        L.new(pm_.outputs[0], pp.inputs[0])
        pf = N.new('ShaderNodeMapRange'); pf.clamp = True
        pf.inputs[1].default_value = 6.0; pf.inputs[2].default_value = 22.0; pf.inputs[3].default_value = 1.0; pf.inputs[4].default_value = 0.0
        L.new(ps.outputs['Y'], pf.inputs[0])
        pn = N.new('ShaderNodeTexNoise'); pn.inputs['Scale'].default_value = 5.0; pn.inputs['Detail'].default_value = 5
        L.new(pg.outputs['Position'], pn.inputs['Vector'])
        pnm = N.new('ShaderNodeMapRange'); pnm.clamp = True; pnm.inputs[1].default_value = 0.35; pnm.inputs[2].default_value = 0.7
        L.new(pn.outputs['Fac'], pnm.inputs[0])
        pk = N.new('ShaderNodeMath'); pk.operation = 'MULTIPLY'
        L.new(pp.outputs[0], pk.inputs[0]); L.new(pnm.outputs[0], pk.inputs[1])
        pk2 = N.new('ShaderNodeMath'); pk2.operation = 'MULTIPLY'
        L.new(pk.outputs[0], pk2.inputs[0]); L.new(pf.outputs[0], pk2.inputs[1])
        pk3 = N.new('ShaderNodeMath'); pk3.operation = 'MULTIPLY'; pk3.inputs[1].default_value = polish
        L.new(pk2.outputs[0], pk3.inputs[0])
        px_ = N.new('ShaderNodeMix'); px_.data_type = 'RGBA'; px_.blend_type = 'MIX'
        L.new(pk3.outputs[0], px_.inputs[0]); L.new(last.outputs[2], px_.inputs[6])
        px_.inputs[7].default_value = (0.19, 0.16, 0.13, 1)
        last = px_
    if edge:
        # convex edges rub bright: where the bevelled normal parts from the real one
        bev = N.new('ShaderNodeBevel'); bev.inputs['Radius'].default_value = 0.02
        gn = N.new('ShaderNodeNewGeometry')
        dt = N.new('ShaderNodeVectorMath'); dt.operation = 'DOT_PRODUCT'
        L.new(gn.outputs['Normal'], dt.inputs[0]); L.new(bev.outputs['Normal'], dt.inputs[1])
        emr = N.new('ShaderNodeMapRange'); emr.clamp = True
        emr.inputs[1].default_value = 0.999; emr.inputs[2].default_value = 0.96
        emr.inputs[3].default_value = 0.0; emr.inputs[4].default_value = edge
        L.new(dt.outputs['Value'], emr.inputs[0])
        enz = N.new('ShaderNodeTexNoise'); enz.inputs['Scale'].default_value = 9.0; enz.inputs['Detail'].default_value = 4
        L.new(tc.outputs['Object'], enz.inputs['Vector'])
        emk = N.new('ShaderNodeMath'); emk.operation = 'MULTIPLY'; emk.use_clamp = True
        emn = N.new('ShaderNodeMapRange'); emn.clamp = True; emn.inputs[1].default_value = 0.35; emn.inputs[2].default_value = 0.65
        L.new(enz.outputs['Fac'], emn.inputs[0])
        L.new(emr.outputs[0], emk.inputs[0]); L.new(emn.outputs[0], emk.inputs[1])
        em_ = N.new('ShaderNodeMix'); em_.data_type = 'RGBA'; em_.blend_type = 'MIX'
        L.new(emk.outputs[0], em_.inputs[0])
        L.new(last.outputs[2], em_.inputs[6]); em_.inputs[7].default_value = (edgecol[0], edgecol[1], edgecol[2], 1)
        last = em_
        L.new(bev.outputs['Normal'], bsdf.inputs['Normal']) if False else None
    L.new(last.outputs[2], bsdf.inputs['Base Color'])
    rm = N.new('ShaderNodeMath')
    rm.operation = 'MULTIPLY'
    rm.inputs[1].default_value = rough
    L.new(r.outputs['Color'], rm.inputs[0])
    rm2 = N.new('ShaderNodeMath')
    rm2.operation = 'MINIMUM'
    rm2.inputs[1].default_value = 1.0
    L.new(rm.outputs[0], rm2.inputs[0])
    if wet:
        # standing water films on the wood: patches of low roughness catch the lamps
        wn2 = N.new('ShaderNodeTexNoise'); wn2.inputs['Scale'].default_value = 2.2; wn2.inputs['Detail'].default_value = 3
        wg = N.new('ShaderNodeNewGeometry')
        L.new(wg.outputs['Position'], wn2.inputs['Vector'])
        wmr2 = N.new('ShaderNodeMapRange'); wmr2.clamp = True
        wmr2.inputs[1].default_value = 0.45; wmr2.inputs[2].default_value = 0.58; wmr2.inputs[3].default_value = 1.0; wmr2.inputs[4].default_value = wet
        L.new(wn2.outputs['Fac'], wmr2.inputs[0])
        wrm = N.new('ShaderNodeMath'); wrm.operation = 'MULTIPLY'
        L.new(rm2.outputs[0], wrm.inputs[0]); L.new(wmr2.outputs[0], wrm.inputs[1])
        L.new(wrm.outputs[0], bsdf.inputs['Roughness'])
    else:
        L.new(rm2.outputs[0], bsdf.inputs['Roughness'])
    bp = N.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = bump
    bp.inputs['Distance'].default_value = 0.03
    L.new(h.outputs['Color'], bp.inputs['Height'])
    L.new(bp.outputs[0], bsdf.inputs['Normal'])
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Specular IOR Level'].default_value = spec
    return m

def plain(name, col, rough=0.6, metal=0.0, emit=None, emit_strength=0.0, spec=0.5):
    m, nt = new_mat(name)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(b.outputs[0], out.inputs[0])
    b.inputs['Base Color'].default_value = (col[0], col[1], col[2], 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    b.inputs['Specular IOR Level'].default_value = spec
    if emit:
        b.inputs['Emission Color'].default_value = (emit[0], emit[1], emit[2], 1)
        b.inputs['Emission Strength'].default_value = emit_strength
    return m

def emissive(name, col, strength):
    m, nt = new_mat(name)
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (col[0], col[1], col[2], 1)
    e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], out.inputs[0])
    return m

# ---------------------------------------------------------------- helpers
PARENT = [None]

def finish(o, mat, name=None):
    if name:
        o.name = name
    if mat is not None:
        o.data.materials.append(mat)
    if PARENT[0] is not None:
        o.parent = PARENT[0]
    return o

def box(loc, size, mat, rot=(0, 0, 0), name='box'):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = size
    return finish(o, mat, name)

def cyl(p0, p1, r, mat, verts=10, r1=None, name='cyl'):
    p0 = Vector(p0); p1 = Vector(p1)
    d = p1 - p0
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r, radius2=(r if r1 is None else r1),
                                    depth=d.length, location=(p0 + p1) / 2)
    o = bpy.context.object
    o.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    return finish(o, mat, name)

def sphere(loc, scale, mat, seg=12, rot=(0, 0, 0), name='sph'):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=max(6, seg // 2), radius=1, location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = scale
    return finish(o, mat, name)

def torus(loc, R, r, mat, rot=(0, 0, 0), name='torus'):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=40, minor_segments=8,
                                     location=loc, rotation=rot)
    o = bpy.context.object
    return finish(o, mat, name)

def from_bm(bm, name, mat, loc=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.location = loc
    return finish(o, mat)

def smooth(o):
    for p in o.data.polygons:
        p.use_smooth = True

def empty(loc, rotz=0.0):
    e = bpy.data.objects.new('grp', None)
    scene.collection.objects.link(e)
    e.location = loc
    e.rotation_euler = (0, 0, rotz)
    return e

# ---------------------------------------------------------------- materials list
stonem = plain('stonem', (0.032, 0.03, 0.028), rough=0.95, spec=0.0)
mudblob = plain('mudblob', (0.03, 0.024, 0.02), rough=0.85, spec=0.03)
mud = surf('mud', 'muddy_tracks', 2.25, tint=(0.62, 0.72, 0.85), dark=0.34, rough=0.6, bump=1.2, rot=math.pi / 2, grime=0.2, patch=0.5)
gravel = surf('gravelpatch', 'gravel_road', 2.0, tint=(0.8, 0.78, 0.75), dark=0.35, rough=1.0, bump=0.8)
planks = surf('planks', 'old_planks_02', 2.0, tint=(0.9, 0.85, 0.8), dark=0.42, rough=0.9, bump=0.6, grime=0.6, edge=0.55, wfoot=0.3)
planks_dark = surf('planks_wet', 'old_planks_02', 2.0, tint=(0.7, 0.68, 0.66), dark=0.30, rough=0.55, bump=0.6, grime=0.7, fine=0.3, edge=0.5, wfoot=0.35)
track = surf('track', 'old_planks_02', 2.0, tint=(0.7, 0.68, 0.66), dark=0.30, rough=0.55, bump=0.6, grime=0.7, fine=0.3, edge=0.5, polish=0.7, wet=0.3)
wheelwood = surf('wheelwood', 'old_planks_02', 2.0, tint=(0.78, 0.74, 0.70), dark=0.36, rough=0.8, bump=0.5, grime=0.6, edge=0.5, wfoot=1.3)
planks_worn = surf('planks_worn', 'old_planks_02', 2.0, tint=(1.0, 0.95, 0.88), dark=0.52, rough=0.5, bump=0.4, grime=0.4, fine=0.25, edge=0.3)
cabinwood = surf('cabin', 'distressed_painted_planks', 1.6, tint=(0.8, 0.85, 0.85), dark=0.45, rough=0.95, bump=0.5, edge=0.5, wfoot=0.4)
roofiron = surf('roofiron', 'rusty_corrugated_iron', 2.0, tint=(0.9, 0.8, 0.75), dark=0.5, rough=0.8, bump=0.7, metal=0.2, edge=0.4)
gunmetal = surf('gunpaint', 'rusty_metal_02', 1.0, tint=(0.45, 0.55, 0.45), dark=0.5, rough=0.85, bump=0.4, metal=0.3, edge=0.9, wfoot=0.25, edgecol=(0.30, 0.27, 0.22), rust=1.0)
rustiron = surf('rustiron', 'rusty_metal_02', 1.0, tint=(0.9, 0.7, 0.55), dark=0.55, rough=0.8, bump=0.4, metal=0.5, edge=0.7, wfoot=0.5, edgecol=(0.28, 0.2, 0.14))
hess = surf('sandbag', 'hessian_380', 0.27, tint=(0.8, 0.72, 0.62), dark=0.55, rough=1.0, bump=0.8, grime=0.8, wfoot=0.3)
canvas = surf('canvas', 'rough_linen', 0.27, tint=(0.95, 0.82, 0.58), dark=0.95, rough=1.0, bump=0.5, grime=0.7, patch=0.5, foot=1.6, seams=12, fine=0.35)
canvas_patch = surf('canvas_patch', 'rough_linen', 0.27, tint=(0.98, 0.82, 0.58), dark=1.05, rough=1.0, bump=0.6, grime=0.6, patch=0.4, fine=0.3, wfoot=0.3)
rubbed = plain('rubbed', (0.13, 0.10, 0.07), rough=0.45, spec=0.5)
canvas_dark = plain('patch_stitch', (0.02, 0.018, 0.014), rough=1.0, spec=0.0)
def backface_glow(m, col, strength):
    nt_ = m.node_tree
    out_ = [n for n in nt_.nodes if n.type == 'OUTPUT_MATERIAL'][0]
    src = out_.inputs['Surface'].links[0].from_socket
    em = nt_.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (col[0], col[1], col[2], 1)
    em.inputs['Strength'].default_value = strength
    bf = nt_.nodes.new('ShaderNodeNewGeometry')
    mx = nt_.nodes.new('ShaderNodeMixShader')
    nt_.links.new(bf.outputs['Backfacing'], mx.inputs[0])
    nt_.links.new(src, mx.inputs[1])
    nt_.links.new(em.outputs[0], mx.inputs[2])
    nt_.links.new(mx.outputs[0], out_.inputs['Surface'])
canvas_lit = canvas.copy()
canvas_lit.name = 'canvas_lit'
backface_glow(canvas_lit, (1.0, 0.5, 0.2), 0.03)
brass = plain('brass', (0.45, 0.30, 0.10), rough=0.45, metal=0.9)
tinm = plain('tin', (0.16, 0.17, 0.18), rough=0.45, metal=0.7)
blackiron = plain('blackiron', (0.03, 0.03, 0.03), rough=0.6, metal=0.4)
wirem = plain('wire', (0.35, 0.16, 0.07), rough=0.45, metal=0.7)
rope = plain('rope', (0.12, 0.09, 0.06), rough=0.9)
dark_in = plain('interior', (0.02, 0.018, 0.015), rough=1.0)
grass_m = plain('grass', (0.16, 0.11, 0.04), rough=0.8, emit=(0.5, 0.28, 0.08), emit_strength=0.08)
water = plain('water', (0.02, 0.03, 0.035), rough=0.04)
hillm = plain('hill', (0.03, 0.06, 0.08), rough=1.0, emit=(0.10, 0.20, 0.27), emit_strength=0.5)
hillm2 = plain('hill2', (0.05, 0.09, 0.12), rough=1.0, emit=(0.18, 0.30, 0.38), emit_strength=0.7)
lampglow = emissive('lampglow', (1.0, 0.62, 0.25), 32)
winglow = emissive('winglow', (1.0, 0.66, 0.28), 22)
doorglow = emissive('doorglow', (1.0, 0.6, 0.25), 8)

# ---------------------------------------------------------------- ground
bpy.ops.mesh.primitive_plane_add(size=300, location=(0, 60, 0))
g = bpy.context.object
g.name = 'ground'
g.data.materials.append(plain('gp',(0.02,0.02,0.02),rough=1.0) if os.environ.get('GP') else mud)

# mud lumps and stones along the verges (foreground interest)
def lump(x, y, s):
    sphere((x, y, s[2] * 0.3), s, mudblob, seg=10, name='lump')
for i in range(26):
    side = random.choice([-1, 1])
    x = side * random.uniform(1.0, 5.0)
    y = random.uniform(1.5, 16)
    lump(x, y, (random.uniform(0.15, 0.5), random.uniform(0.15, 0.5), random.uniform(0.05, 0.16)))

# puddles: long, mirror one light; flat, face up
def puddle(x, y, sx, sy, rot=0.0):
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=1, fill_type='NGON', location=(x, y, 0.012))
    o = bpy.context.object
    o.scale = (sx, sy, 1)
    o.rotation_euler = (0, 0, rot)
    bm = bmesh.new(); bm.from_mesh(o.data)
    for v in bm.verts:
        v.co.x *= 1 + 0.15 * math.sin(v.co.y * 5 + x)
        v.co.y *= 1 + 0.12 * math.sin(v.co.x * 7 + y)
    bm.to_mesh(o.data); bm.free()
    o.data.materials.append(water)
    return o
puddle(-1.0, 2.9, 0.42, 1.0, 0.1)
puddle(-1.55, 7.6, 0.42, 3.2, 0.02)
puddle(-1.3, 15.5, 0.35, 2.4, -0.03)
puddle(0.95, 3.6, 0.5, 1.6, 0.1)
puddle(1.3, 12.8, 0.6, 3.2, 0.03)

# ---------------------------------------------------------------- duckboards
bm = bmesh.new()
bmw = bmesh.new()  # (unused: track wear is in the board material now)
bmn = bmesh.new()  # nail heads
bmr = bmesh.new()  # rust runs under the nails
y = 0.9
i = 0
while y < 46:
    if random.random() < 0.05 and y > 6:
        y += 0.24; continue
    w = 1.15 + random.uniform(-0.03, 0.03)
    ang = random.uniform(-0.03, 0.03)
    xo = random.uniform(-0.04, 0.04) + 0.012 * y * math.sin(y * 0.2)
    tilt = random.uniform(-0.02, 0.02)
    zc = 0.035 + random.uniform(-0.01, 0.015)
    m = Matrix.Translation((xo, y, zc)) @ Euler((tilt, 0, ang)).to_matrix().to_4x4() @ Matrix.Diagonal((w, 0.2, 0.035, 1))
    bmesh.ops.create_cube(bm, size=1, matrix=m)
    if y < 14:
        for sxn in (-1, 1):
            for dyn in (-0.065, 0.065):
                nx_ = sxn * (w / 2 - 0.09)
                base_m = Matrix.Translation((xo, y, zc)) @ Euler((tilt, 0, ang)).to_matrix().to_4x4()
                bmesh.ops.create_cube(bmn, size=1, matrix=base_m @ Matrix.Translation((nx_, dyn, 0.0182)) @ Matrix.Diagonal((0.02, 0.02, 0.006, 1)))
                if DR.random() < 0.7:
                    rl = DR.uniform(0.05, 0.15)
                    bmesh.ops.create_cube(bmr, size=1, matrix=base_m @ Matrix.Translation((nx_, dyn - rl / 2 - 0.01, 0.0176)) @ Matrix.Diagonal((0.008, rl, 0.002, 1)))
    if y < 24:
        ww = (0.46 if y < 10 else 0.34) * DR.uniform(0.75, 1.15)
        mw = Matrix.Translation((xo, y, zc)) @ Euler((tilt, 0, ang)).to_matrix().to_4x4() @ Matrix.Translation((DR.uniform(-0.06, 0.06), 0, 0.0185)) @ Matrix.Diagonal((ww, 0.17, 0.003, 1))
        if DR.random() < 0.9:
            bmesh.ops.create_cube(bmw, size=1, matrix=mw)
    y += 0.235
    i += 1
duck = from_bm(bm, 'duckboards', track)
bmw.free()
from_bm(bmn, 'nails', plain('nailhead', (0.05, 0.026, 0.016), rough=0.9, spec=0.1))
from_bm(bmr, 'nailruns', plain('nailrun', (0.045, 0.018, 0.008), rough=1.0, spec=0.0))
# two runners
box((-0.45, 24, 0.0), (0.07, 46, 0.05), planks_dark, name='runner')
box((0.45, 24, 0.0), (0.07, 46, 0.05), planks_dark, name='runner')

# mud splashes and boot dirt on the boards, heavier at the sides and near the camera
for i in range(70):
    yy = random.uniform(1.0, 20) ** 1.0
    xx = random.choice([-1, 1]) * abs(random.gauss(0, 0.33)) + random.uniform(-0.1, 0.1)
    sphere((xx, yy, 0.05), (random.uniform(0.07, 0.30), random.uniform(0.05, 0.14), 0.01), mudblob, seg=8, rot=(0, 0, random.uniform(0, 3)), name='dirt')
# loose things in the foreground: planks, stones, rope, bags
for (px, py, pr) in [(-0.95, 2.1, 0.5), (-0.7, 2.6, 0.2)]:
    box((px, py, 0.03), (1.2, 0.18, 0.04), planks, rot=(0, 0, pr), name='loose plank')
for i in range(16):
    xx = random.choice([-1, 1]) * random.uniform(0.75, 1.6)
    sphere((xx, random.uniform(1.4, 4.0), 0.03), (random.uniform(0.06, 0.18), random.uniform(0.05, 0.15), random.uniform(0.04, 0.09)), stonem, seg=8, name='stone')
# a telegraph line down the right side of the camp, its wires running to the horizon
for k, py in enumerate([13.0, 22.0, 33.0, 46.0]):
    cyl((3.9, py, 0), (3.9, py, 6.2), 0.09, planks_dark, verts=6, name='pole')
    box((3.9, py, 5.9), (1.1, 0.07, 0.07), planks_dark, name='crossarm')
for dx in (-0.45, 0.45):
    curve = bpy.data.curves.new('tel', 'CURVE'); curve.dimensions = '3D'; curve.bevel_depth = 0.008
    sp = curve.splines.new('POLY'); pts = []
    ys = [13.0, 22.0, 33.0, 46.0]
    for a, b in zip(ys[:-1], ys[1:]):
        for j in range(8):
            t = j / 8
            pts.append((3.9 + dx, a + (b - a) * t, 5.9 - 0.4 * math.sin(math.pi * t)))
    pts.append((3.9 + dx, ys[-1], 5.9))
    sp.points.add(len(pts) - 1)
    for pnt, v in zip(sp.points, pts):
        pnt.co = (v[0], v[1], v[2], 1)
    o = bpy.data.objects.new('telwire', curve); scene.collection.objects.link(o); o.data.materials.append(blackiron)

# ---------------------------------------------------------------- bell tents
def tent(loc, door_dir, lit=False, R=1.75, Ht=3.2, wall=0.55, ropes=True):
    P = empty(loc, math.atan2(door_dir[1], door_dir[0]))
    PARENT[0] = P
    bm = bmesh.new()
    n = 24
    door_seg = {n - 2, n - 1, 0, 1}
    rings = [(R, 0.0), (R, 0.85), (R * 0.9, 1.45), (R * 0.66, 2.05), (R * 0.34, 2.65), (0.05, Ht)]
    vs = []
    for (rr, zz) in rings:
        vs.append([bm.verts.new((rr * math.cos(2 * math.pi * k / n), rr * math.sin(2 * math.pi * k / n), zz)) for k in range(n)])
    for r_i in range(len(rings) - 1):
        for k in range(n):
            if k in door_seg and r_i < 3:
                continue
            k2 = (k + 1) % n
            try:
                bm.faces.new([vs[r_i][k], vs[r_i][k2], vs[r_i + 1][k2], vs[r_i + 1][k]])
            except ValueError:
                pass
    o = from_bm(bm, 'tent', canvas_lit if lit else canvas)
    smooth(o)
    # thickness so the lit tent shows no leaks
    # floor
    cyl((0, 0, 0.01), (0, 0, 0.02), R * 0.98, dark_in, verts=28, name='tentfloor')
    # door frame edges: dark folded flap
    for s in (-1, 1):
        a = 2 * math.pi * (1 if s > 0 else -1) / n * 1.5
        # flap bundle at each side of the door
        cyl((R * math.cos(a), R * math.sin(a), 0.02), (R * 0.62 * math.cos(a), R * 0.62 * math.sin(a), Ht * 0.62), 0.045, canvas, verts=6, name='flap')
    # repair patches on the weather side, away from the door
    def prof(z):
        for (r0, z0), (r1, z1) in zip(rings[:-1], rings[1:]):
            if z0 <= z <= z1:
                return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
        return rings[-1][0]
    if ropes:
        for pi in range(3):
            a_cam = math.atan2(-loc[1], -loc[0]) - math.atan2(door_dir[1], door_dir[0])
            a0 = [-1.45, -1.12, -1.38][pi] + DR.uniform(-0.04, 0.04)
            aw = DR.uniform(0.2, 0.26); z0 = [0.35, 1.0, 1.7][pi] + DR.uniform(-0.05, 0.05); dz = DR.uniform(0.35, 0.6)
            for (grow, pm) in ((0.012, canvas_dark), (0.017, canvas_patch)):
                bmp = bmesh.new()
                gi = 5; gj = 4
                g_ = []
                ex = 0.0 if pm is canvas_patch else 1.0
                for jj in range(gj):
                    row_ = []
                    zz_ = (z0 - 0.015 * ex) + (dz + 0.03 * ex) * jj / (gj - 1)
                    for ii in range(gi):
                        aa = (a0 - 0.012 * ex) + (aw + 0.024 * ex) * ii / (gi - 1)
                        rr = prof(zz_) + grow
                        row_.append(bmp.verts.new((rr * math.cos(aa), rr * math.sin(aa), zz_)))
                    g_.append(row_)
                for jj in range(gj - 1):
                    for ii in range(gi - 1):
                        bmp.faces.new([g_[jj][ii], g_[jj][ii + 1], g_[jj + 1][ii + 1], g_[jj + 1][ii]])
                o_ = from_bm(bmp, 'patch', pm)
                smooth(o_)
    # pole top
    sphere((0, 0, Ht + 0.04), (0.07, 0.07, 0.07), blackiron, seg=8)
    # ropes and pegs (world-plane, local frame)
    for k in (range(3, n - 2, 3) if ropes else []):
        a = 2 * math.pi * k / n
        top = (R * 0.45 * math.cos(a), R * 0.45 * math.sin(a), 1.65)
        peg = ((R + 1.5) * math.cos(a), (R + 1.5) * math.sin(a), 0.05)
        cyl(top, peg, 0.011, rope, verts=4, name='rope')
        cyl(peg, (peg[0], peg[1], 0.0), 0.02, rustiron, verts=5, name='peg')
        cyl((peg[0], peg[1], 0.0), (peg[0], peg[1], 0.22), 0.02, rustiron, verts=5, name='peg')
    if lit:
        bpy.ops.object.light_add(type='POINT', location=(-0.2, 0, 1.5))
        l = bpy.context.object
        l.data.energy = 100
        l.data.color = (1.0, 0.58, 0.24)
        l.data.shadow_soft_size = 0.12
        l.parent = P
        # lamp hanging on the pole: the glow body sits clear of its light's casing
        sphere((0, 0, 1.7), (0.08, 0.08, 0.1), doorglow, seg=10, name='tentlamp')
    PARENT[0] = None
    return P

tent((-3.3, 9.5, 0), (1.0, -0.55), lit=True)
tent((-4.0, 16.5, 0), (1.0, -0.3))
tent((-4.4, 25.0, 0), (1.0, -0.2))
tent((5.0, 21.0, 0), (-1.0, -0.4))
for (tx, ty, dd) in [(-6.5, 34, (1, -0.1)), (6.5, 31, (-1, -0.1)), (-7.0, 43, (1, 0)), (7.0, 40, (-1, 0)), (-7.5, 52, (1, 0)), (7.5, 50, (-1, 0))]:
    tent((tx, ty, 0), dd, ropes=False)

# ---------------------------------------------------------------- watch tower
def tower(base):
    P = empty(base, 0.0)
    PARENT[0] = P
    hgt = 9.0
    legs = [(-1.5, -1.5), (1.5, -1.5), (-1.5, 1.5), (1.5, 1.5)]
    top = 0.85
    for (lx, ly) in legs:
        cyl((lx, ly, 0), (lx * top * 0.62, ly * top * 0.62, hgt), 0.19, planks_dark, verts=6, name='leg')
    # braces at levels
    levels = [0.0, 2.8, 5.6, hgt]
    def pos(lx, ly, z):
        f = 1 - (1 - top * 0.62) * (z / hgt)
        return (lx * f, ly * f, z)
    for a in range(4):
        la, lb = legs[a], legs[(a + 1) % 4] if a != 1 else legs[3]
    pairs = [(0, 1), (1, 3), (3, 2), (2, 0)]
    for (a, b) in pairs:
        for z0, z1 in zip(levels[:-1], levels[1:]):
            pa0, pa1 = pos(*legs[a], z0), pos(*legs[a], z1)
            pb0, pb1 = pos(*legs[b], z0), pos(*legs[b], z1)
            cyl(pa0, pb0, 0.05, planks, verts=5, name='hbrace')
            cyl(pa0, pb1, 0.045, planks, verts=5, name='xbrace')
            cyl(pb0, pa1, 0.045, planks, verts=5, name='xbrace')
    for (lx, ly) in legs:  # concrete-like footing of sandbags at foot
        sphere((lx * 1.08, ly * 1.08, 0.12), (0.4, 0.3, 0.16), hess, seg=8, name='footbag')
    # platform and cabin
    pz = hgt
    box((0, 0, pz + 0.05), (2.6, 2.6, 0.12), planks_dark, name='deck')
    box((0, 0, pz + 1.15), (2.1, 2.1, 2.0), cabinwood, name='cabin')
    # window (lit, open): a small emissive square on the face towards the camera (-y)
    box((-0.35, -1.06, pz + 1.35), (0.55, 0.03, 0.42), winglow, name='window')
    box((-0.35, -1.062, pz + 1.35), (0.62, 0.02, 0.05), blackiron, name='sill')
    # dark second window and door
    box((0.55, -1.06, pz + 1.35), (0.45, 0.03, 0.4), dark_in, name='window2')
    rustst = plain('rustst', (0.20, 0.07, 0.025), rough=0.7)
    for k in range(9):
        xx = -0.95 + k * 0.23 + random.uniform(-0.05, 0.05)
        hh = random.uniform(0.25, 0.9)
        box((xx, -1.065, pz + 2.12 - hh / 2), (random.uniform(0.02, 0.05), 0.012, hh), rustst, name='streak')
    box((-0.35, -1.07, pz + 1.0), (0.5, 0.012, 0.35), rustst, name='streak')
    # roof: two sloping tin sheets
    for s in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, s * 0.62, pz + 2.5))
        r = bpy.context.object
        r.scale = (2.9, 1.75, 0.05)
        r.rotation_euler = (s * -0.28, 0, 0) if s > 0 else (0.28, 0, 0)
        r.rotation_euler = (-s * 0.28, 0, 0)
        finish(r, roofiron, 'roof')
    for k in range(6):
        o = sphere((-1.0 + k * 0.4, -1.2, pz + 0.3), (0.22, 0.15, 0.1), hess, seg=10, name='deckbag'); smooth(o)
    for k in range(5):
        o = sphere((-0.8 + k * 0.4, -1.2, pz + 0.48), (0.22, 0.15, 0.1), hess, seg=10, name='deckbag'); smooth(o)
    # roof/rail: handrail posts
    for (lx, ly) in [(-1.3, -1.3), (1.3, -1.3), (-1.3, 1.3), (1.3, 1.3)]:
        cyl((lx, ly, pz + 0.1), (lx, ly, pz + 1.0), 0.04, planks, verts=5, name='rail')
    cyl((-1.3, -1.3, pz + 1.0), (1.3, -1.3, pz + 1.0), 0.035, planks, verts=5, name='rail')
    # ladder on the camera-side face
    for lxx in (1.1, 1.35):
        cyl((lxx, -1.5, 0), (lxx * 0.78, -1.35, hgt), 0.04, planks, verts=5, name='stile')
    for k in range(1, 18):
        z = k * hgt / 18
        f = 1 - 0.22 * (z / hgt)
        cyl((1.1 * f, -1.5 + 0.15 * z / hgt, z), (1.35 * f, -1.5 + 0.15 * z / hgt, z), 0.025, rubbed, verts=4, name='rung')
    PARENT[0] = None
    # light just outside the window, lighting the cabin wall and deck
    bpy.ops.object.light_add(type='POINT', location=(base[0] - 0.35, base[1] - 1.6, base[2] + hgt + 1.35))
    l = bpy.context.object
    l.data.energy = 200
    l.data.color = (1.0, 0.62, 0.26)
    l.data.shadow_soft_size = 0.1
    return P
tower((0.4, 21.0, 0))

# ---------------------------------------------------------------- guardroom hut at the tower's foot, and a stack of rifles
def hut(cx, cy, rz):
    P = empty((cx, cy, 0), rz)
    PARENT[0] = P
    box((0, 0, 1.0), (3.2, 2.6, 2.0), cabinwood, name='hutwall')
    box((0, 0, 0.12), (3.3, 2.7, 0.25), planks_dark, name='hutsill')
    for sgn in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, sgn * 0.7, 2.28))
        r = bpy.context.object
        r.scale = (3.5, 1.9, 0.05)
        r.rotation_euler = (-sgn * 0.3, 0, 0)
        finish(r, roofiron, 'hutroof')
    box((0.9, -1.31, 1.35), (0.6, 0.03, 0.5), winglow, name='hutwindow')
    box((0.9, -1.315, 1.1), (0.7, 0.03, 0.06), blackiron, name='hutsill2')
    box((-0.7, -1.31, 0.95), (0.8, 0.04, 1.8), dark_in, name='hutdoor')
    cyl((-1.0, 0.4, 2.0), (-1.0, 0.4, 3.3), 0.09, blackiron, verts=8, name='stovepipe')
    for k in range(7):
        o = sphere((-1.3 + k * 0.42, -1.55, 0.14), (0.22, 0.16, 0.1), hess, seg=10, name='hutbag'); smooth(o)
    PARENT[0] = None
    bpy.ops.object.light_add(type='POINT', location=(cx + 0.9, cy - 1.8, 1.4))
    l = bpy.context.object
    l.data.energy = 60; l.data.color = (1.0, 0.62, 0.26); l.data.shadow_soft_size = 0.08
hut(-3.4, 22.5, math.radians(-8))

def smoke_ribbon(base, height, drift, w0, w1):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('uv')
    nseg = 48
    rows = []
    rnd = random.Random(4)
    for i in range(nseg + 1):
        v = i / nseg
        cx = base[0] + drift * v ** 1.4 + 0.35 * math.sin(v * 7.0) * v
        cz = base[2] + height * v
        w = w0 + (w1 - w0) * v
        row = []
        for j, u in enumerate((0.0, 0.5, 1.0)):
            row.append((bm.verts.new((cx + (u - 0.5) * w, base[1], cz)), u, v))
        rows.append(row)
    for i in range(nseg):
        for j in range(2):
            quad = [rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]]
            f = bm.faces.new([q[0] for q in quad])
            for loop, q in zip(f.loops, quad):
                loop[uvl].uv = (q[1], q[2])
    me = bpy.data.meshes.new('smoke'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('smoke', me); scene.collection.objects.link(o)
    mm, nn = new_mat('smoke')
    N_, L_ = nn.nodes, nn.links
    out_ = N_.new('ShaderNodeOutputMaterial')
    mixs = N_.new('ShaderNodeMixShader')
    tr = N_.new('ShaderNodeBsdfTransparent')
    sm = N_.new('ShaderNodeBsdfPrincipled')
    sm.inputs['Base Color'].default_value = (0.035, 0.045, 0.06, 1)
    sm.inputs['Roughness'].default_value = 1.0
    sm.inputs['Emission Color'].default_value = (1.0, 0.5, 0.2, 1)
    sm.inputs['Emission Strength'].default_value = 0.10
    uv = N_.new('ShaderNodeTexCoord')
    sp_ = N_.new('ShaderNodeSeparateXYZ')
    L_.new(uv.outputs['UV'], sp_.inputs[0])
    # across: soft edges
    e1 = N_.new('ShaderNodeMath'); e1.operation = 'MULTIPLY'; e1.inputs[1].default_value = math.pi
    L_.new(sp_.outputs['X'], e1.inputs[0])
    e2 = N_.new('ShaderNodeMath'); e2.operation = 'SINE'
    L_.new(e1.outputs[0], e2.inputs[0])
    e3 = N_.new('ShaderNodeMath'); e3.operation = 'POWER'; e3.inputs[1].default_value = 1.6
    L_.new(e2.outputs[0], e3.inputs[0])
    # along: fades with height and rises in at the pipe
    a1 = N_.new('ShaderNodeMath'); a1.operation = 'SUBTRACT'; a1.inputs[0].default_value = 1.0
    L_.new(sp_.outputs['Y'], a1.inputs[1])
    a2 = N_.new('ShaderNodeMath'); a2.operation = 'POWER'; a2.inputs[1].default_value = 1.3
    L_.new(a1.outputs[0], a2.inputs[0])
    a3 = N_.new('ShaderNodeMath'); a3.operation = 'MULTIPLY'
    L_.new(a2.outputs[0], a3.inputs[0]); L_.new(e3.outputs[0], a3.inputs[1])
    # turbulence
    nzs_ = N_.new('ShaderNodeTexNoise'); nzs_.inputs['Scale'].default_value = 5.0; nzs_.inputs['Detail'].default_value = 6
    mpn = N_.new('ShaderNodeMapping'); mpn.inputs['Scale'].default_value = (2.0, 1.0, 1.0)
    L_.new(uv.outputs['UV'], mpn.inputs[0]); L_.new(mpn.outputs[0], nzs_.inputs['Vector'])
    nr = N_.new('ShaderNodeMapRange'); nr.inputs[1].default_value = 0.3; nr.inputs[2].default_value = 0.7
    nr.inputs[3].default_value = 0.25; nr.inputs[4].default_value = 1.1
    L_.new(nzs_.outputs['Fac'], nr.inputs[0])
    a4 = N_.new('ShaderNodeMath'); a4.operation = 'MULTIPLY'; a4.use_clamp = True
    L_.new(a3.outputs[0], a4.inputs[0]); L_.new(nr.outputs[0], a4.inputs[1])
    a5 = N_.new('ShaderNodeMath'); a5.operation = 'MULTIPLY'; a5.inputs[1].default_value = 0.95
    L_.new(a4.outputs[0], a5.inputs[0])
    L_.new(a5.outputs[0], mixs.inputs[0])
    L_.new(tr.outputs[0], mixs.inputs[1]); L_.new(sm.outputs[0], mixs.inputs[2])
    L_.new(mixs.outputs[0], out_.inputs[0])
    o.data.materials.append(mm)
    o.visible_shadow = False
    return o
smoke_ribbon((-4.33, 22.0, 3.3), 11.0, 4.2, 0.5, 3.8)

# rifle stack by the first tent door: three rifles leaning together
for k in range(3):
    a = 2 * math.pi * k / 3 + 0.4
    base = (-1.9 + 0.32 * math.cos(a), 5.7 + 0.32 * math.sin(a), 0.0)
    tip = (-1.9, 5.7, 1.15)
    cyl(base, (base[0] * 0.2 + tip[0] * 0.8, base[1] * 0.2 + tip[1] * 0.8, 0.92), 0.012, blackiron, verts=5, name='rifle barrel')
    cyl(base, (base[0] * 0.75 + tip[0] * 0.25, base[1] * 0.75 + tip[1] * 0.25, 0.3), 0.022, planks_dark, verts=5, name='rifle stock')

# ---------------------------------------------------------------- field gun
def gun(loc, rotz):
    P = empty(loc, rotz)
    PARENT[0] = P
    Rw = 0.66
    axz = Rw
    for sx in (-0.78, 0.78):
        # tyre, felloe, hub, spokes (wheel in the y-z plane, axis along x)
        torus((sx, 0, axz), Rw, 0.034, rustiron, rot=(0, math.pi / 2, 0), name='tyre')
        torus((sx, 0, axz), Rw - 0.07, 0.04, wheelwood, rot=(0, math.pi / 2, 0), name='felloe')
        cyl((sx - 0.12, 0, axz), (sx + 0.12, 0, axz), 0.11, wheelwood, verts=10, name='hub')
        for k in range(14):
            a = 2 * math.pi * k / 14
            cyl((sx, 0.1 * math.sin(a), axz + 0.1 * math.cos(a)), (sx, (Rw - 0.07) * math.sin(a), axz + (Rw - 0.07) * math.cos(a)), 0.022, wheelwood, verts=5, name='spoke')
    cyl((-0.85, 0, axz), (0.85, 0, axz), 0.04, blackiron, verts=8, name='axle')
    # shield
    box((0, 0.22, axz + 0.62), (1.0, 0.025, 0.72), gunmetal, rot=(-0.12, 0, 0), name='shield')
    # cradle, barrel
    cyl((0, -0.55, axz + 0.38), (0, 0.95, axz + 0.55), 0.13, gunmetal, verts=12, name='cradle')
    cyl((0, 0.7, axz + 0.52), (0, 2.5, axz + 0.74), 0.075, blackiron, verts=14, r1=0.058, name='barrel')
    cyl((0, 2.45, axz + 0.74), (0, 2.55, axz + 0.75), 0.085, blackiron, verts=14, name='muzzle')
    # trail
    for sx in (-0.13, 0.13):
        cyl((sx, -0.1, axz - 0.1), (sx * 0.5, -3.1, 0.07), 0.07, gunmetal, verts=6, r1=0.055, name='trail')
    box((0, -3.1, 0.07), (0.5, 0.06, 0.3), rustiron, rot=(0.3, 0, 0), name='spade')
    # seat and sight
    box((0.5, -0.1, axz + 0.5), (0.22, 0.2, 0.04), blackiron, name='seat')
    PARENT[0] = None
    return P
gun((2.1, 7.4, 0), math.radians(35))

# shells and boxes beside the gun
for k, (sx, sy) in enumerate([(3.2, 7.2), (3.4, 7.45), (3.0, 7.55), (3.25, 7.2)]):
    PARENT[0] = None
    cyl((sx, sy, 0.02), (sx, sy, 0.62), 0.045, brass, verts=10, name='shellcase')
    cyl((sx, sy, 0.62), (sx, sy, 0.8), 0.045, blackiron, verts=10, r1=0.012, name='shellnose')
box((1.3, 11.0, 0.18), (0.8, 0.4, 0.36), planks, rot=(0, 0, 0.3), name='ammobox')
box((1.35, 11.1, 0.5), (0.7, 0.36, 0.3), planks_dark, rot=(0, 0, 0.1), name='ammobox')
box((3.6, 8.3, 0.17), (0.75, 0.4, 0.34), planks, rot=(0, 0, -0.5), name='ammobox')

# ---------------------------------------------------------------- sandbag wall
def sandbags(x0, y0, n_per, rows, axis_rot, step=0.55, bagsize=(0.34, 0.2, 0.12)):
    for rrow in range(rows):
        for k in range(n_per):
            off = (0.5 * step) if rrow % 2 else 0
            lx = (k * step + off)
            ca, sa = math.cos(axis_rot), math.sin(axis_rot)
            x = x0 + lx * ca
            y = y0 + lx * sa
            z = bagsize[2] * 0.95 + rrow * bagsize[2] * 1.75
            o = sphere((x + random.uniform(-0.03, 0.03), y + random.uniform(-0.03, 0.03), z),
                       (bagsize[0] * random.uniform(0.92, 1.05), bagsize[1], bagsize[2] * random.uniform(0.9, 1.1)),
                       hess, seg=12, rot=(0, 0, axis_rot + random.uniform(-0.1, 0.1)), name='bag')
            smooth(o)
sandbags(-1.45, 13.4, 14, 4, math.radians(90), step=0.52)
# spade stuck in the top
cyl((-1.5, 13.0, 0.5), (-1.45, 13.1, 1.5), 0.02, planks, verts=5, name='spadehandle')
box((-1.5, 13.0, 0.45), (0.02, 0.22, 0.3), rustiron, name='spadeblade')

# ---------------------------------------------------------------- crate, lantern, bucket
box((-0.95, 4.6, 0.2), (0.7, 0.42, 0.4), planks, rot=(0, 0, 0.35), name='crate')
# lantern body: tin base, glowing flame, glass-free glow, hoop
PARENT[0] = None
cyl((-0.95, 4.6, 0.4), (-0.95, 4.6, 0.45), 0.07, blackiron, verts=10, name='lamp_base')
sphere((-0.95, 4.6, 0.53), (0.04, 0.04, 0.08), lampglow, seg=10, name='lamp_flame')
cyl((-0.95, 4.6, 0.62), (-0.95, 4.6, 0.65), 0.07, blackiron, verts=10, name='lamp_cap')
torus((-0.95, 4.6, 0.7), 0.05, 0.006, blackiron, rot=(math.pi / 2, 0, 0.35), name='lamp_hoop')
bpy.ops.object.light_add(type='POINT', location=(-0.9, 4.45, 0.56))
l = bpy.context.object
l.data.energy = 70
l.data.color = (1.0, 0.6, 0.25)
l.data.shadow_soft_size = 0.05
# bucket and mess tin
cyl((-0.2, 4.9, 0.0), (-0.2, 4.9, 0.3), 0.15, tinm, verts=14, r1=0.19, name='bucket')
torus((-0.2, 4.9, 0.3), 0.17, 0.007, blackiron, rot=(math.pi / 2, 0, 0.6), name='bail')
cyl((-0.2, 4.9, 0.29), (-0.2, 4.9, 0.3), 0.16, blackiron, verts=14, name='rim')
cyl((-0.35, 4.0, 0.0), (-0.35, 4.0, 0.04), 0.1, rustiron, verts=12, name='tin')

# a second lamp standing on the ammunition box by the gun
box((1.0, 6.4, 0.14), (0.5, 0.3, 0.28), planks_dark, rot=(0, 0, 0.2), name='lampbox')
cyl((1.0, 6.4, 0.28), (1.0, 6.4, 0.32), 0.06, blackiron, verts=10, name='lamp2_base')
sphere((1.0, 6.4, 0.38), (0.035, 0.035, 0.07), lampglow, seg=10, name='lamp2_flame')
cyl((1.0, 6.4, 0.45), (1.0, 6.4, 0.48), 0.06, blackiron, verts=10, name='lamp2_cap')
bpy.ops.object.light_add(type='POINT', location=(1.0, 6.25, 0.42))
l = bpy.context.object
l.data.energy = 90; l.data.color = (1.0, 0.6, 0.25); l.data.shadow_soft_size = 0.05

# ---------------------------------------------------------------- barbed wire on stakes
def wire_line(p0, p1, nposts, strands=(0.35, 0.7, 1.05), stake_h=1.25, sag=0.05):
    p0 = Vector(p0); p1 = Vector(p1)
    posts = []
    for k in range(nposts):
        t = k / (nposts - 1)
        p = p0.lerp(p1, t)
        jitter = random.uniform(-0.05, 0.05)
        lean = random.uniform(-0.06, 0.06)
        cyl((p.x, p.y, 0.0), (p.x + lean, p.y + jitter, stake_h), 0.04, planks_dark, verts=5, name='stake')
        posts.append((p.x + lean * 0, p.y))
    for z in strands:
        curve = bpy.data.curves.new('w', 'CURVE')
        curve.dimensions = '3D'
        curve.bevel_depth = 0.007
        curve.bevel_resolution = 1
        sp = curve.splines.new('POLY')
        pts = []
        for k in range(nposts - 1):
            a = Vector((posts[k][0], posts[k][1], z * stake_h / 1.05)); b = Vector((posts[k + 1][0], posts[k + 1][1], z * stake_h / 1.05))
            for j in range(6):
                t = j / 6
                pts.append(a.lerp(b, t) + Vector((0, 0, -sag * math.sin(math.pi * t) + 0.01 * random.uniform(-1, 1))))
        pts.append(Vector((posts[-1][0], posts[-1][1], z * stake_h / 1.05)))
        sp.points.add(len(pts) - 1)
        for pnt, v in zip(sp.points, pts):
            pnt.co = (v.x, v.y, v.z, 1)
        o = bpy.data.objects.new('wire', curve)
        scene.collection.objects.link(o)
        o.data.materials.append(wirem)
        # barbs: little cross ticks every 0.25 m on the strand
        for k in range(0, len(pts) - 1, 2):
            v = pts[k]
            bpy.ops.mesh.primitive_cube_add(size=1, location=v)
            bb = bpy.context.object
            bb.scale = (0.03, 0.004, 0.004)
            bb.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))
            bb.data.materials.append(wirem)
wire_line((-1.15, 6.4), (-1.2, 10.2), 4)
wire_line((1.6, 14.5), (1.9, 26), 8, stake_h=1.2)

# concertina coil lying in the left foreground, and spare stakes leaning against the lantern crate
curve = bpy.data.curves.new('coil', 'CURVE')
curve.dimensions = '3D'
curve.bevel_depth = 0.011
sp = curve.splines.new('POLY')
npt = 260
sp.points.add(npt - 1)
for i in range(npt):
    t = i / (npt - 1)
    a_ = t * 2 * math.pi * 12
    sp.points[i].co = (-1.5 + t * 0.95 + 0.02 * math.sin(a_ * 3.1), 2.55 + 0.17 * math.sin(a_) * (1 + 0.15 * math.sin(a_ * 0.7)), 0.19 + 0.16 * math.cos(a_), 1)
o = bpy.data.objects.new('coil', curve)
scene.collection.objects.link(o)
o.data.materials.append(plain('coilwire', (0.07, 0.035, 0.02), rough=0.9, metal=0.0, spec=0.05))
for k in range(4):
    cyl((-1.45 + 0.07 * k, 5.2, 0.0), (-1.2 + 0.07 * k, 4.9, 1.2), 0.03, planks_dark, verts=5, name='spare stake')

# ---------------------------------------------------------------- drums, crates, tower foot, halos
def drum(x, y, h=0.85, r=0.3, rot=0):
    cyl((x, y, 0.0), (x, y, h), r, rustiron, verts=18, name='drum')
    for hz_ in (0.08, h * 0.5, h - 0.08):
        cyl((x, y, hz_ - 0.015), (x, y, hz_ + 0.015), r * 1.03, blackiron, verts=18, name='drumring')
    cyl((x, y, h), (x, y, h + 0.012), r * 0.95, blackiron, verts=18, name='drumtop')
drum(1.9, 15.5); drum(2.3, 16.2, h=0.8)
for (cx, cy, cz, cr) in [(1.7, 11.5, 0.16, 0.2), (1.75, 11.55, 0.46, -0.1), (2.55, 11.3, 0.16, 0.5), (1.1, 18.5, 0.16, 0.1), (1.12, 18.5, 0.46, 0.3)]:
    box((cx, cy, cz), (0.75, 0.42, 0.32), planks if cz < 0.4 else planks_dark, rot=(0, 0, cr), name='crate')
def halo(loc, rad, dens):
    hm, hn = new_mat('halo')
    ho = hn.nodes.new('ShaderNodeOutputMaterial')
    hs_ = hn.nodes.new('ShaderNodeVolumeScatter')
    hs_.inputs['Color'].default_value = (1.0, 0.7, 0.4, 1)
    hs_.inputs['Anisotropy'].default_value = 0.3
    tcx = hn.nodes.new('ShaderNodeTexCoord')
    ln = hn.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
    hn.links.new(tcx.outputs['Object'], ln.inputs[0])
    inv_ = hn.nodes.new('ShaderNodeMath'); inv_.operation = 'SUBTRACT'; inv_.inputs[0].default_value = 1.0
    inv_.use_clamp = True
    hn.links.new(ln.outputs['Value'], inv_.inputs[1])
    pw_ = hn.nodes.new('ShaderNodeMath'); pw_.operation = 'POWER'; pw_.inputs[1].default_value = 3.0
    hn.links.new(inv_.outputs[0], pw_.inputs[0])
    ml_ = hn.nodes.new('ShaderNodeMath'); ml_.operation = 'MULTIPLY'; ml_.inputs[1].default_value = dens
    hn.links.new(pw_.outputs[0], ml_.inputs[0])
    hn.links.new(ml_.outputs[0], hs_.inputs['Density'])
    hn.links.new(hs_.outputs[0], ho.inputs['Volume'])
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=10, radius=rad, location=loc)
    o = bpy.context.object
    o.data.materials.append(hm)
    o.visible_shadow = False
    return o
halo((-0.95, 4.6, 0.55), 1.0, 0.2)
halo((1.0, 6.4, 0.45), 0.7, 0.14)
halo((0.05, 19.4, 10.35), 3.0, 0.12)

# ---------------------------------------------------------------- hills and grass
def ridge(y, amp, width, base_h, mat, seed):
    bm = bmesh.new()
    nx = 90
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6) for _ in range(5)]
    cols = []
    for i in range(nx + 1):
        x = -width + 2 * width * i / nx
        h = base_h + amp * (0.5 * math.sin(x * 0.012 + ph[0]) + 0.3 * math.sin(x * 0.031 + ph[1]) + 0.15 * math.sin(x * 0.07 + ph[2]) + 0.05 * math.sin(x * 0.2 + ph[3]))
        cols.append((bm.verts.new((x, y, -2)), bm.verts.new((x, y, h))))
    for i in range(nx):
        bm.faces.new([cols[i][0], cols[i + 1][0], cols[i + 1][1], cols[i][1]])
    from_bm(bm, 'ridge', mat)
ridge(150, 14, 220, 14, hillm2, 3)
ridge(105, 9, 150, 7, hillm, 11)

blades = bmesh.new()
def tuft(x, y, h):
    for k in range(9):
        a = random.uniform(0, 2 * math.pi)
        lean = random.uniform(0.1, 0.4) * h
        hh = h * random.uniform(0.6, 1.1)
        c, s = math.cos(a), math.sin(a)
        w = 0.008
        v0 = blades.verts.new((x + 0.02 * c - w * s, y + 0.02 * s + w * c, 0))
        v1 = blades.verts.new((x + 0.02 * c + w * s, y + 0.02 * s - w * c, 0))
        v2 = blades.verts.new((x + lean * c * 0.5, y + lean * s * 0.5, hh * 0.6))
        v3 = blades.verts.new((x + lean * c, y + lean * s, hh))
        blades.faces.new([v0, v1, v2])
        blades.faces.new([v1, v2, v3][0:3]) if False else None
        blades.faces.new([v0, v2, v3])
for i in range(520):
    side = random.choice([-1, 1])
    x = side * (random.uniform(0.9, 6.5)) + (0.7 if side > 0 else -0.7)
    y = random.uniform(1.0, 26) ** 1.0
    tuft(x, y, random.uniform(0.2, 0.5))
for i in range(60):
    x = random.uniform(1.5, 2.6) * random.choice([-1, 1]) if random.random() < 0.5 else random.uniform(-7, 7)
    tuft(x, random.uniform(1, 6), random.uniform(0.2, 0.45))
from_bm(blades, 'grass', grass_m)

# ---------------------------------------------------------------- world: sky, glow, haze
w = bpy.data.worlds.new('w')
scene.world = w
w.use_nodes = True
nt = w.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
N, L = nt.nodes, nt.links
tcw = N.new('ShaderNodeTexCoord')
norm = N.new('ShaderNodeVectorMath'); norm.operation = 'NORMALIZE'
L.new(tcw.outputs['Object'], norm.inputs[0])
sep = N.new('ShaderNodeSeparateXYZ')
L.new(norm.outputs[0], sep.inputs[0])
mr = N.new('ShaderNodeMapRange')
mr.inputs[1].default_value = 0.0; mr.inputs[2].default_value = 0.75
mr.clamp = True
L.new(sep.outputs['Z'], mr.inputs[0])
ramp = N.new('ShaderNodeValToRGB')
cr = ramp.color_ramp
cr.elements[0].position = 0.0
cr.elements[0].color = (0.95, 0.42, 0.14, 1)
cr.elements[1].position = 1.0
cr.elements[1].color = (0.008, 0.022, 0.045, 1)
for pos, col in ((0.06, (0.55, 0.30, 0.18, 1)), (0.28, (0.02, 0.24, 0.36, 1)), (0.6, (0.01, 0.09, 0.18, 1))):
    e = cr.elements.new(pos); e.color = col
# the ramp has 5 elements now; index order is by position
L.new(mr.outputs[0], ramp.inputs[0])
SUN = Vector((0.12, 1.0, 0.085)).normalized()
dot = N.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
dot.inputs[1].default_value = SUN
L.new(norm.outputs[0], dot.inputs[0])
cl = N.new('ShaderNodeMath'); cl.operation = 'MAXIMUM'; cl.inputs[1].default_value = 0.0
L.new(dot.outputs['Value'], cl.inputs[0])
p1 = N.new('ShaderNodeMath'); p1.operation = 'POWER'; p1.inputs[1].default_value = 140
p2 = N.new('ShaderNodeMath'); p2.operation = 'POWER'; p2.inputs[1].default_value = 7
L.new(cl.outputs[0], p1.inputs[0]); L.new(cl.outputs[0], p2.inputs[0])
g1 = N.new('ShaderNodeMath'); g1.operation = 'MULTIPLY'; g1.inputs[1].default_value = 5.0
g2 = N.new('ShaderNodeMath'); g2.operation = 'MULTIPLY'; g2.inputs[1].default_value = 0.4
L.new(p1.outputs[0], g1.inputs[0]); L.new(p2.outputs[0], g2.inputs[0])
gs = N.new('ShaderNodeMath'); gs.operation = 'ADD'
L.new(g1.outputs[0], gs.inputs[0]); L.new(g2.outputs[0], gs.inputs[1])
gcol = N.new('ShaderNodeMix'); gcol.data_type = 'RGBA'; gcol.blend_type = 'MULTIPLY'
gcol.inputs[0].default_value = 1.0
gcol.inputs[6].default_value = (1.0, 0.55, 0.2, 1)
L.new(gs.outputs[0], gcol.inputs[7])
add = N.new('ShaderNodeMix'); add.data_type = 'RGBA'; add.blend_type = 'ADD'; add.inputs[0].default_value = 1.0
L.new(ramp.outputs[0], add.inputs[6]); L.new(gcol.outputs[2], add.inputs[7])
# cloud band: stretched noise darkens and warms streaks near the horizon
nzs = N.new('ShaderNodeTexNoise')
nzs.inputs['Scale'].default_value = 3.0; nzs.inputs['Detail'].default_value = 6; nzs.inputs['Roughness'].default_value = 0.6
mp_ = N.new('ShaderNodeMapping')
mp_.inputs['Scale'].default_value = (1.0, 1.0, 4.5)
L.new(norm.outputs[0], mp_.inputs[0]); L.new(mp_.outputs[0], nzs.inputs['Vector'])
cramp = N.new('ShaderNodeValToRGB')
cramp.color_ramp.elements[0].position = 0.34; cramp.color_ramp.elements[0].color = (0.30, 0.42, 0.60, 1)
cramp.color_ramp.elements[1].position = 0.64; cramp.color_ramp.elements[1].color = (1.3, 1.0, 0.8, 1)
L.new(nzs.outputs['Fac'], cramp.inputs[0])
cm = N.new('ShaderNodeMix'); cm.data_type = 'RGBA'; cm.blend_type = 'MULTIPLY'; cm.inputs[0].default_value = 1.0
L.new(add.outputs[2], cm.inputs[6]); L.new(cramp.outputs[0], cm.inputs[7])
bg = N.new('ShaderNodeBackground'); bg.inputs['Strength'].default_value = 1.0
lpn = N.new('ShaderNodeLightPath')
lpm = N.new('ShaderNodeMath'); lpm.operation = 'MULTIPLY_ADD'
lpm.inputs[1].default_value = SKY_CAM; lpm.inputs[2].default_value = SKY_LIGHT
L.new(lpn.outputs['Is Camera Ray'], lpm.inputs[0])
L.new(lpm.outputs[0], bg.inputs['Strength'])
amb = N.new('ShaderNodeMix'); amb.data_type = 'RGBA'; amb.blend_type = 'MIX'
amb.inputs[6].default_value = (0.10, 0.24, 0.40, 1)
L.new(lpn.outputs['Is Camera Ray'], amb.inputs[0])
L.new(cm.outputs[2], amb.inputs[7])
L.new(amb.outputs[2], bg.inputs['Color'])
wo = N.new('ShaderNodeOutputWorld')
L.new(bg.outputs[0], wo.inputs['Surface'])
# thin haze: a big box of scatter that thins with height (a world-wide volume swallows the sky)
hz_m, hnt = new_mat('haze')
hN, hL = hnt.nodes, hnt.links
hout = hN.new('ShaderNodeOutputMaterial')
hs = hN.new('ShaderNodeVolumeScatter')
hs.inputs['Color'].default_value = (0.6, 0.72, 0.9, 1)
hs.inputs['Anisotropy'].default_value = 0.5
hp = hN.new('ShaderNodeNewGeometry')
hsep = hN.new('ShaderNodeSeparateXYZ')
hL.new(hp.outputs['Position'], hsep.inputs[0])
hm1 = hN.new('ShaderNodeMath'); hm1.operation = 'MULTIPLY'; hm1.inputs[1].default_value = -1.0 / HAZE_H
hL.new(hsep.outputs['Z'], hm1.inputs[0])
hm2 = hN.new('ShaderNodeMath'); hm2.operation = 'EXPONENT'
hL.new(hm1.outputs[0], hm2.inputs[0])
hm3 = hN.new('ShaderNodeMath'); hm3.operation = 'MULTIPLY'; hm3.inputs[1].default_value = HAZE_D
hL.new(hm2.outputs[0], hm3.inputs[0])
hL.new(hm3.outputs[0], hs.inputs['Density'])
hL.new(hs.outputs[0], hout.inputs['Volume'])
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 85, 28))
hz = bpy.context.object
hz.scale = (500, 400, 60)
hz.name = 'haze'
hz.data.materials.append(hz_m)
hz.visible_shadow = False

# the low sun behind the tower, raking across the camp
bpy.ops.object.light_add(type='SUN')
sun = bpy.context.object
sun.data.energy = 2.2
sun.data.color = (1.0, 0.58, 0.25)
sun.data.angle = math.radians(2.0)
sun.rotation_euler = (-SUN).to_track_quat('-Z', 'Y').to_euler()
# a cool fill from the zenith side so shadows are blue-black and not empty
bpy.ops.object.light_add(type='SUN')
fill = bpy.context.object
fill.data.energy = 0.10
fill.data.color = (0.45, 0.6, 0.9)
fill.rotation_euler = (math.radians(35), 0, math.radians(200))


# ================================================================ DRESSING (second pass): what the people left, each where its owner put it
leather = plain('leather', (0.022, 0.014, 0.009), rough=0.7, spec=0.15)
oilskin = plain('oilskin', (0.016, 0.018, 0.022), rough=0.30, spec=0.6)
tarp = surf('tarp', 'rough_linen', 0.27, tint=(0.7, 0.68, 0.58), dark=0.55, rough=1.0, bump=0.5, grime=0.7, patch=0.5, fine=0.3, wfoot=0.3)
cap_m = plain('capwool', (0.022, 0.02, 0.012), rough=1.0, spec=0.0)
rustst2 = plain('rustrun', (0.17, 0.065, 0.025), rough=0.7)
mugm = plain('enamelmug', (0.045, 0.05, 0.055), rough=0.5, metal=0.2)
tobtin = plain('tobtin', (0.20, 0.13, 0.05), rough=0.4, metal=0.7)

def child_empty(parent, loc, rot):
    e = bpy.data.objects.new('grp', None)
    scene.collection.objects.link(e)
    e.location = loc; e.rotation_euler = rot
    e.parent = parent
    return e

# --- lantern crate (-0.95, 4.6, top at 0.4, turned 0.35): the man who sat here had his tea
CR = empty((-0.95, 4.6, 0.4), 0.35)
PARENT[0] = CR
cyl((-0.23, -0.02, 0.0), (-0.23, -0.02, 0.09), 0.042, mugm, verts=14, r1=0.037, name='mug')
torus((-0.185, -0.02, 0.05), 0.026, 0.005, mugm, rot=(math.pi / 2, 0, 0), name='mughandle')
box((-0.13, 0.11, 0.012), (0.10, 0.065, 0.024), tobtin, rot=(0, 0, 0.5), name='tobaccotin')
o = sphere((0.22, -0.09, 0.03), (0.095, 0.085, 0.032), cap_m, seg=12, rot=(0, 0, 0.7), name='softcap'); smooth(o)
box((0.255, -0.12, 0.05), (0.07, 0.06, 0.006), cap_m, rot=(0, 0, 0.9), name='capPeak')
PARENT[0] = None

# --- boots at the foot of the crate: taken off, left toes to the tent
def boot(loc, rotz, tilt=0.0):
    P = empty(loc, rotz)
    P.rotation_euler = (0, tilt, rotz)
    PARENT[0] = P
    box((0, 0, 0.018), (0.10, 0.285, 0.036), blackiron, name='sole')
    box((0, -0.095, 0.0), (0.085, 0.07, 0.03), blackiron, name='heel')
    cyl((0, -0.06, 0.03), (0, -0.075, 0.27), 0.052, leather, verts=10, r1=0.058, name='shaft')
    cyl((0, -0.075, 0.268), (0, -0.075, 0.272), 0.05, dark_in, verts=10, name='bootMouth')
    o_ = sphere((0, 0.07, 0.06), (0.052, 0.105, 0.048), leather, seg=10, name='toecap'); smooth(o_)
    sphere((0, 0.01, 0.012), (0.075, 0.15, 0.018), mudblob, seg=8, name='soleMud')
    sphere((0, -0.07, 0.07), (0.07, 0.07, 0.07), mudblob, seg=8, name='bootMud')
    PARENT[0] = None
boot((-1.38, 4.12, 0.0), 1.35 + 0.5)
boot((-1.18, 3.98, 0.056), 1.1, tilt=1.47)

# --- wire party's mallet, put down by the coil mid-job
PARENT[0] = None
M = empty((-1.0, 3.3, 0.0), 2.7)
PARENT[0] = M
box((0, 0, 0.075), (0.19, 0.11, 0.11), planks, name='malletHead')
cyl((0.08, 0, 0.055), (0.62, 0.0, 0.035), 0.021, planks_dark, verts=6, name='malletHandle')
cyl((-0.10, 0, 0.075), (-0.095, 0, 0.075), 0.001, blackiron, verts=4, name='x')
box((0.0, 0.0, 0.14), (0.20, 0.02, 0.016), blackiron, name='malletBand')
PARENT[0] = None

# --- digging party's pick, leaning on the sandbag wall's end next to the spade
cyl((-1.12, 12.55, 0.0), (-1.38, 13.1, 0.98), 0.022, planks_dark, verts=6, name='pickHandle')
PK = empty((-1.385, 13.1, 0.98), 0.55)
PARENT[0] = PK
box((0, 0, 0), (0.46, 0.03, 0.035), blackiron, rot=(0, 0.12, 0), name='pickHead')
PARENT[0] = None
sphere((-1.15, 12.7, 0.06), (0.33, 0.25, 0.07), mudblob, seg=8, name='spoil')

# --- gun crew: tarpaulin tied over the stacked ammunition boxes, canvas cover tied on the muzzle, rammer on the ground
TP = empty((1.33, 11.07, 0.0), 0.2)
PARENT[0] = TP
box((0, 0, 0.675), (0.88, 0.52, 0.035), tarp, rot=(0, 0.03, 0), name='tarpTop')
box((0, -0.265, 0.5), (0.88, 0.03, 0.34), tarp, rot=(0.12, 0, 0), name='tarpFront')
box((-0.45, 0, 0.5), (0.03, 0.52, 0.34), tarp, rot=(0, -0.1, 0), name='tarpSide')
box((0.45, 0, 0.5), (0.03, 0.52, 0.34), tarp, rot=(0, 0.1, 0), name='tarpSide')
box((-0.17, 0, 0.7), (0.025, 0.56, 0.03), rope, name='tarpRope')
box((0.17, 0, 0.7), (0.025, 0.56, 0.03), rope, name='tarpRope')
PARENT[0] = None
GP = empty((2.1, 7.4, 0.0), math.radians(35))
PARENT[0] = GP
axz_ = 0.66
cyl((0, 2.42, axz_ + 0.735), (0, 2.62, axz_ + 0.752), 0.1, tarp, verts=14, name='muzzleCover')
cyl((0, 2.45, axz_ + 0.735), (0, 2.45 + 0.0, axz_ + 0.735 - 0.001), 0.001, rope, verts=4, name='x')
torus((0, 2.44, axz_ + 0.735), 0.1, 0.008, rope, rot=(math.pi / 2 + 0.07, 0, 0), name='muzzleTie')
# rammer staff lying beside the trail
cyl((0.62, -0.5, 0.045), (0.5, -2.7, 0.04), 0.022, planks, verts=6, name='rammer')
cyl((0.5, -2.7, 0.045), (0.49, -2.88, 0.045), 0.05, blackiron, verts=10, name='rammerHead')
# mud clinging to the wheels where they sat in the ruts
for sx in (-0.78, 0.78):
    for (oy, sc) in ((0.0, 0.26), (0.34, 0.16), (-0.36, 0.2)):
        o_ = sphere((sx, oy, 0.045), (0.07, sc, 0.075), mudblob, seg=10, name='wheelMud'); smooth(o_)
# shield: rivets, with a rust run under each (water runs down from the rivet)
SH = child_empty(GP, (0, 0.22, axz_ + 0.62), (-0.12, 0, 0))
PARENT[0] = SH
for k in range(7):
    bx = -0.42 + k * 0.14
    for fy in (-1, 1):
        sphere((bx, fy * 0.016, 0.30), (0.03, 0.014, 0.03), blackiron, seg=8, name='rivet')
        hh = DR.uniform(0.09, 0.27)
        box((bx, fy * 0.0135, 0.30 - hh / 2 - 0.01), (DR.uniform(0.025, 0.04), 0.003, hh), rustst2, name='rustRun')
box((0.18, -0.0135, -0.12), (0.2, 0.003, 0.16), rustst2, name='rustPatch')
PARENT[0] = None

# --- guardroom: the cook's rain barrel under the roof edge
BR = empty((-1.7, 20.45, 0.0), 0.0)
PARENT[0] = BR
cyl((0, 0, 0.0), (0, 0, 0.85), 0.3, planks_dark, verts=18, r1=0.27, name='barrel')
for hz_ in (0.08, 0.3, 0.55, 0.77):
    cyl((0, 0, hz_ - 0.012), (0, 0, hz_ + 0.012), 0.285 + 0.035 * (1 - abs(hz_ - 0.42) * 0.3), blackiron, verts=18, name='hoop')
cyl((0, 0, 0.83), (0, 0, 0.845), 0.26, water, verts=18, name='barrelWater')
PARENT[0] = None

# --- track party's spare duckboard lengths stacked beside the track
for k, (px, py, pr, pz) in enumerate([(1.95, 4.5, 0.25, 0.02), (1.98, 4.45, 0.2, 0.062), (1.9, 4.55, 0.32, 0.104)]):
    box((px, py, pz), (1.05, 0.22, 0.036), planks_dark if k != 1 else planks, rot=(0, 0, pr), name='spareBoard')
box((1.95, 4.5, 0.0), (0.12, 0.5, 0.02), planks_dark, rot=(0, 0, 0.25), name='spareBearer')

# --- gun crew's open ammunition crate beside the lamp box: the lid propped, shell noses showing
AC = empty((2.35, 5.45, 0.0), -0.3)
PARENT[0] = AC
box((0, 0, 0.17), (0.75, 0.40, 0.34), planks, name='openCrate')
for k in range(3):
    cyl((-0.22 + 0.22 * k, 0.0, 0.2), (-0.22 + 0.22 * k, 0.0, 0.5), 0.05, brass, verts=10, name='shellInCrate')
    cyl((-0.22 + 0.22 * k, 0.0, 0.5), (-0.22 + 0.22 * k, 0.0, 0.62), 0.05, blackiron, verts=10, r1=0.014, name='shellNose')
box((0.0, 0.31, 0.3), (0.75, 0.03, 0.34), planks_dark, rot=(-0.35, 0, 0), name='crateLid')
PARENT[0] = None


# ---------------------------------------------------------------- camera
cam_d = bpy.data.cameras.new('cam')
cam_d.lens = 26
cam_d.sensor_width = 24
cam_d.sensor_fit = 'HORIZONTAL'
cam_d.shift_y = -0.11
cam = bpy.data.objects.new('cam', cam_d)
scene.collection.objects.link(cam)
cam.location = (0.05, 0.0, 1.55)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam

if os.environ.get('KILL'):
    kinds = os.environ['KILL'].split(',')
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT' and (o.data.type in kinds):
            bpy.data.objects.remove(o)
    if 'WORLD' in kinds:
        bg.inputs['Strength'].default_value = 0.0
# ---------------------------------------------------------------- render settings
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = SAMPLES
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.volume_bounces = 1
scene.cycles.volume_step_rate = 1.5
scene.cycles.sample_clamp_indirect = 6
scene.render.resolution_x = W
scene.render.resolution_y = H
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast' if 'AgX - Medium High Contrast' in [i.identifier for i in scene.view_settings.bl_rna.properties['look'].enum_items] else 'None'
scene.view_settings.exposure = float(os.environ.get('EXPO', '0.0'))
RAW = os.environ.get('RAW', '/tmp/raw_render.png')
scene.render.filepath = RAW
scene.render.image_settings.file_format = 'PNG'
bpy.ops.render.render(write_still=True)

# ---------------------------------------------------------------- finishing: brush softening, bloom, vignette, grade, grain
import numpy as np, cv2
raw = cv2.imread(RAW)
k = raw.shape[1] / 540.0
a = cv2.bilateralFilter(raw, 0, 15, 2.5 * k)
a = cv2.bilateralFilter(a, 0, 11, 1.5 * k)
rng = np.random.default_rng(5)
n = rng.normal(0, 1, a.shape[:2]).astype(np.float32)
n = cv2.GaussianBlur(n, (0, 0), 1.6 * k)
n = n / (n.std() + 1e-6)
sky = cv2.bilateralFilter(a, 0, 55, 14.0 * k)
sky = cv2.bilateralFilter(sky, 0, 45, 10.0 * k)
mask = np.clip(1.0 - (np.mgrid[0:a.shape[0], 0:a.shape[1]][0] / a.shape[0] - 0.30) / 0.22, 0, 1).astype(np.float32)[..., None]
a = (a.astype(np.float32) * (1 - 0.85 * mask) + sky.astype(np.float32) * 0.85 * mask).astype(np.uint8)
a = np.clip(a.astype(np.float32) * (1 + 0.015 * n[..., None]), 0, 255)
bl = cv2.GaussianBlur(a, (0, 0), 1.2 * k)
a = np.clip(a + 0.55 * (a - bl), 0, 255) / 255.0
# bloom from the brightest lights only
lum = a.max(axis=2)
hi = np.clip((lum - 0.6) / 0.4, 0, 1)[..., None] * a
b1 = cv2.GaussianBlur(hi, (0, 0), 4.0 * k)
b2 = cv2.GaussianBlur(hi, (0, 0), 14.0 * k)
a = a + 0.30 * b1 + 0.24 * b2
yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
dx = (xx / a.shape[1] - 0.5) * 2
dy = (yy / a.shape[0] - 0.5) * 2
vig = 1 - 0.30 * np.clip((dx ** 2 * 0.8 + dy ** 2 * 0.6), 0, 1.4)
a = a * vig[..., None]
# cool the shadows (BGR order: raise blue, lower red), warm the lights a touch
l2 = a.mean(axis=2, keepdims=True)
shadow = np.clip(1 - l2 * 3.5, 0, 1)
a = a * (1 + shadow * np.array([0.10, 0.0, -0.08], dtype=np.float32))
light = np.clip((l2 - 0.45) / 0.4, 0, 1)
a = a * (1 + light * np.array([-0.04, 0.0, 0.05], dtype=np.float32))
a = a + rng.normal(0, 0.006, a.shape[:2])[..., None]
a = np.clip(a, 0, 1)
cv2.imwrite(OUT, (a * 255 + 0.5).astype(np.uint8))
print('wrote', OUT)
