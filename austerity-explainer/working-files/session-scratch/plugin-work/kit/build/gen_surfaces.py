"""Builds kit/place-kit/data/surfaces.json (scratch generator; the output is the data)."""
import json, os
OUT = '/home/user/Music/plugins/explainer-film/kit/place-kit/data'
GARDEN = 'the garden character job strengths (log 31)'
MINE = 'the coal mine yard depths'
COOK = 'the texture cookbook relief tests'
STREET = 'the wet street recipe'
INV = 'the plugin 1.4.0 design: a first try, judge by looking'

def E(value, unit, kind, source):
    return {'value': value, 'unit': unit, 'kind': kind, 'source': source}

# id: label, recipe, tile_m, uv, grain, strength (value, kind, source), depth_m or None, rough low, high, map?, palette, bevel, dials, polyhaven, note
rows = [
 ('dirt_road', 'packed dirt road, clods and a few big dark patches', 'earth_clods', 2.0, 'planar', 'v', 0.9, 'judged', GARDEN + ' ground 1.0, softened for ruts', 0.06, 0.85, 0.95, ['#6e5b45', '#5c4a38', '#7b6850', '#4f4233'], None, {}, 'brown_mud_dry', 'a 2 m tile; soft clods blurred 1 to 2 px at 2048'),
 ('packed_earth', 'trodden earth, a little drier', 'earth_clods', 2.0, 'planar', 'v', 0.8, 'judged', GARDEN, 0.03, 0.8, 0.95, ['#78664f', '#695842', '#86735a'], None, {}, 'brown_mud_02', ''),
 ('mud', 'wet mud with slick patches', 'earth_clods', 2.0, 'planar', 'v', 1.0, 'judged', GARDEN, 0.06, 0.3, 0.7, ['#4a3b2c', '#3d3125', '#574634'], None, {'wetness': 1.3}, 'brown_mud', 'roughness about 0.3 where wet'),
 ('forest_floor', 'needles, leaf litter and moss on soil', 'earth_clods', 2.0, 'planar', 'v', 1.0, 'judged', GARDEN, 0.04, 0.85, 0.95, ['#4e4631', '#5b4f35', '#3f3a29', '#675a3c'], None, {}, 'forrest_ground_01', ''),
 ('grass', 'short grass over soil (a ground picture; tufts are separate pieces)', 'soft_noise', 2.0, 'planar', 'v', 1.0, 'judged', GARDEN, None, 0.8, 0.95, ['#5f6b3a', '#4f5c30', '#6f7a45'], None, {}, 'leafy_grass', ''),
 ('gravel_path', 'gravel path', 'gravel_bits', 1.5, 'planar', 'v', 1.0, 'judged', GARDEN, 0.04, 0.7, 0.95, ['#8a8070', '#766d5f', '#9b917f'], None, {}, 'gravel_embedded', 'mine gravel depth 4'),
 ('cobble_paving', 'rounded stones in joints', 'cobbles', 1.5, 'planar', 'v', 0.9, 'judged', GARDEN + ' stone 0.8 to 1.0', 0.03, 0.6, 0.9, ['#7a756c', '#6a665f', '#8b857a'], None, {}, 'cobblestone_01', 'joints darker, duller and sloped (street lesson)'),
 ('flagstone', 'big flat stones', 'stone_blocks', 2.0, 'planar', 'v', 0.9, 'judged', GARDEN, None, 0.6, 0.9, ['#857f75', '#736e65', '#968f84'], None, {}, None, ''),
 ('timber_weathered', 'old silvered timber with grain and checks', 'planks_grain', 1.0, 'plank', 'v', 1.5, 'judged', GARDEN + ' planks 1.5', None, 0.65, 0.9, ['#7a6b58', '#6a5d4c', '#8c7f6b', '#5a4e40'], [0.006, 0.012], {}, None, 'u along the length, v across'),
 ('timber_planks', 'plank boards', 'planks_grain', 1.0, 'plank', 'v', 1.5, 'judged', GARDEN + ' planks 1.5', None, 0.6, 0.85, ['#7d6347', '#6b5239', '#8c7152'], [0.006, 0.012], {}, None, 'mirror or rotate some planks'),
 ('timber_beam', 'square timber beams and posts', 'planks_grain', 1.0, 'plank', 'v', 1.2, 'judged', GARDEN, None, 0.6, 0.85, ['#5b4630', '#4b3a28', '#6a5339'], [0.006, 0.012], {}, None, ''),
 ('log_wall', 'round logs', 'log_bark', 1.0, 'plank', 'v', 1.2, 'judged', GARDEN, None, 0.7, 0.9, ['#6a5238', '#5a4430', '#7a6044'], [0.008, 0.015], {}, None, ''),
 ('wattle_and_daub', 'plaster over woven sticks', 'plaster_blotch', 1.5, 'box', 'v', 1.0, 'judged', GARDEN + ' plaster 1.0', None, 0.75, 0.95, ['#b8a98a', '#a89977', '#c4b79a'], [0.008, 0.015], {}, 'clay_plaster', ''),
 ('plaster_lime', 'lime plaster', 'plaster_blotch', 1.5, 'box', 'v', 1.0, 'judged', GARDEN + ' plaster 1.0', None, 0.75, 0.95, ['#c9bda5', '#bab092', '#d6ccb5'], [0.008, 0.015], {}, 'clay_plaster', ''),
 ('cob_wall', 'earth walls', 'plaster_blotch', 1.5, 'box', 'v', 1.0, 'judged', GARDEN, None, 0.8, 0.95, ['#9a8666', '#8a7656', '#a9966f'], [0.008, 0.015], {}, None, ''),
 ('stone_rubble', 'rough fitted stones', 'stone_blocks', 1.5, 'box', 'v', 0.9, 'judged', GARDEN + ' stone 0.8 to 1.0', None, 0.6, 0.9, ['#8a857b', '#76726a', '#9b968a', '#6a665e'], [0.008, 0.015], {}, 'castle_wall_slates', ''),
 ('stone_dressed', 'cut stone blocks', 'stone_blocks', 1.5, 'box', 'v', 0.8, 'judged', GARDEN, None, 0.55, 0.85, ['#9a948a', '#85807a'], [0.008, 0.015], {}, None, ''),
 ('thatch', 'bunched straw or reed, ridges down the slope', 'thatch_bunches', 1.5, 'box', 'v', 1.0, 'judged', GARDEN + ' roof 0.9, plus the design: x 0.6 when displacement is on', 0.05, 0.85, 0.95, ['#8a7646', '#74633a', '#9a8554', '#5c4e30'], None, {}, 'thatch_roof_angled', 'displacement 4 to 6 cm near the camera'),
 ('shingle_wood', 'wooden shingles in rows', 'shingle_rows', 1.0, 'box', 'v', 0.9, 'judged', GARDEN + ' roof tile 0.9', None, 0.7, 0.9, ['#6f5a43', '#5f4d39', '#7e6a50'], None, {}, None, ''),
 ('roof_tile_clay', 'clay roof tiles', 'tile_rows', 1.0, 'box', 'v', 0.9, 'judged', GARDEN + ' roof tile 0.9', None, 0.55, 0.85, ['#a05a3a', '#8d4d30', '#b06a46'], None, {}, 'clay_roof_tiles', 'UV on the prototype tile'),
 ('slate', 'slate roof', 'tile_rows', 1.0, 'box', 'v', 0.9, 'judged', GARDEN, None, 0.5, 0.8, ['#4d5258', '#42474d', '#5a6066'], None, {}, 'castle_wall_slates', ''),
 ('iron_forged', 'dark forged iron', 'iron_pits', 0.5, 'box', 'v', 0.8, 'judged', MINE + ' metal 1.6', None, 0.45, 0.8, ['#3a3a3c', '#2e2e30', '#48484b'], [0.004, 0.008], {'rust': 1.2}, None, ''),
 ('rope', 'twisted rope', 'rope_twist', 0.5, 'plank', 'v', 0.8, 'invented', INV, None, 0.8, 0.95, ['#a08a62', '#8a7650'], None, {}, None, ''),
 ('straw', 'loose straw', 'straw_strands', 1.0, 'planar', 'v', 0.8, 'invented', INV, None, 0.8, 0.95, ['#c2a85e', '#b09650', '#d0b86e'], None, {}, None, ''),
 ('hay', 'packed hay', 'straw_strands', 1.0, 'box', 'v', 0.8, 'invented', INV, None, 0.85, 0.95, ['#b8a258', '#a69048'], None, {}, None, ''),
 ('wicker', 'woven basket cane', 'fabric_weave', 0.5, 'box', 'v', 1.0, 'invented', INV, None, 0.7, 0.9, ['#9a7a4a', '#866a3e'], None, {}, None, ''),
 ('cloth_sack', 'coarse cloth', 'fabric_weave', 0.5, 'box', 'v', 0.7, 'invented', INV, None, 0.85, 0.95, ['#b0a080', '#9a8c6e'], None, {}, None, ''),
 ('leather', 'worn leather', 'soft_noise', 0.5, 'box', 'v', 0.7, 'invented', INV, None, 0.5, 0.8, ['#5a3d2a', '#4a3222'], None, {}, None, ''),
 ('ceramic_glazed', 'glazed clay', 'soft_noise', 0.5, 'box', 'v', 0.4, 'invented', INV, None, 0.25, 0.6, ['#8a5a3c', '#6e4a30'], None, {}, None, ''),
 ('bark', 'rough bark', 'log_bark', 1.0, 'box', 'v', 0.9, 'judged', GARDEN + ' bark 0.9', None, 0.8, 0.95, ['#4a3d30', '#3b3026', '#58493a'], None, {}, 'bark_brown_01', ''),
 ('foliage', 'leaf cards', 'soft_noise', 0.5, 'box', 'v', 0.4, 'invented', INV, None, 0.6, 0.85, ['#4a6a35', '#3b5a2b', '#5b7a40'], None, {}, None, ''),
 ('water_still', 'still water with a gentle swell', 'wave_swell', 4.0, 'planar', 'v', 0.3, 'invented', INV, None, 0.05, 0.25, ['#2c3b36', '#26332f'], None, {}, None, 'roughness low'),
 ('water_sea', 'open water with swell', 'wave_swell', 8.0, 'planar', 'v', 0.4, 'invented', INV, None, 0.05, 0.3, ['#26454f', '#1f3a44'], None, {}, None, ''),
 ('glass_old', 'old glass with smudges', 'soft_noise', 0.5, 'box', 'v', 0.2, 'invented', INV, None, 0.1, 0.35, ['#9db0ac', '#8ca09c'], None, {}, None, ''),
 ('brick', 'fired brick in courses', 'brick_courses', 1.5, 'box', 'v', 1.0, 'judged', MINE + ' brick 3', None, 0.65, 0.9, ['#8a4a36', '#7a3f2e', '#9a5640'], [0.008, 0.015], {}, 'brick_moss_001', ''),
 ('concrete', 'poured concrete', 'plaster_blotch', 2.0, 'box', 'v', 0.9, 'invented', INV, None, 0.7, 0.92, ['#8e8d88', '#7d7c77', '#9c9b96'], [0.008, 0.015], {}, None, ''),
 ('tarmac', 'laid tarmac', 'gravel_bits', 2.0, 'planar', 'v', 0.9, 'invented', INV, None, 0.75, 0.95, ['#3a3a3a', '#2e2e2e', '#464646'], None, {}, None, ''),
 ('sand', 'sand with ripples', 'sand_ripples', 2.0, 'planar', 'v', 0.8, 'invented', INV, 0.02, 0.85, 0.95, ['#c2ad82', '#b09b72', '#d0bc92'], None, {}, None, ''),
 ('snow', 'snow', 'soft_noise', 2.0, 'planar', 'v', 0.6, 'invented', INV, None, 0.5, 0.8, ['#e6eaee', '#d4dae0'], None, {}, None, ''),
 ('rock_ore', 'rock or ore ground', 'rock_facets', 2.0, 'box', 'v', 1.0, 'judged', MINE + ' slate and gravel 4', 0.04, 0.6, 0.9, ['#55524c', '#45423d', '#66635b'], None, {}, None, ''),
 ('steel_plate', 'steel plate', 'iron_pits', 1.0, 'box', 'v', 0.8, 'judged', MINE + ' metal 1.6', None, 0.4, 0.75, ['#6a6e72', '#585c60', '#7a7e82'], [0.004, 0.008], {'rust': 1.0}, None, ''),
 ('painted_metal', 'painted metal', 'iron_pits', 1.0, 'box', 'v', 0.6, 'invented', INV, None, 0.35, 0.7, ['#3f5a6a', '#34495a'], [0.004, 0.008], {'rust': 0.8}, None, ''),
 ('tile_floor', 'floor tiles', 'tile_rows', 1.0, 'planar', 'v', 0.7, 'invented', INV, None, 0.4, 0.8, ['#9a6a4a', '#8a5c3e'], None, {}, None, ''),
 ('carpet_fabric', 'carpet and heavy cloth', 'fabric_weave', 0.5, 'planar', 'v', 0.6, 'invented', INV, None, 0.9, 0.98, ['#6a3a3a', '#5a2e2e'], None, {}, None, ''),
 ('generic_wood', 'any wood (fallback)', 'planks_grain', 1.0, 'box', 'v', 1.2, 'judged', GARDEN, None, 0.65, 0.9, ['#7a6246', '#665038', '#8a7050'], [0.006, 0.012], {}, None, 'fallback'),
 ('generic_stone', 'any stone (fallback)', 'stone_blocks', 1.5, 'box', 'v', 0.9, 'judged', GARDEN, None, 0.6, 0.9, ['#8a857b', '#76726a', '#9b968a'], [0.008, 0.015], {}, None, 'fallback'),
 ('generic_metal', 'any metal (fallback)', 'iron_pits', 0.5, 'box', 'v', 0.8, 'judged', MINE, None, 0.4, 0.8, ['#5a5a5c', '#4a4a4c'], [0.004, 0.008], {}, None, 'fallback'),
 ('generic_cloth', 'any cloth (fallback)', 'fabric_weave', 0.5, 'box', 'v', 0.7, 'invented', INV, None, 0.85, 0.95, ['#a89a7a', '#8f8264'], None, {}, None, 'fallback'),
]
surfaces = {}
for (sid, label, recipe, tile, uv, _v, strength, skind, ssrc, depth, rlow, rhigh, palette, bevel, dials, polyhaven, note) in rows:
    e = {'label': label, 'height_recipe': recipe, 'tile_metres': E(tile, 'metres', 'judged' if skind == 'judged' else 'invented', COOK + ' tile sizes' if skind == 'judged' else INV),
         'uv_method': uv, 'grain_axis': 'u' if uv == 'plank' else None,
         'normal_strength': E(strength, 'Normal Map strength', skind, ssrc),
         'displacement_depth_metres': E(depth, 'metres', 'judged' if depth else 'invented', MINE + ' and the design') if depth else None,
         'roughness': {'low': E(rlow, 'roughness', 'judged' if skind == 'judged' else 'invented', STREET if rlow in (0.3, 0.9) else INV), 'high': E(rhigh, 'roughness', 'judged' if skind == 'judged' else 'invented', INV), 'map': 'height'},
         'colour': {'palette': E(palette, 'sRGB hex colours', 'invented', INV), 'variation': {'per_object': E(0.08, 'share of value', 'invented', INV), 'macro_scale_metres': E(3.0, 'metres', 'invented', INV)}},
         'bevel_metres': E(bevel, 'metres', 'judged', GARDEN) if bevel else None,
         'dials': dials, 'polyhaven': polyhaven, 'real_scale_note': note}
    surfaces[sid] = e
data = {'about': 'One entry per surface id: a recipe that makes a material. Every number is {value, unit, kind, source}; check-presets fails an entry without kind and source. '
                 'height_recipe names a function in place_kit/surfaces/heights.py (soft large shapes, nothing under about 5 mm). tile_metres is the real size of one picture repeat. '
                 'uv_method: box (one box mapping in metres), planar (from above), plank (u along the length, v across, random offset per plank). '
                 'normal_strength is the Normal Map node strength (multiplied by 0.6 where displacement is on). displacement_depth_metres is used only for roles with displace true. '
                 'Most values are first tries marked judged (from the garden and mine work) or invented; judge by looking.',
        'surfaces': surfaces}
json.dump(data, open(os.path.join(OUT, 'surfaces.json'), 'w'), indent=1)
print(len(surfaces))
