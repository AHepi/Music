# What this does: small helpers for the shader-toolbox experiments (run inside Blender 5.2.2).
#  - tree_from(name, body): builds a shader node group with input 'Vector' (the tile coordinate, u and v from 0 to 1) and outputs
#    'Colour' and 'Height' from a short function you write (body gets a NodeWriter called w; link something to w.nodes['out']).
#  - render_float(group, channel, size): renders one output of a group as exact floating-point numbers (a numpy array) so a
#    setting can be MEASURED (value range, seam jump, average) instead of only looked at.
#  - lit_scene(...): a flat 1 x 1 plane lit by a low sun, photographed from straight above, for bump / normal / wetness tests.
#  - save_png(array, path): write a picture.
import os, sys, math
import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.abspath(os.path.join(HERE, '..', '..', 'lib'))
sys.path.insert(0, LIB)
import bake_harness as bh   # noqa: E402
import recipe_tools as rt   # noqa: E402
import sweep_tools as st    # noqa: E402


def tree_from(name, body):
    tree, w = rt.make_group_tree(name, [('Vector', 'NodeSocketVector', (0, 0, 0))],
                                 [('Colour', 'NodeSocketColor'), ('Height', 'NodeSocketFloat')])
    body(w)
    return tree


def render_float(body, channel='Height', size=128, name='probe'):
    """Render one output of a group (built from the function `body`, see tree_from) as floats (rows top to bottom).
    Colour output returns an (h, w, 3) array. The scene is reset first, so the group is built after the reset."""
    scene, tile = bh.new_bake_scene(size)
    group = tree_from(name, body)
    material = bh.show_channel_material(group, channel)
    tile.data.materials.append(material)
    scene.view_settings.view_transform = 'Raw'
    scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.image_settings.color_depth = '32'
    scene.render.image_settings.color_mode = 'RGB'
    path = os.path.join(HERE, '_tmp_float.exr')
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(path, check_existing=False)
    image.colorspace_settings.name = 'Non-Color'
    w, h = image.size
    px = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(px)
    arr = px.reshape(h, w, 4)[::-1, :, :3]
    bpy.data.images.remove(image)
    return arr[..., 0].copy() if channel != 'Colour' else arr.copy()


def render_float_group(scene, tile, group, channel='Height'):
    """Same as render_float but for a group that was already built in the CURRENT scene (scene, tile from bh.new_bake_scene)."""
    material = bh.show_channel_material(group, channel)
    tile.data.materials.clear()
    tile.data.materials.append(material)
    scene.view_settings.view_transform = 'Raw'
    scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.image_settings.color_depth = '32'
    scene.render.image_settings.color_mode = 'RGB'
    path = os.path.join(HERE, '_tmp_float.exr')
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(path, check_existing=False)
    image.colorspace_settings.name = 'Non-Color'
    w, h = image.size
    px = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(px)
    arr = px.reshape(h, w, 4)[::-1, :, :3]
    bpy.data.images.remove(image)
    return arr[..., 0].copy() if channel != 'Colour' else arr.copy()


def seam_ratio(grey):
    inner = (np.abs(np.diff(grey, axis=1)).mean() + np.abs(np.diff(grey, axis=0)).mean()) / 2.0
    wrap = (np.abs(grey[:, 0] - grey[:, -1]).mean() + np.abs(grey[0, :] - grey[-1, :]).mean()) / 2.0
    return float(wrap / max(inner, 1e-9))


def save_png(array, path, srgb=False):
    array = np.clip(array, 0, 1)
    if array.ndim == 2:
        array = np.stack([array] * 3, axis=-1)
    bh.save_array_png(array, path, False)


def lit_scene(size=256, sun_angle_deg=35.0, sun_from_deg=225.0, samples=24):
    """Flat 1 x 1 plane (u = x, v = y), orthographic camera straight above, ONE sun low over the horizon coming from sun_from_deg
    (compass angle in the plane: 0 = from +x). Returns (scene, plane). The world is black so only the sun lights things."""
    scene, tile = bh.new_bake_scene(size)
    scene.cycles.samples = samples
    scene.cycles.max_bounces = 2
    scene.cycles.use_denoising = False
    scene.view_settings.view_transform = 'Standard'
    light_data = bpy.data.lights.new('sun', 'SUN')
    light_data.energy = 3.0
    light_data.angle = math.radians(1.0)
    sun = bpy.data.objects.new('sun', light_data)
    scene.collection.objects.link(sun)
    elevation = math.radians(sun_angle_deg)
    azimuth = math.radians(sun_from_deg)
    # a sun shines along its local -Z; point -Z toward the plane from the chosen side
    direction = (-math.cos(azimuth) * math.cos(elevation), -math.sin(azimuth) * math.cos(elevation), -math.sin(elevation))
    from mathutils import Vector
    sun.rotation_euler = Vector(direction).to_track_quat('-Z', 'Y').to_euler()
    return scene, tile


def render_png(scene, path, linear=False):
    scene.view_settings.view_transform = 'Raw' if linear else 'Standard'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
