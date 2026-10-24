import bpy, sys
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/place-kit'); sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/calculators')
from place_kit import commands
from place_kit.wear import door
s = commands.read_settings(None); commands.tag_roles(s, write=False, fallback=True)
w = door.age_place(s); w.remove()
