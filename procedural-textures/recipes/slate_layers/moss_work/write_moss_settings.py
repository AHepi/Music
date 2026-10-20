# What this does (plain words): writes moss_settings.json: every setting of the MOSS layer with its default (name -> number or colour code), read from layers/moss.py. This is what
# the layer adds to recipe/settings.json (about 1.5 KB, tens of numbers, no lists of pieces). Check it with: python3 -I lib/description_audit.py moss_settings.json --limit-kilobytes 8
# Use: blender -b --python write_moss_settings.py
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', 'layers')))
import layer_interface as li
import moss
rows = li.controls_table_rows('moss', moss.CONTROLS, with_common=True, default_seed=moss.DEFAULT_SEED)
settings = {r[0]: r[2] for r in rows}
json.dump(settings, open(os.path.join(HERE, 'moss_settings.json'), 'w'), indent=1)
print('wrote moss_settings.json with', len(settings), 'settings')
