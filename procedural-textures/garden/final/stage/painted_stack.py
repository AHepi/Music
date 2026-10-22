# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# PART C of the surfaces stage: the PAINTED look (look = 'painted'). No scans, no weathering kit. It follows the add-on's own painted rules and the person's recorded words:
#   * colour is laid in a FEW BROAD PASSAGES per surface (four to six unequal, directional groups, quiet middles, some firm edges and some lost ones), warm where the low sun
#     lights it against cool shadow colours: never round camouflage islands, never giant clean polygon bands, never all-over grit
#   * stone keeps the add-on's own painted stone shader ('FOUNDRY / Wet Stone') but is retuned: chalky pale fields, SHORT mineral marks, matte, no long streaks
#   * wood: board-directed grain and interrupted lengthwise wear (never all-over streaking); plaster: held and lost edges with directional drip tails
#   * the roofs and timbers that already use the add-on's painted shaders are lifted out of the crushed-black zone
# Everything here is material nodes (no geometry). Surfaces nobody asked about (bark, pebbles, moss tones, leaves, water, glow) are not touched.
# The add-on's pigment tool (apply_pigment) is NOT called by default: it refuses the add-on's own planks, stones and roof (modifiers) and colours one slot per object;
# stage_surfaces.apply({'look': 'painted', 'addon_dir': '<0.2.1 folder>'}) uses it on hall posts, beams, shoji bars and hall plaster when the folder is given (see apply_pigment_tool).
import bpy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import surf_kit as K  # noqa: E402


# ------------------------------------------------------------------------------------------------------------------------------ passages
def passages(S, stretch, noise_scale, stops, soft=0.8, seed_shift=0.0, detail=2.0, distortion=0.6, spread=(0.28, 0.72)):
    """Colour from a stretched noise cut into flat passages. stretch = (sx, sy, sz): coordinates are multiplied by it before the noise (small = long along that axis).
    stops: [(position, (r, g, b))] ascending, first at 0: constant steps of UNEQUAL width. Part of the edges are firm (the constant ramp) and part are lost (the soft ramp):
    soft = how much of the soft ramp the 'lost edge' noise may bring in."""
    b = S.b
    px, py, pz = b.sep(S.pos)
    st = b.comb(b.math('ADD', b.math('MULTIPLY', px, stretch[0]), seed_shift), b.math('MULTIPLY', py, stretch[1]), b.math('MULTIPLY', pz, stretch[2]))
    n = b.noise(st, noise_scale, detail=detail, rough=0.5, distortion=distortion)
    n = b.maprange(n, spread[0], spread[1], 0.0, 1.0)
    firm = b.ramp(n, stops, 'CONSTANT', 'firm edges')
    lost = b.ramp(n, stops, 'LINEAR', 'lost edges')
    k = b.smooth(b.noise(b.vmath('ADD', b.vmath('SCALE', S.pos, scale=0.7), (13.0, 7.0, 3.0)), 1.0, detail=2.0), 0.42, 0.62)
    return b.mixc(b.math('MULTIPLY', k, soft), firm, lost)


def quiet_grain(S, color, scale=40.0, amount=0.035):
    """A very faint fine variation so a flat passage is not a perfectly flat colour (+-amount)."""
    b = S.b
    n = b.noise(S.pos, scale, detail=2.0)
    f = b.maprange(n, 0.35, 0.65, 1.0 - amount, 1.0 + amount)
    return b.vmath('SCALE', color, scale=f)


def simple(S, color, rough, bump=None, spec=0.4):
    return S.finish(color, rough, bump[0] if bump else None, bump=(bump[1], bump[2]) if bump else (0.0, 0.0), spec=spec)


