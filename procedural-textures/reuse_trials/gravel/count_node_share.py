# What this does (plain words): turns checks/node_counts.json (the number of nodes in every box of the recipe, counted by checks_run.py part 4)
# into the share of nodes that come from the SHARED layers (unchanged) and the share that are NEW for gravel. One node = one small step Blender
# works out for every dot. The seamless-noise helper box (15 nodes) comes from lib/recipe_tools and is counted as shared. MOSS is not in the
# final stack, so it is not built and not counted. Writes checks/node_share.json. Use: python3 -I count_node_share.py
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
counts = {name: row['nodes'] for name, row in json.load(open(os.path.join(HERE, 'checks', 'node_counts.json'))).items() if not name.startswith('_')}
shared = {name: counts[name] for name in ('COLOUR AND FADE', 'DAMAGE', 'OUTLINE AND SHADOW', 'COMBINE', 'Tileable Noise')}
new = {name: counts[name] for name in ('GRAVEL LAYOUT', 'SOIL', 'FACETS', 'GRAVEL HEIGHT RULE')}
wiring = counts['GRAVEL (top: the recipe wiring)']
total = sum(shared.values()) + sum(new.values()) + wiring
result = {'shared_unchanged': shared, 'shared_total': sum(shared.values()), 'new': new, 'new_total': sum(new.values()), 'recipe_wiring': wiring, 'all': total,
          'shared_share_percent': round(100 * sum(shared.values()) / total, 1),
          'shared_share_percent_if_the_new_height_box_is_dropped_for_combines_own_rule': round(100 * sum(shared.values()) / (total - new['GRAVEL HEIGHT RULE']), 1),
          'shared_share_percent_without_the_layout': round(100 * sum(shared.values()) / (total - new['GRAVEL LAYOUT']), 1)}
with open(os.path.join(HERE, 'checks', 'node_share.json'), 'w') as handle:
    json.dump(result, handle, indent=1)
print(json.dumps(result, indent=1))
