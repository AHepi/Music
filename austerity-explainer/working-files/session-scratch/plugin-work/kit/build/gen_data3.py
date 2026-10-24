"""Builds the looks, place types, real-world facts, dial table, species, polyhaven choices and the example data (scratch generator; the output is the data)."""
import json, os
OUT = '/home/user/Music/plugins/explainer-film/kit/place-kit/data'
def dump(rel, data):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(data, open(path, 'w'), indent=1)

WEAR = 'the weathering kit re-check and the street (logs 22 and 25)'
INV = 'the plugin 1.4.0 design: a first try, judge by looking'
STREET = 'the street grime budget (log 22)'

# ------------------------------------------------------------------ dial table
def D(name, lo, hi, default, unit, doc, kind='judged', source=WEAR):
    return {'name': name, 'lo': lo, 'hi': hi, 'default': default, 'unit': unit, 'doc': doc, 'kind': kind, 'source': source}
common = [D('amount', 0.0, 1.0, 1.0, 'multiplier', 'How strongly the layer acts, 0 = exactly nothing (the layer node returns its input unchanged).'),
          D('seed', 0.0, 1000.0, 0.0, 'number', 'Picks one random pattern; a new number gives a new pattern with the same character.', 'judged', 'the weathering kit')]
layers = {
 'dirt': [D('film', 0.0, 1.0, 0.35, 'share', 'How much of the surface carries a thin soil film.'), D('foot_splash', 0.0, 1.0, 0.5, 'share', 'Mud splashed up the foot of walls and posts.'),
          D('foot_height_metres', 0.05, 1.5, 0.45, 'metres', 'How high the splash reaches from the object\'s own lowest point.', 'judged', STREET),
          D('dust', 0.0, 1.0, 0.2, 'share', 'Pale dust on up-facing surfaces.'), D('polish', 0.0, 1.0, 0.3, 'share', 'Smooth polished look where feet or wheels pass.')],
 'grime': [D('area_share', 0.05, 0.6, 0.25, 'share of an area', 'About how much of the area carries dark grime (the street measured: a quarter; more is mush).', 'measured', STREET),
           D('darkening', 0.05, 0.6, 0.33, 'share darker', 'How much darker the grime makes the colour (a third).', 'measured', STREET),
           D('soot_under_shelter', 0.0, 1.0, 0.6, 'share', 'Soot on surfaces under eaves and overhangs.'), D('runoff_streaks', 0.0, 1.0, 0.4, 'share', 'Run-off streaks running down from sills and eaves.'),
           D('damp_band', 0.0, 1.0, 0.35, 'share', 'A darker damp band at the foot of walls.')],
 'weathering': [D('silvering', 0.0, 1.0, 0.5, 'share', 'Timber turning silver-grey.'), D('sun_fade', 0.0, 1.0, 0.3, 'share', 'Colour fading on surfaces that face the sky.'),
                D('patina', 0.0, 1.0, 0.2, 'share', 'Green-blue patina on metal and stone.')],
 'wetness': [D('darken', 0.0, 0.6, 0.25, 'share darker', 'How much darker a wet surface is.', 'judged', 'the street wet recipe'),
             D('wet_roughness', 0.05, 0.6, 0.3, 'roughness', 'Roughness of a wet surface (dry is about 0.9).', 'measured', 'the street wet recipe'),
             D('puddles', 0.0, 1.0, 0.5, 'share', 'How much low ground holds standing water.'), D('film_coat', 0.0, 1.0, 0.4, 'share', 'A thin clear coat on wet surfaces.')],
 'cracks_and_chips': [D('crack_density', 0.0, 1.0, 0.3, 'share', 'How many cracks.'), D('crack_width_metres', 0.002, 0.05, 0.012, 'metres', 'Width of a crack line (about 3 dots at plate size).'),
                      D('chip_amount', 0.0, 1.0, 0.3, 'share', 'Chipped patches at edges.')],
 'edge_wear': [D('width_metres', 0.005, 0.1, 0.02, 'metres', 'How far in from the edge the rubbed zone reaches.'), D('pale', 0.0, 0.6, 0.25, 'share lighter', 'How much paler the rubbed edge is.'),
               D('roughness_drop', 0.0, 0.5, 0.2, 'roughness', 'How much smoother the rubbed edge is.')],
 'moss_and_algae': [D('cover', 0.0, 1.0, 0.4, 'share', 'How much of the damp, shaded area is covered.'), D('clump_size_metres', 0.03, 0.6, 0.15, 'metres', 'Size of a moss clump.'),
                    D('damp_need', 0.0, 1.0, 0.5, 'share', 'How damp it must be.'), D('shade_need', 0.0, 1.0, 0.4, 'share', 'How shaded it must be.')],
 'rust': [D('band', 0.0, 1.0, 0.4, 'share', 'Rust bands by height on the object.'), D('runs', 0.0, 1.0, 0.3, 'share', 'Rust runs below joins.'), D('collar', 0.0, 1.0, 0.3, 'share', 'Rust collars where iron meets other material.')],
 'rubbish': [D('density', 0.0, 1.0, 0.3, 'share', 'Muck and litter marks at gutters, wall feet and lane edges.'), D('straw_share', 0.0, 1.0, 0.4, 'share', 'How much of the litter is straw-coloured.')],
}
dial_table = {'about': 'Every dial of every wear layer: name, range, default, unit, plain-words doc, kind and source. A dial name that is not in this table is an error, so a typo cannot hide. '
                       'The common dials (amount, seed) belong to every layer. The look presets (data/looks) set the amount per layer and may set other dials. Carried from the weathering kit\'s table with the street-only dials dropped.',
              'common': common, 'layers': {k: {'dials': v} for k, v in layers.items()},
              'growth': {'dials': [D('weeds_amount', 0.0, 1.0, 0.5, 'share', 'How many weeds, tufts, ferns and nettles.'), D('cushions_amount', 0.0, 1.0, 0.3, 'share', 'How many moss cushions.'),
                                   D('litter_amount', 0.0, 1.0, 0.4, 'share', 'How many leaves, sticks, straw pieces and dung lumps.')]}}
