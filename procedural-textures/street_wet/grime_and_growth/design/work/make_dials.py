"""Makes the dial tables for the plan (markdown) and the two look files (presets/*.json) from ONE list, so the plan and the files cannot disagree.
Run: python3 -I make_dials.py OUT_DIR   (writes OUT_DIR/dials_tables.md, OUT_DIR/sooty_1926.json, OUT_DIR/mossy_courtyard_kept.json, OUT_DIR/mossy_courtyard_neglected.json)
A row: (short name, range, kit default, sooty 1926, mossy courtyard kept, what it does). None in a look column = same as the kit default.
"""
import json
import os
import sys

COMMON = [
    ('amount', '0 to 2', 1.0, None, None, 'Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double.'),
    ('seed', '0 to 100', 0.0, None, None, 'Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.)'),
    ('inflate_limit', '1 to 12', 6.0, None, None, 'A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone.'),
    ('fade_start', '5 to 40 m', 12.0, None, None, 'Metres from the camera where fine detail starts to give way to the average tone.'),
    ('fade_end', '15 to 80 m', 40.0, None, None, 'Metres from the camera where fine detail has fully given way to the average tone (never to "clean").'),
    ('wet_follow', '0 to 1', 1.0, None, None, 'How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness.'),
]

# (owner, key, group title, priority, roles it acts on, masks it reads, rows)
LAYERS = [
    ('walls', 'soot', 'WK SOOT', 'MUST', 'wall.masonry, wall.trim, wall.industrial, chimney, roof.*',
     'sheltered, drip, reveal, shade, tx_cavity, height',
     [
         ('film_mult', '0.3 to 1.0', 0.80, 0.62, 0.97, 'Colour multiplier of the general film on the clean surface (brick 0.50 to 0.65 in 1926).'),
         ('sheltered_mult', '0.2 to 1.0', 0.60, 0.40, 0.85, 'Multiplier where rain cannot reach (under sills, eaves, in reveals).'),
         ('washed_mult', '0.5 to 1.2', 0.95, 0.85, 1.0, 'Multiplier where rain washes (sill tops, the windward upper wall).'),
         ('washed_share', '0 to 0.6', 0.20, 0.20, 0.30, 'Share of wall area that is rain-washed (15 to 25 % in 1926).'),
         ('floor_mult', '0.2 to 0.8', 0.40, 0.30, 0.60, 'No dot may go below this multiple of its clean colour (keeps the film curve from crushing it).'),
         ('grey_pull', '0 to 1', 0.20, 0.30, 0.15, 'How far colour is pulled toward grey (25 to 35 % in 1926).'),
         ('mortar_soot', '0 to 1', 0.30, 0.50, 0.10, 'Extra darkening in mortar hollows (soot sits in hollows first).'),
         ('mottle_size', '0.2 to 3 m', 1.0, 0.9, 1.2, 'Size of the slow mottling.'),
         ('mottle_contrast', '0 to 1', 0.40, 0.50, 0.30, 'How strong the mottling is.'),
         ('edge_sharp', '0 to 1', 0.50, 0.60, 0.40, 'How crisp the line is between washed and sheltered (a clean line under a sill).'),
         ('stack_mult', '0.2 to 1.0', 0.60, 0.35, 1.0, 'Multiplier on chimney stacks (blackest in a coal town).'),
         ('roof_mult', '0.5 to 1.0', 0.90, 0.82, 0.95, 'Multiplier on roof surfaces.'),
         ('base_lift', '0 to 0.5', 0.0, 0.0, 0.0, 'LAST-RESORT dial: lifts the whole wall colour so that a pattern has room above the film-black zone. Off unless the integrator proves it is needed and says so.'),
     ]),
    ('walls', 'runoff', 'WK RUNOFF', 'MUST', 'wall.masonry, wall.trim (iron-sourced streaks use iron objects as sources)',
     'drip, drip_dist, drip_kind, sheltered, height',
     [
         ('strength', '0 to 1', 0.40, 0.55, 0.50, 'Contrast of the streaks.'),
         ('tone', '-1 to 1', 0.0, -0.5, 0.7, '-1 = pale washed stripe, +1 = dark stain. 1926 sooty walls: pale stripes with dark tide-lines. Courtyard plaster: dark grey-green streaks.'),
         ('edge_dark', '0 to 1', 0.30, 0.50, 0.20, 'Dark tide-line along the streak edges.'),
         ('width_dots', '4 to 24', 8.0, 10.0, 10.0, 'Smallest streak width in plate dots (the layer widens a streak with distance up to Inflate Limit).'),
         ('length_mult', '0.3 to 3', 1.0, 1.0, 1.2, 'Length of every streak.'),
         ('ragged', '0 to 1', 0.50, 0.60, 0.50, 'Ragged sides and a stretched-down shape.'),
         ('source_share', '0 to 1', 0.60, 0.70, 0.80, 'Share of sills, ledges and cap edges that carry a streak pair (60 to 80 % in 1926).'),
         ('leak_share', '0 to 0.5', 0.10, 0.15, 0.0, 'Share of downpipes that leak heavily and carry a long streak.'),
         ('leak_length', '0.3 to 1.5 m', 0.8, 0.9, 0.8, 'Length of a heavy leak streak.'),
         ('iron_rust', '0 to 1', 0.30, 0.50, 0.0, 'How orange (rust) a streak is when its source is an iron joint or bracket.'),
         ('eave_streaks', '0 to 1', 0.30, 0.50, 0.70, 'Streaks hanging from eave lines, gutter ends and cap overhangs.'),
     ]),
    ('walls', 'foot', 'WK FOOT', 'MUST', 'wall.masonry, wall.trim, wall.industrial',
     'height, dampness, drip (pipe feet), tx_cavity, shade',
     [
         ('splash_height', '0.1 to 0.6 m', 0.25, 0.28, 0.30, 'Height of the dirt splash band at the wall foot (15 to 35 cm in 1926).'),
         ('splash_strength', '0 to 1', 0.40, 0.50, 0.35, 'How dark the band is at the ground line.'),
         ('splash_ragged', '0 to 1', 0.60, 0.70, 0.60, 'Ragged top edge of splash dots and short upward fingers.'),
         ('finger_height', '0 to 0.2 m', 0.08, 0.10, 0.10, 'Height of the splash fingers above the band.'),
         ('pipe_foot_boost', '0 to 2', 1.0, 1.4, 0.0, 'Extra heavy splash and damp where a downpipe ends.'),
         ('tide_share', '0 to 1', 0.30, 0.45, 0.15, 'Share of house lengths that carry a damp tide-mark (older rows only).'),
         ('tide_height', '0.3 to 1.3 m', 0.70, 0.80, 0.50, 'Ragged top of the damp tide-mark.'),
         ('tide_strength', '0 to 1', 0.30, 0.40, 0.25, 'Darkening inside the tide-mark.'),
         ('tide_green', '0 to 1', 0.20, 0.30, 0.40, 'How green the damp zone is.'),
         ('salt_bloom', '0 to 0.1', 0.02, 0.03, 0.04, 'Share of the band covered by white salts along its top.'),
         ('mortar_wear', '0 to 1', 0.40, 0.50, 0.20, 'Recessed, eroded mortar in the lowest 0.6 m.'),
         ('spall_share', '0 to 0.2', 0.05, 0.07, 0.04, 'Share of bricks or blocks with a flaked face near the foot.'),
         ('wear_height', '0.2 to 0.9 m', 0.50, 0.60, 0.40, 'How high mortar wear and spalls reach.'),
     ]),
    ('walls', 'steps', 'WK STEPS', 'MUST', 'wall.trim (the steps are found by the step masks, not by object)',
     'step_top, step_edge, entry_rand, edge_dist, footfall',
     [
         ('whitened_share', '0 to 1', 0.50, 0.55, 0.0, 'Share of doorsteps that are whitened or donkey-stoned (40 to 70 %; medium confidence for Durham).'),
         ('scrubbed_share', '0 to 1', 0.30, 0.35, 0.0, 'Share that are only scrubbed pale.'),
         ('frame_m', '0.03 to 0.12 m', 0.06, 0.07, 0.07, 'Real width of the white frame along nosing and riser (4 to 10 cm).'),
         ('frame_dots', '4 to 20', 8.0, 8.0, 8.0, 'Smallest frame width in plate dots (widened with distance up to Inflate Limit).'),
         ('boot_grey', '0 to 1', 0.30, 0.30, 0.30, 'Boots grey the centre of the tread (30 %).'),
         ('dish_depth', '0 to 0.012 m', 0.004, 0.005, 0.003, 'Depth of the worn dish in the tread (relief, faded with distance).'),
         ('nosing_chips', '0 to 1', 0.30, 0.30, 0.20, 'Share of steps with a chipped nosing or corner.'),
         ('wear_polish', '0 to 1', 0.40, 0.50, 0.20, 'Polish of the worn centre.'),
     ]),
    ('walls', 'wallgrowth', 'WK WALL GROWTH', 'SHOULD', 'wall.masonry, wall.trim, wall.plaster, roof.tile (painted moss, algae, lichen)',
     'moss_site, algae_site, dampness, drip, lichen_site, height',
     [
         ('moss_amount', '0 to 2', 0.5, 0.4, 1.2, 'Painted moss at wall feet, drips, copings.'),
         ('algae_amount', '0 to 2', 0.8, 1.0, 1.0, 'Green-black algae film at pipe outlets and shaded feet.'),
         ('lichen_amount', '0 to 2', 0.0, 0.0, 0.6, 'Lichen. 1926 coal town: NONE (the smoke killed it). Courtyard: sparse colonies.'),
         ('moss_height', '0.1 to 1 m', 0.30, 0.35, 0.50, 'How high up a wall moss may reach from the foot.'),
         ('patch_dots', '8 to 40', 15.0, 15.0, 15.0, 'Smallest moss patch width in plate dots (patches of 15 dots or more survive the painter).'),
         ('drip_moss', '0 to 1', 0.30, 0.40, 0.50, 'Moss below run-off lines.'),
         ('cap_moss', '0 to 1', 0.30, 0.30, 0.60, 'Moss along copings and wall caps.'),
         ('roof_moss', '0 to 1', 0.0, 0.0, 0.40, 'Moss on roof surfaces (probably very little in 1926).'),
         ('tone_steps', '3 to 6', 5.0, 5.0, 4.0, 'Number of flat painted tones in a moss patch.'),
         ('clump_stretch', '1 to 3', 1.8, 1.8, 1.5, 'How much taller than wide a clump is (drip shape).'),
         ('relief', '0 to 0.02 m', 0.005, 0.006, 0.008, 'Height of moss relief (a bump on the incoming normal, faded with distance).'),
         ('lichen_dots', '4 to 16', 8.0, 8.0, 8.0, 'Lichen disc size in plate dots.'),
         ('brightness_floor', '0.12 to 0.4', 0.25, 0.25, 0.25, 'Lowest plate brightness of a moss patch (it must stay lighter than the stone and above the film-black zone).'),
     ]),
    ('walls', 'wallcracks', 'WK WALL CRACKS', 'SHOULD', 'wall.masonry, wall.trim, wall.plaster',
     'corner, reveal, height, tx_cavity, house flag',
     [
         ('crack_amount', '0 to 2', 0.30, 0.30, 0.50, 'How many cracks (the master Amount scales it too).'),
         ('crack_dots', '2 to 8', 3.5, 3.5, 3.5, 'Smallest crack width in plate dots (3 dots needs contrast 0.11).'),
         ('crack_contrast', '0.04 to 0.2', 0.11, 0.11, 0.11, 'Smallest crack contrast against the surround.'),
         ('stepped_cracks', '0 to 1', 0.0, 1.0, 0.0, 'Stepped mining cracks on the houses the set file flags (1 or 2 of 28).'),
         ('corner_chips', '0 to 1', 0.30, 0.40, 0.50, 'Chips at wall corners and opening corners.'),
         ('chip_cm', '2 to 12', 5.0, 5.0, 6.0, 'Chip size in centimetres (chips of about 5 cm and bigger read).'),
         ('plaster_cracks', '0 to 1', 0.0, 0.0, 0.5, 'Map cracks and corner cracks in plaster.'),
         ('spall_patches', '0 to 1', 0.15, 0.20, 0.30, 'Spalled patches near the foot.'),
         ('near_only', '6 to 30 m', 15.0, 15.0, 12.0, 'Cracks fade out beyond this distance (the painter invents its own texture there).'),
         ('slope_mm', '0 to 5', 1.5, 1.5, 1.5, 'Real slope of a crack edge so a lamp lights one side.'),
         ('dull', '0 to 1', 1.0, 1.0, 1.0, 'Cracks are dull: roughness back to 0.9, shine cut 35 %, water film cut 45 %.'),
     ]),
    ('walls', 'paint', 'WK PAINT', 'COULD', 'timber.paint (doors, window frames, fascia)',
     'height, footfall (door line), shade',
     [
         ('paint_dark', '0.5 to 1', 0.85, 0.78, 0.9, 'General darkening of paint (0.70 to 0.85 in 1926).'),
         ('flake_share', '0 to 0.5', 0.15, 0.20, 0.0, 'Share of painted area that has lost flakes.'),
         ('door_scuff', '0.1 to 0.5 m', 0.25, 0.30, 0.25, 'Height of kicked scuffs at the foot of doors (bare grey wood).'),
         ('latch_grease', '0 to 1', 0.40, 0.40, 0.2, 'Dark hand-grease patch at the latch.'),
         ('gloss_loss', '0 to 1', 0.40, 0.50, 0.3, 'How much the paint has lost its gloss.'),
     ]),
    ('ground', 'dirt', 'WK GROUND DIRT', 'MUST', 'ground.sett, ground.flag, ground.channel, ground.kerb (gravel and earth in other sets)',
     'footfall, keepclear, lowness, crown, wall_dist, shade, vertical_foot, prop_dist, seam_dist, entry_rand, step_foot',
     [
         ('film', '0 to 2', 0.5, 0.6, 0.4, 'Broad soft film of soot and dust, 0.5 to 3 m patches. NOT ash or coal dust (the rubbish layer has those).'),
         ('film_scale', '0.5 to 4 m', 1.6, 1.6, 1.6, 'Patch size of the film.'),
         ('film_darkness', '0 to 0.6', 0.25, 0.30, 0.20, 'Darkening of the film (at most about one third).'),
         ('film_max_share', '0 to 0.5', 0.25, 0.25, 0.25, 'Ceiling on the share of a surface the film may darken by a third or more.'),
         ('film_near_walls', '0 to 1', 1.0, 0.5, 1.0, 'Keeps the film off the places the rubbish layer already dirties (wall foot, gutter strip). 1 = film everywhere; 0.5 = half strength there.'),
         ('polish', '0 to 1', 0.4, 0.5, 0.0, 'Traffic polish: worn lanes are lighter and smoother.'),
         ('polish_lift', '0 to 0.2', 0.05, 0.05, 0.05, 'Brightness added to polished lanes.'),
         ('polish_rough', '0 to 1', 0.3, 0.3, 0.3, 'Roughness taken off polished lanes when dry.'),
         ('water_marks', '0 to 1', 0.3, 0.4, 0.3, 'Dried puddle rings and tide lines in low spots.'),
         ('rust_halo', '0 to 1', 0.5, 0.7, 0.0, 'Rust stain on the ground round the foot of iron posts and pipes (10 to 25 cm).'),
         ('rust_halo_m', '0.05 to 0.4 m', 0.18, 0.18, 0.18, 'Reach of the rust halo.'),
         ('drum_ring', '0 to 1', 0.5, 0.5, 0.0, 'Rust bleed ring on the ground at the foot of the fire drum (the ash ring is already in the rubbish layer).'),
         ('tar_patches', '0 to 1', 0.3, 0.5, 0.0, 'Tar patches over lost setts: scalloped edges, speckle of chippings.'),
         ('tar_max_share', '0 to 0.06', 0.03, 0.03, 0.0, 'Ceiling on tar patches as a share of road area (2 to 4 %).'),
         ('tar_splash', '0 to 1', 0.3, 0.3, 0.0, 'Splashes of tar at the kerb foot.'),
         ('tar_gloss', '0 to 1', 0.6, 0.6, 0.6, 'How glossy new tar is (near black when wet).'),
         ('scrub_strip', '0 to 1', 0.0, 0.6, 0.0, 'Pale scrubbed strip on the flags in front of a whitened or scrubbed doorstep (reads the same door random as the steps layer).'),
         ('scrub_strip_m', '0.2 to 0.8 m', 0.4, 0.4, 0.4, 'Reach of the scrubbed strip.'),
     ]),
    ('ground', 'groundcracks', 'WK GROUND CRACKS', 'MUST', 'ground.flag, ground.kerb, ground.sett (hard ground only)',
     'edge_dist, seam_dist, cover_dist, footfall, tx_cell (flags, setts), tx_cavity, crown',
     [
         ('flag_cracks', '0 to 2', 1.0, 1.0, 0.0, 'Amount of flag cracking.'),
         ('flag_fine_share', '0.05 to 0.2', 0.11, 0.11, 0.0, 'Share of flags with a fine crack (8 to 15 %).'),
         ('flag_broken_share', '0.01 to 0.06', 0.03, 0.03, 0.0, 'Share broken in two or three with a gap (2 to 4 %).'),
         ('flag_tilt_share', '0.02 to 0.08', 0.04, 0.04, 0.0, 'Share tilted or sunk (3 to 6 %).'),
         ('tilt_lip', '3 to 20 mm', 8.0, 8.0, 8.0, 'Height of the raised edge of a tilted flag (throws a dark shadow line).'),
         ('corner_chip_share', '0.03 to 0.15', 0.07, 0.07, 0.0, 'Share of flags with a chipped corner.'),
         ('kerb_chips', '0 to 2', 1.0, 1.0, 0.0, 'Amount of kerb damage.'),
         ('kerb_chip_share', '0.1 to 0.5', 0.28, 0.28, 0.0, 'Share of kerb length with edge chips (20 to 35 %).'),
         ('kerb_break_share', '0 to 0.15', 0.067, 0.067, 0.0, 'Share of kerb stones cracked or broken (1 in 15).'),
         ('kerb_scuffs', '0 to 1', 0.3, 0.3, 0.0, 'Pale wheel scuffs on kerb faces.'),
         ('kerb_joint_open', '3 to 20 mm', 8.0, 8.0, 8.0, 'Width of open, dark kerb joints.'),
         ('sett_disturb', '0 to 2', 0.7, 0.7, 0.0, 'Amount of disturbed setts (tilted, sunk, missing, ash or tar filled).'),
         ('sett_disturbed_share', '0.02 to 0.08', 0.04, 0.04, 0.0, 'Share of the sett field disturbed (3 to 6 %), gathered round seams, covers and wheel bands.'),
         ('open_joint_share', '0.05 to 0.25', 0.14, 0.14, 0.0, 'Share of sett joints open and dark (10 to 20 %).'),
         ('missing_share', '0 to 0.01', 0.003, 0.003, 0.0, 'Share of setts missing (dark rectangle).'),
         ('sunken_patch', '0.3 to 1.5 m', 0.8, 0.8, 0.8, 'Length of a sunken patch.'),
         ('crack_dots', '2 to 8', 3.5, 3.5, 3.5, 'Smallest crack width in plate dots.'),
         ('crack_contrast', '0.04 to 0.2', 0.11, 0.11, 0.11, 'Smallest crack contrast.'),
         ('near_only', '8 to 30 m', 15.0, 15.0, 15.0, 'Cracks fade out beyond this distance.'),
         ('max_contrast', '0.4 to 0.9', 0.75, 0.75, 0.75, 'Guard: no harsh black grid. Sett joints may not exceed this contrast.'),
         ('dull', '0 to 1', 1.0, 1.0, 1.0, 'Cracks are dull so the wet look cannot wash them out.'),
     ]),
    ('ground', 'groundmoss', 'WK GROUND MOSS', 'MUST', 'ground.sett, ground.flag, ground.channel, ground.kerb (ground.earth, stone.natural in other sets)',
     'moss_site, algae_site, tx_cavity, tx_joint, shade, dampness, footfall, keepclear, existing_growth',
     [
         ('joint_share', '0.03 to 0.3', 0.08, 0.10, 0.30, 'Share of joint length carrying painted moss in the best (gutter-side) strip.'),
         ('shade_bias', '0 to 1', 0.6, 0.6, 0.6, 'How much shade favours moss over sun.'),
         ('ribbon_dots', '3 to 12', 4.0, 4.0, 4.0, 'Smallest moss ribbon width in plate dots (a 1 to 3 cm joint ribbon is drawn wider near the camera).'),
         ('ribbon_m', '0.01 to 0.06 m', 0.02, 0.02, 0.02, 'Real ribbon width.'),
         ('broken_len', '0.1 to 0.8 m', 0.30, 0.30, 0.40, 'Length of a broken ribbon piece.'),
         ('algae_fan', '0 to 1', 0.6, 0.6, 0.3, 'Dark green-black algae fan under every downpipe outlet and gully.'),
         ('algae_radius', '0.3 to 1 m', 0.55, 0.55, 0.55, 'Reach of an algae fan.'),
         ('liverwort', '0 to 1', 0.0, 0.1, 0.0, 'The one bright green: 0 to 2 patches of 10 to 40 cm in damp shade.'),
         ('far_band', '0 to 1', 0.5, 0.5, 0.3, 'Beyond the pieces distance: a slightly greener, darker strip along gutter and wall foot instead of single plants.'),
         ('far_band_m', '0.2 to 0.8 m', 0.45, 0.45, 0.45, 'Width of the far band.'),
         ('moss_value', '0.25 to 0.5', 0.36, 0.36, 0.36, 'Plate brightness of dry moss (lighter than the stone; painted values under 0.12 are black on the film).'),
     ]),
    ('ground', 'iron', 'WK IRON', 'MUST', 'iron, iron.post, iron.pipe, fire (cast iron, steel, drum, rails)',
     'height, object zmin and zmax, drip_kind, vertical_foot',
     [
         ('rust_cover', '0 to 1', 0.30, 0.35, 0.0, 'Share of the lower part of an iron object with paint chipped back to rust.'),
         ('rust_height', '0.2 to 1.2 m', 0.55, 0.55, 0.55, 'How high rust reaches from the foot of a post.'),
         ('chip_share', '0.1 to 0.5', 0.30, 0.30, 0.30, 'Share of paint chipped in the rust zone.'),
         ('collar_spacing', '1.2 to 2.5 m', 1.9, 1.9, 1.9, 'Spacing of pipe collars and joints where rust rings sit.'),
         ('collar_rust', '0 to 1', 0.5, 0.5, 0.0, 'Share of collars with rust.'),
         ('metallic_drop', '0 to 1', 0.6, 0.6, 0.6, 'Rust lowers Metallic by up to this fraction (cast iron 0.6, steel 0.5, brass 0.9).'),
         ('heat_scale', '0 to 1', 0.3, 0.3, 0.0, 'Heat-blued scale on the fire drum only.'),
         ('soot_halo', '0 to 1', 0.5, 0.5, 0.0, 'Sooty halo above the drum vent holes and black rim.'),
         ('paint_keep', '0 to 1', 0.6, 0.6, 0.6, 'Share of the original paint kept (black or dark green).'),
         ('rust_run', '0.05 to 0.3 m', 0.12, 0.12, 0.12, 'Length of rust runs below fixings.'),
     ]),
    ('growth', 'growth', 'WK GROWTH (3D pieces)', 'MUST', 'ground.sett, ground.flag, ground.channel, ground.kerb (scatter targets; others by settings)',
     'weed_site, moss_site, keepclear, footfall, rubbish_heap, wall_dist, seam_dist, shade, dampness, existing_growth',
     [
         ('weeds_amount', '0 to 2', 1.0, 1.0, 0.1, 'Amount of weed pieces (grass tufts, rosettes). 0 = none.'),
         ('cushions_amount', '0 to 2', 1.0, 1.0, 1.5, 'Amount of moss cushion pieces. 0 = none.'),
         ('distance', '8 to 40 m', 18.0, 18.0, 25.0, 'Pieces are laid only up to this far from the camera (the camera of the picture being drawn).'),
         ('distance_fade', '2 to 10 m', 5.0, 5.0, 5.0, 'Length of the fade-out at the pieces distance.'),
         ('piece_size', '0.5 to 2', 1.0, 1.0, 1.0, 'Size of every piece (1 = as built to the period sizes).'),
         ('weed_cover', '0 to 0.03', 0.010, 0.010, 0.001, 'Green cover of weeds as a share of ground area inside the pieces distance (0.5 to 2 % in 1926).'),
         ('gutter_tuft_share', '0.02 to 0.1', 0.05, 0.05, 0.0, 'Share of gutter-side joint length with a visible tuft (3 to 8 %).'),
         ('wall_foot_share', '0.01 to 0.08', 0.035, 0.035, 0.0, 'Share of wall-foot length with a plant (2 to 5 %).'),
         ('cushion_cover', '0 to 0.03', 0.008, 0.008, 0.02, 'Moss cushion cover as a share of ground area inside the pieces distance.'),
         ('min_spacing', '0.05 to 0.4 m', 0.15, 0.15, 0.15, 'Nearest two pieces of one kind may be.'),
         ('toadflax_clumps', '0 to 3', 0.0, 1.0, 0.0, 'Ivy-leaved toadflax trails on damp mortar: 0 to 2 clumps in the whole street.'),
         ('rubbish_thin_max', '0.2 to 0.7', 0.45, 0.45, 0.45, 'Weeds grow at full density through rubbish thinner than this mask value.'),
         ('rubbish_heap_min', '0.5 to 0.95', 0.75, 0.75, 0.75, 'No weeds (and no moss above 0.6) on rubbish heavier than this mask value; between the two it thins out linearly.'),
         ('dead_grass_share', '0 to 0.5', 0.15, 0.15, 0.15, 'Share of grass tufts that are dead and straw-coloured.'),
         ('flower_share', '0 to 0.3', 0.08, 0.08, 0.0, 'Share of dandelions in flower or seed-clock (a few only).'),
         ('max_pieces', '500 to 6000', 2500.0, 2500.0, 2500.0, 'Hard ceiling on pieces in one picture (drawing time).'),
         ('wet_dark', '0.4 to 1', 0.70, 0.70, 0.70, 'Colour multiple of wet pieces (richer green, darker).'),
         ('tilt_random', '0 to 1', 0.5, 0.5, 0.5, 'How much each piece leans.'),
     ]),
]

