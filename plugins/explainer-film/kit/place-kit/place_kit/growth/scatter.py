"""What this does: the GROWTH step: stands small 3D plants and litter on the ground: tufts, clover, nettles, ferns, brambles, moss cushions (plants) and leaves, pine needles, sticks,
straw and clods (litter). Where each goes comes from the plan masks and the species' likings (damp, shady, the foot of walls, road edges), cut by EXACT-ZERO gates: nothing
on a wheel track, a worn path (footfall 0.6 or more), the crown of a road (0.7 or more), kept-clear ground (0.5 or more), in a puddle, inside a wall or prop, and plants never within
5 cm of a litter piece. The pieces are real geometry (pieces.py: chunky, designed shapes, several variants, sizes in a range of at least 3 to 1, colours pulled 45 percent toward grey),
laid out in plain numpy and joined into a few meshes (one per kind), each marked pk_scatter so the construction check leaves it out, and each remembering its roots so the audit counts
the keep-out cases again from the roots and the masks. Running it twice removes what the first run made and makes the same again (a fixed seed). It needs Blender (bpy) and numpy.
Density: a floor of about half a candidate per square metre even for a "kept" look (a place with no growth at all reads as a model), more for a neglected one, then thinned by the sites.
A concrete example: grow_things(settings) on a 14 m ground gives about a hundred tufts, clover, nettles and moss cushions and a few hundred leaves, none on a wheel track.
"""
import math

import numpy as np

import bpy

from .. import house_numbers, names, parts, plan2d, roles as roles_module, scene_read, settings_file
from ..wear import masks, seed as seed_module
from . import keepout, pieces

COLLECTION = names.MADE_COLLECTION
MATERIAL = 'PK Scatter'
PIECES_PER_OBJECT = 20000
PLANT_PER_M2 = (0.5, 2.0)            # floor, and per unit of the look's weeds amount
LITTER_PER_M2 = (0.6, 2.5)
VARIANTS = {'tuft': 10, 'rosette': 6, 'stalk': 5, 'frond': 5, 'arch': 4, 'cushion': 5, 'flake': 8, 'clump': 4, 'stick': 5, 'straw': 4, 'lump': 4}


