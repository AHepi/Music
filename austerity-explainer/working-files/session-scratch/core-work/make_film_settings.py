"""Builds kit/film-settings.json (the core helper's sections) and merges it into the file already there, keeping any
section another builder added. Scratch tool for the core helper; not shipped.
Use: python3 -I make_film_settings.py [--write]
"""
import json
import os
import sys
from collections import OrderedDict

OUT = '/home/user/Music/plugins/explainer-film/kit/film-settings.json'
KIT = 'film-kit'   # sources are written relative to the project (austerity-explainer/...)
RS = 'scratchpad redesign'   # the redesign rounds' scratch folder (log 34)


def e(value, unit, kind, source, **more):
    entry = OrderedDict([('value', value), ('unit', unit), ('kind', kind), ('source', source)])
    entry.update(more)
    return entry


def M(value, unit, source, **more):
    return e(value, unit, 'measured', source, **more)


def J(value, unit, source, **more):
    return e(value, unit, 'judged', source, **more)


def I(value, unit, source, **more):
    return e(value, unit, 'invented', source, **more)


def section(about, **entries):
    s = OrderedDict([('about', about)])
    s.update(entries)
    return s


S = OrderedDict()
S['about'] = ('The film\'s house numbers, in one table that every calculator (kit/calculators) and tool reads, so the tools '
              'cannot drift apart. Read it with kit/calculators/settings.py (python3 settings.py show SECTION). Built from the '
              'inventory of 423 hand-found values (log 35, scratchpad plugin-calculators/inventory-and-design.json) and checked '
              'against the project\'s files. Sources name the austerity-explainer project\'s files: film-kit/... is the film kit, '
              'notes/... the project notes, "scratchpad redesign/..." the redesign rounds\' working folder of log 34.')
S['entry_format'] = ('Every number is {"value", "unit", "kind", "source"} (some add "note"). A section may hold groups of '
                     'entries. Keys read with dots: frame.width_pixels. Builders add their own section (with an "about" line); '
                     'they never change another section\'s numbers without saying so.')
S['kinds'] = OrderedDict([
    ('measured', 'the project measured it (a recording, a render, a bill, a fit to a picture): change it only by measuring again'),
    ('judged', 'a person or a helper chose it by looking or by a rule of thumb: change it only after looking again'),
    ('invented', 'nobody has tested it yet: a starting point; say so whenever a result rests on it'),
])

# ------------------------------------------------------------------------------------------------ frame and lenses
S['frame'] = section(
    'The film frame, the plate (the 3D picture the painter repaints) and the lenses.',
    width_pixels=J(1080, 'pixels', 'Decision for phone screens (a tall 9:16 frame); notes/Decisions.md chapter 1; every page and tool'),
    height_pixels=J(1920, 'pixels', 'as width_pixels'),
    frames_per_second=J(30, 'frames a second', 'film-kit/narration-tools/assemble_chapter_narration.py FRAMES_PER_SECOND; estimate_timeline.py'),
    film_vertical_fov_degrees=M(60.4, 'degrees, top to bottom', 'Fitted to the liked picture\'s landmarks in log 31 (experiments/31 .../tools/match_camera.py), '
                                'then kept as the house film lens: assemble_notice_corner.py, assemble_works.py FILM_FOV (line 176), assemble_people_test.py'),
    plate_vertical_fov_degrees=J(64.4, 'degrees, top to bottom', 'Film lens + 4 degrees (log 30 plan; lesson 90): assemble_works.py PLATE_FOV, notice-corner-camera.json fov'),
    plate_lens_extra_degrees=J(4.0, 'degrees', 'Lesson 90 (a 44-degree plate over a 40-degree film lens allowed only about 1 degree of turn); log 30 plan'),
    plate_width_pixels=J(1536, 'pixels', 'Notice corner and people test plates (1.42 times the film frame); notice-corner-paintings.json, people-test-paintings.json'),
    plate_height_pixels=J(2730, 'pixels', 'as plate_width_pixels'),
    painting_returned_size_pixels=M([1504, 2672], 'pixels [width, height]', 'What Flux 3 edit returns at "2k" (people-test-paintings.json returned_size, '
                                    '16 October 2026); resized up to the plate, so the painting\'s real detail is 2672 rows over the plate\'s view',
                                    note='The slide-magnification limit is worked out from this height (skeptic, log 35), not from the plate\'s 2730.'),
    plate_frame_edge_fade_share=J(0.03, 'share of the frame', 'film-kit/paper-film/scenes/projected-set.js frameEdge default (line 562); log 29'),
    blender_to_three_axes=J('three.js (x, y, z) = Blender (x, z, -y)', 'axes', 'Every camera file\'s "about" line (works-camera-w1.json); notice-corner.js fromBlender'),
)

# ------------------------------------------------------------------------------------------------ the camera
S['camera'] = section(
    'Where the camera stands, how it may move, and how a filmed camera path is judged (camera_audit.py).',
    eye_height_range_metres=J([1.5, 1.9], 'metres above the surface under the camera', 'check_shot.py eye_height default (line 478); lessons 100, 105; rule 2',
                              note='A standing person. Overview views from a window measure from that floor (W3 check file eye_height_note).'),
    eye_height_default_metres=J(1.7, 'metres', 'assemble_works.py views (eye_height_metres 1.7); plan 34'),
    eye_height_fix_margin_metres=J(0.05, 'metres', 'check_shot.py line 484 (a fix aims 0.05 inside the range)'),
    level_tolerance_degrees=J(0.5, 'degrees of tilt or lean', 'check_shot.py line 200 (camera-level)'),
    meeting_point_gap_share_of_width=J(0.03, 'share of the frame width', 'Rule 1; check_shot.py check_lines (line 940); lesson 98'),
    meeting_point_drift_during_slide_share_of_width=J(0.02, 'share of the frame width', 'Rule 11 (07 Composing a shot.md lines 125-134); log 30'),
    turn_during_a_slide_degrees=J(0.0, 'degrees', 'Rule 11 and lessons 99, 106-107: a slide never turns; only position is keyframed'),
    reference_lines_tolerance_share=J(0.03, 'share of the frame', 'check_shot.py check_reference_lines (lines 659-693); lesson 105'),
    reference_match_tolerances=J({'height_metres': 0.1, 'sideways_metres': 0.15, 'turn_degrees': 0.75, 'lens_degrees': 2.0}, 'metres and degrees',
                                 'check_shot.py check_camera_match line 584'),
    reference_match_search_steps=J({'x_metres': 0.3, 'height_metres': 0.3, 'turn_degrees': 1.5, 'lens_degrees': 4.0}, 'metres and degrees',
                                   'check_shot.py line 570 (Nelder-Mead start steps)'),
    reference_landmarks_minimum=J(5, 'landmarks', 'Lesson 105 (fit the camera to 5 or more landmarks before moving any prop)'),
    reference_size_ratio_tolerance=J(0.15, 'ratio', 'check_shot.py check_camera_distance lines 647-656 (needs 4 props, 75% agreeing)'),
    moves_per_shot_max=J(3, 'named moves', 'The user\'s rule (decision 25, log 20); cinema-kit.js stillShot'),
    audit_turn_limit_degrees_per_second=J(0.6, 'degrees a second', 'film-kit/paper-film/tools/camera_audit.py TURN_LIMIT (line 23); tuned on chapter 2\'s 21 shots'),
    audit_travel_limit_share_per_second=J(0.012, 'share of the distance to the focus, a second', 'camera_audit.py TRAVEL_LIMIT (line 24); lesson 58'),
    audit_lens_limit_share_per_second=J(0.012, 'share of the lens angle, a second', 'camera_audit.py LENS_LIMIT (line 25)'),
    audit_join_gap_seconds=J(0.35, 'seconds', 'camera_audit.py JOIN_GAP (line 26)'),
    audit_cut_jump_share=J(0.25, 'share of the distance to the target', 'camera_audit.py CUT_JUMP (line 27)'),
    audit_cut_turn_degrees=J(8.0, 'degrees', 'camera_audit.py CUT_TURN (line 28)'),
    audit_naming_thresholds=J({'pan_degrees': 2.5, 'zoom_travel_share': 0.08, 'zoom_lens_share': 0.06, 'move_up_down_share': 0.08,
                               'slide_share': 0.12, 'still_share_of_shot_min': 0.25}, 'degrees and shares', 'camera_audit.py describe() and audit()'),
    slide_length_range_metres=J([0.43, 1.5], 'metres', 'Plan 34 moves table; notice corner 1.5 m; W1/W2 1.2 m'),
    slide_seconds_range=J([2.6, 4.1], 'seconds', 'Plan 34 lines 604-621 (slides start and stop on words)'),
    slides_per_page_max=J(1, 'slides', 'Plan 34 (the user\'s limit is three moves a shot; built sets use one slide a page)'),
    slide_magnification_borderline_share=I(0.01, 'share over the limit', 'Core helper (log 35): a slide within 1% of the limit is reported as "on the limit: judge it"',
                                           note='The limit itself is worked out from the painting (frame_geometry.py slide_limit).'),
    relief_room_moves_units=J([1, 2], 'units', 'Lesson 48; Workflows.md 94-97 (moves inside a painted relief room)'),
)