dump('dial_table.json', dial_table)

# ------------------------------------------------------------------ looks
def look(id_, words, state, amounts, growth, **budgets):
    return {'about': f'The look "{id_}": {words}. Only dial values differ between looks (the code is the same).', 'id': id_, 'state_default': state, 'master': 1.0,
            'layers': {layer: {'amount': a, 'dials': {}} for layer, a in amounts.items()},
            'growth': growth,
            'budgets': {'grime_area_share': 0.25, 'grime_darkening': 0.33, 'darkest_mark': 0.10},
            'kinds': {'amounts': 'invented: first tries by the 1.4.0 design (judge by looking)', 'budgets': 'measured on the street (log 22) and the painted plates (log 25)'},
            'kind': 'invented', 'source': INV}
dump('looks/kept.json', look('kept', 'tidy: light dirt, little rubbish, no heavy moss', 'dry',
     dict(dirt=0.3, grime=0.25, weathering=0.25, wetness=0.5, cracks_and_chips=0.2, edge_wear=0.25, moss_and_algae=0.15, rust=0.3, rubbish=0.15),
     dict(weeds_amount=0.2, cushions_amount=0.1, litter_amount=0.2)))
dump('looks/lived_in.json', look('lived_in', 'in use: dirt where people walk, some moss, a little litter (the default)', 'dry',
     dict(dirt=0.5, grime=0.45, weathering=0.45, wetness=0.5, cracks_and_chips=0.4, edge_wear=0.45, moss_and_algae=0.35, rust=0.5, rubbish=0.35),
     dict(weeds_amount=0.5, cushions_amount=0.3, litter_amount=0.45)))
dump('looks/neglected.json', look('neglected', 'unkept: strong dirt, grime, weeds, moss, rubbish and damp', 'damp',
     dict(dirt=0.75, grime=0.7, weathering=0.7, wetness=0.6, cracks_and_chips=0.6, edge_wear=0.65, moss_and_algae=0.6, rust=0.7, rubbish=0.65),
     dict(weeds_amount=0.8, cushions_amount=0.5, litter_amount=0.75)))
