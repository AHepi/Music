"""What this does: the GROWTH step: stands small 3D plants, litter and stones on the ground: tufts, clover, nettles, ferns, brambles, moss cushions (plants), leaves, pine needles,
sticks, straw and clods (litter), pebbles and cobbles (stones, on unpaved ground only, seated into the surface and sized by the facts table). They grow BY SITE, the way
they do in a real place (sites.py): at the foot of walls, along road edges, between ruts and along the line where two ground surfaces meet, along fences and building lines,
in the joints between stones or boards, in damp shady corners, and only thinly anywhere else. Every site holds its own count (per metre of its length, or per 100 square
metres), from the "sites" block of data/species.json times the look's growth amount, and the step lays EXACTLY that many in it: no random top-up across open ground. Inside a
site each species takes a share by how much it likes that site (its "likes" in data/species.json, "seam" included). Only ground a view camera can see gets pieces (full near a
camera, none past place_wear.scatter_reach_metres), and the whole step stays inside a triangle budget of its own (place_audit.scatter_triangles_max): when the counts would
pass it, every count is scaled down by the same share and the step says so, so the kit never makes a scene its own audit fails.
EXACT-ZERO gates: nothing on a wheel track, a worn path (footfall 0.6 or more), the crown of a road (0.7 or more), kept-clear ground (0.5 or more), in a puddle, inside a wall or
prop, and plants never within 5 cm of a litter piece or a stone. The pieces are real geometry (pieces.py), joined into a few meshes (one per kind), each marked pk_scatter so the
construction check leaves it out, and each remembering its roots so the audit counts the keep-out cases and the share of each site again from the roots and the plan masks.
Plants and leaves let a little light through (a thin leaf lit from behind is never black); stones get a rough, bumped surface. Running it twice removes what the first run made
and makes the same again (a fixed seed). It needs Blender (bpy) and numpy.
A concrete example: grow_things(settings) on a 14 m yard with one wall and one road gives a strip of tufts and nettles at the wall's foot, tufts and clover along the road's edges
and between its ruts, a few pebbles on the road's verges, a thin scatter elsewhere, none on a wheel track, and says how many went into each site.
"""
import math

import numpy as np

import bpy

from .. import house_numbers, names, parts, roles as roles_module, run_record, scene_read, settings_file
from ..wear import masks, seed as seed_module
from . import keepout, pieces, sites

COLLECTION = names.MADE_COLLECTION
MATERIAL = 'PK Scatter'                 # plants and litter: the colour of each piece, and a little light through thin leaves
STONE_MATERIAL = 'PK Scatter stone'     # stones and pebbles: their colour with a rough bumped surface
PIECES_PER_OBJECT = 20000
VARIANTS = {'tuft': 10, 'rosette': 6, 'stalk': 5, 'frond': 5, 'arch': 4, 'cushion': 5, 'flake': 8, 'clump': 4, 'stick': 5, 'straw': 4, 'lump': 4, 'pebble': 8, 'stone': 8}
OVERDRAW = 1.4                          # points drawn per piece wanted (some fall off the ground or too near litter); the extra are dropped, so a site gets exactly its count


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


def scatter_material(group='plant'):
    """The material of a group's pieces. Plants and litter: the colour written on each piece, rough, with a share of Translucent light (a fern frond lit from the other side reads
    green, never black). Stones: their colour, varied by a small noise, rough, with a bump so they do not read as plastic."""
    name = STONE_MATERIAL if group == 'stone' else MATERIAL
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    principled = tree.nodes.new('ShaderNodeBsdfPrincipled')
    attribute = tree.nodes.new('ShaderNodeAttribute')
    attribute.attribute_type = 'GEOMETRY'
    attribute.attribute_name = 'Col'
    if group == 'stone':
        coordinates = tree.nodes.new('ShaderNodeTexCoord')
        noise = tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 40.0
        noise.inputs['Detail'].default_value = 4.0
        tree.links.new(coordinates.outputs['Object'], noise.inputs['Vector'])
        vary = tree.nodes.new('ShaderNodeMix')
        vary.data_type = 'RGBA'
        vary.blend_type = 'MULTIPLY'
        vary.inputs['Factor'].default_value = 0.6
        tree.links.new(attribute.outputs['Color'], vary.inputs['A'])
        tree.links.new(noise.outputs['Color'], vary.inputs['B'])
        tree.links.new(vary.outputs['Result'], principled.inputs['Base Color'])
        principled.inputs['Roughness'].default_value = 0.82
        bump = tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.35
        bump.inputs['Distance'].default_value = 0.004
        tree.links.new(noise.outputs['Fac'], bump.inputs['Height'])
        tree.links.new(bump.outputs['Normal'], principled.inputs['Normal'])
        tree.links.new(principled.outputs['BSDF'], output.inputs['Surface'])
    else:
        tree.links.new(attribute.outputs['Color'], principled.inputs['Base Color'])
        principled.inputs['Roughness'].default_value = 0.75
        translucent = tree.nodes.new('ShaderNodeBsdfTranslucent')
        tree.links.new(attribute.outputs['Color'], translucent.inputs['Color'])
        mix = tree.nodes.new('ShaderNodeMixShader')
        mix.inputs['Fac'].default_value = 0.3
        tree.links.new(principled.outputs['BSDF'], mix.inputs[1])
        tree.links.new(translucent.outputs['BSDF'], mix.inputs[2])
        tree.links.new(mix.outputs['Shader'], output.inputs['Surface'])
    material[names.MADE] = 1
    return material


