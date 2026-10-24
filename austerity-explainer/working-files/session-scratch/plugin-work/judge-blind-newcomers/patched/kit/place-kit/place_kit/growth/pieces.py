"""What this does: builds the small 3D PIECES the scatter stands on the ground, as numpy arrays (vertices and faces), in code and in a designed, slightly chunky style:
a tuft of 5 to 9 folded blades, a low rosette of round leaves, a tall stalk with toothed leaves (nettle), an arching frond (fern), an arching stem (bramble), a lumpy moss
cushion, a single leaf, a clump of pine needles, a bent stick, a few straws and a dung lump. Every kind is made in several VARIANTS (at least 8 tuft meshes), each at a
height of 1 unit with its root at the origin and z up; the scatter scales them (a range of at least 3 to 1) and tints them. No photographic noise: few, big, clean shapes.
Plain numpy, no Blender, so it is tested without Blender. A piece is {'vertices': (n, 3), 'faces': [tuple of vertex numbers]}.
A concrete example: make_variants('tuft', 8, seed=1) gives eight different tufts, each with 5 to 9 blades; every vertex has z between 0 and about 1.
"""
import math

import numpy as np


def _rng(seed):
    return np.random.default_rng(int(seed))


def _strip(points, widths, normal_hint=(0.0, 0.0, 1.0)):
    """A ribbon along a polyline of points (k, 3) with a width at each point: returns vertices (2k, 3) and quads (k - 1)."""
    points = np.asarray(points, dtype=np.float64)
    count = len(points)
    tangents = np.gradient(points, axis=0)
    tangents /= np.maximum(np.linalg.norm(tangents, axis=1, keepdims=True), 1e-9)
    side = np.cross(tangents, np.asarray(normal_hint, dtype=np.float64))
    length = np.linalg.norm(side, axis=1, keepdims=True)
    side = np.where(length > 1e-6, side / np.maximum(length, 1e-9), np.array([1.0, 0.0, 0.0]))
    left = points - side * (np.asarray(widths)[:, None] / 2)
    right = points + side * (np.asarray(widths)[:, None] / 2)
    vertices = np.empty((count * 2, 3))
    vertices[0::2], vertices[1::2] = left, right
    faces = [(2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2) for k in range(count - 1)]
    return vertices, faces


def _merge(parts):
    vertices, faces, offset = [], [], 0
    for v, f in parts:
        vertices.append(v)
        faces += [tuple(i + offset for i in face) for face in f]
        offset += len(v)
    return {'vertices': np.vstack(vertices), 'faces': faces}


def tuft(rng):
    blades = int(rng.integers(5, 10))
    parts = []
    for _ in range(blades):
        angle = rng.uniform(0, 2 * math.pi)
        radius = rng.uniform(0.0, 0.07)
        base = np.array([math.cos(angle) * radius, math.sin(angle) * radius, 0.0])
        height = rng.uniform(0.55, 1.0)
        lean = rng.uniform(0.15, 0.6)
        direction = np.array([math.cos(angle), math.sin(angle), 0.0])
        t = np.linspace(0, 1, 4)
        bend = (t ** 1.6) * lean * height
        pts = np.stack([base[0] + direction[0] * bend, base[1] + direction[1] * bend, height * t * (1 - 0.15 * t)], axis=1)
        width = rng.uniform(0.07, 0.11) * (1 - 0.8 * t)
        parts.append(_strip(pts, width, (-direction[1], direction[0], 0.0)))
    return _merge(parts)


def rosette(rng):
    leaves = int(rng.integers(6, 10))
    parts = []
    for k in range(leaves):
        angle = 2 * math.pi * k / leaves + rng.uniform(-0.2, 0.2)
        direction = np.array([math.cos(angle), math.sin(angle), 0.0])
        length = rng.uniform(0.6, 1.0)
        t = np.linspace(0.05, 1, 4)
        pts = np.stack([direction[0] * t * length, direction[1] * t * length, 0.12 * np.sin(t * math.pi) * length], axis=1)
        width = 0.35 * np.sin(np.clip(t, 0.05, 1) * math.pi) * length + 0.05
        parts.append(_strip(pts, width, (0.0, 0.0, 1.0)))
    return _merge(parts)


