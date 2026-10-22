# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# SOOT (node group WK SOOT, slot A: before the water layer, so water wets it). The old, hard crust of coal smoke on walls, trims, chimneys and roofs (rules G1, G3, G6 in part).
# It is a two-way TONAL PATTERN, not just darkening:
#   * the general film (film_mult) lies on 85 to 100 % of every wall;
#   * where rain cannot reach (Sheltered, and inside window and door reveals) the film is blackest (sheltered_mult), with a crisp line where the shelter ends (edge_sharp);
#   * rain-washed patches (washed_share of the wall: slow noise x exposure x not-shade) are the LIGHT side of the pattern: washed_mult, lifted further above the film by washed_pale (up to 2.5 times the film at 1)
#     so that they read on a dark wall (pale-first: dark soot on a dark wall is crushed by the film, a washed patch is not);
#   * mortar hollows (tx_cavity) carry more soot (soot sits in hollows first), a fine detail that gives way to its average with distance;
#   * the colour is pulled toward grey (grey_pull) and the surface gets a little duller;
#   * NO dot goes below floor_mult of its clean colour (the film's curve crushes anything darker);
#   * chimney stacks and roofs take stack_mult / roof_mult as their film (the object's class, written by apply_walls from the role's own name).
# Sizes: patches are never smaller than patch_min_dots plate dots (through the kit's mark-width helper); the mottling is taller than wide (mottle_stretch).
# It reads only the standard masks by name: sheltered, reveal, shade, tx_cavity, frame_valid. Wall-sheet masks are used only where frame_valid says a sheet applies; chimneys, roofs
# and gable ends get the film and the mottling only.
# Amount 0: every strength is a product with the amount; the film factor is 1 + amount x (factor - 1), so the outputs equal the inputs exactly.
from . import dials_walls
from .walls_common import WallLayer

KEY = 'soot'
GROUP = 'WK SOOT'
MASKS = ['sheltered', 'reveal', 'shade', 'tx_cavity', 'frame_valid']
PARTS = ['washed', 'sheltered', 'factor']
PALE = (0.42, 0.35, 0.26)   # a washed, clean pale stone (albedo): the target the washed patches are lifted toward, wherever the surface is darker than that
PALE_WARM = (0.52, 0.34, 0.19)  # the same stone made warmer (pale_warm = 1): under a blue night sky the plain PALE reads grey-blue, this one reads buff
CAVITY_MEAN = 0.28          # the mean of tx_cavity over the photo materials (their joint share): the average tone the mortar detail fades to


def build(key=KEY):
    dials_walls.register_all()
    L = WallLayer(key, GROUP, masks=MASKS, parts=PARTS)
    g, dial = L.g, L.dial
    fv = g('M Frame Valid')
    fade = g('Fade Near')

    # ---- sizes in plate dots: the mottling is never smaller than a patch of patch_min_dots, measured along the wall
    size_m, size_fade = L.width_dots(dial('mottle_size'), dial('patch_min_dots'), along=True)
    freq_a = L.inv(size_m)
    freq_u = L.div_safe(freq_a, dial('mottle_stretch'))
    slow = L.stretch(L.noise(L.mul(freq_a, 0.8), L.mul(freq_u, 0.8)))
    fine = L.noise(L.mul(freq_a, 2.6), L.mul(freq_u, 2.6), detail=2.0)

    # ---- where rain cannot reach: the shelter picture (flattened a little: the wall sheet's rays band it) and the reveals; crisp or soft by edge_sharp
    shel = L.c01(L.mul(L.mx(L.sstep(g('M Sheltered'), 0.15, 0.95), L.mul(L.sstep(g('M Reveal'), 0.05, 0.6), 0.85)), fv))
    half = L.mad(L.one_minus(dial('edge_sharp')), 0.4, 0.05)
    shel = L.sstep(shel, L.sub(0.5, half), L.add(0.5, half))
    expo = L.mul(L.one_minus(shel), L.mad(g('M Shade'), L.mul(dial('shade_wash'), -1.0), 1.0))

    # ---- rain-washed patches: the light side of the pattern (a field of slow noise raised where the rain reaches, cut at a line that leaves washed_share of the wall)
    is_stack, is_roof = L.object_class()
    wfield = L.mad(L.sub(expo, 0.6), 0.35, slow)
    thr = L.sub(1.0, dial('washed_share'))
    soft = L.mad(L.one_minus(dial('edge_sharp')), 0.2, 0.04)
    washed = L.mul(L.mul(L.sstep(wfield, L.sub(thr, soft), L.add(thr, soft)), L.one_minus(shel)), L.one_minus(is_stack))

    # ---- the film factor (relative to the clean colour)
    wall_film = L.mul(dial('film_mult'), L.role_mult('film_mult'))
    base = L.lerp(is_stack, L.lerp(is_roof, wall_film, dial('roof_mult')), dial('stack_mult'))
    fl = L.lerp(shel, base, L.mul(dial('sheltered_mult'), L.role_mult('sheltered_mult')))
    pale = L.mx(dial('washed_mult'), L.mul(base, L.mad(dial('washed_pale'), 0.6, 1.0)))
    washed_w = L.mul(washed, L.mad(fv, 0.6, 0.4))                      # gables, chimneys and big plain buildings (no wall sheet) get weaker washed patches: no camouflage
    fl = L.lerp(washed_w, fl, pale)
    cavity = L.lerp(fade, CAVITY_MEAN, g('M Tx Cavity'))
    fl = L.mul(fl, L.mad(L.mul(dial('mortar_soot'), 0.5), L.mul(cavity, -1.0), 1.0))
    mot = L.mul(L.sub(fine, 0.5), L.mul(dial('mottle_contrast'), 1.8))
    fl = L.mul(fl, L.mad(mot, L.mul(fade, size_fade), 1.0))
    fl = L.mx(fl, dial('floor_mult'))                                    # nothing darker than the floor of the clean colour

    # ---- colour: grey pull (less in the washed patches), optional last-resort lift, then the film
    colour = L.grey_pull(g('Colour'), L.c01(L.mul(dial('grey_pull'), L.mad(washed, -0.6, 1.0))))
    colour = L.tint(colour, (0.34, 0.27, 0.23), dial('base_lift'))
    warm = dial('pale_warm')
    pale_rgb = L.n.comb_rgb(*(L.mad(warm, PALE_WARM[i] - PALE[i], PALE[i]) for i in range(3)))
    colour = L.lift_to(L.gain(colour, fl), pale_rgb, L.mul(washed_w, L.mul(dial('washed_pale'), 0.9)))

    # ---- a dry crust: duller and less shiny where the film is darker than the surface was
    dark = L.mx(L.sub(1.0, fl), 0.0)
    rough = L.c01(L.mad(L.mul(dial('rough_gain'), 1.0), dark, g('Roughness')))
    spec = L.mul(g('Specular IOR Level'), L.mad(dark, -0.3, 1.0))

    mask = L.mul(L.sstep(washed, 0.4, 0.6), L.gt(L.amount, 1e-4))              # the readable element: the pale washed patches
    return L.finish_layer(colour=L.blend_colour(g('Colour'), colour), roughness=L.blend_float(g('Roughness'), rough), specular=L.blend_float(g('Specular IOR Level'), spec), mask=mask,
                          parts={'washed': washed, 'sheltered': shel, 'factor': L.mul(fl, 0.5)})
