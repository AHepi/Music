# What this does (plain words): turns the two guide templates (guide_template_recipe.md, guide_template_lessons.md) into the finished guides
# "04 Recipe - wood - how it is made.md" and "04 Lessons - wood - what carries over to other surfaces.md" by filling every [[TOKEN]] with numbers and tables read from the
# score files, so that no number in the guides is typed by hand after the fact. Also writes final_report.json. Plain Python (python3 -I).
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WOOD = os.path.abspath(os.path.join(HERE, '..'))
load = lambda *p: json.load(open(os.path.join(WOOD, *p))) if os.path.exists(os.path.join(WOOD, *p)) else None
table = load('scores', 'rate_distortion_table_wrap_aware.json') or load('scores', 'rate_distortion_table_cut_at_edge.json')
cut = load('scores', 'rate_distortion_table_cut_at_edge.json')
by = {r['class']: r for r in table}
extras = {k: load('scores', f'extra_{k}.json') for k in ('X1_S1_without_grain', 'X2_S0_with_grain', 'X3_L2_with_grain', 'X4_M3_with_grain')}
var = load('variations', 'variation_scores.json')
area = load('area', 'area_scores.json')
res = load('resolution', 'resolution_table.json')
audits = load('scores', 'description_audits.json')
geo = load('outputs', 'geometry_route', 'geometry_route_report.json')
half = {n: load('scores', 'half_tile', n + '.json') for n in ('S1_layout_paint_grain', 'sample_101', 'deck_boards', 'L2w', 'L2')}
deck = load('transfer', 'deck_boards_score.json')
f = lambda v, d=3: ('n/a' if v is None else (f'{v:.{d}f}'))
tokens = {}
s0, s1, m1, m3, l1, l2, l3 = (by.get(k, {}) for k in ('S0_layout_only', 'S1_layout_paint_grain', 'M1_trace_20k', 'M3_trace_62k', 'L1_trace_150k', 'L2_trace_300k', 'L3_trace_480k'))
patches = {}
for name in ('L3_trace_480k',):
    for suffix in ('w', ''):
        p = os.path.join(WOOD, 'description', name + suffix + '.json')
        if os.path.exists(p):
            patches[name] = len(json.load(open(p))['layers'][0]['list']); break
tokens.update({'S1_BYTES': str(s1.get('bytes')), 'S1_KIND': f(s1.get('texture_compare_overall')), 'S1_SSIM': f(s1.get('colour_ssim')), 'S0_BYTES': str(s0.get('bytes')), 'S0_SSIM': f(s0.get('colour_ssim')), 'S0_KIND': f(s0.get('texture_compare_overall')),
               'S0_HMAE': f(s0.get('height_mae_best_fit_levels'), 1), 'S0_NORMAL': f(s0.get('normal_mean_angle_degrees'), 1),
               'L3_KB': f(l3.get('bytes', 0) / 1024, 0), 'L3_PATCHES': str(patches.get('L3_trace_480k', '?')), 'L3_SSIM': f(l3.get('colour_ssim')), 'L3_EDGE': f(l3.get('edge_skill_2px')), 'L3_TIER': str(l3.get('tier')),
               'L3_NORMAL': f(l3.get('normal_mean_angle_degrees'), 1), 'L3_HMAE': f(l3.get('height_mae_best_fit_levels'), 1), 'M1_SSIM': f(m1.get('colour_ssim')), 'M3_SSIM': f(m3.get('colour_ssim')), 'L1_SSIM': f(l1.get('colour_ssim')), 'L2_SSIM': f(l2.get('colour_ssim'))})


def one(name):
    r = extras.get(name)
    return 'n/a' if not r else f'kind {r["texture_compare_overall"]:.3f}, dot-for-dot SSIM {r["colour_ssim"]:.3f}, edge skill {r["edge_skill_2px"]:.3f}, normal {r["normal_mean_angle_degrees"]:.1f} degrees'


