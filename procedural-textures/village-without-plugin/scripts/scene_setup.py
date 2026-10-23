"""World, sun, render settings and cameras."""
import math
import numpy as np
import bpy
from mathutils import Vector
from common import *

def sun_az_of(sky):
    d = sky.sun_direction
    return math.degrees(math.atan2(d[0], d[1])) % 360.0

def setup_world(sun_az=222.0, sun_el=31.0, sun_size_deg=0.9, strength=1.3, haze=0.0, sun_int=0.55, clouds=0.0):
    sc = bpy.context.scene
    w = bpy.data.worlds.get('Village World') or bpy.data.worlds.new('Village World')
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    sky.sun_disc = True
    sky.sun_size = math.radians(sun_size_deg)
    sky.sun_intensity = sun_int
    sky.sun_elevation = math.radians(sun_el)
    sky.air_density = 1.0
    sky.aerosol_density = 1.0
    sky.ozone_density = 1.0
    sky.altitude = 0.0
    sky.sun_rotation = math.radians(sun_az)   # verified with a mirror ball: rotation == compass azimuth of the sun
    bg.inputs['Strength'].default_value = strength
    nt.links.new(sky.outputs['Color'], bg.inputs['Color'])
    surf = bg.outputs['Background']
    if clouds > 0:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
        den = nt.nodes.new('ShaderNodeMath'); den.operation = 'MAXIMUM'
        add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'; add.inputs[1].default_value = 0.22
        nt.links.new(sep.outputs['Z'], add.inputs[0])
        nt.links.new(add.outputs[0], den.inputs[0]); den.inputs[1].default_value = 0.08
        dx = nt.nodes.new('ShaderNodeMath'); dx.operation = 'DIVIDE'
        dy = nt.nodes.new('ShaderNodeMath'); dy.operation = 'DIVIDE'
        nt.links.new(sep.outputs['X'], dx.inputs[0]); nt.links.new(den.outputs[0], dx.inputs[1])
        nt.links.new(sep.outputs['Y'], dy.inputs[0]); nt.links.new(den.outputs[0], dy.inputs[1])
        comb = nt.nodes.new('ShaderNodeCombineXYZ')
        nt.links.new(dx.outputs[0], comb.inputs['X']); nt.links.new(dy.outputs[0], comb.inputs['Y'])
        nz = nt.nodes.new('ShaderNodeTexNoise'); nz.noise_dimensions = '3D'; nz.normalize = True
        nz.inputs['Scale'].default_value = 1.1; nz.inputs['Detail'].default_value = 6.0; nz.inputs['Roughness'].default_value = 0.58
        nz.inputs['Distortion'].default_value = 0.35
        nt.links.new(comb.outputs[0], nz.inputs['Vector'])
        mr = nt.nodes.new('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP'
        mr.inputs['From Min'].default_value = 0.47; mr.inputs['From Max'].default_value = 0.70
        nt.links.new(nz.outputs['Factor'], mr.inputs['Value'])
        fd = nt.nodes.new('ShaderNodeMapRange'); fd.interpolation_type = 'SMOOTHSTEP'
        fd.inputs['From Min'].default_value = 0.0; fd.inputs['From Max'].default_value = 0.28
        nt.links.new(sep.outputs['Z'], fd.inputs['Value'])
        mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
        nt.links.new(mr.outputs[0], mul.inputs[0]); nt.links.new(fd.outputs[0], mul.inputs[1])
        cb = nt.nodes.new('ShaderNodeBackground')
        cb.inputs['Color'].default_value = (0.92, 0.93, 0.95, 1.0)
        sm = nt.nodes.new('ShaderNodeMath'); sm.operation = 'MULTIPLY'; sm.inputs[1].default_value = clouds
        nt.links.new(mul.outputs[0], sm.inputs[0])
        nt.links.new(sm.outputs[0], cb.inputs['Strength'])
        ad = nt.nodes.new('ShaderNodeAddShader')
        nt.links.new(bg.outputs['Background'], ad.inputs[0]); nt.links.new(cb.outputs['Background'], ad.inputs[1])
        surf = ad.outputs[0]
    nt.links.new(surf, out.inputs['Surface'])
    if haze > 0:
        vol = nt.nodes.new('ShaderNodeVolumePrincipled')
        vol.inputs['Density'].default_value = haze
        vol.inputs['Color'].default_value = (0.82, 0.88, 0.97, 1.0)
        vol.inputs['Anisotropy'].default_value = 0.4
        nt.links.new(vol.outputs['Volume'], out.inputs['Volume'])
    return {'az': sun_az, 'el': sun_el}

def setup_render(w=1200, h=800, samples=128, exposure=0.0, look='None'):
    sc = bpy.context.scene
    r = sc.render
    r.engine = 'CYCLES'
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    cy = sc.cycles
    cy.device = 'CPU'
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.02
    cy.use_denoising = True
    cy.denoiser = 'OPENIMAGEDENOISE'
    cy.max_bounces = 6
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 3
    cy.transmission_bounces = 4
    cy.transparent_max_bounces = 6
    cy.volume_bounces = 0
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.sample_clamp_indirect = 8.0
    cy.sample_clamp_direct = 0.0
    cy.film_exposure = 1.0
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = look
    except Exception:
        pass
    sc.view_settings.exposure = exposure
    sc.view_settings.gamma = 1.0
    sc.display_settings.display_device = 'sRGB'
    r.film_transparent = False
    r.image_settings.file_format = 'JPEG'
    r.image_settings.quality = 94
    r.threads_mode = 'AUTO'

def make_camera(name, loc, target, lens=35.0, fstop=None, focus_target=None, roll=0.0, coll=None, sensor=36.0, clip=(0.05, 3000.0), shift_y=0.0):
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.sensor_fit = 'HORIZONTAL'
    cd.clip_start, cd.clip_end = clip
    cd.shift_y = shift_y
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, cd)
        (coll or get_coll('Cameras')).objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    q = d.to_track_quat('-Z', 'Y')
    ob.rotation_euler = q.to_euler()
    if roll:
        ob.rotation_euler.rotate_axis('Z', roll) if False else None
    if fstop is not None:
        cd.dof.use_dof = True
        cd.dof.aperture_fstop = fstop
        ft = Vector(focus_target) if focus_target is not None else Vector(target)
        cd.dof.focus_distance = (ft - Vector(loc)).length
    else:
        cd.dof.use_dof = False
    return ob


