"""Builds kit/place-kit/data/roles.json, treatments.json and banned_place_nouns.json (scratch generator; the output is the data)."""
import json, os
OUT = '/home/user/Music/plugins/explainer-film/kit/place-kit/data'
KIND = 'judged'
SRC = 'the plugin 1.4.0 design (22 October 2026) and the garden, street and mine work'

classes = {
 'ground': {'requires': ['normal_map', 'roughness_variation', 'colour_variation', 'dirt', 'grime', 'weathering', 'wetness', 'cracks_and_chips', 'rubbish', 'plants', 'litter_pieces'],
            'wanted': ['moss_and_algae', 'displacement']},
 'floor': {'requires': ['normal_map', 'roughness_variation', 'colour_variation', 'dirt', 'grime', 'cracks_and_chips'],
           'wanted': ['wetness', 'edge_wear', 'rubbish', 'weathering']},
 'wall': {'requires': ['normal_map', 'roughness_variation', 'colour_variation', 'bevelled_edges', 'dirt', 'grime', 'weathering', 'wetness', 'cracks_and_chips', 'edge_wear', 'moss_and_algae'],
          'wanted': ['shape_damage']},
 'roof': {'requires': ['normal_map', 'roughness_variation', 'colour_variation', 'dirt', 'grime', 'weathering', 'wetness', 'cracks_and_chips', 'moss_and_algae', 'shape_damage'], 'wanted': []},
 'timber': {'requires': ['normal_map', 'roughness_variation', 'colour_variation', 'bevelled_edges', 'dirt', 'grime', 'weathering', 'wetness', 'cracks_and_chips', 'edge_wear', 'shape_damage'],
            'wanted': ['moss_and_algae']},
 'stone': {'requires': ['normal_map', 'roughness_variation', 'colour_variation', 'dirt', 'grime', 'weathering', 'wetness', 'cracks_and_chips', 'edge_wear', 'moss_and_algae'], 'wanted': ['shape_damage']},
 'iron': {'requires': ['roughness_variation', 'colour_variation', 'dirt', 'wetness', 'rust', 'edge_wear'], 'wanted': ['normal_map', 'bevelled_edges']},
 'prop': {'requires': ['normal_map', 'roughness_variation', 'colour_variation', 'dirt', 'wetness', 'edge_wear'], 'wanted': ['grime', 'weathering', 'shape_damage']},
 'tree': {'requires': ['normal_map', 'roughness_variation', 'colour_variation', 'moss_and_algae', 'dirt'], 'wanted': []},
 'plant': {'requires': ['colour_variation', 'roughness_variation'], 'wanted': []},
 'water': {'requires': ['normal_map'], 'wanted': ['colour_variation']},
 'glass': {'requires': [], 'wanted': ['roughness_variation', 'dirt']},
 'never': {'requires': [], 'wanted': []},
}
DIAL_DEFAULTS = {
    'ground': {'dirt': {'foot_splash': 0.0, 'polish': 0.5, 'film': 0.5}, 'grime': {'soot_under_shelter': 0.0, 'runoff_streaks': 0.0, 'damp_band': 0.0, 'area_share': 0.2},
               'cracks_and_chips': {'chip_amount': 0.0}, 'rubbish': {'density': 0.4}},
    'floor': {'dirt': {'foot_splash': 0.0, 'polish': 0.5}, 'grime': {'soot_under_shelter': 0.0, 'runoff_streaks': 0.0, 'damp_band': 0.0}, 'cracks_and_chips': {'chip_amount': 0.1}},
    'roof': {'dirt': {'foot_splash': 0.0, 'dust': 0.3}, 'grime': {'damp_band': 0.0, 'soot_under_shelter': 0.2}, 'cracks_and_chips': {'chip_amount': 0.1}},
    'iron': {'dirt': {'foot_splash': 0.2}, 'weathering': {'silvering': 0.0, 'patina': 0.3}},
    'stone': {'weathering': {'silvering': 0.0, 'patina': 0.2}},
    'tree': {'weathering': {'silvering': 0.0}},
}
for name_, c in classes.items():
    c['kind'] = KIND; c['source'] = SRC
    c['dial_defaults'] = DIAL_DEFAULTS.get(name_, {})

