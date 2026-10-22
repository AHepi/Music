# What this does (plain words): "stage_light" is builder 4 (light, backdrop, camera) of the Japanese garden plan. It works on the ALREADY-OPEN
# courtyard scene (astra-work/out/courtyard_final.blend, possibly after the other three stages) and, in the plan's priority order:
#   1 world   the hard-wired orange wash is replaced by a graded sky (warm peach at the horizon, lilac, then blue above), a warm glow round the sun's
#             real direction (taken from the sun lamp, so sky and lamp agree), and a SEPARATE cooler, dimmer "lighting sky" for the light that falls on things
#             (camera and mirror-like rays see the pretty sky; everything else is lit by the cool one, so shadows turn blue instead of orange)
#   2 hills   "Hills, far / middle / near" are rebuilt as full 360-degree ridges (the old ones only existed behind the hall), two more are added
#             ("Hills, farthest", "Hills, foot"), nearer = darker and cooler, farther = paler and more lilac (their tops take the sky's peach so they fade into it by colour, no blur);
#             the dark slab "Dark plain" becomes a ground that carries on to the horizon in colour steps. Backdrop only: it is seen by the camera and by
#             mirrors (the pond) and does NOT light the garden (so the cool lighting sky stays in charge)
#   3 lights  sun kept in direction (strength 8 -> 12 so the low raking light is clearly the key), cool fill cooler and weaker (3500 -> 2600 W), one warm
#             rim lamp (sun type) linked ONLY to the maple and the hall roof/beams (back-light), one soft cool "roof lift" lamp linked ONLY to the hall roof,
#             lantern turned down (dim in the golden-hour view), hall glow kept
#   4 groups  Cycles light groups sun / rim / sky / fill / hall / lantern / rest on the view layer (the picture can be re-balanced after drawing; see regrade.py)
#   5 finish  Cycles settings (caustics off), compositor: mild bloom (only above about 2.0 = screens and lantern), vignette, no blur
#   6 cameras the hero camera is renamed "photo" (same place and lens), "veranda" is added (3.6, 5.3, 1.55) looking at (-2.5, 0.8, 0.55), 24 mm
# Use (inside Blender, scene already open):  import stage_light; report = stage_light.apply({'look': 'real'})   # or 'painted'
#   later (optional): stage_light.apply_evening({'look': 'real'})    -> blue evening variant with the lantern lit
#   options: look 'real'|'painted'; steps (list from: cameras world hills lights groups finish; default all, in the order given here);
#            sky_look / hills_look ('real'|'painted', default = look: the painted look draws the sky in flat brushed bands and the hills as flat planes);
#            seed (int); exposure (default 0.5, the original's); rim (True); vignette (default 0.55); bloom (default 0.05);
#            sun_energy (12), fill_energy (2600), rim_energy (4.5), roof_energy (5000, 0 = no roof lift), lantern_watts (18), flame_strength (7)
#   Also (only the group NAME, never geometry or colour): every other emitting object is put in light group 'rest' so the groups add up to the picture.
#   Tip: call apply({'steps': ['cameras']}) FIRST if the weathering kit (which looks for a camera called "photo") runs before this stage.
# Rules kept: owns only world, lights, emission materials (screens, lantern, hills), hills, plain, cameras, render settings, view-layer light groups, compositor.
#   Every new object has garden_owner = 'light' and garden_role = 'backdrop', 'light' or 'camera' and sits in collection "G4 light". Nothing owned by another builder is
#   renamed (except the camera, which this stage owns), reshaped or deleted. Metres: x across, y away from the camera, z up. Blender 5.2. Safe to run twice.
import math
import os
import random
import sys
import time

import bmesh
import bpy
from mathutils import Vector

sys.dont_write_bytecode = True
OWNER = 'light'
ALL_STEPS = ['cameras', 'world', 'hills', 'lights', 'groups', 'finish']
LOG = []
CHANGED = []          # names of existing objects / datablocks this stage touched
CREATED = []
RENAMED = {}          # old name -> new name (only the camera)


