# What this does (plain words): reads the node counts that verify_run.py wrote for each surface (verify/work/SURFACE/node_count.json) and adds
# them up the way the trials did: a "box" is one node group, counted once (a helper used by several boxes is counted once); boxes that are
# the project's shared snapshot layers (COLOUR AND FADE, DAMAGE, MOSS, OUTLINE AND SHADOW, COMBINE, the shared LAYOUT, the seamless-noise
# helper) are 'shared'; every other box is 'new'. It also lists where each shared file was really imported from (all must lie in
# reuse_trials/shared_layers_snapshot/layers) and which boxes are switched off in the final settings, so the share of boxes that really work
# can be shown too. Use: python3 -I count_analyse.py
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT_MARK = os.path.join('reuse_trials', 'shared_layers_snapshot', 'layers')
SHARED = {'COLOUR AND FADE', 'DAMAGE', 'MOSS', 'OUTLINE AND SHADOW', 'COMBINE', 'LAYOUT', 'Tileable Noise'}
SHARED_MODULE_NAMES = {'layer_interface', 'layout', 'colour_and_fade', 'damage', 'moss', 'outline_and_shadow', 'combine'}
# layers that are in the built recipe but switched off (amount 0) or not in the stack in the final settings, from each trial's own settings.json
SWITCHED_OFF = {'brick': ['MOSS'], 'wood': [], 'metal': [], 'mud': ['DAMAGE', 'OUTLINE AND SHADOW'], 'gravel': []}
BORROWED = {'wood': ['Wood Grain Gain'], 'brick': [], 'metal': [], 'mud': [], 'gravel': []}
out = {}
for surface in ('brick', 'wood', 'metal', 'mud', 'gravel'):
    path = os.path.join(HERE, 'work', surface, 'node_count.json')
    if not os.path.exists(path):
        continue
    data = json.load(open(path))
    boxes = data['boxes']
    shared = {k: v['nodes_directly_inside'] for k, v in boxes.items() if k in SHARED}
    top = boxes['TOP (recipe wiring)']['nodes_directly_inside']
    new = {k: v['nodes_directly_inside'] for k, v in boxes.items() if k not in SHARED and not k.startswith('TOP')}
    borrowed = {k: new.pop(k) for k in list(new) if k in BORROWED[surface]}
    total = sum(shared.values()) + sum(new.values()) + sum(borrowed.values()) + top
    off_nodes = sum(shared.get(k, 0) for k in SWITCHED_OFF[surface])
    wrong_origin = {name: file for name, file in data['imported_files'].items()
                    if name in SHARED_MODULE_NAMES and SNAPSHOT_MARK not in file}
    row = {
        'shared_unchanged_nodes': sum(shared.values()), 'shared_boxes': shared,
        'new_nodes': sum(new.values()), 'new_boxes': new,
        'borrowed_unchanged_nodes': sum(borrowed.values()), 'borrowed_boxes': borrowed,
        'recipe_wiring_nodes': top, 'total_nodes': total,
        'shared_share_percent_of_all': round(100.0 * sum(shared.values()) / total, 1),
        'switched_off_shared_layers': SWITCHED_OFF[surface], 'switched_off_nodes': off_nodes,
        'shared_share_percent_counting_only_working_boxes': round(100.0 * (sum(shared.values()) - off_nodes) / (total - off_nodes), 1),
        'shared_modules_NOT_imported_from_snapshot': wrong_origin,
        'shared_modules_imported_from': {n: f.split('proc-work/')[-1] for n, f in data['imported_files'].items() if n in SHARED_MODULE_NAMES},
    }
    out[surface] = row
    print(f"== {surface}: total {total}, shared {row['shared_unchanged_nodes']} ({row['shared_share_percent_of_all']}%), new {row['new_nodes']} {new}, "
          f"borrowed {row['borrowed_unchanged_nodes']}, wiring {top}; working-only share {row['shared_share_percent_counting_only_working_boxes']}%; "
          f"shared files from elsewhere than the snapshot: {wrong_origin or 'none'}")
with open(os.path.join(HERE, 'node_count_results.json'), 'w') as handle:
    json.dump(out, handle, indent=1)
