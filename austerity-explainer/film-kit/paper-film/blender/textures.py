# What this does: paints the surface pictures ("textures") that Blender models wear: brick, dressed
# stone, painted corrugated iron, slate, cobbled setts, cinder ground, painted timber planks, riveted
# iron, window glass with glazing bars (and the warm glow behind it), a lit interior, and wood grain.
# Each texture tiles without a seam, and the ones with relief also get a "normal map" (a picture of
# which way each spot of the surface faces, so mortar lines and cobbles catch the lamp light).
#
# How it fits: model_kit.py calls these when it makes a material; nothing here needs Blender, only
# numpy and Pillow. Every function returns Pillow pictures; `units` says how many world units one tile
# covers, so model_kit can repeat it at the right size.
#
# Use on its own to look at them: python3 textures.py OUT_FOLDER   (writes every texture as a picture)

import math
import os
import sys

import numpy as np
from PIL import Image

# ------------------------------------------------------------------------------------------- noise


def fractal_noise(height, width, rng, roughness=2.0, smallest=2.0):
    """Tileable cloudy noise between 0 and 1. roughness: higher = smoother (fewer fine specks);
    smallest: removes features bigger than width / smallest."""
    white = rng.standard_normal((height, width))
    spectrum = np.fft.fft2(white)
    fy = np.fft.fftfreq(height)[:, None] * height
    fx = np.fft.fftfreq(width)[None, :] * width
    radius = np.sqrt(fx * fx + fy * fy)
    radius[0, 0] = 1.0
    spectrum *= 1.0 / radius ** (roughness / 2)
    spectrum[radius < smallest] *= 0.3
    noise = np.real(np.fft.ifft2(spectrum))
    noise -= noise.min()
    return noise / max(1e-9, noise.max())


def streak_noise(height, width, rng, length=24):
    """Tileable noise stretched downwards, like rain streaks and rust runs."""
    base = fractal_noise(height, width, rng, roughness=1.6)
    out = np.zeros_like(base)
    for shift in range(length):
        out += np.roll(base, shift * 2, axis=0) * (1 - shift / length)
    out -= out.min()
    return out / max(1e-9, out.max())


def to_picture(array):
    """numpy (h, w, 3) floats 0..1 -> Pillow RGB picture."""
    return Image.fromarray(np.clip(array * 255 + 0.5, 0, 255).astype(np.uint8), 'RGB')


def normal_map(height_field, strength=4.0):
    """A tangent-space normal map (OpenGL / glTF convention, green = up the picture) from a height
    field (0..1), tileable."""
    h = height_field
    du = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) / 2
    dv = (np.roll(h, 1, axis=0) - np.roll(h, -1, axis=0)) / 2   # rows run down, v runs up
    nx, ny, nz = -du * strength, -dv * strength, np.ones_like(h)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    rgb = np.stack([nx / length, ny / length, nz / length], axis=-1) * 0.5 + 0.5
    return to_picture(rgb)


def blur(field, passes=1):
    for _ in range(passes):
        field = (field * 4 + np.roll(field, 1, 0) + np.roll(field, -1, 0) + np.roll(field, 1, 1) + np.roll(field, -1, 1)) / 8
    return field


def tint(colour, amount):
    return np.array(colour, dtype=float) / 255 * amount


# ----------------------------------------------------------------------------------- the textures

BRICK_COLOURS = {
    'red': [(148, 70, 50), (132, 60, 44), (160, 84, 60), (118, 58, 46), (96, 46, 38)],
    'brown': [(112, 72, 54), (100, 64, 50), (124, 82, 60), (88, 58, 46), (72, 48, 40)],
    'yellow': [(176, 146, 98), (160, 130, 86), (186, 158, 110), (146, 116, 80), (120, 96, 70)],
}