def hex_rgb(text):
    text = text.lstrip('#')
    return tuple(int(text[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def to_linear(rgb):
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb)


def remove_old():
    removed = 0
    for obj in list(bpy.data.objects):
        if obj.get(names.SCATTER) and obj.get(names.MADE):
            mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
            removed += 1
    for block in list(bpy.data.texts):
        if block.name.startswith('pk_roots_'):
            bpy.data.texts.remove(block)
    return removed


def scatter_material():
    material = bpy.data.materials.get(MATERIAL)
    if material is None:
        material = bpy.data.materials.new(MATERIAL)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
    attribute = tree.nodes.new('ShaderNodeAttribute')
    attribute.attribute_type = 'GEOMETRY'
    attribute.attribute_name = 'Col'
    tree.links.new(attribute.outputs['Color'], principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.8
    tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    material[names.MADE] = 1
    return material


def made_collection():
    collection = bpy.data.collections.get(COLLECTION)
    if collection is None:
        collection = bpy.data.collections.new(COLLECTION)
    if collection.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(collection)
    return collection


def sample_surface(vertices, triangles, per_m2, rng, cap):
    """Random points on the up-facing triangles of a surface (area-weighted): (points (n, 3), normals). per_m2 candidates per square metre of flat plan area."""
    a, b, c = vertices[triangles[:, 0]], vertices[triangles[:, 1]], vertices[triangles[:, 2]]
    cross = np.cross(b - a, c - a)
    area_plan = np.abs(cross[:, 2]) / 2.0
    normal_length = np.linalg.norm(cross, axis=1)
    up = (cross[:, 2] / np.maximum(normal_length, 1e-12)) > 0.3
    expected = area_plan * per_m2 * up
    counts = rng.poisson(expected)
    total = int(min(counts.sum(), cap))
    if total == 0:
        return np.zeros((0, 3))
    which = np.repeat(np.arange(len(triangles)), counts)
    if len(which) > total:
        which = rng.choice(which, total, replace=False)
    r1, r2 = rng.random(len(which)), rng.random(len(which))
    flip = r1 + r2 > 1
    r1, r2 = np.where(flip, 1 - r1, r1), np.where(flip, 1 - r2, r2)
    return a[which] + (b[which] - a[which]) * r1[:, None] + (c[which] - a[which]) * r2[:, None]


def site_weights(species, points, plan):
    """How much a species likes each point (0..1), before the gates: its likings times the masks."""
    likes = species['likes']
    damp = plan.sample('dampness', points)
    shade = plan.sample('shade', points)
    wall_foot = 1.0 - plan2d.smoothstep(0.0, 0.8, plan.sample_metres('wall_dist', points))
    edge = 1.0 - plan2d.smoothstep(0.0, 1.5, plan.sample_metres('prop_dist', points))
    weight = likes['base'] + likes['damp'] * damp + likes['shade'] * shade + likes['wall_foot'] * wall_foot + likes['edge'] * edge
    return np.clip(weight / 1.6, 0.0, 1.0)


def gates(points, plan):
    """True where a point may hold a piece: not on a worn path, a crown, kept-clear ground, a wheel track, a puddle, or inside a wall or prop."""
    footfall = plan.sample('footfall', points) < house_numbers.value('place_wear.exact_zero_gate_footfall')
    crown = plan.sample('crown', points) < house_numbers.value('place_wear.exact_zero_gate_crown')
    clear = plan.sample('keepclear', points) < house_numbers.value('place_wear.exact_zero_gate_keepclear')
    track = plan.sample('track', points) < 0.5
    dry = plan.sample('above_water', points) >= 0.5
    outside = (plan.sample_metres('wall_dist', points) > 0.06) & (plan.sample_metres('prop_dist', points) > 0.04)
    return footfall & crown & clear & track & dry & outside


def nearest_distance(points, others):
    """The distance from each point to the nearest of `others` (plan view); 9 where there are none."""
    if len(others) == 0:
        return np.full(len(points), 9.0)
    result = np.full(len(points), 9.0)
    step = max(1, int(2e7 // max(len(others), 1)))
    for start in range(0, len(points), step):
        chunk = points[start:start + step, :2]
        result[start:start + step] = np.sqrt(((chunk[:, None, :] - others[None, :, :2]) ** 2).sum(axis=2)).min(axis=1)
    return result


def build_mesh(kind, species, points, rng, variants, colours):
    """One joined mesh object's data for all pieces of one kind: vertices, faces and a colour per vertex."""
    low, high = species['size_cm']
    count = len(points)
    sizes = np.exp(rng.uniform(np.log(low / 100.0), np.log(high / 100.0), count))
    angles = rng.uniform(0, 2 * math.pi, count)
    choice = rng.integers(0, len(variants), count)
    tint = rng.uniform(0.88, 1.1, count)
    palette_choice = rng.integers(0, len(colours), count)
    all_vertices, all_faces, all_colours, offset = [], [], [], 0
    for variant_index, variant in enumerate(variants):
        members = np.nonzero(choice == variant_index)[0]
        if len(members) == 0:
            continue
        v = variant['vertices']
        cos, sin = np.cos(angles[members]), np.sin(angles[members])
        scaled = v[None, :, :] * sizes[members][:, None, None]
        x = scaled[:, :, 0] * cos[:, None] - scaled[:, :, 1] * sin[:, None]
        y = scaled[:, :, 0] * sin[:, None] + scaled[:, :, 1] * cos[:, None]
        out = np.stack([x, y, scaled[:, :, 2]], axis=2) + points[members][:, None, :]
        all_vertices.append(out.reshape(-1, 3))
        base = np.arange(len(members))[:, None] * len(v) + offset
        for face in variant['faces']:
            all_faces.append((base + np.array(face)[None, :]).reshape(len(members), -1))
        palette = np.array(colours)[palette_choice[members]] * tint[members][:, None]
        all_colours.append(np.repeat(palette, len(v), axis=0))
        offset += len(members) * len(v)
    if not all_vertices:
        return None
    return np.vstack(all_vertices), all_faces, np.vstack(all_colours)


def make_object(kind, group, vertices, face_blocks, colour_array, roots, chunk):
    mesh = bpy.data.meshes.new(f'PK scatter {kind} {chunk}')
    faces = []
    for block in face_blocks:
        faces.extend(tuple(int(i) for i in row) for row in block)
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    mesh.update()
    attribute = mesh.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    rgba = np.concatenate([np.clip(colour_array, 0, 1), np.ones((len(colour_array), 1))], axis=1).astype(np.float32)
    attribute.data.foreach_set('color', rgba.ravel())
    mesh.materials.append(scatter_material())
    obj = bpy.data.objects.new(f'PK scatter {kind} {chunk}', mesh)
    made_collection().objects.link(obj)
    obj[names.SCATTER] = 1
    obj[names.MADE] = 1
    obj[names.ROLE] = 'never.scatter'
    obj['pk_scatter_kind'] = kind
    obj['pk_scatter_group'] = group
    obj['pk_count'] = int(len(roots))
    keepout.store_roots(obj, roots)
    return obj


def ground_area(ground_objects):
    """The plan-view area in square metres of the ground objects' triangles."""
    total = 0.0
    for obj in ground_objects:
        vertices, triangles = parts.world_triangles(obj)
        if len(triangles):
            a, b, c = (vertices[triangles[:, i]] for i in range(3))
            total += float(np.abs((b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (c[:, 0] - a[:, 0]) * (b[:, 1] - a[:, 1])).sum() / 2.0)
    return total


def choose_roots(group, kinds, ground_objects, plan, amount, per_m2, existing_litter, rng, budget):
    """One round of picking root points: sample the ground, cut by the exact-zero gates, give each point a species, keep a point with the chance its species likes it,
    and keep plants 5 cm clear of litter. Returns {kind: roots}."""
    candidates = []
    for obj in ground_objects:
        vertices, triangles = parts.world_triangles(obj)
        if len(triangles):
            points = sample_surface(vertices, triangles, per_m2, rng, int(budget))
            if len(points):
                candidates.append(points)
    if not candidates:
        return {}
    points = np.vstack(candidates)
    points = points[gates(points, plan)]
    weights = {k: spec['share'] for k, spec in kinds.items()}
    total_share = sum(weights.values())
    kind_names = list(kinds)
    probabilities = np.array([weights[k] / total_share for k in kind_names])
    assigned = rng.choice(len(kind_names), len(points), p=probabilities)
    clearance = house_numbers.value('place_wear.litter_clearance_metres')
    roots = {}
    for index, kind in enumerate(kind_names):
        chosen = points[assigned == index]
        if len(chosen) == 0:
            continue
        accept = rng.random(len(chosen)) < site_weights(kinds[kind], chosen, plan) * (0.5 + amount)
        chosen = chosen[accept]
        if group == 'plant' and len(existing_litter):
            chosen = chosen[nearest_distance(chosen, existing_litter) >= clearance]
        if len(chosen):
            roots[kind] = chosen
    return roots


def place_group(group, settings, ground_objects, plan, amount, density_multiplier, existing_litter, rng_seed):
    """Plants or litter: returns (roots by kind, objects made). When the first round leaves fewer pieces than the audit's minimum per 100 square metres (with a margin), more rounds
    are added (up to 4, each adding half as many candidates again) so a plain request never fails the count by a few pieces."""
    species_table = settings_file.species_table()
    kinds = {k: v for k, v in species_table['kinds'].items() if v['group'] == group}
    floor, per_unit = PLANT_PER_M2 if group == 'plant' else LITTER_PER_M2
    per_m2 = max(floor, per_unit * amount) * density_multiplier
    budget = house_numbers.value('place_audit.scatter_pieces_max')
    rng = np.random.default_rng(rng_seed)
    minimum = house_numbers.value('place_audit.plants_min_per_100_square_metres' if group == 'plant' else 'place_audit.litter_min_per_100_square_metres')
    needed = int(np.ceil(minimum * 1.15 * ground_area(ground_objects) / 100.0))
    roots_by_kind = choose_roots(group, kinds, ground_objects, plan, amount, per_m2, existing_litter, rng, budget)
    for extra_round in range(4):
        if sum(len(r) for r in roots_by_kind.values()) >= needed:
            break
        more = choose_roots(group, kinds, ground_objects, plan, amount, per_m2 * 0.5, existing_litter, rng, budget)
        for kind, extra in more.items():
            roots_by_kind[kind] = np.vstack([roots_by_kind[kind], extra]) if kind in roots_by_kind else extra
    grey = species_table['tuning']['grey_pull']
    made = []
    for index, kind in enumerate(kinds):
        chosen = roots_by_kind.get(kind)
        if chosen is None or len(chosen) == 0:
            continue
        species = kinds[kind]
        variants = pieces.make_variants(species['builder'], VARIANTS.get(species['builder'], 4), seed=rng_seed + index)
        colours = [to_linear(pieces.pull_toward_grey(hex_rgb(species_table['palette'][c]), grey)) for c in species['colours']]
        for chunk, start in enumerate(range(0, len(chosen), PIECES_PER_OBJECT)):
            part = chosen[start:start + PIECES_PER_OBJECT]
            built = build_mesh(kind, species, part, rng, variants, colours)
            if built is None:
                continue
            vertices, face_blocks, colour_array = built
            made.append(make_object(kind, group, vertices, face_blocks, colour_array, part, chunk))
    return roots_by_kind, made


def scatter_litter(settings, ground_objects, plan, amount, density_multiplier=1.0, seed=1):
    """Leaves, pine needles, sticks, straw, clods. Returns (roots by kind, objects made)."""
    return place_group('litter', settings, ground_objects, plan, amount, density_multiplier, np.zeros((0, 3)), seed)


def scatter_plants(settings, ground_objects, plan, amount, existing_litter, density_multiplier=1.0, seed=1):
    """Tufts, clover, nettles, ferns, brambles, moss cushions; never within 5 cm of litter. Returns (roots by kind, objects made)."""
    return place_group('plant', settings, ground_objects, plan, amount, density_multiplier, existing_litter, seed)


def grow_things(settings, owner=None, density=None):
    """The growth pass (see the note at the top). Returns {'summary', 'plants', 'litter', 'objects'}."""
    table = settings_file.roles_table()
    rules = settings.rules_dict()
    removed = remove_old()
    objects = [o for o in scene_read.mesh_objects(only_visible=True) if not scene_read.is_scatter(o)]
    tagged = roles_module.tag_objects([scene_read.object_facts(o) for o in objects], rules, table)['by_object']
    ground = []
    for obj in objects:
        role = tagged[obj.name]['role'] or ''
        if not role.startswith('ground.'):
            continue
        req = roles_module.requirements(role, table, rules)
        wants_plants = 'plants' in (set(req['required']) | set(req['wanted']))
        if wants_plants and not roles_module.off_entries_for(role, 'plants', rules):
            ground.append(obj)
    if not ground:
        return {'summary': 'no outdoor ground to grow things on (nothing to do)', 'plants': 0, 'litter': 0, 'objects': [], 'removed': removed}
    plan = masks.load_plan_masks()
    if plan is None:
        plan, record = masks.build_plan_masks(settings, only_owner=owner)
        masks.write_plan_images(plan)
        masks.forget_loaded()
        plan = masks.load_plan_masks()
    look_data = settings_file.look(settings.look_id)
    growth = look_data['growth']
    multiplier = float(density if density is not None else 1.0)
    litter_roots, litter_objects = scatter_litter(settings, ground, plan, growth['litter_amount'], multiplier, seed=settings.seed * 7 + 1)
    all_litter = np.vstack(list(litter_roots.values())) if litter_roots else np.zeros((0, 3))
    plant_roots, plant_objects = scatter_plants(settings, ground, plan, max(growth['weeds_amount'], growth['cushions_amount']), all_litter, multiplier, seed=settings.seed * 7 + 2)
    masks.stamp_litter(all_litter)
    seed_module.write_object_values(litter_objects + plant_objects)
    bpy.context.view_layer.update()
    plants = int(sum(len(r) for r in plant_roots.values()))
    litter = int(len(all_litter))
    return {'summary': f'{plants} plant piece(s) and {litter} litter piece(s) in {len(plant_objects) + len(litter_objects)} object(s); none on a wheel track, a worn path, a road crown, a puddle or within 5 cm of litter',
            'plants': plants, 'litter': litter, 'objects': [o.name for o in plant_objects + litter_objects], 'removed': removed}
