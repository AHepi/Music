# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# WK IRON: rust and stains on every iron object (posts, downpipes, the fire drum, rails, wheels, steel props, gates). One layer for all of them; the set says per role how much of
# each element (a per-role multiplier of the dial) and which objects are iron. Slot A, which on a material with no water layer is straight before the Principled BSDF.
# The object's own height is read from its custom values wk_zmin and wk_zmax (the foundation writes them), so "the lowest 55 cm" means the same on a post, a pipe or a gate.
#   foot rust     paint chipped back to rust in the lowest rust_height of the object (rust_cover of it), in vertical streaks 1 to 3 cm wide with a ragged top
#   collar rings  a rust ring at every collar_spacing up a pipe (collar_rust of the collars), with a short run below it (rust_run)
#   shoe streak   a dark wet streak at the foot of a downpipe
#   base ring     rust round the base flange of a post
#   drum          rust and old paint over drum_rust of a drum, heat-blued scale (heat_scale), a black soot rim at the top and soot runs below it (soot_halo)
# Rust LOWERS Metallic (metallic_drop) and makes the surface rougher; the paint that is left stays as the photo has it (paint_keep is the share of the photo's own paint kept
# in the rust zone). Rust is a colour accent (orange-brown, lighter than the dark iron round it): dark marks on dark iron would be crushed by the film.
# Reads no bus mask (so it works on any set): only position, the object's height values and its own seed. Amount 0: every factor contains the amount, outputs equal inputs.
import bpy

from . import ground_common as gc
from .ground_common import GroundLayer, chroma

FRESH_RUST = chroma(150, 80, 45)
OLD_RUST = chroma(90, 58, 42)
SCALE_BLUE = chroma(40, 45, 58)
SOOT = chroma(28, 27, 26)


