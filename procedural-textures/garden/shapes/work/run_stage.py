# usage: blender -b courtyard_final.blend -P run_stage.py -- LOOK STEPS(comma or 'all') OUT_PREFIX [views(comma names)] [save(0/1)]
import sys, os, time, json, importlib
sys.dont_write_bytecode = True
HERE = 'proc-work/garden/shapes'
sys.path.insert(0, HERE); sys.path.insert(0, HERE + '/work')
import bpy
a = sys.argv[sys.argv.index('--') + 1:]
look, steps, prefix = a[0], a[1], a[2]
views = a[3].split(',') if len(a) > 3 and a[3] != '-' else []
save = len(a) > 4 and a[4] == '1'
import stage_shapes, wb
importlib.reload(stage_shapes)
t = time.time()
opts = {'look': look}
if steps != 'all': opts['steps'] = steps.split(',')
rep = stage_shapes.apply(opts)
print('STAGE_SECONDS', round(time.time() - t, 1))
V = {
 'hero': ('cam',), 
 'top': ('top', (-2.5, 1.5, 30), (-2.5, 1.5, 0), -22),
 'topgravel': ('topgravel', (5.0, -2.0, 30), (5.0, -2.0, 0), -10.5),
 'rocks': ('rocks', (-8.5, -0.5, 2.6), (-3.8, 3.5, 0.7), 35),
 'lantern': ('lantern', (-0.55, -0.25, 1.35), (0.95, 1.1, 1.25), 50),
 'lantern2': ('lantern2', (2.4, 0.2, 1.8), (0.95, 1.1, 1.2), 50),
 'bridge': ('bridge', (-3.0, -3.8, 0.9), (-3.0, 0.5, 0.1), 40),
 'bridgeside': ('bridgeside', (-9.0, 0.5, 0.35), (-2.0, 0.5, 0.15), 30),
 'step': ('step', (2.2, 1.6, 0.9), (2.2, 4.4, 0.35), 40),
 'wall': ('wall', (3.0, 3.0, 1.4), (6.0, 10.4, 2.0), 35),
 'gravel': ('gravel', (3.0, -6.2, 1.6), (5.8, -1.0, 0.0), 40),
 'basin': ('basin', (3.0, 2.2, 1.3), (4.4, 4.2, 0.3), 45),
 'stepping': ('stepping', (4.8, -6.4, 1.6), (2.4, 0.0, 0.0), 40),
}
if views:
    vs = []
    for v in views:
        if v == 'hero':
            c = bpy.data.objects['Camera']; f = bpy.data.objects['Focus']
            vs.append(('hero', tuple(c.location), None, c.data.lens))
        else:
            name, loc, tgt, lens = (V[v][0],) + tuple(V[v][1:]) if len(V[v]) == 4 else (None,)*4
            vs.append((name, loc, tgt, lens))
    t = time.time()
    outs = wb.render_views(vs, prefix, res=(800, 533))
    print('WB_SECONDS', round(time.time() - t, 1), outs)
if save:
    bpy.ops.wm.save_as_mainfile(filepath=prefix + '.blend', compress=True, copy=True)
    print('SAVED', prefix + '.blend', os.path.getsize(prefix + '.blend') // 1024, 'KB')