COLOURS = [
    # (layer, name, sooty 1926 plate sRGB 0-255 (dry) / wet, courtyard note, source)
    ('soot', 'soot tint', '(77, 64, 56)', '(92, 102, 77) grey-green dust and algae film', 'period G1; courtyard study 12b'),
    ('runoff', 'washed pale stripe', 'wall colour x 1.10 to 1.25 (never below 0.18 plate brightness)', 'n/a', 'period G2, painted look 7'),
    ('runoff', 'rust streak', '(120, 70, 45) dry, (80, 50, 36) wet', 'none', 'period S2'),
    ('foot', 'splash band', '(62, 52, 45) dry, (45, 38, 33) wet', '(95, 100, 85) dry grey-green', 'period G4'),
    ('foot', 'salt bloom', '(215, 210, 200)', '(225, 222, 212)', 'period S5'),
    ('steps', 'whitened stone', '(228, 222, 208) dry, (170, 165, 150) wet', 'n/a', 'period S8'),
    ('steps', 'scrubbed sandstone', '(195, 180, 155) dry, (145, 130, 108) wet', 'n/a', 'period S8'),
    ('wallgrowth / groundmoss', 'moss dry', 'HSV (98 deg, 0.45, 0.42) = (77, 107, 59)', 'the add-on moss tones (linear 0.035,0.075,0.022 / 0.085,0.15,0.04 / 0.15,0.22,0.065 / 0.055,0.105,0.03)', 'painted look 11; period M1; courtyard 12b'),
    ('wallgrowth / groundmoss', 'moss wet', 'HSV (108 deg, 0.55, 0.30) = (43, 77, 34); never below plate 0.25 brightness for readability', 'brighter saturated green', 'painted look 11'),
    ('wallgrowth / groundmoss', 'algae film', 'dry (105, 112, 82), wet (48, 62, 42)', 'same', 'period M2'),
    ('groundmoss', 'liverwort', 'dry (95, 142, 65), wet (55, 110, 45)', 'n/a', 'period M3'),
    ('dirt', 'tar new / weathered / chippings', '(24, 22, 20) glossy / (50, 48, 44) matt / (100, 98, 92)', 'n/a', 'period S6'),
    ('dirt', 'rust halo on stone', '(160, 110, 80)', 'n/a', 'period S1'),
    ('iron', 'fresh rust / old rust', '(150, 80, 45) / (90, 58, 42)', 'n/a', 'period S1, S3'),
    ('growth', 'weed leaf dry / wet', 'HSV (100 deg, 0.50, 0.40) = (68, 102, 51) / HSV (110 deg, 0.58, 0.30) = (40, 77, 32)', 'fresh green to yellow-green', 'painted look 11; period W1'),
    ('growth', 'dead grass / dandelion flower', '(175, 152, 95) / (240, 195, 35)', 'straw', 'period W1'),
]


