# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# WK GROUND CRACKS: cracks, chips, tilted and sunk stones of the ground (slot B: AFTER the water layer and the joint layer, so the water cannot wash a narrow dark line out;
# every mark makes itself DULL (roughness 0.9, shine less 35 percent, water film less 45 percent) and carries a real slope as a Bump, which the water cannot smooth).
#   flags    (from the number per flag, tx_cell, made different on every tile of the photo): fine cracks on flag_fine_share of flags, broken flags with a wider gap on flag_broken_share,
#            tilted or sunk flags (one edge a few mm proud, with a shadow line) on flag_tilt_share, chipped corners on corner_chip_share; flags near the kerb and the seams get more
#   kerbs    (from edge_dist and piece_gap): scalloped chips along the top edge on kerb_chip_share of the length, open dark joints between stones, cracked stones (kerb_break_share),
#            pale wheel scuffs on the faces
#   setts    (from tx_cell, tx_joint, seam_dist, footfall): sett_disturbed_share of the setts tilted or sunk (more beside seams and in the wheel bands), sunken oval patches,
#            missing setts as a dark hollow with dust, open_joint_share of the joint length open and darker (never past max_contrast: the joint layer's own grid is kept)
# The crack lines are the edges of a loose Voronoi pattern about one flag across, bent a little by noise, so cracks run corner to edge, fork at the meeting points and end in
# stones; each is drawn at least crack_dots plate dots wide (widened with distance up to Inflate Limit, then it gives way: a mark that would have to be drawn too fat is not drawn),
# only near the camera (near_only), with the contrast of a plate mark that the painter keeps (crack_contrast on a surround of ref_brightness).
# Amount 0: every effect is a product that contains the amount, so every output equals its input.
import bpy

from . import ground_common as gc
from .ground_common import GroundLayer, bump_normal

MASKS = ['edge_dist', 'seam_dist', 'cover_dist', 'footfall', 'piece_gap']