dump('looks/derelict.json', look('derelict', 'falling apart: cracks, sag, heavy moss, weeds everywhere', 'damp',
     dict(dirt=0.9, grime=0.85, weathering=0.9, wetness=0.7, cracks_and_chips=0.85, edge_wear=0.85, moss_and_algae=0.85, rust=0.9, rubbish=0.85),
     dict(weeds_amount=1.0, cushions_amount=0.8, litter_amount=0.95)))

# ------------------------------------------------------------------ place types
def ptype(id_, words, look_id, state, likely, require_more, allowed_off, footfall, cell, facts, notes):
    return {'about': f'Starting preset for a {words}. Data only: code never names a place type. new-settings copies the allowed_off entries that fit into the settings as "off" entries.',
            'id': id_, 'default_look': look_id, 'default_state': state, 'roles_likely': likely, 'require_more': require_more, 'allowed_off': allowed_off,
            'footfall_shapes': footfall, 'plan_mask_cell_metres': cell, 'facts': facts, 'notes': notes, 'kind': 'invented', 'source': INV}
def off(id_, treatments, roles, reason):
    return {'id': id_, 'treatments': treatments, 'roles': roles, 'reason': reason}
INDOOR = off('indoors_dry', ['moss_and_algae', 'weathering', 'wetness', 'plants', 'litter_pieces'], ['wall.interior', 'floor.*', 'timber.floor', 'prop.*'], 'indoors: dry, in no sun or rain, nothing grows')
dump('place_types/village.json', ptype('village', 'village or hamlet', 'lived_in', 'damp', ['ground.dirt_road', 'ground.forest_floor', 'wall.timber_frame', 'wall.plaster', 'roof.thatch', 'timber.post', 'stone.footing', 'prop.barrel', 'tree.bark'], {},
     [off('floors_indoors', ['moss_and_algae', 'weathering', 'wetness', 'plants', 'litter_pieces'], ['floor.*'], 'inside the buildings: dry, nothing grows')],
     [{'shape': 'auto_door_strip', 'role': 'timber.door', 'depth': 1.0, 'width': 1.2}], 0.10, ['door_height', 'door_width', 'cart_gauge', 'roof_pitch', 'wall_thickness'], 'dirt lanes with ruts, timber and thatch, trees close by'))
dump('place_types/town.json', ptype('town', 'town street', 'lived_in', 'damp', ['ground.stone_paving', 'wall.brick', 'wall.stone', 'roof.tile', 'timber.door', 'glass.window', 'iron.fitting'], {'wall': ['dirt']},
     [off('floors_indoors', ['moss_and_algae', 'weathering', 'wetness', 'plants', 'litter_pieces'], ['floor.*'], 'inside the buildings: dry, nothing grows')],
     [{'shape': 'auto_door_strip', 'role': 'timber.door', 'depth': 1.0, 'width': 1.2}], 0.10, ['door_height', 'door_width', 'window_width', 'wall_thickness'], 'paved streets, brick and stone, tiled roofs'))
dump('place_types/harbour.json', ptype('harbour', 'harbour or quay', 'neglected', 'wet', ['ground.stone_paving', 'water.sea', 'prop.boat', 'prop.rope', 'prop.barrel', 'timber.beam', 'iron.fitting'], {'timber': ['moss_and_algae'], 'stone': ['wetness']},
     [off('quay_no_growth', ['plants', 'litter_pieces'], ['ground.stone_paving', 'ground.concrete'], 'a working quay is swept and salted: weeds only in cracks, set by the place'),
      off('floors_indoors', ['moss_and_algae', 'weathering', 'wetness', 'plants', 'litter_pieces'], ['floor.*'], 'inside the buildings: dry, nothing grows')],
     [{'shape': 'rect', 'note': 'draw the quay walking strip by hand'}], 0.10, ['door_height', 'door_width'], 'wet stone, rope, boats, tide marks'))
