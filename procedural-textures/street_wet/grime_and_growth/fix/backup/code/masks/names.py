# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE LIST OF BUS NAMES: every mask a layer can read, by ONE name whichever frame supplies it, with what it means and what it is when a set has nothing for it.
# This is data (a list of rows); masks/CONTRACT.md is written from it (masks/make_contract.py) so the two cannot disagree. A layer reads a mask through the node group input
# 'M <Title Case Name>' (mask_socket('moss_site') = 'M Moss Site'); the bus (bus.py) wires it by name.
# frame: GP = the ground plan (seen from above, world x and y), WF = a wall sheet (the wall mesh's own frame: across the front, up from the floor), TX = texture space (the
# material's own picture coordinates), SH = made in the shader from position and normal, OBJ = an object value.
# kind: 'f' = a number 0..1 (or metres where the meaning says so); the bus passes every mask on as 0..1 unless 'metres' says the picture holds metres / reach.
NAMES = [
    # name, frame, default, meaning
    ('ground_height', 'GP', 0.0, 'Height of the top of the ground at each dot, in metres (found by dropping a ray from above onto the ground roles). Stored 16-bit over the set\'s z range; the bus gives metres.'),
    ('height', 'GP/WF', 0.0, 'Height of a surface point above the ground, in metres: its z minus the ground height at its x and y (wall sheets carry the baked value).'),
    ('slope', 'GP', 0.0, '0 = flat, 1 = a 30 degree slope (the angle of the ground\'s gradient over 8 cm).'),
    ('lowness', 'GP', 0.5, 'How much lower this dot is than the ground within the set\'s lowness radius: 1 = the bottom of a gutter or dip (water gathers), 0 = a high spot.'),
    ('crown', 'GP', 0.0, '1 on the raised middle of a road (how much higher a dot is than the lowest ground of the same role within reach); 0 on roles the set does not name and elsewhere.'),
    ('wall_dist', 'GP', 1.0, 'Distance from a point 3 cm above the ground to the nearest solid wall, step or plinth, 0 = touching, 1 = the wall reach (1.275 m) or more.'),
    ('prop_dist', 'GP', 1.0, 'The same for the nearest prop or fire (roles named in geometry.prop_roles).'),
    ('inside_corner', 'GP', 0.0, 'Where two solid things meet (a step and its wall): 1 = a corner where litter and damp collect.'),
    ('step_foot', 'GP', 0.0, 'The foot of every step: a soft spot round each entrance.'),
    ('vertical_foot', 'GP', 0.0, 'The feet of pipes, posts and other standing iron.'),
    ('step_top', 'GP', 0.0, '1 on the tread of a step (an up-facing face of the step roles at least 5 cm above the ground, near an entrance).'),
    ('step_edge', 'GP', 1.0, 'Distance in from the tread\'s outer edge: 0 at the nosing, 1 at 25 cm in (1 where there is no step).'),
    ('edge_dist', 'GP', 1.0, 'Distance (0 to 0.3 m, scaled to 0..1) to the nearest sharp, outward-pointing edge of ground, kerb and step surfaces.'),
    ('piece_gap', 'GP', 1.0, 'Distance to the boundary between two separate stones of one role (kerb ends, copings), 0..1 over 0.3 m.'),
    ('seam_dist', 'GP', 1.0, 'Distance to the line where two ground roles meet (road and gutter, gutter and kerb, kerb and pavement), 0..1 over 0.5 m.'),
    ('cover_dist', 'GP', 1.0, 'Distance to the nearest iron cover or grating (1 if the set has none).'),
    ('water_dist', 'GP', 1.0, 'Distance to the water line (0 to 1.5 m, scaled to 0..1); 1 in a set without water.'),
    ('above_water', 'GP', 1.0, 'Height above the water level, 0..1 over 1 m; 1 in a set without water.'),
    ('sheltered', 'WF/GP', 0.0, '0 to 1: rain cannot reach this dot (the share of short rays within 35 degrees of straight up that hit something within reach).'),
    ('drip', 'WF/GP', 0.0, 'The column of run-off below a source (a sill, ledge, eave, pipe joint, cap): 1 across the source\'s width, falling to 0 over a 15 cm margin at each side, and running down the wall for the set\'s drip length (the ground plan: a soft line under the eaves and ledges). `drip_dist` says how far below the source.'),
    ('drip_dist', 'WF/GP', 1.0, 'How far (0 to 1.5 m, scaled to 0..1) below the nearest run-off source.'),
    ('drip_kind', 'WF/GP', 0.0, 'Which kind of source (0 none, then ledge 0.2, pipe joint 0.4, pipe foot 0.6, gutter end or eave 0.8, cap or kasa 1.0).'),
    ('corner', 'WF', 1.0, 'Distance (0 to 0.4 m, scaled) to a vertical outward wall corner or an opening\'s edge.'),
    ('reveal', 'WF', 0.0, 'How deep inside an opening\'s reveal the dot is.'),
    ('openness', 'WF/GP', 0.5, 'Sky openness: 1 = open to the sky, 0 = enclosed (rays, stretched over the scene\'s own min to max).'),
    ('shade', 'WF/GP', 0.5, '1 = deep shade or facing away from the sun; the mix the set\'s shade block names (declared sun, openness, year sun).'),
    ('dampness', 'WF/GP', 0.3, 'How long a spot stays wet: weights of closeness to a wall foot, drip zone, water, lowness and shade.'),
    ('footfall', 'GP', 0.0, '0 to 1 how trodden, from the set\'s footfall shapes.'),
    ('keepclear', 'GP', 0.0, 'Hard "no plants here": the set\'s keep-clear shapes and wherever footfall is over 0.5 to 0.7.'),
    ('entry_rand', 'GP', 0.5, 'A random number per entrance painted over a disc round each entrance; 0.5 elsewhere (steps and the flags in front of one door agree).'),
    ('existing_growth', 'GP', 0.0, 'Density of growth the set already has (blurred 15 cm), so layers never double it.'),
    ('rubbish_heap', 'GP', 0.0, 'The rubbish layer\'s mask seen from above (0 clean, 1 heap); only sets that have the rubbish layer.'),
    ('moss_site', 'GP/WF', 0.0, 'Where moss may grow (habitat field; exactly 0 where footfall is 0.6 or more, crown 0.7 or more, keepclear 0.5 or more).'),
    ('weed_site', 'GP', 0.0, 'Where weeds may grow (same exclusions).'),
    ('algae_site', 'GP/WF', 0.0, 'Where algae may grow (same exclusions except crown).'),
    ('lichen_site', 'GP/WF', 0.0, 'Where lichen may grow (0 unless the set switches lichen on).'),
    ('tx_cavity', 'TX', 0.0, 'Hollows of the photo\'s own relief (mortar, stone gaps, sett joints): 0..1.'),
    ('tx_joint', 'TX', 0.0, 'Joint centre-lines of setts and flags (and brick courses).'),
    ('tx_cell', 'TX', 0.5, 'A random number per sett, flag or brick (0..1).'),
    ('frame_valid', 'SH', 0.0, '1 where the wall sheet applies to this dot (it faces the sheet\'s frame); 0 elsewhere (gable ends, chimneys, roofs read the ground plan).'),
]
BY_NAME = {row[0]: row for row in NAMES}
ALL = [row[0] for row in NAMES]


def mask_socket(name):
    """'moss_site' -> 'M Moss Site' (the node-group input a layer declares)."""
    return 'M ' + ' '.join(w.capitalize() for w in name.split('_'))


def name_of_socket(socket_name):
    if not socket_name.startswith('M '):
        return None
    candidate = socket_name[2:].lower().replace(' ', '_')
    return candidate if candidate in BY_NAME else None


def default_of(name):
    return BY_NAME[name][2]