def build(key='groundcracks', kit=None, elements=None):
    L = GroundLayer('groundcracks', 'WK GROUND CRACKS', masks=MASKS, wet_normal=False, elements=elements)
    n, g, d = L.n, L.g, L.d
    flags, kerbs, setts = L.has('flag'), L.has('kerb'), L.has('sett')
    tx = L.tx(kit) if (flags or setts) else None
    px, py, pz = L.pos()[1:]
    colour, rough, spec, coat, normal = g('Colour'), g('Roughness'), g('Specular IOR Level'), g('Coat Weight'), g('Normal')
    dot = g('Dot Across')
    puddle = g('Puddle Mask')
    fade_near = g('Fade Near')
    near = n.math('MULTIPLY', L.near_fade('near_only', 5.0), L.amount)

    # ---- the crack colour factor (a plate contrast on a surround, in scene light) and the widths
    mult = n.math('MAXIMUM', n.math('POWER', n.math('MAXIMUM', n.one_minus(n.math('DIVIDE', d('crack_contrast'), n.math('MAXIMUM', d('ref_brightness'), 0.05))), 0.05), 2.2), 0.12)
    drop = n.one_minus(mult)                                   # how much a full-strength crack takes off the colour
    w_fine, f_fine = L.mark_width(n.math('MULTIPLY', d('crack_real_mm'), 0.001), d('crack_dots'), dot)

    if flags or setts:
        # the numbers per stone: a whole number from tx_cell and the tile of the photo (so every flag and sett has its own), random numbers from it
        coord = n.new('ShaderNodeTexCoord')
        ux, uy, uz = n.separate(coord.outputs['UV'])
        tile = n.math('ADD', n.math('MULTIPLY', n.math('FLOOR', ux), 131.0), n.math('MULTIPLY', n.math('FLOOR', uy), 977.0))
        ident = n.math('ADD', n.math('ADD', L.cell_id(tx['cell']), tile), n.math('MULTIPLY', d('seed'), 7.0))
        rnd = L.white(ident, 0.0)
        rnd2 = L.white(ident, 31.0)
        joint_wide = n.smoothstep(tx['joint'], 0.05, 0.7)               # the joint and its shoulders (from the joint picture: smooth; the cavity picture is grainy on the stone faces)
        plateau = n.one_minus(joint_wide)                               # the stone's own face (the number per stone is only true there; joints carry one shared number)

    if flags or kerbs:
        # the crack lines: edges of a Voronoi pattern (distance to the nearest edge, in metres), bent by noise; a slow gate leaves single segments that narrow to a point
        bend = n.math('MULTIPLY', n.math('SUBTRACT', L.noise(0.7, detail=2.0, w=21.0), 0.5), 0.25)
        warped = n.vector_math('ADD', L.pos()[0], n.combine(bend, n.math('MULTIPLY', bend, 0.7), 0.0))
        vor = n.new('ShaderNodeTexVoronoi')
        vor.voronoi_dimensions = '2D'
        vor.feature = 'DISTANCE_TO_EDGE'
        L.tree.links.new(warped, vor.inputs['Vector'])
        L.tree.links.new(n.math('DIVIDE', 1.0, n.math('MAXIMUM', d('crack_scale_m'), 0.2)), vor.inputs['Scale'])
        vor.inputs['Randomness'].default_value = 1.0
        edge_m = n.math('MULTIPLY', vor.outputs['Distance'], d('crack_scale_m'))     # metres to the nearest crack line
        gate_noise = L.noise(0.55, detail=1.0, w=30.0)
        gate_thr = L.thr(0.5, 1)
        taper = n.smoothstep(gate_noise, L.shift(gate_thr, -0.05), L.shift(gate_thr, 0.1))

        def line(width):
            w = n.math('MAXIMUM', n.math('MULTIPLY', width, taper), 0.0001)         # never exactly 0: a smoothstep between two equal numbers is not defined
            return n.one_minus(n.smoothstep(edge_m, n.math('MULTIPLY', w, 0.3), n.math('MULTIPLY', w, 0.55)))

    acc = dict(dark=None, narrow=None, wide=None, pale=None, scuff=None)
    heights = []

    def add_cut(fraction):
        factor = n.one_minus(fraction)
        acc['dark'] = factor if acc['dark'] is None else n.math('MULTIPLY', acc['dark'], factor)

    def add_dark(strength, depth_scale=1.0):
        add_cut(n.math('MULTIPLY', strength, n.math('MULTIPLY', drop, depth_scale)))

    def add_dull(strength, wide=False):
        """Narrow marks (cracks, joints, chips) cut the shine a little (35 percent) and the water film (45 percent); wide patches (a sunk or missing sett, a tilted stone: dust and
        dirt fill, matt) cut the clear coat almost completely, or the sharp coat glints would stay on a matt patch."""
        slot = 'wide' if wide else 'narrow'
        acc[slot] = strength if acc[slot] is None else n.math('MAXIMUM', acc[slot], strength)

    # ================================================================= flags
    if flags:
        w_gap, f_gap = L.mark_width(n.math('MULTIPLY', d('broken_gap_mm'), 0.001), n.math('ADD', d('crack_dots'), 1.5), dot)
        site = n.math('MAXIMUM', n.one_minus(n.smoothstep(g('M Seam Dist'), 0.0, 0.8)), n.one_minus(n.smoothstep(g('M Cover Dist'), 0.0, 0.5)))
        boost = n.math('ADD', 1.0, n.math('MULTIPLY', d('site_bias'), n.math('SUBTRACT', n.math('MULTIPLY', site, 2.0), 0.4)))       # nearer the kerb and the seams, near covers
        flag_amt = n.math('MULTIPLY', L.role('flag_cracks'), n.math('MULTIPLY', d('flag_cracks'), near))
        # one random number set per flag-sized cell of the world grid (the stones' own numbers from the picture are one per picture tile on these surfaces, which gave whole tiles)
        f_ident = n.math('ADD', n.math('ADD', n.math('MULTIPLY', n.math('FLOOR', n.math('DIVIDE', px, 0.6)), 131.0), n.math('MULTIPLY', n.math('FLOOR', n.math('DIVIDE', py, 0.9)), 977.0)), n.math('MULTIPLY', d('seed'), 7.0))
        frnd, frnd2 = L.white(f_ident, 0.0), L.white(f_ident, 31.0)
        fine_sel = n.math('LESS_THAN', frnd[0], n.math('MULTIPLY', d('flag_fine_share'), boost))
        broken_sel = n.math('LESS_THAN', L.white(f_ident, 9.0)[0], n.math('MULTIPLY', d('flag_broken_share'), boost))
        tilt_sel = n.math('LESS_THAN', L.white(f_ident, 17.0)[0], n.math('MULTIPLY', d('flag_tilt_share'), boost))
        chip_cell = n.math('ADD', n.math('MULTIPLY', n.math('FLOOR', n.math('DIVIDE', px, 0.35)), 53.0), n.math('MULTIPLY', n.math('FLOOR', n.math('DIVIDE', py, 0.35)), 17.0))
        chip_sel = n.math('LESS_THAN', L.white(n.math('ADD', chip_cell, n.math('MULTIPLY', d('seed'), 3.0)), 61.0)[0], n.math('MULTIPLY', d('corner_chip_share'), 0.15))      # about corner_chip_share of the flags have one chip on their edge
        fine = n.math('MULTIPLY', n.math('MULTIPLY', line(w_fine), n.math('MULTIPLY', fine_sel, plateau)), n.math('MULTIPLY', flag_amt, f_fine))
        gap = n.math('MULTIPLY', n.math('MULTIPLY', line(w_gap), n.math('MULTIPLY', broken_sel, plateau)), n.math('MULTIPLY', flag_amt, f_gap))
        add_dark(fine)
        add_dark(gap)
        add_dull(n.math('MAXIMUM', fine, gap))
        heights.append(n.math('MULTIPLY', n.math('MAXIMUM', n.math('MULTIPLY', fine, 0.4), gap), -0.004))
        L.add_part(fine, 'flag_fine')
        L.add_part(gap, 'flag_broken')
        L.add_part(n.math('MULTIPLY', n.math('MULTIPLY', fine_sel, plateau), flag_amt), 'flag_fine_cells', tonal=True)
        L.add_part(n.math('MULTIPLY', n.math('MULTIPLY', broken_sel, plateau), flag_amt), 'flag_broken_cells', tonal=True)
        # tilted or sunk: the stone's face lifted or lowered by a few mm; its edge slopes down into the joint (a lit edge on one side, a shadow on the other)
        lip = n.math('MULTIPLY', n.math('SUBTRACT', frnd2[0], 0.5), n.math('MULTIPLY', d('tilt_lip'), 0.002))
        tilt = n.math('MULTIPLY', n.math('MULTIPLY', n.math('MULTIPLY', tilt_sel, plateau), flag_amt), fade_near)
        heights.append(n.math('MULTIPLY', lip, tilt))
        add_cut(n.math('MULTIPLY', tilt, n.math('MULTIPLY', d('lip_dark'), 0.4)))                        # a tilted stone sits a little darker (the shadow line itself comes from the slope)
        add_dull(n.math('MULTIPLY', tilt, 0.5), wide=True)
        L.add_part(tilt, 'flag_tilt')
        # chipped corner: a dark notch at the stone's edge where a blob of noise reaches the joint
        blob = n.smoothstep(L.noise(0.12, detail=1.0, w=22.0, scale_socket=n.math('DIVIDE', 1.0, n.math('MAXIMUM', d('chip_m'), 0.02))), 0.58, 0.66)
        chip = n.math('MULTIPLY', n.math('MULTIPLY', n.math('MULTIPLY', chip_sel, flag_amt), joint_wide), blob)
        add_dark(chip, 0.8)
        add_dull(chip)
        heights.append(n.math('MULTIPLY', chip, -0.004))
        L.add_part(chip, 'flag_chip')

    # ================================================================= kerbs
    if kerbs:
        kerb_amt = n.math('MULTIPLY', L.role('kerb_chips'), n.math('MULTIPLY', d('kerb_chips'), near))
        edge_m_kerb = n.math('MULTIPLY', g('M Edge Dist'), 0.3)
        gap_m = n.math('MULTIPLY', g('M Piece Gap'), 0.3)
        chip_w, chip_fade = L.mark_width(0.02, 9.0, dot)
        span_thr = L.thr(n.math('MULTIPLY', d('kerb_chip_share'), 0.6), 1)       # the ragged ends of a chipped run add to its length: 0.6 of the dial is the run itself
        span = n.smoothstep(L.noise(0.3, detail=1.0, w=23.0, scale_socket=n.math('DIVIDE', 1.0, n.math('MAXIMUM', n.math('MULTIPLY', d('chip_m'), 10.0), 0.2))), L.shift(span_thr, -0.02), L.shift(span_thr, 0.03))
        reach = n.math('MULTIPLY', chip_w, n.math('ADD', 0.6, L.noise(0.04, detail=1.0, w=24.0)))
        k_chip = n.math('MULTIPLY', n.math('MULTIPLY', n.one_minus(n.smoothstep(edge_m_kerb, reach, n.math('MULTIPLY', reach, 1.4))), span), n.math('MULTIPLY', kerb_amt, chip_fade))
        acc['pale'] = k_chip
        heights.append(n.math('MULTIPLY', k_chip, -0.008))
        add_dull(k_chip)
        L.add_part(k_chip, 'kerb_chips')
        # open dark joints between kerb stones, and cracked stones (the same crack lines inside a slow gate of about one stone in fifteen)
        open_w, open_fade = L.mark_width(n.math('MULTIPLY', d('kerb_joint_open'), 0.001), d('crack_dots'), dot)
        jsel = n.smoothstep(L.noise(0.9, detail=1.0, w=25.0), L.thr(0.6, 1) - 0.03, L.thr(0.6, 1) + 0.03)
        k_joint = n.math('MULTIPLY', n.one_minus(n.smoothstep(gap_m, n.math('MULTIPLY', open_w, 0.3), n.math('MULTIPLY', open_w, 0.6))), n.math('MULTIPLY', jsel, n.math('MULTIPLY', kerb_amt, open_fade)))
        brk_thr = L.thr(n.math('MULTIPLY', d('kerb_break_share'), 2.5), 1)
        brk = n.smoothstep(L.noise(1.1, detail=1.0, w=26.0), L.shift(brk_thr, -0.02), L.shift(brk_thr, 0.03))
        k_crack = n.math('MULTIPLY', n.math('MULTIPLY', line(w_fine), brk), n.math('MULTIPLY', kerb_amt, f_fine))
        k_dark = n.math('MAXIMUM', k_joint, k_crack)
        add_dark(k_dark)
        add_dull(k_dark)
        heights.append(n.math('MULTIPLY', k_dark, -0.004))
        L.add_part(k_dark, 'kerb_joints')
        # pale wheel scuffs on the standing faces
        nz = n.math('ABSOLUTE', n.separate(n.new('ShaderNodeNewGeometry').outputs['Normal'])[2])
        face = n.one_minus(n.smoothstep(nz, 0.35, 0.7))
        scuff = n.math('MULTIPLY', n.math('MULTIPLY', n.smoothstep(L.noise(0.1, detail=2.0, w=27.0), 0.62, 0.7), face), n.math('MULTIPLY', kerb_amt, n.math('MULTIPLY', d('kerb_scuffs'), 0.6)))
        acc['scuff'] = scuff
        L.add_part(scuff, 'kerb_scuffs')

    # ================================================================= setts
    if setts:
        sett_amt = n.math('MULTIPLY', L.role('sett_disturb'), n.math('MULTIPLY', d('sett_disturb'), near))
        wheel = n.smoothstep(g('M Footfall'), 0.6, 1.0)
        s_site = n.math('MAXIMUM', n.one_minus(n.smoothstep(g('M Seam Dist'), 0.0, 0.7)), n.math('MULTIPLY', wheel, 0.6))
        s_site = n.math('MAXIMUM', s_site, n.one_minus(n.smoothstep(g('M Cover Dist'), 0.0, 0.5)))
        s_boost = n.math('ADD', 0.5, n.math('MULTIPLY', s_site, 1.5))
        near_s = n.math('MULTIPLY', sett_amt, fade_near)
        dist_sel = n.math('MULTIPLY', n.math('LESS_THAN', rnd[0], n.math('MULTIPLY', d('sett_disturbed_share'), s_boost)), plateau)      # on the stone's own face only
        miss_sel = n.math('MULTIPLY', n.math('LESS_THAN', rnd[1], n.math('MULTIPLY', d('missing_share'), s_boost)), plateau)
        tilt_s = n.math('MULTIPLY', dist_sel, near_s)
        lip_s = n.math('MULTIPLY', n.math('SUBTRACT', rnd2[1], 0.5), 0.012)
        heights.append(n.math('MULTIPLY', lip_s, tilt_s))
        add_cut(n.math('MULTIPLY', tilt_s, 0.3))
        add_dull(n.math('MULTIPLY', tilt_s, 0.6), wide=True)
        # sunken oval patches: a slow gate of noise (about sunken_patch across) in the sites; the setts inside lie lower, a little darker with dust
        sunk_thr = L.thr(0.15, 1)
        sunk = n.math('MULTIPLY', n.smoothstep(L.noise(0.8, detail=1.0, w=28.0, scale_socket=n.math('DIVIDE', 1.0, n.math('MAXIMUM', d('sunken_patch'), 0.2))), sunk_thr, sunk_thr + 0.04), n.math('MULTIPLY', s_site, near_s))
        heights.append(n.math('MULTIPLY', n.math('MULTIPLY', sunk, plateau), n.math('MULTIPLY', d('sunk_depth_mm'), -0.001)))
        add_dark(sunk, 0.55)
        add_dull(n.math('MULTIPLY', sunk, 0.8), wide=True)
        # missing setts: a dark hollow with dust fill (the whole sett lowered, its walls are the joint)
        missing = n.math('MULTIPLY', miss_sel, near_s)
        heights.append(n.math('MULTIPLY', missing, n.math('MULTIPLY', d('missing_depth_mm'), -0.001)))
        add_dark(missing, 0.7)
        add_dull(missing, wide=True)
        L.add_part(n.math('MAXIMUM', tilt_s, n.math('MAXIMUM', sunk, missing)), 'sett_disturbed')
        # open joints: a share of the joint length darker and dull
        osel_thr = L.thr(d('open_joint_share'), 1)
        osel = n.smoothstep(L.noise(0.6, detail=1.0, w=29.0), L.shift(osel_thr, -0.02), L.shift(osel_thr, 0.03))
        openj = n.math('MULTIPLY', n.math('MULTIPLY', n.smoothstep(tx['joint'], 0.1, 0.6), osel), near_s)
        add_cut(n.math('MULTIPLY', openj, d('open_dark')))
        add_dull(openj)
        heights.append(n.math('MULTIPLY', openj, -0.003))
        L.add_part(openj, 'sett_joints')
        L.add_part(n.math('MULTIPLY', n.smoothstep(tx['joint'], 0.1, 0.6), near_s), 'sett_joint_all', tonal=True)

    # ================================================================= put it together
    out = {}
    out_colour = colour
    if acc['scuff'] is not None:
        out_colour = n.mix_colour(n.clamp01(acc['scuff']), out_colour, L.colour_scale(out_colour, 1.45))
    if acc['pale'] is not None:
        out_colour = n.mix_colour(n.clamp01(acc['pale']), out_colour, L.colour_scale(out_colour, 1.6))
    if acc['dark'] is not None:
        out_colour = L.colour_scale(out_colour, acc['dark'])
    out['colour'] = out_colour
    # dull: the water film gives way and the stone goes matt where a mark is (less under a puddle: the water covers it)
    water_off = n.math('MULTIPLY', d('dull'), n.one_minus(n.math('MULTIPLY', puddle, 0.8)))
    dull = n.math('MULTIPLY', n.clamp01(acc['narrow']), water_off) if acc['narrow'] is not None else 0.0
    wide = n.math('MULTIPLY', n.clamp01(acc['wide']), water_off) if acc['wide'] is not None else 0.0
    out['roughness'] = n.mix(n.math('MAXIMUM', dull, wide), rough, 0.9)
    out['specular'] = n.math('MULTIPLY', spec, n.one_minus(n.math('ADD', n.math('MULTIPLY', dull, 0.2), n.math('MULTIPLY', wide, 0.25))))
    out['coat'] = n.math('MULTIPLY', coat, n.one_minus(n.math('MINIMUM', 1.0, n.math('ADD', n.math('MULTIPLY', dull, 0.2), n.math('MULTIPLY', wide, 0.4)))))
    if heights:
        total = None
        for h in heights:
            total = h if total is None else n.math('ADD', total, h)
        relief = n.math('MULTIPLY', n.math('MULTIPLY', n.mix(fade_near, 0.5, 1.0), n.math('GREATER_THAN', L.amount, 0.0)), d('relief'))
        out['normal'] = n.mix_vector(relief, normal, bump_normal(L, total, relief, 1.0, normal))
    return L.finish_parts(**out)