def made_collection():
    collection = bpy.data.collections.get(COLLECTION)
    if collection is None:
        collection = bpy.data.collections.new(COLLECTION)
    if collection.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(collection)
    return collection


def view_cameras():
    """(x, y) of every camera that draws a view of the place (the kit's own preview and test cameras are left out)."""
    found = []
    for obj in bpy.context.scene.objects:
        if obj.type != 'CAMERA' or obj.name.startswith((names.CAMERA_PREFIX, 'pk_')):
            continue
        found.append((float(obj.matrix_world.translation.x), float(obj.matrix_world.translation.y)))
    return found


def ground_tree(ground_objects):
    """A ray-cast tree of the ground objects' triangles in world space (to find the height under a point) and the highest point of them."""
    from mathutils.bvhtree import BVHTree
    all_vertices, all_triangles, offset, top = [], [], 0, -1e9
    for obj in ground_objects:
        vertices, triangles = parts.world_triangles(obj)
        if len(triangles) == 0:
            continue
        all_vertices.append(vertices)
        all_triangles.append(triangles + offset)
        offset += len(vertices)
        top = max(top, float(vertices[:, 2].max()))
    if not all_vertices:
        return None, 0.0
    vertices = np.vstack(all_vertices)
    triangles = np.vstack(all_triangles)
    return BVHTree.FromPolygons([tuple(v) for v in vertices], [tuple(int(i) for i in t) for t in triangles]), top + 5.0


def drop_to_ground(tree, top, points_xy):
    """The ground height under each (x, y): (points (n, 3), found (n,) booleans)."""
    from mathutils import Vector
    result = np.zeros((len(points_xy), 3))
    found = np.zeros(len(points_xy), dtype=bool)
    down = Vector((0.0, 0.0, -1.0))
    for index, (x, y) in enumerate(points_xy):
        hit = tree.ray_cast(Vector((float(x), float(y), top)), down)
        if hit[0] is not None:
            result[index] = (x, y, hit[0].z)
            found[index] = True
    return result, found


