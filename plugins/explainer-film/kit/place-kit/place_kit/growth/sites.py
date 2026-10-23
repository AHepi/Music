"""What this does: says WHERE small plants, litter and stones gather, the way they do in a real place, instead of spreading them evenly. A real weed grows where it is left alone and
where water and dirt collect: in a strip about 18 cm wide at the foot of a wall, along the edge of a road and on the grass strip between its ruts and along the line where two
ground surfaces meet (a verge), along a fence or a building line, in the joints between stones or boards, in damp shady corners, and only thinly anywhere else. These are the
SITES, in this order (a spot belongs to the first site it is in):
  wall_foot    a strip at the foot of a wall (wall_dist up to its width)
  verge        a road's edge and the seam where two different ground surfaces meet (verge_dist up to its width)
  fence_line   a strip along a fence, post, prop or any other solid thing standing on the ground (prop_dist up to its width)
  joint        the joint between two pieces of the same ground surface (separate stones, boards; joint_dist up to its width)
  centre_strip the grass strip between the two ruts of a road with "centre_grass": a close, low sward (the plants that like joints and seams: tufts, clover, moss)
  damp_corner  damp, shady ground near a wall (dampness and shade both high)
  background   everything else a piece may stand on
Each site holds a COUNT: per metre of its length for the strips, per 100 square metres for the areas, from the "sites" block of data/species.json times the look's growth
amount, and only on ground a view camera can see (full within place_wear.scatter_full_metres of a camera, fading to none at place_wear.scatter_reach_metres; a scene with
no camera is seen everywhere). The growth step lays exactly that many in each site; the audit measures the sites again from the plan masks and counts the pieces in each,
so the share of weeds at wall feet, verges and joints is a number a model can read. Plain numpy, no Blender: tested without it.
A concrete example: site_grids(...) on a plan with one wall gives a wall_foot strip one or two cells wide along the wall; site_measures(...) says it is 12.4 m long; with a
lived-in look (weeds 0.5) and 6 plants a metre at full, the wall foot gets 37 plants.
"""
import numpy as np

SITE_ORDER = ('wall_foot', 'verge', 'fence_line', 'joint', 'centre_strip', 'damp_corner', 'background')
STRIP_SITES = ('wall_foot', 'verge', 'fence_line', 'joint')
LINE_SITES = ('verge', 'joint')             # a strip round a LINE (a road's edge, a joint) lies on both sides of it, so its length is its area over twice its width
AREA_SITES = ('centre_strip', 'damp_corner', 'background')
GROUPS = ('plant', 'litter', 'stone')
# which liking of a species (data/species.json "likes") decides how much of a site's count it takes
LIKING_OF_SITE = {'wall_foot': ('wall_foot',), 'verge': ('edge',), 'fence_line': ('edge', 'wall_foot'), 'joint': ('seam',), 'centre_strip': ('seam',), 'damp_corner': ('damp', 'shade'),
                  'background': ('base',)}
DISTANCE_SCALE = {'wall_dist': 4.0, 'prop_dist': 4.0, 'verge_dist': 2.0, 'joint_dist': 1.0}      # the same as the plan masks' (wear/masks.py)


def number(entry):
    return entry['value'] if isinstance(entry, dict) and 'value' in entry else entry


def grid(plan_grids, name):
    """A plan mask as floats: 0..1, or metres for a distance mask. plan_grids: {name: uint8 array}."""
    values = np.asarray(plan_grids[name], dtype=np.float64) / 255.0
    return values * DISTANCE_SCALE[name] if name in DISTANCE_SCALE else values