def say(text):
    LOG.append(text)
    print('[light] ' + text, flush=True)


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def smoothstep(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def mix3(a, b, t):
    return tuple(lerp(a[i], b[i], t) for i in range(3))


def scale3(a, k):
    return tuple(a[i] * (k[i] if isinstance(k, (tuple, list)) else k) for i in range(3))


def collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def tag(ob, role):
    ob['garden_owner'] = OWNER
    ob['garden_role'] = role
    ob['garden_keep_materials'] = 1        # emission / backdrop materials: the surfaces stage must not replace them


def sun_object():
    return bpy.data.objects.get('Golden hour sun')


def sun_vector():
    """Unit vector pointing TOWARD the sun, read from the sun lamp (so sky and lamp always agree)."""
    ob = sun_object()
    if ob is None:
        return Vector((-0.944, -0.244, 0.223)).normalized()
    bpy.context.view_layer.update()
    return -(ob.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()


# ====================================================================================================== palettes
# All colours are linear scene colours. z = sin(elevation) for the sky ramps.
def sky_palette(mode):
    """Visible-sky ramp stops (z, colour) and glow settings per mode: 'golden' (default) or 'evening'."""
    if mode == 'evening':
        return dict(
            vis=[(0.00, (0.30, 0.17, 0.26)), (0.05, (0.20, 0.13, 0.27)), (0.14, (0.09, 0.09, 0.22)), (0.30, (0.045, 0.065, 0.19)),
                 (0.60, (0.02, 0.035, 0.12)), (1.00, (0.008, 0.016, 0.07))],
            light=[(0.00, (0.10, 0.07, 0.10)), (0.15, (0.05, 0.055, 0.12)), (0.50, (0.03, 0.045, 0.11)), (1.00, (0.02, 0.03, 0.09))],
            glow=[((0.9, 0.35, 0.25), 0.0, 0.0), ((1.0, 0.5, 0.3), 0.0, 0.0)],
            ground=(0.02, 0.018, 0.02))
    return dict(
        vis=[(0.00, (1.00, 0.45, 0.15)), (0.06, (0.96, 0.40, 0.15)), (0.16, (0.86, 0.38, 0.21)), (0.27, (0.66, 0.34, 0.33)),
             (0.40, (0.45, 0.34, 0.54)), (0.58, (0.27, 0.33, 0.62)), (0.82, (0.13, 0.23, 0.52)), (1.00, (0.07, 0.15, 0.42))],
        light=[(0.00, (0.44, 0.28, 0.21)), (0.08, (0.31, 0.23, 0.25)), (0.25, (0.21, 0.23, 0.38)), (0.60, (0.13, 0.19, 0.40)),
               (1.00, (0.09, 0.14, 0.36))],
        # glow lobes round the sun: (colour, amplitude, ...) wide soft lobe, hot core
        glow=[((1.0, 0.50, 0.20), 0.50, 0.0), ((1.0, 0.66, 0.36), 1.5, 0.0)],
        ground=(0.075, 0.058, 0.040))


def ramp_eval(stops, z):
    z = clamp(z)
    for i in range(len(stops) - 1):
        z0, c0 = stops[i]
        z1, c1 = stops[i + 1]
        if z <= z1:
            return mix3(c0, c1, (z - z0) / max(1e-6, z1 - z0))
    return stops[-1][1]


def glow_at(cos_gamma, mode='golden'):
    p = sky_palette(mode)['glow']
    w1 = clamp((cos_gamma - 0.55) / 0.45) ** 2
    w2 = clamp((cos_gamma - 0.93) / 0.07) ** 2
    return tuple(p[0][0][i] * p[0][1] * w1 + p[1][0][i] * p[1][1] * w2 for i in range(3))


def sky_color(direction, sunv, mode='golden'):
    """Python twin of the world's visible sky: colour seen in a direction (unit Vector)."""
    pal = sky_palette(mode)
    if direction.z < 0:
        return pal['ground']
    base = ramp_eval(pal['vis'], direction.z)
    g = glow_at(clamp(direction.dot(sunv), -1, 1), mode)
    return tuple(base[i] + g[i] for i in range(3))


# ====================================================================================================== 1 world
def build_world(look='real', mode='golden', seed=7):
    """Rebuild the world 'Golden hour' (kept, same name): camera/mirror rays see the pretty sky V, everything else the cool lighting sky L."""
    sc = bpy.context.scene
    world = sc.world or bpy.data.worlds.new('Golden hour')
    sc.world = world
    try:
        world.use_nodes = True
    except Exception:
        pass
    nt = world.node_tree
    nt.nodes.clear()
    pal = sky_palette(mode)
    sunv = sun_vector()
    N = nt.nodes.new
    out = N('ShaderNodeOutputWorld')
    out.location = (1600, 0)
    bg = N('ShaderNodeBackground')
    bg.location = (1400, 0)
    bg.inputs['Strength'].default_value = 1.0
    tc = N('ShaderNodeTexCoord')
    tc.location = (-1400, 0)
    sep = N('ShaderNodeSeparateXYZ')
    sep.location = (-1200, 200)
    nt.links.new(tc.outputs['Generated'], sep.inputs['Vector'])

    def ramp_node(stops, constant, x, y, label):
        r = N('ShaderNodeValToRGB')
        r.label = label
        r.location = (x, y)
        r.color_ramp.interpolation = 'CONSTANT' if constant else 'LINEAR'
        els = r.color_ramp.elements
        while len(els) < len(stops):
            els.new(0.5)
        for e, (z, c) in zip(els, stops):
            e.position = z
            e.color = (c[0], c[1], c[2], 1.0)
        return r

    painted = (look == 'painted')
    # --- visible sky V: ramp over z = sin(elevation); in the painted look the input is warped a little (brush-edged flat bands)
    zin = sep.outputs['Z']
    if painted:
        nz = N('ShaderNodeTexNoise')
        nz.location = (-1200, -100)
        nz.inputs['Scale'].default_value = 5.0
        nz.inputs['Detail'].default_value = 3.0
        nz.inputs['Roughness'].default_value = 0.55
        try:
            nz.noise_dimensions = '3D'
        except Exception:
            pass
        nt.links.new(tc.outputs['Generated'], nz.inputs['Vector'])
        sub = N('ShaderNodeMath')
        sub.operation = 'SUBTRACT'
        sub.location = (-1000, -100)
        sub.inputs[1].default_value = 0.5
        nt.links.new(nz.outputs['Fac'], sub.inputs[0])
        mul = N('ShaderNodeMath')
        mul.operation = 'MULTIPLY'
        mul.location = (-850, -100)
        mul.inputs[1].default_value = 0.07
        nt.links.new(sub.outputs[0], mul.inputs[0])
        add = N('ShaderNodeMath')
        add.operation = 'ADD'
        add.location = (-700, 100)
        nt.links.new(sep.outputs['Z'], add.inputs[0])
        nt.links.new(mul.outputs[0], add.inputs[1])
        zin = add.outputs[0]
    # painted bands: take about 9 flat bands out of the smooth stops
    vis_stops = pal['vis']
    if painted and mode == 'golden':
        vis_stops = [(0.00, (1.00, 0.45, 0.15)), (0.05, (0.96, 0.41, 0.15)), (0.11, (0.88, 0.38, 0.20)), (0.19, (0.76, 0.36, 0.28)),
                     (0.28, (0.62, 0.34, 0.36)), (0.38, (0.47, 0.34, 0.52)), (0.52, (0.31, 0.34, 0.62)), (0.72, (0.16, 0.26, 0.55)),
                     (0.90, (0.08, 0.17, 0.44))]
    rv = ramp_node(vis_stops, painted, -500, 300, 'Visible sky V (by elevation)')
    nt.links.new(zin, rv.inputs['Fac'])
    rl = ramp_node(pal['light'], False, -500, -300, 'Lighting sky L (cool, by elevation)')
    nt.links.new(sep.outputs['Z'], rl.inputs['Fac'])

    # --- glow round the sun's real direction (cos of the angle between this direction and the sun lamp)
    dot = N('ShaderNodeVectorMath')
    dot.operation = 'DOT_PRODUCT'
    dot.location = (-1000, -450)
    dot.inputs[1].default_value = (sunv.x, sunv.y, sunv.z)
    dot.label = 'cos(angle to sun lamp)'
    nt.links.new(tc.outputs['Generated'], dot.inputs[0])

    def lobe(lo, hi, amp, col, y, quant):
        m = N('ShaderNodeMapRange')
        m.location = (-800, y)
        m.inputs['From Min'].default_value = lo
        m.inputs['From Max'].default_value = hi
        m.inputs['To Min'].default_value = 0.0
        m.inputs['To Max'].default_value = 1.0
        m.clamp = True
        nt.links.new(dot.outputs['Value'], m.inputs['Value'])
        p = N('ShaderNodeMath')
        p.operation = 'POWER'
        p.location = (-620, y)
        p.inputs[1].default_value = 2.0
        nt.links.new(m.outputs['Result'], p.inputs[0])
        src = p.outputs[0]
        if quant:    # painted: the glow is laid in 3 flat steps
            q = N('ShaderNodeValToRGB')
            q.location = (-450, y)
            q.color_ramp.interpolation = 'CONSTANT'
            steps = [(0.0, 0.0), (0.12, 0.35), (0.40, 0.70), (0.75, 1.0)]
            els = q.color_ramp.elements
            while len(els) < len(steps):
                els.new(0.5)
            for e, (pos, val) in zip(els, steps):
                e.position = pos
                e.color = (val, val, val, 1.0)
            nt.links.new(p.outputs[0], q.inputs['Fac'])
            src = q.outputs['Color']
        rgb = N('ShaderNodeRGB')
        rgb.location = (-450, y - 150)
        rgb.outputs[0].default_value = (col[0] * amp, col[1] * amp, col[2] * amp, 1.0)
        mul2 = N('ShaderNodeMix')
        mul2.data_type = 'RGBA'
        mul2.blend_type = 'MULTIPLY'
        mul2.location = (-250, y)
        mul2.inputs['Factor'].default_value = 1.0
        nt.links.new(src, mul2.inputs[6])          # a float into a colour socket is read as grey
        nt.links.new(rgb.outputs[0], mul2.inputs[7])
        return mul2.outputs[2]

    g1 = lobe(0.55, 1.0, pal['glow'][0][1] or 0.0, pal['glow'][0][0], -700, painted)
    g2 = lobe(0.93, 1.0, pal['glow'][1][1] or 0.0, pal['glow'][1][0], -1000, painted)

    def add_rgb(a, b, x, y, fac=1.0):
        m = N('ShaderNodeMix')
        m.data_type = 'RGBA'
        m.blend_type = 'ADD'
        m.location = (x, y)
        m.inputs['Factor'].default_value = fac
        nt.links.new(a, m.inputs[6])
        nt.links.new(b, m.inputs[7])
        return m.outputs[2]

    vglow = add_rgb(g1, g2, 0, -800)
    V = add_rgb(rv.outputs['Color'], vglow, 200, 300)
    # lighting sky gets a little of the warm glow only (so the sun side is a touch warmer, never an orange wash)
    L = add_rgb(rl.outputs['Color'], g1, 200, -300, fac=0.25)

    # --- below the horizon: dim warm earth bounce (never seen, lights the undersides)
    gfac = N('ShaderNodeMapRange')
    gfac.location = (200, 600)
    gfac.inputs['From Min'].default_value = -0.03
    gfac.inputs['From Max'].default_value = 0.0
    gfac.inputs['To Min'].default_value = 1.0
    gfac.inputs['To Max'].default_value = 0.0
    gfac.clamp = True
    nt.links.new(sep.outputs['Z'], gfac.inputs['Value'])
    ground = N('ShaderNodeRGB')
    ground.location = (200, 750)
    ground.outputs[0].default_value = (*pal['ground'], 1.0)

    def mix_rgb(fac_sock, a, b, x, y):
        m = N('ShaderNodeMix')
        m.data_type = 'RGBA'
        m.blend_type = 'MIX'
        m.location = (x, y)
        nt.links.new(fac_sock, m.inputs['Factor'])
        nt.links.new(a, m.inputs[6])
        nt.links.new(b, m.inputs[7])
        return m.outputs[2]

    V2 = mix_rgb(gfac.outputs['Result'], V, ground.outputs[0], 500, 300)
    L2 = mix_rgb(gfac.outputs['Result'], L, ground.outputs[0], 500, -300)

    # --- camera and mirror rays see V; every other ray is lit by L
    lp = N('ShaderNodeLightPath')
    lp.location = (500, 0)
    mx = N('ShaderNodeMath')
    mx.operation = 'MAXIMUM'
    mx.location = (700, 0)
    nt.links.new(lp.outputs['Is Camera Ray'], mx.inputs[0])
    nt.links.new(lp.outputs['Is Glossy Ray'], mx.inputs[1])
    final = mix_rgb(mx.outputs[0], L2, V2, 900, 0)
    nt.links.new(final, bg.inputs['Color'])
    nt.links.new(bg.outputs['Background'], out.inputs['Surface'])
    # no volume on the world (the old optional haze is gone: the plan keeps the hall un-veiled)
    try:
        world.cycles.sampling_method = 'MANUAL'
        world.cycles.sample_map_resolution = 1024
    except Exception:
        pass
    world['garden_owner'] = OWNER
    world['garden_sky_look'] = look
    world['garden_sky_mode'] = mode
    CHANGED.append('World:' + world.name)
    say(f"world '{world.name}' rebuilt ({mode}, sky look {look}); sun direction from the lamp = ({sunv.x:.3f}, {sunv.y:.3f}, {sunv.z:.3f}), "
        f"elevation {math.degrees(math.asin(sunv.z)):.1f} deg, azimuth {math.degrees(math.atan2(sunv.y, sunv.x)):.1f} deg")
    return world


# ====================================================================================================== 2 hills and plain
RIDGES = [  # name, radius, centre y, base height, wobble, seed, haze 0 (near) .. 1 (far), existing?
    dict(name='Hills, farthest', r=190, cy=12, base=26, wobble=11, seed=4, haze=1.00, new=True),
    dict(name='Hills, far', r=120, cy=10, base=24, wobble=9, seed=1, haze=0.80, new=False),
    dict(name='Hills, middle', r=80, cy=8, base=17, wobble=7, seed=2, haze=0.55, new=False),
    dict(name='Hills, near', r=56, cy=6, base=9, wobble=4, seed=3, haze=0.30, new=False),
    dict(name='Hills, foot', r=36, cy=5, base=4.2, wobble=1.8, seed=5, haze=0.12, new=True),
]


def ridge_height(spec, a):
    rr = random.Random(spec['seed'])
    ph = [rr.uniform(0, 6.3) for _ in range(5)]
    return spec['base'] + spec['wobble'] * (0.5 * math.sin(a * 5 + ph[0]) + 0.3 * math.sin(a * 11 + ph[1]) +
                                            0.15 * math.sin(a * 23 + ph[2]) + 0.08 * math.sin(a * 47 + ph[3]))


def hill_palette(mode='golden'):
    """Per ridge (by haze 1 = farthest .. 0 = nearest): crest, body and foot colours (linear emission), cool side."""
    if mode == 'evening':
        # a deep, cool silhouette set; the foot picks up a little of the horizon glow
        return {
            1.00: ((0.10, 0.065, 0.11), (0.075, 0.055, 0.105), (0.11, 0.07, 0.11)),
            0.80: ((0.060, 0.045, 0.085), (0.045, 0.040, 0.080), (0.075, 0.055, 0.09)),
            0.55: ((0.030, 0.030, 0.060), (0.025, 0.027, 0.055), (0.045, 0.040, 0.07)),
            0.30: ((0.012, 0.016, 0.034), (0.010, 0.014, 0.030), (0.022, 0.024, 0.045)),
            0.12: ((0.005, 0.008, 0.016), (0.004, 0.007, 0.014), (0.010, 0.012, 0.022)),
        }
    return {
        1.00: ((0.76, 0.43, 0.38), (0.55, 0.37, 0.47), (0.82, 0.48, 0.42)),     # farthest: pale, the body bluer-lilac than the peach sky, the top fading into it
        0.80: ((0.52, 0.33, 0.38), (0.37, 0.27, 0.38), (0.62, 0.38, 0.40)),
        0.55: ((0.30, 0.22, 0.29), (0.20, 0.16, 0.23), (0.37, 0.26, 0.32)),
        0.30: ((0.115, 0.115, 0.145), (0.060, 0.072, 0.092), (0.14, 0.13, 0.15)),   # near: darker, cooler, bluer-green
        0.12: ((0.045, 0.060, 0.062), (0.026, 0.040, 0.040), (0.060, 0.070, 0.066)),
    }


def noise1(x, seed, octaves=3):
    """Smooth 1-D value noise in 0..1 (periodic over 2*pi for x in radians)."""
    v = 0.0
    amp = 0.5
    tot = 0.0
    for o in range(octaves):
        f = 2 ** o * 3
        rr = random.Random(seed * 131 + o)
        a, b, c = rr.uniform(0, 6.3), rr.uniform(0, 6.3), rr.uniform(0, 1)
        v += amp * (0.5 + 0.5 * math.sin(x * f + a + 0.7 * math.sin(x * (f + 2) + b)))
        tot += amp
        amp *= 0.5
    return v / tot


def emission_vc_material(name):
    """Unlit emission that shows the mesh colour attribute 'Col' (the backdrop is painted by vertex colour)."""
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    at = nt.nodes.new('ShaderNodeAttribute')
    at.attribute_name = 'Col'
    at.attribute_type = 'GEOMETRY'
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = 1.0
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    at.location, em.location, o.location = (-300, 0), (0, 0), (250, 0)
    nt.links.new(at.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs[0], o.inputs['Surface'])
    m.diffuse_color = (0.3, 0.3, 0.3, 1)
    m['garden_owner'] = OWNER
    return m


def set_backdrop_visibility(ob):
    """Seen by the camera and by mirrors (pond), but it does not light the garden and casts no shadow."""
    for attr, val in (('visible_camera', True), ('visible_glossy', True), ('visible_diffuse', False), ('visible_transmission', False),
                      ('visible_volume_scatter', False), ('visible_shadow', False)):
        try:
            setattr(ob, attr, val)
        except Exception:
            pass


def build_ridge(spec, look, sunv, mode, hp, n_target=300):
    """One full 360-degree ridge as a vertical strip with 5 rows of colour. Returns the object."""
    name = spec['name']
    rr = random.Random(spec['seed'] * 7 + 1)
    painted = (look == 'painted')
    # sample angles (radians from +y toward +x, full circle). Painted: unequal flat facets 3..9 degrees; real: even 1.2 degrees
    angs = []
    if painted:
        a = -math.pi
        while a < math.pi - math.radians(3):
            angs.append(a)
            a += math.radians(rr.uniform(3.0, 9.0))
        angs.append(math.pi)
    else:
        n = n_target
        angs = [-math.pi + 2 * math.pi * i / n for i in range(n + 1)]
    pts = []
    for a in angs:
        h = ridge_height(spec, a)
        pts.append((a, spec['r'] * math.sin(a), spec['cy'] + spec['r'] * math.cos(a), h))
    # seam: the last point must coincide with the first
    pts[-1] = (pts[-1][0], pts[0][1], pts[0][2], pts[0][3])
    crest_c, body_c, foot_c = hp[spec['haze']]
    sunh = Vector((sunv.x, sunv.y, 0)).normalized()
    sun_az = math.atan2(sunv.y, sunv.x)

    def tint(c, az, h01):
        """Sun side (backlit, hazy-warm) vs far side (front-lit, cool)."""
        d = Vector((math.cos(az), math.sin(az), 0)).dot(sunh)
        w = clamp(d, 0, 1) ** 2
        if mode == 'evening':
            return mix3(c, (c[0] * 1.4 + 0.01, c[1] * 1.0, c[2] * 0.8), w)
        warm = (c[0] * (1.0 + 0.35 * w) + 0.05 * w * h01, c[1] * (1.0 + 0.0 * w) + 0.010 * w * h01, c[2] * (1.0 - 0.28 * w))
        return warm

    bm = bmesh.new()
    layer = bm.loops.layers.float_color.new('Col')
    def rows_z(h):
        if painted:      # irregular row heights per column: the planes are not a tidy grid of equal quads
            return [-4.0, -0.4, rr.uniform(0.28, 0.52) * h, rr.uniform(0.68, 0.90) * h, h]
        return [-4.0, -0.4, 0.40 * h, 0.82 * h, h]
    verts = []
    cols = []
    for i, (a, x, y, h) in enumerate(pts):
        az = math.atan2(y - 0.0, x - 0.0)
        zs = rows_z(h)
        # edge loss: some stretches of the crest dissolve into the sky behind them (colour only)
        loss = smoothstep((noise1(a, spec['seed'] * 5 + 1) - 0.35) / 0.4) * (0.15 + 0.6 * spec['haze'])
        elev = math.atan2(h, math.hypot(x, y - 0.0))
        skyc = sky_color(Vector((x, y, h)).normalized(), sunv, mode)
        patch = 0.85 + 0.30 * noise1(a * 2.0, spec['seed'] * 11 + 3)
        c_crest = mix3(tint(crest_c, az, spec['haze']), scale3(skyc, 0.92), loss)
        c_body = tint(scale3(body_c, patch), az, spec['haze'])
        c_foot = tint(foot_c, az, spec['haze'])
        rc = [c_foot, c_foot, c_body, mix3(c_body, c_crest, 0.55), c_crest]
        verts.append([bm.verts.new((x, y, z)) for z in zs])
        cols.append(rc)
    nrow = 5
    for i in range(len(pts) - 1):
        for r in range(nrow - 1):
            f = bm.faces.new((verts[i][r], verts[i + 1][r], verts[i + 1][r + 1], verts[i][r + 1]))
            f.smooth = False
            if painted:
                # flat facet: one colour per quad, tone by the slope of the facet against the sun (slope-aligned plane feel) and a little unevenness
                a0, a1 = pts[i][0], pts[i + 1][0]
                am = 0.5 * (a0 + a1)
                dh = pts[i + 1][3] - pts[i][3]
                arc = max(1e-3, spec['r'] * (a1 - a0))
                slope = dh / arc
                tx, ty = math.cos(am), -math.sin(am)       # tangent of increasing angle (x = r sin a, y = cy + r cos a)
                tdots = tx * sunh.x + ty * sunh.y
                lit = clamp(0.55 + 2.2 * (-slope) * tdots + 0.25 * (0.5 - r / 4.0), 0.0, 1.0)
                rng = random.Random(i * 97 + r * 13 + spec['seed'])
                base = mix3(cols[i][r], cols[i + 1][r], 0.5)
                base2 = mix3(cols[i][r + 1], cols[i + 1][r + 1], 0.5)
                c = mix3(base, base2, 0.5)
                tone = (0.80 + 0.45 * lit) * (0.94 + 0.12 * rng.random())
                warmth = (1.0 + 0.10 * (lit - 0.5), 1.0, 1.0 - 0.14 * (lit - 0.5))
                cc = (c[0] * tone * warmth[0], c[1] * tone * warmth[1], c[2] * tone * warmth[2], 1.0)
                for lp in f.loops:
                    lp[layer] = cc
            else:
                for lp in f.loops:
                    v = lp.vert
                    # find row/col of this vert
                    for (ii, jj) in ((i, r), (i + 1, r), (i + 1, r + 1), (i, r + 1)):
                        if verts[ii][jj] is v:
                            c = cols[ii][jj]
                            lp[layer] = (c[0], c[1], c[2], 1.0)
                            break
    # close the seam: nothing to do (first/last share coordinates), faces already join them geometrically
    ob = bpy.data.objects.get(name)
    existed = ob is not None
    if existed and ob.type == 'MESH':
        me = ob.data
        me.clear_geometry()
        bm.to_mesh(me)
        for a in list(me.color_attributes):
            if a.name != 'Col':
                me.color_attributes.remove(a)
    else:
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        ob = bpy.data.objects.new(name, me)
        collection('G4 light').objects.link(ob)
    bm.free()
    mat = emission_vc_material(name + ' haze')
    if len(ob.data.materials):
        ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.use_smooth = False
    ob.location = (0, 0, 0)
    ob.rotation_euler = (0, 0, 0)
    ob.scale = (1, 1, 1)
    tag(ob, 'backdrop')
    set_backdrop_visibility(ob)
    (CHANGED if existed else CREATED).append(name)
    return ob


def build_plain(look, sunv, mode, hp, seed=9):
    """'Dark plain' becomes a ground that runs to the horizon: colour by distance, matched to each ridge's foot colour."""
    name = 'Dark plain'
    painted = (look == 'painted')
    cx, cy = 0.0, 7.0
    # ring radii (m) and the colour there (foot colours of the ridges; near the court dark mossy green-brown)
    stops = [(0, (0.020, 0.032, 0.020)), (14, (0.024, 0.034, 0.021)), (30, (0.045, 0.058, 0.040)), (46, hp[0.12][2]), (60, hp[0.30][2]),
             (82, hp[0.55][2]), (122, hp[0.80][2]), (192, hp[1.00][2]), (320, hp[1.00][2]), (900, hp[1.00][2])]
    if mode == 'evening':
        stops[0] = (0, (0.004, 0.006, 0.006))
        stops[1] = (14, (0.005, 0.007, 0.007))
        stops[2] = (30, (0.010, 0.012, 0.014))

    def col_at(r):
        for i in range(len(stops) - 1):
            r0, c0 = stops[i]
            r1, c1 = stops[i + 1]
            if r <= r1:
                return mix3(c0, c1, smoothstep((r - r0) / max(1e-6, r1 - r0)))
        return stops[-1][1]
    radii = [0, 10, 16, 22, 30, 38, 46, 54, 62, 72, 82, 95, 110, 122, 140, 165, 192, 230, 320, 500, 900]
    nseg = 96
    bm = bmesh.new()
    layer = bm.loops.layers.float_color.new('Col')
    zt = -0.5
    ring = []
    for r in radii:
        row = []
        for k in range(nseg):
            a = 2 * math.pi * k / nseg
            row.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), zt)))
        ring.append(row)
    for ri in range(len(radii) - 1):
        for k in range(nseg):
            k2 = (k + 1) % nseg
            quad = ((ri, k), (ri, k2), (ri + 1, k2), (ri + 1, k))
            f = bm.faces.new([ring[a][b] for a, b in quad])
            f.smooth = False
            rm = 0.5 * (radii[ri] + radii[ri + 1])
            am = 2 * math.pi * (k + 0.5) / nseg
            base = col_at(rm)
            # fields: broad patches of slightly different tone (real: soft low-frequency, painted: per-facet flat)
            if painted:
                rng = random.Random(ri * 1013 + k * 7 + seed)
                tone = 0.82 + 0.36 * rng.random()
                hue = (1.0 + 0.10 * (rng.random() - 0.5), 1.0, 1.0 - 0.10 * (rng.random() - 0.5))
                cc = (base[0] * tone * hue[0], base[1] * tone * hue[1], base[2] * tone * hue[2], 1.0)
                for lp in f.loops:
                    lp[layer] = cc
            else:
                for lp in f.loops:
                    ii = [(a, b) for a, b in quad if ring[a][b] is lp.vert][0]
                    rv = radii[ii[0]]
                    av = 2 * math.pi * ii[1] / nseg
                    c = col_at(rv)
                    t = 0.80 + 0.40 * noise1(av * 3 + rv * 0.07, seed + 2)
                    lp[layer] = (c[0] * t, c[1] * t * (0.97 + 0.06 * noise1(av * 5 + rv * 0.03, seed + 5)), c[2] * t, 1.0)
    ob = bpy.data.objects.get(name)
    existed = ob is not None
    if existed and ob.type == 'MESH':
        me = ob.data
        me.clear_geometry()
        bm.to_mesh(me)
    else:
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        ob = bpy.data.objects.new(name, me)
        collection('G4 light').objects.link(ob)
    bm.free()
    mat = emission_vc_material('Dark plain ground')
    if len(ob.data.materials):
        ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)
    ob.location = (0, 0, 0)
    ob.rotation_euler = (0, 0, 0)
    ob.scale = (1, 1, 1)
    tag(ob, 'backdrop')
    set_backdrop_visibility(ob)
    (CHANGED if existed else CREATED).append(name)
    return ob