dump('place_types/mine.json', ptype('mine', 'mine, quarry or industrial yard', 'neglected', 'damp', ['ground.rock', 'ground.mud', 'wall.brick', 'wall.metal_sheet', 'iron.fitting', 'iron.sheet', 'timber.beam', 'prop.cart'], {'iron': ['grime']},
     [off('underground_no_sun', ['weathering'], ['floor.*', 'wall.interior', 'ground.rock'], 'underground or under cover: no sun fade'),
      off('bare_rock_no_moss', ['moss_and_algae', 'plants'], ['ground.rock'], 'bare spoil and rock: nothing takes root'),
      off('floors_indoors', ['moss_and_algae', 'weathering', 'wetness', 'plants', 'litter_pieces'], ['floor.*'], 'inside the buildings: dry, nothing grows')],
     [{'shape': 'polyline', 'note': 'a track along the rails or the yard route'}], 0.10, ['door_height', 'door_width', 'cart_wheel_diameter'], 'coal dust, rails, rust, ruts in mud'))
dump('place_types/farm.json', ptype('farm', 'farm or farmyard', 'lived_in', 'damp', ['ground.mud', 'ground.grass', 'ground.dirt_road', 'timber.fence', 'wall.timber_frame', 'roof.shingle', 'prop.straw', 'prop.cart', 'prop.wood'], {'ground': ['moss_and_algae']},
     [off('floors_indoors', ['moss_and_algae', 'weathering', 'wetness', 'plants', 'litter_pieces'], ['floor.*'], 'inside the buildings: dry, nothing grows')],
     [{'shape': 'auto_door_strip', 'role': 'timber.door', 'depth': 1.5, 'width': 1.6}], 0.10, ['door_height', 'door_width', 'fence_height', 'cart_gauge'], 'mud, straw, fences, tracks between buildings'))
dump('place_types/garden.json', ptype('garden', 'garden or park', 'lived_in', 'damp', ['ground.grass', 'ground.gravel', 'stone.rock', 'tree.bark', 'plant.foliage', 'water.still', 'timber.post', 'timber.plank'], {'ground': ['moss_and_algae'], 'stone': ['moss_and_algae']},
     [off('floors_indoors', ['moss_and_algae', 'weathering', 'wetness', 'plants', 'litter_pieces'], ['floor.*'], 'inside the buildings: dry, nothing grows')],
     [{'shape': 'polyline', 'note': 'the path people walk'}], 0.10, ['fence_height', 'plank_width', 'post_size'], 'moss, leaves, stones, a path, water'))
dump('place_types/interior.json', ptype('interior', 'room or interior set', 'lived_in', 'dry', ['floor.planks', 'floor.tile', 'wall.interior', 'timber.beam', 'prop.furniture', 'glass.window', 'prop.cloth'], {},
     [INDOOR], [{'shape': 'rect', 'note': 'the walking area of the room'}], 0.05, ['door_height', 'door_width', 'window_width', 'table_height', 'bench_height'], 'dust, scuffs, worn edges; no growth'))

# ------------------------------------------------------------------ real-world facts
FSRC = 'common building and prop practice (from memory; confirm for the period and place)'
def F(id_, what, role_pattern, dimension, lo, hi, unit, confidence, name_pattern=None, slab_only=False, kind='judged', note=''):
    f = {'id': id_, 'what': what, 'applies_to_role': role_pattern, 'dimension': dimension, 'min': lo, 'max': hi, 'unit': unit, 'kind': kind, 'source': FSRC, 'confidence': confidence}
    if name_pattern: f['applies_to_name'] = name_pattern
    if slab_only: f['only_if_slab_like'] = True
    if note: f['note'] = note
    return f
