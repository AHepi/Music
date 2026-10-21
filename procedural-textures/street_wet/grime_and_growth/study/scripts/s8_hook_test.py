# What this does (plain words): STUDY ONLY, saves nothing. Tests whether the way the earlier layers (JOINTS, RUBBISH) hook into a material works on every material of the file:
# the earlier code looks for "the link that feeds the Principled BSDF's Base Color / Roughness / Specular IOR Level / Coat Weight / Normal" and fails if one of the five is not wired.
# It counts, for every material, which of the five are wired, before and after the wetness layer is put on (in memory only), and lists the ones the old code could not hook.
# Run: blender -b --disable-autoexec FILE --python s8_hook_test.py -- OUT.json [with_wetness]
import json, sys
import bpy
args = sys.argv[sys.argv.index('--') + 1:]
out_path = args[0]
with_wetness = len(args) > 1
sys.path.insert(0, 'proc-work/street_wet/tools')
sys.dont_write_bytecode = True
if with_wetness:
    import apply_wetness_to_set as aw
    aw.apply(wetness=0.0, puddles=0.0)
NAMES = ('Base Color', 'Roughness', 'Specular IOR Level', 'Coat Weight', 'Normal')
res = {'with_wetness_applied': with_wetness, 'materials': {}}
fails = []
for mat in bpy.data.materials:
    if mat.users == 0 or not mat.use_nodes or mat.node_tree is None:
        continue
    tree = mat.node_tree
    principled = [n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED']
    out = [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output]
    feeds = out[0].inputs['Surface'].links[0].from_node.bl_idname if out and out[0].inputs['Surface'].links else None
    entry = {'principled': len(principled), 'surface_from': feeds}
    if principled:
        p = principled[0]
        entry['wired'] = {n: bool(p.inputs[n].is_linked) for n in NAMES}
        # the old hook: next(link for link in tree.links if link.to_socket == principled.inputs[name])
        try:
            for n in NAMES:
                next(l for l in tree.links if l.to_socket == p.inputs[n])
            entry['old_hook_works'] = True
        except StopIteration:
            entry['old_hook_works'] = False
        entry['emission'] = float(p.inputs['Emission Strength'].default_value) > 0 or p.inputs['Emission Color'].is_linked and float(p.inputs['Emission Strength'].default_value) > 0
    else:
        entry['old_hook_works'] = False
    res['materials'][mat.name] = entry
res['summary'] = dict(total=len(res['materials']), old_hook_works=sum(1 for v in res['materials'].values() if v['old_hook_works']), no_principled=sum(1 for v in res['materials'].values() if v['principled'] == 0),
                      roughness_wired=sum(1 for v in res['materials'].values() if v.get('wired', {}).get('Roughness')), normal_wired=sum(1 for v in res['materials'].values() if v.get('wired', {}).get('Normal')),
                      specular_wired=sum(1 for v in res['materials'].values() if v.get('wired', {}).get('Specular IOR Level')), coat_wired=sum(1 for v in res['materials'].values() if v.get('wired', {}).get('Coat Weight')))
res['old_hook_cannot'] = sorted(k for k, v in res['materials'].items() if not v['old_hook_works'])
res['old_hook_works_on'] = sorted(k for k, v in res['materials'].items() if v['old_hook_works'])
json.dump(res, open(out_path, 'w'), indent=1)
print('HOOK TEST', json.dumps(res['summary']))