def add_stable_lights(stable, l2w):
    """Hidden warm area lights under the loft floor so the empty stalls read in the picture."""
    coll = get_coll('Lights')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    L = stable['W']
    for i in range(4):
        lx = -L / 2 + 0.14 + (i + 0.5) * (L - 0.28) / 4
        wx, wy = l2w(stable, lx, 0.6)
        ld = bpy.data.lights.new('StallFill%d' % i, 'AREA')
        ld.shape = 'RECTANGLE'
        ld.size, ld.size_y = 2.0, 2.4
        ld.energy = 55.0
        ld.color = (1.0, 0.82, 0.6)
        ob = bpy.data.objects.new('StallFill%d' % i, ld)
        coll.objects.link(ob)
        ob.location = (wx, wy, stable['pad_z'] + 2.45)
        ob.visible_camera = False
        ob.visible_glossy = False
    return 4


def add_haze_box(density=0.0035, height_scale=45.0, half=330.0, top=320.0, bottom=-30.0):
    """Finite haze volume (a world volume turns the whole render black in this setup). Density falls off with height."""
    coll = get_coll('Atmosphere')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.name == 'HazeBox_mesh':
            bpy.data.meshes.remove(me)
    mb = MB()
    mb.box((18.0, 8.0, (top + bottom) / 2), (2 * half, 2 * half, top - bottom), None, 0, smooth=False)
    m = MatB('Haze')
    pz = m.sepxyz(m.position())[2]
    dens = m.math('MULTIPLY', m.math('EXPONENT', m.math('MULTIPLY', pz, -1.0 / height_scale)), density)
    vs = m.nodes.new('ShaderNodeVolumeScatter')
    m._set(vs.inputs['Density'], dens)
    m._set(vs.inputs['Color'], (0.86, 0.91, 1.0))
    m._set(vs.inputs['Anisotropy'], 0.45)
    m.links.new(vs.outputs[0], m.out.inputs['Volume'])
    me = mb.build('HazeBox_mesh', [m.m])
    ob = bpy.data.objects.new('HazeBox', me)
    coll.objects.link(ob)
    ob.visible_glossy = False
    ob.visible_diffuse = False
    return ob