def pick(row, look):
    short, rng, kit, sooty, court, meaning = row
    if look == 'kit':
        return kit
    if look == 'sooty':
        return kit if sooty is None else sooty
    return kit if court is None else court


def build_preset(look, name, note):
    out = {'schema': 'weathering-look/1', 'id': name, 'note': note, 'layers': {}}
    for owner, key, group, prio, roles, masks, rows in LAYERS:
        values = {}
        for row in COMMON + rows:
            values[row[0]] = pick(row, look)
        out['layers'][key] = values
    return out


def tables():
    lines = []
    lines.append('**Dials every layer has** (the same names, ranges and defaults on every layer):\n')
    lines.append('| dial | range | kit default | what it does |')
    lines.append('|---|---|---|---|')
    for short, rng, kit, sooty, court, meaning in COMMON:
        lines.append(f'| `{short}` | {rng} | {kit:g} | {meaning} |')
    lines.append('')
    for owner, key, group, prio, roles, masks, rows in LAYERS:
        lines.append(f'#### `{key}` ({group}), owner: {owner}, priority: {prio}')
        lines.append(f'Acts on roles: {roles}. Reads masks: {masks}.\n')
        lines.append('| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |')
        lines.append('|---|---|---|---|---|---|')
        for short, rng, kit, sooty, court, meaning in rows:
            s = '=' if sooty is None else f'{sooty:g}'
            c = '=' if court is None else f'{court:g}'
            lines.append(f'| `{short}` | {rng} | {kit:g} | {s} | {c} | {meaning} |')
        lines.append('')
    lines.append('**Colours** (plate sRGB 0 to 255 unless said; they are START values for the plate, to be tuned against the painter-size pictures; wet = dry x 0.76 to 0.88 for stone, brick, mortar, soot, wood; moss, algae and leaves darken more and get richer; whitening goes grey):\n')
    lines.append('| layer | colour | sooty 1926 | courtyard | source |')
    lines.append('|---|---|---|---|---|')
    for layer, name, s, c, src in COLOURS:
        lines.append(f'| {layer} | {name} | {s} | {c} | {src} |')
    return '\n'.join(lines)


