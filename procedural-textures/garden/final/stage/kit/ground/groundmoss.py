# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# WK GROUND MOSS: flat painted moss, algae and liverwort on the ground (slot C: after the water layer, the joint layer and the cracks, before the rubbish, so litter lies on plants).
#   joint moss    a ribbon along the joints of setts and flags (tx_joint) and along the seams between stones (seam_dist, piece_gap), 1 to 3 cm real, drawn at least ribbon_dots wide,
#                 broken into pieces of broken_len, on joint_share of the joint length in the places the habitat field likes (moss_site: damp, shaded, beside walls and gutters, never
#                 on the crown, in the traffic lanes, near the fire or on a doorstep strip: the field is exactly 0 there and this layer multiplies by it again)
#   patch moss    soft patches on open ground for sets that have no joints (earth, gravel, stones); the set turns it on per role (patch_moss), a set with joints turns it off
#   algae fans    a dark green-black film under every downpipe outlet (a standing foot that touches a wall), radius algae_radius
#   liverwort     the one bright green: 0 to 2 patches of 10 to 40 cm at a pipe foot
#   far band      beyond the distance where the 3D pieces stop (Far Blend, set in the set file as far_band_handover_m): a slightly greener, darker strip along the gutter and the
#                 wall foot instead of single plants
# Moss is lighter than the stone beneath it (moss_lift x the stone's own brightness, so it follows what the water layer did) and saturated (the painter weakens colour); wet moss is
# darker and richer, matt, never glossy. It never covers more than the joint's own ribbon, so the joint grid still reads. Reads only bus masks and the incoming bundle.
# Amount 0: every effect factor contains the amount, so every output equals its input.
import bpy

from . import ground_common as gc
from .ground_common import GroundLayer, chroma

MASKS = ['moss_site', 'algae_site', 'shade', 'dampness', 'footfall', 'keepclear', 'crown', 'existing_growth', 'vertical_foot', 'wall_dist', 'seam_dist', 'piece_gap']
MOSS_DRY = chroma(77, 107, 59)
MOSS_WET = chroma(43, 77, 34)
ALGAE_DRY = chroma(105, 112, 82)
ALGAE_WET = chroma(48, 62, 42)
LIVER_DRY = chroma(95, 142, 65)
LIVER_WET = chroma(55, 110, 45)
BAND_TINT = (0.86, 0.97, 0.78)
WALL_REACH_M = 1.275            # the bus gives wall_dist as a share of the set's wall reach (CONTRACT.md); 1.275 m is the kit's default for it


