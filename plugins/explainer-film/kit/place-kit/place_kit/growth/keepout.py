"""What this does: counts, for the audit, how many of the small scattered pieces (weeds, tufts, ferns, leaves, litter) stand where nothing may
stand: inside a keep-out (worn track or kept-clear ground), on the crown of a road, on a wheel track, in a puddle, or within 5 cm of litter.
All of these must be 0. The pieces are objects marked pk_scatter; each remembers its roots (one point per piece) in a small text block, so the
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
    return {'groups': result}