# ------------------------------------------------------------------------------------------------ composing (rules that do not change with the kind of shot)
S['composing'] = section(
    'The shot checker\'s numbers that hold for every kind of shot. The limits that change with the kind of shot '
    '(story box, brightest parts, quiet side ...) are in shot_kind_profiles.',
    brightest_parts_share=J(0.03, 'share of the frame', 'check_shot.py check_light; measure_composition.py lines 96-104 (the brightest 3%)'),
    brightest_parts_blur_share_of_width=J(0.01, 'share of the width', 'check_shot.py check_light'),
    warm_pixel_threshold=J(0.18, '(red - blue)/255 x brightness', 'measure_composition.py; check_shot.py line ~1524; lessons 111-112'),
    warm_near_story_widen_share_of_width=J(0.06, 'share of the width', 'check_shot.py line ~1526'),
    lit_from_below_reference=M(0.17, '(r - b)/(r + b), bottom 15% minus top 15%', 'The liked picture\'s notice (log 30); check_shot.py rule 6 text'),
    light_prop_outshine_share=M(0.10, 'share of the prop', 'Log 32: a flame lights about 6% of a lantern, a glowing glass 18 to 22%; check_shot.py line ~1586'),
    story_prop_margin_below_subject=J(0.05, 'brightness (0 to 1)', 'check_shot.py line ~1585 (95th percentile under the subject\'s median - 0.05)'),
    burnt_out_channel_level=J(254, 'levels of 255', 'check_shot.py line ~1605'),
    burnt_out_limits=J({'frame_share': 0.0002, 'prop_share': 0.03, 'set_share': 0.001}, 'shares', 'check_shot.py lines 1604-1619'),
    stray_warm_patch=J({'hue_min': 0.25, 'brightness_min': 0.25, 'frame_share_min': 0.002}, 'shares', 'check_shot.py lines 1620-1636'),
    clear_overlap_pixels_at_1536=J(20, 'pixels on a frame 1536 wide (scaled to the frame)', 'Rule 4 (07 Composing a shot.md); check_shot.py line 966; log 30 liked picture near-touches 10 to 25 px'),
    clear_gap_pixels_at_1536=J(25, 'pixels on a frame 1536 wide', 'as clear_overlap_pixels_at_1536'),
    near_touch_fix_margin_pixels_at_1536=J(4, 'pixels on a frame 1536 wide', 'check_shot.py line 966'),
    only_just_factor=J(1.3, 'times the limit', 'check_shot.py check_pairs (a pass under 1.3 times the limit is noted)'),
    edge_run_pixels_at_1536=J(40, 'pixels on a frame 1536 wide', 'check_shot.py edge_run lines 316-364 (log 31-32 planted lamp post)'),
    thin_parts_ignored_pixels_at_1080=J(6, 'pixels on a frame 1080 wide', 'check_shot.py without_wires lines 112-117 (a wire handle)'),
    story_together_metres=J(0.3, 'metres between footprints', 'check_shot.py check_story_in_3d (lines 1065-1115); log 31 planted drum'),
    story_depth_behind_support_metres=J(0.1, 'metres', 'check_shot.py line 1072'),
    reference_box_margin_share=J(0.02, 'share of the frame', 'check_shot.py lines 1163-1171 (the reference\'s own box + 0.02 when larger)'),
    words_hidden_share_max=J(0.05, 'share of the upper four fifths', 'check_shot.py check_words_hidden line 854'),
    words_bottom_share_may_hide=J(0.2, 'share of the words\' height', 'check_shot.py (the bottom fifth, the signature, may be covered)'),
    work_prop_middle_band_down=M([0.45, 0.62], 'down the frame', 'Log 30: the liked picture\'s back props at 0.47 to 0.54 down; check_shot.py line 1348'),
    work_prop_fix_band_down=J([0.47, 0.60], 'down the frame', 'check_shot.py line 1358'),
    dark_entry_shape=J({'blur_share_of_width': 0.004, 'darker_than_quarter_75th_percentile': 0.6, 'open_share_of_width': 0.01,
                        'top_row_touch_share_max': 0.25}, 'shares', 'check_shot.py check_dark_entry lines 1382-1421 (log 31 verifier)'),
    resting_floating_metres=J(0.03, 'metres of air', 'check_shot.py check_resting line 716'),
    resting_sunk_metres=J(0.05, 'metres', 'check_shot.py line 712'),
    resting_landed_high_metres=J(0.5, 'metres above the street', 'check_shot.py line 719 (a street rule: interiors use declared support surfaces)'),
    resting_moved_apart_metres=J(0.1, 'metres', 'check_shot.py line 765'),
    resting_ray_start_above_base_metres=J(0.05, 'metres', 'shot_facts.py (five rays from 5 cm above the base; lesson 109)'),
    picture_out_of_date=M({'gain_min': 0.08, 'agreement_min': 0.45}, 'share of outline', 'check_shot.py picture_mismatch line 447 (log 31: up-to-date pictures gained 0, moved props 0.09 to 0.23)'),
    picture_edges=J({'lightness_canny': [20, 60], 'colour_canny': [10, 30], 'blur': 1.5, 'widen_pixels': 7}, 'Canny thresholds and pixels', 'check_shot.py line 423; lesson 117'),
    bottom_fifth_darker_max_share=J(0.30, 'share darker than the middle band', 'Log 26 review (in about 70% of frames the bottom fifth was over 30% darker than the '
                                    'middle: the painting prompts asked for an empty floor); story log rule "Fill the bottom of the tall frame"'),
    subject_frame_share=M([0.029, 0.033], 'share of the frame', 'Log 30 (the liked notice 3.3%; the rebuild aimed at 2.9%; clip 29 had 0.95%)'),
    cut_by_frame_pixels=J(2, 'pixels from the left, top or bottom edge', 'check_shot.py check_cut_by_edge lines 897-917 (a fix brings the box to 0.03 / 0.97)'),
    quiet_side_prop_share_max=J(0.02, 'share of the frame', 'Rule 10; check_shot.py line ~1657 (no non-story prop on the quiet side over 2%)'),
    shot_facts_groups_max=M(20, 'groups', 'shot_facts.py PALETTE (20 colours)'),
    shot_facts_colour_match=J(24, 'sum of channel differences', 'shot_facts.py / check_shot.py lines 140-147'),
    shot_facts_solo_threshold=J(8, 'levels', 'shot_facts.py / check_shot.py'),
    line_finder=M({'min_length_share_of_height': 0.06, 'not_within_degrees_of_level': 8, 'not_within_degrees_of_upright': 10,
                   'vote_grid': [40, 24], 'average_within_cells': 1.5, 'trust_min_lines': 15}, 'shares, degrees, cells, lines',
                  'measure_composition.py lines 48-112; lesson 104 (47 lines in the sharp picture, 4 to 7 in clip 29: wrong)'),
)

# ------------------------------------------------------------------------------------------------ safe area for words
S['safe_area'] = section(
    'Where typed words and things to read may sit on the 1080 x 1920 frame (phone apps put buttons on the right and bottom).',
    text_left_pixels=J(65, 'pixels (0.06 of the width)', 'film-kit/paper-film/scenes/graphics.js TEXT_LEFT (line 345)'),
    text_right_pixels=J(972, 'pixels (0.90 of the width)', 'graphics.js TEXT_RIGHT (line 346); rule 12'),
    must_read_right_edge_share=J(0.90, 'share of the width', 'Rule 12; check_shot.py check_right_edge (line 1232); log 30 (the liked notice reached 0.91)'),
    story_right_edge_share=J(0.95, 'share of the width', 'Rule 12; check_shot.py line 1231'),
    button_strip_down=J([0.45, 0.95], 'down the frame', 'check_shot.py line 1235 (story props judged only in this strip)'),
    title_band_down=J([0.05, 0.22], 'down the frame', 'Plan 34 top band; Works check files title_zone [0.06, 0.05, 0.90, 0.22]'),
    letter_top_min_down=J(0.06, 'down the frame', 'Round 3 check (a heading at 0.047 sat under a phone app\'s top bar; moved to 0.061)'),
    nothing_to_read_below_down=J(0.80, 'down the frame (the bottom 380 pixels)', 'graphics.js header and frame_check.py (380 px at the bottom: buttons and captions)'),
    rule_cards_down=J([[0.07, 0.15], [0.16, 0.24]], 'down the frame', 'page-5.js lines 36-40; works-effects.js (lower card ends 0.236)'),
    top_shade=J({'bottom_pixels': 470, 'strength': 0.62}, 'pixels and opacity', 'graphics.js topShade (line 349): the soft dark band behind words'),
    callout_margin_pixels=J(70, 'pixels', 'graphics.js callout'),
    old_frame_check_margins_pixels=J([140, 140, 380], 'pixels [sides, top, bottom]', 'frame_check.py (lines 3-4) and the plugin\'s camera-and-framing.md',
                                     note='Superseded: 140 px is 0.87 across, stricter than rule 12\'s 0.90. Tools should read the entries above instead.'),
    landmark_top_min_down=J(0.24, 'down the frame', 'Round 2-3 (chimney tops at 0.07 to 0.14 down sat in the words band; keep a top below 0.24 or put the words beside it)'),
    heading_baselines_pixels=J([172, 250], 'pixels from the top', 'graphics.js; page-3.js LINE_1 and LINE_2'),
)