def brick(kind='red', size=1024, courses=24, bricks_per_course=7, seed=1, soot=0.35):
    """English running-bond brickwork. One tile = 0.5 x 0.5 units. Returns (colour, normal, units)."""
    rng = np.random.default_rng(seed)
    course = size / courses
    brick_width = size / bricks_per_course
    mortar = max(3, round(course * 0.12))
    ys, xs = np.mgrid[0:size, 0:size].astype(float)
    row = np.floor(ys / course).astype(int)
    offset = (row % 2) * brick_width / 2
    column = np.floor((xs + offset) / brick_width).astype(int) % bricks_per_course
    in_y = ys - row * course
    in_x = (xs + offset) - np.floor((xs + offset) / brick_width) * brick_width
    edge = np.minimum(np.minimum(in_y, course - in_y), np.minimum(in_x, brick_width - in_x))
    is_brick = edge > mortar / 2
    # one colour per brick
    palette = np.array(BRICK_COLOURS[kind], dtype=float) / 255
    ids = row * bricks_per_course + column
    picks = rng.integers(0, len(palette), size=courses * bricks_per_course)
    shade = 0.85 + 0.3 * rng.random(courses * bricks_per_course)
    brick_colour = palette[picks[ids]] * shade[ids][..., None]
    grain = fractal_noise(size, size, rng, roughness=1.2)
    brick_colour *= (0.82 + 0.3 * grain)[..., None]
    # worn, darker edges on each brick
    brick_colour *= np.clip(0.75 + edge / (course * 0.6), 0.75, 1.0)[..., None]
    mortar_colour = np.array([0.56, 0.53, 0.48]) * (0.8 + 0.35 * fractal_noise(size, size, rng, roughness=1.4))[..., None]
    colour = np.where(is_brick[..., None], brick_colour, mortar_colour)
    # soot and grime in big soft patches
    grime = fractal_noise(size, size, rng, roughness=2.6)
    colour *= (1 - soot * np.clip(grime - 0.35, 0, 1) * 1.4)[..., None]
    height = np.clip((edge - mortar / 2) / (course * 0.25), 0, 1) ** 0.5 * 0.85 + 0.15 * grain * is_brick
    return to_picture(colour), normal_map(blur(height), strength=3.0), (0.5, 0.5)


