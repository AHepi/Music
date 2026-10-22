# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# WK GROUND DIRT: the broad, soft dirt and the stains of the ground (slot A: before the water layer, so the water wets them the way it wets the stone itself).
#   film        a broad soft film of soot and dust, patches 0.5 to 3 m, not on the crown or the trodden lanes, never more than a third darker, a share of the surface set
#               by film_max_share, weaker where the rubbish layer already works (wall foot, gutter strip, heaps: film_near_walls)
#   polish      worn lanes (footfall) are paler and smoother; the joint hollows are left out
#   marks       dried puddle rings (a pale tide line round a slightly darker dip) in the low places away from the lanes
#   halo        rust stain on the ground round the foot of iron posts and pipes (10 to 25 cm); at a pipe foot it is a dark wet stain instead
#   drum        a rust bleed ring on the ground round standing objects the set names (the fire drum); the ash ring is the rubbish layer's, not repeated here
#   tar         patches over lost setts: scalloped irregular edges (never straight), pale chippings, glossy and black when new, matt and grey when old, flat (the sett relief
#               is taken out), a share of the road never above tar_max_share
#   splash      tar splashes at the kerb foot along one or two stretches
#   scrub       the pale scrubbed strip on the flags in front of a whitened or scrubbed doorstep (the same door random, entry_rand, and the same two shares as the steps layer)
# NOT here (the rubbish layer has them): ash, coal dust, cinders, mud, straw, paper, leaves.
# Reads only the bus masks (footfall keepclear lowness crown wall_dist shade vertical_foot seam_dist entry_rand step_foot rubbish_heap) and the incoming bundle; the picture of
# the photo's own hollows (tx_cavity) is read through GroundLayer.tx. Fine detail (chippings, ring edges) gives way to the average tone with Fade Near, never to clean.
# VARIANTS: build(key, kit, elements) leaves out the elements a material's objects can never use (the set's role multipliers), so each material compiles only what it needs.
# Amount 0: every effect factor contains the amount, so every output equals its input.
import bpy

from . import ground_common as gc
from .ground_common import GroundLayer, bump_normal, chroma, lin

MASKS = ['footfall', 'keepclear', 'lowness', 'crown', 'wall_dist', 'shade', 'vertical_foot', 'seam_dist', 'entry_rand', 'step_foot', 'rubbish_heap']
SOOT_TINT = (0.85, 1.0, 1.1)
RUST_TINT = chroma(160, 110, 80)
DRUM_TINT = chroma(140, 75, 40)
PALE_TINT = chroma(195, 180, 155)
TAR_TINT = chroma(48, 46, 42)