# ------------------------------------------------------------------------------------------------ lettering
S['lettering'] = section(
    'How big lettering must be on the film frame to read on a phone, and how to quieten a sign the narration does not name.',
    reading_evidence_pixels=M({'only_just': 11, 'tiny': 14, 'marginal': 16, 'readable': 22, 'easy': 29, 'readable_large': 60}, 'pixels tall on 1080 x 1920',
                              'Log 32 (PITS WILL BE CLOSED 11 px "only just"); rounds 3-4 (No. 1/No. 2 boards 14 px "tiny", BANK 15-17 px marginal, PETROL/DIESEL '
                              '22 px "fully readable", BANK 29 px "easy"); round 1 (60 px bill letters)'),
    must_read_min_pixels=J(20, 'pixels tall', 'Skeptic (log 35) from the evidence: 22 px read, 14 px did not; fail under 20'),
    must_read_comfortable_pixels=J(25, 'pixels tall', 'Skeptic (log 35): warn between 20 and 25 (25 was a critic\'s suggestion for WAGES)'),
    headline_pixels=J([40, 60], 'pixels tall', 'Plan 34 T12 (about 40 px the plan\'s test; 60 px bill letters read on a phone)'),
    not_meant_to_read_max_pixels=J(14, 'pixels tall', 'notice-corner-and-checker inventory: words not meant to be read stay about 14 px or less, or are dimmed'),
    unnamed_sign_dim=J(0.15, 'brightness factor until the word is said', 'works-effects.js BANK_SIGN.dim (lines 132-138): 0.3 was still read (round 4 critic), 0.15 chosen by eye'),
    facing_lean_max_degrees=J(15, 'degrees', 'Plan 34 lines 391-393; round 3 stood WAGES up leaning back 14 degrees'),
    plank_joint_clear_metres=J(0.03, 'metres from any letter', 'Round 2 gate boards (joints 3 to 4 cm clear)'),
    stencil_wrap_degrees=M(44, 'degrees either side of the front', 'props/index.json steel drums (word_reaches_degrees_either_side 43.8 and 43.9)'),
    key_line_easy_pixels=J(18, 'pixels tall', 'Log 32 "left for later": PITS WILL BE CLOSED was 11 px; "about 18 would read easily" (a judgement, before the 20 px floor above)'),
)

# ------------------------------------------------------------------------------------------------ people
S['people'] = section(
    'Painted and built figures: sizes, distances, crowds, faces.',
    figure_height_metres=J(1.75, 'metres', 'Plan 34 People table; build_figures.py (men 1.69 to 1.83 m in works-shot.json)'),
    head_height_metres=J(0.23, 'metres', 'Plan 34 (head_px = f x 0.23 / d); checker_formulas_check.py'),
    backs_to_camera_min_distance_metres=J(6.0, 'metres from every camera spot along a slide', 'Plan 34 line 124 (a 1.75 m man at 6 m is a quarter of the frame height); round 3'),
    facing_head_max_pixels=I(24, 'pixels tall', 'Plan 34 T8 and round 4 (doorway workers 20 to 24 px)',
                             note='Untested (skeptic, log 35): in the people test far walkers with about 10 px heads still got face dots, and the facing man at '
                                  'about 7 m (about 53 px) got none because the prompt said "face lost in shadow". Calibrate on the first Works painting.'),
    silhouettes_allowed=J(False, 'yes or no', 'Lesson 137 (people test: own-surface silhouettes read as shadow puppets)'),
    crowd_shoulder_gap_metres=J([0.3, 0.5], 'metres', 'Round 5 new_layout.txt; assemble_works.py lines 898-958'),
    crowd_back_row_behind_metres=J(0.8, 'metres', 'as crowd_shoulder_gap_metres'),
    crowd_turn_degrees=J([4, 16], 'degrees each way', 'as crowd_shoulder_gap_metres'),
    crowd_scale_range=J([0.96, 1.04], 'scale', 'as crowd_shoulder_gap_metres (so heads differ)'),
    crowd_axis_min_angle_to_view_degrees=I(60, 'degrees', 'Design (log 35): never line figures up along a camera\'s ray (round 4 finding 2: single file read as one column)'),
    crowd_head_spacing_head_widths=J(1.0, 'head widths between head centres on screen', 'Skeptic (log 35): replaces rule 4\'s 15/18 px between figures'),
    crowd_figure_visible_share_min=J(0.5, 'share of each figure', 'Skeptic (log 35)'),
    head_turn_from_strongest_light_degrees=J([15, 24], 'degrees', 'Rounds 2-4 (profile faces turned away from the fire)'),
    hands_above_hot_rim_metres=J([0.10, 0.15], 'metres', 'Round 2; assemble_works.py lines 919-921'),
    painted_figure_contrast=M(2.2, '(surround + 0.05)/(figure + 0.05)', 'People test (scratchpad redesign/people-paint/check-figures/film-figure-contrast.json: painted 2.20, silhouettes 2.98)'),
    tone_piece=J({'saturation': 0.62, 'contrast': 0.9, 'lift': 0.03}, 'factors', 'film-kit/paper-film/tools/tone_piece.py header (a face 1.7 times as colourful as the others)'),
    cloth_turns_black_below_levels=M(28, 'levels of 255 in the plate', 'Round 3: the film grade turns anything darker than about 28/255 black (tan coats came out crimson)'),
)

# ------------------------------------------------------------------------------------------------ light
S['light'] = section(
    'Lights in Blender and the stage that hold for every place, plus starting points that worked for one place.',
    shadow_pool_size=M('1024', 'EEVEE setting', 'Lesson 110: 1024 ran out on a 1536-wide plate unless scaled; 2048 could not be set up on this machine'),
    shadow_resolution_reference_width=J(1080, 'pixels (scale = min(1, 1080 / width))', 'set_dressing.py render() lines 208-217'),
    render_faults=M(['Shadow buffer full', 'Could not allocate shadow atlas'], 'words in the render log', 'check_shot.py RENDER_FAULTS (line 1811); lesson 110'),
    reflections_inside_paintings=J(0.3, 'scene.environmentIntensity', 'Lesson 49; cinema-kit.js lines 90-96 (default 1)'),
    projected_page_look=J({'exposure': 1.0, 'aperture': 4.0, 'maxBlur': 2, 'glowThreshold': 0.9, 'glowStrength': 0.6, 'contrast': 1.04, 'vignette': 0.3},
                          'stage look settings', 'notice-corner.js line ~180; inflation-chapter-2-newcomers/page-3.js LOOK'),
    projected_page_light_rig=J({'reflections': 0.2, 'key_cast_shadow': False, 'haze_density': 0.008}, 'stage light rig', 'notice-corner.js lightRig call lines 44-46'),
    lit_window_glow=J(1.4, 'emission strength', 'works_kit.py LIT_GLOW (lines 59-60; round 2: lit glass glowed white at higher values)'),
    exposure_dark_view=J(1.6, 'stage exposure', 'page-3.js LOOK_W1 (W1 plate 35 levels against 49 and 59; men 18 levels on screen, 28 after)',
                         note='To be judged again once the painting replaces the plate.'),
    starting_points=OrderedDict([
        ('about', 'Watts that passed the light rules at one place: a start for the next place, which retunes them.'),
        ('notice_corner', M({'fire_watts': 70, 'fire_light_above_coals_metres': 0.55, 'lantern_watts': 1, 'notice_glow_watts': 200, 'notice_glow_cone_degrees': 50,
                             'notice_glow_blend': 0.9, 'notice_glow_reach_metres': 1.4, 'road_glow_watts': 450, 'corner_lamp_watts': 12, 'sky_strength': 1.96},
                            'watts and Blender settings', 'assemble_notice_corner.py lines 58-71; notice-corner-shot.json; logs 31-32 (26 lighting rounds)')),
        ('works', M({'fire_watts': 80, 'gate_lamp_watts': 7, 'men_rim_yard_watts': 220, 'men_rim_lamp_watts': 90, 'yard_dusk_watts': 900, 'room_watts': 160,
                     'sky_strength': 1.6}, 'watts and Blender settings', 'assemble_works.py lines 856-859, 1148, 1214-1221; round 5')),
    ]),
)

# ------------------------------------------------------------------------------------------------ effects
S['effects'] = section(
    'Live effects drawn in the film (never painted): smoke, flicker, glow, contact shadows.',
    wind_three_axes=J([-0.85, -0.12, -0.5], 'direction (three.js axes, normalised in use)', 'works-effects.js lines 92-113 (round 5: across the views, a little away, sinking)'),
    smoke_kinds=J({'heavy': {'count': 44, 'life': 7, 'rise': 0.6, 'drift': 16, 'mouth_seconds': 2, 'mouth_size': 1.9, 'size': [3.4, 9], 'opacity': 0.95, 'fade': 1.8, 'colour': [100, 92, 84]},
                   'working': {'count': 36, 'life': 7, 'rise': 0.6, 'drift': 15, 'mouth_size': 1.7, 'size': [3.0, 8], 'opacity': 0.93, 'fade': 1.8, 'colour': [104, 96, 88]},
                   'thin': {'count': 14, 'life': 7, 'rise': 0.5, 'drift': 14, 'mouth_size': 1.3, 'size': [1.8, 6], 'opacity': 0.5, 'fade': 1.9}},
                  'puffs, seconds, metres, levels', 'works-effects.js lines 87-118; round 4 finding 4'),
    busy_window_change_min_levels=J(15, 'levels', 'Round 4 critic target; round5-pages/tools/window_change.py'),
    glow_size_swing_share=J(0.012, 'share', 'Log 32 (2.8% swing slid the glow\'s rim; calmed to 1.2%)'),
    contact_shadow=J({'height_above_ground_metres': 0.012, 'opacity': 0.55, 'fade_in_seconds': 0.8}, 'metres, opacity, seconds',
                     'notice-corner.js lines ~129-175 (faded in from the slide\'s start)'),
)

