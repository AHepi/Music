# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# WALL CRACKS (node group WK WALL CRACKS, slot B: AFTER the water layer and the joints, and DULL). A FEW cracks and chips on walls, trims and plaster (rules C5, C6, C7 in part):
#   * STEPPED MINING CRACKS (C6) on the objects the set flags (object value wk_stepped; the plan: one or two houses of 28): a staircase through the mortar joints at about 45 degrees,
#     step_cm high, wider at the top, about seven steps long; position per house from its own seed. Low confidence for 1926: the set's flag says which houses.
#   * CORNER AND OPENING CRACKS: a few meandering cracks within about 0.25 m of a wall corner or an opening's edge (the corner picture), wavy lines of a noise cut thin, only where a
#     sparse gate lets them live (crack_amount): never a net.
#   * CHIPS at wall corners and opening corners (corner_chips, chip_cm): fresh pale stone, so they read on a dark wall; SPALLED PATCHES near the foot (spall_patches).
#   * PLASTER (plaster_cracks): thin map cracks along the edges of a few big cells (a Voronoi picture, gated sparse), for plaster walls; 0 for a coal-smoke row of brick houses.
# A crack is drawn at least crack_dots plate dots wide along the wall (the mark-width helper) and has a PALE DUST LIP (crack_pale) because a dark line on a dark wall is crushed by the
# film; it fades with distance (the painter makes up its own texture there). DULL: where there is a crack the roughness goes back to 0.9, the shine is cut by 35 % and the coat (water
# film) by 45 % (dull): the roughness and the shine are done; the COAT (water film) cut is NOT done: a coat made from noise changed the picture at Amount 0 in the self-test (found, not
# understood; REQUESTS.md). The crack has a real slope (slope_mm, a relief on the incoming normal) so a lamp lights one side.
# Amount 0 gives the inputs back exactly.
from . import dials_walls
from .walls_common import WallLayer, CORNER_REACH_M

KEY = 'wallcracks'
GROUP = 'WK WALL CRACKS'
MASKS = ['corner', 'reveal', 'height', 'tx_cell', 'tx_cavity', 'frame_valid']
PARTS = ['stepped', 'corner_cracks', 'chips', 'plaster']
LIP = (0.30, 0.26, 0.20)           # pale dust along a crack (albedo)
FRESH = (0.38, 0.30, 0.22)         # fresh stone where a chip came away
STEPS = 7.0
CM = 0.01
REAL_CRACK_M = 4.0 * 0.001      # a real mining crack is a few millimetres wide; it is drawn at least crack_dots dots wide


