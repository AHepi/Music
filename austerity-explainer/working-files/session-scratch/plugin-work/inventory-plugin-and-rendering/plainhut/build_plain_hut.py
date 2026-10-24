# What this does (scratch test only): builds a deliberately plain hut and ground with the plugin's own model_kit (flat colours, no
# normal maps, no wear), writes a .glb, so the plugin's model_lint can be run on it to see whether it objects.
import sys, os
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-work/inventory-plugin-and-rendering/stubs')
sys.path.insert(0, '/home/user/Music/plugins/explainer-film/kit/paper-film/blender')
sys.dont_write_bytecode = True
import model_kit as mk
mk.reset()
flat = mk.material(None, name='flat-wall', colour=(0.6, 0.5, 0.4))
roof = mk.material(None, name='flat-roof', colour=(0.3, 0.25, 0.2))
ground = mk.material(None, name='flat-ground', colour=(0.35, 0.3, 0.22))
mk.box('ground', (20, 20, 0.2), at=(0, 0, -0.1), material=ground, map_units=False)
mk.box('wall', (4, 3, 2.4), at=(0, 0, 1.2), material=flat, bevel=0.01)
mk.box('roof', (4.4, 3.4, 0.2), at=(0, 0, 2.5), material=roof, bevel=0.01)
mk.finish(sys.argv[sys.argv.index('--') + 1])