# ------------------------------------------------------------------------------------------------------------------------------ builders
def paint_ground(mat, opt, ctx):
    S = K.Surface(mat, 'ground')
    b = S.b
    col = passages(S, (0.45, 1.0, 3.0), 0.30, [
        (0.0, (0.034, 0.070, 0.028)),     # deep moss green (shadow side)
        (0.17, (0.046, 0.080, 0.058)),    # cool green-teal shadow (kept light enough not to read as water)
        (0.36, (0.072, 0.112, 0.030)),    # olive, the main field
        (0.62, (0.125, 0.095, 0.045)),    # warm ochre-brown where the sun lies
        (0.80, (0.120, 0.178, 0.052)),    # pale warm green, a small lit passage
    ], soft=0.8, distortion=0.8)
    col = quiet_grain(S, col, 14.0, 0.05)
    noise = b.noise(S.pos, 9.0, detail=2.0)
    S.finish(col, 0.95, noise, bump=(0.12, 0.02), spec=0.3)


def paint_gravel(mat, opt, ctx):
    S = K.Surface(mat, 'gravel')
    col = passages(S, (0.5, 0.9, 3.0), 0.55, [
        (0.0, (0.43, 0.44, 0.44)),        # cool pale grey
        (0.30, (0.50, 0.48, 0.44)),       # neutral pale
        (0.58, (0.57, 0.545, 0.49)),      # warm lit pale
        (0.84, (0.46, 0.455, 0.43)),
    ], soft=0.6, distortion=0.5)
    col = quiet_grain(S, col, 160.0, 0.03)
    S.finish(col, 0.9, S.b.noise(S.pos, 180.0, detail=3.0), bump=(0.2, 0.003), spec=0.3)


def paint_plaster(mat, opt, ctx):
    fam = ctx.get('family', 'wall.hall')
    S = K.Surface(mat, mat.name)
    b = S.b
    if fam == 'wall.garden':
        stops = [(0.0, (0.44, 0.39, 0.31)), (0.34, (0.52, 0.46, 0.37)), (0.60, (0.40, 0.37, 0.31)), (0.82, (0.55, 0.50, 0.41))]
    else:
        stops = [(0.0, (0.64, 0.60, 0.53)), (0.38, (0.70, 0.66, 0.58)), (0.62, (0.58, 0.55, 0.50)), (0.86, (0.74, 0.70, 0.62))]
    # directional tails: coordinates stretched UP the wall (small z scale) so the passages run like drips from the eaves
    col = passages(S, (1.0, 1.0, 0.22), 0.8, stops, soft=0.75, distortion=0.4)
    col = quiet_grain(S, col, 25.0, 0.02)
    S.finish(col, 0.95, b.noise(S.pos, 30.0, detail=3.0), bump=(0.08, 0.01), spec=0.25)


def paint_timber(mat, opt, ctx):
    fam = ctx.get('family', 'timber.post')
    S = K.Surface(mat, mat.name)
    b = S.b
    # board-directed grain: posts run up (z), beams run along x
    stretch = (1.0, 1.0, 0.12) if fam == 'timber.post' else (0.12, 1.0, 1.0)
    col = passages(S, stretch, 3.2, [
        (0.0, (0.042, 0.028, 0.019)), (0.28, (0.075, 0.048, 0.030)), (0.55, (0.105, 0.066, 0.036)), (0.80, (0.060, 0.040, 0.026))], soft=0.35, distortion=0.2, detail=3.0)
    # interrupted lengthwise wear: short pale streaks
    px, py, pz = b.sep(S.pos)
    st = b.comb(b.math('MULTIPLY', px, stretch[0] * 0.35 + 0.65 * (1.0 if stretch[0] > 0.5 else 0.2)), b.math('MULTIPLY', py, 1.0), b.math('MULTIPLY', pz, 0.2 if fam == 'timber.post' else 1.0))
    wear = b.smooth(b.noise(st, 14.0, detail=2.0), 0.58, 0.68)
    col = b.mixc(b.math('MULTIPLY', wear, 0.55), col, (0.17, 0.115, 0.07))
    S.finish(col, 0.82, b.noise(S.pos, 20.0, detail=2.0), bump=(0.1, 0.006), spec=0.3)


