"""Adds the place_* sections to kit/film-settings.json (run once; safe to run again: it replaces those sections)."""
import json, sys
PATH = '/home/user/Music/plugins/explainer-film/kit/film-settings.json'
d = json.load(open(PATH))

def E(value, unit, kind, source, **more):
    e = {'value': value, 'unit': unit, 'kind': kind, 'source': source}
    e.update(more)
    return e

GARDEN = 'the garden character job (procedural-textures/garden/character, log 31)'
STREET = 'the wet street work (procedural-textures/street_wet, logs 18 and 22)'
MINE = 'the coal mine yard (mine-scene/modules/ground_and_yard.py)'
COOK = 'the texture cookbook (procedural-textures/cookbook)'
WEAR = 'the weathering kit re-check (procedural-textures kits/weathering, log 25)'
PLAN = 'the plugin 1.4.0 design (22 October 2026)'

place_surfaces = {
 'about': 'The surface pass of the place kit: map sizes, normal-map checks, displacement, bevels and how repeats are hidden. Read by place_kit/surfaces and the audit.',
 'map_size_pixels': E(1024, 'pixels a side', 'judged', GARDEN + ': the garden check wanted 1024 and more'),
 'map_size_near_camera_pixels': E(2048, 'pixels a side', 'judged', COOK + ': height pictures blurred 1 to 2 px at 2048'),
 'map_size_quick_pixels': E(256, 'pixels a side', 'judged', PLAN + ': a trial size for this slow machine; a final built from it fails the audit'),
 'normal_map_size_min_pixels': E(1024, 'pixels a side', 'judged', GARDEN + ': normal-map check (1024 px)'),
 'normal_strength_with_displacement_factor': E(0.6, 'times the normal strength', 'judged', MINE + ': normal strength x 0.6 where displacement is on (decision D7, not yet proved by a picture of ours)'),
 'steepest_one_percent_tilt_degrees': E([26, 34], 'degrees', 'judged', GARDEN + ': wood_maps.calibrate_height'),
 'height_blur_pixels_at_2048': E([1, 2], 'pixels', 'judged', COOK + ': soft clods, no micro pores'),
 'smallest_feature_metres': E(0.005, 'metres', 'judged', GARDEN + ': style note, nothing under about 5 mm'),
 'normal_blue_mean_min': E(0.85, 'share of 1', 'judged', GARDEN + ': nm_struct.py'),
 'normal_red_green_mean_band': E([0.47, 0.53], 'share of 1', 'judged', GARDEN + ': nm_struct.py'),
 'normal_direction_correlation_min': E(0.25, 'correlation', 'judged', GARDEN + ': nm_dir.py (a real map read +0.55 to +0.87)'),
 'normal_slope_energy_min': E(0.02, 'mean absolute slope of the map on that axis', 'invented', PLAN + ': a map with less slope on one axis says nothing about that axis, so that axis is reported "not informative" (the garden plank map had almost no X slope)'),
 'normal_maps_per_material_max': E(4, 'pictures', 'judged', GARDEN + ': nm_struct.py'),
 'bump_leftover_strength_max': E(0.3, 'strength', 'judged', GARDEN + ': a leftover Bump above 0.3 not fed by the Normal Map fights it'),
 'uv_mirrored_face_share_max': E(0.02, 'share of faces', 'judged', GARDEN + ': uv_check.py'),
 'displacement_dicing_rate_pixels': E([1, 2], 'pixels', 'measured', COOK + ': relief tests'),
 'displacement_mesh_edge_metres_max': E(0.3, 'metres', 'invented', PLAN + ': a mesh with longer edges is "coarse" for displacement unless it is subdivided'),
 'displacement_graded_grid_near_metres': E(0.12, 'metres', 'judged', MINE + ': graded grid near the camera'),
 'displacement_graded_grid_growth': E(1.09, 'times a step', 'judged', MINE + ': graded grid'),
 'displacement_graded_grid_far_metres': E(5.0, 'metres', 'judged', MINE + ': graded grid'),
 'bevel_metres': {
   'wall': E([0.008, 0.015], 'metres', 'judged', GARDEN + ': builder briefs'),
   'trim': E(0.006, 'metres', 'judged', GARDEN + ': builder briefs'),
   'plank': E([0.006, 0.012], 'metres', 'judged', GARDEN + ': wood_geo.py chamfer'),
 },
 'repeat_hiding': {
   'second_scale': E(0.79, 'times the first scale', 'judged', COOK + ': repeat breaker'),
   'offset': E([0.37, 0.58], 'tile fractions', 'judged', COOK + ': repeat breaker'),
   'blend_noise_scale': E(0.17, 'noise scale', 'judged', COOK + ': repeat breaker'),
 },
 'roughness_dry_wet': {
   'dry': E(0.9, 'roughness', 'measured', STREET + ': wet recipe, dry sett roughness about 0.9'),
   'wet': E(0.3, 'roughness', 'measured', STREET + ': wet recipe, wet roughness about 0.3'),
 },
 'glb_surfaces_fail_share': E(0.5, 'share of triangle area', 'invented', PLAN + ': model_lint --surfaces fails a .glb when more than this share of its area has no normal map, constant roughness and no vertex colours'),
}

