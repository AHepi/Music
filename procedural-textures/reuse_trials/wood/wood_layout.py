# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# THE WOOD LAYOUT: the boards, and the eleven layout numbers (the "bundle") every layer reads. It is made of two boxes:
#   1. the SHARED slate LAYOUT (layout.py from the frozen snapshot, UNCHANGED), given wood settings: 5 rows per tile and ONE slate per row, so each
#      "slate" is a whole board that runs right across the tile with one butt joint where the row's random slide puts it; the band between rows is
#      the dark gap between boards (settings 'layout.*' in settings.json);
#   2. the WOOD TURN (new, built here, 4 working nodes): hands the bundle on turned a quarter, so that for every shared layer "down the piece" means
#      ALONG the board (with the grain) and "across the piece" means across the board. The shared layers lay their tall streaks, tall patches and
#      "downward" cracks along their own down direction, so after the turn they all run along the grain with no change to any layer.
#        new local_x           = old local_y            (across the board: 0 at the board's top edge, 1 at its bottom edge)
#        new local_y           = old local_x            (along the board: 0 at its left end, 1 at its right end)
#        new piece_width       = old piece_height       (the board's height, across the grain)
#        new piece_height      = old piece_width / Grain Stretch   (the board's length; see below)
#        new top_edge_distance = old local_x x old piece_width x piece_mask   (distance from the board's left end, 0 off the board)
#        piece_id, row, edge_distance, gap_mask, piece_mask, base_height pass through unchanged.
#      GRAIN STRETCH (setting 'turn.grain_stretch', 1 = off): the layers measure "how far along the board" as local_y x piece_height. Handing them a
#      board length Grain Stretch times SHORTER than it really is makes every pattern they draw on the board's own coordinates (paint patches, specks,
#      the fine grain) that many times longer along the grain, without touching any layer. (Round 1 multiplied instead of dividing: the patterns came
#      out shorter, the opposite of what was wanted; fixed in round 2.) Sizes the layers read along the board are then in "grain units" (true length
#      divided by Grain Stretch); the settings say so where it matters. It does NOT change anything read on the picture coordinate (lichen discs,
#      big patches) or on true distances (edge_distance, top_edge_distance). Used only if it helps; the notes say which value was used.
# A LIMIT: every board has one butt joint per tile (the slate LAYOUT puts one joint in every row). A board that ran across the whole tile with no
# joint would restart its own coordinates at the tile edge, which shows as a seam in every pattern drawn on the board. The reference has no joints.
# Also here (fall-back only, used if the slate LAYOUT with one slate per row had failed): none was needed, so there is no second layout.
# Settings: 'turn.grain_stretch'. Everything else is the shared LAYOUT's own settings.
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'turn'
GROUP_NAME = 'WOOD TURN'
CONTROLS = [
    Control('grain_stretch', 'Grain Stretch', 1.0, 0.25, 8.0, 'how many times shorter than it really is the board is said to be, so every pattern the layers draw on the board\'s own coordinates comes out this many times longer along the grain (1 = true length)'),
]


def build_turn_group(parameters):
    """The WOOD TURN box: eleven bundle numbers in (as the slate LAYOUT makes them), the same eleven out, turned a quarter."""
    values = li.resolve(LAYER_KEY, CONTROLS, parameters)
    inputs = [(name, 'float', 0.0, None, None, 'from LAYOUT: ' + li.BUNDLE_TEXT[name]) for name in li.BUNDLE_NAMES]
    inputs += [(c.label, c.kind, values[c.key], c.low, c.high, c.text) for c in CONTROLS]
    outputs = [(name, 'float', 'turned: ' + li.BUNDLE_TEXT[name]) for name in li.BUNDLE_NAMES]
    tree, b = li.make_plain_group(GROUP_NAME, inputs, outputs)
    S = b.input
    turned = {
        'local_x': S('local_y'),
        'local_y': S('local_x'),
        'piece_width': S('piece_height'),
        'piece_height': b.div(S('piece_width'), S('Grain Stretch')),
        'top_edge_distance': b.mul(b.mul(S('local_x'), S('piece_width')), S('piece_mask')),
    }
    for name in li.BUNDLE_NAMES:
        b.output(name, turned.get(name, S(name)))
    return tree
