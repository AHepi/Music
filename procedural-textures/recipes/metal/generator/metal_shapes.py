# What this does (plain words): turns a "metal plate description" (a short list of numbers: where the straps, braces, rivets and seam lines are,
# what colour each is, how each strap edge is shaded, and a list of rust / chip patches) into an ORDERED STACK OF FLAT SHAPES, painted from the back
# to the front like a painter would. It is the "what goes where" half of the metal generator; metal_generator.py is the Blender half that turns
# the stack into real geometry and photographs it from straight above. It never opens a reference picture, only the description.
# numpy only, so it runs both inside Blender and outside it (the fitting scripts use it with OpenCV to paint a quick preview).
#
# One shape = a dict:
#   points  (N x 2 array, tile dots, x to the right, y DOWN the picture like the reference)
#   colours (N x 3 array, screen colours 0..255, one per corner: the colour changes smoothly across the shape between the corners)
#   kind    what made it: 'plate' 'panel' 'face' 'edge' 'seam' 'rivet' 'patch' 'scratch'
#   base    1 when the shape is bare steel that procedural rust may be laid over (plate, panel, strap face), else 0
#   rough / metal  roughness and metallic numbers (0..1) for the other maps
# Everything is also drawn one tile over in every direction, so whatever crosses a tile edge comes back on the other side (seamless tile).
#
# What a description holds (all optional except tile; see description/ for real examples):
#   tile            1254 (dots; a bigger area uses a bigger number: the whole description just scales its tile)
#   plate           [r,g,b] the bare plate colour; plate_panels: [[x0,y0,x1,y1,[r,g,b]], ...] panels of a slightly different tone
#   profiles        {name: [[d, r, g, b], ...]}  how a strap edge is shaded: d = dots OUTWARD from the edge crease (negative = onto the strap)
#   bands           straps, braces, seam lines: oriented bars.  {centre:[x,y], angle, length, half (crease to centre), face:[r,g,b],
#                   a, b (names of the profile on each side; side a is the side the normal (sin angle, -cos angle) points to),
#                   inner_a, inner_b (how far into the strap each profile reaches), clip:[x0,y0,x1,y1] or null, kind}
#   rivet           {radius, rings:[r1,r2,...] (fractions of radius), cells:[[r,g,b] x sectors, per ring]}   rivets: [[x,y], ...]
#   patches         [[kind, colour_index, ...]]  see build_patch_shapes
#   rust_palette    colours used by patches
import math

import numpy as np

TILE = 1254.0
EDGE_BIAS_WIDTH = 14.0      # dots from a strap edge crease over which procedural rust is drawn towards the edge


def srgb_array(values):
    return np.asarray(values, dtype=np.float64)


# ----------------------------------------------------------------------------------------------------------------------- small geometry
def clip_polygon_halfplane(points, colours, axis, limit, keep_greater):
    """Sutherland-Hodgman cut of one polygon (with its corner colours) by the line axis = limit. Keeps the side where value >= limit (keep_greater) or <= limit."""
    out_p, out_c = [], []
    n = len(points)
    for i in range(n):
        p, q = points[i], points[(i + 1) % n]
        cp_, cq = colours[i], colours[(i + 1) % n]
        pin = (p[axis] >= limit) if keep_greater else (p[axis] <= limit)
        qin = (q[axis] >= limit) if keep_greater else (q[axis] <= limit)
        if pin:
            out_p.append(p)
            out_c.append(cp_)
        if pin != qin:
            t = (limit - p[axis]) / (q[axis] - p[axis])
            out_p.append(p + t * (q - p))
            out_c.append(cp_ + t * (cq - cp_))
    if len(out_p) < 3:
        return None, None
    return np.array(out_p), np.array(out_c)


def clip_to_box(points, colours, box):
    x0, y0, x1, y1 = box
    for axis, limit, greater in ((0, x0, True), (0, x1, False), (1, y0, True), (1, y1, False)):
        if points is None:
            return None, None
        if limit is None:
            continue
        points, colours = clip_polygon_halfplane(points, colours, axis, limit, greater)
    return points, colours


