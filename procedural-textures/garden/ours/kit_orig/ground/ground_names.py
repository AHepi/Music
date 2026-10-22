# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# The plain tables of the ground layers (no Blender needed, so the drawing and measuring scripts that run on an ordinary Python can read them): the layers' keys, the elements each
# layer is made of, the fixed numbers of their debug parts, the dials a set may vary by role, and where a set's ground section and a look's extra dials are read from.
import json
import os

GROUND_DIR = os.path.dirname(os.path.abspath(__file__))
SECTION_DIR = os.path.join(GROUND_DIR, 'ground_sets')
LOOK_DIR = os.path.join(GROUND_DIR, 'looks_ground')
LAYER_KEYS = ('dirt', 'groundcracks', 'groundmoss', 'iron')




# ------------------------------------------------------------------------------------------------------------------------------ the set's ground section
def ground_section(settings):
    """The set's `ground` block: settings.ground if the set file has one, else the sidecar ground/ground_sets/<set id>.json, else {}."""
    block = settings.get('ground')
    if block:
        return block
    path = os.path.join(SECTION_DIR, f'{settings.id}.json')
    if os.path.exists(path):
        with open(path) as handle:
            return json.load(handle)
    return {}


def look_extras(look_id):
    """The extra-dial values of a look, from ground/looks_ground/<look id>.json ({layer: {dial: value}}), or {}."""
    path = os.path.join(LOOK_DIR, f'{look_id}.json')
    if look_id and os.path.exists(path):
        with open(path) as handle:
            return {k: v for k, v in json.load(handle).items() if not k.startswith('_')}
    return {}


# What each layer is made of: element -> the role dials that switch it (an element is left OUT of the node group built for a material when every role of the objects that use the
# material has multiplier 0 for all of its dials: the shader then does not carry nodes it can never use, and EEVEE compiles less). A set that says nothing keeps every element.
ELEMENTS = {
    'dirt': {'film': ['film'], 'polish': ['polish'], 'marks': ['water_marks'], 'halo': ['rust_halo'], 'drum': ['drum_ring'], 'tar': ['tar_patches'], 'splash': ['tar_splash'], 'scrub': ['scrub_strip']},
    'groundcracks': {'flag': ['flag_cracks'], 'kerb': ['kerb_chips'], 'sett': ['sett_disturb']},
    'groundmoss': {'joint': ['joint_share'], 'patch': ['patch_moss'], 'algae': ['algae_fan'], 'liver': ['liverwort'], 'band': ['far_band']},
    'iron': {'foot': ['rust_cover'], 'collars': ['collar_rust'], 'shoe': ['shoe_streak'], 'base': ['base_ring'], 'drum': ['drum_rust'], 'heat': ['heat_scale'], 'soot': ['soot_halo']},
}
# the numbers of the parts of each layer (the dial show_part): fixed, so a part has the same number in every variant of the group
PART_NUMBERS = {
    'dirt': {'film': 1, 'polish': 2, 'marks': 3, 'halo': 4, 'drum': 5, 'tar': 6, 'splash': 7, 'scrub': 8},
    'groundcracks': {'flag_fine': 1, 'flag_broken': 2, 'flag_tilt': 3, 'flag_chip': 4, 'kerb_chips': 5, 'kerb_joints': 6, 'kerb_scuffs': 7, 'sett_disturbed': 8, 'sett_joints': 9, 'flag_fine_cells': 10, 'flag_broken_cells': 11, 'sett_joint_all': 12},
    'groundmoss': {'joint_moss': 1, 'patch_moss': 2, 'algae': 3, 'liverwort': 4, 'far_band': 5, 'joint_all': 6},
    'iron': {'foot_rust': 1, 'collars': 2, 'shoe': 3, 'base_ring': 4, 'drum_rust': 5, 'heat_scale': 6, 'soot': 7},
}

# the dials each layer lets the set vary by role (a per-object multiplier, 1 where the set says nothing)
ROLE_DIALS = {
    'dirt': ['film', 'polish', 'water_marks', 'rust_halo', 'drum_ring', 'tar_patches', 'tar_splash', 'scrub_strip'],
    'groundcracks': ['flag_cracks', 'kerb_chips', 'sett_disturb'],
    'groundmoss': ['joint_share', 'patch_moss', 'algae_fan', 'liverwort', 'far_band'],
    'iron': ['rust_cover', 'collar_rust', 'shoe_streak', 'base_ring', 'drum_rust', 'heat_scale', 'soot_halo'],
}
RING_SLOTS = 3


