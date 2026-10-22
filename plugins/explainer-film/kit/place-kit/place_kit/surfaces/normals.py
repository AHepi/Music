"""What this does: turns height pictures into REAL normal maps that point the right way, puts them into Blender as Non-Color
images, wires the Normal Map node, and checks the direction. The numpy parts need no Blender (so they are tested without it);
the functions that make images or nodes import bpy only when called.

The convention used everywhere (the one Blender's Normal Map node expects): OpenGL, green = up the picture (+V), red = to the
right (+U), tangent space, stored in a Non-Color image. A bump that is WHITE in the height picture must be lit on the side that faces
the light. Rows of a numpy picture run from the TOP; rows of a Blender image run from the BOTTOM (the functions here flip for you).

Traps this file already steps around (each cost a day once):
  * Blender 5.2 wipes a generated image to black if its colour space is changed AFTER the pixels are written: the colour space is set
    right after images.new and before the pixels.
  * A normal map saved as JPEG or left as sRGB colour is silently wrong.
  * A flipped green channel (DirectX convention) looks plausible at a glance; direction_correlation catches it against the height.
A concrete example: n = height_to_normal(h, 1.0); direction_correlation(to_rgb(n), h) gives {'x': +0.99, 'y': +0.99}; with the green
channel flipped the 'y' value is about -0.99.
"""
import struct
import zlib

import numpy as np


def height_to_normal(h, strength=1.0, tile=True):
    """OpenGL tangent-space normals (values -1..1, shape (rows, cols, 3)) from a height picture whose slope is in pixel units
    (see heights.calibrate_height). tile=True uses wrap-around differences, so a seamless picture gives a seamless map."""
    h = np.asarray(h, dtype=np.float32)
    if h.ndim == 3:
        h = h[..., :3].mean(axis=2)
    if tile:
        dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5            # per column, to the right (+U)
        dy_row = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5        # per row, DOWN the picture (-V)
    else:
        dx = np.gradient(h, axis=1)
        dy_row = np.gradient(h, axis=0)
    nx = -dx * strength
    ny = +dy_row * strength            # +V is up the picture and rows go down, so the sign flips: this is OpenGL's green
    nz = np.ones_like(nx)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / length, ny / length, nz / length], axis=-1).astype(np.float32)


def to_rgb(normals):
    """Normals (-1..1) as a picture (0..1)."""
    return np.clip(normals * 0.5 + 0.5, 0.0, 1.0).astype(np.float32)


def from_rgb(rgb):
    """A picture (0..1) back to normals (-1..1), not normalised."""
    return np.asarray(rgb, dtype=np.float32)[..., :3] * 2.0 - 1.0


def flip_green(normals):
    flipped = np.array(normals, copy=True)
    flipped[..., 1] *= -1.0
    return flipped


def mean_rgb(rgb):
    return [float(v) for v in np.asarray(rgb, dtype=np.float32)[..., :3].reshape(-1, 3).mean(axis=0)]


def direction_correlation(rgb, height):
    """How well a normal map (picture 0..1, rows from the top) agrees with the height picture it should come from (same rows, same size):
    the correlation of the red channel's slope with the height's slope along +U, and of the green channel's with the slope along +V.
    +1 means it points the right way; about -1 means that axis is flipped. An axis with almost no slope returns the text 'not informative'
    (a map with no slope on one axis says nothing about that axis)."""
    from_height = height_to_normal(height, 1.0, tile=True)
    normals = from_rgb(rgb)
    result = {}
    for axis, name in ((0, 'x'), (1, 'y')):
        expected = from_height[..., axis].ravel()
        given = normals[..., axis].ravel()
        if np.abs(expected).mean() < 0.02 or np.abs(given).mean() < 0.02 * 0.5:
            result[name] = 'not informative'
            continue
        e = expected - expected.mean()
        g = given - given.mean()
        denominator = float(np.sqrt((e * e).sum() * (g * g).sum())) + 1e-12
        result[name] = float((e * g).sum() / denominator)
    return result


def structure_report(rgb):
    """Mean red, green, blue of a normal map: a good map is centred (about 0.5, 0.5) and mostly blue (flat is 1.0)."""
    return {'mean_rgb': mean_rgb(rgb)}


