"""Shared helper for the four builders (written by the direction step, 22 October). Runs inside Blender's Python (numpy is there; PIL is NOT).

What it does, in plain words:
  height_to_normal(h, strength, tile)  turns a height picture (numpy array, rows from the TOP of the picture, 0..1, white = high)
                                        into a tangent-space normal picture in the OPENGL convention (green = up the picture, +V),
                                        which is what Blender's Normal Map node expects.
  save_normal_png(path, n)              writes it as an 8-bit PNG (use 16-bit if you can: save through bpy.data.images, see below).
  make_normal_image(name, rgb)          puts the picture straight into Blender as a Non-Color image (no file needed).
  check_direction(out_dir)              the TEST LIGHT: builds a plane with one round bump, lights it from +X, then from +Y, then draws
                                        two tiny pictures and prints PASS only if the lit side is brighter. Run it once per builder
                                        and keep the printed line in your report. It draws with Cycles on the CPU, a few seconds.
Convention used everywhere: image row 0 = top = +V (Blender), column 0 = left = -U. A bump that is WHITE in the height picture must
be lit on the side that faces the light.
"""
import numpy as np


def height_to_normal(h, strength=2.0, tile=True):
    """h: 2D float array (rows top to bottom). strength: bigger = steeper (2.0 is soft and painterly, 6.0 is strong).
    tile=True uses wrap-around differences so a tiling texture shows no seam."""
    h = np.asarray(h, dtype=np.float32)
    if h.ndim == 3:
        h = h[..., :3].mean(axis=2)
    if tile:
        dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5      # per column step, to the right (+U)
        dy_row = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5  # per row step, DOWN the picture (-V)
    else:
        dx = np.gradient(h, axis=1)
        dy_row = np.gradient(h, axis=0)
    # slope is in height units per pixel; scale so strength 1.0 means "height 1.0 over about 1/8 of the picture width is 45 degrees"
    k = strength * h.shape[1] / 8.0
    nx = -dx * k
    ny = +dy_row * k          # +V is up the picture, rows go down, so the sign flips here (this is the OpenGL green channel)
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / ln, ny / ln, nz / ln], axis=-1)
    return n.astype(np.float32)          # values -1..1


def to_rgb(n):
    return np.clip(n * 0.5 + 0.5, 0.0, 1.0)


def make_normal_image(name, n, float_buffer=False):
    """Creates a Blender image called `name` from a normal array (-1..1) and marks it Non-Color. Remember to bpy.data.images[name].pack()
    or save it to your folder (image.filepath_raw = ..., image.file_format = 'PNG', image.save()) before the scene is saved."""
    import bpy
    rgb = to_rgb(n)
    h, w = rgb.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=False, float_buffer=float_buffer)
    # GOTCHA (found 22 October, Blender 5.2.2): changing the colour space AFTER the pixels were written wipes a generated image to black.
    # So: colour space first, pixels second, and never touch colorspace_settings again on a generated image.
    img.colorspace_settings.name = 'Non-Color'
    flat = np.concatenate([rgb[::-1], np.ones((h, w, 1), np.float32)], axis=2)   # bpy rows start at the BOTTOM, numpy rows at the top
    img.pixels.foreach_set(flat.ravel())
    img.update()
    return img


def save_normal_png(path, n):
    import bpy
    img = make_normal_image("_tmp_normal_save", n)
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)