place_audit = {
 'about': 'What the place audit (place_audit_check.py) allows. Thresholds live here, never in the code; the audit only gathers facts (D2 of the 1.4.0 design).',
 'unknown_role_objects_allowed': E(0, 'objects', 'judged', PLAN + ': every visible mesh gets a role'),
 'fallback_role_share_max': E(0.10, 'share of objects', 'invented', PLAN + ': objects the kit could only give a fallback role (prop.generic); more than this is a look, far more a fail'),
 'fallback_role_share_fail': E(0.5, 'share of objects', 'invented', PLAN + ': above this share the roles say nothing'),
 'required_treatments_missing_allowed': E(0, 'treatments', 'judged', PLAN + ': decision D3'),
 'layer_amount_zero_needs_reason': E(True, 'rule', 'judged', PLAN + ': a layer with amount 0 and no off entry fails'),
 'plain_box_share_max': E(0.15, 'share of objects', 'invented', PLAN + ': objects that are plain six-sided boxes with no bevel'),
 'off_share_max': E(0.25, 'share of required role-and-treatment pairs', 'invented', PLAN + ': more off entries than this is a look; each off entry is reported as KNOWN with its reason'),
 'quick_allowed_for_final': E(False, 'rule', 'judged', PLAN + ': output made with --quick is for trials only'),
 'layer_amount_floor_by_look': {
   'kept': E(0.15, 'amount', 'judged', WEAR + ': a layer with an amount this small does nothing a viewer can see'),
   'lived_in': E(0.25, 'amount', 'judged', WEAR),
   'neglected': E(0.40, 'amount', 'judged', WEAR),
   'derelict': E(0.50, 'amount', 'judged', WEAR),
 },
 'plants_min_per_100_square_metres': E(20, 'pieces', 'invented', PLAN + ': weeds and tufts per 100 square metres of ground (the street calibration: about 1 percent cover)'),
 'litter_min_per_100_square_metres': E(30, 'pieces', 'invented', PLAN + ': leaves, straw, sticks, dung lumps per 100 square metres of ground'),
 'triangles_total_max': E(6000000, 'triangles', 'judged', GARDEN + ': the card draws 1.5 million per builder comfortably'),
 'triangles_per_builder_max': E(1500000, 'triangles', 'judged', GARDEN + ': builder brief'),
 'scatter_pieces_max': E(400000, 'pieces', 'invented', PLAN + ': a cap so a scatter cannot fill the memory'),
 'draw_seconds_final_max': E(90, 'seconds', 'judged', GARDEN + ': final draw time cap'),
 'card_memory_gigabytes_max': E(12, 'gigabytes', 'judged', GARDEN + ': card memory cap'),
}