def build(key='dirt', kit=None, elements=None):
    L = GroundLayer('dirt', 'WK GROUND DIRT', masks=MASKS, wet_normal=True, elements=elements)
    n, g, d = L.n, L.g, L.d
    tx = L.tx(kit) if L.has('polish') else None
    px, py, pz = L.pos()[1:]
    colour, rough, normal, wnormal = g('Colour'), g('Roughness'), g('Normal'), g('Wet Normal')
    fade = g('Fade Near')
    free = L.gate_free()
    seam = g('M Seam Dist')

    # ---- 0 dust: a thin even coat on all ground, the same at every distance (the patchy film below gives way to its average far away)
    dust = n.math('MULTIPLY', n.math('MULTIPLY', d('dust'), L.amount), L.role('film'))
    colour = L.colour_mul(colour, n.comb_rgb(n.one_minus(n.math('MULTIPLY', dust, SOOT_TINT[0])), n.one_minus(n.math('MULTIPLY', dust, SOOT_TINT[1])), n.one_minus(n.math('MULTIPLY', dust, SOOT_TINT[2]))))

    # ---- 1 film: noise patches, coverage from the film dial, depth from film_darkness; lowered where the rubbish layer already works (wall foot, gutter strip, heaps)
    if L.has('film'):
        rub = n.math('MAXIMUM', g('M Rubbish Heap'), n.math('MAXIMUM', n.one_minus(n.smoothstep(g('M Wall Dist'), 0.1, 0.6)), n.smoothstep(g('M Lowness'), 0.5, 0.9)))
        near = n.one_minus(n.math('MULTIPLY', rub, n.one_minus(d('film_near_walls'))))
        nf = L.noise(1.6, detail=d('film_octaves'), w=1.0, scale_socket=n.math('DIVIDE', 1.0, n.math('MAXIMUM', d('film_scale'), 0.05)))
        cover = n.math('MINIMUM', n.math('MULTIPLY', d('film'), 0.45), n.math('MULTIPLY', d('film_max_share'), 1.4))      # how much of the noise lies above the line: the film's share
        thr = L.thr(cover, 3)
        patch = n.smoothstep(nf, L.shift(thr, -0.03), L.shift(thr, 0.03))
        quiet = n.math('ADD', 0.75, n.math('MULTIPLY', g('M Shade'), 0.25))
        gain = n.math('MULTIPLY', L.amount, L.role('film'))
        film_full = n.math('MULTIPLY', n.math('MULTIPLY', n.math('MULTIPLY', patch, free), n.math('MULTIPLY', near, quiet)), gain)
        film_mean = n.math('MULTIPLY', n.math('MULTIPLY', free, near), n.math('MULTIPLY', gain, 0.3))
        film_f = n.mix(fade, film_mean, film_full)
        darkening = n.math('MULTIPLY', d('film_darkness'), film_f)
        soot_mul = n.comb_rgb(n.math('SUBTRACT', 1.0, n.math('MULTIPLY', darkening, SOOT_TINT[0])), n.math('SUBTRACT', 1.0, n.math('MULTIPLY', darkening, SOOT_TINT[1])),
                              n.math('SUBTRACT', 1.0, n.math('MULTIPLY', darkening, SOOT_TINT[2])))
        colour = L.colour_mul(colour, soot_mul)
        rough = n.math('ADD', rough, n.math('MULTIPLY', film_f, 0.05))
        L.add_part(n.math('MULTIPLY', n.clamp01(n.math('MULTIPLY', film_f, 2.5)), n.math('GREATER_THAN', film_f, 0.02)), 'film', tonal=True)

    # ---- 2 polish: worn lanes lighter and smoother (tops only: the hollows keep their joint)
    if L.has('polish'):
        tops = n.one_minus(n.smoothstep(tx['cavity'], 0.08, 0.35))
        wobble = n.math('ADD', 0.65, n.math('MULTIPLY', L.noise(0.5, detail=2.0, w=2.0), 0.7))
        pol = n.math('MULTIPLY', n.math('MULTIPLY', L.eff('polish'), n.smoothstep(g('M Footfall'), 0.88, 0.98)), n.math('MULTIPLY', tops, n.math('MINIMUM', wobble, 1.0)))
        lift = n.math('ADD', 1.0, n.math('MULTIPLY', n.math('MULTIPLY', d('polish_lift'), 5.0), pol))
        colour = L.colour_scale(colour, lift)
        cut = n.math('MINIMUM', n.math('MULTIPLY', d('polish_rough'), pol), n.math('MULTIPLY', rough, 0.8))
        rough = n.math('SUBTRACT', rough, cut)
        L.add_part(pol, 'polish', tonal=True)

    # ---- 3 water marks: a pale tide line round a slightly darker dip, in the low places away from the lanes
    if L.has('marks'):
        pool_scale = n.math('MAXIMUM', d('pool_scale_m'), 0.3)
        nw = L.noise(1.3, detail=2.0, w=3.0, scale_socket=n.math('DIVIDE', 1.0, pool_scale))
        q = n.math('ADD', nw, n.math('MULTIPLY', n.math('SUBTRACT', g('M Lowness'), 0.2), 0.3))
        ring_w, ring_fade = L.mark_width(d('ring_m'), d('mark_dots'), g('Dot Across'))
        half = n.math('MULTIPLY', n.math('MULTIPLY', ring_w, 0.5), n.math('DIVIDE', 0.9, pool_scale))
        ring = n.one_minus(n.smoothstep(n.math('ABSOLUTE', n.math('SUBTRACT', q, 0.55)), 0.0, n.math('MAXIMUM', half, 4e-3)))
        dip = n.one_minus(n.smoothstep(q, 0.53, 0.57))
        low_gate = n.math('ADD', 0.35, n.math('MULTIPLY', n.smoothstep(g('M Lowness'), 0.05, 0.5), 0.65))
        wgate = n.math('MULTIPLY', n.math('MULTIPLY', L.eff('water_marks'), free), low_gate)
        ring_f = n.math('MULTIPLY', n.math('MULTIPLY', wgate, ring), n.mix(fade, 0.35, 1.0))
        ring_f = n.math('MULTIPLY', ring_f, n.mix(ring_fade, 0.35, 1.0))
        fill_f = n.math('MULTIPLY', n.math('MULTIPLY', wgate, dip), 0.5)
        colour = L.colour_scale(colour, n.math('MULTIPLY', n.math('ADD', 1.0, n.math('MULTIPLY', ring_f, d('ring_pale'))), n.math('SUBTRACT', 1.0, n.math('MULTIPLY', fill_f, d('dip_dark')))))
        L.add_part(n.math('MAXIMUM', ring_f, fill_f), 'marks', tonal=True)

    # ---- 4 rust halo round the foot of standing iron; a dark wet stain at a pipe foot (its foot touches a wall), rust at a post foot
    if L.has('halo'):
        vf = g('M Vertical Foot')
        edge = n.math('SUBTRACT', 1.08, n.math('MULTIPLY', d('rust_halo_m'), 1.8))
        nr = L.noise(0.08, detail=2.0, w=4.0)
        halo = n.smoothstep(n.math('ADD', vf, n.math('MULTIPLY', n.math('SUBTRACT', nr, 0.5), 0.35)), n.math('SUBTRACT', edge, 0.1), n.math('ADD', edge, 0.1))
        pipe = n.one_minus(n.smoothstep(g('M Wall Dist'), 0.2, 0.4))
        halo_f = n.math('MULTIPLY', n.math('MULTIPLY', L.eff('rust_halo'), halo), n.mix(fade, 0.6, 1.0))
        rust_luma = n.math('MULTIPLY', L.luma(colour), 1.25)
        rust_col = L.colour_of_luma(RUST_TINT, rust_luma)
        colour = n.mix_colour(n.math('MULTIPLY', halo_f, n.one_minus(pipe)), colour, rust_col)
        colour = L.colour_scale(colour, n.math('SUBTRACT', 1.0, n.math('MULTIPLY', n.math('MULTIPLY', halo_f, pipe), 0.4)))
        L.add_part(halo_f, 'halo')

    # ---- 5 drum ring: a rust bleed ring just outside the footprint of the standing objects the set names (per-object values wk_dirt_ring0..2_x/_y/_r)
    if L.has('drum'):
        ring_width, ring_width_fade = L.mark_width(d('drum_ring_m'), d('mark_dots'), g('Dot Across'))
        drum = None
        nd = L.noise(0.15, detail=2.0, w=5.0)
        here = n.combine(px, py, 0.0)
        for slot in range(gc.RING_SLOTS):
            cx, cy, cr = (n.attr(f'wk_dirt_ring{slot}_{c}') for c in ('x', 'y', 'r'))
            dist = n.vector_math('DISTANCE', here, n.combine(cx, cy, 0.0))
            rr = n.math('ADD', cr, n.math('MULTIPLY', n.math('SUBTRACT', nd, 0.5), n.math('MULTIPLY', ring_width, 0.8)))
            band = n.math('MULTIPLY', n.smoothstep(dist, n.math('MULTIPLY', rr, 0.92), rr), n.one_minus(n.smoothstep(dist, n.math('ADD', rr, ring_width), n.math('ADD', rr, n.math('MULTIPLY', ring_width, 1.8)))))
            band = n.math('MULTIPLY', band, n.math('GREATER_THAN', cr, 0.01))
            drum = band if drum is None else n.math('MAXIMUM', drum, band)
        drum_f = n.math('MULTIPLY', n.math('MULTIPLY', L.eff('drum_ring'), drum), n.mix(ring_width_fade, 0.5, 1.0))
        colour = n.mix_colour(n.math('MULTIPLY', drum_f, 0.85), colour, L.colour_of_luma(DRUM_TINT, n.math('MULTIPLY', L.luma(colour), 1.15)))
        L.add_part(drum_f, 'drum')

    # ---- 6 tar patches over lost setts, on a loose grid of sites
    if L.has('tar'):
        S = n.math('MAXIMUM', d('tar_spacing_m'), 1.0)
        cx_, cy_ = n.math('FLOOR', n.math('DIVIDE', px, S)), n.math('FLOOR', n.math('DIVIDE', py, S))
        ident = n.math('ADD', n.math('MULTIPLY', cx_, 73.0), n.math('MULTIPLY', cy_, 151.0))
        ident = n.math('ADD', ident, n.math('MULTIPLY', d('seed'), 3.0))
        r1 = L.white(ident, 0.0)
        r2 = L.white(ident, 17.0)
        centre_x = n.math('MULTIPLY', n.math('ADD', cx_, n.math('ADD', 0.15, n.math('MULTIPLY', r1[1], 0.7))), S)
        centre_y = n.math('MULTIPLY', n.math('ADD', cy_, n.math('ADD', 0.15, n.math('MULTIPLY', r1[2], 0.7))), S)
        lx, ly = n.math('SUBTRACT', px, centre_x), n.math('SUBTRACT', py, centre_y)
        theta = n.math('MULTIPLY', n.math('SUBTRACT', r1[3], 0.5), 3.14159)
        ct, st = n.math('COSINE', theta), n.math('SINE', theta)
        u = n.math('ADD', n.math('MULTIPLY', lx, ct), n.math('MULTIPLY', ly, st))
        v = n.math('SUBTRACT', n.math('MULTIPLY', ly, ct), n.math('MULTIPLY', lx, st))
        # the long half-size, shrunk so that tar never passes tar_max_share of the sites' area (the short half is 0.7 of it)
        a_cap = n.math('SQRT', n.math('DIVIDE', n.math('MULTIPLY', n.math('MULTIPLY', d('tar_max_share'), S), S), 2.2))
        a = n.math('MINIMUM', n.math('MULTIPLY', d('tar_patch_m'), n.math('ADD', 0.65, n.math('MULTIPLY', r2[1], 0.35))), a_cap)
        a = n.math('MAXIMUM', a, 0.05)
        e = n.math('SQRT', n.math('ADD', n.math('POWER', n.math('DIVIDE', u, a), 2.0), n.math('POWER', n.math('DIVIDE', v, n.math('MULTIPLY', a, 0.7)), 2.0)))
        lobes = n.math('MULTIPLY', n.math('SUBTRACT', L.noise(0.6, detail=3.0, w=6.0), 0.5), 0.5)
        scallop = n.math('MULTIPLY', n.math('SUBTRACT', L.noise(0.12, detail=2.0, w=7.0), 0.5), 0.35)
        e = n.math('ADD', e, n.math('ADD', lobes, scallop))
        inside = n.one_minus(n.smoothstep(e, 0.8, 1.0))
        has = n.math('LESS_THAN', r1[0], n.math('MULTIPLY', d('tar_patches'), L.role('tar_patches')))
        tar = n.math('MULTIPLY', n.math('MULTIPLY', inside, has), L.amount)
        old = n.math('LESS_THAN', r2[2], d('tar_weathered'))
        tar_k = n.mix(old, 0.28, 0.5)
        chips_n = L.noise(0.012, detail=0.0, rough=0.5, w=8.0)
        chips = n.math('MULTIPLY', n.smoothstep(chips_n, 0.60, 0.68), n.math('MULTIPLY', d('tar_chippings'), n.mix(fade, 0.25, 1.0)))
        tar_luma = n.math('MULTIPLY', L.luma(colour), n.math('MULTIPLY', tar_k, n.math('ADD', 1.0, n.math('MULTIPLY', chips, 2.2))))
        colour = n.mix_colour(tar, colour, L.colour_of_luma(TAR_TINT, tar_luma))
        rough_new = n.math('SUBTRACT', 0.62, n.math('MULTIPLY', d('tar_gloss'), 0.4))
        rough_tar = n.mix(old, rough_new, 0.88)
        rough = n.mix(tar, rough, rough_tar)
        flat = n.math('MULTIPLY', tar, 0.9)
        geo_n = n.geometry().outputs['Normal']
        normal = n.mix_vector(flat, normal, geo_n)
        wnormal = n.mix_vector(flat, wnormal, geo_n)
        L.add_part(tar, 'tar')

    # ---- 7 tar splash at the kerb foot: blobs along one or two stretches of the seam between gutter and kerb
    if L.has('splash'):
        near_seam = n.one_minus(n.smoothstep(seam, 0.0, 0.25))
        blobs = n.smoothstep(L.noise(0.25, detail=1.0, w=9.0, scale_socket=n.math('DIVIDE', 1.0, n.math('MAXIMUM', d('splash_m'), 0.05))), 0.6, 0.68)
        stretch_thr = L.thr(n.math('MULTIPLY', d('tar_splash'), 0.4), 1)
        stretch = n.smoothstep(L.noise(12.0, detail=1.0, w=10.0), stretch_thr, L.shift(stretch_thr, 0.04))
        splash = n.math('MULTIPLY', n.math('MULTIPLY', n.math('MULTIPLY', blobs, near_seam), stretch), L.eff('tar_splash'))
        splash = n.clamp01(n.math('MULTIPLY', splash, 3.3))
        colour = n.mix_colour(splash, colour, L.colour_of_luma(TAR_TINT, n.math('MULTIPLY', L.luma(colour), 0.5)))
        rough = n.mix(splash, rough, 0.55)
        L.add_part(splash, 'splash')

    # ---- 8 scrub strip on the flags in front of a whitened or scrubbed doorstep (same random and the same two shares as the steps layer)
    if L.has('scrub'):
        s_edge = n.math('SUBTRACT', 1.15, n.math('MULTIPLY', d('scrub_strip_m'), 1.3))
        door = n.smoothstep(n.math('ADD', g('M Step Foot'), n.math('MULTIPLY', n.math('SUBTRACT', L.noise(0.1, detail=2.0, w=11.0), 0.5), 0.3)), n.math('SUBTRACT', s_edge, 0.1), n.math('ADD', s_edge, 0.1))
        pick = n.math('LESS_THAN', g('M Entry Rand'), n.math('ADD', d('scrub_whitened_share'), d('scrub_scrubbed_share')))
        strip = n.math('MULTIPLY', n.math('MULTIPLY', door, pick), L.eff('scrub_strip'))
        pale = L.colour_of_luma(PALE_TINT, n.math('MULTIPLY', L.luma(colour), n.math('ADD', 1.0, d('scrub_lift'))))
        colour = n.mix_colour(n.math('MULTIPLY', strip, 0.9), colour, pale)
        L.add_part(strip, 'scrub')

    return L.finish_parts(colour=colour, roughness=rough, normal=normal, wet_normal=wnormal)