# ----------------------------------------------------------------------------------------------------------------------- bands (straps, braces, seams)
def band_shapes(band, profiles, kind_default='face'):
    """Shapes for one oriented bar, back to front: the two edge strips (each made of small gradient quads) then the face.
    Local frame: d = (cos angle, sin angle) along the bar, n = (sin angle, -cos angle) across it (side a is +n)."""
    angle = math.radians(band['angle'])
    d = np.array([math.cos(angle), math.sin(angle)])
    n = np.array([math.sin(angle), -math.cos(angle)])
    cx, cy = band['centre']
    centre = np.array([cx, cy], float)
    half_len = band['length'] / 2.0
    half = band['half']                                    # crease-to-centre distance (the footprint half width)
    face = np.array(band['face'], float)
    shapes = []
    names = (band.get('a'), band.get('b'))
    inner = (band.get('inner_a'), band.get('inner_b'))
    sides = []
    for sign, name, inner_reach in ((1.0, names[0], inner[0]), (-1.0, names[1], inner[1])):
        if name is None or name not in profiles:
            sides.append((sign, None, 0.0))
            continue
        table = np.array(profiles[name], float)             # columns: d, r, g, b ; d ascending from inside (negative) to outside
        reach = -table[0, 0] if inner_reach is None else inner_reach
        sides.append((sign, table, reach))

    def corner(offset_across, along):
        return centre + n * offset_across + d * along

    def make_quad(o0, c0, o1, c1):
        pts = np.array([corner(o0, -half_len), corner(o0, half_len), corner(o1, half_len), corner(o1, -half_len)])
        cols = np.array([c0, c0, c1, c1], float)
        return pts, cols

    face_edges = []
    for sign, table, reach in sides:
        if table is None:
            face_edges.append(sign * half)
            continue
        face_edges.append(sign * (half - reach))
        # strip quads between consecutive table points (inside to outside)
        ds = table[:, 0]
        keep = ds >= -reach - 1e-9
        t = table[keep]
        if (~keep).any():
            # interpolate the first kept point exactly at -reach
            last_out = np.where(~keep)[0][-1]
            frac = (-reach - table[last_out, 0]) / (table[last_out + 1, 0] - table[last_out, 0])
            first = table[last_out] + frac * (table[last_out + 1] - table[last_out])
            first[0] = -reach
            t = np.vstack([first[None, :], t])
        for i in range(len(t) - 1):
            o0 = sign * (half + t[i, 0])
            o1 = sign * (half + t[i + 1, 0])
            pts, cols = make_quad(o0, t[i, 1:4], o1, t[i + 1, 1:4])
            bias = lambda dd: max(0.0, 1.0 - abs(dd) / EDGE_BIAS_WIDTH)
            aux = np.array([bias(t[i, 0]), bias(t[i, 0]), bias(t[i + 1, 0]), bias(t[i + 1, 0])])
            shapes.append({'points': pts, 'colours': cols, 'kind': 'edge', 'base': 0, 'aux': aux, 'convex': True})
    # the face: between the two inner edges
    low, high = sorted(face_edges)
    if high - low > 0.05:
        pts, cols = make_quad(low, face, high, face)
        shapes.append({'points': pts, 'colours': cols, 'kind': band.get('kind', kind_default), 'base': 1 if band.get('kind', kind_default) in ('face', 'panel') else 0, 'convex': True})
    return shapes


# ----------------------------------------------------------------------------------------------------------------------- rivets
def rivet_shapes(rivet, positions):
    """Every rivet is a small disc cut into rings and sectors, each cell its own colour (the domed, faceted look), drawn the same way for all rivets."""
    radius = rivet['radius']
    rings = [0.0] + list(rivet['rings'])
    cells = np.array(rivet['cells'], float)               # (ring, sector, 3)
    sectors = cells.shape[1]
    base_angle = math.radians(rivet.get('first_sector_angle', 0.0))
    shapes = []
    for (x, y) in positions:
        for ring in range(len(rings) - 1):
            r0, r1 = rings[ring] * radius, rings[ring + 1] * radius
            for s in range(sectors):
                a0 = base_angle + 2 * math.pi * s / sectors
                a1 = base_angle + 2 * math.pi * (s + 1) / sectors
                # a few points along each arc so the ring looks round, not like a polygon
                steps = max(2, int(round(8.0 / sectors * 3)))
                arc = np.linspace(a0, a1, steps + 1)
                outer = np.stack([x + r1 * np.cos(arc), y + r1 * np.sin(arc)], axis=1)
                if r0 <= 0:
                    pts = np.vstack([[x, y], outer])
                else:
                    inner = np.stack([x + r0 * np.cos(arc[::-1]), y + r0 * np.sin(arc[::-1])], axis=1)
                    pts = np.vstack([outer, inner])
                colour = cells[ring, s]
                aux = np.full(len(pts), 0.9 if ring == len(rings) - 2 else 0.0)       # the outer (shadow) ring attracts rust
                shapes.append({'points': pts, 'colours': np.tile(colour, (len(pts), 1)), 'kind': 'rivet', 'base': 0, 'convex': r0 <= 0, 'aux': aux})
    return shapes


