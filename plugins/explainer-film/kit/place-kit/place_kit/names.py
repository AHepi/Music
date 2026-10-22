"""What this does: keeps every name the place kit writes into a scene (custom properties, collections, materials, node
groups, images, modifiers) in one place, so no other file spells one by hand and a name can be changed in one line.
Plain Python: no Blender needed to import it.

A concrete example: a plank object that the kit has finished carries the properties place_owner = "huts",
place_role = "timber.plank", pk_seed = 0.4172 and pk_dirt_amount = 0.6, sits in the collection "Place: huts", and
its material is called "PK timber.plank / timber_weathered".
"""

# ---- custom properties on objects
OWNER = 'place_owner'              # which builder owns the object (the part it belongs to)
ROLE = 'place_role'                # what the object is, for example wall.timber_frame
MADE = 'pk_made'                   # 1 on everything the kit itself creates (objects, so undo can remove them)
SEED = 'pk_seed'                   # a number 0..1 per object that picks its own random pattern
SCATTER = 'pk_scatter'             # 1 on small scattered pieces (plants, litter): the construction check leaves them out
TOP_Z = 'pk_top_z'                 # the highest point of the object in world metres (what shelters the ground below)
BOTTOM_Z = 'pk_zmin'               # the lowest point of the object in world metres (the wall foot starts here)
HEIGHT = 'pk_height'               # the object's own height in metres
SEAT_GROUND_Z = 'pk_seat_ground_z' # the ground height under the object when it was seated (so it can be seated again)
SEAT_SINK = 'pk_seat_sink'         # how far into the ground it was sunk when seated
ORIGINAL_MATERIALS = 'pk_original_materials'   # JSON list: the material name in each slot before the kit changed it
SLOT_ROLES = 'pk_slot_roles'       # JSON list: the role of each material slot, when slots differ
LOOK = 'pk_look'                   # the look id given to this object
SHAPE_DAMAGE = 'pk_shape_damage'   # 1 when the shape-damage step has bent or chipped this object


def layer_amount_name(layer):
    """The property that says how strongly a layer acts on this object: pk_dirt_amount."""
    return f'pk_{layer}_amount'


def layer_dial_name(layer, dial):
    return f'pk_{layer}_{dial}'


# ---- the nine wear layers, in their fixed order (a layer earlier in the list goes in front of a later one)
LAYER_ORDER = ('dirt', 'grime', 'weathering', 'wetness', 'cracks_and_chips', 'edge_wear', 'moss_and_algae', 'rust', 'rubbish')

# ---- the sixteen treatments the audit looks for
TREATMENTS = ('normal_map', 'displacement', 'roughness_variation', 'colour_variation', 'bevelled_edges', 'dirt', 'grime',
              'weathering', 'wetness', 'cracks_and_chips', 'edge_wear', 'moss_and_algae', 'rust', 'rubbish', 'plants',
              'litter_pieces')
# one more the kit makes: damage as shape (bent, chipped, no two parts alike); checked like a treatment
SHAPE_TREATMENT = 'shape_damage'
ALL_TREATMENTS = TREATMENTS + (SHAPE_TREATMENT,)
LAYER_TREATMENTS = tuple(t for t in LAYER_ORDER)           # the treatments that a wear layer makes
OBJECT_CHECKS = ('uv', 'carried', 'scale_ok')

LOOKS = ('kept', 'lived_in', 'neglected', 'derelict')
STATES = ('dry', 'damp', 'wet')

# ---- collections, materials, node groups, images, modifiers
PART_COLLECTION_PREFIX = 'Place: '
MADE_COLLECTION = 'PK made'
MATERIAL_PREFIX = 'PK '
NODE_GROUP_PREFIX = 'PK '
PLAN_GROUP = 'PK Plan'
CAMERA_PREFIX = 'Place '            # preview cameras are called "Place <owner> cam <n>" and finish deletes them
BEVEL_MODIFIER = 'PK Bevel'
WEIGHTED_NORMAL_MODIFIER = 'PK Weighted Normal'
DAMAGE_MODIFIER = 'PK Damage'
DAMAGE_SUBDIVIDE_MODIFIER = 'PK Damage Cuts'
DISPLACE_SUBDIVIDE_MODIFIER = 'PK Displace Cuts'


def part_collection_name(owner):
    return f'{PART_COLLECTION_PREFIX}{owner}'


def material_name(role, surface):
    return f'{MATERIAL_PREFIX}{role} / {surface}'


def layer_group_name(layer):
    """'cracks_and_chips' -> 'PK Cracks And Chips'; 'dirt' -> 'PK Dirt'."""
    return NODE_GROUP_PREFIX + ' '.join(word.capitalize() for word in layer.split('_'))


def normal_image_name(surface):
    return f'pk_{surface}_nor'


def height_image_name(surface):
    return f'pk_{surface}_height'


def plan_image_name(mask):
    return f'pk_plan_{mask}'


def is_kit_material(name):
    return name.startswith(MATERIAL_PREFIX)


def is_kit_node_group(name):
    return name.startswith(NODE_GROUP_PREFIX)


def is_kit_image(name):
    return name.startswith('pk_')