def build_hills(look='real', mode='golden', seed=7):
    sunv = sun_vector()
    hp = hill_palette(mode)
    obs = []
    for spec in RIDGES:
        obs.append(build_ridge(spec, look, sunv, mode, hp))
    obs.append(build_plain(look, sunv, mode, hp))
    say(f"hills: {len(RIDGES)} full-circle ridges + plain to the horizon ({'flat facets' if look == 'painted' else 'colour gradients'}, {mode})")
    return obs


# ====================================================================================================== 3 lights
def kelvin_rgb(k):
    """Rough blackbody colour for 1000..6500 K (linear-ish, for lamp colours)."""
    t = k / 100.0
    r = 1.0 if t <= 66 else clamp(1.292936 * ((t - 60) ** -0.1332047592))
    g = clamp(0.390081 * math.log(t) - 0.631841) if t <= 66 else clamp(1.129891 * ((t - 60) ** -0.0755148492))
    b = 1.0 if t >= 66 else (0.0 if t <= 19 else clamp(0.543207 * math.log(t - 10) - 1.196254))
    return (r, g, b)


def get_collection_objects(pred):
    return [o for o in bpy.data.objects if pred(o)]


LIGHT_DEFAULTS = dict(sun_energy=12.0, fill_energy=2600.0, rim_energy=4.5, roof_energy=5000.0, lantern_watts=18.0, flame_strength=7.0)