# ----------------------------------------------------------------------------------------------------------------------- patches (rust, chips, scratches)
def smooth_ring_noise(count, rng):
    knots = rng.uniform(-1.0, 1.0, count)

    def value(t):
        position = (np.asarray(t) % 1.0) * count
        i0 = np.floor(position).astype(int) % count
        i1 = (i0 + 1) % count
        f = position - np.floor(position)
        f = f * f * (3.0 - 2.0 * f)
        return knots[i0] * (1 - f) + knots[i1] * f
    return value


def blob_polygon(cx, cy, rx, ry, angle_deg, ragged, seed, points=24):
    """A ragged ellipse: an ellipse whose radius wobbles smoothly (the wobble is fixed by the seed, so the same description always gives the same patch)."""
    rng = np.random.default_rng(int(seed))
    wobble = smooth_ring_noise(7, rng)
    wobble2 = smooth_ring_noise(13, rng)
    t = np.arange(points) / points
    a = 2 * np.pi * t
    k = 1.0 + ragged * (0.6 * wobble(t) + 0.4 * wobble2(t))
    k = np.clip(k, 0.25, 2.0)
    ex, ey = rx * k * np.cos(a), ry * k * np.sin(a)
    th = math.radians(angle_deg)
    x = cx + ex * math.cos(th) - ey * math.sin(th)
    y = cy + ex * math.sin(th) + ey * math.cos(th)
    return np.stack([x, y], axis=1)


def drip_polygon(x, y, length, width, taper, seed, wobble_amount=0.25):
    """A rust drip: a narrow streak that starts at (x, y), runs DOWN the picture, narrows to a point and wobbles a little sideways."""
    rng = np.random.default_rng(int(seed))
    wobble = smooth_ring_noise(5, rng)
    n = 10
    ts = np.linspace(0, 1, n)
    widths = width * (1.0 - taper * ts) * (1 + 0.3 * wobble(ts * 0.5))
    sway = wobble_amount * width * np.cumsum(rng.uniform(-1, 1, n)) / 3.0
    left = np.stack([x + sway - widths / 2, y + ts * length], axis=1)
    right = np.stack([x + sway + widths / 2, y + ts * length], axis=1)
    return np.vstack([left, right[::-1]])


def grow_outline(points, distance):
    """Move every corner of a closed outline outward by `distance` dots (mitre joins, limited). Used so that a traced outline that runs through the CENTRES of
    the outermost dots fills those dots completely (a paint program fills them; an exact-area renderer would only fill half of each)."""
    p = np.asarray(points, float)
    n = len(p)
    area = 0.5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1])
    sign = 1.0 if area > 0 else -1.0
    nxt = np.roll(p, -1, axis=0)
    edge = nxt - p
    length = np.hypot(edge[:, 0], edge[:, 1])
    length[length == 0] = 1.0
    normal = sign * np.stack([edge[:, 1], -edge[:, 0]], axis=1) / length[:, None]      # outward normal of the edge that starts at each corner
    previous = np.roll(normal, 1, axis=0)
    bisector = normal + previous
    denominator = 1.0 + np.sum(normal * previous, axis=1)
    factor = np.where(denominator > 0.4, 1.0 / np.maximum(denominator, 1e-6), 2.5)
    return p + distance * bisector * factor[:, None]