facts = [
 F('door_height', 'a door is about head high and a little more', r'^timber\.door$', 'height', 1.6, 2.3, 'metres', 'weak'),
 F('door_width', 'a single door or a double door', r'^timber\.door$', 'width', 0.6, 2.0, 'metres', 'weak'),
 F('door_thickness', 'door leaf thickness', r'^timber\.door$', 'thickness', 0.025, 0.10, 'metres', 'weak'),
 F('shutter_height', 'a window shutter', r'^timber\.shutter$', 'height', 0.3, 2.0, 'metres', 'guess'),
 F('window_width', 'a window opening', r'^glass\.window$', 'width', 0.3, 1.5, 'metres', 'weak'),
 F('window_height', 'a window opening', r'^glass\.window$', 'height', 0.3, 1.6, 'metres', 'weak'),
 F('wall_thickness', 'a wall slab', r'^wall\.', 'thickness', 0.10, 0.9, 'metres', 'weak', slab_only=True),
 F('roof_pitch', 'a pitched roof slope', r'^roof\.(thatch|shingle|tile|slate)$', 'pitch', 28, 62, 'degrees', 'weak', note='a flat roof (under 5 degrees) is not judged'),
 F('thatch_thickness', 'thatch thickness', r'^roof\.thatch$', 'thickness', 0.15, 0.45, 'metres', 'guess', slab_only=True),
 F('post_size', 'a timber post', r'^timber\.post$', 'width', 0.06, 0.45, 'metres', 'weak'),
 F('beam_size', 'a timber beam cross-section', r'^timber\.beam$', 'thickness', 0.04, 0.4, 'metres', 'weak'),
 F('plank_width', 'a board', r'^timber\.(plank|floor)$', 'middle', 0.08, 0.35, 'metres', 'weak', slab_only=True),
 F('plank_thickness', 'board thickness', r'^timber\.(plank|floor)$', 'thickness', 0.012, 0.08, 'metres', 'weak', slab_only=True),
 F('fence_height', 'a fence', r'^timber\.fence$', 'height', 0.5, 2.2, 'metres', 'weak'),
 F('chimney_height', 'a chimney stack', r'^stone\.chimney$', 'height', 0.8, 7.0, 'metres', 'guess'),
 F('well_height', 'a well, trough or sink', r'^stone\.well$', 'height', 0.3, 1.4, 'metres', 'guess'),
 F('barrel_height', 'a barrel', r'^prop\.barrel$', 'height', 0.4, 1.3, 'metres', 'weak'),
 F('crate_size', 'a crate or chest', r'^prop\.crate$', 'span', 0.25, 1.8, 'metres', 'guess'),
 F('cart_height', 'a hand or horse cart', r'^prop\.cart$', 'height', 0.5, 2.4, 'metres', 'guess'),
 F('cart_wheel_diameter', 'a cart wheel', r'^prop\.wheel$', 'height', 0.4, 1.7, 'metres', 'weak'),
 F('cart_gauge', 'the distance between cart wheels (rut centre to rut centre)', r'^ground\.dirt_road$', 'gauge', 1.0, 1.8, 'metres', 'weak', kind='judged', note='compared with the gauge written in the place settings roads'),
 F('table_height', 'a table or desk', r'^prop\.furniture$', 'height', 0.6, 0.95, 'metres', 'weak', name_pattern=r'table|desk'),
 F('bench_height', 'a bench or stool seat', r'^prop\.furniture$', 'height', 0.3, 0.6, 'metres', 'weak', name_pattern=r'bench|stool'),
 F('stall_width', 'a horse stall', r'.*', 'width', 1.4, 3.2, 'metres', 'guess', name_pattern=r'\bstall\b'),
 F('manger_height', 'a manger rim', r'.*', 'height', 0.7, 1.3, 'metres', 'guess', name_pattern=r'manger'),
 F('step_rise', 'one stair or step rise', r'.*', 'height', 0.10, 0.25, 'metres', 'weak', name_pattern=r'\bstep\b|\bstair\b'),
 F('ladder_width', 'a ladder', r'.*', 'width', 0.3, 0.7, 'metres', 'guess', name_pattern=r'ladder'),
 F('bucket_height', 'a bucket', r'.*', 'height', 0.2, 0.5, 'metres', 'weak', name_pattern=r'bucket'),
 F('tree_height', 'a tree', r'^tree\.bark$', 'height', 1.0, 45.0, 'metres', 'guess'),
]
dump('real_world_facts.json', {'about': 'Generic scale facts the scale check uses (every number has kind and source; most are weak or guesses because they are from memory). '
       'dimension: height = z extent; width = larger horizontal extent; depth = smaller horizontal extent; thickness = smallest of the three extents; middle = middle of the three; span = largest; '
       'pitch = roof slope in degrees; gauge = distance between wheel ruts (read from the settings, not from an object). only_if_slab_like: used only when the object\'s smallest extent is at most 0.4 of its middle one, '
       'so a whole building in one object is not read as one thick wall. A fact applies to an object when its role matches applies_to_role (a regular expression) and, if given, its name matches applies_to_name. '
       'A place adds or replaces facts in its own facts file (the planner researches them with sources).', 'facts': facts})