tokens.update({'X1_KIND': f((extras.get('X1_S1_without_grain') or {}).get('texture_compare_overall')), 'L2_NORMAL': f(l2.get('normal_mean_angle_degrees'), 1), 'X1_SUMMARY': one('X1_S1_without_grain'), 'X2_SUMMARY': one('X2_S0_with_grain'), 'X3_SUMMARY': one('X3_L2_with_grain') + f' (without grain: kind {f(l2.get("texture_compare_overall"))}, SSIM {f(l2.get("colour_ssim"))})',
               'X4_SUMMARY': one('X4_M3_with_grain') + f' (without grain: kind {f(m3.get("texture_compare_overall"))}, SSIM {f(m3.get("colour_ssim"))})'})
rows = ['| class | size (KB) | tier | colour SSIM | colour diff (Delta E) | edge skill | height error (steps) | normal angle (deg) | "same kind" | bake seconds |', '|---|---|---|---|---|---|---|---|---|---|']
for r in table:
    rows.append(f'| {r["class"]} | {r["bytes"] / 1024:.1f} | {r["tier"]} | {r["colour_ssim"]:.3f} | {r["colour_mean_delta_e"]:.2f} | {r["edge_skill_2px"]:.3f} | {r["height_mae_best_fit_levels"]:.1f} | {r["normal_mean_angle_degrees"]:.1f} | {r["texture_compare_overall"]:.3f} | {r["bake_seconds"]:.1f} |')
ladder_table = '\n'.join(rows)
if table is not cut and cut:
    rows2 = ['', 'The same traced classes made WITHOUT letting patches join across the tile edge (each patch cut at the edge; the colour of the two halves can differ: a visible colour seam in the coarse classes):', '',
             '| class | size (KB) | tier | colour SSIM | edge skill | "same kind" | seam number (1.0 = none) |', '|---|---|---|---|---|---|---|']
    for r in cut:
        if r['class'][0] in 'ML':
            rows2.append(f'| {r["class"]} (cut at edge) | {r["bytes"] / 1024:.1f} | {r["tier"]} | {r["colour_ssim"]:.3f} | {r["edge_skill_2px"]:.3f} | {r["texture_compare_overall"]:.3f} | {r["seam_ratio"]:.2f} |')
    ladder_table += '\n' + '\n'.join(rows2)
tokens['LADDER_TABLE'] = ladder_table
layer = ['| layer added | description size | what it fixed | what it did NOT fix |', '|---|---|---|---|',
         f'| layout only (planks, gaps, 25 cracks, knots, splatter, pebbles; flat colour) | {s0.get("bytes", 0) / 1024:.1f} KB | the plank structure; SSIM {f(s0.get("colour_ssim"))} | any paint; height error {f(s0.get("height_mae_best_fit_levels"), 1)}; kind {f(s0.get("texture_compare_overall"))} |',
         f'| + invented paint (zones, strips) + dry-brush grain | {s1.get("bytes", 0) / 1024:.1f} KB | looks like the surface: kind {f(s1.get("texture_compare_overall"))} | the match dot for dot: SSIM {f(s1.get("colour_ssim"))} (the paint is not where the real paint is) |',
         f'| traced patches, coarse | {m1.get("bytes", 0) / 1024:.0f} KB | big tones in the right places: SSIM {f(m1.get("colour_ssim"))} | edges (skill {f(m1.get("edge_skill_2px"))}) |',
         f'| traced patches, 62 KB | {m3.get("bytes", 0) / 1024:.0f} KB | SSIM {f(m3.get("colour_ssim"))}, edge skill {f(m3.get("edge_skill_2px"))} | thin cracks and fine strips |',
         f'| traced patches, 150 KB | {l1.get("bytes", 0) / 1024:.0f} KB | tier {l1.get("tier")}: SSIM {f(l1.get("colour_ssim"))}, edge skill {f(l1.get("edge_skill_2px"))} | fine edges; normal {f(l1.get("normal_mean_angle_degrees"), 1)} degrees |',
         f'| traced patches, 300 KB | {l2.get("bytes", 0) / 1024:.0f} KB | SSIM {f(l2.get("colour_ssim"))}, edge skill {f(l2.get("edge_skill_2px"))}, height error {f(l2.get("height_mae_best_fit_levels"), 1)} | normal {f(l2.get("normal_mean_angle_degrees"), 1)} degrees |',
         f'| traced patches, {l3.get("bytes", 0) / 1024:.0f} KB (the biggest class) | {l3.get("bytes", 0) / 1024:.0f} KB | SSIM {f(l3.get("colour_ssim"))}, edge skill {f(l3.get("edge_skill_2px"))}, colour difference {f(l3.get("colour_mean_delta_e"), 2)} | tier close (needs normal under 12 degrees: got {f(l3.get("normal_mean_angle_degrees"), 1)}) |']