def paint_plank(mat, opt, ctx):
    run = ctx.get('run', 0)
    base = ctx.get('orig_rgb', (0.15, 0.1, 0.07))
    S = K.Surface(mat, mat.name)
    b = S.b
    if run <= 2:
        tone = (base[0] * 0.95, base[1] * 1.02, base[2] * 1.0)               # amber-brown, a touch less red than the salmon of the original
    else:
        grey = 0.2126 * base[0] + 0.7152 * base[1] + 0.0722 * base[2]
        tone = tuple(0.45 * c + 0.55 * grey * 1.25 for c in base)            # bridge boards: silver-brown
    # interrupted wear running along each board (boards run along x): long thin streaks, broken
    px, py, pz = b.sep(S.pos)
    off = b.math('MULTIPLY', S.rand, 20.0)
    st = b.comb(b.math('MULTIPLY', px, 0.10), b.math('ADD', b.math('MULTIPLY', py, 1.0), off), b.math('MULTIPLY', pz, 1.0))
    wear = b.smooth(b.noise(st, 11.0, detail=2.0), 0.55, 0.68)
    grain = b.maprange(b.noise(b.comb(b.math('MULTIPLY', px, 0.15), b.math('MULTIPLY', py, 1.0), 0.0), 26.0, detail=1.0), 0.3, 0.7, 0.86, 1.08)
    col = b.vmath('SCALE', b.rgb(tone), scale=grain)
    pale = tuple(min(1.0, c * 1.55 + 0.01) for c in tone)
    col = b.mixc(b.math('MULTIPLY', wear, 0.6), col, pale)
    S.finish(col, 0.8, None, spec=0.3)


FOUNDRY = {
    # kind: (Base, Shadow, Highlight, Scale, Variation, Roughness, Bump, Wear, Wetness, Stroke Length, Stroke Width)
    'rock': ((0.205, 0.205, 0.185, 1), (0.045, 0.058, 0.072, 1), (0.36, 0.34, 0.285, 1), 2.6, 0.38, 0.86, 0.1, 0.20, 0.04, 0.26, 0.09),
    'pier': ((0.135, 0.145, 0.135, 1), (0.030, 0.045, 0.058, 1), (0.26, 0.25, 0.21, 1), 2.6, 0.38, 0.80, 0.1, 0.20, 0.12, 0.26, 0.09),
    'step': ((0.225, 0.215, 0.195, 1), (0.055, 0.064, 0.075, 1), (0.38, 0.35, 0.29, 1), 2.4, 0.34, 0.86, 0.1, 0.24, 0.04, 0.24, 0.08),
    'lantern': ((0.185, 0.18, 0.165, 1), (0.045, 0.055, 0.068, 1), (0.34, 0.32, 0.27, 1), 2.4, 0.34, 0.84, 0.1, 0.22, 0.04, 0.24, 0.08),
    'roof.tile': ((0.052, 0.064, 0.078, 1), (0.020, 0.027, 0.036, 1), (0.17, 0.20, 0.22, 1), 3.0, 0.5, 0.70, 0.1, 0.12, 0.0, 0.35, 0.08),
}
FOUNDRY_NAMES = ('Base', 'Shadow', 'Highlight', 'Scale', 'Variation', 'Roughness', 'Bump', 'Wear', 'Wetness', 'Stroke Length', 'Stroke Width')


def foundry_node(mat):
    if mat.node_tree is None:
        return None
    for n in mat.node_tree.nodes:
        if n.bl_idname == 'ShaderNodeGroup' and n.node_tree and n.node_tree.name.startswith('FOUNDRY'):
            return n
    return None


def retune_foundry(mat, kind, jitter=0.0):
    node = foundry_node(mat)
    if node is None:
        return False
    for name, value in zip(FOUNDRY_NAMES, FOUNDRY[kind]):
        sock = node.inputs.get(name)
        if sock is None:
            continue
        if name == 'Base' and jitter:
            value = tuple(min(1.0, v * (1.0 + jitter)) for v in value[:3]) + (1,)
        sock.default_value = value
    return True


