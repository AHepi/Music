# What this does: builds the "world around the mine" for the coal-mine scene: (1) a painted dusk sky picture (4096 x 2048,
# clumpy teal-grey clouds, a band of orange glow along the horizon toward the right-back) that is drawn here with numpy,
# saved as a PNG in out/, and set as the scene's world; (2) three rings of big dark hills far away, all the way around,
# lighter and bluer the farther they are; (3) a pit village of terraced brick houses with slate roofs, chimneys with pots,
# doors, windows (some glowing warm), a lamp-lit street with lamp posts, standing on the right-back of the mine;
# (4) the lights: a low warm orange sun from the right-back and a cool soft fill.
# Use: in a Blender script, sys.path.insert(0, ".../lib") and ".../modules", import village_and_sky, then call
#      village_and_sky.build()   -> {'objects': [...], 'notes': '...'}
# Everything the assembler may want to tune is a named setting near the top of this file, or a named node / light in the scene.
import math
import os
import struct
import sys
import time
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MINE_FOLDER = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(MINE_FOLDER, 'lib'))
try:
    import bpy
    import mine_common as mc
except ImportError:          # lets the sky painter be tried outside Blender
    bpy = None
    mc = None

# --------------------------------------------------------------------------------------------------------------------
# Settings (plain names, easy to change)
# --------------------------------------------------------------------------------------------------------------------
SKY_PICTURE_PATH = os.path.join(MINE_FOLDER, 'out', 'village_and_sky_dusk_sky_4096x2048.png')
SKY_PICTURE_VERSION = 6                      # raise this number when the painting code changes, so an old picture is redrawn
GLOW_DIRECTION_DEGREES = 50.0                # where the sunset glow sits: compass-style angle, 0 = +Y (away from camera), 90 = +X (right)
SUN_ELEVATION_DEGREES = 6.0                  # how far above the horizon the low sun is
SUN_COLOUR = (1.0, 0.50, 0.19)
SUN_STRENGTH = 8.0
FILL_COLOUR = (0.52, 0.68, 1.0)
FILL_STRENGTH = 3.0
FILL_FROM_DEGREES = 232.0                    # the cool fill shines from the front-left (compass angle, like the glow direction)
SKY_LIGHT_STRENGTH = 4.0                     # the strength of the world (sky picture) light
RECOMMENDED_EXPOSURE = 0.0                   # extra exposure (stops) the assembler should start from, with AgX