INDOORS = {'moss_and_algae': 'indoors: dry, nothing grows', 'weathering': 'indoors: no sun or rain on it', 'wetness': 'indoors: dry floor and walls', 'plants': 'indoors: no weeds', 'litter_pieces': 'indoors: swept, no leaves'}

def role(klass, surface, hints, displace=False, may_hang=False, support='ground', span=None, scale=(), dials=None, exempt=None, note=''):
    r = {'class': klass, 'surface': surface, 'displace': displace, 'may_hang': may_hang, 'needs_support': support,
         'max_span_metres': span, 'scale': list(scale), 'dials': dials or {}, 'name_hints': hints, 'exempt': exempt or {}, 'kind': KIND, 'source': SRC}
    if note: r['note'] = note
    return r

roles = {}
# ---- specific first, generic last inside each family (the name-hint matcher takes the first role in this order on a tie)
roles['ground.dirt_road'] = role('ground', 'dirt_road', [r'\broad\b', r'\blane\b', r'\btrack\b', r'cart ?way', r'dirt ?road'], displace=True, dials={'dirt': 1.2, 'rubbish': 0.8, 'moss_and_algae': 0.0}, scale=['cart_gauge'], note='ruts, banks and hoof prints are shaped by the roads step')
roles['ground.mud'] = role('ground', 'mud', [r'\bmud\b', r'mire', r'bog'], displace=True, dials={'wetness': 1.3})
roles['ground.forest_floor'] = role('ground', 'forest_floor', [r'forest ?floor', r'woodland', r'undergrowth', r'leaf ?litter ground'], dials={'moss_and_algae': 1.2})
roles['ground.stone_paving'] = role('ground', 'cobble_paving', [r'paving', r'cobble', r'flagstone', r'\bsett', r'pavement'], dials={'moss_and_algae': 1.1})
roles['ground.gravel'] = role('ground', 'gravel_path', [r'gravel', r'\bpath\b', r'footpath'])
roles['ground.sand'] = role('ground', 'sand', [r'\bsand\b', r'beach', r'dune'])
roles['ground.snow'] = role('ground', 'snow', [r'\bsnow\b'], exempt={'rubbish': 'snow: rubbish would be buried', 'plants': 'snow: nothing grows', 'moss_and_algae': 'snow'})
roles['ground.tarmac'] = role('ground', 'tarmac', [r'tarmac', r'asphalt', r'\btarred'])
roles['ground.concrete'] = role('ground', 'concrete', [r'concrete (ground|slab|yard|floor)', r'\bslab\b', r'apron'])
roles['ground.rock'] = role('ground', 'rock_ore', [r'rock ?ground', r'bedrock', r'\bcliff', r'quarry', r'\bore\b', r'spoil'], displace=True, exempt={'plants': 'bare rock: only a few weeds in cracks, set by the place'})
roles['ground.grass'] = role('ground', 'grass', [r'grass', r'lawn', r'meadow', r'pasture', r'\bfield\b'])
roles['ground.earth'] = role('ground', 'packed_earth', [r'\bground\b', r'terrain', r'\bsoil\b', r'\bearth\b', r'\byard\b'])
roles['floor.earth'] = role('floor', 'packed_earth', [r'earth floor', r'dirt floor', r'stall floor'], dials={'dirt': 1.2})
roles['floor.planks'] = role('floor', 'timber_planks', [r'plank floor', r'wood(en)? floor', r'floorboard'], support='ground')
roles['floor.tile'] = role('floor', 'tile_floor', [r'tile floor', r'tiled floor'])
roles['floor.stone'] = role('floor', 'flagstone', [r'stone floor', r'flag floor'])
roles['floor.concrete'] = role('floor', 'concrete', [r'concrete floor', r'screed'])
roles['floor.carpet'] = role('floor', 'carpet_fabric', [r'carpet', r'\brug\b', r'\bmat\b'])
roles['wall.timber_frame'] = role('wall', 'plaster_lime', [r'timber.?frame', r'half.?timber', r'wattle'], support='ground', scale=['wall_thickness'])
roles['wall.log'] = role('wall', 'log_wall', [r'log ?(wall|cabin|house)', r'\blogs?\b wall'], scale=['wall_thickness'])
roles['wall.stone'] = role('wall', 'stone_rubble', [r'stone ?wall', r'rubble', r'masonry', r'drystone', r'\bgable stone'], dials={'moss_and_algae': 1.1}, scale=['wall_thickness'])
roles['wall.brick'] = role('wall', 'brick', [r'brick'], scale=['wall_thickness'])
roles['wall.cob'] = role('wall', 'cob_wall', [r'\bcob\b', r'adobe', r'mud ?brick'], scale=['wall_thickness'])
roles['wall.concrete'] = role('wall', 'concrete', [r'concrete wall', r'concrete'], scale=['wall_thickness'])
roles['wall.metal_sheet'] = role('wall', 'steel_plate', [r'sheet metal', r'corrugated', r'tin (wall|shed)'], exempt={'moss_and_algae': 'metal sheet: moss does not take', 'bevelled_edges': 'folded sheet, no bevel'})
roles['wall.interior'] = role('wall', 'plaster_lime', [r'interior wall', r'inside wall', r'partition'], exempt=dict(INDOORS), note='indoor wall: the dry-indoors exemptions apply')
roles['wall.plaster'] = role('wall', 'plaster_lime', [r'plaster', r'render', r'daub', r'whitewash', r'\bwall\b', r'\bhouse\b', r'cottage'], scale=['wall_thickness'])
roles['roof.thatch'] = role('roof', 'thatch', [r'thatch', r'\breed\b', r'straw roof'], displace=True, support='part', dials={'moss_and_algae': 1.3}, scale=['roof_pitch', 'thatch_thickness'])
roles['roof.shingle'] = role('roof', 'shingle_wood', [r'shingle', r'\broof\b'], support='part', scale=['roof_pitch'])
roles['roof.tile'] = role('roof', 'roof_tile_clay', [r'roof ?tile', r'\btiles?\b'], support='part', scale=['roof_pitch'])
roles['roof.slate'] = role('roof', 'slate', [r'slate'], support='part', scale=['roof_pitch'])
roles['roof.metal'] = role('roof', 'steel_plate', [r'metal roof', r'tin roof', r'corrugated roof'], support='part', exempt={'moss_and_algae': 'metal roof: moss does not take'})
roles['timber.post'] = role('timber', 'timber_beam', [r'\bposts?\b', r'pillar', r'stanchion', r'upright'], support='ground', scale=['post_size'])
roles['timber.beam'] = role('timber', 'timber_beam', [r'\bbeams?\b', r'rafter', r'joist', r'lintel', r'purlin', r'\bplate\b', r'stringer', r'\bsill\b', r'bearer'], support='part', may_hang=False, span=2.5, scale=['beam_size'])
roles['timber.floor'] = role('timber', 'timber_planks', [r'floor ?plank', r'decking', r'deck\b'], support='part', span=1.38, scale=['plank_width'])
roles['timber.plank'] = role('timber', 'timber_planks', [r'plank', r'board', r'\bslat'], support='part', span=1.38, scale=['plank_width'], dials={'shape_damage': 1.0})
roles['timber.door'] = role('timber', 'timber_planks', [r'\bdoors?\b'], support='part', may_hang=True, scale=['door_height', 'door_width', 'door_thickness'])
roles['timber.shutter'] = role('timber', 'timber_planks', [r'shutter'], support='part', may_hang=True, scale=['shutter_height'])
roles['timber.fence'] = role('timber', 'timber_weathered', [r'fence', r'palisade', r'railing', r'\brail\b', r'\bgates?\b'], support='ground', span=2.5, scale=['fence_height'])
roles['timber.generic'] = role('timber', 'timber_weathered', [r'timber', r'wood(en)?\b', r'\boak\b', r'\bpine\b'], support='part')
roles['stone.footing'] = role('stone', 'stone_rubble', [r'footing', r'plinth', r'foundation', r'padstone', r'sill ?stone'], dials={'moss_and_algae': 1.2})
roles['stone.chimney'] = role('stone', 'stone_rubble', [r'chimney', r'flue', r'stack\b'], support='part', scale=['chimney_height'])
roles['stone.well'] = role('stone', 'stone_rubble', [r'\bwell\b', r'trough', r'\bsink\b'], scale=['well_height'])
roles['stone.rock'] = role('stone', 'stone_rubble', [r'\brocks?\b', r'boulder', r'\bstone\b', r'cairn'], dials={'moss_and_algae': 1.2})
roles['iron.sheet'] = role('iron', 'steel_plate', [r'steel', r'iron sheet', r'\bplate metal', r'girder'], support='part')
roles['iron.painted'] = role('iron', 'painted_metal', [r'painted metal', r'railing iron', r'\bsign\b'], support='part')
roles['iron.fitting'] = role('iron', 'iron_forged', [r'\biron\b', r'hinge', r'\bband\b', r'hoop', r'\bnail', r'bracket', r'latch', r'\bchain\b', r'hook', r'cramp', r'metal'], support='part', may_hang=True, dials={'rust': 1.2})
roles['prop.barrel'] = role('prop', 'timber_planks', [r'barrel', r'\bcask\b', r'keg', r'\btun\b'], scale=['barrel_height'], note='iron bands: give the band material a rule so its slot gets iron.fitting')
roles['prop.crate'] = role('prop', 'timber_planks', [r'crate', r'\bbox\b', r'chest', r'\btrunk\b'], scale=['crate_size'])
roles['prop.cart'] = role('prop', 'timber_weathered', [r'\bcart\b', r'wagon', r'carriage', r'barrow'], scale=['cart_height'])
roles['prop.wheel'] = role('prop', 'timber_weathered', [r'wheel'], scale=['cart_wheel_diameter'])
roles['prop.boat'] = role('prop', 'timber_planks', [r'\bboat\b', r'\bhull\b', r'dinghy', r'\bship\b'], dials={'wetness': 1.2})
roles['prop.furniture'] = role('prop', 'timber_planks', [r'\btable\b', r'\bchair\b', r'\bbench\b', r'\bstool\b', r'shelf', r'\bbed\b', r'cupboard', r'\bdesk\b', r'manger', r'trestle'], scale=['table_height', 'bench_height'])
roles['prop.wicker'] = role('prop', 'wicker', [r'wicker', r'basket', r'\bwattle (fence|panel)'])
roles['prop.cloth'] = role('prop', 'cloth_sack', [r'\bsack', r'cloth', r'canvas', r'sail', r'\brag\b', r'banner', r'tarp'])
roles['prop.rope'] = role('prop', 'rope', [r'\brope', r'\bnet\b', r'cable', r'cordage'], may_hang=True)
roles['prop.ceramic'] = role('prop', 'ceramic_glazed', [r'\bjug\b', r'\bpot\b', r'\burn\b', r'amphora', r'\bbowl\b', r'ceramic', r'crock'])
roles['prop.straw'] = role('prop', 'straw', [r'\bstraw\b', r'\bhay\b', r'bale', r'\bfodder'])
roles['prop.imported'] = role('prop', 'generic_wood', [r'poly ?haven', r'imported', r'\bscan\b'], note='its own maps count as normal_map and roughness_variation when they feed those inputs')
roles['prop.wood'] = role('prop', 'generic_wood', [r'\bprop\b', r'woodpile', r'\blog pile', r'chopping', r'bucket', r'ladder', r'stump block', r'\bblock\b'])
roles['prop.generic'] = role('prop', 'generic_stone', [r'\bobject\b', r'\bthing\b', r'\bmesh\b'], note='the role an object gets when nothing else matched and its material gives no hint (the audit reports every one)')
roles['tree.bark'] = role('tree', 'bark', [r'\btree\b', r'trunk', r'\bbark\b', r'\blog\b', r'branch', r'stump'], scale=['tree_height'])
roles['plant.foliage'] = role('plant', 'foliage', [r'foliage', r'leaves', r'\bleaf', r'bush', r'shrub', r'hedge', r'\bfern', r'canopy', r'needles'])
roles['water.still'] = role('water', 'water_still', [r'\bwater\b', r'pond', r'puddle', r'\blake\b', r'\bpool\b', r'stream', r'\briver\b'], support='none')
roles['water.sea'] = role('water', 'water_sea', [r'\bsea\b', r'\bocean\b', r'harbour water', r'\bwaves?\b'], support='none')
roles['glass.window'] = role('glass', 'glass_old', [r'glass', r'window pane', r'\bpane\b', r'glazing', r'lantern glass'], support='part', may_hang=True, scale=['window_width', 'window_height'])
roles['never.sky'] = role('never', None, [r'^sky', r'backdrop', r'horizon', r'skydome', r'^world'], support='none')
roles['never.glow'] = role('never', None, [r'\bglow\b', r'emitter', r'flame', r'\bfire\b', r'lamp glow', r'light card'], support='none')
roles['never.light'] = role('never', None, [r'^light', r'\blamp helper', r'^sun$'], support='none')
roles['never.helper'] = role('never', None, [r'helper', r'^guide', r'^preview', r'\bcamera', r'^empty', r'^cam ', r'^place .* cam', r'collision', r'proxy'], support='none')
roles['never.scatter'] = role('never', None, [r'^pk scatter', r'scatter', r'^pk litter'], support='none')

