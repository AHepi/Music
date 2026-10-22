# usage: blender -b courtyard.blend -P delivery_after.py -- LOOK OUT.json   (applies the surfaces stage, then the Scenario delivery gate, profile 'render', on the same groups as ours/work/delivery_check.py)
import sys, os
LOOK = sys.argv[sys.argv.index('--')+1]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
sys.path.insert(0, 'proc-work/garden/surfaces')
import stage_surfaces
stage_surfaces.apply({'look': LOOK, 'weathering': LOOK == 'real', 'verbose': False})
sys.argv = [sys.argv[0], '--', sys.argv[sys.argv.index('--')+2]]
import sys, json, re
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-expert/scripts'); sys.dont_write_bytecode = True
import bpy, bx_audit
out = sys.argv[sys.argv.index('--')+1]
names = [o.name for o in bpy.context.scene.objects if o.type == 'MESH']
def pick(*patterns):
    return [n for n in names if any(re.match(p, n) for p in patterns)]
groups = {
 'hall': pick(r'^Hall posts$', r'^Hall beams$', r'^Eave soffit$', r'^Shoji bars$', r'^Hall plaster$', r'^Stone plinth$', r'^Hall roof$', r'^Astra / varied planks(\.00[0-2])?$'),
 'bridge': pick(r'^Astra / varied planks\.00[3-7]$', r'^Bridge pier \d+$'),
 'lantern': pick(r'^Lantern (base|post|gallery|firebox|cap|finial)$', r'^Lantern window glow$'),
 'walls': pick(r'^Back wall, (left|right)( cap)?$', r'^Right wall behind hall( cap)?$'),
 'pond_rocks_and_stones': pick(r'^Rock \d+$', r'^Gravel rock \d+$', r'^Pond edge stone \d+$'),
 'stepping_stones': pick(r'^Stepping stone \d+$', r'^Veranda step'),
 'ground_and_water': pick(r'^Astra / Courtyard receiving ground$', r'^Raked gravel court$', r'^Pond water$', r'^Basin water$', r'^Water basin$'),
 'bamboo': pick(r'^Bamboo (fence|stalks)$'),
}
res = {}
for g, objs in groups.items():
    if not objs:
        res[g] = {'objects': 0}; continue
    try:
        r = bx_audit.deliverable(objs, profile='render')
        res[g] = {'objects': len(objs), 'pass': r['pass'], 'errors': r['errors'][:12], 'n_errors': len(r['errors']), 'warnings': r['warnings'][:12], 'n_warnings': len(r['warnings']), 'tol': r['tol'], 'gap': r['gap']}
    except Exception as e:
        res[g] = {'objects': len(objs), 'exception': repr(e)[:300]}
json.dump(res, open(out, 'w'), indent=1)
for g, v in res.items():
    print('GATE', g, {k: v.get(k) for k in ('objects', 'pass', 'n_errors', 'n_warnings', 'exception')})
