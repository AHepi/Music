import bpy, math
from lib import *
from mathutils import Vector

SUN_ELEV = math.radians(10.0)
SUN_AZ = math.radians(308.0)   # compass azimuth, clockwise from +Y

def sun_vec():
    # direction towards the sun
    return Vector((math.sin(SUN_AZ) * math.cos(SUN_ELEV), math.cos(SUN_AZ) * math.cos(SUN_ELEV), math.sin(SUN_ELEV)))

def build_world(sky_rot_offset=0.0, haze=0.0012, strength=1.0):
    w = bpy.data.worlds.new('sky'); w.use_nodes = True
    bpy.context.scene.world = w
    nb = NB(w)
    sky = nb.n('ShaderWorldTexNodeSky') if False else nb.n('ShaderNodeTexSky')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_elevation = SUN_ELEV
    sky.sun_rotation = SUN_AZ + sky_rot_offset
    sky.sun_disc = False
    sky.air_density = 1.4; sky.aerosol_density = 0.4; sky.ozone_density = 1.0
    sky.altitude = 0
    # direction based cloud layer
    tc = nb.n('ShaderNodeTexCoord')
    dirv = tc.outputs['Generated'] if False else tc.outputs['Window']
    geo = nb.n('ShaderNodeNewGeometry')
    d = geo.outputs['Incoming']   # points from the surface to the camera => view direction reversed
    sx, sy, sz = nb.sep(d)
    # sky direction = -incoming
    dx = nb.math('MULTIPLY', sx, -1.0); dy = nb.math('MULTIPLY', sy, -1.0); dz = nb.math('MULTIPLY', sz, -1.0)
    den = nb.math('MAXIMUM', nb.math('ADD', dz, 0.12), 0.06)
    px = nb.math('DIVIDE', dx, den); py = nb.math('DIVIDE', dy, den)
    comb = nb.n('ShaderNodeCombineXYZ'); nb.link(px, comb.inputs[0]); nb.link(py, comb.inputs[1])
    sv = sun_vec()
    # sun direction in the same projected plane
    spx = sv.x / (sv.z + 0.12); spy = sv.y / (sv.z + 0.12)
    n1 = nb.noise(nb.mapping(comb.outputs[0], (1.1, 1.9, 1), (5, 0, 0)), 1.8, 7, 0.58, distort=0.45)
    off = nb.n('ShaderNodeVectorMath'); off.operation = 'ADD'
    nb.link(comb.outputs[0], off.inputs[0]); off.inputs[1].default_value = (-0.10 * spx, -0.10 * spy, 0)
    n2 = nb.noise(nb.mapping(off.outputs[0], (1.1, 1.9, 1), (5, 0, 0)), 1.8, 7, 0.58, distort=0.45)
    cov = nb.ramp(n1.outputs['Fac'], [(0.50, (0, 0, 0)), (0.66, (1, 1, 1))])
    # fade clouds toward the horizon so haze takes over, and thin them overhead
    hor = nb.math('MULTIPLY', nb.math('DIVIDE', dz, 0.22, clamp=True), 1.0)
    covm = nb.math('MULTIPLY', cov.outputs[0], hor)
    shade = nb.math('ADD', nb.math('MULTIPLY', nb.math('SUBTRACT', n1.outputs['Fac'], n2.outputs['Fac']), 6.0), 0.55, clamp=True)
    ccol = nb.mix(shade, (0.10, 0.12, 0.20, 1), (1.6, 1.05, 0.72, 1))
    # high thin streaks
    n3 = nb.noise(nb.mapping(comb.outputs[0], (0.5, 4.0, 1), (11, 3, 0)), 2.5, 5, 0.6, distort=0.3)
    cir = nb.ramp(n3.outputs['Fac'], [(0.5, (0, 0, 0)), (0.75, (0.35, 0.35, 0.35))])
    cir2 = nb.math('MULTIPLY', cir.outputs[0], nb.math('DIVIDE', dz, 0.3, clamp=True))
    tint = nb.ramp(nb.math('DIVIDE', dz, 0.85, clamp=True), [(0.0, (1, 1, 1)), (0.3, (0.82, 0.92, 1.1)), (1.0, (0.42, 0.68, 1.3))])
    tm = nb.n('ShaderNodeMix'); tm.data_type = 'RGBA'; tm.blend_type = 'MULTIPLY'; tm.inputs[0].default_value = 1.0
    nb.link(sky.outputs[0], tm.inputs[6]); nb.link(tint.outputs[0], tm.inputs[7])
    skyc = nb.mix(covm, tm.outputs[2], ccol)
    skyc = nb.mix(cir2, skyc, (1.2, 0.8, 0.65, 1))
    bg = nb.n('ShaderNodeBackground'); nb.link(skyc, bg.inputs['Color']); bg.inputs['Strength'].default_value = strength
    out = nb.n('ShaderNodeOutputWorld'); nb.link(bg.outputs[0], out.inputs['Surface'])
    if haze > 0:
        m = new_mat('haze'); nb2 = NB(m)
        vs = nb2.n('ShaderNodeVolumeScatter'); vs.inputs['Density'].default_value = haze
        vs.inputs['Color'].default_value = (0.80, 0.90, 1.0, 1); vs.inputs['Anisotropy'].default_value = 0.45
        o = nb2.n('ShaderNodeOutputMaterial'); nb2.link(vs.outputs[0], o.inputs['Volume'])
        hb = box('haze_box', (6000, 5200, 420), (0, 2200, 195), m)
        hb.visible_shadow = False
    # sun lamp with the same direction
    ld = bpy.data.lights.new('sun', 'SUN'); ld.energy = 5.0; ld.angle = math.radians(0.6)
    ld.color = (1.0, 0.62, 0.36)
    lo = bpy.data.objects.new('sun', ld); bpy.context.scene.collection.objects.link(lo)
    # sun light shines along -sun_vec ; align -Z of light to -sv
    q = (-sv).to_track_quat('-Z', 'Y')
    lo.rotation_euler = q.to_euler()
    return w, lo
