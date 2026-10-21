# What this does (plain words): STUDY ONLY, saves nothing. Sorts every material of the courtyard into how it is built (all plain numbers / noise-made colour / vertex colour / the add-on's shader group /
# glow only / leaf with a see-through mix) and counts which plugs of the Principled box are wired. Uses the family table of c6_hook_test.py.
# Run: blender -b --disable-autoexec FILE --python c11_material_kinds.py -- OUT.json
import json, os, sys
from collections import Counter, defaultdict
import bpy
OUT = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'c6_hook_test.py')).read().split('# ---------------------------------------------------------------- the do-nothing group')[0]
sys.argv = [sys.argv[0], '--', 'x']
exec(compile(src, 'c6_family_part', 'exec'))
PL = ['Base Color', 'Roughness', 'Metallic', 'Specular IOR Level', 'Coat Weight', 'Normal']
rows = []
for m in bpy.data.materials:
    if m.users == 0 or not m.use_nodes: continue
    t = m.node_tree
    types = Counter(n.bl_idname.replace('ShaderNode', '') for n in t.nodes)
    outs = [n for n in t.nodes if n.bl_idname == 'ShaderNodeOutputMaterial']
    prin = [n for n in t.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled']
    groups = [n.node_tree.name for n in t.nodes if n.bl_idname == 'ShaderNodeGroup' and n.node_tree]
    if groups and not prin: kind = 'add-on shader group (no Principled on the surface)'
    elif 'Emission' in types and not prin: kind = 'glow only'
    elif prin:
        p = prin[0]
        wired = [k for k in PL if k in p.inputs and p.inputs[k].is_linked]
        if 'VertexColor' in types or 'Attribute' in types: kind = 'Principled, colour from vertex colour' + (' + see-through mix' if 'MixShader' in types else '')
        elif 'TexNoise' in types or 'TexWave' in types: kind = 'Principled, colour and bump made by noise nodes'
        elif wired: kind = 'Principled, some plugs wired'
        else: kind = 'Principled, every plug a plain number'
    else: kind = 'other'
    p = prin[0] if prin else None
    rows.append({'name': m.name, 'family': mat_fam.get(m.name, 'unused'), 'kind': kind, 'nodes': len(t.nodes), 'wired_plugs': [k for k in PL if p and k in p.inputs and p.inputs[k].is_linked],
                 'props': {k: str(m[k])[:40] for k in m.keys() if k in ('ct_material_role', 'foundry_kind', 'ink_kind')}, 'users': m.users})
by_kind = Counter(r['kind'] for r in rows); by_fam_kind = defaultdict(Counter)
for r in rows: by_fam_kind[r['family']][r['kind']] += 1
json.dump({'n': len(rows), 'by_kind': dict(by_kind), 'by_family_and_kind': {k: dict(v) for k, v in by_fam_kind.items()}, 'rows': rows}, open(OUT, 'w'), indent=1)
print(json.dumps({'n': len(rows), 'by_kind': dict(by_kind)}, indent=1))
