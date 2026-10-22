# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# WALL GROWTH (node group WK WALL GROWTH, slot C: after the cracks, so a plant lies on the stone and in its cracks). PAINTED moss, algae and lichen on walls, trims, caps, plaster and
# roof tile (rules M2, M4, M5, L1); the 3D tufts and cushions are another part. Method of the slate moss layer (flat painted steps, tall clumps with teeth, a lighter rim), rebuilt on
# the standard masks:
#   * WHERE: moss_site (the habitat field: damp, shaded, near a wall foot; exactly 0 on a trodden lane) x how low on the wall (moss_height), plus below run-off lines (drip_moss), on up-facing
#     tops (cap_moss) and on roofs (roof_moss); algae_site for the thin green-black algae film at pipe outlets and shaded feet; lichen_site for lichen (lichen_amount 0 in a coal-smoke
#     town: nothing is made; a garden look switches it on).
#   * HOW: clumps are taller than wide (clump_stretch) and never smaller than patch_dots plate dots across the wall; the colour is cut into tone_steps FLAT olive tones (no smooth shading);
#     the moss is LIGHTER than the stone it sits on and never below brightness_floor (a painted brightness the film does not crush), saturation 0.45 or more, hue 85 to 120 degrees, so a
#     painter that weakens colour still leaves green. When the surface is wet (Wet Mask, wet_follow) the moss goes darker and richer. A relief on the incoming normal, faded with distance.
#   * LICHEN: pale tan discs with a darker ring, in colonies, lichen_dots across.
# It never invents a place: every strength is multiplied by the habitat fields, so a lane, the crown of a road and a keep-clear place stay clean. Amount 0 gives the inputs back exactly.
from . import dials_walls
from .walls_common import WallLayer, DRIP_REACH_M

KEY = 'wallgrowth'
GROUP = 'WK WALL GROWTH'
MASKS = ['moss_site', 'algae_site', 'lichen_site', 'dampness', 'drip', 'drip_dist', 'height', 'frame_valid']
PARTS = ['moss', 'algae', 'lichen']
ALGAE = (0.08, 0.14, 0.05)
LICHEN = (0.46, 0.42, 0.30)
LICHEN_RING = (0.30, 0.28, 0.20)
ALBEDO_PER_BRIGHTNESS = 0.4       # a painted brightness of 1 corresponds to about this albedo in dim dusk light (used only for the brightness floor)