# ------------------------------------------------------------------------------------------------ state pictures
S['state_pictures'] = section(
    'Changes on a held shot made by swapping only the part of the painting that changes (make_state_picture.py).',
    threshold_levels=M(6, 'levels (largest channel, after a 2 px blur)', 'make_state_picture.py lines 20-47; round 2 (6 alone left 6.8% of the frame over 3 levels)'),
    faint_levels=M(3, 'levels (after a 10 px blur)', 'as threshold_levels (with it, under 4 levels everywhere but 0.04%)'),
    blur_pixels=J(2, 'pixels', 'make_state_picture.py'),
    faint_blur_pixels=J(10, 'pixels', 'make_state_picture.py'),
    widen_pixels=J(12, 'pixels at 1536 wide (scaled by width)', 'make_state_picture.py'),
    soften_pixels=J(5, 'pixels at 1536 wide', 'make_state_picture.py'),
    outline_widen_pixels=J(6, 'pixels at 1536 wide', 'make_state_picture.py'),
    speck_disc_pixels=J(1.5, 'pixels', 'make_state_picture.py'),
    smallest_piece_square_pixels=J(60, 'square pixels', 'make_state_picture.py'),
    close_disc_pixels=J(6, 'pixels', 'make_state_picture.py'),
    reference_width_pixels=J(1536, 'pixels', 'make_state_picture.py (sizes are for a 1536-wide plate)'),
    noise_factor_min=J(3, 'times the measured noise', 'make_state_picture.py (warns if a threshold is under 3 x noise)'),
    residual_outside_mask_levels=J(0, 'levels', 'make_state_picture.py lines 41-46 (stops otherwise); round 2 (JPEG moved every pixel)'),
    cut_when_mask_share_max=J(0.10, 'share of the frame', 'Rounds 3-4: a time cut where the swap is small (men going: 6.5 to 9.3%)'),
    blend_when_mask_share_evidence=M([0.41, 0.76], 'share of the frame', 'Rounds 3-4: windows lighting swapped 41 to 76%'),
    flag_mask_share=J(0.15, 'share of the frame', 'make_state_picture.py docstring lines 44-46; round 4 finding 15'),
    stepped_blend=J({'seconds': 0.8, 'steps': 3}, 'seconds and steps', 'works-effects.js steppedBlend (first step on the word)'),
    fallback_fade=J({'gate_swing_seconds': 0.8, 'people_fade_seconds': 1.2}, 'seconds', 'Plan 34 T9; page-3.js GO swing fallback'),
)

# ------------------------------------------------------------------------------------------------ painting
S['painting'] = section(
    'Asking the painter (fal) and lining the painting up with the plate. Prices are in money.',
    painter_model=J('blackforestlabs/flux-3/edit-image', 'fal model', 'people-test-paintings.json; notice-corner-paintings.json'),
    painter_settings=J({'resolution': '2k', 'aspect_ratio': 'auto', 'output_format': 'png', 'safety_tolerance': 2}, 'fal settings', 'people-test-paintings.json settings'),
    style_picture_size_pixels=J([768, 1368], 'pixels', 'people-test-paintings.json images_sent (about 1 MP saves about 7 c)'),
    align_search=J({'stretch': [0.985, 1.015], 'stretch_step': 0.0025, 'shift_pixels': [-12, 12], 'shift_step': 2, 'fine_stretch': 0.002, 'fine_stretch_step': 0.0005,
                    'fine_shift_pixels': 2, 'fine_shift_step': 0.5}, 'scale and pixels (frame basis 1080 wide)', 'align_painting.py lines 29-33, 65-70'),
    align_outline_agreement_aim=J(0.90, 'share of outlines on painting edges', 'align_painting.py docstring; Workflows.md'),
    align_results=M({'notice_corner': {'stretch': 1.0065, 'shift': [3, 3], 'before': 0.70, 'after': 0.96},
                     'people_test': {'stretch': 1.0010, 'shift': [1.0, 0.5], 'before': 0.874, 'after': 0.903}}, 'stretch, pixels, shares',
                    'notice-corner-paintings.json; people-test-paintings.json lined_up'),
    keep_painted_shadows_widen_pixels=J(10, 'pixels (painting pixels)', 'keep_painted_shadows.py WIDEN_PIXELS; lessons 122, 125'),
    behind_fill=J({'widen_pixels': 10, 'telea_radius': 9}, 'pixels at 1536 wide', 'make_behind_picture.py lines 1-31'),
    projected_set=J({'quickMove': 0.00003, 'behind_reach_share_of_height': 0.05, 'frontStretch': [1.3, 1.9], 'edgeWidth': 0.006, 'stretch': [2.5, 5],
                     'moveAngle': 0.01, 'frameEdge': 0.03, 'darken': 0.75, 'tint': 0.6, 'fill': 0.35, 'mapSize': 2048, 'bias': 0.004, 'jump': 0.03},
                    'projected-set.js options', 'film-kit/paper-film/scenes/projected-set.js lines 510-563; lessons 91, 95, 96'),
    sky_card=J({'distance_metres': 300, 'height_factor': 1.6, 'width_to_height': 1.5}, 'metres and factors', 'notice-corner.js lines ~114-127; lesson 93'),
    plate_thin_parts_pixels_at_1080=J(6, 'pixels', 'assemble_notice_corner.py lines 209-211 (parts thinner are removed, thickened or named "stay thin")'),
    repaint_reserve_share=J(0.5, 'repaints per painting', 'Plan 34 money table (lesson 97: the painter\'s strength varies)'),
    relief_room=J({'near': 5, 'far': 60, 'fov_degrees': 40, 'blur_pixels': 3}, 'units, degrees, pixels', 'cinema-kit.js relief(); prepare_relief.py --blur 3'),
    align_against=J({'lightness_canny': [40, 100], 'removed_props_widen_pixels': 25}, 'Canny thresholds and pixels', 'align_painting.py lines 35-45 (the behind painting against the main one)'),
    stand_in_match=M({'mean_levels': 4, 'share_over_12_levels': 0.064}, 'levels and share', 'Log 24 (3D stand-ins against the painting: the pass mark used)'),
)