def region_shapes(regions, colours):
    """Traced regions (the 'tracing the picture' layer): each is [colour index, x0, y0, dx1, dy1, dx2, dy2, ...] with steps in whole dots; the outline closes by itself."""
    shapes = []
    flat = []
    for item in regions:                       # the list may be stored in chunks of 60 outlines (chunk = a list of outlines); painted in the order written
        if item and isinstance(item[0], list):
            flat.extend(item)
        else:
            flat.append(item)
    for p in flat:
        steps = np.array(p[3:], float).reshape(-1, 2)
        pts = np.array([p[1], p[2]], float) + np.vstack([[0, 0], np.cumsum(steps, axis=0)])
        if len(pts) < 3:
            continue
        pts = grow_outline(pts, 0.5)          # the outline runs through dot centres: grow it by half a dot so that it holds the whole outer dots
        shapes.append({'points': pts, 'colours': np.tile(np.asarray(colours[int(p[0])], float), (len(pts), 1)), 'kind': 'patch', 'base': 0, 'convex': False, 'fan': False})
    return shapes


def patch_shapes(patches, colours):
    """patches: list of lists. First item = kind.
       ['b', colour, cx, cy, rx, ry, angle, ragged, seed]                 ragged ellipse
       ['d', colour, x, y, length, width, taper, seed]                    drip
       ['r', colour, x0, y0, dx1, dy1, dx2, dy2, ...]                     traced region: start point then steps (in half dots)
       ['l', colour, x0, y0, x1, y1, width]                               straight line (scratch)
       The colour is an index into the colour list (screen colours 0..255)."""
    shapes = []
    for p in patches:
        kind, colour = p[0], colours[int(p[1])]
        fan = False
        if kind == 'b':
            ring = blob_polygon(*p[2:9])
            pts = np.vstack([[p[2], p[3]], ring])
            fan = True
        elif kind == 'd':
            pts = drip_polygon(*p[2:8])
        elif kind == 'r':
            steps = np.array(p[4:], float).reshape(-1, 2) * 0.5
            start = np.array([p[2], p[3]], float)
            pts = start + np.vstack([[0, 0], np.cumsum(steps, axis=0)])
        elif kind == 'l':
            x0, y0, x1, y1, w = p[2:7]
            dv = np.array([x1 - x0, y1 - y0], float)
            ln = np.hypot(*dv)
            nrm = np.array([-dv[1], dv[0]]) / max(ln, 1e-9) * w / 2
            pts = np.array([[x0, y0] - nrm, [x1, y1] - nrm, [x1, y1] + nrm, [x0, y0] + nrm])
        else:
            continue
        if len(pts) < 3:
            continue
        shapes.append({'points': np.asarray(pts, float), 'colours': np.tile(np.asarray(colour, float), (len(pts), 1)), 'kind': 'scratch' if kind == 'l' else 'patch', 'base': 0, 'convex': kind in ('l',), 'fan': fan})
    return shapes


# ----------------------------------------------------------------------------------------------------------------------- the whole stack
def shift_shape(shape, dx, dy):
    new = dict(shape)
    new['points'] = shape['points'] + np.array([dx, dy])
    return new


def on_screen(points, tile, margin=-0.25):
    return not (points[:, 0].max() < -margin or points[:, 0].min() > tile + margin or points[:, 1].max() < -margin or points[:, 1].min() > tile + margin)


def wrap_copies(shapes, tile, shift=(0.0, 0.0)):
    """Every shape drawn at every tile offset that touches the picture (so things leaving one edge come in at the other). `shift` moves the whole painting first."""
    out = []
    for s in shapes:
        base = s['points'] + np.array(shift)
        lo, hi = base.min(axis=0), base.max(axis=0)
        i0, i1 = int(math.floor((-2.0 - hi[0]) / tile)) + 1, int(math.floor((tile + 2.0 - lo[0]) / tile))
        j0, j1 = int(math.floor((-2.0 - hi[1]) / tile)) + 1, int(math.floor((tile + 2.0 - lo[1]) / tile))
        for j in range(min(j0, 0), max(j1, 0) + 1):
            for i in range(min(i0, 0), max(i1, 0) + 1):
                moved = base + np.array([i * tile, j * tile])
                if not on_screen(moved, tile):
                    continue
                new = dict(s)
                new['points'] = moved
                out.append(new)
    return out