# --------------------------------------------------------------------------------------------------------------------
# 1. The painted sky
# --------------------------------------------------------------------------------------------------------------------
def _smooth(low, high, value):
    t = np.clip((value - low) / (high - low), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _fade(t):
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


class _NoiseMaker:
    """Soft blotchy noise that wraps round the full circle of the sky. One lattice of random numbers per call."""

    def __init__(self, seed):
        self.generator = np.random.default_rng(seed)

    def lattice(self, cells_x, cells_y):
        return self.generator.random((cells_y + 2, cells_x)).astype(np.float32)

    @staticmethod
    def sample(lattice, cells_x, cells_y, across, down):
        """across, down: 0..1 coordinates (arrays of the same shape). across wraps round the circle."""
        x = across * cells_x
        y = down * cells_y
        ix = np.floor(x).astype(np.int64)
        iy = np.floor(y).astype(np.int64)
        tx = _fade((x - ix).astype(np.float32))
        ty = _fade((y - iy).astype(np.float32))
        ix0 = ix % cells_x
        ix1 = (ix + 1) % cells_x
        top = lattice[iy, ix0] * (1.0 - tx) + lattice[iy, ix1] * tx
        bottom = lattice[iy + 1, ix0] * (1.0 - tx) + lattice[iy + 1, ix1] * tx
        return top * (1.0 - ty) + bottom * ty

    def fbm(self, across, down, cells_x, cells_y, octaves=6, persistence=0.55, warp=None):
        """Layered noise, 0..1. warp = (strength_across, strength_down) bends the coordinates for swirly painted shapes."""
        total = np.zeros(across.shape, dtype=np.float32)
        weight = 1.0
        norm = 0.0
        if warp is not None:
            wl_x = self.lattice(max(3, cells_x // 2), max(2, cells_y // 2))
            wl_y = self.lattice(max(3, cells_x // 2), max(2, cells_y // 2))
            across = across + warp[0] * (self.sample(wl_x, max(3, cells_x // 2), max(2, cells_y // 2), across, down) - 0.5)
            down = np.clip(down + warp[1] * (self.sample(wl_y, max(3, cells_x // 2), max(2, cells_y // 2), across, down) - 0.5), 0.0, 0.9999)
        for octave in range(octaves):
            cx, cy = cells_x * 2 ** octave, cells_y * 2 ** octave
            total += weight * self.sample(self.lattice(cx, cy), cx, cy, across, np.clip(down, 0.0, 0.9999))
            norm += weight
            weight *= persistence
        return total / norm


def _mix(a, b, t):
    return a + (b - a) * t[..., None]


def _gradient(position, stops):
    """Colour along a list of (position, (r, g, b)) stops, for an array of positions."""
    positions = np.array([s[0] for s in stops], dtype=np.float32)
    colours = np.array([s[1] for s in stops], dtype=np.float32)
    return np.stack([np.interp(position, positions, colours[:, k]) for k in range(3)], axis=-1).astype(np.float32)


def _stretch_to(picture, height, width):
    """Smoothly enlarges a (h, w, 3) picture to (height, width, 3); the left and right edges wrap round the circle."""
    h, w = picture.shape[:2]
    ys = (np.arange(height, dtype=np.float32) + 0.5) / height * h - 0.5
    xs = (np.arange(width, dtype=np.float32) + 0.5) / width * w - 0.5
    y0 = np.clip(np.floor(ys).astype(np.int64), 0, h - 2)
    ty = np.clip(ys - y0, 0.0, 1.0)[:, None, None].astype(np.float32)
    x0 = np.floor(xs).astype(np.int64)
    tx = (xs - x0)[None, :, None].astype(np.float32)
    x0w, x1w = x0 % w, (x0 + 1) % w
    top = picture[y0][:, x0w] * (1 - tx) + picture[y0][:, x1w] * tx
    bottom = picture[y0 + 1][:, x0w] * (1 - tx) + picture[y0 + 1][:, x1w] * tx
    return top * (1 - ty) + bottom * ty


def paint_sky(width=4096, height=2048, seed=7, glow_direction_degrees=GLOW_DIRECTION_DEGREES):
    """Returns a (height, width, 3) float picture of a dusk sky (display colours, 0..1). Row 0 is the zenith.
    Columns run round the compass: picture column u = 0.25 + angle/360, where angle 0 = +Y and 90 = +X (Blender's layout).
    The big shapes are worked out at half size (quicker) and enlarged; brush marks are added at full size."""
    noise = _NoiseMaker(seed)
    full_width, full_height = width, height
    width, height = width // 2, height // 2
    column = (np.arange(width, dtype=np.float32) + 0.5) / width
    row = (np.arange(height, dtype=np.float32) + 0.5) / height
    compass = np.mod((column - 0.25) * 360.0, 360.0)                      # degrees, 0 = +Y
    elevation = 90.0 - row * 180.0                                        # degrees above the horizon
    angle_from_glow = np.mod(compass - glow_direction_degrees + 180.0, 360.0) - 180.0
    across, down = np.meshgrid(column, row)                               # (height, width)
    el = np.broadcast_to(elevation[:, None], (height, width))
    dg = np.broadcast_to(angle_from_glow[None, :], (height, width))
    ones3 = np.ones((height, width, 3), dtype=np.float32)

    glow_across = np.exp(-(dg / 58.0) ** 2)                               # 1 right at the glow, fading round the horizon
    glow_wide = 0.14 + 0.86 * glow_across

    # --- clear sky colours (display values): yellow rim -> orange -> pale green-yellow -> teal -> dark teal -> dark top
    near_glow = _gradient(el, [(-90, (0.07, 0.08, 0.10)), (-6, (0.12, 0.10, 0.10)), (-1.5, (0.82, 0.44, 0.15)), (0.0, (1.0, 0.72, 0.32)),
                               (2.5, (1.0, 0.64, 0.24)), (6.0, (0.95, 0.66, 0.34)), (11.0, (0.70, 0.72, 0.54)), (19.0, (0.40, 0.60, 0.58)),
                               (34.0, (0.25, 0.44, 0.50)), (58.0, (0.15, 0.29, 0.35)), (90.0, (0.10, 0.20, 0.25))])
    far_from_glow = _gradient(el, [(-90, (0.05, 0.06, 0.08)), (-6, (0.08, 0.08, 0.10)), (-1.5, (0.40, 0.29, 0.22)), (0.0, (0.60, 0.44, 0.31)),
                                   (3.0, (0.52, 0.48, 0.40)), (8.0, (0.40, 0.54, 0.54)), (16.0, (0.32, 0.51, 0.55)), (30.0, (0.23, 0.42, 0.49)),
                                   (58.0, (0.15, 0.29, 0.35)), (90.0, (0.10, 0.20, 0.25))])
    sky = _mix(far_from_glow, near_glow, glow_wide)

    # --- main clumpy painted cloud masses (bent by a slow warp so they look brushed, not machine noise)
    density = noise.fbm(across, down * 0.93, 15, 8, octaves=7, persistence=0.56, warp=(0.05, 0.035))
    detail = noise.fbm(across, down, 90, 50, octaves=3, persistence=0.5)
    density = 0.5 + (density - 0.5) * 1.35 + (detail - 0.5) * 0.12
    density = density + 0.16 * _smooth(2.0, 30.0, el) - 0.20 * glow_across * (1.0 - _smooth(0.0, 11.0, el)) * _smooth(-2.0, 3.0, el)
    cloud_mask = _smooth(0.44, 0.56, density) * _smooth(-1.0, 2.0, el)                             # soft edged masses
    thick = _smooth(0.55, 0.85, density)

    # lit-from-the-horizon shading: where the cloud edge faces the glow (below it, or toward it sideways) it catches the light
    def shifted(field, shift_rows, shift_columns):
        return np.roll(np.roll(field, shift_rows, axis=0), shift_columns, axis=1)

    below = shifted(density, -11, 0)                                      # picture row below = lower in the sky
    toward_glow = np.where(dg < 0, shifted(density, 0, -13), shifted(density, 0, 13))
    lit = np.clip((density - below) * 5.0, 0.0, 1.0) * 0.85 + np.clip((density - toward_glow) * 3.5, 0.0, 1.0) * 0.6
    lit = np.clip(lit, 0.0, 1.0)
    glow_weight = glow_wide * np.exp(-np.maximum(el, 0.0) / 24.0) * (1.0 - 0.5 * _smooth(20.0, 55.0, el))

    body = _gradient(el, [(0, (0.20, 0.31, 0.35)), (12, (0.22, 0.35, 0.40)), (30, (0.17, 0.29, 0.34)), (55, (0.11, 0.19, 0.24)), (90, (0.08, 0.14, 0.18))])
    body = body * (1.0 - 0.38 * thick[..., None])
    rim_colour = _gradient(el, [(0, (1.0, 0.62, 0.24)), (6, (0.98, 0.62, 0.32)), (14, (0.78, 0.70, 0.52)), (26, (0.52, 0.70, 0.70)), (50, (0.36, 0.54, 0.60)), (90, (0.28, 0.44, 0.50))])
    clouds = _mix(body, rim_colour, np.clip(lit * glow_weight * 1.2, 0.0, 1.0))
    # teal-blue lighter tops: the open sky colour shining a little on the cloud's upper side
    tops = np.clip((shifted(density, 11, 0) - density) * 3.0, 0.0, 1.0)
    top_colour = np.array([0.42, 0.60, 0.63], dtype=np.float32) * (1.0 - 0.45 * _smooth(20.0, 60.0, el))[..., None]
    clouds = _mix(clouds, top_colour, tops * 0.5 * (1.0 - 0.8 * glow_weight))
    sky = _mix(sky, clouds, cloud_mask * (0.90 - 0.2 * _smooth(-1.0, 3.0, -el)))

    # --- dark storm clouds high up (big darker masses, a few clear teal gaps between them)
    storm_density = noise.fbm(across, down, 6, 4, octaves=6, persistence=0.58, warp=(0.07, 0.05))
    storm_mask = _smooth(0.48, 0.58, storm_density + 0.26 * _smooth(16.0, 58.0, el) - 0.28) * _smooth(14.0, 38.0, el)
    storm_below = shifted(storm_density, -13, 0)
    storm_lit = np.clip((storm_density - storm_below) * 4.0, 0.0, 1.0)
    storm_colour = _gradient(el, [(10, (0.17, 0.26, 0.30)), (30, (0.13, 0.21, 0.25)), (60, (0.08, 0.13, 0.16)), (90, (0.06, 0.10, 0.12))])
    storm_colour = _mix(storm_colour, np.array([0.40, 0.52, 0.54], dtype=np.float32) * np.ones_like(storm_colour), storm_lit * 0.45 * glow_wide * (1.0 - _smooth(25.0, 60.0, el)))
    sky = _mix(sky, storm_colour, storm_mask * 0.90)

    # --- long flat dark cloud strips lying just above the horizon, lit orange along their undersides
    strip_density = noise.fbm(across, down * 0.5 + 0.2, 20, 30, octaves=5, persistence=0.52, warp=(0.04, 0.0))
    strip_zone = _smooth(0.5, 3.0, el) * (1.0 - _smooth(9.0, 17.0, el))
    strip_mask = _smooth(0.52, 0.62, strip_density - 0.08 * (1.0 - glow_wide) + 0.04) * strip_zone
    strip_below = shifted(strip_density, -5, 0)
    strip_lit = np.clip((strip_density - strip_below) * 7.0, 0.0, 1.0)
    strip_colour = _gradient(el, [(0, (0.17, 0.23, 0.29)), (8, (0.15, 0.23, 0.29)), (17, (0.14, 0.23, 0.29))])
    strip_colour = _mix(strip_colour, np.array([0.98, 0.60, 0.22], dtype=np.float32) * np.ones_like(strip_colour), strip_lit * glow_wide ** 1.2)
    sky = _mix(sky, strip_colour, strip_mask * 0.93)

    # --- a thin bright haze hugging the horizon in the glow direction, then the dark band under the horizon
    haze = np.exp(-np.maximum(el, 0.0) / 3.2) * glow_across * 0.30 * _smooth(-3.0, 0.5, el)
    sky = _mix(sky, np.array([1.0, 0.74, 0.36], dtype=np.float32) * ones3, haze)
    below_horizon = _smooth(-0.8, -5.0, el)
    sky = _mix(sky, np.array([0.07, 0.08, 0.10], dtype=np.float32) * ones3, below_horizon)

    # --- enlarge, then painterly finishing: soft brush marks, and soft flattening of the shades into steps like gouache
    sky = _stretch_to(np.clip(sky, 0.0, 1.0).astype(np.float32), full_height, full_width)
    width, height = full_width, full_height
    column = (np.arange(width, dtype=np.float32) + 0.5) / width
    row = (np.arange(height, dtype=np.float32) + 0.5) / height
    across, down = np.meshgrid(column, row)
    brush_a = noise.fbm(across, down, 420, 120, octaves=2, persistence=0.5)
    brush_b = noise.fbm(across, down, 200, 300, octaves=2, persistence=0.5)
    brush = (brush_a - 0.5) * 0.05 + (brush_b - 0.5) * 0.04
    sky = sky * (1.0 + brush[..., None])
    luminance = sky @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    levels = 16.0
    scaled = luminance * levels
    flattened = (np.floor(scaled) + _smooth(0.2, 0.8, scaled - np.floor(scaled))) / levels
    ratio = flattened / np.maximum(luminance, 1e-4)
    sky = sky + (sky * ratio[..., None] - sky) * 0.5
    return np.clip(sky, 0.0, 1.0)


def write_png_rgb(path, picture):
    """Saves a (height, width, 3) float picture (0..1) as an 8-bit PNG, with a tiny bit of noise so smooth shades do not band."""
    generator = np.random.default_rng(5)
    height, width, _ = picture.shape
    bytes_picture = np.clip(picture * 255.0 + generator.random(picture.shape, dtype=np.float32) - 0.5, 0, 255).astype(np.uint8)
    # PNG "sub" filter on every row compresses smooth pictures much better
    filtered = np.empty((height, width * 3 + 1), dtype=np.uint8)
    filtered[:, 0] = 1
    flat = bytes_picture.reshape(height, width * 3)
    filtered[:, 1:] = flat
    filtered[:, 1 + 3:] = (flat[:, 3:].astype(np.int16) - flat[:, :-3].astype(np.int16)).astype(np.uint8)

    def chunk(kind, data):
        body = kind + data
        return struct.pack('>I', len(data)) + body + struct.pack('>I', zlib.crc32(body) & 0xffffffff)

    with open(path, 'wb') as handle:
        handle.write(b'\x89PNG\r\n\x1a\n')
        handle.write(chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)))
        handle.write(chunk(b'IDAT', zlib.compress(filtered.tobytes(), 6)))
        handle.write(chunk(b'IEND', b''))


def make_sky_picture(path=SKY_PICTURE_PATH, force=False):
    """Draws the sky picture unless a current one is already on disk. Returns the path."""
    marker = path + '.version'
    if not force and os.path.exists(path) and os.path.exists(marker):
        with open(marker) as handle:
            if handle.read().strip() == str(SKY_PICTURE_VERSION) + ':' + str(GLOW_DIRECTION_DEGREES):
                return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    started = time.time()
    picture = paint_sky()
    write_png_rgb(path, picture)
    with open(marker, 'w') as handle:
        handle.write(str(SKY_PICTURE_VERSION) + ':' + str(GLOW_DIRECTION_DEGREES))
    if mc is not None:
        mc.say(f'painted the dusk sky picture in {time.time() - started:.1f} s -> {path}')
    return path


# --------------------------------------------------------------------------------------------------------------------
# 2. The world (sky light) and the lights
# --------------------------------------------------------------------------------------------------------------------
def compass_to_direction(compass_degrees):
    """Compass angle (0 = +Y, 90 = +X) -> flat unit vector (x, y)."""
    a = math.radians(compass_degrees)
    return math.sin(a), math.cos(a)


def build_world(picture_path, strength=SKY_LIGHT_STRENGTH, glow_boost=1.5):
    """Sets scene.world to the painted sky. Nodes you can tune afterwards by name: 'Sky strength' (Background node, input
    Strength), 'Sky turn' (Mapping node, Rotation Z in radians; if you turn the sky also turn the sun), 'Glow boost' (Math node)."""
    scene = bpy.context.scene
    world = bpy.data.worlds.new('Dusk sky')
    scene.world = world
    world.use_nodes = True
    tree = world.node_tree
    tree.nodes.clear()
    nodes, links = tree.nodes, tree.links
    output = nodes.new('ShaderNodeOutputWorld'); output.location = (900, 0)
    background = nodes.new('ShaderNodeBackground'); background.name = 'Sky strength'; background.label = 'Sky strength'
    background.location = (700, 0)
    background.inputs['Strength'].default_value = strength
    links.new(background.outputs['Background'], output.inputs['Surface'])
    coords = nodes.new('ShaderNodeTexCoord'); coords.location = (-700, 0)
    mapping = nodes.new('ShaderNodeMapping'); mapping.name = 'Sky turn'; mapping.label = 'Sky turn'; mapping.location = (-500, 0)
    links.new(coords.outputs['Generated'], mapping.inputs['Vector'])
    image = bpy.data.images.load(picture_path, check_existing=True)
    image.colorspace_settings.name = 'sRGB'
    environment = nodes.new('ShaderNodeTexEnvironment'); environment.name = 'Sky picture'; environment.label = 'Sky picture'
    environment.image = image
    environment.interpolation = 'Cubic'
    environment.location = (-250, 0)
    links.new(mapping.outputs['Vector'], environment.inputs['Vector'])
    # a little extra kick for the brightest (glow) parts, so the horizon glow lights the land warmly: colour * (1 + boost * brightness^3)
    to_grey = nodes.new('ShaderNodeRGBToBW'); to_grey.location = (0, -200)
    cube = nodes.new('ShaderNodeMath'); cube.operation = 'POWER'; cube.inputs[1].default_value = 3.0; cube.location = (150, -200)
    boost = nodes.new('ShaderNodeMath'); boost.operation = 'MULTIPLY_ADD'; boost.name = 'Glow boost'; boost.label = 'Glow boost'
    boost.inputs[1].default_value = glow_boost; boost.inputs[2].default_value = 1.0; boost.location = (300, -200)
    scale = nodes.new('ShaderNodeVectorMath'); scale.operation = 'SCALE'; scale.location = (500, 0)
    links.new(environment.outputs['Color'], to_grey.inputs['Color'])
    links.new(to_grey.outputs['Val'], cube.inputs[0])
    links.new(cube.outputs['Value'], boost.inputs[0])
    links.new(environment.outputs['Color'], scale.inputs[0])
    links.new(boost.outputs['Value'], scale.inputs['Scale'])
    links.new(scale.outputs['Vector'], background.inputs['Color'])
    return world


def make_sun(name, compass_from_degrees, elevation_degrees, colour, strength, angle_degrees):
    """A sun light shining FROM the compass direction (0 = +Y, 90 = +X) at the given height above the horizon."""
    light = bpy.data.lights.new(name, 'SUN')
    light.energy = strength
    light.color = colour
    light.angle = math.radians(angle_degrees)
    obj = bpy.data.objects.new(name, light)
    bpy.context.scene.collection.objects.link(obj)
    fx, fy = compass_to_direction(compass_from_degrees)
    ce, se = math.cos(math.radians(elevation_degrees)), math.sin(math.radians(elevation_degrees))
    travel = mc.Vector((-fx * ce, -fy * ce, -se))                           # the light travels away from where it comes from
    obj.rotation_euler = travel.to_track_quat('-Z', 'Y').to_euler()
    obj.location = (-fx * ce * 30.0, -fy * ce * 30.0, se * 30.0)           # (a sun's position does not matter; this just parks it)
    return obj


def build_lights():
    sun = make_sun('Village low sun', GLOW_DIRECTION_DEGREES, SUN_ELEVATION_DEGREES, SUN_COLOUR, SUN_STRENGTH, 2.0)
    fill = make_sun('Village cool fill', FILL_FROM_DEGREES, 38.0, FILL_COLOUR, FILL_STRENGTH, 25.0)
    return [sun, fill]


# --------------------------------------------------------------------------------------------------------------------
# 3. The hills: three rings of big smooth hills all the way round, lighter and bluer the farther away
# --------------------------------------------------------------------------------------------------------------------
HILL_CENTRE = (4.0, 4.0)
HILL_RINGS = [
    # name, inner edge, crest distance, outer edge (metres from the centre), lowest crest, highest crest (metres), colour, mist, seed
    dict(name='Near hills', r_in=45.0, r_crest=140.0, r_out=250.0, low=11.0, high=27.0, colour=(0.050, 0.062, 0.078), mist=0.22, seed=21),
    dict(name='Middle hills', r_in=190.0, r_crest=290.0, r_out=450.0, low=24.0, high=46.0, colour=(0.13, 0.17, 0.22), mist=0.40, seed=22),
    dict(name='Far hills', r_in=360.0, r_crest=520.0, r_out=800.0, low=36.0, high=66.0, colour=(0.30, 0.38, 0.46), mist=0.55, seed=23),
]
HAZE_COLOUR = (0.24, 0.30, 0.36)
HAZE_WARM_COLOUR = (0.62, 0.38, 0.20)


def skyline(theta, seed, harmonics=34):
    """A bumpy outline round the full circle (0..1): many gentle waves with random phases, plus a few pointed shoulders and peaks."""
    generator = np.random.default_rng(seed)
    total = np.zeros_like(theta)
    for k in range(2, harmonics):
        total += (1.0 / k ** 1.05) * np.sin(k * theta + generator.uniform(0, 2 * np.pi))
    total = (total - total.min()) / (total.max() - total.min())
    peaks = np.zeros_like(theta)
    for _ in range(9):
        centre = generator.uniform(0, 2 * np.pi)
        width = generator.uniform(0.04, 0.13)
        height = generator.uniform(0.25, 0.6)
        distance = np.abs(np.mod(theta - centre + np.pi, 2 * np.pi) - np.pi)
        peaks = np.maximum(peaks, height * np.exp(-(distance / width) ** 1.25))
    rough = 0.012 * np.sin(theta * 61 + generator.uniform(0, 6)) + 0.008 * np.sin(theta * 97 + generator.uniform(0, 6))
    mixed = 0.62 * total + 0.55 * peaks + rough
    return np.clip((mixed - mixed.min()) / (mixed.max() - mixed.min()), 0.0, 1.0)


def make_hill_ring(ring, collection_name, steps_round=720, steps_out=30):
    theta = np.linspace(0.0, 2 * np.pi, steps_round, endpoint=False)
    outline = skyline(theta, ring['seed'])
    outline = outline ** 0.9
    height_here = ring['low'] + (ring['high'] - ring['low']) * outline
    crest_wobble = ring['r_crest'] * (1.0 + 0.10 * (skyline(theta + 1.7, ring['seed'] + 50) - 0.5))
    t = np.linspace(0.0, 1.0, steps_out + 1)
    radius = ring['r_in'] + (ring['r_out'] - ring['r_in']) * t ** 1.15
    grid_theta, grid_r = np.meshgrid(theta, radius, indexing='ij')                       # (round, out)
    crest = crest_wobble[:, None]
    rise = _smooth(0.0, 1.0, (grid_r - ring['r_in']) / (crest - ring['r_in']))
    fall = _smooth(0.0, 1.0, (grid_r - crest) / (ring['r_out'] - crest))
    profile = np.where(grid_r < crest, rise, 1.0 - 0.72 * fall)
    # gullies and shoulders so the slopes are not plain
    seed_shift = ring['seed'] * 0.7
    wobble = 1.0 + 0.10 * np.sin(grid_theta * 23 + grid_r * 0.035) + 0.07 * np.sin(grid_theta * 41 - grid_r * 0.02 + 1.3)
    # long spurs and gullies running down the slopes (creased, like real hills), strongest near the crest
    spurs = 1.0 - np.abs(np.sin(grid_theta * 17 + grid_r * 0.012 + seed_shift))
    spurs2 = 1.0 - np.abs(np.sin(grid_theta * 31 - grid_r * 0.02 + seed_shift * 2.1))
    wobble = wobble * (1.0 + 0.16 * (spurs - 0.5) * profile + 0.10 * (spurs2 - 0.5) * profile)
    z = height_here[:, None] * profile * wobble - 1.5
    x = HILL_CENTRE[0] + grid_r * np.sin(grid_theta)        # compass-style: angle 0 = +Y
    y = HILL_CENTRE[1] + grid_r * np.cos(grid_theta)
    vertices = np.stack([x, y, z], axis=-1).reshape(-1, 3)
    # faces: quads between neighbouring angles and distances, wrapping round the circle
    ii, jj = np.meshgrid(np.arange(steps_round), np.arange(steps_out), indexing='ij')
    i1 = (ii + 1) % steps_round
    a = ii * (steps_out + 1) + jj
    b = i1 * (steps_out + 1) + jj
    c = i1 * (steps_out + 1) + jj + 1
    d = ii * (steps_out + 1) + jj + 1
    # angle grows toward +X when seen from above, so (a, b, c, d) runs clockwise from above: reverse it so the top faces up
    faces = np.stack([a, d, c, b], axis=-1).reshape(-1, 4)
    # colour per point: dark ridge colour; misty light colour on the low slopes and facing the glow
    glow_amount = np.exp(-((np.mod(np.degrees(grid_theta) - GLOW_DIRECTION_DEGREES + 180.0, 360.0) - 180.0) / 50.0) ** 2)
    lowness = np.clip(1.0 - profile * (height_here[:, None] / ring['high']) ** 0.5, 0.0, 1.0) ** 1.4
    haze = np.array(HAZE_COLOUR)[None, None, :] * (1 - glow_amount[..., None] * 0.65) + np.array(HAZE_WARM_COLOUR)[None, None, :] * glow_amount[..., None] * 0.65
    mist_amount = np.clip(ring['mist'] * (0.25 + 1.1 * lowness), 0.0, 0.9)[..., None]
    base = np.array(ring['colour'])[None, None, :]
    colours = base * (1 - mist_amount) + haze * mist_amount * 0.55
    colours = colours.reshape(-1, 3)

    mesh = bpy.data.meshes.new(ring['name'])
    mesh.vertices.add(len(vertices))
    mesh.vertices.foreach_set('co', vertices.ravel())
    mesh.loops.add(len(faces) * 4)
    mesh.loops.foreach_set('vertex_index', faces.ravel())
    mesh.polygons.add(len(faces))
    mesh.polygons.foreach_set('loop_start', np.arange(len(faces)) * 4)
    mesh.polygons.foreach_set('use_smooth', np.ones(len(faces), dtype=bool))
    mesh.update(calc_edges=True)
    attribute = mesh.color_attributes.new('Colour', 'FLOAT_COLOR', 'POINT')
    rgba = np.concatenate([colours, np.ones((len(colours), 1))], axis=1)
    attribute.data.foreach_set('color', rgba.ravel())
    mesh.materials.append(hill_material())
    obj = bpy.data.objects.new(ring['name'], mesh)
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    collection.objects.link(obj)
    obj.visible_shadow = False                  # the hills must not throw shadows on the yard
    return obj


_hill_material = None


def hill_material():
    """Matte, no glow: colour comes from the colours painted on the hill points."""
    global _hill_material
    try:
        if _hill_material is not None and _hill_material.name in bpy.data.materials:
            return _hill_material
    except ReferenceError:                  # the scene was cleared since last time
        pass
    material = bpy.data.materials.new('Hill matte')
    material.use_nodes = True
    tree = material.node_tree
    bsdf = tree.nodes['Principled BSDF']
    colour = tree.nodes.new('ShaderNodeVertexColor'); colour.layer_name = 'Colour'
    tree.links.new(colour.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 1.0
    for name in ('Specular IOR Level', 'Specular'):
        if name in bsdf.inputs:
            bsdf.inputs[name].default_value = 0.0
    _hill_material = material
    return material


def build_hills(collection_name):
    return [make_hill_ring(ring, collection_name) for ring in HILL_RINGS]


# --------------------------------------------------------------------------------------------------------------------
# 4. The village: terraced brick houses with slate roofs, on a gently rising hillside, with a lamp-lit street
# --------------------------------------------------------------------------------------------------------------------
HILLSIDE_SLOPE = 0.08            # metres the land rises for every metre going back (+Y) from y = 6, so back rows look over front rows
HILLSIDE_FIRST_Y = 6.0
HILLSIDE_TOP_Y = 52.0             # where the rise stops and the land rolls over behind the village
HOUSE_DEPTH = 4.8
HOUSE_WALL_HEIGHT = 4.5
ROOF_PITCH_DEGREES = 34.0
MAIN_STREET = dict(x_west_edge=15.0, x_kerb_west=15.9, x_kerb_east=19.9, x_pavement_east=21.5)
ROWS = [
    # y of the front wall, x where the row starts, house widths (metres), brick palette shift
    dict(name='Row 1', y_front=9.5, x_start=21.5, widths=[5.2, 5.0, 5.4, 5.2, 5.0], seed=1),
    dict(name='Row 2', y_front=20.0, x_start=21.5, widths=[5.0, 5.4, 5.2, 5.0, 5.2], seed=2),
    dict(name='Row 3', y_front=30.5, x_start=21.5, widths=[5.4, 5.2, 5.0, 5.2, 5.0], seed=3),
    dict(name='Row 4', y_front=41.0, x_start=23.5, widths=[5.2, 5.0, 5.4, 5.2], seed=4),
]
BRICK_TINTS = [(1.00, 0.85, 0.78), (0.92, 0.72, 0.62), (0.66, 0.68, 0.72), (1.00, 0.92, 0.84), (0.86, 0.62, 0.52), (0.72, 0.70, 0.70),
               (0.95, 0.80, 0.66), (0.62, 0.60, 0.60), (0.80, 0.78, 0.72), (0.70, 0.74, 0.76)]
SLATE_TINTS = [(1.0, 1.0, 1.0), (0.82, 0.90, 1.0), (0.75, 0.78, 0.86), (0.95, 0.90, 0.88), (0.68, 0.74, 0.80)]
DOOR_TINTS = [(0.55, 1.0, 0.65), (1.0, 0.35, 0.28), (0.40, 0.55, 1.0), (0.85, 0.60, 0.40), (1.0, 0.82, 0.30), (0.35, 0.35, 0.38)]
FRAME_COLOURS = [(0.42, 0.40, 0.36), (0.07, 0.08, 0.09), (0.30, 0.36, 0.32), (0.40, 0.20, 0.16)]
LIT_WINDOW_SHARE = 0.26           # about this share of windows glows warm


def hillside_rise(x, y):
    """How far the village land is raised above the shared ground (metres). Works for numbers or numpy arrays."""
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    ramp_in = _smooth(HILLSIDE_FIRST_Y, HILLSIDE_FIRST_Y + 8.0, y)
    climb = HILLSIDE_SLOPE * (np.clip(y, HILLSIDE_FIRST_Y, HILLSIDE_TOP_Y) - HILLSIDE_FIRST_Y)
    roll_over = 1.0 - _smooth(HILLSIDE_TOP_Y, HILLSIDE_TOP_Y + 46.0, y)
    side = _smooth(5.0, 19.0, x) * (1.0 - _smooth(60.0, 82.0, x))
    return climb * ramp_in * roll_over * side


def land_height(x, y):
    return mc.ground_height(x, y) + float(hillside_rise(x, y))


class RowFrame:
    """Local measuring frame of a row of houses: s runs along the row, d runs from the front wall into the house, z up."""

    def __init__(self, origin_x, origin_y, yaw=0.0):
        self.origin = np.array([origin_x, origin_y])
        self.yaw = yaw
        self.along = np.array([math.cos(yaw), math.sin(yaw), 0.0])
        self.inward = np.array([-math.sin(yaw), math.cos(yaw), 0.0])

    def point(self, s, d, z):
        return (self.origin[0] + s * self.along[0] + d * self.inward[0], self.origin[1] + s * self.along[1] + d * self.inward[1], z)

    def box(self, builder, low, high, slot, skip=()):
        """A box between two corners given in (s, d, z)."""
        centre = self.point((low[0] + high[0]) / 2, (low[1] + high[1]) / 2, (low[2] + high[2]) / 2)
        builder.add_box(centre, (high[0] - low[0], high[1] - low[1], high[2] - low[2]), slot=slot, yaw=self.yaw, skip=skip)

    def polygon(self, builder, local_points, slot, outward):
        """A flat face from (s, d, z) points; the winding is fixed so that the face looks along `outward` (given as s, d, z)."""
        points = np.array([self.point(*p) for p in local_points], dtype=float)
        out = outward[0] * self.along + outward[1] * self.inward + np.array([0.0, 0.0, outward[2]])
        normal = np.zeros(3)
        for i in range(len(points)):
            a, b = points[i], points[(i + 1) % len(points)]
            normal += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
        if float(normal @ out) < 0:
            points = points[::-1]
        builder.add_polygon(points, slot=slot)

    def slab(self, builder, centre, size, up_slope, normal, slot):
        """A rotated box. centre (s, d, z); size (along the row, up the slope, thickness); up_slope and normal are (s, d, z) unit vectors."""
        x_axis = self.along
        y_axis = up_slope[0] * self.along + up_slope[1] * self.inward + np.array([0.0, 0.0, up_slope[2]])
        z_axis = normal[0] * self.along + normal[1] * self.inward + np.array([0.0, 0.0, normal[2]])
        rotation = np.stack([x_axis, y_axis, z_axis], axis=1)
        if np.linalg.det(rotation) < 0:                                  # keep the box right-handed
            rotation[:, 0] = -rotation[:, 0]
        builder.add_box(self.point(*centre), size, slot=slot, rotation=rotation)


class VillageMaterials:
    """All the materials of the houses in one list, with a slot number for each by name."""

    def __init__(self):
        self.list = []
        self.slots = {}

    def add(self, name, material):
        self.slots[name] = len(self.list)
        self.list.append(material)
        return self.slots[name]

    def __getitem__(self, name):
        return self.slots[name]


def make_village_materials(rng):
    M = VillageMaterials()
    for i, tint in enumerate(BRICK_TINTS):
        M.add(f'brick{i}', mc.surface_material('brick', tint=tint, variation=0.25))
    for i, tint in enumerate(SLATE_TINTS):
        M.add(f'slate{i}', mc.surface_material('slate', tint=tint, variation=0.3))
    for i, tint in enumerate(DOOR_TINTS):
        M.add(f'door{i}', mc.surface_material('wood', tint=tint, variation=0.15, splash=0.3))
    for i, colour in enumerate(FRAME_COLOURS):
        M.add(f'frame{i}', mc.plain_material(f'Window frame {i}', colour, roughness=0.55))
    M.add('stone_plinth', mc.surface_material('gravel', tint=(0.78, 0.76, 0.72), variation=0.2, splash=0.3, tile=1.1))
    M.add('stone_trim', mc.plain_material('Light stone trim', (0.20, 0.195, 0.185), roughness=0.85))
    M.add('glass', mc.plain_material('Dark window glass', (0.012, 0.02, 0.028), roughness=0.08))
    M.add('glow0', mc.glow_material('Warm window glow 0', (1.0, 0.38, 0.07), 2.4))
    M.add('glow1', mc.glow_material('Warm window glow 1', (1.0, 0.47, 0.11), 3.4))
    M.add('glow2', mc.glow_material('Warm window glow 2', (1.0, 0.34, 0.06), 4.8))
    M.add('ridge', mc.plain_material('Ridge tiles', (0.030, 0.034, 0.040), roughness=0.6))
    M.add('pot', mc.plain_material('Chimney pot clay', (0.30, 0.10, 0.05), roughness=0.8))
    M.add('stack_cap', mc.plain_material('Chimney cap stone', (0.10, 0.10, 0.095), roughness=0.85))
    M.add('iron', mc.plain_material('Cast iron black', (0.018, 0.02, 0.022), roughness=0.45, metallic=0.6))
    M.add('pole', mc.surface_material('wood', tint=(0.45, 0.40, 0.36), variation=0.2, splash=0.0))
    M.add('lamp_glow', mc.glow_material('Street lamp glow', (1.0, 0.42, 0.10), 5.0))
    M.add('street', mc.surface_material('gravel', tint=(0.50, 0.46, 0.42), variation=0.25, splash=0.0, tile=1.6))
    M.add('pavement', mc.surface_material('gravel', tint=(0.85, 0.82, 0.78), variation=0.25, splash=0.0, tile=1.0))
    M.add('kerb', mc.plain_material('Kerb stone', (0.16, 0.155, 0.15), roughness=0.85))
    M.add('wall_stone', mc.surface_material('gravel', tint=(0.62, 0.60, 0.56), variation=0.3, splash=0.4, tile=1.3))
    M.add('rubble', mc.surface_material('slate', tint=(0.55, 0.55, 0.58), variation=0.3, splash=0.0, tile=1.6))
    return M


def wall_box(frame, builder, wall, wall_info, t0, t1, z0, z1, out0, out1, slot):
    """A box on a wall: along-wall range t0..t1, height z0..z1, and out0..out1 away from the wall face (negative = inside the wall).
    wall_info gives the positions of the faces: {'s_left', 's_right', 'depth'} for the house."""
    if wall == 'front':
        frame.box(builder, (t0, -out1, z0), (t1, -out0, z1), slot)
    elif wall == 'back':
        frame.box(builder, (t0, wall_info['depth'] + out0, z0), (t1, wall_info['depth'] + out1, z1), slot)
    elif wall == 'left':
        frame.box(builder, (wall_info['s_left'] - out1, t0, z0), (wall_info['s_left'] - out0, t1, z1), slot)
    else:
        frame.box(builder, (wall_info['s_right'] + out0, t0, z0), (wall_info['s_right'] + out1, t1, z1), slot)


def add_window(frame, builder, M, wall, wall_info, t0, t1, z0, z1, recessed, pane_slot, frame_slot, with_sill=True, with_lintel=True):
    """A window: stone sill and lintel, a painted frame with a middle rail (and a middle bar if wide) and a pane of glass or glow."""
    width, height = t1 - t0, z1 - z0
    if recessed:
        pane = (-0.20, -0.17)
        bars = (-0.22, -0.05)
    else:
        pane = (0.005, 0.03)
        bars = (0.0, 0.075)
    wall_box(frame, builder, wall, wall_info, t0, t1, z0, z1, pane[0], pane[1], pane_slot)
    bar = 0.07
    wall_box(frame, builder, wall, wall_info, t0, t0 + bar, z0, z1, bars[0], bars[1], frame_slot)
    wall_box(frame, builder, wall, wall_info, t1 - bar, t1, z0, z1, bars[0], bars[1], frame_slot)
    wall_box(frame, builder, wall, wall_info, t0 + bar, t1 - bar, z0, z0 + bar, bars[0], bars[1], frame_slot)
    wall_box(frame, builder, wall, wall_info, t0 + bar, t1 - bar, z1 - bar, z1, bars[0], bars[1], frame_slot)
    zm = (z0 + z1) / 2 + height * 0.04
    wall_box(frame, builder, wall, wall_info, t0 + bar, t1 - bar, zm - 0.03, zm + 0.03, bars[0], bars[1], frame_slot)
    if width > 1.15:
        tm = (t0 + t1) / 2
        wall_box(frame, builder, wall, wall_info, tm - 0.025, tm + 0.025, z0 + bar, z1 - bar, bars[0], bars[1], frame_slot)
    if with_sill:
        wall_box(frame, builder, wall, wall_info, t0 - 0.10, t1 + 0.10, z0 - 0.09, z0 - 0.01, -0.01, 0.12, M['stone_trim'])
    if with_lintel:
        wall_box(frame, builder, wall, wall_info, t0 - 0.12, t1 + 0.12, z1 + 0.01, z1 + 0.17, -0.01, 0.08, M['stone_trim'])


def solid_wall_pieces(width, z_low, z_high, openings):
    """Splits a wall of the given width into boxes that leave the openings clear. openings: list of (s0, s1, z0, z1).
    Returns a list of (s0, s1, z0, z1) solid pieces."""
    breaks = sorted(set([z_low, z_high] + [o[2] for o in openings if z_low < o[2] < z_high] + [o[3] for o in openings if z_low < o[3] < z_high]))
    pieces = []
    for za, zb in zip(breaks[:-1], breaks[1:]):
        cuts = sorted([(o[0], o[1]) for o in openings if o[2] <= za + 1e-6 and o[3] >= zb - 1e-6])
        cursor = 0.0
        for c0, c1 in cuts:
            if c0 > cursor + 1e-6:
                pieces.append((cursor, c0, za, zb))
            cursor = max(cursor, c1)
        if cursor < width - 1e-6:
            pieces.append((cursor, width, za, zb))
    return pieces


def build_house(frame, builder, M, rng, s_left, width, base_z, bottom_z, wall_height, is_first, is_last, house_number, row_seed, lit_plan):
    """One terraced house at s_left..s_left+width along the row. base_z: floor level; bottom_z: bottom of the stone base (below the ground)."""
    depth = HOUSE_DEPTH
    brick = M[f'brick{rng.integers(len(BRICK_TINTS))}']
    slate = M[f'slate{rng.integers(len(SLATE_TINTS))}']
    door_slot = M[f'door{rng.integers(len(DOOR_TINTS))}']
    frame_slot = M[f'frame{rng.integers(len(FRAME_COLOURS))}']
    hw = wall_height
    top = base_z + hw
    info = {'s_left': s_left, 's_right': s_left + width, 'depth': depth}
    plinth_top = base_z + 0.45
    wall_thickness = 0.32
    # stone base all round, slightly proud of the brick
    frame.box(builder, (s_left - 0.03, -0.04, bottom_z), (s_left + width + 0.03, depth + 0.04, plinth_top), M['stone_plinth'], skip=('bottom',))
    # body behind the front slab (all faces; the ones between neighbours are hidden)
    frame.box(builder, (s_left, wall_thickness, plinth_top - 0.02), (s_left + width, depth, top), brick, skip=('bottom',))
    # front slab with the openings cut out
    mirrored = (house_number % 2 == 1)
    def mirror(s0, s1):
        return (width - s1, width - s0) if mirrored else (s0, s1)
    door_s = mirror(0.38, 1.33)
    window_s = mirror(2.15, 3.65)
    upper_a = mirror(0.36, 1.36)
    upper_b = mirror(2.40, 3.40)
    door = (door_s[0], door_s[1], plinth_top - base_z, 2.72)
    ground_window = (window_s[0], window_s[1], 1.02, 2.38)
    up_z0, up_z1 = hw - 1.38, hw - 0.42
    windows_up = [(upper_a[0], upper_a[1], up_z0, up_z1), (upper_b[0], upper_b[1], up_z0, up_z1)]
    openings = [door, ground_window] + windows_up
    for (s0, s1, z0, z1) in solid_wall_pieces(width, plinth_top - base_z, hw, openings):
        frame.box(builder, (s_left + s0, 0.0, base_z + z0), (s_left + s1, wall_thickness, base_z + z1), brick)
    # window furniture
    lit_ground, lit_up_a, lit_up_b = lit_plan
    def pane_for(lit):
        return M[f'glow{rng.integers(3)}'] if lit else M['glass']
    add_window(frame, builder, M, 'front', info, s_left + ground_window[0], s_left + ground_window[1], base_z + ground_window[2], base_z + ground_window[3],
               True, pane_for(lit_ground), frame_slot)
    add_window(frame, builder, M, 'front', info, s_left + windows_up[0][0], s_left + windows_up[0][1], base_z + up_z0, base_z + up_z1, True, pane_for(lit_up_a), frame_slot)
    add_window(frame, builder, M, 'front', info, s_left + windows_up[1][0], s_left + windows_up[1][1], base_z + up_z0, base_z + up_z1, True, pane_for(lit_up_b), frame_slot)
    # door, fanlight and step
    d0, d1 = s_left + door_s[0], s_left + door_s[1]
    door_bottom, door_top = plinth_top, base_z + 2.36
    frame.box(builder, (d0 + 0.04, 0.10, door_bottom), (d1 - 0.04, 0.17, door_top), door_slot)
    frame.box(builder, (d0, 0.07, door_top), (d1, 0.19, door_top + 0.08), frame_slot)
    fan = M['glow1'] if lit_ground and rng.random() < 0.6 else M['glass']
    frame.box(builder, (d0 + 0.06, 0.12, door_top + 0.08), (d1 - 0.06, 0.15, base_z + 2.70), fan)
    frame.box(builder, (d0 - 0.12, -0.02, base_z + 2.72), (d1 + 0.12, 0.10, base_z + 2.90), M['stone_trim'])
    frame.box(builder, (d0 - 0.10, -0.55, base_z - 0.05), (d1 + 0.10, -0.02, base_z + 0.19), M['stone_trim'])
    # roof
    pitch = math.radians(ROOF_PITCH_DEGREES)
    overhang = 0.32
    half_span = depth / 2.0
    ridge_top = top + 0.12 + half_span * math.tan(pitch)
    thickness = 0.12
    run = half_span + overhang
    slab_length = run / math.cos(pitch) + 0.10
    s_extra_left = 0.14 if is_first else 0.0
    s_extra_right = 0.14 if is_last else 0.0
    slab_width = width + s_extra_left + s_extra_right
    s_mid = s_left + (width + s_extra_right - s_extra_left) / 2
    for side in (+1, -1):                                                    # +1 = front slope (faces -d), -1 = back slope
        u = (0.0, side * math.cos(pitch), math.sin(pitch))                 # up the slope (side = +1 rises toward +d)
        if side == +1:
            n = (0.0, -math.sin(pitch), math.cos(pitch))
            start_d = -overhang
        else:
            n = (0.0, math.sin(pitch), math.cos(pitch))
            start_d = depth + overhang
        start_z = top + 0.12 + (-overhang) * math.tan(pitch)
        top_start = np.array([start_d, start_z])
        top_dir = np.array([u[1], u[2]])
        mid_top = top_start + top_dir * (slab_length - 0.10) / 2 + top_dir * 0.0
        centre_d = mid_top[0] - n[1] * thickness / 2
        centre_z = mid_top[1] - n[2] * thickness / 2
        frame.slab(builder, (s_mid, centre_d, centre_z), (slab_width, slab_length, thickness), u, n, slate)
    frame.box(builder, (s_left - (0.14 if is_first else 0.0), depth / 2 - 0.16, ridge_top - 0.02), (s_left + width + (0.14 if is_last else 0.0), depth / 2 + 0.16, ridge_top + 0.12), M['ridge'])
    # gable triangles at the row ends
    apex_z = ridge_top - 0.18
    if is_first:
        frame.polygon(builder, [(s_left, 0.0, top), (s_left, depth, top), (s_left, depth / 2, apex_z)], brick, (-1, 0, 0))
    if is_last:
        frame.polygon(builder, [(s_left + width, 0.0, top), (s_left + width, depth, top), (s_left + width, depth / 2, apex_z)], brick, (1, 0, 0))
    # back wall: a small window, a door and an upstairs window (plain, proud of the wall)
    back_info = info
    add_window(frame, builder, M, 'back', back_info, s_left + 0.7, s_left + 1.6, base_z + 1.2, base_z + 2.2, False, M['glass'], frame_slot, True, True)
    add_window(frame, builder, M, 'back', back_info, s_left + 2.4, s_left + 3.4, base_z + hw - 1.38, base_z + hw - 0.42, False, M['glass'], frame_slot, True, True)
    wall_box(frame, builder, 'back', back_info, s_left + 3.7, s_left + 4.6, plinth_top, base_z + 2.3, 0.0, 0.06, door_slot)
    return {'ridge_top': ridge_top, 'top': top}


def build_row(builder, M, row, rng_seed):
    rng = np.random.default_rng(rng_seed)
    frame = RowFrame(row['x_start'], row['y_front'])
    widths = row['widths']
    count = len(widths)
    s_cursor = 0.0
    houses = []
    stack_boundaries = []
    for i, width in enumerate(widths):
        corners = [(s_cursor, 0.0), (s_cursor + width, 0.0), (s_cursor, HOUSE_DEPTH), (s_cursor + width, HOUSE_DEPTH), (s_cursor + width / 2, 0.0)]
        heights = [land_height(*frame.point(s, d, 0.0)[:2]) for s, d in corners]
        front_height = max(land_height(*frame.point(s, 0.0, 0.0)[:2]) for s in (s_cursor, s_cursor + width / 2, s_cursor + width))
        base_z = front_height + 0.12
        bottom_z = min(heights) - 0.35
        wall_height = HOUSE_WALL_HEIGHT + rng.uniform(-0.18, 0.22)
        lit_ground = rng.random() < LIT_WINDOW_SHARE * 1.2
        lit_up_a = rng.random() < LIT_WINDOW_SHARE * 0.9
        lit_up_b = rng.random() < LIT_WINDOW_SHARE * 0.7
        info = build_house(frame, builder, M, rng, s_cursor, width, base_z, bottom_z, wall_height, i == 0, i == count - 1, i, row['seed'],
                           (lit_ground, lit_up_a, lit_up_b))
        houses.append(dict(s_left=s_cursor, width=width, base_z=base_z, ridge_top=info['ridge_top'], top=info['top']))
        s_cursor += width
    # chimney stacks on the party walls and the ends
    for i in range(count + 1):
        if i == 0 or i == count:
            if rng.random() < 0.55:
                pass
            else:
                continue
        elif rng.random() < 0.2:
            continue
        s_boundary = houses[i]['s_left'] if i < count else houses[-1]['s_left'] + houses[-1]['width']
        neighbours = [houses[j] for j in (i - 1, i) if 0 <= j < count]
        ridge = min(h['ridge_top'] for h in neighbours)
        stack_top = ridge + rng.uniform(1.05, 1.5)
        stack_bottom = min(h['top'] for h in neighbours) - 0.3
        inset = 0.20 if i in (0, count) else 0.0
        s_centre = s_boundary + (inset if i == 0 else (-inset if i == count else 0.0))
        brick_slot = M[f'brick{rng.integers(len(BRICK_TINTS))}']
        frame.box(builder, (s_centre - 0.50, HOUSE_DEPTH / 2 - 0.34, stack_bottom), (s_centre + 0.50, HOUSE_DEPTH / 2 + 0.34, stack_top), brick_slot, skip=('bottom',))
        frame.box(builder, (s_centre - 0.60, HOUSE_DEPTH / 2 - 0.44, stack_top), (s_centre + 0.60, HOUSE_DEPTH / 2 + 0.44, stack_top + 0.13), M['stack_cap'])
        for k, offset in enumerate((-0.22, 0.22)):
            if rng.random() < 0.15 and k == 1:
                continue
            cx = frame.point(s_centre + offset, HOUSE_DEPTH / 2, stack_top + 0.13)
            height = rng.uniform(0.38, 0.6)
            builder.add_cylinder(cx, (cx[0], cx[1], cx[2] + height), 0.15, sides=8, slot=M['pot'], radius_end=0.12)
            builder.add_cylinder((cx[0], cx[1], cx[2] + height - 0.02), (cx[0], cx[1], cx[2] + height + 0.1), 0.17, sides=8, slot=M['pot'], radius_end=0.17)
    # left end gable windows (they face the main street): one ground floor, one upstairs, lit sometimes
    first = houses[0]
    gable_info = {'s_left': first['s_left'], 's_right': first['s_left'], 'depth': HOUSE_DEPTH}
    frame_slot = M[f'frame{rng.integers(len(FRAME_COLOURS))}']
    lit_a, lit_b = rng.random() < 0.5, rng.random() < 0.5
    add_window(frame, builder, M, 'left', gable_info, 1.2, 2.4, first['base_z'] + 1.1, first['base_z'] + 2.3, False, M[f'glow{rng.integers(3)}'] if lit_a else M['glass'], frame_slot)
    add_window(frame, builder, M, 'left', gable_info, 1.2, 2.4, first['top'] - 1.4, first['top'] - 0.45, False, M[f'glow{rng.integers(3)}'] if lit_b else M['glass'], frame_slot)
    add_window(frame, builder, M, 'left', gable_info, 3.0, 3.8, first['base_z'] + 1.1, first['base_z'] + 2.3, False, M['glass'], frame_slot)
    return houses


def ribbon(builder, points_xy, half_width, lift, slot, along_step=2.0, rise_fn=None):
    """A flat strip following the land along a line of (x, y) points, lifted a little above it."""
    pts = np.array(points_xy, dtype=float)
    segment = np.diff(pts, axis=0)
    lengths = np.hypot(segment[:, 0], segment[:, 1])
    total = lengths.sum()
    count = max(2, int(total / along_step) + 1)
    distances = np.linspace(0, total, count)
    cumulative = np.concatenate([[0], np.cumsum(lengths)])
    xs = np.interp(distances, cumulative, pts[:, 0])
    ys = np.interp(distances, cumulative, pts[:, 1])
    directions = np.gradient(np.stack([xs, ys], axis=1), axis=0)
    directions /= np.linalg.norm(directions, axis=1, keepdims=True)
    normals = np.stack([-directions[:, 1], directions[:, 0]], axis=1)
    vertices = []
    for k in range(count):
        for side in (-1, +1):
            x = xs[k] + normals[k, 0] * half_width * side
            y = ys[k] + normals[k, 1] * half_width * side
            vertices.append((x, y, land_height(x, y) + lift))
    faces = []
    for k in range(count - 1):
        a, b, c, d = 2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2
        faces.append([a, d, c, b])
    # winding: make sure faces point up
    v = np.array(vertices)
    f0 = faces[0]
    n = np.cross(v[f0[1]] - v[f0[0]], v[f0[2]] - v[f0[0]])
    if n[2] < 0:
        faces = [f[::-1] for f in faces]
    builder.add_indexed_faces(vertices, faces, slot=slot)


def add_lamp(builder, M, x, y, height=3.6):
    z = land_height(x, y)
    builder.add_cylinder((x, y, z - 0.1), (x, y, z + 0.55), 0.15, sides=8, slot=M['iron'], radius_end=0.11)
    builder.add_cylinder((x, y, z + 0.5), (x, y, z + height), 0.055, sides=8, slot=M['iron'])
    builder.add_cylinder((x, y, z + height + 0.02), (x, y, z + height + 0.52), 0.17, sides=4, slot=M['lamp_glow'], radius_end=0.24, caps=False, smooth=False)
    builder.add_box((x, y, z + height + 0.02), (0.40, 0.40, 0.06), slot=M['iron'])
    builder.add_box((x, y, z + height + 0.56), (0.42, 0.42, 0.07), slot=M['iron'])
    builder.add_cylinder((x, y, z + height + 0.58), (x, y, z + height + 0.74), 0.20, sides=4, slot=M['iron'], radius_end=0.03)
    return (x, y, z + height + 0.25)


def hillside_material():
    """The yard's own mud picture (so it blends into the ground), but with the wet shine turned off, and a slightly grassier tint."""
    material = mc.surface_material('mud', tint=(0.86, 0.94, 0.80), variation=0.35, splash=0.0, tile=4.0)
    tree = material.node_tree
    bsdf = [n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    for link in list(bsdf.inputs['Roughness'].links):
        tree.links.remove(link)
    bsdf.inputs['Roughness'].default_value = 0.93
    return material


def build_hillside(collection_name):
    """The land of the village: the shared ground, raised in a gentle slope toward the back, with the same mud look."""
    xs = np.arange(2.0, 84.1, 2.0)
    ys = np.arange(4.0, 100.1, 2.0)
    gx, gy = np.meshgrid(xs, ys, indexing='ij')
    rise = hillside_rise(gx, gy)
    ground = np.vectorize(mc.ground_height)(gx, gy)
    z = ground + rise - 0.10                         # a touch below the ground where the rise is nil, so it vanishes into it
    z = np.where(rise > 0.0, ground + rise - 0.10 + 0.0, ground - 0.25)
    vertices = np.stack([gx, gy, z], axis=-1).reshape(-1, 3)
    ny = len(ys)
    faces = []
    for i in range(len(xs) - 1):
        for j in range(ny - 1):
            a = i * ny + j
            faces.append([a, a + ny, a + ny + 1, a + 1])
    builder = mc.MeshBuilder('Village hillside', [hillside_material()])
    builder.add_indexed_faces(vertices, faces, slot=0, smooth=True, uv_axes=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    obj = builder.finish(collection_name)
    return obj


def build_village(collection_name):
    rng = np.random.default_rng(2024)
    M = make_village_materials(rng)
    objects = []
    objects.append(build_hillside(collection_name))
    builder = mc.MeshBuilder('Village houses', M.list)
    # the houses
    all_houses = {}
    for row in ROWS:
        all_houses[row['name']] = build_row(builder, M, row, row['seed'] * 101 + 7)
    # main street (runs along Y on the west edge of the village), lane streets in front of each row
    street_builder = builder
    ribbon(street_builder, [(MAIN_STREET['x_kerb_west'] + 2.2, 5.0), (MAIN_STREET['x_kerb_west'] + 2.2, 46.0)],
           (MAIN_STREET['x_kerb_east'] - MAIN_STREET['x_kerb_west']) / 2, 0.06, M['street'])
    ribbon(street_builder, [((MAIN_STREET['x_kerb_east'] + MAIN_STREET['x_pavement_east']) / 2, 5.0), ((MAIN_STREET['x_kerb_east'] + MAIN_STREET['x_pavement_east']) / 2, 46.0)],
           (MAIN_STREET['x_pavement_east'] - MAIN_STREET['x_kerb_east']) / 2, 0.14, M['pavement'])
    ribbon(street_builder, [(MAIN_STREET['x_kerb_east'] + 0.06, 5.0), (MAIN_STREET['x_kerb_east'] + 0.06, 46.0)], 0.07, 0.17, M['kerb'])
    for row in ROWS:
        y_front = row['y_front']
        x_end = row['x_start'] + sum(row['widths']) + 1.5
        ribbon(street_builder, [(MAIN_STREET['x_pavement_east'], y_front - 1.3 - 1.95), (x_end, y_front - 1.3 - 1.95)], 1.95, 0.06, M['street'])
        ribbon(street_builder, [(MAIN_STREET['x_pavement_east'], y_front - 0.65), (x_end, y_front - 0.65)], 0.65, 0.14, M['pavement'])
    # low stone wall on the west edge of the street
    for y0 in np.arange(6.0, 44.0, 3.0):
        z0 = land_height(MAIN_STREET['x_west_edge'], y0)
        builder.add_box((MAIN_STREET['x_west_edge'], y0 + 1.5, z0 + 0.5), (0.55, 3.0, 1.2), slot=M['wall_stone'])
    # telegraph poles with sagging wires along the west side of the main street
    pole_spots = [(14.2, y) for y in (12.0, 30.0, 48.0)]
    pole_tops = []
    for (x, y) in pole_spots:
        z = land_height(x, y)
        builder.add_cylinder((x, y, z - 0.3), (x, y, z + 7.6), 0.11, sides=8, slot=M['pole'], radius_end=0.07)
        builder.add_box((x, y, z + 7.1), (0.12, 1.5, 0.12), slot=M['pole'])
        builder.add_box((x, y, z + 6.6), (0.12, 1.1, 0.12), slot=M['pole'])
        pole_tops.append((x, y, z))
    for (xa, ya, za), (xb, yb, zb) in zip(pole_tops[:-1], pole_tops[1:]):
        for arm_height, arm_offset in ((7.1, -0.65), (7.1, 0.65), (6.6, -0.45), (6.6, 0.45)):
            previous = None
            for k in range(9):
                t = k / 8.0
                point = np.array([xa + (xb - xa) * t, ya + (yb - ya) * t + arm_offset, za + (zb - za) * t + arm_height - 0.9 * 4 * t * (1 - t) + 0.05])
                if previous is not None:
                    builder.add_beam(previous, point, 0.02, 0.02, slot=M['iron'])
                previous = point
    # lamps along the street
    lamp_spots = [(MAIN_STREET['x_kerb_west'] + 0.4, y) for y in (9.0, 18.5, 28.0, 37.5)]
    lamp_tops = [add_lamp(builder, M, x, y) for (x, y) in lamp_spots]
    objects.append(builder.finish(collection_name))
    # real lights for the lamps
    for i, (x, y, z) in enumerate(lamp_tops):
        light = bpy.data.lights.new(f'Village lamp light {i + 1}', 'POINT')
        light.energy = 450.0
        light.color = (1.0, 0.6, 0.28)
        light.shadow_soft_size = 0.18
        obj = bpy.data.objects.new(f'Village lamp light {i + 1}', light)
        obj.location = (x, y, z + 0.05)
        bpy.context.scene.collection.objects.link(obj)
    return objects


# --------------------------------------------------------------------------------------------------------------------
# 5. Putting it all together
# --------------------------------------------------------------------------------------------------------------------
KNOWN_FLAWS = [
    'From the standard tall camera only a few houses at the right edge show, and the headframe leg, track and coal heaps hide part of them; the rest of the village shows from other angles.',
    'The village stands on a gently rising hillside that this part adds on top of the shared ground (Village hillside, about 10 cm below the ground where it begins). It relies on the real ground being there; if the ground part ends before x = 84, y = 100 the hillside edge could show.',
    'The ground_height() bank (about 12 m high 100 m out) can cover the lowest hills; the ground part should fade its bank out beyond about 60 m, or the near hills show only their tops.',
    'The sky picture is 8-bit (no true bright sun): the orange glow is brightened inside the world nodes ("Glow boost"), and the sun is a separate light. At 4096 x 2048 it is soft when enlarged into a tall frame (about 2.5 times).',
    'Brick and slate on the houses use the normal maps only (no real displacement): they are 40 m or more from the standard camera. Close up (under about 10 m) the brick relief is flat.',
    'Window glass is a dark opaque pane or a glow, so there are no interiors and no curtains; lit windows are plain rectangles of light.',
    'All houses follow one template (mirrored in pairs); the variety comes from tints, heights, door and frame colours and which windows glow. No gutters, downpipes, gardens or people.',
    'The hills are smooth procedural rings with colours painted on their points (no rock texture, no trees); the far ring is lighter and bluer to fake haze. They need the camera clip end at 1000 m (the Blender default).',
    'Four real point lights on the street lamps add a little render noise at low sample counts.',
]


def tune(sky_strength=None, sun_strength=None, fill_strength=None, lamp_power=None, glow_boost=None):
    """Change the main strengths after build(): world sky light, the low sun, the cool fill, the street lamp lights, the glow boost."""
    world = bpy.context.scene.world
    if world is not None and world.node_tree is not None:
        if sky_strength is not None and 'Sky strength' in world.node_tree.nodes:
            world.node_tree.nodes['Sky strength'].inputs['Strength'].default_value = sky_strength
        if glow_boost is not None and 'Glow boost' in world.node_tree.nodes:
            world.node_tree.nodes['Glow boost'].inputs[1].default_value = glow_boost
    for name, value in (('Village low sun', sun_strength), ('Village cool fill', fill_strength)):
        if value is not None and name in bpy.data.lights:
            bpy.data.lights[name].energy = value
    if lamp_power is not None:
        for light in bpy.data.lights:
            if light.name.startswith('Village lamp light'):
                light.energy = lamp_power


def count_triangles(objects):
    total = 0
    for obj in objects:
        if obj.type == 'MESH':
            total += sum(len(p.vertices) - 2 for p in obj.data.polygons)
    return total


def build(collection_name='Mine', with_village=True):
    """Creates the sky world, the lights, the hills and the village. Returns {'objects': [...], 'notes': '...', ...}."""
    started = time.time()
    created_before = set(bpy.data.objects.keys())
    picture = make_sky_picture()
    build_world(picture)
    lights = build_lights()
    build_hills(collection_name)
    if with_village:
        build_village(collection_name)
    new_objects = [bpy.data.objects[name] for name in bpy.data.objects.keys() if name not in created_before]
    notes = (
        'World: painted dusk sky picture (' + os.path.basename(picture) + ') on world "Dusk sky"; tune node "Sky strength" (default %.2f), node "Sky turn" '
        '(rotation Z; if you turn it, turn the sun too) and node "Glow boost". Lights: "Village low sun" (SUN, orange, %.0f degrees above the horizon, '
        'from compass %.0f = right-back, strength %.1f) and "Village cool fill" (SUN, blue, from front-left, strength %.1f). '
        'Recommended exposure: %+.1f stops with AgX. Hills: objects "Near hills", "Middle hills", "Far hills" (shadow-casting turned off); '
        'the camera needs clip end of at least 1000 m.' % (SKY_LIGHT_STRENGTH, SUN_ELEVATION_DEGREES, GLOW_DIRECTION_DEGREES, SUN_STRENGTH, FILL_STRENGTH, RECOMMENDED_EXPOSURE))
    return {'objects': [o.name for o in new_objects], 'notes': notes, 'light_names': [l.name for l in lights],
            'triangle_count': count_triangles(new_objects), 'build_seconds': round(time.time() - started, 1)}