def build(key=KEY):
    dials_walls.register_all()
    L = WallLayer(key, GROUP, masks=MASKS, parts=PARTS)
    n, g, dial = L.n, L.g, L.dial
    fade = g('Fade Near')
    fv = g('M Frame Valid')
    h = L.height_eff(g('M Height'), fv)

    # ---- sizes: a crack is never thinner than crack_dots (along the wall for an upright one, up the wall for a level one)
    w_along, w_fade = L.width_dots(REAL_CRACK_M, dial('crack_dots'), along=True)
    w_up, _ = L.width_dots(REAL_CRACK_M, dial('crack_dots'), along=False)
    keep = L.mul(fade, w_fade)

    # ---- stepped mining crack: a staircase of level and upright pieces through the joints, flagged houses only
    flagged = L.mul(L.gt(n.attr('wk_stepped'), 0.5), dial('stepped_cracks'))
    st_h = L.mul(dial('step_cm'), 0.01)
    st_w = L.mul(st_h, 1.5)
    a0 = L.mad(L.house_rand(0.2), 2.0, -1.0)                                        # where along the front the crack starts: between -1 and +1 m of the house's middle
    v0 = L.mad(L.house_rand(0.5), 1.2, 3.2)                                         # and how high above its floor
    along_o, up_o = L.local_frame()
    t = L.div_safe(L.sub(v0, up_o), st_h)                                           # steps down from the start
    k = n.math('FLOOR', t)
    fy = L.sub(t, k)
    dx = L.sub(L.div_safe(L.sub(along_o, a0), st_w), k)
    taper = L.mad(L.div_safe(t, STEPS), -0.5, 1.3)                                  # wider at the top
    d_level = L.div_safe(L.mul(fy, st_h), L.mul(w_up, taper))                       # distance to the level piece (the floor of the cell), in crack widths
    d_up = L.div_safe(L.mul(L.absv(L.sub(1.0, dx)), st_w), L.mul(w_along, taper))   # and to the upright piece (the right side of the cell)
    in_cell = L.mul(L.sstep(dx, -0.05, 0.0), L.one_minus(L.sstep(dx, 1.0, 1.05)))
    in_len = L.mul(L.sstep(t, -0.1, 0.1), L.one_minus(L.sstep(t, STEPS - 0.3, STEPS)))
    stepped = L.mul(L.mul(L.mul(L.one_minus(L.sstep(L.mn(d_level, d_up), 0.0, 1.0)), L.mul(in_cell, in_len)), flagged), keep)

    # ---- corner and opening cracks: thin lines of a slow noise within 0.25 m of a corner or an opening, a sparse gate
    near = L.one_minus(L.sstep(L.mul(g('M Corner'), CORNER_REACH_M), 0.04, 0.25))
    nz_ = L.noise(L.mul(L.inv(w_along), REAL_CRACK_M), 1.6, detail=3.0)                       # (frequency along: meanders over about a metre, never finer than the crack)
    gate = L.lt(L.house_rand(0.9), L.mul(dial('crack_amount'), 1.2))                  # a few houses only, never every house
    thin = L.one_minus(L.sstep(L.absv(L.sub(nz_, 0.5)), 0.0, L.mul(w_along, 0.5)))
    corner_cracks = L.mul(L.mul(L.mul(near, gate), thin), L.mul(keep, fv))

    # ---- chips at corners and opening corners, and spalled patches near the foot (fresh pale stone); one number per brick or stone (tx_cell) decides which bricks
    cell = g('M Tx Cell')
    chip_near = L.one_minus(L.sstep(L.mul(g('M Corner'), CORNER_REACH_M), L.mul(dial('chip_cm'), CM), L.mul(dial('chip_cm'), 2.5 * CM)))
    foot_zone = L.mul(L.mul(L.one_minus(L.sstep(h, 0.3, 0.8)), L.gt(h, 0.05)), dial('spall_patches'))
    chips = L.mul(L.mul(L.mx(L.mul(chip_near, fv), foot_zone), L.lt(cell, L.mx(L.mul(dial('corner_chips'), 0.5), L.mul(dial('spall_patches'), 0.3)))), fade)

    # ---- plaster map cracks: edges of big cells of a Voronoi picture, a few houses only
    vor = n.new('ShaderNodeTexVoronoi')
    vor.voronoi_dimensions = '3D'
    vor.feature = 'DISTANCE_TO_EDGE'
    L.tree.links.new(L.coord(0.9, 0.9), vor.inputs['Vector'])
    vor.inputs['Scale'].default_value = 1.0
    plaster = L.mul(L.mul(L.one_minus(L.sstep(vor.outputs['Distance'], 0.0, L.mul(w_along, 0.5))), L.lt(L.house_rand(0.4), dial('plaster_cracks'))), keep)

    crack = L.c01(L.add(L.add(stepped, corner_cracks), plaster))

    # ---- colour: dark line with a pale dust lip, pale chips and spalls
    dark = L.gain(g('Colour'), L.mad(crack, L.mul(dial('crack_contrast'), -6.0), 1.0))
    colour = L.lift_to(dark, LIP, L.mul(L.mul(crack, dial('crack_pale')), 1.0))
    colour = L.tint(colour, FRESH, L.mul(L.mul(chips, dial('chip_pale')), 0.8))

    # ---- dull: roughness back to 0.9, shine and water film cut, a real slope
    mark = L.mx(crack, chips)
    dull = L.mul(mark, dial('dull'))
    rough = L.lerp(dull, g('Roughness'), 0.9)
    spec = L.mul(g('Specular IOR Level'), L.mad(dull, -0.35, 1.0))
    normal = L.bump_raw(L.mad(L.mx(crack, 0.0), L.mul(dial('slope_mm'), -0.001), L.mul(chips, -0.003)))

    mask = L.mul(L.sstep(L.mx(crack, chips), 0.4, 0.6), L.gt(L.amount, 1e-4))
    return L.finish_layer(colour=L.blend_colour(g('Colour'), colour), roughness=L.blend_float(g('Roughness'), rough), specular=L.blend_float(g('Specular IOR Level'), spec),
                          normal=L.blend_normal(g('Normal'), normal, fade), mask=mask,
                          parts={'stepped': stepped, 'corner_cracks': corner_cracks, 'chips': chips, 'plaster': plaster})