def build(key='groundmoss', kit=None, elements=None):
    L = GroundLayer('groundmoss', 'WK GROUND MOSS', masks=MASKS, wet_normal=False, elements=elements)
    n, g, d = L.n, L.g, L.d
    tx = L.tx(kit) if L.has('joint') else None
    px, py, pz = L.pos()[1:]
    colour, rough, spec, coat = g('Colour'), g('Roughness'), g('Specular IOR Level'), g('Coat Weight')
    dot, fade = g('Dot Across'), g('Fade Near')
    wet = n.math('MULTIPLY', n.clamp01(g('Wet Mask')), d('wet_follow'))
    free = L.gate_free()
    unseen = n.one_minus(g('M Existing Growth'))
    stone_luma = L.luma(colour)
    seam_m = n.math('MULTIPLY', g('M Seam Dist'), 0.5)
    cover_parts = []

    def moss_colour(tint_dry, tint_wet, lift_mult, wet_mult):
        luma = n.math('MULTIPLY', stone_luma, n.math('MULTIPLY', lift_mult, n.mix(wet, 1.0, wet_mult)))
        tint = n.comb_rgb(n.mix(wet, tint_dry[0], tint_wet[0]), n.mix(wet, tint_dry[1], tint_wet[1]), n.mix(wet, tint_dry[2], tint_wet[2]))
        return L.colour_scale(tint, luma)

    moss_all = None
    # ---- joint moss: ribbon widths in plate dots
    if L.has('joint'):
        ribbon_w, ribbon_fade = L.mark_width(d('ribbon_m'), d('ribbon_dots'), dot)
        gap_m = n.math('MULTIPLY', g('M Piece Gap'), 0.3)
        ragged_w = n.math('MULTIPLY', ribbon_w, n.math('ADD', 0.45, n.math('MULTIPLY', L.noise(0.05, detail=2.0, w=45.0), 1.1)))          # a ribbon that swells and thins, with a ragged edge
        seam_ribbon = n.one_minus(n.smoothstep(seam_m, n.math('MULTIPLY', ragged_w, 0.3), n.math('MULTIPLY', ragged_w, 0.7)))
        gap_ribbon = n.one_minus(n.smoothstep(gap_m, n.math('MULTIPLY', ragged_w, 0.3), n.math('MULTIPLY', ragged_w, 0.7)))
        tx_ribbon = n.math('MAXIMUM', n.smoothstep(tx['joint'], 0.2, 0.7), n.math('MULTIPLY', n.smoothstep(tx['cavity'], 0.1, 0.45), 0.7))
        ribbon = n.math('MAXIMUM', n.math('MAXIMUM', seam_ribbon, gap_ribbon), tx_ribbon)
        piece_thr = L.thr(n.math('MULTIPLY', d('joint_share'), n.math('MAXIMUM', L.role('joint_share'), 0.05)), 1)
        pieces = n.smoothstep(L.noise(0.3, detail=1.0, w=41.0, scale_socket=n.math('DIVIDE', 1.0, n.math('MAXIMUM', n.math('MULTIPLY', d('broken_len'), 1.2), 0.1))),
                              L.shift(piece_thr, -0.02), L.shift(piece_thr, 0.03))
        bias = n.math('ADD', 1.0, n.math('MULTIPLY', d('shade_bias'), n.math('SUBTRACT', g('M Shade'), 0.5)))
        site = n.math('MULTIPLY', n.smoothstep(g('M Moss Site'), 0.03, 0.25), n.math('MINIMUM', bias, 1.3))
        joint_f = n.math('MULTIPLY', n.math('MULTIPLY', n.math('MULTIPLY', ribbon, pieces), n.math('MULTIPLY', site, free)), n.math('MULTIPLY', unseen, n.math('MULTIPLY', L.amount, n.math('MULTIPLY', L.role('joint_share'), n.mix(fade, 0.45, 1.0)))))
        joint_f = n.math('MULTIPLY', joint_f, ribbon_fade)
        moss_all = joint_f
        L.add_part(joint_f, 'joint_moss')
        L.add_part(n.math('MULTIPLY', n.math('MULTIPLY', ribbon, site), n.math('MULTIPLY', free, unseen)), 'joint_all', tonal=True)

    # ---- patch moss on open ground (sets with no joints)
    if L.has('patch'):
        q = n.math('ADD', n.math('MULTIPLY', n.math('SUBTRACT', L.noise(0.7, detail=3.0, w=42.0, scale_socket=n.math('DIVIDE', 1.0, n.math('MAXIMUM', d('patch_scale_m'), 0.1))), 0.5), 2.0), n.math('MULTIPLY', g('M Moss Site'), 1.5))
        patch = n.math('MULTIPLY', n.smoothstep(q, 0.45, 0.6), n.math('MULTIPLY', n.math('MULTIPLY', free, unseen), n.math('MULTIPLY', n.math('MULTIPLY', d('patch_moss'), L.role('patch_moss')), L.amount)))
        patch = n.math('MULTIPLY', patch, n.mix(fade, 0.7, 1.0))
        moss_all = patch if moss_all is None else n.math('MAXIMUM', moss_all, patch)
        L.add_part(patch, 'patch_moss')
    if moss_all is not None:
        rim = n.math('MULTIPLY', n.math('MULTIPLY', n.one_minus(n.smoothstep(moss_all, 0.3, 0.8)), n.math('GREATER_THAN', moss_all, 0.02)), d('moss_rim'))
        lift = n.math('MULTIPLY', d('moss_lift'), n.math('ADD', 1.0, n.math('MULTIPLY', rim, 0.3)))
        colour = n.mix_colour(n.math('MULTIPLY', moss_all, 0.92), colour, moss_colour(MOSS_DRY, MOSS_WET, lift, 0.72))
        cover_parts.append(moss_all)

    # ---- algae fans under every downpipe outlet and liverwort at a pipe foot: a standing foot that touches a wall (a post stands farther out)
    if L.has('algae') or L.has('liver'):
        vf = g('M Vertical Foot')
        outlet = n.one_minus(n.smoothstep(g('M Wall Dist'), d('outlet_reach'), n.math('ADD', d('outlet_reach'), 0.15)))
        fan_gate = n.math('MULTIPLY', n.math('MULTIPLY', free, unseen), n.math('ADD', 0.5, n.math('MULTIPLY', n.smoothstep(g('M Algae Site'), 0.0, 0.3), 0.5)))
    if L.has('algae'):
        edge = n.math('SUBTRACT', 1.08, n.math('MULTIPLY', d('algae_radius'), 1.8))
        ragged = n.math('ADD', 0.6, n.math('MULTIPLY', L.noise(0.12, detail=2.0, w=43.0), 0.8))
        fan = n.math('MULTIPLY', n.smoothstep(vf, n.math('SUBTRACT', edge, 0.08), n.math('ADD', edge, 0.25)), ragged)
        algae_f = n.math('MULTIPLY', n.math('MULTIPLY', n.math('MULTIPLY', fan, outlet), fan_gate), n.math('MULTIPLY', n.math('MULTIPLY', d('algae_fan'), L.role('algae_fan')), L.amount))
        algae_f = n.clamp01(algae_f)
        dark = n.one_minus(n.math('MULTIPLY', d('algae_dark'), 0.45))
        algae_luma = n.math('MULTIPLY', stone_luma, n.math('MULTIPLY', dark, n.mix(wet, 1.15, 0.8)))
        algae_tint = n.comb_rgb(n.mix(wet, ALGAE_DRY[0], ALGAE_WET[0]), n.mix(wet, ALGAE_DRY[1], ALGAE_WET[1]), n.mix(wet, ALGAE_DRY[2], ALGAE_WET[2]))
        colour = n.mix_colour(n.math('MULTIPLY', algae_f, 0.85), colour, L.colour_scale(algae_tint, algae_luma))
        cover_parts.append(algae_f)
        L.add_part(algae_f, 'algae')

    # ---- liverwort: at most a patch or two, at a pipe foot picked by a hash of where the foot stands
    if L.has('liver'):
        spot = n.math('ADD', n.math('MULTIPLY', n.math('FLOOR', n.math('DIVIDE', px, 2.0)), 91.0), n.math('MULTIPLY', n.math('FLOOR', n.math('DIVIDE', py, 2.0)), 53.0))
        spot = n.math('ADD', spot, n.math('MULTIPLY', d('seed'), 5.0))
        pick = n.math('LESS_THAN', L.white(spot, 3.0)[0], n.math('MULTIPLY', n.math('MULTIPLY', d('liverwort'), L.role('liverwort')), 0.5))
        ledge = n.math('SUBTRACT', 1.08, n.math('MULTIPLY', d('liverwort_m'), 1.8))
        lobes = n.math('ADD', 0.5, L.noise(0.08, detail=3.0, w=44.0))
        liver = n.math('MULTIPLY', n.smoothstep(n.math('MULTIPLY', vf, lobes), n.math('SUBTRACT', ledge, 0.05), n.math('ADD', ledge, 0.1)), n.math('MULTIPLY', n.math('MULTIPLY', outlet, pick), n.math('MULTIPLY', fan_gate, L.amount)))
        liver_tint = n.comb_rgb(n.mix(wet, LIVER_DRY[0], LIVER_WET[0]), n.mix(wet, LIVER_DRY[1], LIVER_WET[1]), n.mix(wet, LIVER_DRY[2], LIVER_WET[2]))
        liver_luma = n.math('MULTIPLY', stone_luma, n.math('MULTIPLY', d('moss_lift'), n.mix(wet, 1.1, 0.8)))
        colour = n.mix_colour(n.math('MULTIPLY', liver, 0.95), colour, L.colour_scale(liver_tint, liver_luma))
        cover_parts.append(liver)
        L.add_part(liver, 'liverwort')

    # ---- the far band along the gutter seam and the wall foot, where the 3D pieces have stopped
    if L.has('band'):
        band_m = n.math('MAXIMUM', d('far_band_m'), 0.05)
        band_seam = n.one_minus(n.smoothstep(seam_m, n.math('MULTIPLY', band_m, 0.3), band_m))
        band_wall = n.one_minus(n.smoothstep(n.math('MULTIPLY', g('M Wall Dist'), WALL_REACH_M), n.math('MULTIPLY', band_m, 0.3), band_m))
        band_site = n.smoothstep(g('M Moss Site'), 0.0, 0.2)
        band = n.math('MULTIPLY', n.math('MULTIPLY', n.math('MAXIMUM', band_seam, band_wall), n.math('MULTIPLY', free, unseen)),
                      n.math('MULTIPLY', n.math('MULTIPLY', d('far_band'), L.role('far_band')), n.math('MULTIPLY', g('Far Blend'), L.amount)))
        band = n.clamp01(n.math('MULTIPLY', band, n.math('ADD', 0.4, n.math('MULTIPLY', band_site, 0.6))))
        colour = L.colour_mul(colour, n.mix_vector(n.math('MULTIPLY', band, 0.8), (1.0, 1.0, 1.0), BAND_TINT))
        L.add_part(band, 'far_band')

    out = dict(colour=colour)
    if cover_parts:
        # moss, algae and liverwort are matt and give no clear coat
        cover = cover_parts[0]
        for c in cover_parts[1:]:
            cover = n.math('MAXIMUM', cover, c)
        out['roughness'] = n.mix(n.math('MULTIPLY', cover, 0.8), rough, 0.85)
        out['specular'] = n.math('MULTIPLY', spec, n.one_minus(n.math('MULTIPLY', cover, 0.5)))
        out['coat'] = n.math('MULTIPLY', coat, n.one_minus(n.math('MULTIPLY', cover, 0.9)))
    return L.finish_parts(**out)