# ------------------------------------------------------------------------------------------------ timing
S['timing'] = section(
    'Page timing and words on screen. Both timeline tools must read these (today estimate_timeline.py keeps 1.5 s, '
    'assemble_chapter_narration.py 1.4 s for the default pause).',
    first_word_at_seconds=J(1.08, 'seconds of music before the first word', 'assemble_chapter_narration.py FIRST_WORD_AT (line 28); estimate_timeline.py line 18'),
    tail_after_last_word_seconds=J(4.0, 'seconds', 'assemble_chapter_narration.py TAIL_AFTER_LAST_WORD (line 29); estimate_timeline.py line 19'),
    default_page_pause_seconds=J(1.4, 'seconds', 'assemble_chapter_narration.py DEFAULT_PAUSE (line 31)',
                                 note='estimate_timeline.py --default-pause still defaults to 1.5 (line 76): the drift this table ends.'),
    page_pause_range_seconds=J([1.1, 1.7], 'seconds', 'Decisions.md lines 81-82 (chapter 1)'),
    chapter_1_pauses_seconds=M([1.7, 1.4, 1.1, 1.5, 1.5, 1.3, 1.5, 1.4, 1.6], 'seconds', 'Log 07 (chosen gap by gap, longer where the turn has more to do)'),
    turn_after_last_word_seconds=J(0.3, 'seconds', 'cinema-chapter.js DEFAULT_JOIN (line 15); paper-chapter.js line 22'),
    peel_length_seconds=J(0.85, 'seconds', 'cinema-chapter.js DEFAULT_JOIN'),
    peel_shading_in_share=J(0.3, 'share of the peel', 'cinema-stage.js PEEL_SHADING_IN (line 364); round 3 (first peel frame 5.8 against 0.4)'),
    guess_hold_seconds=J(4.0, 'seconds', 'Lesson 129; estimate_timeline.py --pause-after PAGE=4.0'),
    rule_hold_seconds=J(2.0, 'seconds', 'Plan 34 lines 604-621'),
    final_fade_seconds=J(4.0, 'seconds', 'Plan 34; mix fade out 4 s'),
    rest_without_change_max_seconds=J(1.7, 'seconds (2.5 on the end card)', 'Decisions.md lines 87-88; lesson 16'),
    end_card_rest_max_seconds=J(2.5, 'seconds', 'as rest_without_change_max_seconds'),
    key_number_hold_seconds=J(1.0, 'seconds', 'Lesson 53; plugin guide "Hold the key number still"'),
    conclusion_full_strength_seconds=J(1.2, 'seconds before the cut', 'Round 3 check (PRICES UP 0.65 s could not be read; moved to 1.2 s)'),
    label_readable_min_seconds=J(1.0, 'seconds at full strength', 'Round 4 finding 8 (MACHINES readable 0.38 to 0.45 s)'),
    callout_words_delay_seconds=J(0.55, 'seconds after the line starts', 'graphics.js callout default (lines 105-118)'),
    callout_words_with_line_seconds=J(0.12, 'seconds', 'graphics.js wordsWithLine (round 5)'),
    presence_fades_seconds=J({'in': 0.3, 'out': 0.35}, 'seconds', 'graphics.js presence() (line 22)'),
    word_group_every_seconds=J(6, 'seconds', 'Plan 34 T6 (about 65 groups in 407 s)'),
    word_groups_per_page=J([3, 5], 'groups', 'Plan 34'),
    words_per_minute=M(160, 'words a minute', 'Lesson 126 (Malina read 164; plan at about 160); estimate_timeline.py 252 s predicted against 251.7 s'),
    thinking_pause_min_seconds=J(1.0, 'seconds for a "..."', 'Log 33 (each "..." gave under a second)'),
    page_drawn_window_seconds=J({'from_previous_last_word': 0.3, 'after_own_last_word': 1.2}, 'seconds', 'cinema-chapter.js line 9'),
    camera_plan_window_seconds=J({'before_first_word': 0.8, 'after_last_word_end': 1.3}, 'seconds', 'Plan 34 part 2 "Between pages"'),
    page_turn_still_after_last_word_seconds=J(0.7, 'seconds', 'Workflows.md lines 120-121 (check page turns in one run)'),
    first_word_tolerance_seconds=J(0.03, 'seconds', 'extract_word_times.py FIRST_WORD_TOLERANCE (line 33); lesson 18'),
    bracket_cue_max_seconds=J(0.2, 'seconds', 'Log 07 (a cue read aloud lasts longer or shows in the transcript)'),
    caption_max_letters=J(42, 'letters', 'make_captions.py MAX_LETTERS (line 20)'),
    caption_hold_after_last_word_seconds=J(0.15, 'seconds', 'make_captions.py HOLD_AFTER_LAST_WORD (line 21)'),
    caption_shortest_seconds=J(0.8, 'seconds', 'make_captions.py SHORTEST_CAPTION (line 22)'),
    fade_out_at_cut_seconds=J(0.0, 'seconds', 'graphics.js presence(..., fadeOut = 0) for everything that ends on a cut (round 3: words faded a frame early)'),
    new_words_after_old_frames=J(1, 'frames after the old words have gone', 'page-5.js lines 65-68 (round 3: NO SPARE drawn over the fading question)'),
    run_on_join_dip=J(0.0, 'dip in the blend', 'cinema-stage.js "run-on" join (round 3: the normal dissolve dipped 4 levels)'),
)

# ------------------------------------------------------------------------------------------------ sound
S['sound'] = section(
    'Loudness, the music under the voice, the limiter and the voice checks.',
    sample_rate=J(48000, 'samples a second', 'assemble_chapter_narration.py SAMPLE_RATE; lesson 5 (resample to 48,000 after every loudnorm)'),
    length_tolerance_seconds=J(0.05, 'seconds', 'Design (log 35) from lesson 5 (23 s asked, 23.04 s delivered)'),
    voice_page_lufs=J(-16.0, 'LUFS', 'assemble_chapter_narration.py VOICE_LOUDNESS (line 27); decisions'),
    mix_lufs=M(-15.0, 'LUFS integrated', 'mix_narration_over_music.sh target; measured -15.0 to -15.1 in logs 13, 19, 20'),
    music_only_lufs=J(-14.0, 'LUFS integrated', 'add_music_bed.sh LOUDNESS (log 32: -17.7 was faint on a phone)'),
    true_peak_max_dbtp=J(-1.0, 'dBTP', 'Decisions; measured -1.5 to -1.8 on the sent copies'),
    limiter=J({'limit': 0.84, 'attack_ms': 5, 'release_ms': 60, 'latency': 1}, 'alimiter settings', 'mix_narration_over_music.sh line 33; lessons 11, 15'),
    music_level_db=J(-11.0, 'dB', 'mix_narration_over_music.sh (the user asked for "slightly" louder: -14 to -11)'),
    music_eq=J({'frequency_hz': 2500, 'gain_db': -4, 'width_q': 1.2}, 'equalizer', 'mix_narration_over_music.sh line 26'),
    duck=J({'threshold': 0.08, 'ratio': 2.5, 'attack_ms': 30, 'release_ms': 1100, 'makeup': 1}, 'sidechaincompress', 'mix_narration_over_music.sh line 27; lesson 6'),
    music_under_voice_db=M({'while_speaking': 18, 'in_pauses': 12, 'tolerance': 1}, 'dB under the voice', 'Logs 04, 07, 10 (measured page by page)'),
    music_fades_seconds=J({'in': 0.8, 'out': 4.0}, 'seconds', 'mix_narration_over_music.sh line 28'),
    music_only_fades_seconds=J({'in': 0.8, 'out': 1.5}, 'seconds', 'add_music_bed.sh FADE_IN, FADE_OUT'),
    sound_alignment_max_ms=M(0.0, 'milliseconds (a few tolerated)', 'check_sound_alignment.py; log 08 (5 ms late before latency=1), 0.00 ms since'),
    loud_word_db=J(6, 'dB above the page\'s typical word', 'find_loud_words.py default'),
    raised_voice_semitones=J(5, 'semitones above the page\'s typical pitch', 'find_raised_voice.py default'),
    pitch_spread_across_pages=M({'accepted': 2.2, 'not_accepted': 3.0}, 'semitones', 'Decisions item 20; compare_voice_steadiness.py'),
    pitch_burst_semitones=J(7, 'semitones', 'compare_voice_steadiness.py'),
    mouth=J({'quiet_db': -25.0, 'loud_db': -11.0, 'slice_ms': 40, 'open_speed': 0.8, 'close_speed': 0.55}, 'dB, ms, factors', 'make_mouth_track.py QUIET_DB, LOUD_DB (lines 20-21); lesson 24'),
)

# ------------------------------------------------------------------------------------------------ filming
S['filming'] = section(
    'What a frame costs to film, and how to cut a long filming run into pieces that survive restarts.',
    seconds_per_frame_held_live_effects=M(0.9, 'seconds a frame, one worker', f'{RS}/round4-film/film/frame-times.txt (round 4: 0.88 to 0.99 by view; W3 0.89, W2 0.91, W1 0.99)'),
    seconds_per_frame_sliding=M(4.3, 'seconds a frame, one worker', f'{RS}/round4-film/film/frame-times.txt (W1 slide 4.31)'),
    seconds_loading_a_piece=M(34, 'seconds a piece', f'{RS}/round4-film/film/frame-times.txt (first stretch of each piece minus the steady rate: 22 to 58 s, mean 34)'),
    seconds_per_frame_held_nothing_live=M({'one_worker': 0.8, 'two_workers': 0.57}, 'seconds a frame', 'Plan 34 F3 (notice corner measurements)'),
    seconds_per_frame_paper=M(0.85, 'seconds a frame', 'Workflows.md (chapter 1, about 95 minutes for 6,641 frames; log 13 measured about 80)'),
    seconds_per_frame_model_pages=M([12, 15], 'seconds a frame', 'Lesson 70 (realistic materials of the works and town)'),
    peel_frames_cost_factor=J(2, 'times a held frame', 'Plan 34 computer time table (page peels about double)'),
    piece_frames=J({'default': 60, 'lazy_chapter': 240}, 'frames', 'film-chapter-parallel.sh PIECE_FRAMES (line 70); Workflows.md (lazy chapters 240)'),
    stretch_max_hours=M(2, 'hours', 'Lesson 69 (background jobs stop after 2 hours)'),
    workers=M({'two_processors': 1, 'four_processors': 2, 'two_workers_speed_gain': 0.17}, 'workers', 'Lesson 34; Workflows traps (1.44 against 1.68 s a frame)'),
    memory_per_piece_gb=M([2.6, 2.8], 'GB of browser memory', 'Plan 34 F1; log 34 (about 2.8 GB a piece)'),
    free_memory_before_piece_gb=J(6, 'GB', 'Plan 34 computer time (when Blender runs alongside)'),
    machine_memory_gb=M(16, 'GB (no swap)', 'Plan 34 F1'),
    plate_render_minutes=M([6, 11], 'minutes (EEVEE, 1536 x 2730)', 'Round 1 (11 min at 48 samples); round 3 (6 min with three shadowing lights)'),
    preview_render_minutes=M(1, 'minutes (540 x 960)', 'Round 1-3 previews'),
    checker_render=J({'size': [1080, 1920], 'samples': 16}, 'pixels and samples', 'Round 1-4 checker runs'),
    pages_3_to_5_minutes=M({'frames': 2283, 'round_3': 70, 'round_4': 53}, 'frames and minutes', 'round3-result.json, round4-result.json film.summary'),
    film_with_grain_megabytes_per_second=M(3.5, 'MB a second', 'Plan 34 F2'),
    msaa_samples=J(4, 'samples', 'cinema-stage.js (?samples=N; default 4)'),
)

