"""World, sun, render settings and cameras."""
import bpy
import math
from mathutils import Vector, Euler, Matrix
import common as C

SUN_ELEV = 34.0     # degrees above horizon
SUN_AZ = 315.0      # degrees counter-clockwise from +X (east): 315 = south-east (morning sun)


def sun_vector(elev=None, az=None):
    elev = math.radians(SUN_ELEV if elev is None else elev)
    az = math.radians(SUN_AZ if az is None else az)
    return Vector((math.cos(elev) * math.cos(az), math.cos(elev) * math.sin(az), math.sin(elev)))


def setup_world(strength=0.16, elev=None, az=None, clouds=True, coverage=0.8):
    sc = bpy.context.scene
    w = bpy.data.worlds.get("Sky") or bpy.data.worlds.new("Sky")
    sc.world = w
    w.use_nodes = True
    nb = C.NB(w.node_tree)
    sky = nb.node('ShaderNodeTexSky')
    sky.sky_type = 'MULTIPLE_SCATTERING'
    e = math.radians(SUN_ELEV if elev is None else elev)
    a = math.radians(SUN_AZ if az is None else az)
    sky.sun_elevation = e
    # Cycles: sun azimuth phi = sun_rotation + 90deg (measured from +X)
    sky.sun_rotation = a - math.pi / 2
    sky.sun_disc = False
    sky.air_density = 1.0
    sky.aerosol_density = 1.6
    sky.altitude = 300.0
    skycol = nb.out(sky)
    col = skycol
    if clouds:
        tc = nb.node('ShaderNodeTexCoord')
        D = nb.vmath('NORMALIZE', nb.out(tc, 'Generated'))
        dx, dy, dz = nb.sep(D)
        zc = nb.math('MAXIMUM', dz, 0.02)
        p = nb.comb(nb.math('DIVIDE', dx, zc), nb.math('DIVIDE', dy, zc), 0.0)
        n1 = nb.noise(p, scale=0.42, detail=6, rough=0.58, distortion=0.25)
        n2 = nb.noise(p, scale=2.3, detail=5, rough=0.6)
        dens = nb.math('ADD', n1, nb.math('MULTIPLY', nb.math('SUBTRACT', n2, 0.5), 0.35))
        cov = nb.maprange(dens, 1.0 - coverage * 0.62, 1.0 - coverage * 0.62 + 0.16, 0.0, 1.0, interp='SMOOTHSTEP')
        fade = nb.maprange(dz, 0.02, 0.22, 0.0, 1.0, interp='SMOOTHSTEP')
        cov = nb.math('MULTIPLY', cov, fade)
        shade = nb.maprange(n2, 0.3, 0.7, 1.15, 2.1)
        cloudcol = nb.hsv(skycol, s=0.12, v=shade)
        col = nb.mix(nb.math('MULTIPLY', cov, 0.92), skycol, cloudcol)
    bg = nb.node('ShaderNodeBackground')
    nb.set(bg, 'Color', col)
    nb.set(bg, 'Strength', strength)
    out = nb.node('ShaderNodeOutputWorld')
    nb.links.new(bg.outputs[0], out.inputs['Surface'])
    return w


def setup_sun(strength=4.6, angle_deg=1.0, color=(1.0, 0.91, 0.79), elev=None, az=None):
    sun = bpy.data.objects.get("Sun")
    if sun is None:
        ld = bpy.data.lights.new("Sun", 'SUN')
        sun = bpy.data.objects.new("Sun", ld)
        C.get_collection("Lighting").objects.link(sun)
    ld = sun.data
    ld.energy = strength
    ld.angle = math.radians(angle_deg)
    ld.color = color
    d = sun_vector(elev, az)
    # lamp shines along -Z: +Z must point at the sun
    rot = d.to_track_quat('Z', 'Y')
    sun.rotation_mode = 'QUATERNION'
    sun.rotation_quaternion = rot
    sun.location = d * 100
    return sun


