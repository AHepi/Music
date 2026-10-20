# What this does: a fully procedural, seamless (tile-wrapping) RUSTED RIVETED STEEL recipe made only from Blender shader nodes.
# Idea in one sentence: describe the plate layout with a handful of numbers (two vertical straps, two horizontal straps that wrap
# round the tile edge, two diagonal braces), paint a dark blue-grey plate with vertical brush-stroke variation, lay the straps on top
# with a dark outline and a light edge line, put domed rivets in rows along the straps, then wear it all: orange rust that likes
# to sit near strap edges, drip streaks hanging below the rust, small bare-metal chips, and two long scratches.
# Chain, in order:
#   1) plate colour = stretched noise (60 across x 6 up) in hard steps
#   2) bands: |u - centre| - half width  (vertical straps), same on v with wrap-round (horizontal), and distance to a slanted line (braces)
#   3) each band: inside mask, dark outline where the inside distance is tiny, light line a little further in
#   4) rivets: for each row, the distance to the nearest rivet centre in the row (fract of coordinate / spacing); a dome ramp inside the radius
#   5) rust = seamless noise + (distance to the nearest strap edge) so rust gathers at edges; stepped colours; drips = a second stretched noise
#   6) scratches = distance to a line segment, thin;  7) height = brightness of the colour, stretched
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import builder as bd  # noqa: E402

DEFAULT_PARAMETERS = {'seed': 4.0}
V_STRAPS = [(0.0885, 0.0475), (0.583, 0.0505)]               # (centre u, half width)
H_STRAPS = [(0.4625, 0.038), (0.004, 0.060)]                  # (centre v, half width); the second one wraps round the tile edge
BRACES = [((0.1435, 0.952), (0.7217, -0.6925), 0.55, 0.036),   # (start point u, v), direction, length, half width
          ((0.646, 0.450), (0.660, -0.751), 0.53, 0.036)]