# ------------------------------------------------------------------ species for 3D plants and litter
def sp(group, builder, size_cm, share, colours, likes, note, gates=None, count_hint=None):
    return {'group': group, 'builder': builder, 'size_cm': size_cm, 'share': share, 'colours': colours, 'likes': likes, 'gates': gates or {}, 'note': note, 'kind': 'invented', 'source': INV}
species = {'about': 'The 3D plant and litter species: chunky designed shapes built in code (growth/pieces.py), where each likes to grow (likes: 0..1 weights on base, damp, shade, wall_foot, edge, seam) and its gates. '
           'Sizes are tall (or across for flat things) in centimetres. Colours are sRGB hex, pulled 45 percent toward their own grey so they sit in the style. Gates are exact: a piece whose root is inside footfall 0.6, crown 0.7, keepclear 0.5, a puddle or within 5 cm of litter is never made.',
           'palette': {'leaf': '#4d6f36', 'leaf_light': '#6a8a44', 'leaf_dark': '#38552a', 'dead': '#a89560', 'fern': '#3f6a3a', 'bramble': '#4a5a30', 'nettle': '#476b34', 'moss': '#587a38', 'moss_light': '#7a9548',
                       'straw': '#c2a85e', 'needle': '#7a5a32', 'stick': '#5a4630', 'dung': '#4a3a24', 'autumn_leaf': '#8a5a2a', 'clover': '#5a8040'},
           'tuning': {'grey_pull': 0.45, 'size_range_min_ratio': 3.0, 'tuft_meshes_min': 8, 'kind': 'judged', 'source': 'the garden ground builder (g6_tufts.py): at least 8 tuft meshes, scale range 3 to 1, colour pulled 45 percent to grey'},
           'kinds': {
             'tuft': sp('plant', 'tuft', [6, 28], 0.30, ['leaf', 'leaf_light', 'dead'], {'base': 0.5, 'damp': 0.3, 'shade': 0.1, 'wall_foot': 0.3, 'edge': 0.5, 'seam': 0.4}, 'a tuft of 5 to 9 folded blades'),
             'clover': sp('plant', 'rosette', [3, 8], 0.08, ['clover', 'leaf'], {'base': 0.4, 'damp': 0.4, 'shade': 0.2, 'wall_foot': 0.1, 'edge': 0.3, 'seam': 0.6}, 'a low mat of round leaves'),
             'nettle': sp('plant', 'stalk', [30, 90], 0.10, ['nettle', 'leaf_dark'], {'base': 0.3, 'damp': 0.5, 'shade': 0.3, 'wall_foot': 0.7, 'edge': 0.4, 'seam': 0.1}, 'tall stalks with toothed leaves, at wall feet and fences'),
             'fern': sp('plant', 'frond', [20, 80], 0.10, ['fern', 'leaf_dark'], {'base': 0.2, 'damp': 0.7, 'shade': 0.8, 'wall_foot': 0.3, 'edge': 0.2, 'seam': 0.0}, 'arching fronds in shade'),
             'bramble': sp('plant', 'arch', [40, 120], 0.04, ['bramble', 'leaf_dark'], {'base': 0.2, 'damp': 0.3, 'shade': 0.4, 'wall_foot': 0.3, 'edge': 0.8, 'seam': 0.0}, 'arching thorny stems at the edge of the place'),
             'moss_cushion': sp('plant', 'cushion', [4, 18], 0.12, ['moss', 'moss_light'], {'base': 0.2, 'damp': 0.8, 'shade': 0.8, 'wall_foot': 0.5, 'edge': 0.3, 'seam': 0.5}, 'lumpy cushions with a rolled edge, never brighter than the stone below'),
             'leaf': sp('litter', 'flake', [3, 9], 0.14, ['autumn_leaf', 'dead', 'leaf_dark'], {'base': 0.4, 'damp': 0.4, 'shade': 0.3, 'wall_foot': 0.7, 'edge': 0.7, 'seam': 0.3}, 'single leaves, at wall feet, gutters and lane edges'),
             'pine_needles': sp('litter', 'clump', [4, 12], 0.05, ['needle'], {'base': 0.5, 'damp': 0.3, 'shade': 0.5, 'wall_foot': 0.2, 'edge': 0.4, 'seam': 0.2}, 'a clump of needles'),
             'stick': sp('litter', 'stick', [8, 40], 0.04, ['stick'], {'base': 0.5, 'damp': 0.3, 'shade': 0.3, 'wall_foot': 0.3, 'edge': 0.5, 'seam': 0.1}, 'a bent twig'),
             'straw': sp('litter', 'straw', [6, 30], 0.02, ['straw'], {'base': 0.4, 'damp': 0.1, 'shade': 0.1, 'wall_foot': 0.6, 'edge': 0.6, 'seam': 0.2}, 'a few straws near doors and carts'),
             'dung_lump': sp('litter', 'lump', [3, 8], 0.01, ['dung'], {'base': 0.5, 'damp': 0.2, 'shade': 0.1, 'wall_foot': 0.1, 'edge': 0.4, 'seam': 0.0}, 'a lump near stables and tracks (never on the crown)'),
           }}