def remove_light(name, coll_name=None):
    ob = bpy.data.objects.get(name)
    if ob is not None:
        bpy.data.objects.remove(ob, do_unlink=True)
    ld = bpy.data.lights.get(name)
    if ld is not None and ld.users == 0:
        bpy.data.lights.remove(ld)
    if coll_name:
        c = bpy.data.collections.get(coll_name)
        if c is not None:
            bpy.data.collections.remove(c)


def linked_receivers(coll_name, predicate):
    """A collection (kept out of the scene) listing the only objects a linked light will light."""
    recv = bpy.data.collections.new(coll_name)
    recv.use_fake_user = True
    names = []
    for o in bpy.data.objects:
        if o.type in ('MESH', 'CURVE') and predicate(o):
            try:
                recv.objects.link(o)
                names.append(o.name)
            except Exception:
                pass
    return recv, names


def setup_lights(look='real', mode='golden', rim=True, **kw):
    sc = bpy.context.scene
    L = dict(LIGHT_DEFAULTS)
    L.update({k: v for k, v in kw.items() if v is not None})
    sun = sun_object()
    fill = bpy.data.objects.get('Cool sky fill')
    lantern = bpy.data.objects.get('Lantern light')
    if mode == 'golden':
        # sun: direction and 1.2 degree disc stay exactly as they are (the low raking light is the picture); strength is an option
        if sun is not None:
            sun.data.energy = L['sun_energy']
            CHANGED.append(sun.name)
        if fill is not None:
            fill.data.energy = L['fill_energy']
            fill.data.color = (0.68, 0.79, 1.0)
            fill.visible_camera = False
            CHANGED.append(fill.name)
        if lantern is not None:
            lantern.data.energy = L['lantern_watts']
            lantern.data.color = (1.0, 0.50, 0.20)
            CHANGED.append(lantern.name)
        flame = bpy.data.materials.get('Lantern flame')
        if flame is not None and flame.node_tree:
            em = next((n for n in flame.node_tree.nodes if n.bl_idname == 'ShaderNodeEmission'), None)
            if em is not None:
                em.inputs['Color'].default_value = (1.0, 0.46, 0.14, 1.0)
                em.inputs['Strength'].default_value = L['flame_strength']      # dim: a few stops over the sunlit stone, not a white cut-out
                CHANGED.append('Material:Lantern flame')
        for i in range(4):
            g = bpy.data.objects.get(f'Hall glow {i}')
            if g is not None:
                g.data.energy = 90.0
                g.visible_camera = False
    # ---- rim: one sun-type lamp from behind-left (the sun's side), linked ONLY to the maple and the hall roof / beams (back-light, edge glow)
    remove_light('Rim light (maple, hall edge)', 'G4 rim receivers')
    remove_light('Roof lift (hall roof only)', 'G4 roof receivers')
    if rim and mode == 'golden':
        ld = bpy.data.lights.new('Rim light (maple, hall edge)', 'SUN')
        ld.energy = L['rim_energy']
        ld.angle = math.radians(2.0)
        ld.color = (1.0, 0.62, 0.32)
        ro = bpy.data.objects.new('Rim light (maple, hall edge)', ld)
        collection('G4 light').objects.link(ro)
        travel = Vector((0.62, -0.66, -0.42)).normalized()          # travels toward the camera side and a little right: comes from the north-west, 25 deg up
        ro.rotation_euler = travel.to_track_quat('-Z', 'Y').to_euler()
        tag(ro, 'light')
        recv, names = linked_receivers('G4 rim receivers', lambda o: o.name.startswith('Maple') or o.name in ('Hall roof', 'Hall beams', 'Eave soffit'))
        try:
            ro.light_linking.receiver_collection = recv
        except Exception as e:
            say('light linking not set: ' + str(e))
        CREATED.append(ro.name)
        say(f"rim light (sun type, {L['rim_energy']}) linked to {len(names)} objects (maple parts, hall roof edge)")
        # ---- roof lift: the tile roof is crushed black (5 percent of its band is near black); a big soft cool light on the roof only
        if L['roof_energy'] > 0 and bpy.data.objects.get('Hall roof') is not None:
            rl = bpy.data.lights.new('Roof lift (hall roof only)', 'AREA')
            rl.shape = 'RECTANGLE'
            rl.size, rl.size_y = 9.0, 4.0
            rl.energy = L['roof_energy']
            rl.color = (0.86, 0.90, 1.0)
            rob = bpy.data.objects.new('Roof lift (hall roof only)', rl)
            collection('G4 light').objects.link(rob)
            rob.location = (-6.0, -9.0, 9.0)
            rob.rotation_euler = (Vector((0.2, 7.2, 3.9)) - rob.location).to_track_quat('-Z', 'Y').to_euler()
            rob.visible_camera = False
            tag(rob, 'light')
            recv2, names2 = linked_receivers('G4 roof receivers', lambda o: o.name == 'Hall roof')
            try:
                rob.light_linking.receiver_collection = recv2
            except Exception as e:
                say('roof light linking not set: ' + str(e))
            CREATED.append(rob.name)
            say(f"roof lift light ({L['roof_energy']} W) linked to {names2}")
    say(f"lights: sun {L['sun_energy']}, fill {L['fill_energy']} W cooler, lantern dim ({L['lantern_watts']} W, flame {L['flame_strength']}), hall glow kept")