def paint_stone(mat, opt, ctx):
    kind = ctx.get('kind', 'rock')
    jitter = (K.seed_hash(mat.name) - 0.5) * 0.24
    if retune_foundry(mat, kind, jitter):
        return
    paint_stone_new(mat, opt, ctx)


def paint_stone_new(mat, opt, ctx):
    """For a stone that has no painted-stone shader yet (a new object from another builder): chalky pale fields in a few unequal planes and short dark mineral marks."""
    kind = ctx.get('kind', 'rock')
    base = {'rock': 0.205, 'pier': 0.14, 'step': 0.22, 'lantern': 0.185}[kind]
    S = K.Surface(mat, mat.name)
    b = S.b
    col = passages(S, (1.0, 1.0, 1.6), 1.6, [
        (0.0, (base * 0.80, base * 0.84, base * 0.86)), (0.3, (base * 1.0, base * 1.0, base * 0.95)), (0.58, (base * 1.22, base * 1.18, base * 1.06)), (0.82, (base * 0.92, base * 0.92, base * 0.90))],
        soft=0.5, distortion=0.4)
    px, py, pz = b.sep(S.pos)
    marks = b.smooth(b.noise(b.comb(b.math('MULTIPLY', px, 1.0), b.math('MULTIPLY', py, 1.0), b.math('MULTIPLY', pz, 2.2)), 16.0, detail=2.0), 0.64, 0.72)
    col = b.mixc(b.math('MULTIPLY', marks, 0.55), col, (base * 0.45, base * 0.45, base * 0.48))
    S.finish(col, 0.86, b.noise(S.pos, 12.0, detail=2.0), bump=(0.15, 0.01), spec=0.3)


def paint_plinth(mat, opt, ctx):
    tree = mat.node_tree
    for n in tree.nodes:
        if n.bl_idname == 'ShaderNodeValToRGB':
            els = n.color_ramp.elements
            els[0].color = (0.13, 0.125, 0.115, 1)
            els[-1].color = (0.30, 0.285, 0.25, 1)
    return True


def paint_roof(mat, opt, ctx):
    part = ctx.get('part', 'roof.tile')
    if part == 'roof.deck':
        node = foundry_node(mat)
        if node is not None:
            node.inputs['Base'].default_value = (0.05, 0.04, 0.03, 1)
            node.inputs['Shadow'].default_value = (0.016, 0.02, 0.028, 1)
            node.inputs['Highlight'].default_value = (0.17, 0.105, 0.05, 1)
        return
    retune_foundry(mat, 'roof.tile', jitter=0.0 if part == 'roof.tile' else -0.1)


def paint_cap(mat, opt, ctx):
    tree = mat.node_tree
    for n in tree.nodes:
        if n.bl_idname == 'ShaderNodeBsdfPrincipled':
            n.inputs['Base Color'].default_value = (0.05, 0.056, 0.066, 1)
            n.inputs['Roughness'].default_value = 0.55


def paint_leave(mat, opt, ctx):
    """Bark, pebbles: the add-on's own painted materials stay."""
    return


PAINTED_BUILDERS = {
    'ground.earth': paint_ground, 'ground.gravel': paint_gravel, 'wall.hall': paint_plaster, 'wall.garden': paint_plaster, 'timber.post': paint_timber,
    'timber.beam': paint_timber, 'plank': paint_plank, 'stone.rock': paint_stone, 'stone.pier': paint_stone, 'stone.step': paint_stone, 'stone.lantern': paint_stone,
    'stone.plinth': paint_plinth, 'roof': paint_roof, 'roof.tile': paint_roof, 'roof.ridge': paint_roof, 'roof.deck': paint_roof, 'wall.cap': paint_cap,
    'bark.maple': paint_leave, 'bark.pine': paint_leave, 'pebbles': paint_leave,
}
