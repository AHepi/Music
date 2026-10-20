# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# SOIL is the one NEW paint layer of the gravel trial. It paints the orange-brown, crumbly earth that lies BETWEEN the stones. No shared
# layer can do this: MOSS and DAMAGE only paint on a piece (they multiply by piece_mask), COLOUR AND FADE lies under the gap paint, and OUTLINE
# AND SHADOW paints the gap one flat colour. So SOIL stacks last and paints only where the layout says "gap" (gap_mask = 1).
# It makes three things:
#   1. LUMPS    the soil is not one flat colour: flat patches of five soil tones (two darker, two lighter, one pale), about 10 dots across.
#               One slow seamless noise is cut by thresholds: the low part is the darker tones, the high part the lighter tones, the middle
#               is left as the flat base colour that OUTLINE AND SHADOW already painted. A threshold is set from a "cover" share (the way
#               COLOUR AND FADE does it), so 'dark cover 0.2' means roughly 20 percent of the soil.
#   2. CRUMBS   tiny dark grey and pale grey specks, 3 to 5 dots across: grit and the smallest stones. A second, much finer seamless noise.
#   3. SHADOW   the soil is darker right next to a stone. The layout pushes the soil DOWN next to every stone (its base_height dips over
#               a few dots); SOIL reads that dip and paints it as two flat steps of dark brown (near and far), so the shadow is painted, not
#               a blur. This is the "low-spot darkening" the surveyor's plan asked for.
# What it reads: Vector, Tile Count, gap_mask, base_height, its own controls and Seed. It never looks at another layer (no declared links).
# Sockets: exactly the shared layer interface (layer_interface.make_layer_group): Vector, Tile Count, the eleven bundle numbers, Seed, Amount,
# its own controls; outputs Mask, Colour, Height, Roughness. Amount 0 = Mask, Height and Roughness exactly 0 (finish_layer).
# Seamless: every noise is the project's seamless noise read on Vector, with a feature count of (features per tile x Tile Count), so the tile
# repeats exactly and a 2 x 2 area has the same look per dot.
# Sizes are TILE units (1.0 = the whole base tile; at 1254 dots per tile 0.008 = 10 dots).
# Height: pale lumps stand up a little and dark ones sink a little (the finished height is made from the finished colour anyway).
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'soil'
GROUP_NAME = 'SOIL'
DEFAULT_SEED = 51.0

CONTROLS = [
    # ---- lumps
    Control('lump_amount', 'Lump Amount', 1.0, 0.0, 1.0, 'how strongly the flat lump patches cover the base soil colour (0 = flat soil)'),
    Control('lump_size', 'Lump Size', 0.008, 0.002, 0.05, 'width of one soil lump, in tile units (0.008 = 10 dots)'),
    Control('darkest_cover', 'Darkest Cover', 0.05, 0.0, 0.6, 'share of the soil painted the darkest tone'),
    Control('dark_cover', 'Dark Cover', 0.20, 0.0, 0.8, 'share of the soil painted the dark tone (the darkest lies inside it)'),
    Control('light_cover', 'Light Cover', 0.35, 0.0, 0.8, 'share of the soil painted the light tone'),
    Control('lighter_cover', 'Lighter Cover', 0.16, 0.0, 0.8, 'share of the soil painted the lighter tone (inside the light patches)'),
    Control('pale_cover', 'Pale Cover', 0.05, 0.0, 0.5, 'share of the soil painted the pale tan tone (inside the lighter patches)'),
    Control('darkest_colour', 'Darkest Colour', '#281e18', kind='colour', text='the darkest soil (the reference soil palette starts at 40, 30, 24)'),
    Control('dark_colour', 'Dark Colour', '#3f2c21', kind='colour', text='dark soil'),
    Control('light_colour', 'Light Colour', '#60402a', kind='colour', text='light soil'),
    Control('lighter_colour', 'Lighter Colour', '#765136', kind='colour', text='lighter, more orange soil'),
    Control('pale_colour', 'Pale Colour', '#957357', kind='colour', text='the palest tan soil (the reference soil palette ends at 149, 115, 87)'),
    # ---- crumbs
    Control('crumb_amount', 'Crumb Amount', 1.0, 0.0, 1.0, 'how strongly the tiny specks cover the soil (0 = none)'),
    Control('crumb_size', 'Crumb Size', 0.0035, 0.001, 0.02, 'width of one speck, in tile units (0.0035 = 4 dots)'),
    Control('crumb_dark_cover', 'Crumb Dark Cover', 0.12, 0.0, 0.5, 'share of the soil covered by dark grey specks'),
    Control('crumb_pale_cover', 'Crumb Pale Cover', 0.05, 0.0, 0.5, 'share of the soil covered by pale grey specks'),
    Control('crumb_dark_colour', 'Crumb Dark Colour', '#1b1b1d', kind='colour', text='dark grey speck (a tiny black stone)'),
    Control('crumb_pale_colour', 'Crumb Pale Colour', '#6f7574', kind='colour', text='pale grey speck (a tiny pale stone)'),
    # ---- shadow next to the stones
    Control('shadow_soil_height', 'Shadow Soil Height', 0.12, 0.0, 1.0, 'the height the layout gives soil that is far from any stone (the layout\'s Soil Level)'),
    Control('shadow_depth', 'Shadow Depth', 0.06, 0.001, 0.3, 'how far the layout pushes the soil down right next to a stone (the layout\'s Shadow Depth)'),
    Control('shadow_near_share', 'Shadow Near Share', 0.55, 0.0, 1.0, 'how much of the dip counts as "near" (the dark step); the rest of the dip up to Shadow Far Share is the lighter step'),
    Control('shadow_far_share', 'Shadow Far Share', 0.12, 0.0, 1.0, 'how small a dip still counts as shadow (the outer, lighter step starts here)'),
    Control('shadow_near_strength', 'Shadow Near Strength', 0.55, 0.0, 1.0, 'how strongly the shadow colour covers the soil in the near step'),
    Control('shadow_far_strength', 'Shadow Far Strength', 0.28, 0.0, 1.0, 'how strongly the shadow colour covers the soil in the far step'),
    Control('shadow_colour', 'Shadow Colour', '#1d140e', kind='colour', text='the dark brown of the soil shadow'),
    # ---- relief and roughness
    Control('lump_height', 'Lump Height', 0.03, 0.0, 0.3, 'how much pale lumps stand up and dark lumps sink (height scale 0..1)'),
    Control('soil_roughness', 'Soil Roughness', 0.05, -1.0, 1.0, 'roughness change on the soil (minus = smoother)'),
]
DECLARED_LINKS = []          # SOIL reads no other layer

