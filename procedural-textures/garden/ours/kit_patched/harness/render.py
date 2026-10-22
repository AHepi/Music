# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# Small drawing helpers for the Blender side: EEVEE set up the way the plates are drawn (ray tracing on, shadow rays 4, steps 16), draw to a file, read a picture back as an
# array (Non-Color, so nothing changes the numbers), compare two pictures.
import os
import time

import bpy
import numpy as np


def eevee(w, h, samples, raytracing=True, bits=8, filter_size=1.5):
    s = bpy.context.scene
    s.render.engine = 'BLENDER_EEVEE'
    s.render.resolution_x, s.render.resolution_y = w, h
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = 'PNG'
    s.render.image_settings.color_mode = 'RGB'
    s.render.image_settings.color_depth = str(bits)
    s.render.dither_intensity = 0.0
    s.eevee.taa_render_samples = samples
    s.eevee.use_raytracing = raytracing
    s.eevee.shadow_ray_count, s.eevee.shadow_step_count = 4, 16
    if hasattr(s.eevee, 'shadow_pool_size') and w > 1080:
        s.eevee.shadow_pool_size = '1024'
        s.eevee.shadow_resolution_scale = min(1.0, 1080 / w)
    s.render.filter_size = filter_size


def draw(path, w, h, samples, camera=None, raytracing=True, bits=16):
    """Draws the scene to a PNG (16 bit by default so comparisons are exact). Returns the seconds."""
    s = bpy.context.scene
    if camera is not None:
        s.camera = camera
    eevee(w, h, samples, raytracing, bits)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    s.render.filepath = path
    bpy.context.view_layer.update()
    t = time.time()
    bpy.ops.render.render(write_still=True)
    return time.time() - t


def read(path):
    image = bpy.data.images.load(path)
    image.colorspace_settings.name = 'Non-Color'
    a = np.array(image.pixels[:], dtype=np.float32).reshape(image.size[1], image.size[0], 4)[..., :3]
    bpy.data.images.remove(image)
    return a


def compare(a, b, step=1.0 / 255.0):
    d = np.abs(a - b)
    return dict(dots=int(d.shape[0] * d.shape[1]), max_diff=float(d.max()), mean_diff=float(d.mean()), share_over_one_step=float((d.max(axis=2) > step + 1e-6).mean()),
                share_changed=float((d.max(axis=2) > 0).mean()))


_PLAIN_KEEP = {}


def plain_light(on):
    """Raw numbers: no colour look, no dither, the world switched to black (a sky would otherwise read as a number). Call plain_light(False) to put everything back."""
    s = bpy.context.scene
    v = s.view_settings
    world = s.world
    bg = world.node_tree.nodes.get('Background') if world is not None and world.node_tree is not None else None
    if on:
        _PLAIN_KEEP['view'] = (v.view_transform, v.look, v.exposure, v.gamma, s.render.dither_intensity)
        v.view_transform, v.look, v.exposure, v.gamma = 'Raw', 'None', 0.0, 1.0
        s.render.dither_intensity = 0.0
        if bg is not None:
            _PLAIN_KEEP['bg'] = (tuple(bg.inputs['Color'].default_value), bg.inputs['Strength'].default_value)
            bg.inputs['Strength'].default_value = 0.0
        _PLAIN_KEEP['world_black'] = bg is not None
    else:
        keep = _PLAIN_KEEP.pop('view', None)
        if keep:
            v.view_transform, v.look, v.exposure, v.gamma, s.render.dither_intensity = keep
        if bg is not None and 'bg' in _PLAIN_KEEP:
            color, strength = _PLAIN_KEEP.pop('bg')
            bg.inputs['Color'].default_value = color
            bg.inputs['Strength'].default_value = strength
