# plain note: my own re-measure of two of the builder's numbers; reads pictures only, prints to screen, writes nothing in other folders
import sys, json
sys.dont_write_bytecode = True
sys.path.insert(0, 'proc-work/recipes/slate_layers/look_fixes')
import measure_look as ml
M = 'proc-work/mask_test/compare/'
out = {}
for name in ['reference', '1_node_made', '2_moss_stamps', '3_chip_stamps']:
    folder = name if name == 'reference' else M + name
    m = ml.measure(folder)
    out[name] = {k: round(float(v), 3) for k, v in m.items() if isinstance(v, (int, float))}
    print(name, {k: out[name][k] for k in ('gradient', 'stripiness', 'olive_percent', 'tan_percent') if k in out[name]})
json.dump(out, open('proc-work/mask_test/check/remeasure.json', 'w'), indent=1)
