# What this does (plain words): a two-minute check for the inventory "which tools fit which surface". Inside Blender (no picture is made) it
# 1. imports the FROZEN copy of the shared layer files (reuse_trials/shared_layers_snapshot/layers) and builds every layer box with its own default
#    settings, to prove the trials can use them from there without any change; it counts the nodes and the sockets of each box;
# 2. builds lib/contrib/stone_tools.polygon_stones inside an empty layout box (the way a gravel or mud LAYOUT would use it) to see if that shared
#    helper works on the layer helper as it is;
# 3. builds the wood build's "Wood Grain Gain" node group (recipes/wood/generator/wood_shaders.py) with the wood S1 description's grain numbers, to see
#    if a new wood layer could borrow it unchanged.
# It writes what it found to build_check.json next to this file. It changes no file outside this folder.
# Use: blender -b --disable-autoexec -t 2 --python reuse_trials/inventory_checks/build_check.py
import json
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
SNAPSHOT = os.path.join(PROC, 'reuse_trials', 'shared_layers_snapshot', 'layers')
sys.path.insert(0, SNAPSHOT)
sys.path.insert(0, os.path.join(PROC, 'lib', 'contrib'))
sys.path.insert(0, os.path.join(PROC, 'lib'))

import bpy  # noqa: E402

report = {'snapshot_folder': SNAPSHOT, 'layers': {}, 'stone_tools': {}, 'wood_grain_group': {}}
started = time.time()
try:
    import layer_interface as li
    report['layer_interface_finds_proc_work_at'] = li.PROC
    report['layer_interface_proc_is_this_proc'] = os.path.samefile(li.PROC, PROC)
    report['bundle_names'] = li.BUNDLE_NAMES
    import colour_and_fade, damage, moss, outline_and_shadow, combine, layout  # noqa: E401
    for module in (layout, colour_and_fade, damage, moss, outline_and_shadow, combine):
        name = module.__name__
        try:
            tree = module.build_group({})
            inputs = [s.name for s in tree.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT']
            outputs = [s.name for s in tree.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'OUTPUT']
            report['layers'][name] = {'built': True, 'file_imported_from': os.path.dirname(module.__file__), 'nodes': len(tree.nodes),
                                      'inputs': len(inputs), 'outputs': outputs,
                                      'declared_links': [link[0] for link in getattr(module, 'DECLARED_LINKS', [])]}
        except Exception as error:  # noqa: BLE001
            report['layers'][name] = {'built': False, 'error': repr(error), 'trace': traceback.format_exc()[-1200:]}
except Exception as error:  # noqa: BLE001
    report['import_error'] = repr(error)
    report['import_trace'] = traceback.format_exc()[-2000:]

# 2. the shared stone helper inside an empty layout box
try:
    import stone_tools
    tree, b = li.make_plain_group('STONE LAYOUT check', [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, 'tile coordinate')],
                                  [('Colour', 'colour', ''), ('Height', 'float', '')])
    before = len(tree.nodes)
    stones = stone_tools.polygon_stones(b, 9, 3.0)
    b.output('Height', stones['inside_distance'])
    report['stone_tools'] = {'built': True, 'nodes_added': len(tree.nodes) - before, 'outputs_given': sorted(stones.keys())}
except Exception as error:  # noqa: BLE001
    report['stone_tools'] = {'built': False, 'error': repr(error), 'trace': traceback.format_exc()[-1500:]}

# 3. the wood grain group, borrowed unchanged
try:
    sys.path.insert(0, os.path.join(PROC, 'recipes', 'wood', 'generator'))
    import wood_shaders
    with open(os.path.join(PROC, 'recipes', 'wood', 'description', 'S1_layout_paint_grain.json')) as handle:
        grain = json.load(handle)['maps']['grain']
    group = wood_shaders.grain_gain_group(grain)
    report['wood_grain_group'] = {'built': True, 'nodes': len(group.nodes),
                                  'inputs': [s.name for s in group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT'],
                                  'outputs': [s.name for s in group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'OUTPUT']}
except Exception as error:  # noqa: BLE001
    report['wood_grain_group'] = {'built': False, 'error': repr(error), 'trace': traceback.format_exc()[-1500:]}

report['seconds'] = round(time.time() - started, 1)
with open(os.path.join(HERE, 'build_check.json'), 'w') as handle:
    json.dump(report, handle, indent=1)
print('[build check]', json.dumps({k: (v if k != 'layers' else {n: x.get('built') for n, x in v.items()}) for k, v in report.items()
                                    if k not in ('bundle_names',)}, default=str)[:3000])
