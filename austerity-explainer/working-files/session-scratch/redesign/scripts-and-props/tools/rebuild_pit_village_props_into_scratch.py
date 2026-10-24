# What this does: rebuilds some pit village scripted props with the changed kit, into a scratch library
# (never the pit village's), so they can be compared with the kept ones.
# Run: blender -b --python rebuild_pit_village_props_into_scratch.py -- OUT_FOLDER PIT_VILLAGE_SCRATCH name ...
import sys
sys.path.insert(0, '/home/user/Music/austerity-explainer/film-kit/paper-film/blender/pit-village/props')
import prop_library as library
import build_scripted_props as pit_village
arguments = sys.argv[sys.argv.index('--') + 1:]
library.use_library(arguments[0])
library.use_scratch(arguments[1])
for name in arguments[2:]:
    pit_village.BUILDERS[name]()