# ------------------------------------------------------------------------------------------------ money
S['money'] = section(
    'Prices of paid services, with the date each was read. Nothing here spends money: every paid step asks the user first.',
    fal_flux_3_edit_cents_per_megapixel=M(4.8, 'US cents a megapixel (returned + every picture sent)', 'people-test-paintings.json note',
                                          date_read='2026-10-16', note='The plan had 2.4 c/MP from the price list (log 34 plan); the bill on the day was twice that. '
                                          'The people test came to about 85 c for two paintings, itself an estimate (fal shows no exact charge).'),
    fal_price_list_cents_per_megapixel=M(2.4, 'US cents a megapixel', 'Plan 34 lines 1131-1133 (fal\'s price list)', date_read='2026-10-15',
                                         note='Superseded by the 4.8 c/MP charged on 2026-10-16.'),
    nano_banana_pro_cents=M(15, 'US cents a picture', 'Project story logs 30-34', date_read='2026-10-14'),
    seedance_10_second_draft_cents=M(206, 'US cents', 'Project story log 30', date_read='2026-10-14'),
    minimax_6_second_video_cents=M(18, 'US cents', 'Project story logs 10-19', date_read='2026-10-12'),
    sam_3d_cents=M(2, 'US cents an object', 'Project story logs 23-24', date_read='2026-10-13'),
    tripo_cents=M([20, 40], 'US cents a model (never its free plan)', 'Project story', date_read='2026-10-13'),
    world_labs_cents=M({'per_world': 126, 'minimum_purchase': 500}, 'US cents', 'Project story log 26', date_read='2026-10-13'),
    elevenlabs_credits_per_letter=M(1.0, 'credits a letter of page text (accent instruction included)', 'Logs 04, 07, 19, 33 (2,950 credits for pages 2-10; 4,300 for chapter 2)',
                                    date_read='2026-10-13'),
    elevenlabs_dollars_per_credit=J(0.000175, 'US dollars a credit', 'Status.md (about 75 c for 4,300 credits "counted by text length", not a bill)', date_read='2026-10-13'),
    painting_failure_share=M(0.04, 'share of paintings redone', 'Log 13: 2 failures in 47 paintings'),
    user_allowance_dollars=J({'allowance': 20, 'spending_line': 12}, 'US dollars', 'Decision 40 (a new US$20 from log 34); plan 34 money table', date_read='2026-10-15'),
    old_painting_prices_cents=M({'flux_2k': 10, 'flux_1k': 2.5, 'cut_out_mask': 0.2, 'flux_edit_repaint': 10}, 'US cents a picture', 'Project story logs 10-34 (before the per-megapixel price)',
                                date_read='2026-10-12', note='Superseded for paintings by the 4.8 c/MP charged on 2026-10-16; the plugin\'s paint-and-cut skill still says 10 c.'),
    sam_3d_cents_per_painting=M(12, 'US cents a painting\'s objects', 'Inventory "Painting prices" (plan 34)', date_read='2026-10-15'),
)

# ------------------------------------------------------------------------------------------------ delivery
S['delivery'] = section(
    'The finished film: the sendable copy and the repository.',
    sendable_megabytes=J(28, 'MB', 'finish_film.sh (a file sent in chat must be under 30 MB; decision 16)'),
    sendable_audio_kbps=J(128, 'kbps AAC', 'finish_film.sh'),
    sendable_bitrate_factor=J(0.97, 'share kept for overhead', 'finish_film.sh: video kbps = (28 x 8000 x 0.97) / seconds - 128'),
    master_audio_kbps=J(256, 'kbps AAC', 'finish_film.sh'),
    repository_file_max_megabytes=J(90, 'MB (GitHub refuses 100)', 'Plan 34 "The repository"; decisions 27, 30'),
    repository_batch_max_megabytes=J(400, 'MB a push', 'Decisions 27, 30'),
    disk=M({'chapter_copy_gb': [1.4, 1.6], 'peak_gb': [6.5, 7.5]}, 'GB', 'Plan 34 F2, F15'),
)

# ------------------------------------------------------------------------------------------------ models
S['models'] = section(
    'Building models and sets in Blender.',
    coplanar_gap_metres=J(0.01, 'metres', 'Lesson 85 (a ceiling on the slab above flickered)'),
    contact_metres=M([0.01, 0.03], 'metres', 'Log 22 (SAM models floated 0.5, then 0.01 to 0.03)'),
    bake_shading=J({'ao_reach': 0.6, 'size_pixels': 1024, 'samples': 32, 'margin': 4}, 'Blender bake settings', 'model_kit.py bake_shading (line 283); lesson 61'),
    detailed_building_triangles=M([22000, 34000], 'triangles', 'Lesson 67 (232 parts joined into 19)'),
    held_frame_budget_seconds=J(1.5, 'seconds a frame', 'Plan 34 (budget by frame time, not triangles)'),
    ground_under_raised_area_metres=J(0.05, 'metres', 'Round 2 (setts only 2 cm above ground showed dark patches)'),
    index_size_match_metres=J(0.0015, 'metres', 'Round 1-2 (sizes measured from the saved model)'),
    place_prop_ray_start_above_pavement_metres=J(2.0, 'metres', 'set_dressing.place_prop lines 56-79 (under the eaves); lesson 88'),
    pit_village_street=M({'carriageway': 5.0, 'pavement': 1.65, 'length': 72, 'slope_degrees': 4, 'eaves': 6.0}, 'metres and degrees', 'build_street.py lines 77-116 (as built)'),
    striped_parts_allowed=J(0, 'parts', 'Round 3 (find_stripes.py found 15 to 33 striped parts; round 4 rebuilt to 0)'),
    clearance_units=J({'standing': 0.05, 'in_the_air': 0.15, 'tags_in_front_of_painted_room': 15}, 'units', 'cinema-kit.js clearance(); log 20 (price tags)'),
    virtual_screen=J('Xvfb :96 -screen 0 1920x1080x24; DISPLAY=:96 blender -b ...', 'command', 'check-shot.sh lines 17-29; build_works.sh line 13 (plates and checks drawn with EEVEE)'),
    painterly_library_slowdown=M({'seconds_with': 223, 'seconds_without': 33}, 'seconds a render', 'Log 34 (the FOUNDRY painterly library: 7 times slower, nothing looked painted; rejected)'),
)

# ------------------------------------------------------------------------------------------------ checking
S['checking'] = section(
    'Checking the film in motion and proving shared code changed nothing.',
    find_jumps=J({'size': [270, 480], 'jump_factor': 4.0, 'neighbours': 5, 'floor': 0.05, 'change_min': 1.0}, 'pixels and factors', 'find_jumps.py lines 17-35'),
    frame_change_evidence=M({'ordinary': [0.39, 0.51], 'cut': [42, 46], 'time_cut': [8.4, 10.7]}, 'mean level change', 'Rounds 2-4 find_jumps runs'),
    unplanned_change_fault=J(1.5, 'mean level change', 'Rounds 2-4 (anything above about 1.5 that is not a planned event)'),
    regression_largest_difference_levels=J(5, 'levels of 255, on a few pixels', 'Status (drawing noise 4-5 levels); log 14, 21, 34'),
    kept_shot_changed_pixels=J(0, 'pixels', 'Rounds 1-5 (the notice corner redrawn and all 518,400 pixels compared)'),
    contact_sheet_every_seconds=J({'overview': 3, 'moving_shots': 0.5}, 'seconds between frames', 'Logs 13-32'),
    profile_frame=J({'warm_up_frames': 2, 'timed_frames': 3}, 'frames', 'profile_frame.mjs lines 1-40'),
)

# ------------------------------------------------------------------------------------------------ script
S['script'] = section(
    'What a script for newcomers needs, measured on the recorded chapter 2 and its rewrite (log 33). The script gate adds its own limits.',
    words_per_sentence=J(9, 'words (about)', 'Log 33 audit and rewrite (sentences about 8 to 10 words)'),
    main_rule_said_times=J(2, 'times, in identical words', 'Log 33 (the main rule had been said once, 3 minutes in, as one 28-word sentence)'),
    real_cases=J(4, 'cases in time order', 'Log 33 (8 cases changing direction in time 8 times were too many)'),
    spoken_figures=M({'before': 37, 'after': 28}, 'figures in the chapter', 'Log 33 (the newcomer script carries about 28 spoken figures)'),
    stakes_within_seconds=J(30, 'seconds', 'Log 33'),
    newcomer_script_length=M({'words': 1021, 'minutes': 7.25}, 'words and minutes', 'Log 33; Status.md'),
    delivery_cues_per_page=J(1, 'leading bracket cue (the accent instruction)', 'Decisions (voice fix): one identical cue per page, no mood cues, no capitals'),
)