# every never role must not demand anything: classes 'never' has empty lists
data = {'about': 'The role table: what each kind of object IS and what treatments it needs. Roles may name example things (thatch, barrel) because this is data, never code. '
                 'A role is "class.name". The class decides which treatments are REQUIRED (the audit fails without them) and which are WANTED (the audit says look). '
                 'Each role carries a surface id (data/surfaces.json), a displace flag (real displacement only where true), may_hang (a part hung from above is allowed), '
                 'needs_support (ground: stands on the ground, part: carried by another part, none), max_span_metres (the longest free span of a plank or beam), '
                 'scale (fact ids in data/real_world_facts.json), dials (multipliers per wear layer, 0 = the layer is not for this role), exempt (treatments the role does not need, with the reason) '
                 'and name_hints (regular expressions that guess the role from an object, collection or material name when the settings say nothing). '
                 'Numbers in a role (max_span_metres, dials) share the role\'s own kind and source. A treatment is REQUIRED only if the kit really makes it and a test proves it (check-presets enforces this).',
        'classes': classes, 'roles': roles}
json.dump(data, open(os.path.join(OUT, 'roles.json'), 'w'), indent=1)

treatments = {
 'about': 'The seventeen treatments the audit looks for (sixteen from the design plus shape_damage), what each one is in plain words, which of the person\'s words it covers, which verb makes it, where the audit reads it, and how a smaller model might skip it and what stops that. made_by names a function (check-presets reads the file and finds it); tested_by names a test file and a phrase the test prints.',
 'treatments': {
  'normal_map': {'plain': 'a real normal map (small bumps and dents) on the surface, pointing the right way', 'persons_words': ['normals'], 'made_by': {'verb': 'surfaces', 'module': 'surfaces/materials.py', 'function': 'give_surfaces'}, 'checked_by': 'materials[].treatments.normal_map and normal_maps[]', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'normal maps are OpenGL'}, 'applies_to': 'all hard surfaces', 'skip_and_stop': 'bump only, a flipped green channel or an sRGB map: the audit reads the wiring and the direction test'},
  'displacement': {'plain': 'real displacement of the surface where the role says (roads, mud, thatch, rock ground), on a dense mesh', 'persons_words': ['displacements'], 'made_by': {'verb': 'surfaces', 'module': 'surfaces/displacement.py', 'function': 'set_displacement'}, 'checked_by': 'materials[].treatments.displacement.detail', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'displacement is set'}, 'applies_to': 'roles with displace true', 'skip_and_stop': 'a Displacement node on a flat plane or with Bump Only: the audit reads method, depth and mesh density'},
  'roughness_variation': {'plain': 'roughness that changes across the surface (not one number)', 'persons_words': ['roughness'], 'made_by': {'verb': 'surfaces', 'module': 'surfaces/materials.py', 'function': 'give_surfaces'}, 'checked_by': 'materials[].treatments.roughness_variation', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'roughness varies'}, 'applies_to': 'all', 'skip_and_stop': 'a constant roughness is read from the Principled node and fails'},
  'colour_variation': {'plain': 'colour that changes across the surface and from object to object', 'persons_words': ['colour variation'], 'made_by': {'verb': 'surfaces', 'module': 'surfaces/materials.py', 'function': 'give_surfaces'}, 'checked_by': 'materials[].treatments.colour_variation', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'colour varies'}, 'applies_to': 'all', 'skip_and_stop': 'a plain colour fails'},
  'bevelled_edges': {'plain': 'edges that are rounded a little (a razor-sharp box edge reads as a computer model)', 'persons_words': ['damage'], 'made_by': {'verb': 'surfaces', 'module': 'surfaces/bevel.py', 'function': 'bevel_objects'}, 'checked_by': 'objects[].geometry.bevel', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'bevel'}, 'applies_to': 'wall, timber, iron', 'skip_and_stop': 'the audit counts plain boxes'},
  'dirt': {'plain': 'dirt: soil film, mud splash at wall feet, dust, polish on worn ground', 'persons_words': ['dirt'], 'made_by': {'verb': 'age', 'module': 'wear/layers/dirt.py', 'function': 'build_dirt'}, 'checked_by': 'materials[].treatments.dirt and objects[].layer_amounts', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'layer dirt'}, 'applies_to': 'all', 'skip_and_stop': 'a layer with amount 0 or a missing pk_dirt_amount fails'},
  'grime': {'plain': 'grime: soot, run-off streaks, damp bands, stains', 'persons_words': ['grime', 'stains'], 'made_by': {'verb': 'age', 'module': 'wear/layers/grime.py', 'function': 'build_grime'}, 'checked_by': 'as dirt', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'layer grime'}, 'applies_to': 'ground, wall, roof, timber, stone', 'skip_and_stop': 'as dirt'},
  'weathering': {'plain': 'weathering: silvering of timber, sun fade, bleaching, patina', 'persons_words': ['weathering'], 'made_by': {'verb': 'age', 'module': 'wear/layers/weathering.py', 'function': 'build_weathering'}, 'checked_by': 'as dirt', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'layer weathering'}, 'applies_to': 'outdoor surfaces', 'skip_and_stop': 'as dirt'},
  'wetness': {'plain': 'wetness: darker, smoother, puddles by depth; dry, damp or wet by state', 'persons_words': ['wetness'], 'made_by': {'verb': 'age', 'module': 'wear/layers/wetness.py', 'function': 'build_wetness'}, 'checked_by': 'as dirt (amount 0 is allowed when the state is dry)', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'layer wetness'}, 'applies_to': 'all outdoor', 'skip_and_stop': 'as dirt'},
  'cracks_and_chips': {'plain': 'cracks and chips painted into the surface (and bump)', 'persons_words': ['cracks', 'damage'], 'made_by': {'verb': 'age', 'module': 'wear/layers/cracks_and_chips.py', 'function': 'build_cracks_and_chips'}, 'checked_by': 'as dirt', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'layer cracks_and_chips'}, 'applies_to': 'hard surfaces', 'skip_and_stop': 'as dirt'},
  'edge_wear': {'plain': 'edge wear: pale rubbed edges and worn corners', 'persons_words': ['damage', 'edge wear'], 'made_by': {'verb': 'age', 'module': 'wear/layers/edge_wear.py', 'function': 'build_edge_wear'}, 'checked_by': 'as dirt', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'layer edge_wear'}, 'applies_to': 'wall, timber, stone, iron, prop', 'skip_and_stop': 'as dirt'},
  'moss_and_algae': {'plain': 'moss and algae where it is damp and shady, never on trodden or kept-clear ground', 'persons_words': ['moss'], 'made_by': {'verb': 'age', 'module': 'wear/layers/moss_and_algae.py', 'function': 'build_moss_and_algae'}, 'checked_by': 'as dirt', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'layer moss_and_algae'}, 'applies_to': 'walls, roofs, stone, tree, ground (wanted)', 'skip_and_stop': 'as dirt; indoors it is allowed off with a reason'},
  'rust': {'plain': 'rust on iron: height bands, collars at joins, runs below', 'persons_words': ['weathering'], 'made_by': {'verb': 'age', 'module': 'wear/layers/rust.py', 'function': 'build_rust'}, 'checked_by': 'as dirt', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'layer rust'}, 'applies_to': 'iron', 'skip_and_stop': 'as dirt'},
  'rubbish': {'plain': 'rubbish: muck and litter marks at gutters, wall feet and lane edges, never on the crown', 'persons_words': ['rubbish'], 'made_by': {'verb': 'age', 'module': 'wear/layers/rubbish.py', 'function': 'build_rubbish'}, 'checked_by': 'as dirt', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'layer rubbish'}, 'applies_to': 'ground', 'skip_and_stop': 'as dirt'},
  'plants': {'plain': 'weeds, tufts, ferns, nettles and moss cushions as small 3D pieces, off the wheel tracks and out of puddles', 'persons_words': ['weeds', 'moss'], 'made_by': {'verb': 'grow', 'module': 'growth/scatter.py', 'function': 'scatter_plants'}, 'checked_by': 'scatter.groups[] counts and keep-out counts', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'plants kept out'}, 'applies_to': 'outdoor ground', 'skip_and_stop': 'the audit counts pieces per 100 square metres and the roots inside keep-out (must be 0)'},
  'litter_pieces': {'plain': 'leaves, sticks, straw, pine needles, dung lumps as small 3D pieces', 'persons_words': ['rubbish'], 'made_by': {'verb': 'grow', 'module': 'growth/scatter.py', 'function': 'scatter_litter'}, 'checked_by': 'scatter.groups[]', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'plants kept out'}, 'applies_to': 'outdoor ground', 'skip_and_stop': 'as plants'},
  'shape_damage': {'plain': 'damage as SHAPE: boards that bow, corners that chip, no two parts alike (what read at film size in the garden)', 'persons_words': ['damage'], 'made_by': {'verb': 'damage', 'module': 'surfaces/damage.py', 'function': 'damage_objects'}, 'checked_by': 'objects[].geometry.shape_damage and siblings', 'tested_by': {'file': 'test_place_blender.py', 'phrase': 'shape damage'}, 'applies_to': 'timber, roof, stone (wanted for wall, prop)', 'skip_and_stop': 'the audit lists siblings of one role that are exact copies'},
 },
 'object_checks': {'uv': 'an object under a normal-mapped material has a UV layer and few mirrored faces', 'carried': 'the part is carried from the ground up (construction check)', 'scale_ok': 'the size fits the real-world facts table'},
 'persons_words_map': {'normals': ['normal_map'], 'displacements': ['displacement'], 'dirt': ['dirt'], 'grime and stains': ['grime'], 'weeds': ['plants'], 'weathering': ['weathering', 'rust'], 'damage': ['cracks_and_chips', 'edge_wear', 'bevelled_edges', 'shape_damage'],
                       'moss': ['moss_and_algae', 'plants'], 'wetness': ['wetness'], 'rubbish': ['rubbish', 'litter_pieces'], 'cracks': ['cracks_and_chips'], 'edge wear': ['edge_wear']},
}
json.dump(treatments, open(os.path.join(OUT, 'treatments.json'), 'w'), indent=1)

banned = {'about': 'Words that name a kind of PLACE. No file of kit code under kit/place-kit/place_kit may contain one (check-presets and test_place_data.py scan for them), so the kit works for any place. Material words (thatch, plaster, timber) are allowed in code; data files and examples may use any word.',
          'banned_nouns': ['village', 'town', 'harbour', 'harbor', 'mine', 'farm', 'garden', 'interior', 'forest', 'cottage', 'stable', 'street', 'courtyard', 'hamlet', 'city'],
          'allowed_where': ['data/', 'data/examples/', 'data/place_types/']}
json.dump(banned, open(os.path.join(OUT, 'banned_place_nouns.json'), 'w'), indent=1)
print('roles', len(roles))