def smoke_material():
    m = MatB('Smoke')
    g = m.tc().outputs['Generated']
    vec = m.vmath('MULTIPLY', m.vmath('SUBTRACT', g, (0.5, 0.5, 0.5)), (2.0, 2.0, 2.0))
    r = m.vmath('LENGTH', vec, out='Value')
    fall = m.math('POWER', m.maprange(r, 0.0, 1.0, 1.0, 0.0), 1.7)
    P = m.position()
    nz = m.maprange(m.noise(P, 1.7, 5, 0.6, 0.3), 0.30, 0.72, 0.15, 1.0)
    oi = m.nodes.new('ShaderNodeObjectInfo')
    colr = m.sepcol(oi.outputs['Color'])[0]
    dens = m.math('MULTIPLY', m.math('MULTIPLY', fall, nz), m.math('MULTIPLY', colr, 2.2))
    vs = m.nodes.new('ShaderNodeVolumeScatter')
    m._set(vs.inputs['Density'], dens)
    m._set(vs.inputs['Color'], (0.82, 0.82, 0.84))
    m._set(vs.inputs['Anisotropy'], 0.5)
    m.links.new(vs.outputs[0], m.out.inputs['Volume'])
    return m.m

def add_smoke(chimney_tops, seed=31, wind=(0.8, 0.45)):
    """chimney_tops: list of (x, y, z). Builds a plume of overlapping soft volume puffs above each."""
    rng = np.random.RandomState(seed)
    coll = get_coll('Smoke')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    mat = smoke_material()
    # one low-poly sphere mesh shared by all puffs
    me = bpy.data.meshes.get('SmokePuff_mesh')
    if me is None:
        mb = MB()
        prof = [(0.001, -1.0)] + [(math.sin(a), -math.cos(a)) for a in np.linspace(0.3, math.pi - 0.3, 6)] + [(0.001, 1.0)]
        mb.lathe(prof, sides=12, smooth=True)
        me = mb.build('SmokePuff_mesh', [mat])
    n = 0
    for (x, y, z) in chimney_tops:
        for k in range(26):
            t = k / 25.0
            h = 0.3 + 8.5 * t ** 1.05
            rad = 0.28 + 1.6 * t ** 0.9
            lat = (0.9 * t ** 1.6) * 5.5
            px = x + wind[0] * lat + rng.normal(0, 0.12 + 0.25 * t)
            py = y + wind[1] * lat + rng.normal(0, 0.12 + 0.25 * t)
            ob = bpy.data.objects.new('Smoke_%d' % n, me)
            coll.objects.link(ob)
            ob.location = (px, py, z + h)
            ob.scale = (rad, rad, rad * 1.1)
            ob.rotation_euler = (rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3))
            a = 0.55 * (1.0 - t) ** 0.8 + 0.06
            ob.color = (a, a, a, 1.0)
            ob.visible_glossy = False
            ob.visible_diffuse = False
            n += 1
    return n