if __name__ == '__main__':
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, 'dials_tables.md'), 'w').write(tables() + '\n')
    sooty = build_preset('sooty', 'sooty_1926', 'A coal-smoke colliery village in County Durham, May 1926 (the lockout). Old hard soot crust, washed streaks, damp wall feet, rust only on iron, whitened doorsteps, tar patches, few small weeds, moss in the damp gutter-side joints, NO lichen, nothing modern. Values are first starts from the period and painted-look studies (a guess where the studies say so); the integrator tunes them.')
    court = build_preset('court', 'mossy_courtyard_kept', 'A kept Japanese temple courtyard (raked gravel, moss as the only plant, no coal, no iron). FIRST GUESSES from study 12b section 9, to be re-measured in the courtyard job.')
    neglected = json.loads(json.dumps(court))
    neglected['id'] = 'mossy_courtyard_neglected'
    neglected['note'] = 'The same courtyard left untended: more dust and algae, more moss and lichen, weeds along the gravel edge and at rock feet, more cracks. FIRST GUESSES (study 12b section 9).'
    ng = neglected['layers']
    ng['wallgrowth'].update(moss_amount=1.8, algae_amount=1.6, lichen_amount=1.0)
    ng['soot'].update(film_mult=0.90, sheltered_mult=0.70)
    ng['growth'].update(weeds_amount=1.0, weed_cover=0.012, gutter_tuft_share=0.05, wall_foot_share=0.03)
    ng['groundmoss'].update(joint_share=0.45)
    ng['wallcracks'].update(crack_amount=1.0, plaster_cracks=0.9, spall_patches=0.5)
    for name, data in (('sooty_1926', sooty), ('mossy_courtyard_kept', court), ('mossy_courtyard_neglected', neglected)):
        json.dump(data, open(os.path.join(out, name + '.json'), 'w'), indent=1)
    print('rows:', sum(len(r[6]) for r in LAYERS), 'layers:', len(LAYERS))