def stone(size=512, seed=2, colour=(176, 168, 150), block=(4, 2), joint=0.012):
    """Dressed stone blocks (sills, plinths, copings, cornices). One tile = 0.5 x 0.5 units."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(float) / size
    columns, rows = block
    row = np.floor(ys * rows)
    in_x = (xs * columns + (row % 2) * 0.5) % 1
    in_y = (ys * rows) % 1
    edge = np.minimum(np.minimum(in_x, 1 - in_x) / columns, np.minimum(in_y, 1 - in_y) / rows)
    base = tint(colour, 1) * (0.86 + 0.22 * fractal_noise(size, size, rng, roughness=1.3))[..., None]
    base *= (0.92 + 0.12 * rng.random((rows, columns + 1))[row.astype(int) % rows, np.floor(xs * columns + (row % 2) * 0.5).astype(int) % (columns + 1)])[..., None]
    joints = edge < joint
    base = np.where(joints[..., None], base * 0.55, base)
    height = np.clip(edge / (joint * 2.5), 0, 1)
    return to_picture(base), normal_map(blur(height, 2), strength=2.0), (0.5, 0.5)


def corrugated(size=1024, seed=3, colour=(98, 108, 114), rust=0.45):
    """Painted corrugated iron, colour only (the ribs are real shapes). Runs of rust go down the
    picture (the slope). One tile = 1 x 1 unit."""
    rng = np.random.default_rng(seed)
    paint = tint(colour, 1) * (0.88 + 0.2 * fractal_noise(size, size, rng, roughness=1.5))[..., None]
    runs = streak_noise(size, size, rng, length=40)
    rust_colour = np.array([0.42, 0.24, 0.14])
    amount = np.clip((runs - 0.55) * 2.2, 0, 1) * rust
    paint = paint * (1 - amount[..., None]) + rust_colour * amount[..., None]
    dirt = fractal_noise(size, size, rng, roughness=2.4)
    paint *= (0.8 + 0.25 * dirt)[..., None]
    return to_picture(paint), None, (1.0, 1.0)


def slate(size=1024, seed=4, colour=(84, 88, 98)):
    """A slate roof: overlapping courses of slates. One tile = 0.5 x 0.5 units."""
    rng = np.random.default_rng(seed)
    courses, per_course = 14, 9
    ys, xs = np.mgrid[0:size, 0:size].astype(float) / size
    row = np.floor(ys * courses)
    in_y = (ys * courses) % 1                          # 0 at the top of a course, 1 at its lower edge
    shifted = xs * per_course + (row % 2) * 0.5
    column = np.floor(shifted) % per_course
    in_x = shifted % 1
    ids = (row * per_course + column).astype(int)
    shade = 0.78 + 0.34 * rng.random(courses * per_course + per_course)
    hue = rng.random(courses * per_course + per_course)
    base = tint(colour, 1)[None, None, :] * shade[ids][..., None]
    base += (hue[ids][..., None] - 0.5) * np.array([0.04, 0.0, 0.05])
    base *= (0.9 + 0.15 * fractal_noise(size, size, rng, roughness=1.2))[..., None]
    gap = (np.minimum(in_x, 1 - in_x) < 0.03)
    base = np.where(gap[..., None], base * 0.45, base)
    base *= (0.75 + 0.25 * in_y)[..., None] ** 0.5     # the lower edge of the course above shades the top
    height = in_y * 0.8 + 0.2 * (~gap)
    return to_picture(base), normal_map(blur(height), strength=3.0), (0.5, 0.5)


def setts(size=1024, seed=5, colour=(92, 90, 88)):
    """Cobbled setts (granite blocks) with dark joints. One tile = 1 x 1 unit."""
    rng = np.random.default_rng(seed)
    rows, per_row = 26, 18
    ys, xs = np.mgrid[0:size, 0:size].astype(float) / size
    row = np.floor(ys * rows)
    shifted = xs * per_row + (row % 2) * 0.5 + rng.random(rows)[row.astype(int) % rows] * 0.3
    column = np.floor(shifted) % per_row
    in_x, in_y = shifted % 1, (ys * rows) % 1
    dome = np.clip(1 - ((in_x - 0.5) / 0.46) ** 4 - ((in_y - 0.5) / 0.44) ** 4, 0, 1)
    ids = (row * per_row + column).astype(int) % (rows * per_row)
    shade = 0.7 + 0.45 * rng.random(rows * per_row)
    warm = rng.random(rows * per_row)
    base = tint(colour, 1)[None, None, :] * shade[ids][..., None] + (warm[ids][..., None] - 0.5) * np.array([0.05, 0.03, 0.0])
    base *= (0.85 + 0.2 * fractal_noise(size, size, rng, roughness=1.0))[..., None]
    joint = dome < 0.05
    grit = np.array([0.16, 0.14, 0.12])
    base = np.where(joint[..., None], grit * (0.8 + 0.4 * fractal_noise(size, size, rng, roughness=0.6))[..., None], base * (0.7 + 0.3 * dome[..., None]))
    return to_picture(base), normal_map(blur(dome ** 0.6), strength=5.0), (1.0, 1.0)


def cinders(size=1024, seed=6, colour=(86, 80, 72)):
    """Trodden cinder and earth ground of a works yard: dark, gritty, with puddle-dark patches.
    One tile = 2 x 2 units."""
    rng = np.random.default_rng(seed)
    big = fractal_noise(size, size, rng, roughness=2.8)
    fine = fractal_noise(size, size, rng, roughness=0.4)
    base = tint(colour, 1)[None, None, :] * (0.7 + 0.5 * big)[..., None] * (0.85 + 0.3 * fine)[..., None]
    specks = rng.random((size, size)) > 0.985
    base = np.where(specks[..., None], base * 1.6, base)
    height = blur(fine * 0.7 + big * 0.3, 1)
    return to_picture(base), normal_map(height, strength=2.0), (2.0, 2.0)


def planks(size=512, seed=7, colour=(48, 72, 60), planks_across=8, wear=0.35):
    """Painted timber planks (doors, fences), running up the picture. One tile = 0.5 x 0.5 units."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(float) / size
    plank = np.floor(xs * planks_across)
    in_x = (xs * planks_across) % 1
    grain = fractal_noise(size, size, rng, roughness=1.0)
    grain = (grain + np.roll(grain, 3, 0) + np.roll(grain, 7, 0)) / 3
    shade = (0.85 + 0.25 * rng.random(planks_across))[plank.astype(int)]
    paint = tint(colour, 1)[None, None, :] * shade[..., None]
    wood = np.array([0.42, 0.30, 0.2]) * (0.7 + 0.5 * grain)[..., None]
    worn = np.clip((fractal_noise(size, size, rng, roughness=1.8) - (1 - wear)) * 4, 0, 1)
    base = paint * (1 - worn[..., None]) + wood * worn[..., None]
    gap = np.minimum(in_x, 1 - in_x) < 0.04
    base = np.where(gap[..., None], base * 0.35, base)
    height = np.clip(np.minimum(in_x, 1 - in_x) / 0.08, 0, 1)
    return to_picture(base), normal_map(blur(height), strength=2.5), (0.5, 0.5)