def setup_render(samples=64, res=(1200, 800), pct=100, denoise=True):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.03
    cy.use_denoising = denoise
    try:
        cy.denoiser = 'OPENIMAGEDENOISE'
    except Exception:
        pass
    cy.max_bounces = 8
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 3
    cy.transmission_bounces = 6
    cy.transparent_max_bounces = 12
    cy.volume_bounces = 0
    cy.sample_clamp_indirect = 8.0
    cy.use_light_tree = True
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    sc.render.resolution_x = res[0]
    sc.render.resolution_y = res[1]
    sc.render.resolution_percentage = pct
    sc.render.film_transparent = False
    vs = sc.view_settings
    vs.view_transform = 'AgX'
    try:
        vs.look = 'AgX - Medium High Contrast'
    except Exception:
        try:
            vs.look = 'Medium High Contrast'
        except Exception:
            pass
    vs.exposure = 0.0
    vs.gamma = 1.0
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = 93
    return sc


def camera(name, loc, target=None, lens=35.0, rot=None, sensor=36.0, clip_end=1500.0):
    cam = bpy.data.objects.get(name)
    if cam is None:
        cd = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, cd)
        C.get_collection("Cameras").objects.link(cam)
    cam.data.lens = lens
    cam.data.sensor_width = sensor
    cam.data.clip_start = 0.05
    cam.data.clip_end = clip_end
    cam.location = loc
    if target is not None:
        d = Vector(target) - Vector(loc)
        cam.rotation_mode = 'QUATERNION'
        cam.rotation_quaternion = d.to_track_quat('-Z', 'Y')
    elif rot is not None:
        cam.rotation_mode = 'XYZ'
        cam.rotation_euler = [math.radians(r) for r in rot]
    return cam


def render_to(path, cam_name, samples=None, pct=None):
    sc = bpy.context.scene
    sc.camera = bpy.data.objects[cam_name]
    if samples:
        sc.cycles.samples = samples
    if pct:
        sc.render.resolution_percentage = pct
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


SHOTS = {
    # name: (eye xy, eye height above ground, target xy, target height above ground, lens)
    "CamAerial": dict(eye=(-48.0, -70.0), eye_h=70.0, tgt=(-3.0, 5.0), tgt_h=0.0, lens=29.0, abs_eye=True),
    "CamRoad": dict(eye=(-39.5, -11.75), eye_h=1.65, tgt=(-12.0, -1.5), tgt_h=1.5, lens=26.0),
    "CamStable": dict(eye=(2.0, 19.2), eye_h=1.7, tgt=(9.2, 30.3), tgt_h=1.75, lens=25.0),
    "CamCottage": dict(eye=(-31.8, -3.4), eye_h=1.65, tgt=(-24.0, 4.6), tgt_h=2.6, lens=28.0),
    "CamRoadClose": dict(eye=(-4.9, -5.55), eye_h=0.95, tgt=(-1.6, -4.85), tgt_h=0.0, lens=30.0, dof=(3.2, 5.6)),
}


def make_cameras(shots=None):
    import terrain as T
    shots = shots or SHOTS
    trees = T.ground_bvh()
    out = {}
    for name, s in shots.items():
        ex, ey = s["eye"]
        tx, ty = s["tgt"]
        ez = s["eye_h"] if s.get("abs_eye") else T.ground_z(ex, ey, trees) + s["eye_h"]
        tz = T.ground_z(tx, ty, trees) + s["tgt_h"]
        cam = camera(name, (ex, ey, ez), (tx, ty, tz), lens=s["lens"])
        if s.get("dof"):
            cam.data.dof.use_dof = True
            cam.data.dof.focus_distance = s["dof"][0]
            cam.data.dof.aperture_fstop = s["dof"][1]
        else:
            cam.data.dof.use_dof = False
        out[name] = [round(ex, 2), round(ey, 2), round(ez, 2)]
    return out