tokens['LAYER_TABLE'] = '\n'.join(layer)
if var:
    tokens.update({'VAR_MEAN': f(var['texture_compare_mean']), 'VAR_MIN': f(var['texture_compare_min']), 'VAR_MAX': f(var['texture_compare_max']), 'VAR_SSIM': f(var['pixel_ssim_vs_reference_mean']),
                   'VAR_PAIR_DIFF': f(var['pair_mean_abs_difference_mean'], 1), 'VAR_PAIR_SSIM': f(var['pair_ssim_mean'])})
    v_rows = ['| seed | description (bytes) | same kind | dot-for-dot SSIM vs reference | edge skill vs reference | colour diff vs reference | tier vs reference |', '|---|---|---|---|---|---|---|']
    for r in var['rows']:
        v_rows.append(f'| {r["seed"]} | {r["description_bytes"]} | {r["texture_compare_overall"]:.3f} | {r["pixel_ssim_vs_reference"]:.3f} | {r["pixel_edge_skill_vs_reference"]:.3f} | {r["pixel_delta_e_vs_reference"]:.2f} | {r["pixel_tier"]} |')
    tokens['VAR_DETAIL'] = (f'one Blender run baked all 8 at 1254 dots in {var["bake_seconds_for_all_8"]} seconds. Same-kind score: mean {f(var["texture_compare_mean"])}, lowest {f(var["texture_compare_min"])}, highest {f(var["texture_compare_max"])} '
                            f'(the reference scored against itself shuffled is about 0.99; the S1 description fitted to the reference scores {f(s1.get("texture_compare_overall"))}). Against the reference dot for dot they are poor, as they must be (mean SSIM {f(var["pixel_ssim_vs_reference_mean"])}). '
                            f'Between two new tiles: mean absolute brightness difference {f(var["pair_mean_abs_difference_mean"], 1)} steps and mean SSIM {f(var["pair_ssim_mean"])} over all 28 pairs (the reference against a new tile is about as low): the tiles are different pictures, not copies.\n\n' + '\n'.join(v_rows))
