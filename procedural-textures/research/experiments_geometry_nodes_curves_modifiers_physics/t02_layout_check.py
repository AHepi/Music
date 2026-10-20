# What this does: checks the row layout group's numbers: do pieces in a row add up to exactly 1.0, how many wrap copies are made,
# do Accumulate Field's Leading/Trailing mean what the manual says, does Duplicate Elements keep the original.
# Run: blender -b --disable-autoexec -t 2 --python t02_layout_check.py
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, numpy as np
import gn_tools as gt, layout_tools as lt
gt.new_scene(64)
tree = lt.row_layout_group()
results = {}
for wrap in (True, False):
    obj = lt.debug_object(tree, f'dbg{wrap}', Wrap=wrap, Rows=6, Per_row=4, Seed=3)
    pts = gt.evaluated_vertices(obj)
    attrs = {n: gt.evaluated_attribute(obj, n) for n in ('piece_id', 'piece_w', 'piece_h', 'row', 'is_copy')}
    results[f'wrap={wrap}'] = {'points': len(pts), 'copies': int(attrs['is_copy'].sum()), 'originals': int((~attrs['is_copy'].astype(bool)).sum())}
    if wrap:
        orig = ~attrs['is_copy'].astype(bool)
        w = attrs['piece_w'][orig] + 0.02       # add the gap back
        rows = attrs['row'][orig]
        results['row_width_sums'] = [round(float(w[rows == r].sum()), 6) for r in range(6)]
        results['centre_x_range_originals'] = [float(pts[orig][:, 0].min()), float(pts[orig][:, 0].max())]
        results['copy_positions_x'] = sorted([round(float(x), 3) for x in pts[~orig][:, 0]])
        results['copy_positions_y'] = sorted([round(float(x), 3) for x in pts[~orig][:, 1]])
print(json.dumps(results, indent=1))
