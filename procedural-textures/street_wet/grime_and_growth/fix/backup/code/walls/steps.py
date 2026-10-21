# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# STEPS (node group WK STEPS, slot A). Doorsteps whitened, scrubbed or worn (rules S8 and C4; medium confidence for a northern pit row). Found by the standard masks step_top (1 on the tread of a
# step near an entrance), step_edge (distance in from the tread's outer edge) and entry_rand (one random number per entrance, shared with the flag in front of the door), at the
# surface's own world position: the steps are part of the trim mesh, no object is named.
#   * per door: entry_rand below whitened_share = whitened (a pale frame of frame_m, never narrower than frame_dots plate dots, along the nosing, and a pale riser), below
#     whitened_share + scrubbed_share = scrubbed pale (tread_pale), the rest plain;
#   * boots grey the middle of the tread (boot_grey: footfall), polish on the worn centre (wear_polish: duller colour, shinier surface), a worn dish (dish_depth: a relief on the
#     incoming normal, faded with distance), a chipped nosing on nosing_chips of the steps (edge_dist; fresh buff stone);
#   * white goes grey when wet because the water layer comes after this layer (slot A).
# The whitened stone is the PALEST thing in a row of dark houses: that is the point (pale-first on dark walls). Only up-facing parts of the step (the tread) get the full frame; the riser
# and the foot of the doorway get riser_share of it.
# Amount 0 gives the inputs back exactly.
from . import dials_walls
from .walls_common import WallLayer, STEP_REACH_M, EDGE_REACH_M

KEY = 'steps'
GROUP = 'WK STEPS'
MASKS = ['step_top', 'step_edge', 'entry_rand', 'edge_dist', 'footfall', 'step_foot', 'height', 'frame_valid']
PARTS = ['whitened', 'scrubbed', 'dish', 'chips']
WHITE = (0.88, 0.86, 0.78)         # whitened stone: nearly the palest albedo a surface can have (the doorstep is dimly lit, so only a very pale stone reads)
BUFF = (0.34, 0.25, 0.14)          # fresh buff stone of a chip
GREY = (0.16, 0.15, 0.14)
SCRUB = (0.60, 0.54, 0.45)         # scrubbed pale sandstone


def build(key=KEY):
    dials_walls.register_all()
    L = WallLayer(key, GROUP, masks=MASKS, parts=PARTS)
    n, g, dial = L.n, L.g, L.dial
    fade = g('Fade Near')
    _, nrm, _, _ = L.frame()
    _, _, nz = n.separate(nrm)
    up_facing = L.sstep(nz, 0.5, 0.85)

    h = L.height_eff(g('M Height'), g('M Frame Valid'))
    near_door = L.sstep(g('M Step Foot'), 0.05, 0.25)                      # the soft spot round an entrance: no step is whitened away from a door
    low = L.mul(L.sstep(h, 0.02, 0.05), L.one_minus(L.sstep(h, 0.45, 0.6)))    # only the lowest part of the trim: no wall or lintel above the doorway
    zone = L.mul(near_door, low)
    pale_fill = L.mul(0.4, L.lerp(up_facing, dial('riser_share'), 1.0))      # the whole tread (and, riser_share of it, the riser) is at least scrubbed pale

    rnd = g('M Entry Rand')
    ws = dial('whitened_share')
    white_door = L.lt(rnd, ws)
    scrub_door = L.mul(L.lt(rnd, L.add(ws, dial('scrubbed_share'))), L.one_minus(white_door))

    # ---- the frame along every sharp edge of the step (the nosing and the edges of the riser): frame_m, never narrower than frame_dots dots across the view
    frame_m, frame_fade = L.width_dots(dial('frame_m'), dial('frame_dots'), along=False)
    d_edge = L.mn(L.mul(g('M Step Edge'), STEP_REACH_M), L.mul(g('M Edge Dist'), EDGE_REACH_M))
    frame = L.one_minus(L.sstep(d_edge, frame_m, L.mad(frame_m, 1.25, 0.01)))
    boots = L.mul(L.mul(dial('boot_grey'), L.sstep(g('M Footfall'), 0.4, 0.9)), L.mul(zone, up_facing))
    white = L.mul(L.mul(zone, L.mx(frame, pale_fill)), white_door)
    scrub = L.mul(zone, scrub_door)

    # ---- worn dish and polish in the middle of the tread, a chipped nosing on some steps
    dish = L.mul(L.mul(L.sstep(g('M Footfall'), 0.35, 0.9), L.mul(zone, up_facing)), L.sstep(d_edge, 0.04, 0.12))
    chip_door = L.lt(L.frac(L.mad(rnd, 37.0, 0.31)), dial('nosing_chips'))
    cm = L.inv(dial('chip_m'))
    n_chip = L.stretch(L.noise(cm, cm, detail=1.0), 3.0)
    edge_near = L.one_minus(L.sstep(L.mul(g('M Edge Dist'), EDGE_REACH_M), 0.01, 0.03))
    chips = L.mul(L.mul(L.mul(edge_near, L.mul(zone, up_facing)), L.mul(chip_door, L.sstep(n_chip, 0.5, 0.7))), fade)

    # ---- colour
    colour = L.tint(g('Colour'), WHITE, L.mul(white, 0.95))
    colour = L.tint(colour, SCRUB, L.mul(scrub, L.mul(dial('tread_pale'), 0.9)))
    colour = L.tint(colour, GREY, L.mul(boots, 0.45))
    colour = L.tint(colour, BUFF, L.mul(chips, 0.9))

    # ---- surface: polish where worn (rough down, spec up), a dish as a relief
    polish = L.mul(dial('wear_polish'), dish)
    rough = L.c01(L.mad(polish, -0.3, g('Roughness')))
    spec = L.c01(L.mad(polish, 0.25, g('Specular IOR Level')))
    normal = L.bump_raw(L.mul(dish, L.mul(dial('dish_depth'), -1.0)))

    mask = L.mul(L.sstep(L.mx(white, L.mul(scrub, 0.8)), 0.4, 0.7), L.gt(L.amount, 1e-4))
    return L.finish_layer(colour=L.blend_colour(g('Colour'), colour), roughness=L.blend_float(g('Roughness'), rough), specular=L.blend_float(g('Specular IOR Level'), spec),
                          normal=L.blend_normal(g('Normal'), normal, fade), mask=mask, parts={'whitened': white, 'scrubbed': scrub, 'dish': dish, 'chips': chips})