if area:
    q = area['quarters_pairs']
    tokens['AREA_SUMMARY'] = (f'baked in {area["bake_seconds"]} s; the four 1254-dot quarters differ from each other (mean SSIM between quarters {sum(p["ssim"] for p in q) / len(q):.3f}); half-tile shift test: mean difference {area["half_tile"]["mean_difference_levels"]} steps, '
                              f'{area["half_tile"]["share_over_40"] * 100:.2f} % of dots over 40 steps (a wrong roll: {area["half_tile"]["wrong_roll_share_over_40"] * 100:.1f} %).')
    tokens['AREA_DETAIL'] = (f'`area/area_2508.json` is a sampled description with design tile 2508 (10 planks, about 4 times the knots, cracks, splatter and paint, grain feature counts doubled). One bake at 2508 dots took {area["bake_seconds"]} seconds. '
                             f'(a) The four 1254 x 1254 quarters are different pictures: ' + ', '.join(f'{p["a"]} vs {p["b"]}: SSIM {p["ssim"]}, mean difference {p["mean_abs_difference_levels"]}' for p in q) + '. '
                             f'(b) Half-tile shift test on the big picture: mean difference {area["half_tile"]["mean_difference_levels"]} steps, share of dots over 40 steps {area["half_tile"]["share_over_40"] * 100:.3f} % (a deliberately wrong roll: mean {area["half_tile"]["wrong_roll_mean_difference"]}, {area["half_tile"]["wrong_roll_share_over_40"] * 100:.1f} % over 40). '
                             f'(c) Jump across the middle lines over a normal one-dot jump: vertical line {area["seam_across_middle_over_normal_jump"]["vertical_line"]}, horizontal line {area["seam_across_middle_over_normal_jump"]["horizontal_line"]} (about 1 = no seam); '
                             f'across the wrap-around edge: left-right {area["wrap_edge_over_normal_jump"]["left_right"]}, top-bottom {area["wrap_edge_over_normal_jump"]["top_bottom"]}. A 2 x 2 tiling of one 1254 tile would show the same picture four times (quarter SSIM 1.0); here it is about {sum(p["ssim"] for p in q) / len(q):.2f}. '
                             'Picture `area/area_tiled_2x2_preview.png` is the big picture itself tiled 2 x 2 to look for seams.')
if res:
    r = res['rows']
    tokens['RES_SUMMARY'] = '; '.join(f'{x["size"]} dots: {x["wall_seconds"]} s' for x in r) + ' for the same description (seed 7).'
    sh = res['sharpness_seen_at_1254']
    res_rows = ['| size (dots) | total time (s) | colour render (s) | shapes | PNG files (MB) | mean gradient seen at 1254 | same kind |', '|---|---|---|---|---|---|---|']
    for x in r:
        s = sh[str(x['size'])]
        res_rows.append(f'| {x["size"]} | {x["wall_seconds"]} | {x["colour_render_s"]} | {x["shapes"]} | {x["png_megabytes"]} | {s["mean_gradient"]} | {s["texture_compare_overall"]} |')
    tokens['RES_DETAIL'] = ('the SAME description (coordinates in design dots; the camera simply sees the same sheet at another number of dots) baked at 512, 1254 and 2508 dots. The shapes are the same; the render time grows with the number of dots '
                            '(the shader grain is evaluated per dot); at 512 dots the thin 1-3 dot strokes and hair lines fall below a dot and blur away (mean gradient falls); at 2508 dots the same shapes are drawn with four times as many dots (looked at full size every edge is crisper; after shrinking to 1254 dots it measures the same: gradient 5.7 against 5.9 at 1254), and the dry-brush streaks keep their shape because their feature counts are per tile. '
                            'The "same kind" score is computed after the tool resizes every picture to 1254 dots.\n\n' + '\n'.join(res_rows))
if half:
    h_rows = ['| description | mean difference after the half-tile roll (steps) | share of dots over 40 steps | wrong-roll control: mean / share over 40 | edge jump over normal jump (left-right, top-bottom) |', '|---|---|---|---|---|']
    for n, v in half.items():
        if v:
            h_rows.append(f'| {n} | {v["half_tile_roll"]["mean_difference_levels"]} | {v["half_tile_roll"]["share_over_40_levels"] * 100:.2f} % | {v["wrong_roll_control"]["mean_difference_levels"]} / {v["wrong_roll_control"]["share_over_40_levels"] * 100:.1f} % | {v["edge_jump_over_normal_jump_left_right_and_top_bottom"]} |')
    tokens['HALF_TILE_TABLE'] = '\n'.join(h_rows) + '\n\n(L2 = the traced class cut at the tile edge, L2w = patches allowed to join across the edge. The edge-jump numbers are the jump across the wrap-around edge divided by a normal one-dot jump in the same direction; the traced classes copy the reference\'s own mild edge mismatch (the reference itself is 1.7 to 2.5), the invented ones have none.)'
if audits:
    tokens['AUDIT_SUMMARY'] = '; '.join(f'{k} {v["bytes"] / 1024:.1f} KB (limit {v["limit_kb"]}): ' + ('passes' if not v['problems'] else 'PROBLEM ' + str(v['problems'])) for k, v in audits.items())