def stalk(rng):
    parts = []
    height = 1.0
    t = np.linspace(0, 1, 5)
    lean = rng.uniform(-0.08, 0.08, 2)
    stem = np.stack([lean[0] * t ** 2, lean[1] * t ** 2, height * t], axis=1)
    parts.append(_strip(stem, 0.035 * np.ones(5), (1.0, 0.0, 0.0)))
    for k in range(int(rng.integers(4, 7))):
        z = 0.2 + 0.7 * k / 6
        angle = k * 2.4 + rng.uniform(-0.3, 0.3)
        direction = np.array([math.cos(angle), math.sin(angle), 0.0])
        span = rng.uniform(0.25, 0.4) * (1.1 - z * 0.5)
        s = np.linspace(0, 1, 3)
        leaf = np.stack([direction[0] * s * span + lean[0] * z ** 2, direction[1] * s * span + lean[1] * z ** 2, z + 0.08 * np.sin(s * math.pi) - 0.05 * s], axis=1)
        parts.append(_strip(leaf, 0.14 * np.sin(np.clip(s, 0.1, 1) * math.pi) + 0.03, (0.0, 0.0, 1.0)))
    return _merge(parts)


def frond(rng):
    parts = []
    for _ in range(int(rng.integers(4, 7))):
        angle = rng.uniform(0, 2 * math.pi)
        direction = np.array([math.cos(angle), math.sin(angle), 0.0])
        t = np.linspace(0, 1, 6)
        reach = rng.uniform(0.55, 1.0)
        pts = np.stack([direction[0] * reach * t ** 1.4, direction[1] * reach * t ** 1.4, np.sin(t * 2.2) * 0.55 * reach], axis=1)
        parts.append(_strip(pts, (0.22 * np.sin(np.clip(t, 0.05, 1) * math.pi * 0.9) + 0.03) * reach, (-direction[1], direction[0], 0.0)))
    return _merge(parts)


def arch(rng):
    parts = []
    for _ in range(int(rng.integers(2, 4))):
        angle = rng.uniform(0, 2 * math.pi)
        direction = np.array([math.cos(angle), math.sin(angle), 0.0])
        t = np.linspace(0, 1, 6)
        reach = rng.uniform(0.7, 1.2)
        pts = np.stack([direction[0] * reach * t, direction[1] * reach * t, 0.9 * np.sin(t * math.pi * 0.85)], axis=1)
        parts.append(_strip(pts, 0.05 * (1 - 0.6 * t), (-direction[1], direction[0], 0.0)))
        for k in range(2, 5):
            point = pts[k]
            leaf_direction = np.array([math.cos(angle + 1.2), math.sin(angle + 1.2), 0.3])
            leaf = np.stack([point, point + leaf_direction * 0.18], axis=0)
            parts.append(_strip(np.vstack([leaf[0], (leaf[0] + leaf[1]) / 2 + np.array([0, 0, 0.03]), leaf[1]]), np.array([0.02, 0.1, 0.02]), (0, 0, 1.0)))
    return _merge(parts)