def build_layout_shapes(description):
    """Plate, panels, seams, braces, straps (in their `order`) and rivets: everything that is not wear."""
    tile = float(description.get('tile', TILE))
    shapes = []
    plate = np.array(description['plate'], float)
    full = np.array([[0, 0], [tile, 0], [tile, tile], [0, tile]], float)
    shapes.append({'points': full, 'colours': np.tile(plate, (4, 1)), 'kind': 'plate', 'base': 1, 'convex': True})
    for x0, y0, x1, y1, colour in description.get('plate_panels', []):
        shapes.append({'points': np.array([[x0, y0], [x1, y0], [x1, y1], [x0, y1]], float), 'colours': np.tile(np.array(colour, float), (4, 1)), 'kind': 'panel', 'base': 1, 'convex': True})
    profiles = description.get('profiles', {})
    bands = sorted(description.get('bands', []), key=lambda b: b.get('order', 0))
    for band in bands:
        for s in band_shapes(band, profiles):
            clip = band.get('clip')
            if clip:
                pts, cols = clip_to_box(s['points'], s['colours'], clip)
                if pts is None:
                    continue
                s = dict(s, points=pts, colours=cols)
                if 'aux' in s:                       # clipping can change the number of corners: keep one edge-attraction number per corner
                    s['aux'] = np.full(len(pts), float(np.mean(s['aux'])))
            shapes.append(s)
    if 'rivet' in description:
        shapes.extend(rivet_shapes(description['rivet'], description.get('rivets', [])))
    return shapes


DOT_CENTRE = 0.5      # coordinates in a description are DOT NUMBERS (dot i is the i-th dot counting from 0, its centre is the number i); the picture itself spans 0..tile


def build_stack(description, wrap=True, shift=(0.0, 0.0), include_patches=True):
    tile = float(description.get('tile', TILE))
    layout = [dict(s, points=s['points'] + DOT_CENTRE) for s in build_layout_shapes(description)]
    stack = wrap_copies(layout, tile, shift) if wrap else layout
    if include_patches and description.get('patches'):
        patches = [dict(s, points=s['points'] + DOT_CENTRE) for s in patch_shapes(description['patches'], description['patch_colours'])]
        stack += wrap_copies(patches, tile, shift) if wrap else patches
    if include_patches and description.get('regions'):
        regions = [dict(s, points=s['points'] + DOT_CENTRE) for s in region_shapes(description['regions'], description['patch_colours'])]
        stack += wrap_copies(regions, tile, shift) if wrap else regions
    return stack


# ----------------------------------------------------------------------------------------------------------------------- filling any outline with triangles
def slab_triangles(points):
    """Fill a closed outline (even-odd rule, like a paint program) with triangles, by cutting it into horizontal slabs between neighbouring corner heights;
    inside each slab the outline is a set of straight edges that do not cross, paired left to right into trapezoids. Works for concave outlines and for
    outlines that touch themselves at a corner (which Blender's own tessellate tool mis-fills). Returns (new points M x 2, triangles as index triples)."""
    p = np.asarray(points, float)
    n = len(p)
    a, b = p, np.roll(p, -1, axis=0)
    keep = a[:, 1] != b[:, 1]
    a, b = a[keep], b[keep]
    flip = a[:, 1] > b[:, 1]
    top = np.where(flip[:, None], b, a)
    bottom = np.where(flip[:, None], a, b)
    slope = (bottom[:, 0] - top[:, 0]) / (bottom[:, 1] - top[:, 1])
    ys = np.unique(p[:, 1])
    vertices, triangles = [], []
    for ya, yb in zip(ys[:-1], ys[1:]):
        active = np.nonzero((top[:, 1] <= ya) & (bottom[:, 1] >= yb))[0]
        if len(active) < 2:
            continue
        xa = top[active, 0] + slope[active] * (ya - top[active, 1])
        xb = top[active, 0] + slope[active] * (yb - top[active, 1])
        order = np.argsort(xa + xb)
        xa, xb = xa[order], xb[order]
        for k in range(0, len(xa) - 1, 2):
            base = len(vertices)
            vertices += [(xa[k], ya), (xa[k + 1], ya), (xb[k + 1], yb), (xb[k], yb)]
            triangles += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
    return np.array(vertices, float).reshape(-1, 2), triangles
