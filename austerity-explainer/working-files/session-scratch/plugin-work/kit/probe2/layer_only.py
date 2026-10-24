import bpy, sys, runpy, os
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit'); sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/calculators')
from place_kit import commands
from place_kit.wear import door
args = sys.argv[sys.argv.index('--')+1:]
layer = args[0]; out = args[1]; boost = float(args[2]) if len(args) > 2 else 1.0
s = commands.read_settings(None); commands.tag_roles(s, write=False, fallback=True)
w = door.age_place(s, layers=[layer] if layer != 'all' else None)
if boost != 1.0:
    w.set_master(boost)
sys.argv = [sys.argv[0], '--', out, '800', '520', '24', '4.5', '-5.5', '2.4', '-0.3', '0', '1.1']
runpy.run_path('/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-work/kit/preview.py', run_name='__main__')