def build(key='iron', kit=None, elements=None):
    L = GroundLayer('iron', 'WK IRON', masks=[], wet_normal=False, elements=elements)
    n, g, d = L.n, L.g, L.d
    px, py, pz = L.pos()[1:]
    colour, rough, spec, metallic = g('Colour'), g('Roughness'), g('Specular IOR Level'), g('Metallic')
    fade = g('Fade Near')
    zmin, zmax = n.attr('wk_zmin'), n.attr('wk_zmax')
    h = n.math('MAXIMUM', n.math('SUBTRACT', pz, zmin), 0.0)                 # height above the object's own foot
    top = n.math('MAXIMUM', n.math('SUBTRACT', zmax, pz), 0.0)               # depth below the object's own top
    base_luma = L.luma(colour)
    seed_obj = n.math('MULTIPLY', n.attr('wk_seed'), 997.0)
    streak_vec = n.combine(px, py, n.math('MULTIPLY', pz, 0.12))             # noise stretched upward: vertical streaks
    streak = L.noise(0.03, detail=2.0, w=51.0, vector=streak_vec, scale_socket=n.math('DIVIDE', 1.0, n.math('MAXIMUM', d('streak_m'), 0.01)))
    blotch = L.noise(0.15, detail=3.0, w=52.0)
    soft = n.mix(fade, 0.55, 1.0)                                              # fine marks give way to the average tone far away
    rust_parts = []

    def thr_of(share):
        return L.thr(share, 1)

    # ---- foot rust
    if L.has('foot'):
        ragged = n.math('ADD', h, n.math('MULTIPLY', n.math('SUBTRACT', streak, 0.5), n.math('MULTIPLY', d('rust_height'), 0.5)))
        zone = n.one_minus(n.smoothstep(ragged, n.math('MULTIPLY', d('rust_height'), 0.45), n.math('MULTIPLY', d('rust_height'), 1.1)))
        share = n.math('MULTIPLY', d('rust_cover'), n.math('SUBTRACT', 1.4, d('paint_keep')))          # the more paint is kept, the less is chipped back
        t_chip = thr_of(share)
        chipped = n.smoothstep(n.math('ADD', streak, n.math('MULTIPLY', n.math('SUBTRACT', blotch, 0.5), 0.5)), t_chip, L.shift(t_chip, 0.06))
        scatter = n.math('MULTIPLY', n.smoothstep(blotch, 0.66, 0.72), n.math('MULTIPLY', d('chip_share'), 0.25))
        foot = n.math('MULTIPLY', n.math('MAXIMUM', n.math('MULTIPLY', zone, chipped), n.math('MULTIPLY', scatter, 0.6)), n.math('MULTIPLY', L.eff('rust_cover'), soft))
        foot = n.clamp01(n.math('MULTIPLY', foot, 2.4))
        rust_parts.append(foot)
        L.add_part(foot, 'foot_rust')

    # ---- collar rings every collar_spacing, with a short rust run below each rusty collar
    if L.has('collars'):
        spacing = n.math('MAXIMUM', d('collar_spacing'), 0.3)
        k = n.math('DIVIDE', n.math('SUBTRACT', h, n.math('MULTIPLY', spacing, 0.15)), spacing)
        nearest = n.math('ROUND', k)
        off = n.math('MULTIPLY', n.math('SUBTRACT', k, nearest), spacing)       # metres above (+) or below (-) the nearest collar
        which = L.white(n.math('ADD', nearest, seed_obj), 5.0)[0]
        rusty = n.math('LESS_THAN', which, d('collar_rust'))
        ring_h = n.math('MAXIMUM', d('collar_m'), 0.01)
        ring = n.math('MULTIPLY', n.one_minus(n.smoothstep(n.math('ABSOLUTE', off), n.math('MULTIPLY', ring_h, 0.5), ring_h)), n.math('GREATER_THAN', nearest, 0.5))
        run = n.math('MULTIPLY', n.math('MULTIPLY', n.smoothstep(n.math('MULTIPLY', off, -1.0), 0.0, 0.02), n.one_minus(n.smoothstep(n.math('MULTIPLY', off, -1.0), n.math('MULTIPLY', d('rust_run'), 0.6), d('rust_run')))), n.smoothstep(streak, 0.4, 0.55))
        collars = n.math('MULTIPLY', n.math('MULTIPLY', n.math('MAXIMUM', ring, n.math('MULTIPLY', run, 0.8)), rusty), n.math('MULTIPLY', L.eff('collar_rust'), soft))
        rust_parts.append(collars)
        L.add_part(collars, 'collars')

    # ---- shoe streak: dark and wet at the foot of a downpipe, in vertical streaks
    shoe = None
    if L.has('shoe'):
        shoe_zone = n.one_minus(n.smoothstep(n.math('ADD', h, n.math('MULTIPLY', n.math('SUBTRACT', streak, 0.5), 0.2)), n.math('MULTIPLY', d('shoe_height'), 0.5), d('shoe_height')))
        shoe = n.math('MULTIPLY', n.math('MULTIPLY', shoe_zone, n.smoothstep(streak, 0.38, 0.5)), n.math('MULTIPLY', L.eff('shoe_streak'), soft))
        L.add_part(shoe, 'shoe')

    # ---- base ring of a post
    if L.has('base'):
        ring_base = n.one_minus(n.smoothstep(n.math('ADD', h, n.math('MULTIPLY', n.math('SUBTRACT', blotch, 0.5), 0.1)), n.math('MULTIPLY', d('base_ring_m'), 0.6), d('base_ring_m')))
        base = n.clamp01(n.math('MULTIPLY', n.math('MULTIPLY', ring_base, n.math('ADD', 0.55, n.math('MULTIPLY', streak, 0.6))), n.math('MULTIPLY', L.eff('base_ring'), soft)))
        rust_parts.append(base)
        L.add_part(base, 'base_ring')

    # ---- the drum: rust and old paint over most of it, heat scale, the soot rim and soot runs below it
    drum = heat = soot = None
    if L.has('drum'):
        t_drum = thr_of(d('drum_rust'))
        drum = n.math('MULTIPLY', n.smoothstep(n.math('ADD', blotch, n.math('MULTIPLY', n.math('SUBTRACT', streak, 0.5), 0.4)), t_drum, L.shift(t_drum, 0.08)), n.math('MULTIPLY', L.eff('drum_rust'), soft))
        drum = n.clamp01(drum)
        rust_parts.append(drum)
        L.add_part(drum, 'drum_rust')
    if L.has('heat'):
        heat = n.math('MULTIPLY', n.smoothstep(L.noise(0.25, detail=2.0, w=53.0), 0.54, 0.64), n.math('MULTIPLY', L.eff('heat_scale'), 2.5))
        if drum is not None:
            heat = n.math('MULTIPLY', heat, n.one_minus(drum))
        heat = n.clamp01(heat)
        L.add_part(heat, 'heat_scale')
    if L.has('soot'):
        rim = n.math('ADD', d('rim_soot_m'), n.math('MULTIPLY', n.math('MULTIPLY', streak, d('rim_soot_m')), 1.5))
        soot_zone = n.one_minus(n.smoothstep(top, n.math('MULTIPLY', rim, 0.5), rim))
        soot = n.clamp01(n.math('MULTIPLY', n.math('MULTIPLY', soot_zone, L.eff('soot_halo')), 2.0))
        L.add_part(soot, 'soot')

    # ---- the colours
    out = {}
    out_colour = colour
    rust_all = None
    for r in rust_parts:
        rust_all = r if rust_all is None else n.math('MAXIMUM', rust_all, r)
    if rust_all is not None:
        fresh = n.smoothstep(n.math('ADD', streak, n.math('MULTIPLY', blotch, 0.4)), 0.62, 0.8)
        rust_luma = n.math('MAXIMUM', n.math('MULTIPLY', base_luma, d('rust_bright')), 0.03)
        rust_tint = n.comb_rgb(n.mix(fresh, OLD_RUST[0], FRESH_RUST[0]), n.mix(fresh, OLD_RUST[1], FRESH_RUST[1]), n.mix(fresh, OLD_RUST[2], FRESH_RUST[2]))
        out_colour = n.mix_colour(n.math('MULTIPLY', rust_all, 0.92), out_colour, L.colour_scale(rust_tint, rust_luma))
    if shoe is not None:
        out_colour = L.colour_scale(out_colour, n.one_minus(n.math('MULTIPLY', shoe, 0.55)))
    if heat is not None:
        out_colour = n.mix_colour(n.math('MULTIPLY', heat, 0.8), out_colour, L.colour_scale(n.comb_rgb(SCALE_BLUE[0], SCALE_BLUE[1], SCALE_BLUE[2]), n.math('MULTIPLY', base_luma, 1.5)))
    if soot is not None:
        out_colour = n.mix_colour(n.math('MULTIPLY', soot, 0.9), out_colour, L.colour_of_luma(SOOT, n.math('MAXIMUM', n.math('MULTIPLY', base_luma, 0.35), 4e-3)))
    grime = n.math('MULTIPLY', n.math('MULTIPLY', d('grime_dark'), L.amount), L.role('rust_cover'))
    out_colour = L.colour_scale(out_colour, n.one_minus(grime))
    out['colour'] = out_colour
    rough_cover = rust_all
    if soot is not None:
        rough_cover = soot if rough_cover is None else n.math('MAXIMUM', rough_cover, soot)
    if rough_cover is not None:
        out['roughness'] = n.mix(n.math('MULTIPLY', rough_cover, 0.8), rough, 0.82)
    if rust_all is not None:
        out['metallic'] = n.math('MULTIPLY', metallic, n.one_minus(n.math('MULTIPLY', rust_all, d('metallic_drop'))))
    return L.finish_parts(**out)