place_construction = {
 'about': 'The construction check: every visible part carried from the ground up, nothing floating, sizes and doorways. Numbers from the garden bridge checks.',
 'touch_metres': E(0.005, 'metres', 'judged', GARDEN + ': struct.py touching'),
 'overlap_centimetres_min': E(4, 'centimetres', 'judged', GARDEN + ': a joined member overlaps its carrier by at least this'),
 'rest_patch_square_centimetres_min': E(16, 'square centimetres', 'judged', GARDEN + ': struct.py rest patch'),
 'rest_patch_reach_millimetres': E(8, 'millimetres', 'judged', GARDEN + ': struct.py rest patch'),
 'float_gap_millimetres_fail': E(5, 'millimetres', 'judged', GARDEN + ': a gap over this is floating'),
 'z_fight_gap_millimetres': E(1, 'millimetres', 'judged', GARDEN + ': coplanar faces closer than this fight'),
 'support_span_metres_max': E(1.38, 'metres', 'judged', GARDEN + ': no plank span between supports over 1.4 m'),
 'ground_seat_metres_tolerance': E(0.02, 'metres', 'invented', PLAN + ': how far above or below the ground an object seated on it may be'),
 'doorway_floor_gap_metres_max': E(0.30, 'metres', 'invented', PLAN + ': a doorway needs a floor within this below the sill (the coal-mine engine house had a door onto nothing)'),
 'walk_ray_step_metres': E(0.05, 'metres', 'judged', GARDEN + ': walk rays'),
 'walk_step_metres_max': E(0.02, 'metres', 'judged', GARDEN + ': walk rays'),
 'walk_slope_max': E(0.05, 'rise over run', 'judged', GARDEN + ': walk rays'),
 'peg_seat_millimetres': E(1, 'millimetres', 'judged', GARDEN + ': seat.py pegs'),
 'inside_out_parts_allowed': E(0, 'parts', 'judged', 'Scenario skills test on the street (73 inside-out parts found by hand-free checks), log 23'),
 'sample_spacing_metres': E(0.02, 'metres', 'judged', GARDEN + ': struct.py samples'),
 'parts_checked_max': E(4000, 'parts', 'invented', PLAN + ': above this the check samples fewer rays a part and says so'),
}

place_scale = {
 'about': 'The scale check: sizes against real-world numbers (data/real_world_facts.json plus the place\'s own facts).',
 'warn_factor': E(1.0, 'times the range', 'judged', PLAN + ': outside the range is a look'),
 'fail_factor': E(1.5, 'times the range', 'invented', PLAN + ': beyond 1.5 times the range (or under 1/1.5) fails; a door 1.0 m high fails'),
}

place_wear = {
 'about': 'Wear: where it may go, how much, how big. The exact-zero gates and budgets are measured on the street and the painted plates.',
 'exact_zero_gate_footfall': E(0.6, 'mask 0..1', 'measured', WEAR + ': growth gates (nothing grows on a worn track)'),
 'exact_zero_gate_crown': E(0.7, 'mask 0..1', 'measured', WEAR + ': growth gates'),
 'exact_zero_gate_keepclear': E(0.5, 'mask 0..1', 'measured', WEAR + ': growth gates'),
 'plants_in_puddles_allowed': E(0, 'plants', 'measured', WEAR + ': above_water gate'),
 'litter_clearance_metres': E(0.05, 'metres', 'measured', WEAR + ': litter_dist'),
 'rubbish_on_crown_allowed': E(0, 'pieces', 'measured', STREET + ': rubbish mask'),
 'grime_area_share': E(0.25, 'share of an area', 'measured', STREET + ': more than a quarter is mush'),
 'grime_darkening_share': E(0.33, 'share darker', 'measured', STREET),
 'darkest_mark_min': E(0.10, 'luminance 0..1', 'measured', 'the painted plates (procedural-textures kits/weathering, log 25)'),
 'mark_surround_min': E(0.18, 'luminance 0..1', 'measured', 'the painted plates (log 25)'),
 'mark_dots_marks_size': E(5, 'picture dots', 'measured', 'the painted plates (log 25): marks 5 dots at contrast 0.08'),
 'mark_dots_marks_contrast': E(0.08, 'luminance', 'measured', 'the painted plates (log 25)'),
 'mark_dots_lines_size': E(3, 'picture dots', 'measured', 'the painted plates (log 25): lines 3 dots at contrast 0.11'),
 'mark_dots_lines_contrast': E(0.11, 'luminance', 'measured', 'the painted plates (log 25)'),
 'mark_dots_patches_size': E(15, 'picture dots', 'measured', 'the painted plates (log 25): patches 15 dots at contrast 0.04'),
 'mark_dots_patches_contrast': E(0.04, 'luminance', 'measured', 'the painted plates (log 25)'),
 'plan_mask_cell_metres': E(0.10, 'metres', 'judged', PLAN + ': decision D4 (the lighter masks are not tested anywhere yet)'),
 'plan_mask_cell_metres_quick': E(0.5, 'metres', 'judged', PLAN + ': decision D4'),
 'plan_mask_cells_across_max': E(1500, 'cells', 'judged', 'the critic\'s review of the design: cell = max(0.10, extent / 1500)'),
 'plan_mask_time_budget_seconds': E(120, 'seconds', 'invented', PLAN + ': a mask run slower than this is reported, not hidden'),
 'wall_foot_height_metres': E(0.45, 'metres', 'judged', STREET + ': stone plinths 15 to 46 cm high hid a wall-foot band measured from the ground; measure it from each object\'s own lowest point'),
 'puddle_depth_shares': E([0.40, 0.40, 0.20], 'shares', 'judged', STREET + ': wetness layer puddles by depth'),
 'shape_damage_bow_per_length_max': E(0.012, 'share of the length', 'judged', GARDEN + ': planks bow, cup and twist a little (wood_geo.py)'),
 'shape_sibling_min_count': E(4, 'objects', 'judged', GARDEN + ': varied planks and tiles'),
 'shape_sibling_copy_share_max': E(0.5, 'share of siblings', 'invented', PLAN + ': siblings of one role that are exact copies (same mesh and size)'),
 'ground_relief_metres_min': E(0.03, 'metres', 'invented', MINE + ': the yard ruts were 4 to 9 cm deep; a road with less relief than this reads flat'),
 'rut_depth_metres': E([0.05, 0.15], 'metres', 'invented', MINE + ': yard ruts 4 to 9 cm; deeper for an unkept lane'),
 'cart_gauge_metres': E([1.2, 1.5], 'metres', 'judged', PLAN + ': from memory, confirm in the facts table'),
 'hoof_dimple_spacing_metres': E([0.8, 1.0], 'metres', 'invented', PLAN),
}