def gate_grid(plan_grids, gates):
    """True in a cell where a piece may stand: not on a worn path, a road's crown, kept-clear ground, a wheel track or in a puddle, not inside a wall or a prop, on ground
    that grows things. gates: {'footfall', 'crown', 'keepclear'} exact-zero limits (house numbers place_wear.exact_zero_gate_*)."""
    ok = (grid(plan_grids, 'footfall') < gates['footfall']) & (grid(plan_grids, 'crown') < gates['crown']) & (grid(plan_grids, 'keepclear') < gates['keepclear'])
    ok &= (grid(plan_grids, 'track') < 0.5) & (grid(plan_grids, 'above_water') >= 0.5)
    ok &= (grid(plan_grids, 'wall_dist') > 0.06) & (grid(plan_grids, 'prop_dist') > 0.04)
    if 'grows' in plan_grids:
        ok &= grid(plan_grids, 'grows') >= 0.5                 # the top ground here is one that grows plants and litter
    return ok


def site_grids(plan_grids, cell, table):
    """{site: boolean grid}, each cell in exactly one site (the first of SITE_ORDER it is in), or in none (a cell nothing may stand on is still given a site; the gates
    are applied by the caller). A strip narrower than one cell is widened to one cell, so a coarse plan of a big place still has its strips."""
    width = {site: max(float(number(table[site]['width_metres'])), cell * 1.01) for site in STRIP_SITES}
    wall, prop = grid(plan_grids, 'wall_dist'), grid(plan_grids, 'prop_dist')
    verge = grid(plan_grids, 'verge_dist') if 'verge_dist' in plan_grids else np.full(wall.shape, 9.0)
    joint = grid(plan_grids, 'joint_dist') if 'joint_dist' in plan_grids else np.full(wall.shape, 9.0)
    damp, shade = grid(plan_grids, 'dampness'), grid(plan_grids, 'shade')
    corner = table['damp_corner']
    wanted = {
        'wall_foot': (wall > 0.0) & (wall <= width['wall_foot']),
        'verge': verge <= width['verge'],
        'fence_line': (prop > 0.0) & (prop <= width['fence_line']),
        'joint': joint <= width['joint'],
        'centre_strip': (grid(plan_grids, 'centre_strip') >= 0.5) if 'centre_strip' in plan_grids else np.zeros(wall.shape, dtype=bool),
        'damp_corner': (damp >= float(number(corner['dampness_min']))) & (shade >= float(number(corner['shade_min']))) & (wall <= float(number(corner['wall_reach_metres']))),
    }
    taken = np.zeros(wall.shape, dtype=bool)
    result = {}
    for site in SITE_ORDER:
        cells_here = (~taken) if site == 'background' else (wanted[site] & ~taken)
        result[site] = cells_here
        taken |= cells_here
    return result


def seen_weight(shape, x0, y0, cell, cameras_xy, full_metres, reach_metres):
    """How much each cell counts (1 within full_metres of a view camera, falling to 0 at reach_metres; 1 everywhere with no camera). cameras_xy: [(x, y), ...]."""
    if not cameras_xy:
        return np.ones(shape)
    rows, cols = shape
    xs = x0 + (np.arange(cols) + 0.5) * cell
    ys = y0 + (np.arange(rows) + 0.5) * cell
    nearest = np.full(shape, np.inf)
    for cx, cy in cameras_xy:
        dx = (xs - cx) ** 2
        dy = (ys - cy) ** 2
        nearest = np.minimum(nearest, np.sqrt(dy[:, None] + dx[None, :]))
    fall = np.clip((reach_metres - nearest) / max(reach_metres - full_metres, 1e-6), 0.0, 1.0)
    return fall * fall * (3.0 - 2.0 * fall)


def site_measures(sites, allowed, weight, cell, table):
    """{site: {'cells', 'area_m2', 'seen_area_m2', 'length_m', 'seen_length_m'}} for the cells where a piece may stand. A strip's length is its area over its width."""
    result = {}
    area_per_cell = cell * cell
    for site in SITE_ORDER:
        cells = sites[site] & allowed
        area = float(cells.sum() * area_per_cell)
        seen = float((weight * cells).sum() * area_per_cell)
        entry = {'cells': int(cells.sum()), 'area_m2': round(area, 2), 'seen_area_m2': round(seen, 2)}
        if site in STRIP_SITES:
            width = max(float(number(table[site]['width_metres'])), cell * 1.01) * (2.0 if site in LINE_SITES else 1.0)
            entry['length_m'] = round(area / width, 2)
            entry['seen_length_m'] = round(seen / width, 2)
        result[site] = entry
    return result


