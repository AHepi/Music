import sys, os, bpy, json, time
sys.path.insert(0, 'proc-work/garden/surfaces')
look = sys.argv[sys.argv.index('--') + 1]
pack = sys.argv[sys.argv.index('--') + 2] == '1'
import stage_surfaces as ss
rep = ss.apply({'look': look, 'weathering': look == 'real', 'pack_images': pack, 'verbose': False})
out = f'proc-work/garden/surfaces/out/surfaces_test_{look}{"_packed" if pack else ""}.blend'
bpy.ops.wm.save_as_mainfile(filepath=out, compress=True, copy=True)
print('SAVED', out, round(os.path.getsize(out) / 1e6, 1), 'MB; images packed:', sum(1 for i in bpy.data.images if i.packed_file), 'of', len(bpy.data.images))