def build(key=KEY):
    dials_walls.register_all()
    L = WallLayer(key, GROUP, masks=MASKS, parts=PARTS)
    n, g, dial = L.n, L.g, L.dial
    fade = g('Fade Near')
    h = L.height_eff(g('M Height'), g('M Frame Valid'))
    _, nrm, _, _ = L.frame()
    _, _, nz = n.separate(nrm)
    up_facing = L.sstep(nz, 0.6, 0.9)
    _, is_roof = L.object_class()
    wet = L.mul(g('Wet Mask'), dial('wet_follow'))

    # ---- where: the habitat field and the preferences of each kind of place
    low = L.one_minus(L.sstep(h, 0.0, dial('moss_height')))
    below_drip = L.mul(L.sstep(g('M Drip'), 0.4, 0.9), L.one_minus(L.sstep(L.mul(g('M Drip Dist'), DRIP_REACH_M), 0.3, 0.9)))
    prefer = L.add(L.add(low, L.mul(dial('drip_moss'), below_drip)), L.mul(up_facing, L.add(dial('cap_moss'), L.mul(dial('roof_moss'), is_roof))))
    field = L.mul(L.mul(g('M Moss Site'), L.mul(dial('moss_amount'), 2.2)), L.mn(prefer, 1.5))

    # ---- how: tall clumps, never narrower than patch_dots; flat tones
    size_m, size_fade = L.width_dots(0.16, dial('patch_dots'), along=True)
    fa = L.inv(size_m)
    fu = L.div_safe(fa, dial('clump_stretch'))
    clump = L.stretch(L.noise(fa, fu, detail=3.0), 2.6)
    tone_n = L.noise(L.mul(fa, 2.1), L.mul(fu, 2.1), detail=2.0)
    present = L.sstep(L.mad(field, 1.2, L.mul(clump, 0.55)), 0.62, 0.66)
    steps = dial('tone_steps')
    tone = L.n.math('FLOOR', L.mul(L.stretch(tone_n, 2.5), L.sub(steps, 0.001)))
    tone = L.div_safe(tone, L.mx(L.sub(steps, 1.0), 1.0))                          # 0 .. 1 in tone_steps flat steps

    # ---- colour: lighter than the stone, never below the floor, green (hue, saturation), darker and richer when wet
    stone_luma = L.luma(g('Colour'))
    floor_v = L.mul(dial('brightness_floor'), ALBEDO_PER_BRIGHTNESS)
    value = L.mx(L.mx(L.mul(dial('moss_value'), L.mad(tone, 0.5, 0.55)), L.mul(stone_luma, dial('moss_vs_stone'))), floor_v)
    value = L.mul(value, L.mad(wet, -0.25, 1.0))
    hue = L.mul(dial('hue'), 1.0 / 360.0)
    moss_colour = L.hsv_colour(hue, L.mad(wet, 0.1, dial('saturation')), value)
    moss = L.mul(present, fade)
    moss = L.mx(moss, L.mul(present, L.mul(0.35, L.one_minus(fade))))              # far away a thinner, average tone is left (never clean)

    # ---- algae: a thin dull green-black film where it is damp and shaded, at pipe outlets
    algae_f = L.mul(L.mul(g('M Algae Site'), dial('algae_amount')), L.mad(below_drip, 0.6, 0.5))
    algae = L.mul(L.mul(L.sstep(algae_f, 0.12, 0.45), L.mad(clump, 0.6, 0.4)), dial('algae_strength'))

    # ---- lichen: discs with a darker ring, in colonies (a Voronoi cell with a disc in it)
    vor = n.new('ShaderNodeTexVoronoi')
    vor.voronoi_dimensions = '3D'
    vor.feature = 'F1'
    L.tree.links.new(L.coord(L.inv(L.mx(L.mul(g('Dot Along'), dial('lichen_dots')), 0.03)), L.inv(L.mx(L.mul(g('Dot Across'), dial('lichen_dots')), 0.03))), vor.inputs['Vector'])
    vor.inputs['Scale'].default_value = 1.0
    dist = vor.outputs['Distance']
    disc = L.one_minus(L.sstep(dist, 0.28, 0.34))
    ring = L.mul(disc, L.sstep(dist, 0.16, 0.24))
    colony = L.sstep(L.mad(clump, 0.5, L.mul(g('M Lichen Site'), 0.6)), 0.5, 0.7)
    lichen = L.mul(L.mul(L.mul(disc, colony), L.mul(g('M Lichen Site'), dial('lichen_amount'))), L.mul(fade, 1.0))
    lichen = L.c01(L.mul(lichen, 2.0))

    colour = g('Colour')
    colour = L.tint(colour, ALGAE, L.mul(algae, 0.8))
    colour = L.tint(colour, moss_colour, moss)
    colour = L.tint(colour, LICHEN, L.mul(lichen, 0.9))
    colour = L.tint(colour, LICHEN_RING, L.mul(L.mul(lichen, ring), 0.8))

    rough = L.c01(L.mad(L.mx(moss, lichen), 0.14, g('Roughness')))
    normal = L.bump_raw(L.mul(L.mad(tone, 0.5, 0.6), L.mul(moss, dial('relief'))))
    spec = L.mul(g('Specular IOR Level'), L.mad(L.mx(moss, lichen), -0.4, 1.0))

    mask = L.mul(L.mx(L.sstep(moss, 0.4, 0.6), L.sstep(lichen, 0.4, 0.6)), L.gt(L.amount, 1e-4))
    return L.finish_layer(colour=L.blend_colour(g('Colour'), colour), roughness=L.blend_float(g('Roughness'), rough), specular=L.blend_float(g('Specular IOR Level'), spec),
                          normal=L.blend_normal(g('Normal'), normal, fade), mask=mask, parts={'moss': moss, 'algae': algae, 'lichen': lichen})