def riveted(size=512, seed=8, colour=(70, 64, 58)):
    """Riveted iron plates (a water tank, girders). One tile = 0.5 x 0.5 units."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(float) / size
    in_x, in_y = (xs * 2) % 1, (ys * 2) % 1
    edge = np.minimum(np.minimum(in_x, 1 - in_x), np.minimum(in_y, 1 - in_y))
    base = tint(colour, 1)[None, None, :] * (0.8 + 0.3 * fractal_noise(size, size, rng, roughness=1.6))[..., None]
    runs = streak_noise(size, size, rng, length=30)
    base = base * (1 - 0.4 * np.clip(runs - 0.6, 0, 1)[..., None]) + np.array([0.3, 0.16, 0.09]) * 0.4 * np.clip(runs - 0.6, 0, 1)[..., None]
    rivet_x, rivet_y = (xs * 16) % 1, (ys * 16) % 1
    near_seam = edge < 0.06
    rivet = near_seam & (((rivet_x - 0.5) ** 2 + (rivet_y - 0.5) ** 2) < 0.06)
    seam = edge < 0.008
    base = np.where(seam[..., None], base * 0.5, base)
    base = np.where(rivet[..., None], base * 1.25, base)
    height = rivet * 1.0 + (~seam) * 0.3
    return to_picture(base), normal_map(blur(height.astype(float), 2), strength=3.0), (0.5, 0.5)


def window_glass(columns=4, rows=6, pixels=(256, 384), seed=9, broken=0.06):
    """One window: small panes in a cast-iron glazing grid. Returns (colour, glow): the glow picture
    is where warm light shows through when the room behind is lit (bars stay dark)."""
    rng = np.random.default_rng(seed)
    width, height = pixels
    ys, xs = np.mgrid[0:height, 0:width].astype(float)
    pane_x, pane_y = xs / width * columns, ys / height * rows
    in_x, in_y = pane_x % 1, pane_y % 1
    bar = (np.minimum(in_x, 1 - in_x) * width / columns < 3.2) | (np.minimum(in_y, 1 - in_y) * height / rows < 3.2)
    frame = (xs < 7) | (xs > width - 8) | (ys < 7) | (ys > height - 8)
    ids = (np.floor(pane_y) * columns + np.floor(pane_x)).astype(int)
    tone = 0.75 + 0.4 * rng.random(columns * rows)
    dark = rng.random(columns * rows) < broken
    sky = (0.16 + 0.1 * (1 - ys / height))[..., None] * np.array([0.75, 0.9, 1.0])
    glass = sky * tone[ids][..., None]
    glass += 0.12 * np.clip(1 - np.abs(in_x - in_y * 0.6 - 0.2) * 6, 0, 1)[..., None]   # a streak of reflection
    iron = np.array([0.1, 0.11, 0.11])
    colour = np.where((bar | frame)[..., None], iron, glass)
    warm = np.array([1.0, 0.68, 0.34]) * (tone[ids] * (0.75 + 0.25 * (ys / height)))[..., None]
    warm = np.where(dark[ids][..., None], warm * 0.15, warm)
    glow = np.where((bar | frame)[..., None], 0.0, warm)
    return to_picture(colour), to_picture(glow)


def interior(width=512, height=512, seed=10):
    """The inside of a busy works seen through an open door: warm haze, dark machine shapes, lamps."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:height, 0:width].astype(float) / np.array([height, width])[:, None, None]
    warm = np.array([1.0, 0.62, 0.3]) * (0.55 + 0.45 * (1 - ys))[..., None]
    picture = warm * (0.8 + 0.3 * fractal_noise(height, width, rng, roughness=2.4))[..., None]
    shapes = np.zeros((height, width))
    for _ in range(9):
        x0, w = rng.random(), 0.05 + 0.12 * rng.random()
        top = 0.45 + 0.35 * rng.random()
        shapes = np.maximum(shapes, ((xs > x0) & (xs < x0 + w) & (ys > top)).astype(float))
    for _ in range(5):
        x0 = rng.random()
        shapes = np.maximum(shapes, ((np.abs(xs - x0) < 0.006) & (ys < 0.6)).astype(float))   # belts
    picture = picture * (1 - 0.82 * shapes[..., None])
    for _ in range(4):
        cx, cy = rng.random(), 0.1 + 0.2 * rng.random()
        picture += np.array([1.0, 0.85, 0.6]) * np.exp(-(((xs - cx) * 30) ** 2 + ((ys - cy) * 30) ** 2))[..., None]
    return to_picture(picture)


