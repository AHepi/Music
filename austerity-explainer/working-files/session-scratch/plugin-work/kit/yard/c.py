import bpy, sys, json
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit'); sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/calculators')
from place_kit import commands
from place_kit.checks import construction
s = commands.read_settings(None); commands.tag_roles(s, write=False, fallback=True)
r = construction.check_construction(s)
print('KEYS', list(r.keys()) if isinstance(r, dict) else type(r))
objs = r['objects']; print('TYPE', type(objs), (list(objs)[:3] if isinstance(objs, dict) else objs[:1]))
for o in ([dict(v, name=k) for k, v in objs.items()] if isinstance(objs, dict) else objs):
    if isinstance(o, dict) and o.get('name') in ('Fence rail 1 low', 'Fence post 1', 'Fence rail 4 high'):
        print('OBJ', json.dumps(o)[:900])