SOFT = 0.012                 # soft width of a threshold in noise units (a thin, about one-dot ramp at the edge of a flat patch)


def share_to_spread(b, share):
    """How many standard deviations above the middle a bell-shaped noise must be cut so that about `share` of the dots lie above the cut
    (Tukey's short formula; the same one COLOUR AND FADE uses)."""
    return b.mul(b.sub(b.power(b.sub(1.0, share), 0.14), b.power(share, 0.14)), 4.91)


def build_group(parameters):
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    tiles, seed, vector = S('Tile Count'), S('Seed'), S('Vector')
    gap_mask, base_height = S('gap_mask'), S('base_height')

    def noise(features_per_tile, detail, roughness, offset):
        """The seamless noise (about 0.5 plus or minus 0.09), read on Vector with its own place in the noise (from this layer's Seed)."""
        return b.tileable_noise(vector, b.mul(tiles, features_per_tile), detail, roughness, b.add(b.mul(seed, 5.3), offset))

    def above(field, share, spread):
        """1 where the noise is in its top `share` (a flat patch with a thin soft edge), 0 elsewhere. spread = the noise's usual spread."""
        line = b.math('MULTIPLY_ADD', share_to_spread(b, share), spread, 0.5)
        return b.smoothstep(field, b.sub(line, SOFT * 0.5), b.add(line, SOFT * 0.5))

    def lay_over(under_colour, under_strength, colour, strength):
        """Paint `colour` with `strength` over what is already painted; returns (colour, strength) - the usual 'over' rule."""
        total = b.sub(1.0, b.mul(b.sub(1.0, under_strength), b.sub(1.0, strength)))
        share = b.div(strength, b.mx(total, 1e-6))
        return b.mix(under_colour, colour, share), total

    # ------------------------------------------------------------------------------------------------ 1. LUMPS
    lump_features = b.div(1.0, b.mx(S('Lump Size'), 1e-4))
    field = noise(lump_features, 2.0, 0.5, 11.0)
    where = b.mul(gap_mask, S('Lump Amount'))
    light = above(field, S('Light Cover'), 0.09)
    lighter = above(field, S('Lighter Cover'), 0.09)
    pale = above(field, S('Pale Cover'), 0.09)
    dark = above(b.sub(1.0, field), S('Dark Cover'), 0.09)
    darkest = above(b.sub(1.0, field), S('Darkest Cover'), 0.09)
    colour, strength = S('Light Colour'), b.mul(light, where)
    colour, strength = lay_over(colour, strength, S('Lighter Colour'), b.mul(lighter, where))
    colour, strength = lay_over(colour, strength, S('Pale Colour'), b.mul(pale, where))
    colour, strength = lay_over(colour, strength, S('Dark Colour'), b.mul(dark, where))
    colour, strength = lay_over(colour, strength, S('Darkest Colour'), b.mul(darkest, where))
    lump_height = b.mul(b.mul(b.sub(b.add(lighter, pale), dark), S('Lump Height')), gap_mask)

    # ------------------------------------------------------------------------------------------------ 2. CRUMBS (tiny specks)
    crumb_features = b.div(1.0, b.mx(S('Crumb Size'), 1e-4))
    crumb_field = noise(crumb_features, 1.0, 0.5, 29.0)
    crumb_where = b.mul(gap_mask, S('Crumb Amount'))
    crumb_dark = above(crumb_field, S('Crumb Dark Cover'), 0.12)
    crumb_pale = above(b.sub(1.0, noise(crumb_features, 1.0, 0.5, 47.0)), S('Crumb Pale Cover'), 0.12)
    colour, strength = lay_over(colour, strength, S('Crumb Pale Colour'), b.mul(crumb_pale, crumb_where))
    colour, strength = lay_over(colour, strength, S('Crumb Dark Colour'), b.mul(crumb_dark, crumb_where))

    # ------------------------------------------------------------------------------------------------ 3. SHADOW (two flat steps from the dip in base_height)
    dip = b.maprange(b.sub(S('Shadow Soil Height'), base_height), 0.0, S('Shadow Depth'), 0.0, 1.0, True)       # 0 far from a stone, 1 right next to one
    near = b.smoothstep(dip, S('Shadow Near Share'), b.add(S('Shadow Near Share'), 0.02))
    far = b.smoothstep(dip, S('Shadow Far Share'), b.add(S('Shadow Far Share'), 0.02))
    colour, strength = lay_over(colour, strength, S('Shadow Colour'), b.mul(b.mul(far, S('Shadow Far Strength')), gap_mask))
    colour, strength = lay_over(colour, strength, S('Shadow Colour'), b.mul(b.mul(near, S('Shadow Near Strength')), gap_mask))

    roughness = b.mul(gap_mask, S('Soil Roughness'))
    b.finish_layer(mask=strength, colour=colour, height=lump_height, roughness=roughness)
    return tree