# ====================================================================================================== 4 light groups
def emits(ob):
    if ob.type != 'MESH':
        return False
    for slot in ob.material_slots:
        m = slot.material
        if m is None or m.node_tree is None:
            continue
        for n in m.node_tree.nodes:
            if n.bl_idname == 'ShaderNodeBsdfPrincipled':
                s, c = n.inputs['Emission Strength'], n.inputs['Emission Color']
                if (s.is_linked or s.default_value > 0) and (c.is_linked or max(c.default_value[:3]) > 0):
                    return True
            elif n.bl_idname == 'ShaderNodeEmission':
                if n.inputs['Strength'].is_linked or n.inputs['Strength'].default_value > 0:
                    return True
    return False


GROUPS = ['sun', 'rim', 'sky', 'fill', 'hall', 'lantern', 'rest']


def setup_groups():
    sc = bpy.context.scene
    vl = sc.view_layers[0]
    for g in GROUPS:
        if g not in [x.name for x in vl.lightgroups]:
            vl.lightgroups.add(name=g)
    assigned = {}

    def put(ob, g):
        ob.lightgroup = g
        assigned.setdefault(g, []).append(ob.name)
    for o in bpy.data.objects:
        n = o.name
        if o.type == 'LIGHT':
            if n == 'Golden hour sun':
                put(o, 'sun')
            elif n.startswith('Rim light'):
                put(o, 'rim')
            elif n == 'Cool sky fill' or n.startswith('Roof lift'):
                put(o, 'fill')
            elif n.startswith('Hall glow'):
                put(o, 'hall')
            elif n == 'Lantern light':
                put(o, 'lantern')
            else:
                put(o, 'rest')
        elif o.type == 'MESH' and (o.name.startswith('Hills, ') or o.name == 'Dark plain'):
            put(o, 'sky')
        elif o.type == 'MESH' and n in ('Shoji paper', 'Open room back'):
            put(o, 'hall')
        elif o.type == 'MESH' and (n.startswith('Lantern window glow')):
            put(o, 'lantern')
        elif emits(o):
            put(o, 'rest')
    sc.world.lightgroup = 'sky'
    CHANGED.append('ViewLayer lightgroups')
    say('light groups: ' + ', '.join(f"{g} ({len(v)})" for g, v in assigned.items()) + ', world -> sky')
    return assigned


