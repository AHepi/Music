# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# PRIVATE MASKS of the growth layer (the foundation's bus has no names for these; they are made here from the foundation's ground-plan pack and say so in the report):
#     wall_strip     1 at the foot of a wall, falling to 0 at about 18 cm out (the strip where a plant at a wall foot may stand), from the pack's wall_dist
#     gutter_strip   1 on the dots of the set's gutter-side role (for a paved road: the setts) that lie within a reach of the stones of the channel role (the 0.3 to 0.9 m beside the
#                    channel: rule W1), 0 elsewhere; the roles and the reach are the set's `growth.gutter_side` block; a set without one gets 0
#     has_ground     1 where the ground plan has ground (the pack's own gp_height green channel)
# and the numbers the calibration needs: the ground area, the wall-foot length and the gutter-side length inside a window round a camera (plain numpy; the same arrays make the plan
# of piece density). The arrays are laid out like the pack: row 0 = the LOW end of y, column 0 = the LOW end of x, one dot = the pack's ground dot.
# Blender code reads the pack pictures from the images the bus already loaded (no OpenCV needed except for the distance map of the gutter strip: masks.ensure_cv2()).
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def smooth(x, e0, e1):
    t = np.clip((x - e0) / max(e1 - e0, 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ---------------------------------------------------------------------------------------------------------------------------------------------- reading the pack
def channel_from_image(image, channel):
    """One channel of a Blender image as a (h, w) float array with row 0 = low y (Blender's own row order; the pack's PNGs were written to match)."""
    w, h = image.size
    buf = np.empty(w * h * 4, np.float32)
    image.pixels.foreach_get(buf)
    return buf.reshape(h, w, 4)[..., 'RGBA'.index(channel)].copy()


def read_masks(pack, names):
    """{name: (h, w) array} of ground-plan masks from the loaded MaskPack (names the pack does not have are left out)."""
    out = {}
    for name in names:
        entry = pack.entry('GP', name)
        if entry is None or entry['picture'].startswith('tx:'):
            continue
        out[name] = channel_from_image(pack.image(entry['picture']), entry['channel'])
    return out


def read_ground(pack):
    """(height m, has_ground, role id) from the pack's height picture: R height over the z range, G has ground, B role number / 65."""
    manifest = pack.manifest
    image = pack.image('gp_height')
    w, h = image.size
    buf = np.empty(w * h * 4, np.float32)
    image.pixels.foreach_get(buf)
    a = buf.reshape(h, w, 4)
    z_lo, z_hi = manifest['ground']['z_range']
    return z_lo + a[..., 0] * (z_hi - z_lo), a[..., 1] > 0.5, np.round(a[..., 2] * 65.0).astype(int)


# ---------------------------------------------------------------------------------------------------------------------------------------------- the private masks
def make_sites(masks, has_ground, role_id, role_names, grid, section, wall_reach_m):
    """The private pictures. masks: ground-plan arrays (needs wall_dist); section: the set's growth block; grid: the pack's ground grid dict (x, y, dot_m)."""
    dot = grid['dot_m']
    foot = (section.get('wall_foot') or {})
    reach = float(foot.get('reach_m', 0.15))
    wd = masks['wall_dist'] * wall_reach_m if 'wall_dist' in masks else np.full(has_ground.shape, 9.0, np.float32)
    wall_strip = 1.0 - smooth(wd, 0.25 * reach, 1.2 * reach)
    gutter_strip = np.zeros_like(wall_strip)
    side = section.get('gutter_side')
    if side:
        ids = {name: i + 1 for i, name in enumerate(role_names)}
        mine, beside = ids.get(side['role']), ids.get(side['beside'])
        if mine is not None and beside is not None:
            from masks import ensure_cv2
            ensure_cv2()
            import cv2
            src = np.where(role_id == beside, 0, 1).astype(np.uint8)
            dist = cv2.distanceTransform(src, cv2.DIST_L2, 5) * dot
            lo, hi = float(side.get('from_m', 0.05)), float(side.get('reach_m', 0.9))
            ramp = smooth(dist, lo * 0.5, lo) * (1.0 - smooth(dist, hi * 0.7, hi))
            gutter_strip = np.where(role_id == mine, ramp, 0.0).astype(np.float32)
    return dict(wall_strip=(wall_strip * has_ground).astype(np.float32), gutter_strip=gutter_strip.astype(np.float32), has_ground=has_ground.astype(np.float32))


def make_image(name, sites):
    """A float Blender image holding the private pictures: R gutter_strip, G wall_strip, B has_ground (Non-Color)."""
    import bpy
    h, w = sites['wall_strip'].shape
    old = bpy.data.images.get(name)
    if old is not None:
        bpy.data.images.remove(old)
    image = bpy.data.images.new(name, w, h, alpha=True, float_buffer=True, is_data=True)
    buf = np.zeros((h, w, 4), np.float32)
    buf[..., 0] = sites['gutter_strip']
    buf[..., 1] = sites['wall_strip']
    buf[..., 2] = sites['has_ground']
    buf[..., 3] = 1.0
    image.alpha_mode = 'CHANNEL_PACKED'                      # (changing the colour space or alpha mode of a generated picture blanks it: set them first, the numbers last)
    image.pixels.foreach_set(buf.ravel())
    image.update()
    return image


# ---------------------------------------------------------------------------------------------------------------------------------------------- numbers for the calibration
def dot_centres(grid):
    x0, x1 = grid['x']
    y0, y1 = grid['y']
    dot = grid['dot_m']
    xs = x0 + dot * (np.arange(int(round((x1 - x0) / dot))) + 0.5)
    ys = y0 + dot * (np.arange(int(round((y1 - y0) / dot))) + 0.5)
    return xs, ys


def window_mask(grid, ground_z, has_ground, camera, distance, forward=None, cone_cos=-1.0):
    """True for ground dots within `distance` metres (straight line) of the camera position and, when a forward direction is given, inside the cone of half angle acos(cone_cos)
    round the camera's axis (the plants are made only there)."""
    xs, ys = dot_centres(grid)
    X, Y = np.meshgrid(xs, ys)
    rx, ry, rz = X - camera[0], Y - camera[1], ground_z - camera[2]
    d = np.sqrt(rx ** 2 + ry ** 2 + rz ** 2)
    ok = (d < distance) & has_ground
    if forward is not None:
        ok &= (rx * forward[0] + ry * forward[1] + rz * forward[2]) > cone_cos * np.maximum(d, 1e-6)
    return ok


def gates(masks, keep_soft=0.40, foot_from=0.35, foot_to=0.60, crown_from=0.30, crown_to=0.60):
    """The hard gates exactly as the scatter makes them (zero inside the zones), as an array."""
    g = np.ones(next(iter(masks.values())).shape, np.float32)
    if 'keepclear' in masks:
        g *= 1.0 - smooth(masks['keepclear'], 0.0, keep_soft)
    if 'footfall' in masks:
        g *= 1.0 - smooth(masks['footfall'], foot_from, foot_to)
    if 'crown' in masks:
        g *= 1.0 - smooth(masks['crown'], crown_from, crown_to)
    if 'above_water' in masks:
        g *= smooth(masks['above_water'], 0.03, 0.12)
    return g


def window_stats(masks, sites, grid, ground_z, window, strip_width_m=0.15, wall_gate=True):
    """Ground area (m2), wall-foot length (m) and gutter-side length (m) inside the window. Lengths are strip areas divided by the strip's width; only dots a plant may stand on
    (the hard gates above 0.5) count, so a share of 'wall-foot length' is a share of the length where a plant could stand."""
    dot2 = grid['dot_m'] ** 2
    ok = gates(masks) > 0.5
    area = float(window.sum() * dot2)
    wall_len = float(((sites['wall_strip'] > 0.5) & window & ok).sum() * dot2 / strip_width_m)
    gut_len = float(((sites['gutter_strip'] > 0.5) & window & ok).sum() * dot2 / 0.6)
    return dict(area_m2=area, wall_foot_m=wall_len, gutter_side_m=gut_len, gutter_strip_width_m=0.6)
