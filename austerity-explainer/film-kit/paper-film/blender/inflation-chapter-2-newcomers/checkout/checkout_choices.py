# What this does: the Poly Haven choices (all CC0, free) for chapter 2's checkout ("34 Plan - chapter 2
# full redesign - places, shots and order of work.md", part 1 "B. The checkout"), written the same way as
# the pit village's poly_haven_choices.py and chapter 2's chapter_2_choices.py, so the same scripts read it:
#   python3 -I ../../pit-village/props/download_poly_haven.py DOWNLOAD_FOLDER --choices checkout_choices.py \
#       --textures KIT/assets/models/inflation-chapter-2-newcomers/checkout/textures
#   blender -b --python ../../pit-village/props/convert_poly_haven.py -- --choices checkout_choices.py --scratch SCRATCH
# build_checkout.sh runs both. The checkout's props go to the checkout's own library,
# assets/models/inflation-chapter-2-newcomers/checkout/props, with its own index.json (the Works' library and
# the pit village's stay as they are).
#
# Every name was checked against Poly Haven's full lists (saved on 15 October 2026 in the scratch folder's
# redesign/polyhaven/models.tsv and textures.tsv) and again live by download_poly_haven.py. plastic_crate_02,
# not _01, which carries a brand print (plan 34, finding F11).

import os

# where these props go: the checkout's own library (a folder)
LIBRARY = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..',
                                       'assets', 'models', 'inflation-chapter-2-newcomers', 'checkout', 'props'))

TRIANGLE_LIMIT = 30000

CHOICES = [
    # (Poly Haven id, file name in the film, what it is, texture size)
    ('food_kiwi_01', 'kiwifruit', 'a kiwifruit, brown and fuzzy, for the basket', '1k'),
    ('food_apple_01', 'apple', 'a red apple, for the basket', '1k'),
    ('bananas', 'bananas', 'Poly Haven\'s bananas: bunches and single bananas side by side (the assembly takes one bunch to hang over '
                           'the basket\'s rim)', '1k'),
    ('lemon', 'lemon-fruit', 'a lemon, for the basket (its part is called lemon, so the prop is lemon-fruit)', '1k'),
    ('food_avocado_01', 'avocado', 'a dark ripe avocado, for the basket', '1k'),
    ('steel_frame_shelves_01', 'steel-frame-shelves', 'tall steel-framed shelves with wooden boards: the ends of the two aisles beyond the '
                                                      'checkout', '1k'),
    ('mounted_fluorescent_lights', 'mounted-fluorescent-lights', 'two fluorescent tube fittings on a ceiling mount: the shop\'s ceiling rows', '1k'),
    ('cardboard_box_01', 'cardboard-box', 'a worn plain cardboard box: stock on the aisle ends\' bottom shelves', '1k'),
    ('plastic_crate_02', 'plastic-crate', 'a stackable grey plastic crate with no print: empty crates stacked by the bag rack', '1k'),
]

# Poly Haven surfaces the scripted props wear (assemble_checkout.py, checkout_props.py), at 1k, in DOWNLOADS/surfaces
SURFACES = [
    'ash_veneer',              # the counter's wooden top edge and the bag rack's rail
    'metal_plate',             # brushed steel: the belt's side rails, the stands, the basket's handles
    'asphalt_02',              # the car park outside the window and the road
]

# surfaces the room wears, kept as the street's are (NAME_colour.jpg, NAME_normal.jpg) in
# assets/models/inflation-chapter-2-newcomers/checkout/textures: {Poly Haven id: colour picture size}
SET_SURFACES = {
    'large_floor_tiles_02': '2k',   # the shop's floor
    'painted_plaster_wall': '1k',   # the walls
    'ceiling_interior': '1k',       # the ceiling's tiles
}