place_measures = {
 'about': 'Picture measures (calculators/picture_measures.py): value range, detail energy, flat windows, palette, squint. Thresholds from the garden character round.',
 'percentile_tolerance': E(0.03, 'luminance', 'judged', GARDEN + ': finish_character.py measures'),
 'percentile_99_max': E(0.92, 'luminance', 'judged', GARDEN + ': finish_character.py'),
 'mean_saturation_tolerance': E(0.04, 'saturation', 'judged', GARDEN + ': finish_character.py'),
 'detail_energy_blur_pixels': E(2, 'pixels', 'judged', GARDEN + ': finish_character.py'),
 'detail_energy_ratio_low': E(0.9, 'times the guard', 'judged', GARDEN + ': finish_character.py'),
 'detail_energy_ratio_high': E(1.4, 'times the guard', 'judged', GARDEN + ': finish_character.py'),
 'detail_energy_cap': E(10, 'energy', 'judged', GARDEN + ': finish_character.py'),
 'squint_blur_pixels': E(12, 'pixels', 'judged', GARDEN + ': squint_regions.py'),
 'squint_window_pixels': E(6, 'pixels', 'judged', GARDEN + ': squint_regions.py'),
 'squint_target': E(0.92, 'similarity', 'judged', GARDEN + ': the garden missed it at 0.883 and 0.873'),
 'flat_window_pixels': E(96, 'pixels', 'judged', GARDEN + ': finish_character.py'),
 'flat_window_step_pixels': E(48, 'pixels', 'judged', GARDEN + ': finish_character.py'),
 'flat_window_std_max': E(0.010, 'luminance spread', 'judged', GARDEN + ': finish_character.py'),
 'flat_window_share_under_0_014_max': E(0.02, 'share of windows', 'judged', GARDEN + ': finish_character.py'),
 'strong_saturation_level': E(0.70, 'saturation', 'judged', GARDEN + ': finish_character.py'),
 'strong_saturation_share_max': E(0.01, 'share of pixels', 'judged', GARDEN + ': finish_character.py'),
 'turquoise_hue_band': E([160, 210], 'degrees', 'judged', GARDEN + ': finish_character.py'),
 'turquoise_saturation_min': E(0.35, 'saturation', 'judged', GARDEN + ': finish_character.py'),
 'turquoise_share_max': E(0.003, 'share of pixels', 'judged', GARDEN + ': finish_character.py'),
 'white_patch_pixels_max': E(30, 'pixels', 'judged', GARDEN + ': finish_character.py'),
 'silhouette_iou_min': E(0.85, 'overlap', 'judged', GARDEN + ': sil_iou.py (two yardsticks disagreed)'),
 'light_group_sum_error_max': E(0.02, 'share', 'measured', GARDEN + ': light groups sum to the picture'),
 'reading_test_share_min': E(0.75, 'share of features', 'judged', GARDEN + ': never run blind before; 12 of 16'),
}

