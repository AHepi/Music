"""What this file does (plain words): collects the key numbers of this step from the other number files into one file, numbers/stage_result.json (so they can be found in one place). Run: python3 -I tools/write_result_json.py"""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
J = lambda n: json.load(open(P('numbers', n)))
b, a = J('stage_measurements_before.json'), J('stage_measurements_after.json')
real = J('diagnosis_real_stage.json'); joints = J('joints_in_stage.json'); noch = J('no_change_proof.json'); chg = J('change_where_asked.json'); sc = J('sky_and_colour.json')
pv = lambda d, n: d['plate_view_stage_against_painting'][n]
res = {
 'note': 'key numbers of the stage step, all from the files in this folder; "before" = the film\'s stage as it is, "after" = with the brightness fix (look.toe = 1 and frame edge 0.25 in the lockout look)',
 'road_arrives_over_painted_plate_view': {'first_test_wet_painting_before': 0.748, 'first_test_film_dry_painting_before': 0.924, 'new_wet_painting_before': pv(b, 'new_wet_front_painting')['road_stage_over_painting'], 'new_wet_painting_after': pv(a, 'new_wet_front_painting')['road_stage_over_painting'],
                                          'film_dry_painting_before': pv(b, 'film_dry_painting')['road_stage_over_painting'], 'film_dry_painting_with_the_fix_switched_on': pv(a, 'film_dry_painting')['road_stage_over_painting']},
 'new_wet_painting_by_part_before_and_after': {k: [pv(b, 'new_wet_front_painting')[k], pv(a, 'new_wet_front_painting')[k]] for k in ('road_far_third_over_painting', 'road_middle_third_over_painting', 'road_near_third_over_painting', 'road_dark_parts_over_painting_(painted_0.08_to_0.22)',
                       'road_dots_painted_over_0.08_but_arriving_under_0.03_(crushed_to_black)', 'walls_stage_over_painting', 'whole_picture_mean_stage', 'share_of_dots_brighter_than_0.97_in_the_stage')},
 'why_(real_stage,_road_arrives_over_painted,_new_wet_painting)': {k: v['road_arrives'] for k, v in real.items() if k.startswith('diagnosis/') and not k.startswith('diagnosis/dry')},
 'colour_and_sky': sc, 'joints_in_stage': joints, 'existing_scenes_not_asked_for': noch, 'where_asked_for': chg,
 'dry_looking_patches_first_test_method': {'old_dry_behind_before': b['dry_behind_patches_old_dry_behind'], 'new_wet_behind_before': b['dry_behind_patches_new_wet_behind'], 'old_dry_behind_after': a['dry_behind_patches_old_dry_behind'], 'new_wet_behind_after': a['dry_behind_patches_new_wet_behind']},
 'where_the_behind_painting_is_worn': {'before': {k: b[k] for k in b if k.startswith('where_the_behind')}, 'after': {k: a[k] for k in a if k.startswith('where_the_behind')}},
 'moved_view_road_mean': {n: [b['moved_view'][n]['road_mean'], a['moved_view'][n]['road_mean']] for n in b['moved_view']},
}
json.dump(res, open(P('numbers/stage_result.json'), 'w'), indent=1)
print('written numbers/stage_result.json')