dump('species.json', species)

# ------------------------------------------------------------------ poly haven choices
def ph(slug, kind, why, caution=''):
    return {'slug': slug, 'kind': kind, 'real_size_metres': None, 'real_size_note': 'not read: open the asset page and write the real size before use', 'why': why, 'caution': caution, 'date_read': '2026-10-22'}
tex = ['brown_mud', 'brown_mud_02', 'brown_mud_03', 'brown_mud_dry', 'brown_mud_leaves_01', 'brown_mud_rocks_01', 'forrest_ground_01', 'forrest_ground_03', 'forest_ground_05', 'forest_leaves_02', 'grass_path_2', 'leafy_grass',
       'thatch_roof_angled', 'reed_roof_03', 'reed_roof_04', 'riet_01', 'clay_plaster', 'clay_roof_tiles', 'castle_wall_slates', 'cobblestone_01', 'cobblestone_02', 'cobblestone_03', 'cobblestone_04', 'cobblestone_05', 'bark_brown_01', 'bark_brown_02', 'brick_moss_001']
mod = ['Barrel_01', 'Barrel_02', 'barrel_03', 'wine_barrel_01', 'wooden_bucket_01', 'wooden_bucket_02', 'wooden_crate_01', 'wooden_crate_02', 'wicker_basket_01', 'wicker_basket_02', 'wooden_ladder', 'wooden_ladder_02', 'tree_stump_01', 'tree_stump_02',
       'dead_tree_trunk', 'dead_tree_trunk_02', 'fir_sapling', 'fir_sapling_medium', 'fir_tree_01', 'Lantern_01', 'wooden_lantern_01', 'jug_01', 'metal_jug', 'spinning_wheel_01', 'rusted_wheel_rim_01', 'rusted_wheel_rim_02']
dump('polyhaven_choices.json', {'about': 'Poly Haven pictures and models (CC0 licence) that were seen on the site on 22 October 2026 and may suit mediaeval and rural places. NOTHING is shipped: fetch at run time. '
       'URL pattern for a texture map: https://dl.polyhaven.org/file/ph-assets/Textures/jpg/<1k|2k>/<id>/<id>_<map>_<1k|2k>.jpg. Use a generic agent name in the request and nothing personal. '
       'Not found on that date: a cart, hay or straw bales, a trough, an anvil, a well, stable stalls, a thatched cottage: script those. '
       'Rules: pick a photo surface by drawing a small test plate; open every downloaded picture at full size and look for stickers, brands and digits (judgement); scans alone read bland, so designed marks and geometry go on top.',
       'textures': [ph(s, 'texture', 'seen on the site on the date read; suits the named surface', 'check for stickers, brands and digits before use') for s in tex],
       'models': [ph(s, 'model', 'seen on the site on the date read', 'check scale and materials; its own maps count as normal_map and roughness_variation under prop.imported') for s in mod],
       'not_found': ['cart', 'hay or straw bales', 'trough', 'anvil', 'well', 'stable stalls', 'thatched cottage']})
print('ok')
