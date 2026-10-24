# Delivery check (Scenario expert skill, bx_audit.deliverable, profile 'render') on the objects the life stage owns, plus the add-on's own audit of each live scatter.
# Run: blender -b --disable-autoexec START.blend -P test_delivery.py -- LOOK OUT.json
import bpy, sys, json, re, os
sys.path.append('/home/user/Music/.claude/skills/scenario-blender-expert/scripts'); sys.dont_write_bytecode = True
import bx_audit
argv = sys.argv[sys.argv.index('--') + 1:]
look, out = argv[0], argv[1]
HERE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/life'
sys.path.insert(0, HERE)
import stage_life
stage_life.apply({'look': look})
bpy.context.view_layer.update()
groups = {
    'maple_mass': ['Maple inner mass'],
    'pine_pads': ['Pine pads'],
    'pond_bed_and_pebbles': ['Life / pond bed', 'Life / pond pebbles'],
    'pond_surface_plants': ['Pond water', 'Lily pads', 'Lotus blossoms', 'Life / lily stems', 'Life / iris clumps'],
    'shrubs': ['Life / shrubs'],
    'fallen_leaves': ['Fallen leaves'],
    'bamboo_stalks': ['Bamboo stalks'],
    'bamboo_fence': ['Bamboo fence'],
}
res = {'look': look, 'groups': {}, 'scatter_audits': {}}
for g, names in groups.items():
    names = [n for n in names if n in bpy.data.objects]
    if not names:
        continue
    try:
        r = bx_audit.deliverable(names, profile='render')
        res['groups'][g] = {'objects': names, 'pass': r['pass'], 'n_errors': len(r['errors']), 'errors': r['errors'][:8], 'n_warnings': len(r['warnings']), 'warnings': r['warnings'][:6], 'skipped': r.get('skipped')}
    except Exception as e:
        res['groups'][g] = {'objects': names, 'exception': repr(e)[:300]}
# the add-on's audit of each live scatter
api = stage_life.load_addon(stage_life.Stage({'look': look}))
for ob in bpy.data.objects:
    if ob.get('astra_kind') == 'native_scatter' and ob.get('garden_owner') == 'life':
        a = api.audit_native_scatter(ob)
        res['scatter_audits'][ob.name] = {'checks': a['checks'], 'controls': a['controls'], 'contract': {k: a['contract'][k] for k in ('candidate_count', 'retained_candidates', 'footprint_rejections', 'kind')}}
json.dump(res, open(out, 'w'), indent=1, default=str)
for g, v in res['groups'].items():
    print('GATE', g, {k: v.get(k) for k in ('pass', 'n_errors', 'n_warnings', 'exception')})
    for e in v.get('errors', [])[:3]: print('   ', e)
for k, v in res['scatter_audits'].items():
    print('SCATTER', k, 'all checks true:', all(v['checks'].values()), [c for c, ok in v['checks'].items() if not ok])