place_render = {
 'about': 'Drawing places: the renderer rule (Cycles where lights are lit, EEVEE when they are off), picture sizes and the rented-card limits. Prices carry the date they were read.',
 'renderer_rule': E('Cycles for views where lamps, windows, lanterns or fires are lit; EEVEE when they are off', 'rule', 'judged', 'the film owner\'s rule of 21 October 2026 (procedural-textures project story)'),
 'preview_size_pixels': E([1200, 800], 'pixels', 'measured', 'the rented-card runs: previews 6 to 10 s (RunPod set-up findings)'),
 'preview_samples': E(96, 'samples', 'measured', 'the rented-card runs (RunPod set-up findings)'),
 'close_up_size_pixels': E([1600, 1067], 'pixels', 'judged', 'the garden light job'),
 'final_size_pixels': E([2400, 1600], 'pixels', 'measured', 'the rented-card runs: 44.3 s and 39.7 s on an RTX 4090'),
 'final_samples': E(512, 'samples', 'measured', 'the rented-card runs'),
 'eevee_shadow_rays': E(4, 'rays', 'measured', 'the wet street (white speckle on wet ground was soft shadows, not the material)'),
 'eevee_shadow_steps': E(16, 'steps', 'measured', 'the wet street'),
 'eevee_samples': E(48, 'samples', 'measured', 'the wet street'),
 'job_minutes_max': E(55, 'minutes', 'measured', 'the rented-card guide: keep each job under about an hour'),
 'jobs_waiting_stop_minutes': E(5, 'minutes', 'judged', 'the film owner\'s rule: if jobs wait this long while workers show idle, stop and report'),
 'preview_download_kilobytes_max': E(400, 'kilobytes', 'judged', 'the rented-card guide: bring back small JPG previews only'),
 'disk_free_gigabytes_stop_here': E(0.4, 'gigabytes', 'measured', 'this machine\'s disk during the 1.4.0 build (2.7 GB free and shared)'),
 'card_dollars_per_hour': E(1.10, 'US dollars an hour', 'measured', 'the rented-card guide (an RTX 4090 on a pay-per-second endpoint)', date_read='2026-10-22',
                            note='A price shown on the day, not a bill: one bill came out 2.5 times the work seconds and was never explained, so never promise a cost from seconds alone.'),
 'workers_max': E(3, 'workers', 'judged', 'the rented-card guide: a usual set-up; the person sets their own'),
 'local_cycles_preview_size_pixels': E([320, 240], 'pixels', 'judged', 'this machine: Cycles takes 35 to 90 s a frame on 4 cores, so local pictures stay tiny'),
}

place_light = {
 'about': 'Starting values for the light verb (sun, sky, fill and lit lamps). They are a first try, not tuned: judge by looking.',
 'sun_strength': E(3.5, 'watts per square metre', 'invented', PLAN + ': a bright but not blown-out day sun'),
 'sky_strength': E(0.8, 'world strength', 'invented', PLAN),
 'clip_share_max': E(0.005, 'share of pixels', 'judged', 'the Scenario lighting skill: value study clip under 0.5 percent'),
 'sun_elevation_degrees': E(35, 'degrees', 'judged', 'the garden light job (golden hour low sun)'),
}

place_checks = {
 'about': 'How the fresh checkers work (workflow build-a-place).',
 'fix_rounds': E(1, 'rounds', 'judged', 'the garden job: one fix round, then stop'),
 'checkers_see_builder_reports': E(False, 'rule', 'judged', 'the garden job: a checker recomputes claims without the builders\' numbers'),
 'claims_recheck': E(True, 'rule', 'judged', 'the garden job: builders\' claims were wrong three times out of three'),
}

for name, section in (('place_surfaces', place_surfaces), ('place_audit', place_audit), ('place_construction', place_construction),
                      ('place_scale', place_scale), ('place_wear', place_wear), ('place_measures', place_measures),
                      ('place_render', place_render), ('place_light', place_light), ('place_checks', place_checks)):
    d[name] = section
with open(PATH, 'w') as f:
    f.write(json.dumps(d, indent=1, ensure_ascii=True) + '\n')
print('written', PATH)
