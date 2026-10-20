# What this does (plain words): the Blender half of the round-2 independence re-test for the two layers whose files changed in round 2 (MOSS and OUTLINE AND SHADOW).
# In ONE Blender run it bakes, at 384 dots, the finished tile and the masks of every layer for: the tile as it is (settings.json), then each changed layer
# switched off (Amount 0) and each with a new seed (Seed + 1). The pictures go to the folder given. independence_two_layers_analysis.py then counts what changed.
# This uses the same helpers (tests/bake_tools.py) and the same views as the earlier full test (tests/independence_full.py); only the list of variants is shorter
# and everything is baked in one Blender process instead of one process per variant.
# Use: blender -b --disable-autoexec -t 2 --python independence_two_layers_bake.py -- OUT_FOLDER [SIZE]
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.abspath(os.path.join(HERE, '..', 'tests'))
sys.path.insert(0, TESTS)
import bake_tools as bt  # noqa: E402

RECIPE = os.path.abspath(os.path.join(HERE, '..', 'recipe', 'slate_recipe.py'))
MASK_VIEWS = {'m_colour_and_fade': {'debug_view': 'colour_and_fade.mask'}, 'm_damage': {'debug_view': 'damage.mask'},
              'm_moss': {'debug_view': 'moss.mask'}, 'm_outline_and_shadow': {'debug_view': 'outline_and_shadow.mask'},
              'm_piece_id': {'debug_view': 'bundle.piece_id'}, 'm_piece_mask': {'debug_view': 'bundle.piece_mask'}}
VARIANTS = {'base': {}, 'moss_Amount_0': {'moss.amount': 0.0}, 'moss_Seed_plus_1': {'moss.seed': 32.0},
            'outline_and_shadow_Amount_0': {'outline_and_shadow.amount': 0.0}, 'outline_and_shadow_Seed_plus_1': {'outline_and_shadow.seed': 42.0}}

arguments = sys.argv[sys.argv.index('--') + 1:]
out = arguments[0]
size = int(arguments[1]) if len(arguments) > 1 else 384
for name, params in VARIANTS.items():
    bt.bake_views(RECIPE, {'view': params}, os.path.join(out, name + '_final'), size, 4, {}, ('Colour', 'Height', 'Roughness'))
    bt.bake_views(RECIPE, dict(MASK_VIEWS, **{}), os.path.join(out, name + '_masks'), size, 4, params, ('Height',))
    print('[independence]', name, 'done', flush=True)