# ====================================================================================================== 5 finish: render settings and compositor
def load_comp_asset(name):
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        return ng
    path = os.path.join(bpy.utils.system_resource('DATAFILES'), 'assets', 'nodes', 'compositing_nodes_essentials.blend')
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        if name not in src.node_groups:
            raise KeyError(f'{name} not in {path}')
        dst.node_groups = [name]
    return bpy.data.node_groups[name]


def setup_finish(look='real', exposure=0.5, vignette=0.55, bloom=0.05, bloom_threshold=2.0):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.01
    cy.use_denoising = True
    try:
        cy.denoiser = 'OPENIMAGEDENOISE'
        cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
    except Exception:
        pass
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Punchy'
    except Exception:
        pass
    sc.view_settings.exposure = exposure
    try:
        sc.render.compositor_device = 'CPU'
    except Exception:
        pass
    tree = bpy.data.node_groups.get('GARDEN finish')
    if tree is not None:
        bpy.data.node_groups.remove(tree)
    tree = bpy.data.node_groups.new('GARDEN finish', 'CompositorNodeTree')
    tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = tree.nodes.new('CompositorNodeRLayers')
    out = tree.nodes.new('NodeGroupOutput')
    rl.location, out.location = (-600, 0), (900, 0)
    sock = rl.outputs['Image']
    x = -300
    if bloom:
        g = tree.nodes.new('CompositorNodeGlare')
        g.inputs['Type'].default_value = 'Bloom'
        try:
            g.inputs['Quality'].default_value = 'High'
        except Exception:
            pass
        g.inputs['Threshold'].default_value = bloom_threshold
        g.inputs['Strength'].default_value = bloom
        g.inputs['Size'].default_value = 0.5
        tree.links.new(g.inputs['Image'], sock)
        sock = g.outputs['Image']
        g.location = (x, 0)
        x += 250
    if vignette:
        v = tree.nodes.new('CompositorNodeGroup')
        v.node_tree = load_comp_asset('Vignette')
        v.inputs['Factor'].default_value = vignette
        v.inputs['Feather'].default_value = 0.4
        tree.links.new(v.inputs['Image'], sock)
        sock = v.outputs[0]
        v.location = (x, 0)
        x += 250
    tree.links.new(out.inputs[0], sock)
    sc.compositing_node_group = tree
    sc.render.use_compositing = True
    CHANGED.append('Scene render settings and compositor')
    say(f"finish: Cycles, caustics off, AgX Punchy exposure {exposure}, bloom {bloom} above {bloom_threshold}, vignette {vignette}, no blur")