def smoke_card_material():
    m = MatB('SmokeCard')
    u, v, _ = m.sepxyz(m.uv())
    rnd = m.attr('rnd'); hgt = m.attr('hgt')
    xy = m.combxyz(m.math('MULTIPLY', m.math('SUBTRACT', u, 0.5), 2.0), m.math('MULTIPLY', m.math('SUBTRACT', v, 0.5), 2.0), 0.0)
    r = m.vmath('LENGTH', xy, out='Value')
    soft = m.math('POWER', m.maprange(r, 0.0, 1.0, 1.0, 0.0), 1.6)
    P = m.position()
    nz = m.maprange(m.noise(m.vmath('ADD', P, m.combxyz(m.math('MULTIPLY', rnd, 20.0), 0.0, 0.0)), 1.3, 5, 0.62, 0.3), 0.30, 0.72, 0.1, 1.0)
    a = m.math('MULTIPLY', m.math('MULTIPLY', soft, nz), m.math('MULTIPLY', m.math('ADD', 0.45, m.math('MULTIPLY', rnd, 0.55)), m.maprange(hgt, 0.0, 1.0, 0.75, 0.12)))
    shade = m.maprange(nz, 0.1, 1.0, 0.95, 0.55)
    d = m.principled(m.mixc(shade, (0.45, 0.45, 0.47), (0.9, 0.9, 0.92)), 0.9, spec=0.1)
    t = m.translucent((0.8, 0.8, 0.82))
    surf = m.mixsh(0.4, d.outputs[0], t)
    return m.m, m.finish(m.mixsh(m.math('MULTIPLY', a, 0.38), m.transparent(), surf))

def add_smoke_cards(chimney_tops, seed=31, wind=(0.8, 0.45)):
    """Cheap smoke: crossed soft-alpha cards along a leaning plume (volumes were far too slow in Cycles on this machine)."""
    rng = np.random.RandomState(seed)
    coll = get_coll('Smoke')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.name.startswith('SmokePuff') or me.name.startswith('SmokeCards'):
            bpy.data.meshes.remove(me)
    old = bpy.data.materials.get('Smoke')
    if old is not None:
        bpy.data.materials.remove(old)
    mat = smoke_card_material()[1]
    n_cards = 0
    for k, (x, y, z) in enumerate(chimney_tops):
        mb = MB(); mb.rng = rng
        nn = 16
        for i in range(nn):
            t = i / (nn - 1)
            h = 0.25 + 6.5 * t ** 1.05
            size = 0.28 + 1.25 * t ** 0.9
            lat = (0.9 * t ** 1.6) * 4.0
            cx = wind[0] * lat + rng.normal(0, 0.1 + 0.2 * t)
            cy = wind[1] * lat + rng.normal(0, 0.1 + 0.2 * t)
            c = np.array([cx, cy, h])
            rot = rng.uniform(0, 3.14)
            for ori in range(3):
                if ori == 0:
                    a = np.array([math.cos(rot), math.sin(rot), 0.0]); b = np.array([0.0, 0.0, 1.0])
                elif ori == 1:
                    a = np.array([-math.sin(rot), math.cos(rot), 0.0]); b = np.array([0.0, 0.0, 1.0])
                else:
                    a = np.array([math.cos(rot), math.sin(rot), 0.0]); b = np.array([-math.sin(rot), math.cos(rot), 0.0])
                s_ = size * rng.uniform(0.8, 1.2) * (0.8 if ori == 2 else 1.0)
                P = np.array([c - a * s_ - b * s_, c + a * s_ - b * s_, c + a * s_ + b * s_, c - a * s_ + b * s_])
                uv = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], float)
                mb.quads_hard(P[None], uv[None], 0, False, rnd=rng.rand(), hgt=t)
                n_cards += 1
        me = mb.build('SmokeCards_%d' % k, [mat])
        ob = bpy.data.objects.new('SmokePlume_%d' % k, me)
        coll.objects.link(ob)
        ob.location = (x, y, z)
        ob.visible_glossy = False
        ob.visible_shadow = False
    return n_cards


def set_haze(density):
    m = bpy.data.materials.get('Haze')
    if m is None:
        return False
    for n in m.node_tree.nodes:
        if n.bl_idname == 'ShaderNodeMath' and n.operation == 'MULTIPLY' and abs(n.inputs[1].default_value) < 0.05 and n.inputs[1].default_value > 0:
            n.inputs[1].default_value = density
            return True
    return False