# ------------------------------------------------------------------------------------------------ page graphics
S['graphics'] = section(
    'The newcomer graphics drawn over the film (graphics.js).',
    dot_panel=J({'grid': [10, 10], 'spacing_pixels': 34, 'radius_pixels': 12, 'empty_step_seconds': 0.18}, 'pixels and seconds', 'graphics.js dotPanel (lines 286-554)'),
    build_words=J({'size_pixels': 52, 'line_gap': 1.22}, 'pixels and factor', 'graphics.js buildWords (auto-shrinks to fit)'),
    rule_card_plate_alpha=J(0.66, 'opacity', 'graphics.js ruleCard'),
    guess_ring_seconds=J(4.0, 'seconds to fill', 'graphics.js guessRing'),
    name_tag_pixels=J(34, 'pixels', 'graphics.js nameTag'),
    price_arrow_seconds=J(0.9, 'seconds to draw', 'graphics.js priceArrow'),
    pointer_seconds=J(0.45, 'seconds', 'graphics.js pointer'),
    callout_corner_pixels=J({'dx': 120, 'dy': -8}, 'pixels', 'page-3.js line 116 (the line leaves its thing sideways)'),
)

# ------------------------------------------------------------------------------------------------ the paper look
S['paper_look'] = section(
    'The paper pop-up look of chapter 1 (cut-out pieces in front of a page).',
    pieces_out_from_page_units=J([0.7, 2.7], 'units (bigger pieces further out)', 'Lesson 22 (at 0.5 the shadows hid behind the pieces)'),
    words_out_from_page_units=J(0.55, 'units', 'Lessons 22, 32'),
    piece_edge_from_middle_units=J(4.1, 'units at the page plane (less for pieces further forward)', 'Lesson 31'),
    shadows=J({'paper_stage': {'kind': 'PCFShadowMap', 'radius': 5}, 'cinema_kit': {'map_size': 2048, 'radius': 6, 'normal_bias': 0.02},
               'folded_props_normal_bias': 0}, 'three.js shadow settings', 'Lessons 21, 36; paper-stage.js lines 37-54; cinema-kit.js lines 95-106'),
    fading_alpha_test=J(0.02, 'alphaTest while a piece fades (0.5 otherwise)', 'Lesson 87; house-sample/page-1.js setFading'),
)

# ------------------------------------------------------------------------------------------------ shot-kind profiles
SOURCE_R5 = f'{RS}/round5-set/checks/final-*/report.md (round 5 final checks, 2026-10-16)'


def rule(applies, value, unit, kind, source, limit_type, **more):
    r = OrderedDict([('applies', applies), ('value', value), ('unit', unit), ('kind', kind), ('source', source), ('limit_type', limit_type)])
    r.update(more)
    return r


