"""What this does: counts, for the audit, how many of the small scattered pieces (weeds, tufts, ferns, leaves, litter, stones) stand where nothing may
stand: inside a keep-out (worn track or kept-clear ground), on the crown of a road, on a wheel track, in a puddle, or within 5 cm of litter.
All of these must be 0. It also says how many pieces of each group stand in each SITE (wall foot, verge, fence line, joint, damp corner, background:
growth/sites.py), measured again from the roots and the plan masks, so the audit can show whether weeds grow by place or are spread evenly. The pieces are objects marked pk_scatter; each remembers its roots (one point per piece) in a small text block, so the
count is made again from the roots and the plan masks, never taken from what the scatter said it did.
It needs Blender (bpy) and numpy. A concrete example: scatter_facts(settings) returns {'groups': [{'name': 'tuft', 'group': 'plant', 'count': 80,
'in_keepout': 0, 'in_puddle': 0, 'on_crown': 0, 'on_wheel_track': 0, 'within_5cm_of_litter': 0}]}.
"""
import base64

import numpy as np

import bpy

from .. import house_numbers, names


def encode_roots(points):
    """Roots (n, 3) as text for a text block."""
    return base64.b64encode(np.asarray(points, dtype=np.float32).tobytes()).decode('ascii')


def decode_roots(text):
    data = np.frombuffer(base64.b64decode(text.encode('ascii')), dtype=np.float32)
    return data.reshape(-1, 3)


def roots_of(obj):
    """The roots remembered for a scatter object, (n, 3), or an empty array."""
    block = bpy.data.texts.get(f'pk_roots_{obj.name}')
    if block is None:
        return np.zeros((0, 3), dtype=np.float32)
    return decode_roots(block.as_string())


def store_roots(obj, points):
    name = f'pk_roots_{obj.name}'
    block = bpy.data.texts.get(name) or bpy.data.texts.new(name)
    block.clear()
    block.write(encode_roots(points))
    block['pk_made'] = 1
    return block


def scatter_objects():
    return [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.get(names.SCATTER)]


def puddle_facts():
    """The standing water the kit laid (growth/puddles.py): how many puddles and how much area, and the place's state."""
    found = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.get('pk_puddle')]
    return {'objects': [o.name for o in found], 'puddles': int(sum(int(o.get('pk_puddle_count', 0)) for o in found)),
            'area_m2': round(float(sum(float(o.get('pk_puddle_area', 0.0)) for o in found)), 3)}


def site_facts(plan, groups, cameras):
    """Per group (plant, litter, stone): how many pieces stand in each site (wall foot, verge, fence line, joint, damp corner, background), their shares, and the sites'
    lengths and areas on the ground a view camera sees, measured again from the plan masks with the same functions the growth step used (growth/sites.py)."""
    from .. import settings_file
    from . import sites
    table = settings_file.species_table()['sites']
    gates = {'footfall': house_numbers.value('place_wear.exact_zero_gate_footfall'), 'crown': house_numbers.value('place_wear.exact_zero_gate_crown'),
             'keepclear': house_numbers.value('place_wear.exact_zero_gate_keepclear')}
    allowed = sites.gate_grid(plan.grids, gates)
    site_grid = sites.site_grids(plan.grids, plan.cell, table)
    weight = sites.seen_weight(plan.shape, plan.x0, plan.y0, plan.cell, cameras, house_numbers.value('place_wear.scatter_full_metres'), house_numbers.value('place_wear.scatter_reach_metres'))
    unpaved = sites.grid(plan.grids, 'unpaved') >= 0.5 if 'unpaved' in plan.grids else np.ones(plan.shape, dtype=bool)
    result = {}
    for group in sites.GROUPS:
        roots = [np.vstack(g['roots']) for g in groups.values() if g['group'] == group and g['roots'] and any(len(r) for r in g['roots'])]
        roots = np.vstack(roots) if roots else np.zeros((0, 3))
        names_list = sites.classify_points(roots, plan.grids, plan.x0, plan.y0, plan.cell, table) if len(roots) else []
        measures = sites.site_measures(site_grid, allowed & unpaved if group == 'stone' else allowed, weight, plan.cell, table)
        counts = {site: sum(1 for n in names_list if n == site) for site in sites.SITE_ORDER}
        result[group] = {'count': int(len(roots)), 'by_site': counts, 'shares': {k: round(v, 4) for k, v in sites.shares(names_list).items()},
                         'in_sites_share': round(1.0 - sites.shares(names_list)['background'], 4) if names_list else 0.0, 'measures': measures,
                         'seen_area_m2': round(sum(m['seen_area_m2'] for m in measures.values()), 2)}
    return result


def scatter_facts(settings):
    """The scatter section of the audit (see the note at the top)."""
    from ..wear import masks
    groups = {}
    for obj in scatter_objects():
        key = obj.get('pk_scatter_kind') or obj.name
        entry = groups.setdefault(key, {'name': key, 'group': obj.get('pk_scatter_group') or 'plant', 'objects': [], 'roots': []})
        entry['objects'].append(obj.name)
        entry['roots'].append(roots_of(obj))
    plan = masks.load_plan_masks()
    litter_roots = np.vstack([np.vstack(g['roots']) for g in groups.values() if g['group'] == 'litter' and len(g['roots'])]) if any(g['group'] == 'litter' and g['roots'] for g in groups.values()) else np.zeros((0, 3))
    result = []
    clearance = house_numbers.value('place_wear.litter_clearance_metres')
    gates = {'footfall': house_numbers.value('place_wear.exact_zero_gate_footfall'), 'crown': house_numbers.value('place_wear.exact_zero_gate_crown'),
             'keepclear': house_numbers.value('place_wear.exact_zero_gate_keepclear')}
    for key, entry in groups.items():
        roots = np.vstack(entry['roots']) if entry['roots'] and any(len(r) for r in entry['roots']) else np.zeros((0, 3))
        facts = {'name': key, 'group': entry['group'], 'objects': entry['objects'][:8], 'count': int(len(roots)), 'in_keepout': 0, 'in_puddle': 0, 'on_crown': 0,
                 'on_wheel_track': 0, 'within_5cm_of_litter': 0}
        if len(roots) and plan is not None:
            facts['in_keepout'] = int(np.sum((plan.sample('keepclear', roots) >= gates['keepclear']) | (plan.sample('footfall', roots) >= gates['footfall'])))
            facts['on_crown'] = int(np.sum(plan.sample('crown', roots) >= gates['crown']))
            facts['on_wheel_track'] = int(np.sum(plan.sample('track', roots) >= 0.5))
            facts['in_puddle'] = int(np.sum(plan.sample('above_water', roots) < 0.5))
        if len(roots) and entry['group'] == 'plant' and len(litter_roots):
            nearest = np.min(np.linalg.norm(roots[:, None, :2] - litter_roots[None, :, :2], axis=2), axis=1) if len(roots) * len(litter_roots) < 4e7 else np.full(len(roots), 9.0)
            facts['within_5cm_of_litter'] = int(np.sum(nearest < clearance))
        result.append(facts)
    by_site = None
    if plan is not None:
        try:
            from . import scatter as scatter_module
            by_site = site_facts(plan, groups, scatter_module.view_cameras())
        except KeyError as problem:              # plan masks from an older kit lack the verge and joint pictures: said, never a crash
            by_site = {'not_measured': f'the plan masks lack {problem} (made by an older kit)'}
    from .. import run_record
    record = run_record.read().get('scatter') or {}
    return {'groups': result, 'sites': by_site, 'record': record}