def write_png(path, rgb8):
    """Writes an 8-bit RGB or RGBA picture (rows from the top, uint8) as a PNG with no Pillow: zlib and struct only."""
    rgb8 = np.ascontiguousarray(rgb8, dtype=np.uint8)
    rows, cols = rgb8.shape[:2]
    channels = rgb8.shape[2] if rgb8.ndim == 3 else 1
    colour_type = {1: 0, 3: 2, 4: 6}[channels]
    raw = b''.join(b'\x00' + rgb8[row].tobytes() for row in range(rows))

    def chunk(kind, payload):
        body = kind + payload
        return struct.pack('>I', len(payload)) + body + struct.pack('>I', zlib.crc32(body) & 0xffffffff)

    data = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', cols, rows, 8, colour_type, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))
    with open(path, 'wb') as handle:
        handle.write(data)


# ------------------------------------------------------------------ Blender side (bpy is imported when these are called)
def make_image(name, rgb, non_colour=True, float_buffer=False, replace=True):
    """Puts a picture (0..1, rows from the top, shape (rows, cols, 3 or 4)) into Blender as an image called `name`. The colour space is set
    BEFORE the pixels are written (Blender 5.2 wipes the image to black otherwise). Replaces an image of the same name."""
    import bpy
    rgb = np.asarray(rgb, dtype=np.float32)
    rows, cols = rgb.shape[:2]
    old = bpy.data.images.get(name)
    if old is not None and replace:
        bpy.data.images.remove(old)
    image = bpy.data.images.new(name, cols, rows, alpha=False, float_buffer=float_buffer)
    image.colorspace_settings.name = 'Non-Color' if non_colour else 'sRGB'
    if rgb.shape[2] == 3:
        rgb = np.concatenate([rgb, np.ones((rows, cols, 1), np.float32)], axis=2)
    image.pixels.foreach_set(rgb[::-1].ravel())                  # Blender rows start at the bottom
    image.update()
    image['pk_made'] = 1
    return image


def make_normal_image(name, normals):
    """A Non-Color image from normals (-1..1), flagged as made by the kit and as OpenGL."""
    image = make_image(name, to_rgb(normals), non_colour=True)
    image['pk_convention'] = 'opengl'
    return image


def make_height_image(name, height01):
    """A Non-Color picture of a height picture stretched to 0..1 (grey)."""
    h = np.asarray(height01, dtype=np.float32)
    return make_image(name, np.stack([h, h, h], axis=-1), non_colour=True)


def image_to_array(image):
    """A Blender image as (rows from the top, cols, 4) float32."""
    cols, rows = image.size
    flat = np.empty(cols * rows * image.channels, dtype=np.float32)
    image.pixels.foreach_get(flat)
    array = flat.reshape(rows, cols, image.channels)
    if image.channels == 3:
        array = np.concatenate([array, np.ones((rows, cols, 1), np.float32)], axis=2)
    return array[::-1]


def pack(image):
    """Packs the image into the .blend so it travels with the file (a generated image is lost on save otherwise)."""
    try:
        image.pack()
    except RuntimeError:
        pass
    return image


def add_normal_map_nodes(material, image, uv_map, strength=1.0, scale=(1, 1, 1), principled=None, vector_node=None):
    """UV Map -> Mapping -> Image (Non-Color, Repeat, Cubic) -> Normal Map (Tangent, uv_map set) -> the Principled node's Normal.
    Returns the Normal Map node. An existing link into the Normal input is replaced."""
    tree = material.node_tree
    nodes, links = tree.nodes, tree.links
    principled = principled or next(n for n in nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    uv = nodes.new('ShaderNodeUVMap')
    uv.uv_map = uv_map
    mapping = nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = scale
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = image
    texture.interpolation = 'Cubic'
    texture.extension = 'REPEAT'
    if image.colorspace_settings.name != 'Non-Color':
        image.colorspace_settings.name = 'Non-Color'          # only when it is wrong: setting it again wipes a generated image
    normal_map = nodes.new('ShaderNodeNormalMap')
    normal_map.space = 'TANGENT'
    normal_map.uv_map = uv_map
    normal_map.inputs['Strength'].default_value = strength
    links.new(uv.outputs['UV'], mapping.inputs['Vector'])
    links.new(mapping.outputs['Vector'], texture.inputs['Vector'])
    links.new(texture.outputs['Color'], normal_map.inputs['Color'])
    links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
    for node, label in ((uv, 'PK UV'), (mapping, 'PK Mapping'), (texture, 'PK Normal Image'), (normal_map, 'PK Normal Map')):
        node.name = node.label = label
    return normal_map