S['shot_kind_profiles'] = OrderedDict([
    ('about', 'Which composing rules apply to each kind of shot, and their limits. still_life is the base (the notice corner, '
              'where the rules were measured); the other kinds list only what they change, taken from what the project kept. '
              'A view names one or more kinds (place facts "kind_of_shot"). settings.py resolve_profile() gives the rules a view '
              'is held to.'),
    ('about_combining', 'For each rule, every named kind that changes it is used and the loosest wins: a rule switched off by '
                        'any named kind is off; "max" limits take the largest, "min" limits the smallest, "range" the widest. '
                        'A view\'s one-off exceptions go in its place facts "accepted" list, not here.'),
    ('rule_order_when_rules_conflict', J([
        'rule2: camera level and at eye height (it moves everything on screen)',
        'rule1: the street\'s lines meet at the subject\'s edge (slide or move the subject, never turn)',
        'rule12: words and story props clear of the phone buttons',
        'rule7: some story thing reaches 0.70 down (wins over rule 8\'s bottom-left limit for the story things that make the reach)',
        'people: figures at least 6 m away, backs turned, a crowd across the view (wins over rule 3\'s box width)',
        'rule3: the story group together',
        'rule4: clear overlaps or clear gaps',
        'rule8: work props small and far; nothing big at bottom left',
        'rule5 and rule6: light, once the layout has settled',
        'rule10: the quiet side\'s weight (the weakest: the checker ranks it 0.8)'],
        'order, first wins', 'check_shot.py ranking (KINDS/TIER lines 48-56: camera first; quiet side weighted 0.8); skeptic\'s missing list (log 35)')),
    ('still_life', OrderedDict([
        ('about', 'A few props round one subject, close to the camera: the notice corner (log 31-32, kept by the user: decision 38). '
                  'These limits were measured on the picture the user liked (log 30) and are the check_shot.py defaults.'),
        ('example_views', ['notice corner (end)']),
        ('rules', OrderedDict([
            ('main_rule_spot_box', rule(True, [0.40, 0.50], 'share of width x height', 'measured', 'Log 30 (liked picture); check_shot.py check_light lines 1667-1691', 'box_max')),
            ('rule1_meeting_point_gap', rule(True, 0.03, 'share of the width', 'judged', 'Rule 1; check_shot.py line 940', 'max', measure='to the subject\'s (or support\'s) nearest edge')),
            ('rule2_eye_height', rule(True, [1.5, 1.9], 'metres above the surface under the camera', 'judged', 'check_shot.py line 478', 'range')),
            ('rule3_story_box', rule(True, [0.40, 0.50], 'share of width x height', 'measured', 'Log 30 (or the reference\'s box + 0.02: 0.48 x 0.50 at the notice corner)', 'box_max')),
            ('rule3_story_together_metres', rule(True, 0.3, 'metres between footprints', 'judged', 'check_shot.py check_story_in_3d', 'max')),
            ('rule4_near_touch', rule(True, {'overlap_min': 20, 'gap_min': 25}, 'pixels at 1536 wide', 'judged', 'Rule 4; check_shot.py line 966', 'rule')),
            ('rule4_between_figures', rule(True, {'overlap_min': 20, 'gap_min': 25}, 'pixels at 1536 wide', 'judged', 'Rule 4 (as rule4_near_touch)', 'rule')),
            ('rule5_subject_brightness_ratio', rule(True, 1.8, 'times the frame\'s mean', 'measured', 'Log 30 (liked notice 0.61 against 0.32); check_shot.py line 1515', 'min')),
            ('rule5_brightest_share_on_subject', rule(True, 0.40, 'share of the brightest 3%', 'measured', 'Log 30; check_shot.py line 1507', 'min')),
            ('rule5_brightest_share_in_story_box', rule(True, 0.75, 'share of the brightest 3%', 'measured', 'Log 30 (about 80%); check_shot.py line 1507', 'min')),
            ('rule5_nothing_in_story_as_bright', rule(True, 0.05, 'brightness below the subject\'s median', 'judged', 'check_shot.py line ~1585', 'rule')),
            ('rule5_top_third_brightness', rule(True, 0.36, 'mean brightness (0 to 1)', 'measured', 'Log 30 (liked top-centre sky 0.35); check_shot.py line 1518', 'max')),
            ('rule6_warm_share', rule(True, [0.015, 0.03], 'share of the frame', 'measured', 'Log 30 (liked 2.2 to 2.3%); check_shot.py lines 1529-1532', 'range')),
            ('rule6_lit_from_below', rule(True, 0.10, '(r - b)/(r + b) bottom minus top', 'judged', 'Rule 6 (the liked picture 0.17); check_shot.py line 1569', 'min')),
            ('rule7_story_reaches_down', rule(True, 0.70, 'down the frame', 'judged', 'Round 4 critic and round 5 (the notice corner\'s drum, chair and pail fill 0.45 to 0.8)', 'min',
                                              who_may_reach='story')),
            ('rule8_work_prop_share', rule(True, 0.02, 'share of the frame', 'measured', 'Log 30 (liked back props 0.16 to 1.9%); check_shot.py line 1346', 'max')),
            ('rule8_bottom_left_share', rule(True, 0.01, 'share of the frame per thing', 'judged', 'Rule 8; check_shot.py line 1369', 'max', applies_to='every thing')),
            ('rule10_quiet_side_weight', rule(True, [0.40, 0.48], 'share of the weight', 'judged', 'Rule 10 (liked 43/57); check_shot.py line 1645', 'range')),
            ('rule10_nothing_on_quiet_side_outshines', rule(True, 1.0, 'times the subject\'s brightness', 'judged', 'Rule 10; check_shot.py lines 1660-1666', 'rule')),
            ('rule12_must_read_right_edge', rule(True, 0.90, 'share of the width', 'judged', 'Rule 12', 'max')),
            ('rule12_story_right_edge', rule(True, 0.95, 'share of the width (in 0.45-0.95 down)', 'judged', 'Rule 12', 'max')),
            ('rule12_title_zone_sky_share', rule(True, 0.85, 'share of the title zone that is sky', 'judged', 'check_shot.py check_titles line 1316', 'min')),
            ('resting_on', rule(True, 'the street (ground rays; "landed high" over 0.5 m)', 'rule', 'judged', 'check_shot.py check_resting lines 697-775', 'rule')),
            ('slide_magnification', rule(True, 'painting limit', 'times nearer at the nearest painted surface', 'measured',
                                         'Plan 34 F13; skeptic (log 35): (2672/1920) x tan(30.2)/tan(32.2) = 1.29 (frame_geometry.py slide_limit)', 'rule')),
        ])),
    ])),
    ('crowd', OrderedDict([
        ('about', 'A gathered crowd as the story (the Works\' waiting men, W1 and W2 slowed; the people test). Taken from the round 5 views the '
                  'helpers kept (not yet seen by the user): recalibrate when the user has judged them.'),
        ('example_views', ['works w1', 'works w2 (slowed)', 'works w3', 'people test']),
        ('rules', OrderedDict([
            ('rule3_story_box', rule(True, [0.80, 0.50], 'share of width x height', 'judged', SOURCE_R5 + ': W1 quiet 0.64 x 0.33, W2 slowed 0.76 x 0.32, W1 working 0.50; '
                                    'a loose crowd two deep across a gate (round 4 finding 2) cannot fit 0.40 wide (skeptic: "a crowd\'s box limit is set by the crowd")', 'box_max')),
            ('rule4_between_figures', rule(False, None, 'replaced', 'judged', SOURCE_R5 + ': near-touches between men accepted (W1 5, W2 slowed 8, W3 14)', 'rule',
                                          replaced_by='people.crowd_head_spacing_head_widths and people.crowd_figure_visible_share_min (skeptic, log 35)')),
            ('rule8_bottom_left_share', rule(True, 0.02, 'share of the frame per story thing (the subject or a story prop)', 'judged', SOURCE_R5 + ': W1 quiet diesel drum 1.6%, '
                                            'man 6 1.5%, man 5 1.2%; W2 quiet the gateway 1.4%; W2 slowed men 1.6, 1.6, 1.3% (rule order: the reach wins). W1\'s petrol '
                                            'drum (1.4%) is not a story thing there and stays a problem', 'max',
                                            applies_to='story things (the subject and story props); other things keep 0.01')),
            ('rule10_quiet_side_weight', rule(True, [0.40, 0.50], 'share of the weight', 'judged', SOURCE_R5 + ': W1 quiet 49%, W1 working 49%, W2 48%', 'range')),
            ('rule12_title_zone_sky_share', rule(False, None, 'replaced', 'judged', SOURCE_R5 + ': only 27% (W1) and 32% (W2) of the title band is sky; '
                                                 'rounds 3-4 measured 28 to 49%', 'rule',
                                                 replaced_by='a soft dark band behind the words (safe_area.top_shade) wherever the band holds roofs, chimneys or smoke (plan T13)')),
        ])),
    ])),
    ('overview', OrderedDict([
        ('about', 'A raised view of the whole place, its story far away (the Works\' W3 from an upstairs window, 29-30 m from the crowd).'),
        ('example_views', ['works w3']),
        ('rules', OrderedDict([
            ('rule2_eye_height', rule(True, [0.8, 7.0], 'metres above the surface the checker finds under the camera', 'judged',
                                      'works-w3-shot-check.json eye_height_note (the checker measures down to the window sill)', 'range',
                                      note='Better: floor + [1.5, 1.9] with the floor the viewer stands on (place facts camera.floor_height).')),
            ('rule3_story_box', rule(True, [0.60, 0.50], 'share of width x height', 'judged', SOURCE_R5 + ': W3 0.51 x 0.17', 'box_max')),
            ('rule3_story_together_metres', rule(True, 2.0, 'metres between footprints', 'judged', SOURCE_R5 + ': W3 no-2 crates 1.92 m from the gate boards '
                                                 '(the subject is two gates: two clusters)', 'max')),
            ('rule7_story_reaches_down', rule(True, 0.70, 'down the frame', 'judged', 'works-shot.json decisions.round_4 (the handcart in W3\'s bottom third); '
                                              'skeptic: W3\'s crowd at 29-30 m reaches only 0.67 (an eye of about 6.9 m would be needed)', 'min',
                                              who_may_reach='story or a fill prop (a handcart, crates)')),
            ('rule10_quiet_side_weight', rule(True, [0.40, 0.60], 'share of the weight', 'judged', SOURCE_R5 + ': W3 57%', 'range')),
        ])),
    ])),
    ('interior', OrderedDict([
        ('about', 'Indoors, props on counters, shelves and tables (3 of plan 34\'s 6 places: the checkout, the corner shop, the kitchen). '
                  'Provisional: from checkout C1\'s checks 1-10 (16 October 2026), which nobody has accepted yet.'),
        ('example_views', ['checkout c1']),
        ('rules', OrderedDict([
            ('rule2_eye_height', rule(True, [1.5, 1.7], 'metres above the floor', 'judged', 'examples/inflation-chapter-2-newcomers/checkout-c1-shot-check.json eye_height', 'range')),
            ('resting_on', rule(True, 0.03, 'metres of air above a declared support surface (floor, counter, shelf, table)', 'judged',
                                f'{RS}/round5-checkout/check1/report.md: four props on the 0.9 m counter falsely "landed on something high"; '
                                'the check file needed on_ground [] (skeptic, log 35)', 'max',
                                note='"Landed high" (0.5 m above the street) does not apply indoors.')),
            ('rule5_top_third_brightness', rule(True, 0.36, 'mean brightness (0 to 1)', 'judged', 'checkout-c1-shot-check.json "sky": "ceiling*" (the ceiling is the dim top)', 'max',
                                                sky_pattern='ceiling*')),
            ('rule7_story_reaches_down', rule(True, 0.70, 'down the frame', 'judged', 'checkout-c1-shot-check.json story_reaches_down (reach worked out above the counter top)', 'min',
                                              who_may_reach='story', reach_above='the support surface the story stands on')),
        ])),
    ])),
    ('dark_subject', OrderedDict([
        ('about', 'A subject that is dark by nature (an iron gate, an open doorway): shown by lighting what is behind it, judged by its silhouette, '
                  'not its brightness (W1\'s gate, W2\'s gateway).'),
        ('example_views', ['works w1', 'works w2']),
        ('rules', OrderedDict([
            ('rule1_meeting_point_gap', rule(True, 0.03, 'share of the width, across only', 'judged', SOURCE_R5 + ': W2\'s gateway 0 px across but 117 px below the meeting point '
                                             '(0.108); W1 working: the meeting point lies inside the opened gateway', 'max',
                                             measure='to the opening\'s whole outline; a meeting point inside the opening passes')),
            ('rule5_subject_brightness_ratio', rule(False, None, 'replaced', 'judged', SOURCE_R5 + ': W1 gate 0.85 x the mean, W2 gateway 0.68, W1 working 0.64; '
                                                    'round 5 raised the yard light 260 to 900 W and the gate still could not be brightest (inventory: a dark subject)', 'rule',
                                                    replaced_by='shot_kind_profiles.dark_subject.rules.silhouette_contrast')),
            ('rule5_brightest_share_on_subject', rule(False, None, 'replaced', 'judged', SOURCE_R5 + ': W1 8%, W2 0%, W2 slowed 13%', 'rule',
                                                      replaced_by='silhouette_contrast')),
            ('rule5_brightest_share_in_story_box', rule(False, None, 'replaced', 'judged', SOURCE_R5 + ': W1 43%, W2 33%, W1 working 62%', 'rule',
                                                        replaced_by='silhouette_contrast')),
            ('rule5_nothing_in_story_as_bright', rule(False, None, 'replaced', 'judged', SOURCE_R5 + ': every story thing is brighter than a dark gate', 'rule',
                                                      replaced_by='silhouette_contrast')),
            ('rule6_lit_from_below', rule(False, None, 'off', 'judged', SOURCE_R5 + ': W1 0.06, W2 0.01, W2 slowed -0.10, W1 working -0.05 (a dark subject has no colour to warm)', 'rule')),
            ('rule10_nothing_on_quiet_side_outshines', rule(False, None, 'off', 'judged', SOURCE_R5 + ': a lit window or lamp always outshines a dark gate', 'rule')),
            ('silhouette_contrast', rule(True, 2.2, '(surround + 0.05)/(subject + 0.05) over a band round the subject', 'measured',
                                         'People test: painted figures read at 2.20 on the film frame (film-figure-contrast.json)', 'min',
                                         note='Measured on figures, not a gate: calibrate on the W1 painting.')),
        ])),
    ])),
])


def merge_keep_others(mine, theirs, where=''):
    """My version of a section, plus every key another builder added inside it (kept and reported). Where both have a
    key with different contents, mine wins and the difference is printed so it can be looked at."""
    merged = OrderedDict(mine)
    for key, value in theirs.items():
        if key not in mine:
            merged[key] = value
            print(f'kept another builder\'s entry: {where}{key}')
        elif isinstance(mine[key], dict) and isinstance(value, dict) and 'value' not in mine[key]:
            merged[key] = merge_keep_others(mine[key], value, f'{where}{key}.')
        elif value != mine[key]:
            print(f'NOTE: {where}{key} differs in the file; the core helper\'s version is written (look before trusting either)')
    return merged


def build():
    existing = OrderedDict()
    if os.path.exists(OUT):
        with open(OUT) as handle:
            existing = json.load(handle, object_pairs_hook=OrderedDict)
    merged = OrderedDict()
    for key, value in S.items():
        if key in existing and isinstance(value, dict) and isinstance(existing[key], dict):
            merged[key] = merge_keep_others(value, existing[key], f'{key}.')
        else:
            merged[key] = value
    for key, value in existing.items():   # keep sections other builders added
        if key not in merged:
            merged[key] = value
            print('kept another builder\'s section:', key)
    return merged


if __name__ == '__main__':
    merged = build()
    text = json.dumps(merged, indent=1, ensure_ascii=False)
    if '--write' in sys.argv:
        with open(OUT, 'w') as handle:
            handle.write(text + '\n')
        print('wrote', OUT, len(text), 'characters')
    else:
        print(text[:2000])