def group_scale(group, growth):
    """How much of the full count a look gives a group: plants follow the look's weeds amount, litter its litter amount, stones half fixed and half the litter amount
    (a kept road still has its stones)."""
    if group == 'plant':
        return float(growth['weeds_amount'])
    if group == 'litter':
        return float(growth['litter_amount'])
    return 0.5 + 0.5 * float(growth['litter_amount'])


def targets(measures, table, group, scale, density=1.0):
    """{site: count} for one group: the full count per metre (strips) or per 100 square metres (areas) of SEEN ground, times the look's scale and any density dial."""
    result = {}
    for site in SITE_ORDER:
        dial = table[site].get(f'{group}_per_metre' if site in STRIP_SITES else f'{group}_per_100_square_metres')
        dial = float(number(dial)) if dial is not None else 0.0
        amount = measures[site]['seen_length_m'] if site in STRIP_SITES else measures[site]['seen_area_m2'] / 100.0
        result[site] = int(round(dial * amount * scale * density))
    return result


def species_weights(kinds, site, extra_share=None):
    """{kind: weight} of the species of one group for one site: its share times how much it likes that site (data/species.json "likes"; "seam" is read for joints).
    A species that does not like a site at all (0) never grows there."""
    keys = LIKING_OF_SITE[site]
    weights = {}
    for name, spec in kinds.items():
        likes = spec.get('likes') or {}
        liking = float(np.mean([float(likes.get(key, 0.0)) for key in keys]))
        weights[name] = max(0.0, float(spec.get('share', 0.0)) * (extra_share or {}).get(name, 1.0) * liking)
    return weights


def pick_cells(rng, cells_mask, weight, count, cell, x0, y0):
    """`count` points (x, y) inside the cells of a mask, a cell chosen with a chance by its weight, the point anywhere inside it. Returns (n, 2)."""
    rows, cols = np.nonzero(cells_mask)
    if len(rows) == 0 or count <= 0:
        return np.zeros((0, 2))
    chance = weight[rows, cols].astype(np.float64)
    if chance.sum() <= 0:
        return np.zeros((0, 2))
    chosen = rng.choice(len(rows), size=int(count), replace=True, p=chance / chance.sum())
    xs = x0 + (cols[chosen] + rng.random(int(count))) * cell
    ys = y0 + (rows[chosen] + rng.random(int(count))) * cell
    return np.stack([xs, ys], axis=1)


def classify_points(points, plan_grids, x0, y0, cell, table):
    """The site of each point (n, 2 or 3) as a list of names, read from the same site grids the growth step used."""
    sites = site_grids(plan_grids, cell, table)
    p = np.asarray(points, dtype=np.float64).reshape(-1, np.asarray(points).shape[-1]) if len(points) else np.zeros((0, 2))
    shape = next(iter(plan_grids.values())).shape
    cols = np.clip(((p[:, 0] - x0) / cell).astype(int), 0, shape[1] - 1)
    rows = np.clip(((p[:, 1] - y0) / cell).astype(int), 0, shape[0] - 1)
    names = np.array(['background'] * len(p), dtype=object)
    for site in reversed(SITE_ORDER):
        inside = sites[site][rows, cols]
        names[inside] = site
    return list(names)


def shares(site_names):
    """{site: share of the pieces} (0..1) for a list of site names."""
    total = len(site_names)
    return {site: (sum(1 for s in site_names if s == site) / total if total else 0.0) for site in SITE_ORDER}
