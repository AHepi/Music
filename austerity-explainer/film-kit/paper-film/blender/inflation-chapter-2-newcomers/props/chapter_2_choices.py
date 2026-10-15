# What this does: the Poly Haven choices (all CC0, free) for chapter 2's full redesign ("34 Plan -
# chapter 2 full redesign - places, shots and order of work.md", part 1 and part 3), written the same
# way as the pit village's poly_haven_choices.py, so the same scripts read it:
#   python3 -I ../../pit-village/props/download_poly_haven.py DOWNLOAD_FOLDER --choices chapter_2_choices.py \
#       --textures KIT/assets/models/inflation-chapter-2-newcomers/textures
#   blender -b --python ../../pit-village/props/convert_poly_haven.py -- --choices chapter_2_choices.py --scratch SCRATCH
# Its props go to their own library, assets/models/inflation-chapter-2-newcomers/props, with their own
# index.json (the pit village's library stays as it is).
#
# Every name was checked against Poly Haven's full lists (saved on 15 October 2026 in the scratch
# folder's redesign/polyhaven/models.tsv and textures.tsv) and again live by download_poly_haven.py.
# So far it holds the Works' choices; the other places' (the checkout, the building site, the kitchen,
# Glasgow, the corner shop) are added here as they are built.

# where these props go: a name in prop_library.LIBRARIES (or a folder)
LIBRARY = 'inflation-chapter-2-newcomers'

TRIANGLE_LIMIT = 30000

CHOICES = [
    # (Poly Haven id, file name in the film, what it is, texture size)
    # --- the Works
    ('hand_truck', 'hand-truck', "steel sack truck (hand truck) with chipped paint, a worn toe plate and two rubber-tyred wheels, for No. 2's yard", '1k'),
]

# Poly Haven surfaces the scripted props wear (build_chapter_2_props.py), at 1k, in DOWNLOADS/surfaces
SURFACES = [
    'weathered_planks',        # the timber behind the gate boards' and the bank sign's paint
    'raw_plank_wall',          # the packing crate's sawn deal boards
    'rough_wood',              # battens
    'rusty_painted_metal',     # black iron: straps, the sign's bracket, the padlock
    'rust_coarse_01',          # wrought iron: the chain, the nail
    'rusty_metal_02',          # the steel drums
    'rusty_metal_04',          # brass (tinted): the bank's plate and its screws
    'metal_plate',             # tinplate: the lunch tin, the mug
    'caban',                   # the work jacket's wool cloth
    'poly_wool_herringbone',   # the cap's tweed
]

# surfaces the Works' walls wear, kept as the street's are (NAME_colour.jpg, NAME_normal.jpg) in
# assets/models/inflation-chapter-2-newcomers/textures: {Poly Haven id: colour picture size}
SET_SURFACES = {
    'white_sandstone_bricks': '2k',   # No. 2, the flat-out factory: pale buff-grey brick (toned when used)
    'large_red_bricks': '2k',         # No. 1, the quiet factory's piers
}
