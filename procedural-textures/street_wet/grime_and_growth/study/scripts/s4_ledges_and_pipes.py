# What this does (plain words): STUDY ONLY, saves nothing. (a) finds the ledges (up-facing shelves: sills, steps, thresholds, string courses, eaves) of ONE cottage from the geometry,
# looking at the wall shell, the trim, the windows and the door together, and compares them with the numbers the builder gave the wetness layer by hand;
# (b) finds the rain pipe's vertical run and its hopper and shoe from the pipe mesh; (c) lists the up-facing faces of the other families (lamp post base, colliery building ledges) by height.
# Run: blender -b --disable-autoexec street.blend --python s4_ledges_and_pipes.py -- OUT.json
import json
import sys

import bpy
import numpy as np

out = sys.argv[sys.argv.index('--') + 1]
scene = bpy.context.scene
deps = bpy.context.evaluated_depsgraph_get()
cottage = 'right_row_a_cottage_01'
wall = bpy.data.objects[f'{cottage}_walls']
floor_z, centre_y, front_x = wall.location.z, wall.location.y, wall.location.x      # local frame: z = 0 is the floor, y = 0 the middle of the front, x = 0 the wall face (-x faces the street)
res = {'frame': dict(floor_z=round(floor_z, 3), centre_y=centre_y, front_x=front_x)}


def faces_of(obj):
    ev = obj.evaluated_get(deps)
    me = ev.to_mesh()
    m = np.array(obj.matrix_world)
    rows = []
    for p in me.polygons:
        n = np.array(p.normal) @ m[:3, :3].T
        n /= max(np.linalg.norm(n), 1e-9)
        pts = np.array([np.append(np.array(me.vertices[i].co), 1.0) @ m.T for i in p.vertices])[:, :3]
        rows.append((n, pts, float(p.area), me.materials[p.material_index].name if me.materials[p.material_index] else None))
    ev.to_mesh_clear()
    return rows


ledges = []
for name in (f'{cottage}_walls', f'{cottage}_trim', f'{cottage}_window_ground', f'{cottage}_window_upper_0', f'{cottage}_window_upper_1', f'{cottage}_door'):
    for n, pts, area, mat in faces_of(bpy.data.objects[name]):
        if n[2] < 0.9 or area < 0.02:
            continue
        lo, hi, c = pts.min(0), pts.max(0), pts.mean(0)
        x_local = float(c[0] - front_x)            # + = behind the wall face (into the house), - = in front of it (toward the street)
        z_local = float(c[2] - floor_z)
        if not (-0.8 < x_local < 0.6) or not (-0.5 < z_local < 6.6):
            continue
        width_y = float(hi[1] - lo[1])
        if width_y < 0.25:
            continue
        ledges.append(dict(src=name.split(cottage + '_')[1], mat=mat, z=round(z_local, 2), y=round(float(c[1] - centre_y), 2), width=round(width_y, 2), depth=round(float(hi[0] - lo[0]), 2),
                           x_from_face=round(x_local, 2), area=round(area, 3)))
ledges.sort(key=lambda e: (e['z'], e['y']))
res['ledges'] = ledges
res['builder_by_hand'] = dict(ground_sill_z=0.85, upper_sill_z=3.55, eaves_z=6.0, door_y=-1.15, ground_window_y=0.95, upper_window_y=[-1.15, 0.95])

# ---- rain pipe: bin the vertices along y; a vertical pipe is a y bin with a tall z range
pipe = bpy.data.objects[f'{cottage}_rainwater']
ev = pipe.evaluated_get(deps)
me = ev.to_mesh()
co = np.empty(len(me.vertices) * 3)
me.vertices.foreach_get('co', co)
co = co.reshape(-1, 3)
m = np.array(pipe.matrix_world)
w = co @ m[:3, :3].T + m[:3, 3]
ev.to_mesh_clear()
w[:, 2] -= floor_z
w[:, 1] -= centre_y
bins = np.round(w[:, 1] / 0.1).astype(int)
tall = []
for b in np.unique(bins):
    sel = w[bins == b]
    if sel[:, 2].max() - sel[:, 2].min() > 3.0:
        tall.append((round(b * 0.1, 1), round(float(sel[:, 2].min()), 2), round(float(sel[:, 2].max()), 2), round(float(sel[:, 0].mean() - front_x), 2)))
res['rain_pipe_vertical_runs(y, zmin, zmax, x_from_face)'] = tall
res['rain_pipe_total_extent_local'] = dict(y=[round(float(w[:, 1].min()), 2), round(float(w[:, 1].max()), 2)], z=[round(float(w[:, 2].min()), 2), round(float(w[:, 2].max()), 2)], x_from_face=[round(float(w[:, 0].min() - front_x), 2), round(float(w[:, 0].max() - front_x), 2)])
# gutter along the eaves: vertices near z 5.9..6.6 spread over y
eaves = w[(w[:, 2] > 5.8) & (w[:, 2] < 6.7)]
res['eaves_gutter_y_range'] = [round(float(eaves[:, 1].min()), 2), round(float(eaves[:, 1].max()), 2)] if len(eaves) else None
json.dump(res, open(out, 'w'), indent=1)
print('LEDGES', len(ledges), 'tall pipe bins', len(tall))