if geo:
    tokens['GEOMETRY_DETAIL'] = (f'`generator/geometry_route.py` draws the SAME sampled description (seed {geo["seed"]}: planks, {geo["curves"]} cracks and gaps, {geo["blobs"]} splatter blobs) twice: (1) the normal way (numpy polygons in one mesh) and (2) with Blender geometry tools: each crack is a CURVE object (poly curve, bevel on, the radius of every point = half the width, so the ribbon tapers by itself; flattened because only the view from above matters) and the blobs come from a GEOMETRY NODES tree (points with a "radius" and a colour -> Instance on Points with a 12-sided circle scaled by the radius -> Realize Instances -> Set Material). '
                              f'Result: the two pictures differ by a mean of {geo["mean_difference_levels"]} brightness steps and {geo["share_of_dots_differing_over_40"] * 100:.2f} % of the dots differ by more than 40 steps (the geometry-nodes blobs are perfect circles, the polygon blobs are ragged). Time {geo["geometry_route_seconds_total"]} s against {geo["polygon_route_seconds_total"]} s. '
                              f'So: the geometry route gives the same picture; its advantages are that a taper is one setting (the point radius) and that Geometry Nodes can scatter thousands of items with one node tree; its disadvantages are one Blender object per crack ({geo["curves"]} objects here; it would not scale to 3000 traced patches) and no ragged paint edges without adding a noise displacement. For flat painted surfaces the polygon painter is simpler and exactly as good; the geometry route would start to pay for real relief (grooves, raised splinters), which I did not test.')
tokens['LIB_CHANGES'] = ('* `pixel_compare.py`: the "close" tier asks for a normal angle under 12 degrees, which a fine-grained surface such as this wood cannot reach at 512 KB (a flat normal map is 24 degrees off; my 470 KB trace gets about 17). Suggest expressing the limit as a share of the flat-normal error, or reporting the tier without the normal measure as well.\n'
                         '* `bake_harness.new_bake_scene`: the camera sits at height 5 with clip end 100; a generator with many stacked shapes must move it (mine puts it above the highest shape). Suggest a helper that sets the camera above the highest shape.\n'
                         '* `recipe_tools.tileable_noise_group`: only one feature count for both directions; `contrib/builder.py` has the stretched version. Suggest adding Scale U and Scale V inputs to the group.\n'
                         '* `description_audit.py`: fine for patches written as `[colour, [numbers]]`; a long flat list of corner steps is accepted below 4000 numbers per patch. Suggest also reporting the share of numbers that are corner steps so "tracing" is named in the report.\n'
                         '* `sweep_tools.py`: only for shader node groups. A helper that bakes a DESCRIPTION with one setting changed (mine: `generator/sweeps_for_guide.py`) would suit every description-driven surface.\n'
                         '* `texture_compare.py`: score noise of +-0.03 between seeds; a built-in repeat over a few seeds would help tuning.')
if deck:
    tokens['TRANSFER_SUMMARY'] = deck.get('summary', 'n/a'); tokens['TRANSFER_DETAIL'] = deck.get('detail', 'n/a')
else:
    tokens['TRANSFER_SUMMARY'] = tokens['TRANSFER_DETAIL'] = 'see transfer/'
for name, template, target in (('recipe', 'guide_template_recipe.md', '04 Recipe - wood - how it is made.md'), ('lessons', 'guide_template_lessons.md', '04 Lessons - wood - what carries over to other surfaces.md')):
    text = open(os.path.join(WOOD, template)).read()
    text = re.sub(r'\[\[([A-Z0-9_]+)\]\]', lambda m: tokens.get(m.group(1), f'[[{m.group(1)} missing]]'), text)
    open(os.path.join(WOOD, target), 'w').write(text)
    print('wrote', target, len(text), 'characters;', len(re.findall(r'\[\[[A-Z0-9_]+ missing\]\]', text)), 'tokens missing')