def build_node_group(parameters):
    p = {**DEFAULT_PARAMETERS, **parameters}
    b = bd.Builder('Metal recipe', shift=p.get('shift', (0.0, 0.0)))
    u, v = b.uv_xy()

    # ---------------------------------------------------------------- 1) the plate
    plate_noise = b.tnoise(60, 6, detail=4, roughness=0.55, distortion=0.2, seed=p['seed'])
    plate = b.ramp(plate_noise, [(0.0, '#262c33'), (0.35, '#2d343c'), (0.5, '#343c45'), (0.65, '#3b444e'), (0.8, '#454f5a')], 'CONSTANT')
    plate_blotch = b.tnoise(4, 4, detail=4, roughness=0.6, seed=p['seed'] + 1.0)
    plate = b.mix(plate, '#20252b', b.mul(b.maprange(plate_blotch, 0.55, 0.58), 0.7))

    surface_plate = plate
    # ---------------------------------------------------------------- 2) bands: signed distance (negative = inside), in tile units
    bands = []
    for centre, half in V_STRAPS:
        bands.append(b.sub(b.absolute(b.sub(u, centre)), half))
    for centre, half in H_STRAPS:
        dv = b.absolute(b.sub(b.frac(b.add(b.sub(v, centre), 0.5)), 0.5))   # distance to the centre line, wrapping round the tile
        bands.append(b.sub(dv, half))
    diag_parts = []
    for (start, direction, length, half) in BRACES:
        px = b.sub(u, start[0])
        py = b.sub(v, start[1])
        along = b.add(b.mul(px, direction[0]), b.mul(py, direction[1]))
        across = b.sub(b.mul(px, direction[1] * -1.0), b.mul(py, direction[0] * -1.0))       # cross product with the direction
        perp = b.sub(b.absolute(across), half)
        # also limit the length: outside 0..length counts as "outside" (positive distance)
        beyond = b.mx(b.sub(0.0, along), b.sub(along, length))
        d_brace = b.mx(perp, beyond)
        bands.append(d_brace)
        diag_parts.append((along, across))

    # ---------------------------------------------------------------- 3) lay the bands on the plate: draw order braces, horizontal, vertical
    order = [bands[4], bands[5], bands[2], bands[3], bands[0], bands[1]]
    surface = plate
    strap_noise = b.tnoise(50, 5, detail=4, roughness=0.55, seed=p['seed'] + 2.0)
    strap_colour = b.ramp(strap_noise, [(0.0, '#2e353d'), (0.4, '#353d46'), (0.6, '#3d4650'), (0.8, '#47515c')], 'CONSTANT')
    for d in order:
        inside = b.invert(b.window(d, 0.0, 0.0))                                # 1 inside the band
        edge_inside = b.sub(0.0, d)                                              # distance in from the band's edge
        outline = b.mul(inside, b.invert(b.window(edge_inside, 0.0035, 0.0035)))
        highlight = b.mul(b.mul(inside, b.window(edge_inside, 0.0035, 0.0035)), b.invert(b.window(edge_inside, 0.0075, 0.0075)))
        surface = b.mix(surface, strap_colour, inside)
        surface = b.mix(surface, '#59636d', b.mul(highlight, 0.55))
        surface = b.mix(surface, '#0e1114', b.mul(outline, 0.95))
    surface_straps = surface
    # nearest strap edge (absolute distance), used to make rust and chips gather along edges
    near = b.absolute(bands[0])
    for d in bands[1:]:
        near = b.mn(near, b.absolute(d))

    # ---------------------------------------------------------------- 4) rivets
    def rivet_mask(du, dv, radius):
        distance = b.div(b.math('SQRT', b.add(b.mul(du, du), b.mul(dv, dv))), radius)
        inside = b.invert(b.window(distance, 1.0, 1.0))
        # dome: light from the top-left
        lit = b.maprange(b.add(b.mul(du, -0.6), b.mul(dv, 0.8)), -radius, radius)
        dome = b.mix(b.mix('#1d1715', '#4a3b33', b.invert(distance)), '#8a7365', b.mul(b.mul(lit, lit), b.invert(distance)))
        ring = b.mul(inside, b.window(distance, 0.78, 0.80))
        return inside, dome, ring

    def rivet_row_u(v0, phase, spacing, radius):
        du = b.mul(b.sub(b.frac(b.add(b.div(b.sub(u, phase), spacing), 0.5)), 0.5), spacing)
        dv = b.sub(b.frac(b.add(b.sub(v, v0), 0.5)), 0.5)                     # wrapped, so a rivet on the tile edge continues on the other side
        return rivet_mask(du, dv, radius)

    def rivet_row_v(u0, phase, spacing, radius):
        dv = b.mul(b.sub(b.frac(b.add(b.div(b.sub(v, phase), spacing), 0.5)), 0.5), spacing)
        du = b.sub(b.frac(b.add(b.sub(u, u0), 0.5)), 0.5)
        return rivet_mask(du, dv, radius)

    rivet_sets = [rivet_row_v(0.0885, 0.100, 0.125, 0.017), rivet_row_v(0.583, 0.093, 0.125, 0.017),
                  rivet_row_u(0.4625, 0.0877, 0.125, 0.017), rivet_row_u(0.004, 0.18, 0.125, 0.017)]
    for (start, direction, length, half), (along, across) in zip(BRACES, diag_parts):
        spacing = 0.11
        t_local = b.mul(b.sub(b.frac(b.add(b.div(b.sub(along, 0.065), spacing), 0.5)), 0.5), spacing)
        # rebuild du, dv from the along / across coordinates (rotate back)
        rivet_sets.append(rivet_mask(t_local, b.mul(across, -1.0), 0.017))
    brace_limit = [b.invert(b.window(bands[4], 0.0, 0.0)), b.invert(b.window(bands[5], 0.0, 0.0))]
    for index, (inside, dome, ring) in enumerate(rivet_sets):
        if index >= 4:
            inside = b.mul(inside, brace_limit[index - 4])
            ring = b.mul(ring, brace_limit[index - 4])
        # a soft shadow under the rivet: a slightly bigger dark disc is skipped to keep the node count down
        surface = b.mix(surface, dome, inside)
        surface = b.mix(surface, '#0c0a09', b.mul(ring, 0.8))

    surface_rivets = surface
    # ---------------------------------------------------------------- 5) wear: rust, drips, chips
    rust_noise = b.tnoise(6, 6, detail=5, roughness=0.62, distortion=0.5, seed=p['seed'] + 10.0)
    edge_bias = b.mul(b.invert(b.maprange(near, 0.0, 0.05)), 0.06)               # +0.16 right at an edge, 0 far from edges
    rust_value = b.add(rust_noise, edge_bias)
    rust_mask = b.maprange(rust_value, 0.60, 0.615)
    rust_colour = b.ramp(b.tnoise(18, 18, detail=3, roughness=0.6, seed=p['seed'] + 11.0),
                         [(0.0, '#43220f'), (0.4, '#5d2f17'), (0.6, '#78401e'), (0.8, '#8f4f26')], 'CONSTANT')
    brown = b.tnoise(9, 9, detail=4, roughness=0.6, seed=p['seed'] + 15.0)
    surface = b.mix(surface, '#4d3c33', b.mul(b.maprange(brown, 0.50, 0.56), 0.55))        # brown mottling over the plate
    scuff = b.tnoise(16, 16, detail=4, roughness=0.6, seed=p['seed'] + 16.0)
    surface = b.mix(surface, '#5b6064', b.mul(b.maprange(scuff, 0.62, 0.64), 0.55))        # worn paint: grey scuffs
    surface = b.mix(surface, rust_colour, b.mul(rust_mask, 0.95))
    surface_rust = surface
    # drips: thin vertical streaks, only where a coarse noise allows
    drip_fine = b.tnoise(70, 5, detail=3, roughness=0.6, seed=p['seed'] + 12.0)
    drip_gate = b.tnoise(7, 3, detail=3, roughness=0.6, seed=p['seed'] + 13.0)
    drips = b.mul(b.maprange(drip_fine, 0.58, 0.60), b.maprange(drip_gate, 0.55, 0.58))
    surface = b.mix(surface, '#5a2f19', b.mul(drips, 0.85))
    # bare metal chips: small light patches near edges
    chip_noise = b.add(b.tnoise(22, 22, detail=4, roughness=0.6, seed=p['seed'] + 14.0), b.mul(b.invert(b.maprange(near, 0.0, 0.04)), 0.07))
    chips = b.maprange(chip_noise, 0.685, 0.70)
    surface = b.mix(surface, '#7e807e', b.mul(chips, 0.9))

    surface_chips = surface
    # ---------------------------------------------------------------- 6) two long scratches (distance to a line segment)
    for (x0, y0, x1, y1) in [(0.757, 0.742, 0.995, 0.78), (0.18, 0.435, 0.35, 0.318)]:
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy)
        ux, uy = dx / length, dy / length
        px = b.sub(u, x0)
        py = b.sub(v, y0)
        along_s = b.add(b.mul(px, ux), b.mul(py, uy))
        across_s = b.absolute(b.sub(b.mul(px, -uy), b.mul(py, -ux)))
        scratch = b.mul(b.invert(b.window(across_s, 0.0012, 0.0012)), b.mul(b.window(along_s, 0.0, 0.0), b.invert(b.window(along_s, length, length))))
        surface = b.mix(surface, '#8f9396', b.mul(scratch, 0.8))

    if p.get('stage'):
        views = {'1 plate with brush streaks': surface_plate, '2 + straps and braces': surface_straps, '3 + rivets': surface_rivets,
                 '4 + brown, scuffs, rust': surface_rust, '5 + drips, bare-metal chips': surface_chips, '6 + scratches': surface}
        surface = views[p['stage']]
    height = b.maprange(b.height_from_colour(surface), 0.02, 0.50)
    rough = b.mixf(0.55, 0.9, rust_mask)
    metallic = b.mixf(0.9, 0.1, rust_mask)
    return b.finish(surface, height, rough, metallic)