def add_normal_map_nodes(mat, image, uv_map, strength=1.0, scale=(1, 1, 1), bsdf=None):
    """Adds UV Map -> Mapping -> Image Texture (Non-Color, Repeat) -> Normal Map (Tangent, OpenGL) -> BSDF Normal, and returns the Normal Map node.
    The Principled BSDF's existing Normal link (for example from a Bump node) is replaced; if you want both, feed the Bump node's
    'Normal' input from this node instead (Bump after Normal Map is fine for fine detail on top)."""
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = bsdf or next(n for n in nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    uv = nodes.new('ShaderNodeUVMap'); uv.uv_map = uv_map
    mp = nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = scale
    tx = nodes.new('ShaderNodeTexImage'); tx.image = image; tx.interpolation = 'Cubic'; tx.extension = 'REPEAT'
    if image.colorspace_settings.name != 'Non-Color':      # see the GOTCHA in make_normal_image: do not set it again when it is already right
        image.colorspace_settings.name = 'Non-Color'
    nm = nodes.new('ShaderNodeNormalMap'); nm.space = 'TANGENT'; nm.uv_map = uv_map; nm.inputs['Strength'].default_value = strength
    links.new(uv.outputs['UV'], mp.inputs['Vector'])
    links.new(mp.outputs['Vector'], tx.inputs['Vector'])
    links.new(tx.outputs['Color'], nm.inputs['Color'])
    links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    for n_, nm_ in ((uv, 'NM UV'), (mp, 'NM Mapping'), (tx, 'NM Image'), (nm, 'NM Normal Map')):
        n_.name = n_.label = nm_
    return nm


def check_direction(out_dir=None, size=96, samples=24, verbose=True):
    """TEST LIGHT. One round bump on a plane with default UVs (u to the right = +X, v up = +Y), camera straight down (ortho, up = +Y),
    a low sun from +X and then from +Y. PASS only if the +X side of the bump is brighter than its -X side under the first sun and the
    +Y side is brighter than its -Y side under the second. Also draws the deliberately WRONG (green flipped) version to prove the test
    can fail. Returns a dict and prints one line starting with NORMAL_DIRECTION."""
    import bpy, math, os, tempfile
    from mathutils import Vector
    out_dir = out_dir or tempfile.mkdtemp(prefix="nrmtest_")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = samples; sc.cycles.use_denoising = False
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.view_settings.view_transform = 'Standard'
    sc.world = bpy.data.worlds.new("W"); sc.world.color = (0, 0, 0)
    bpy.ops.mesh.primitive_plane_add(size=2.0)
    plane = bpy.context.active_object
    N = 256
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    r2 = ((xx - N / 2) ** 2 + (yy - N / 2) ** 2) / (N * 0.18) ** 2
    height = np.exp(-r2)                                   # one soft round bump in the middle, white = high
    results = {}
    cam_d = bpy.data.cameras.new("C"); cam_d.type = 'ORTHO'; cam_d.ortho_scale = 2.0
    cam = bpy.data.objects.new("C", cam_d); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = (0, 0, 5)                               # looking down -Z, image up = +Y, image right = +X
    sun_d = bpy.data.lights.new("S", 'SUN'); sun_d.energy = 4.0
    sun = bpy.data.objects.new("S", sun_d); sc.collection.objects.link(sun)
    for flip in (False, True):
        n = height_to_normal(height, strength=3.0, tile=False)
        if flip:
            n[..., 1] *= -1.0
        img = make_normal_image("nrm_test_%s" % ("flipped" if flip else "ok"), n)
        m = bpy.data.materials.new("m"); m.use_nodes = True
        bs = m.node_tree.nodes['Principled BSDF']; bs.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1); bs.inputs['Roughness'].default_value = 1.0
        plane.data.materials.clear(); plane.data.materials.append(m)
        if not plane.data.uv_layers:
            plane.data.uv_layers.new(name="UVMap")
        add_normal_map_nodes(m, img, plane.data.uv_layers[0].name)
        for az_name, az in (("from+X", 0.0), ("from+Y", 90.0)):
            el = math.radians(30.0)
            direction = Vector((-math.cos(math.radians(az)) * math.cos(el), -math.sin(math.radians(az)) * math.cos(el), -math.sin(el)))
            sun.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
            path = os.path.join(out_dir, "nrm_%s_%s.png" % ("flipped" if flip else "ok", az_name))
            sc.render.filepath = path
            bpy.ops.render.render(write_still=True)
            a = bpy.data.images.load(path)
            px = np.array(a.pixels[:], dtype=np.float32).reshape(size, size, 4)[..., :3].mean(axis=2)   # rows from the BOTTOM
            bpy.data.images.remove(a)
            c = size // 2; w = size // 6
            if az == 0.0:
                lit, dark = px[c - w:c + w, c + w // 2:c + w + w // 2].mean(), px[c - w:c + w, c - w - w // 2:c - w // 2].mean()   # right of centre vs left
            else:
                lit, dark = px[c + w // 2:c + w + w // 2, c - w:c + w].mean(), px[c - w - w // 2:c - w // 2, c - w:c + w].mean()   # top (higher row = +Y) vs bottom
            results[("flipped" if flip else "ok", az_name)] = (float(lit), float(dark), bool(lit > dark * 1.05))
    ok = all(results[("ok", k)][2] for k in ("from+X", "from+Y"))
    wrong_fails = (not results[("flipped", "from+Y")][2])          # flipping green must break the +Y light; if it does not, the test is blind
    line = "NORMAL_DIRECTION %s (right/left under sun from +X: %.3f vs %.3f; top/bottom under sun from +Y: %.3f vs %.3f; flipped-green test detects the error: %s)" % (
        "PASS" if (ok and wrong_fails) else "FAIL",
        results[("ok", "from+X")][0], results[("ok", "from+X")][1], results[("ok", "from+Y")][0], results[("ok", "from+Y")][1], wrong_fails)
    if verbose:
        print(line)
    return {"pass": bool(ok and wrong_fails), "detail": {str(k): v for k, v in results.items()}, "line": line}


if __name__ == "__main__":
    check_direction()
