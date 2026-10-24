"""What this does: the GROUND AND WATER part of the canal lock side (owner ground_and_water): the canal bed, the towpath (gravel, in three pieces round the trench for the stone steps), the grass verges either side, and two water surfaces
(the lock chamber and the higher pound behind the gate).
Built by the verifier from the plugin's stage template. Idempotent: running it twice leaves the same scene.
A concrete example of use: apply({}) makes eight ground objects and two water objects in the collection "Place: ground_and_water".
"""
import os
import sys

import bpy
import numpy as np

KIT = os.environ.get('EXPLAINER_FILM_KIT', '')
if KIT and os.path.join(KIT, 'place-kit') not in sys.path:
    sys.path.insert(0, os.path.join(KIT, 'place-kit'))
import place_kit as pk  # noqa: E402

OWNER = 'ground_and_water'
BED_Z = -2.0
WATER_Z = -1.1
POUND_Z = -0.45


def grid_mesh(name, x0, x1, y0, y1, z, step, seed=0, bumpiness=0.0):
    """A grid of squares about `step` metres across over the rectangle, at height z with a little unevenness (bumpiness, metres)."""
    nx = int(round((x1 - x0) / step))
    ny = int(round((y1 - y0) / step))
    xs = np.linspace(x0, x1, nx + 1)
    ys = np.linspace(y0, y1, ny + 1)
    rng = np.random.default_rng(seed)
    heights = z + bumpiness * rng.uniform(-1.0, 1.0, (ny + 1, nx + 1))
    vertices = [(float(xs[i]), float(ys[j]), float(heights[j, i])) for j in range(ny + 1) for i in range(nx + 1)]
    faces = []
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            faces.append((a, a + 1, a + nx + 2, a + nx + 1))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    return mesh


def apply(options):
    pk.forget_part(OWNER)
    pk.begin_part(OWNER)
    seed = int(options.get('seed', 5))
    # the bed runs under the towpath too, so that the steps and cheek walls have something to stand on
    pk.new_part_object(OWNER, 'ground.mud', 'Ground canal bed', grid_mesh('Ground canal bed', -6.5, 6.5, -3.0, 2.95, BED_Z, 0.15, seed=seed, bumpiness=0.0))   # a flat bed: everything that stands on it, and everything that stands on that, then lines up exactly
    # the towpath: gravel on both sides of the trench for the steps and a short strip behind it. The trench edges sit 2 cm outside the stone that fills it, so the stone's
    # corners never touch the towpath (the audit looks at the ground under a part's corners).
    pk.new_part_object(OWNER, 'ground.gravel', 'Ground towpath west', grid_mesh('Ground towpath west', -7.0, -3.62, -2.9, -0.5, 0.0, 0.08, seed=seed + 1, bumpiness=0.006))
    pk.new_part_object(OWNER, 'ground.gravel', 'Ground towpath east', grid_mesh('Ground towpath east', -1.98, 7.0, -2.9, -0.5, 0.0, 0.08, seed=seed + 4, bumpiness=0.006))
    pk.new_part_object(OWNER, 'ground.gravel', 'Ground towpath end', grid_mesh('Ground towpath end', -3.62, -1.98, -2.9, -2.84, 0.0, 0.06, seed=seed + 6, bumpiness=0.006))
    pk.new_part_object(OWNER, 'ground.grass', 'Ground back verge', grid_mesh('Ground back verge', -7.0, 7.0, -9.0, -2.9, 0.0, 0.25, seed=seed + 2, bumpiness=0.02))
    pk.new_part_object(OWNER, 'ground.grass', 'Ground far verge', grid_mesh('Ground far verge', -7.0, 7.0, 2.9, 9.0, 0.0, 0.25, seed=seed + 3, bumpiness=0.02))
    # the water of the lock chamber (part-emptied) and the higher pound behind the gate
    pk.new_part_object(OWNER, 'water.still', 'Water lock chamber', grid_mesh('Water lock chamber', -6.5, 4.0, 0.0, 2.4, WATER_Z, 0.5))
    pk.new_part_object(OWNER, 'water.still', 'Water upper pound', grid_mesh('Water upper pound', 4.0, 6.5, 0.0, 2.4, POUND_Z, 0.5))
