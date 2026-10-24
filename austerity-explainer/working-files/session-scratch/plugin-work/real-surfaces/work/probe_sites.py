# What this does: calls the audit's site facts on a finished proof scene and prints the error in full, to find why the audit said "not measured".
import sys, traceback
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit')
from place_kit.wear import masks
from place_kit.growth import keepout, scatter
plan = masks.load_plan_masks()
groups = {}
for obj in keepout.scatter_objects():
    key = obj.get('pk_scatter_kind')
    entry = groups.setdefault(key, {'name': key, 'group': obj.get('pk_scatter_group'), 'objects': [], 'roots': []})
    entry['roots'].append(keepout.roots_of(obj))
try:
    facts = keepout.site_facts(plan, groups, scatter.view_cameras())
    print('SITES', {g: (v['count'], v['by_site']) for g, v in facts.items()})
except Exception:
    traceback.print_exc()