# ====================================================================================================== 6 cameras
def setup_cameras():
    sc = bpy.context.scene
    cam = bpy.data.objects.get('photo') or bpy.data.objects.get('Camera')
    if cam is not None and cam.name != 'photo':
        RENAMED[cam.name] = 'photo'
        cam.name = 'photo'
        if cam.data.name == 'Camera':
            cam.data.name = 'photo'
        CHANGED.append("Camera -> photo")
        say("hero camera renamed 'Camera' -> 'photo' (place and lens unchanged)")
    old = bpy.data.objects.get('veranda')
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    cd = bpy.data.cameras.new('veranda')
    cd.lens = 24
    cd.sensor_width = 36
    cd.clip_start, cd.clip_end = 0.1, 1000.0
    focus = bpy.data.objects.get('Focus')
    cd.dof.use_dof = focus is not None
    if focus is not None:
        cd.dof.focus_object = focus
        cd.dof.aperture_fstop = 4.0
    ob = bpy.data.objects.new('veranda', cd)
    collection('G4 light').objects.link(ob)
    ob.location = (3.6, 5.3, 1.55)
    ob.rotation_euler = (Vector((-2.5, 0.8, 0.55)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
    ob['garden_owner'] = OWNER
    ob['garden_role'] = 'camera'
    CREATED.append('veranda')
    if cam is not None:
        sc.camera = cam
    say("camera 'veranda' added at (3.6, 5.3, 1.55) looking at (-2.5, 0.8, 0.55), 24 mm; scene camera stays 'photo'")


# ====================================================================================================== entry points
def snapshot_names():
    return set(o.name for o in bpy.data.objects), set(m.name for m in bpy.data.materials)


def apply(options=None):
    o = dict(look='real', steps=None, sky_look=None, hills_look=None, seed=7, exposure=0.5, vignette=0.55, bloom=0.05, rim=True,
             sun_energy=None, fill_energy=None, rim_energy=None, roof_energy=None, lantern_watts=None, flame_strength=None)
    o.update(options or {})
    if o['look'] not in ('real', 'painted'):
        raise ValueError("look must be 'real' or 'painted'")
    LOG.clear()
    CHANGED.clear()
    CREATED.clear()
    RENAMED.clear()
    t0 = time.time()
    before_o, before_m = snapshot_names()
    steps = [s for s in ALL_STEPS if (o['steps'] is None or s in o['steps'])]
    sky_look = o['sky_look'] or o['look']
    hills_look = o['hills_look'] or o['look']
    for s in steps:
        say(f'--- step {s}')
        if s == 'cameras':
            setup_cameras()
        elif s == 'world':
            build_world(sky_look, 'golden', o['seed'])
        elif s == 'hills':
            build_hills(hills_look, 'golden', o['seed'])
        elif s == 'lights':
            setup_lights(o['look'], 'golden', rim=o['rim'], sun_energy=o['sun_energy'], fill_energy=o['fill_energy'], rim_energy=o['rim_energy'],
                         roof_energy=o['roof_energy'], lantern_watts=o['lantern_watts'], flame_strength=o['flame_strength'])
        elif s == 'groups':
            setup_groups()
        elif s == 'finish':
            setup_finish(o['look'], o['exposure'], o['vignette'], o['bloom'])
    bpy.context.scene['garden_light_applied'] = o['look']
    after_o, after_m = snapshot_names()
    gone = sorted(n for n in (before_o - after_o) if n not in RENAMED)
    rep = dict(look=o['look'], steps=steps, seconds=round(time.time() - t0, 1), created=sorted(CREATED), changed=sorted(set(CHANGED)),
               renamed=dict(RENAMED), deleted=gone, new_objects=sorted(after_o - before_o), new_materials=sorted(after_m - before_m),
               gone_materials=sorted(before_m - after_m), log=list(LOG))
    say(f"REPORT created {len(rep['created'])}: {', '.join(rep['created'])}")
    say(f"REPORT changed {len(rep['changed'])}: {', '.join(rep['changed'])}")
    say(f"REPORT renamed {rep['renamed']}; deleted {len(gone)}: {', '.join(gone) or 'none'}")
    say(f"done in {rep['seconds']} s")
    return rep


def apply_evening(options=None):
    """Blue evening variant, applied AFTER apply(): sun off, deep blue graded sky, cooler dimmer fill, screens kept, lantern lit (about 2000 K) and dim."""
    o = dict(look='real', seed=7, exposure=1.4, lantern_watts=40.0, flame_strength=16.0, fill_energy=620.0)
    o.update(options or {})
    LOG.clear()
    CHANGED.clear()
    CREATED.clear()
    before_o, before_m = snapshot_names()
    sun = sun_object()
    if sun is not None:
        sun.data.energy = 0.0
        CHANGED.append(sun.name)
    fill = bpy.data.objects.get('Cool sky fill')
    if fill is not None:
        fill.data.energy = o['fill_energy']
        fill.data.color = (0.42, 0.55, 1.0)
        CHANGED.append(fill.name)
    for nm in ('Rim light (maple, hall edge)', 'Roof lift (hall roof only)'):
        rim = bpy.data.objects.get(nm)
        if rim is not None:
            rim.data.energy = 0.0
            CHANGED.append(rim.name)
    build_world(o['look'], 'evening', o['seed'])
    build_hills(o['look'], 'evening', o['seed'])
    lan = bpy.data.objects.get('Lantern light')
    if lan is not None:
        lan.data.energy = o['lantern_watts']
        lan.data.color = kelvin_rgb(2000)
        CHANGED.append(lan.name)
    flame = bpy.data.materials.get('Lantern flame')
    if flame is not None and flame.node_tree:
        em = next((n for n in flame.node_tree.nodes if n.bl_idname == 'ShaderNodeEmission'), None)
        if em is not None:
            c = kelvin_rgb(2000)
            em.inputs['Color'].default_value = (c[0], c[1] * 0.95, c[2] * 0.7, 1.0)
            em.inputs['Strength'].default_value = o['flame_strength']
            CHANGED.append('Material:Lantern flame')
    sc = bpy.context.scene
    sc.view_settings.exposure = o['exposure']
    sc['garden_light_variant'] = 'evening'
    after_o, after_m = snapshot_names()
    rep = dict(variant='evening', created=sorted(CREATED), changed=sorted(set(CHANGED)), deleted=sorted(before_o - after_o), log=list(LOG))
    say('evening variant applied: sun 0, deep blue sky, fill %s W, lantern 2000 K' % o['fill_energy'])
    return rep


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    look = argv[0] if argv else 'real'
    print(apply({'look': look}))
