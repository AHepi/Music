# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# The plain tables of the growth layer (no Blender needed, so the measuring and picture scripts that run on an ordinary Python can read them): where a set's growth section and a
# look's extra dials are read from, which piece kinds a set's piece sets name, the mask names the scatter reads.
import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SECTION_DIR = os.path.join(HERE, 'growth_sets')
LOOK_DIR = os.path.join(HERE, 'looks_growth')
LAYER_KEY = 'growth'
MASK_NAMES = ('weed_site', 'moss_site', 'keepclear', 'footfall', 'crown', 'rubbish_heap', 'wall_dist', 'seam_dist', 'shade', 'dampness', 'existing_growth', 'above_water')


def growth_section(settings):
    """The set's growth block: settings.growth if the set file has one, else growth/growth_sets/<set id>.json; apply.growth (targets, piece_sets, realise_instances) is merged in."""
    block = copy.deepcopy(settings.get('growth') or {})
    if not block:
        path = os.path.join(SECTION_DIR, f'{settings.id}.json')
        if os.path.exists(path):
            with open(path) as handle:
                block = json.load(handle)
    apply_block = (settings.apply or {}).get('growth') or {}
    targets = block.get('targets') or {}
    if isinstance(targets, list):
        targets = {'roles': targets}
    if apply_block.get('targets'):
        targets = dict(targets, roles=list(apply_block['targets']))
    block['targets'] = targets
    if apply_block.get('piece_sets'):
        block['piece_sets'] = list(apply_block['piece_sets'])
    if apply_block.get('realise_instances'):
        block['realise_instances'] = list(apply_block['realise_instances'])
    return block


def look_extras(look_id):
    path = os.path.join(LOOK_DIR, f'{look_id}.json')
    if look_id and os.path.exists(path):
        with open(path) as handle:
            return {k: v for k, v in json.load(handle).get(LAYER_KEY, {}).items() if not k.startswith('_')}
    return {}


def kinds_of_sets(species, set_names):
    names = []
    for set_name in set_names:
        for kind in species['piece_sets'].get(set_name, []):
            if kind not in names:
                names.append(kind)
    return names