def _sphere(rng, rings, segments, flatten, lumpy):
    vertices, faces = [(0.0, 0.0, 0.0)], []
    for r in range(1, rings + 1):
        phi = (r / rings) * math.pi / 2
        for s in range(segments):
            theta = 2 * math.pi * s / segments
            radius = 1.0 + rng.uniform(-lumpy, lumpy)
            vertices.append((math.sin(phi) * math.cos(theta) * radius, math.sin(phi) * math.sin(theta) * radius, math.cos(phi) * flatten * radius))
    for s in range(segments):
        faces.append((0, 1 + s, 1 + (s + 1) % segments))
    for r in range(1, rings):
        for s in range(segments):
            a, b = 1 + (r - 1) * segments + s, 1 + (r - 1) * segments + (s + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    return {'vertices': np.array(vertices), 'faces': faces}


def cushion(rng):
    parts = []
    for _ in range(int(rng.integers(3, 6))):
        lump = _sphere(rng, 3, 8, rng.uniform(0.35, 0.6), 0.18)
        shift = np.array([rng.uniform(-0.5, 0.5), rng.uniform(-0.5, 0.5), 0.0])
        parts.append((lump['vertices'] * rng.uniform(0.35, 0.6) + shift, lump['faces']))
    return _merge(parts)


def flake(rng):
    t = np.linspace(0, 1, 4)
    pts = np.stack([t * 0.9, 0.08 * np.sin(t * 5) * rng.uniform(0.5, 1.0), 0.06 * np.sin(t * math.pi) * rng.uniform(0.5, 1.5)], axis=1)
    piece = _strip(pts, 0.55 * np.sin(np.clip(t, 0.08, 1) * math.pi * 0.95) + 0.04, (0.0, 0.0, 1.0))
    return {'vertices': piece[0], 'faces': piece[1]}


def clump(rng):
    parts = []
    for _ in range(int(rng.integers(8, 14))):
        angle = rng.uniform(0, 2 * math.pi)
        direction = np.array([math.cos(angle), math.sin(angle), 0.0])
        t = np.linspace(0, 1, 2)
        pts = np.stack([direction[0] * t * rng.uniform(0.6, 1.0), direction[1] * t * rng.uniform(0.6, 1.0), 0.08 * t + 0.02], axis=1)
        parts.append(_strip(pts, np.array([0.05, 0.02]), (0, 0, 1.0)))
    return _merge(parts)


def stick(rng):
    t = np.linspace(0, 1, 4)
    bend = rng.uniform(-0.1, 0.1, 2)
    pts = np.stack([t, bend[0] * np.sin(t * math.pi), 0.03 + bend[1] * np.sin(t * math.pi) * 0.3], axis=1)
    piece = _strip(pts, 0.06 * (1 - 0.5 * t), (0.0, 0.0, 1.0))
    return {'vertices': piece[0], 'faces': piece[1]}


def straw(rng):
    parts = []
    for _ in range(int(rng.integers(3, 6))):
        angle = rng.uniform(0, math.pi)
        direction = np.array([math.cos(angle), math.sin(angle), 0.0])
        t = np.linspace(-0.5, 0.5, 3)
        pts = np.stack([direction[0] * t, direction[1] * t, 0.02 + 0.03 * rng.uniform(0, 1) * (1 - 4 * t ** 2)], axis=1)
        parts.append(_strip(pts, np.full(3, 0.04), (0, 0, 1.0)))
    return _merge(parts)


def lump(rng):
    return _sphere(rng, 3, 7, rng.uniform(0.5, 0.8), 0.2)


BUILDERS = {'tuft': tuft, 'rosette': rosette, 'stalk': stalk, 'frond': frond, 'arch': arch, 'cushion': cushion, 'flake': flake, 'clump': clump, 'stick': stick, 'straw': straw, 'lump': lump}


def normalise_height(piece):
    """Scales a piece so its tallest point is 1 (a flat piece is scaled by its longest side instead) and puts its lowest point at z = 0."""
    vertices = np.array(piece['vertices'], dtype=np.float64)
    vertices[:, 2] -= vertices[:, 2].min()
    extent = max(vertices[:, 2].max(), np.ptp(vertices[:, 0]), np.ptp(vertices[:, 1]), 1e-6)
    return {'vertices': vertices / extent, 'faces': piece['faces']}


def make_variants(builder, count, seed=1):
    """`count` different pieces of one builder kind, each normalised to a height (or length) of 1 with its root at the origin."""
    rng = _rng(seed)
    return [normalise_height(BUILDERS[builder](rng)) for _ in range(int(count))]


def triangle_count(piece):
    return sum(max(len(face) - 2, 0) for face in piece['faces'])


def pull_toward_grey(rgb, share=0.45):
    """A colour (0..1 each) pulled `share` of the way toward its own grey, so scatter colours sit in the place's style."""
    r, g, b = rgb
    grey = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return tuple(c + (grey - c) * share for c in (r, g, b))
