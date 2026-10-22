# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# PAINT (node group WK PAINT, slot A). Worn paint on doors, window frames and fascia boards (rules G5 and C7): the general darkening of old paint (paint_dark), flakes lost along the grain
# (flake_share: bare grey wood, PALE against the dark paint so that it reads), scuffs kicked up from the foot of the surface (door_scuff: bare wood, ragged top), a dark hand-grease patch at
# latch height on one side (latch_grease), and lost gloss (gloss_loss: rougher, less shine). Reads the standard masks height (metres above the ground) and footfall; the position along the
# object and the object's own seed come from the object's own frame, so a door gets its own scuffs and its own latch side.
# Built small (about 70 nodes) and checked for the master dial (amount 0 gives the inputs back exactly) and for isolation; NOT tuned and not measured on the plates (COULD priority).
from . import dials_walls
from .walls_common import WallLayer

KEY = 'paint'
GROUP = 'WK PAINT'
MASKS = ['height', 'footfall']
PARTS = ['flakes', 'scuffs', 'latch']
BARE = (0.30, 0.27, 0.23)          # bare weathered wood, albedo: paler than dark paint
GREASE = (0.03, 0.026, 0.02)


def build(key=KEY):
    dials_walls.register_all()
    L = WallLayer(key, GROUP, masks=MASKS, parts=PARTS)
    g, dial = L.g, L.dial
    fade = g('Fade Near')
    h = L.height_eff(g('M Height'), 0.0)
    along_o, up_o = L.local_frame()

    # ---- flakes along the grain: tall narrow cells of a noise, never narrower than grain_dots
    w_m, w_fade = L.width_dots(0.02, dial('grain_dots'), along=True)
    fa = L.inv(w_m)
    cells = L.stretch(L.noise(fa, L.mul(fa, 0.12), detail=2.0), 3.0)
    thr = L.sub(1.0, L.mul(dial('flake_share'), 0.7))
    flakes = L.mul(L.sstep(cells, thr, L.add(thr, 0.05)), L.mul(fade, w_fade))

    # ---- scuffs kicked up from the foot: bare wood with a ragged top
    rag = L.stretch(L.noise(L.mul(fa, 0.7), 0.0, detail=2.0), 3.0)
    top = L.mul(dial('door_scuff'), L.mad(rag, 0.9, 0.35))
    scuffs = L.mul(L.one_minus(L.sstep(h, L.mul(top, 0.6), top)), L.mad(g('M Footfall'), 0.5, 0.5))

    # ---- a hand-grease patch at latch height on one side of the object
    side = L.mad(L.lt(L.house_rand(0.6), 0.5), 0.64, -0.32)
    oval = L.add(L.mul(L.sstep(L.absv(L.sub(along_o, side)), 0.0, 0.14), 1.0), L.mul(L.sstep(L.absv(L.sub(h, 1.0)), 0.0, 0.18), 1.0))
    latch = L.mul(L.one_minus(L.mn(oval, 1.0)), dial('latch_grease'))

    # ---- colour: darker old paint, bare wood in the flakes and scuffs, grease at the latch
    colour = L.gain(g('Colour'), dial('paint_dark'))
    colour = L.tint(colour, BARE, L.mul(L.mx(flakes, scuffs), 0.9))
    colour = L.tint(colour, GREASE, L.mul(latch, 0.8))
    rough = L.c01(L.mad(dial('gloss_loss'), 0.3, g('Roughness')))
    spec = L.mul(g('Specular IOR Level'), L.mad(dial('gloss_loss'), -0.4, 1.0))

    mask = L.mul(L.sstep(L.mx(flakes, scuffs), 0.4, 0.6), L.gt(L.amount, 1e-4))
    return L.finish_layer(colour=L.blend_colour(g('Colour'), colour), roughness=L.blend_float(g('Roughness'), rough), specular=L.blend_float(g('Specular IOR Level'), spec), mask=mask,
                          parts={'flakes': flakes, 'scuffs': scuffs, 'latch': latch})
