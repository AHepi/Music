# What this does (plain words): writes verify/full_effective_description.json = EVERY control of every layer with the value the default tile uses
# (the layer file's starting value, overridden by settings.json), so the size audit can be run on the whole description, not only settings.json.
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
LAYERS = os.path.abspath(os.path.join(HERE, '..', '..', 'layers'))
sys.path.insert(0, LAYERS)
import layer_interface as li, layout, colour_and_fade, damage, moss, outline_and_shadow, combine
settings = json.load(open(os.path.join(HERE, '..', '..', 'recipe', 'settings.json')))
full, from_file = {}, 0
for module, seed in ((layout, None), (colour_and_fade, colour_and_fade.DEFAULT_SEED), (damage, damage.DEFAULT_SEED), (moss, moss.DEFAULT_SEED), (outline_and_shadow, outline_and_shadow.DEFAULT_SEED), (combine, None)):
    controls = list(module.CONTROLS) if seed is None else li.common_controls(seed) + list(module.CONTROLS)
    for c in controls:
        key = f'{module.LAYER_KEY}.{c.key}'
        full[key] = settings.get(key, c.default)
        from_file += key not in settings
for k in ('recipe.stack_order', 'recipe.tiles_across'):
    full[k] = settings[k]
json.dump(full, open(os.path.join(HERE, '..', 'full_effective_description.json'), 'w'), indent=1)
colours = sum(1 for v in full.values() if isinstance(v, str) and v.startswith('#'))
print('[verify] entries', len(full), 'from layer files only', from_file, 'colours', colours)