def wood(size=512, seed=11, colour=(104, 66, 40)):
    """Polished wood (a desk top): long grain along the picture. One tile = 1 x 1 unit."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:size, 0:size].astype(float) / size
    warp = fractal_noise(size, size, rng, roughness=2.2)
    rings = np.sin((ys * 40 + warp * 6) * math.pi) * 0.5 + 0.5
    fine = fractal_noise(size, size, rng, roughness=0.8)
    streak = np.repeat(fractal_noise(1, size, rng, roughness=1.0), size, axis=0)
    base = tint(colour, 1)[None, None, :] * (0.75 + 0.2 * rings + 0.15 * streak + 0.1 * fine)[..., None]
    return to_picture(base), normal_map(blur(rings * 0.3 + fine * 0.2), strength=1.0), (1.0, 1.0)


def leather(size=512, seed=12, colour=(40, 66, 54)):
    """Leather (a desk blotter): fine crinkle, soft sheen."""
    rng = np.random.default_rng(seed)
    crinkle = fractal_noise(size, size, rng, roughness=0.9)
    base = tint(colour, 1)[None, None, :] * (0.8 + 0.3 * crinkle)[..., None]
    return to_picture(base), normal_map(blur(crinkle), strength=2.0), (0.5, 0.5)


def paper_stack_edge(size=512, seed=13, colour=(226, 218, 198)):
    """The edge of a stack of paper: many thin lines, slightly uneven."""
    rng = np.random.default_rng(seed)
    ys = np.arange(size)[:, None].repeat(size, 1).astype(float)
    lines = np.sin(ys * 0.9 + fractal_noise(size, size, rng, roughness=2.0) * 5) * 0.5 + 0.5
    base = tint(colour, 1)[None, None, :] * (0.78 + 0.22 * lines)[..., None]
    return to_picture(base), None, (0.2, 0.2)


ALL = {
    'brick-red': lambda: brick('red'), 'brick-brown': lambda: brick('brown', seed=21),
    'brick-yellow': lambda: brick('yellow', seed=22), 'stone': stone, 'corrugated': corrugated, 'slate': slate,
    'setts': setts, 'cinders': cinders, 'planks': planks, 'riveted': riveted, 'wood': wood, 'leather': leather,
}

if __name__ == '__main__':
    folder = sys.argv[1] if len(sys.argv) > 1 else 'textures-preview'
    os.makedirs(folder, exist_ok=True)
    for name, make in ALL.items():
        colour, normal, units = make()
        colour.save(os.path.join(folder, f'{name}.jpg'), quality=92)
        if normal: normal.save(os.path.join(folder, f'{name}-normal.png'))
    colour, glow = window_glass()
    colour.save(os.path.join(folder, 'window.jpg')); glow.save(os.path.join(folder, 'window-glow.jpg'))
    interior().save(os.path.join(folder, 'interior.jpg'))
    print('wrote textures to', folder)
