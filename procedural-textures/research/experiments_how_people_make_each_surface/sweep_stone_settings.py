# What this does: "what does this setting do" strips for the polygon stone maker, using the gravel recipe: (1) the number of faces per stone (3, 4, 5, 6, 8), (2) how many cells hold a stone
# (presence scale 0.4, 0.7, 1.0, 1.4). Writes strips into pictures/. Run: blender -b --disable-autoexec -t 2 --python sweep_stone_settings.py
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'lib')))
sys.path.insert(0, os.path.join(HERE, 'recipes'))
import sweep_tools as st
import recipe_gravel as rg
OUT = os.path.join(HERE, 'out', 'stone_sweeps')
st.render_sweep(lambda v: rg.build_node_group({'sides': v}), [3, 4, 5, 6, 8], os.path.join(OUT, 'sides'), 'Colour', 256, [f'{v} faces per stone' for v in (3, 4, 5, 6, 8)])
st.render_sweep(lambda v: rg.build_node_group({'presence_scale': v}), [0.4, 0.7, 1.0, 1.4], os.path.join(OUT, 'presence'), 'Colour', 256, [f'stone presence x {v}' for v in (0.4, 0.7, 1.0, 1.4)])