def nearest_distance(points, others):
    """The distance from each point to the nearest of `others` (plan view); 9 where there are none."""
    if len(others) == 0 or len(points) == 0:
        return np.full(len(points), 9.0)
    result = np.full(len(points), 9.0)
    step = max(1, int(2e7 // max(len(others), 1)))
    for start in range(0, len(points), step):
        chunk = points[start:start + step, :2]
        result[start:start + step] = np.sqrt(((chunk[:, None, :] - others[None, :, :2]) ** 2).sum(axis=2)).min(axis=1)
    return result


def size_range_cm(species, facts):
    """(smallest, largest) size in centimetres: the species' own size_cm, or for a stone its fact (size_fact) from the facts table, never under its visible_min_cm."""
    if species.get('size_fact'):
        fact = facts.get(species['size_fact'])
        if fact is not None:
            low = max(float(fact['min']) * 100.0, float(species.get('visible_min_cm', 0.0)))
            return low, max(float(fact['max']) * 100.0, low * 1.5)
    return float(species['size_cm'][0]), float(species['size_cm'][1])


def build_mesh(species, points, rng, variants, colours, size_cm, sink_share=0.0):
    """One joined mesh object's data for all pieces of one kind: vertices, faces and a colour per vertex. sink_share pushes each piece that share of its height into the
    ground (a stone is seated, not laid on top)."""
    low, high = size_cm
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
        height = float(v[:, 2].max()) if len(v) else 0.0
        cos, sin = np.cos(angles[members]), np.sin(angles[members])
        scaled = v[None, :, :] * sizes[members][:, None, None]
        x = scaled[:, :, 0] * cos[:, None] - scaled[:, :, 1] * sin[:, None]
        y = scaled[:, :, 0] * sin[:, None] + scaled[:, :, 1] * cos[:, None]
        z = scaled[:, :, 2] - (sink_share * height * sizes[members])[:, None]
        out = np.stack([x, y, z], axis=2) + points[members][:, None, :]
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


def make_object(kind, group, vertices, face_blocks, colour_array, roots, chunk, site_names):
    mesh = bpy.data.meshes.new(f'PK scatter {kind} {chunk}')
    faces = []
    for block in face_blocks:
        faces.extend(tuple(int(i) for i in row) for row in block)
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    mesh.update()
    attribute = mesh.color_attributes.new('Col', 'FLOAT_COLOR', 'POINT')
    rgba = np.concatenate([np.clip(colour_array, 0, 1), np.ones((len(colour_array), 1))], axis=1).astype(np.float32)
    attribute.data.foreach_set('color', rgba.ravel())
    mesh.materials.append(scatter_material(group))
    obj = bpy.data.objects.new(f'PK scatter {kind} {chunk}', mesh)
    made_collection().objects.link(obj)
    obj[names.SCATTER] = 1
    obj[names.MADE] = 1
    obj[names.ROLE] = 'never.scatter'
    obj['pk_scatter_kind'] = kind
    obj['pk_scatter_group'] = group
    obj['pk_count'] = int(len(roots))
    obj['pk_sites'] = ','.join(f'{site}:{sum(1 for s in site_names if s == site)}' for site in sites.SITE_ORDER)
    keepout.store_roots(obj, roots)
    return obj


def eligible_ground(settings, objects, tagged, table, rules):
    """The ground objects that grow plants and litter (their role requires or wants plants and no off entry stops it)."""
    ground = []
    for obj in objects:
        role = tagged[obj.name]['role'] or ''
        if not role.startswith('ground.'):
            continue
        req = roles_module.requirements(role, table, rules)
        if 'plants' in (set(req['required']) | set(req['wanted'])) and not roles_module.off_entries_for(role, 'plants', rules):
            ground.append(obj)
    return ground


SAFETY = 0.9                            # the counts are planned to 90 percent of the budget: the triangles of a piece vary with its variant


def kit_triangles(objects):
    return int(sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objects if o.type == 'MESH'))


def plan_layout(settings, plan, look_growth, density, cameras, used_triangles=0):
    """Everything the growth step decides before laying a piece, in plain numbers: the site grids, the cells each group may use, the seen weight, the site measures and the
    count of every group in every site (after the budget). Returns a dict (the audit makes the same with the same functions)."""
    table = settings_file.species_table()
    site_table = table['sites']
    gates = {'footfall': house_numbers.value('place_wear.exact_zero_gate_footfall'), 'crown': house_numbers.value('place_wear.exact_zero_gate_crown'),
             'keepclear': house_numbers.value('place_wear.exact_zero_gate_keepclear')}
    allowed = sites.gate_grid(plan.grids, gates)
    site_grid = sites.site_grids(plan.grids, plan.cell, site_table)
    weight = sites.seen_weight(plan.shape, plan.x0, plan.y0, plan.cell, cameras, house_numbers.value('place_wear.scatter_full_metres'), house_numbers.value('place_wear.scatter_reach_metres'))
    unpaved = sites.grid(plan.grids, 'unpaved') >= 0.5 if 'unpaved' in plan.grids else np.ones(plan.shape, dtype=bool)
    allowed_by_group = {'plant': allowed, 'litter': allowed, 'stone': allowed & unpaved}
    measures = {group: sites.site_measures(site_grid, allowed_by_group[group], weight, plan.cell, site_table) for group in sites.GROUPS}
    counts = {group: sites.targets(measures[group], site_table, group, sites.group_scale(group, look_growth), density) for group in sites.GROUPS}
    kinds = {group: {k: v for k, v in table['kinds'].items() if v['group'] == group} for group in sites.GROUPS}
    for group in sites.GROUPS:                      # a site no species of the group likes gets none of it (no stones in the sward between ruts)
        for site in sites.SITE_ORDER:
            if sum(sites.species_weights(kinds[group], site).values()) <= 0:
                counts[group][site] = 0
    triangles_each = {}
    for group in sites.GROUPS:
        for kind, spec in kinds[group].items():
            variants = pieces.make_variants(spec['builder'], min(VARIANTS.get(spec['builder'], 4), 4), seed=7)
            triangles_each[kind] = float(np.mean([pieces.triangle_count(v) for v in variants]))
    planned_triangles = 0.0
    for group in sites.GROUPS:
        for site in sites.SITE_ORDER:
            weights = sites.species_weights(kinds[group], site)
            total = sum(weights.values())
            if total > 0:
                planned_triangles += counts[group][site] * sum(w / total * triangles_each[k] for k, w in weights.items())
    planned_pieces = sum(sum(c.values()) for c in counts.values())
    budget_triangles = max(0.0, float(house_numbers.value('place_audit.scatter_triangles_max')) - float(used_triangles)) * SAFETY       # the puddles come out of the same budget
    budget_pieces = float(house_numbers.value('place_audit.scatter_pieces_max'))
    scale = min(1.0, budget_triangles / planned_triangles if planned_triangles > 0 else 1.0, budget_pieces / planned_pieces if planned_pieces > 0 else 1.0)
    if scale < 1.0:
        counts = {group: {site: int(math.floor(count * scale)) for site, count in by_site.items()} for group, by_site in counts.items()}
    return {'site_grid': site_grid, 'allowed': allowed_by_group, 'weight': weight, 'measures': measures, 'counts': counts, 'kinds': kinds, 'budget_scale': round(scale, 4),
            'planned_triangles': int(planned_triangles), 'triangles_each': triangles_each}


def lay_group(group, layout, plan, tree, top, rng, keep_clear_of, facts, extra_share=None):
    """Lays one group's pieces site by site, exactly the planned count in each (when the site has room). Returns ({kind: roots}, {kind: [site names]}, {site: laid})."""
    kinds = layout['kinds'][group]
    roots_by_kind, sites_by_kind, laid = {}, {}, {}
    clearance = house_numbers.value('place_wear.litter_clearance_metres')
    for site in sites.SITE_ORDER:
        wanted = layout['counts'][group][site]
        laid[site] = 0
        if wanted <= 0:
            continue
        weights = sites.species_weights(kinds, site, extra_share)
        total = sum(weights.values())
        if total <= 0:
            continue
        cells = layout['site_grid'][site] & layout['allowed'][group]
        kept = np.zeros((0, 3))
        for attempt in range(3):
            need = wanted - len(kept)
            if need <= 0:
                break
            xy = sites.pick_cells(rng, cells, layout['weight'], int(math.ceil(need * OVERDRAW)) + 2, plan.cell, plan.x0, plan.y0)
            if len(xy) == 0:
                break
            points, found = drop_to_ground(tree, top, xy)
            points = points[found]
            if group == 'plant' and len(keep_clear_of):
                points = points[nearest_distance(points, keep_clear_of) >= clearance]
            kept = np.vstack([kept, points])[:wanted]
        laid[site] = len(kept)
        if len(kept) == 0:
            continue
        names_list = list(weights)
        chances = np.array([weights[k] / total for k in names_list])
        assigned = rng.choice(len(names_list), len(kept), p=chances)
        for index, kind in enumerate(names_list):
            chosen = kept[assigned == index]
            if len(chosen):
                roots_by_kind[kind] = np.vstack([roots_by_kind[kind], chosen]) if kind in roots_by_kind else chosen
                sites_by_kind.setdefault(kind, []).extend([site] * len(chosen))
    return roots_by_kind, sites_by_kind, laid


def make_group_objects(group, roots_by_kind, sites_by_kind, rng_seed, facts):
    species_table = settings_file.species_table()
    grey = species_table['tuning']['grey_pull']
    made = []
    for index, (kind, chosen) in enumerate(sorted(roots_by_kind.items())):
        species = species_table['kinds'][kind]
        variants = pieces.make_variants(species['builder'], VARIANTS.get(species['builder'], 4), seed=rng_seed + index)
        colours = [to_linear(pieces.pull_toward_grey(hex_rgb(species_table['palette'][c]), grey)) for c in species['colours']]
        rng = np.random.default_rng(rng_seed * 31 + index)
        size_cm = size_range_cm(species, facts)
        site_names = sites_by_kind.get(kind, [])
        for chunk, start in enumerate(range(0, len(chosen), PIECES_PER_OBJECT)):
            part = chosen[start:start + PIECES_PER_OBJECT]
            built = build_mesh(species, part, rng, variants, colours, size_cm, float(species.get('sink_share', 0.0)))
            if built is None:
                continue
            vertices, face_blocks, colour_array = built
            made.append(make_object(kind, group, vertices, face_blocks, colour_array, part, chunk, site_names[start:start + PIECES_PER_OBJECT]))
    return made


def grow_things(settings, owner=None, density=None):
    """The growth pass (see the note at the top). Returns {'summary', 'plants', 'litter', 'stones', 'objects', 'sites', 'budget_scale', ...}."""
    table = settings_file.roles_table()
    rules = settings.rules_dict()
    removed = remove_old()
    objects = [o for o in scene_read.mesh_objects(only_visible=True) if not scene_read.is_scatter(o) and not o.get(PUDDLE_KEY)]
    tagged = roles_module.tag_objects([scene_read.object_facts(o) for o in objects], rules, table)['by_object']
    ground = eligible_ground(settings, objects, tagged, table, rules)
    if not ground:
        return {'summary': 'no outdoor ground to grow things on (nothing to do)', 'plants': 0, 'litter': 0, 'stones': 0, 'objects': [], 'removed': removed}
    plan = masks.load_plan_masks()
    if plan is None:
        plan, record = masks.build_plan_masks(settings, only_owner=owner)
        masks.write_plan_images(plan)
        masks.forget_loaded()
        plan = masks.load_plan_masks()
    look_growth = settings_file.look(settings.look_id)['growth']
    cameras = view_cameras()
    puddle_triangles = kit_triangles([o for o in bpy.data.objects if o.get(PUDDLE_KEY)])
    layout = plan_layout(settings, plan, look_growth, float(density if density is not None else 1.0), cameras, used_triangles=puddle_triangles)
    all_ground = [o for o in objects if (tagged[o.name]['role'] or '').startswith('ground.')]
    tree, top = ground_tree(all_ground)
    if tree is None:
        return {'summary': 'the ground has no faces to stand pieces on (nothing to do)', 'plants': 0, 'litter': 0, 'stones': 0, 'objects': [], 'removed': removed}
    from ..checks import scale as scale_module
    try:
        facts = {f['id']: f for f in scale_module.load_facts(settings.data)}
    except (OSError, ValueError):                       # a place's own facts file that cannot be read: the kit's own facts still size the stones
        facts = {f['id']: f for f in settings_file.facts_table()}
    seed = int(settings.seed)
    litter_roots, litter_sites, litter_laid = lay_group('litter', layout, plan, tree, top, np.random.default_rng(seed * 7 + 1), np.zeros((0, 3)), facts)
    stone_roots, stone_sites, stone_laid = lay_group('stone', layout, plan, tree, top, np.random.default_rng(seed * 7 + 3), np.zeros((0, 3)), facts)
    all_litter = np.vstack(list(litter_roots.values())) if litter_roots else np.zeros((0, 3))
    all_stones = np.vstack(list(stone_roots.values())) if stone_roots else np.zeros((0, 3))
    cushions = float(look_growth.get('cushions_amount', look_growth['weeds_amount'])) / max(float(look_growth['weeds_amount']), 0.05)
    plant_roots, plant_sites, plant_laid = lay_group('plant', layout, plan, tree, top, np.random.default_rng(seed * 7 + 2), np.vstack([all_litter, all_stones]), facts,
                                                     extra_share={'moss_cushion': cushions})
    litter_objects = make_group_objects('litter', litter_roots, litter_sites, seed * 7 + 1, facts)
    stone_objects = make_group_objects('stone', stone_roots, stone_sites, seed * 7 + 3, facts)
    plant_objects = make_group_objects('plant', plant_roots, plant_sites, seed * 7 + 2, facts)
    available = float(house_numbers.value('place_audit.scatter_triangles_max')) - puddle_triangles
    made_triangles = kit_triangles(litter_objects + stone_objects + plant_objects)
    if made_triangles > available:          # the pieces came out heavier than planned: every kind is thinned by the same share, evenly along its roots, and laid again
        keep = available / made_triangles * 0.98
        for obj in litter_objects + stone_objects + plant_objects:
            keepout_text = bpy.data.texts.get(f'pk_roots_{obj.name}')
            if keepout_text is not None:
                bpy.data.texts.remove(keepout_text)
            mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        for roots, site_lists in ((litter_roots, litter_sites), (stone_roots, stone_sites), (plant_roots, plant_sites)):
            for kind in list(roots):
                chosen = np.unique(np.linspace(0, len(roots[kind]) - 1, max(int(len(roots[kind]) * keep), 0)).astype(int)) if len(roots[kind]) else np.zeros(0, dtype=int)
                roots[kind] = roots[kind][chosen]
                site_lists[kind] = [site_lists[kind][i] for i in chosen]
        litter_objects = make_group_objects('litter', litter_roots, litter_sites, seed * 7 + 1, facts)
        stone_objects = make_group_objects('stone', stone_roots, stone_sites, seed * 7 + 3, facts)
        plant_objects = make_group_objects('plant', plant_roots, plant_sites, seed * 7 + 2, facts)
        all_litter = np.vstack(list(litter_roots.values())) if litter_roots else np.zeros((0, 3))
        all_stones = np.vstack(list(stone_roots.values())) if stone_roots else np.zeros((0, 3))
        for laid_group, site_lists in ((litter_laid, litter_sites), (stone_laid, stone_sites), (plant_laid, plant_sites)):
            for site in list(laid_group):
                laid_group[site] = sum(1 for names_list in site_lists.values() for n in names_list if n == site)
        for group, laid_group in (('litter', litter_laid), ('stone', stone_laid), ('plant', plant_laid)):
            for site in laid_group:
                layout['counts'][group][site] = laid_group[site]           # the plan is what was laid: the thinning is written into the budget share below
        layout['budget_scale'] = round(layout['budget_scale'] * keep, 4)
    masks.stamp_litter(all_litter)
    made = litter_objects + stone_objects + plant_objects
    seed_module.write_object_values(made)
    bpy.context.view_layer.update()
    plants = int(sum(len(r) for r in plant_roots.values()))
    litter = int(len(all_litter))
    stones = int(len(all_stones))
    laid = {'plant': plant_laid, 'litter': litter_laid, 'stone': stone_laid}
    site_lines = {group: {site: {'planned': layout['counts'][group][site], 'laid': laid[group].get(site, 0)} for site in sites.SITE_ORDER} for group in sites.GROUPS}
    in_sites = sum(v['laid'] for site, v in site_lines['plant'].items() if site != 'background')
    share = in_sites / plants if plants else 0.0
    triangles = sum(scene_read.triangle_count(o, False, None) for o in made) if made else 0
    record = {'cameras': len(cameras), 'budget_scale': layout['budget_scale'], 'planned_triangles': layout['planned_triangles'], 'triangles': int(triangles),
              'sites': site_lines, 'plants': plants, 'litter': litter, 'stones': stones}
    run_record.write(scatter=record)
    budget_text = '' if layout['budget_scale'] >= 1.0 else (f'; every count scaled to {layout["budget_scale"]:.0%} to stay inside the scatter budget '
                                                           f'({house_numbers.value("place_audit.scatter_triangles_max"):,} triangles)')
    summary = (f'{plants} plant(s), {litter} litter piece(s) and {stones} stone(s) in {len(made)} object(s), {triangles:,} triangles; {share:.0%} of the plants at wall feet, verges, '
               f'fence lines, joints and damp corners (by site: ' + ', '.join(f'{site} {site_lines["plant"][site]["laid"]}' for site in sites.SITE_ORDER) + ')'
               + (f'; only where {len(cameras)} view camera(s) can see' if cameras else '') + budget_text + '; none on a wheel track, a worn path, a road crown or in a puddle')
    return {'summary': summary, 'plants': plants, 'litter': litter, 'stones': stones, 'objects': [o.name for o in made], 'removed': removed, 'sites': site_lines,
            'budget_scale': layout['budget_scale'], 'triangles': int(triangles), 'share_in_sites': round(share, 3)}


PUDDLE_KEY = 'pk_puddle'
