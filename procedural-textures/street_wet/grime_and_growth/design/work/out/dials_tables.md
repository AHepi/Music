**Dials every layer has** (the same names, ranges and defaults on every layer):

| dial | range | kit default | what it does |
|---|---|---|---|
| `amount` | 0 to 2 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |

#### `soot` (WK SOOT), owner: walls, priority: MUST
Acts on roles: wall.masonry, wall.trim, wall.industrial, chimney, roof.*. Reads masks: sheltered, drip, reveal, shade, tx_cavity, height.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `film_mult` | 0.3 to 1.0 | 0.8 | 0.62 | 0.97 | Colour multiplier of the general film on the clean surface (brick 0.50 to 0.65 in 1926). |
| `sheltered_mult` | 0.2 to 1.0 | 0.6 | 0.4 | 0.85 | Multiplier where rain cannot reach (under sills, eaves, in reveals). |
| `washed_mult` | 0.5 to 1.2 | 0.95 | 0.85 | 1 | Multiplier where rain washes (sill tops, the windward upper wall). |
| `washed_share` | 0 to 0.6 | 0.2 | 0.2 | 0.3 | Share of wall area that is rain-washed (15 to 25 % in 1926). |
| `floor_mult` | 0.2 to 0.8 | 0.4 | 0.3 | 0.6 | No dot may go below this multiple of its clean colour (keeps the film curve from crushing it). |
| `grey_pull` | 0 to 1 | 0.2 | 0.3 | 0.15 | How far colour is pulled toward grey (25 to 35 % in 1926). |
| `mortar_soot` | 0 to 1 | 0.3 | 0.5 | 0.1 | Extra darkening in mortar hollows (soot sits in hollows first). |
| `mottle_size` | 0.2 to 3 m | 1 | 0.9 | 1.2 | Size of the slow mottling. |
| `mottle_contrast` | 0 to 1 | 0.4 | 0.5 | 0.3 | How strong the mottling is. |
| `edge_sharp` | 0 to 1 | 0.5 | 0.6 | 0.4 | How crisp the line is between washed and sheltered (a clean line under a sill). |
| `stack_mult` | 0.2 to 1.0 | 0.6 | 0.35 | 1 | Multiplier on chimney stacks (blackest in a coal town). |
| `roof_mult` | 0.5 to 1.0 | 0.9 | 0.82 | 0.95 | Multiplier on roof surfaces. |
| `base_lift` | 0 to 0.5 | 0 | 0 | 0 | LAST-RESORT dial: lifts the whole wall colour so that a pattern has room above the film-black zone. Off unless the integrator proves it is needed and says so. |

#### `runoff` (WK RUNOFF), owner: walls, priority: MUST
Acts on roles: wall.masonry, wall.trim (iron-sourced streaks use iron objects as sources). Reads masks: drip, drip_dist, drip_kind, sheltered, height.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `strength` | 0 to 1 | 0.4 | 0.55 | 0.5 | Contrast of the streaks. |
| `tone` | -1 to 1 | 0 | -0.5 | 0.7 | -1 = pale washed stripe, +1 = dark stain. 1926 sooty walls: pale stripes with dark tide-lines. Courtyard plaster: dark grey-green streaks. |
| `edge_dark` | 0 to 1 | 0.3 | 0.5 | 0.2 | Dark tide-line along the streak edges. |
| `width_dots` | 4 to 24 | 8 | 10 | 10 | Smallest streak width in plate dots (the layer widens a streak with distance up to Inflate Limit). |
| `length_mult` | 0.3 to 3 | 1 | 1 | 1.2 | Length of every streak. |
| `ragged` | 0 to 1 | 0.5 | 0.6 | 0.5 | Ragged sides and a stretched-down shape. |
| `source_share` | 0 to 1 | 0.6 | 0.7 | 0.8 | Share of sills, ledges and cap edges that carry a streak pair (60 to 80 % in 1926). |
| `leak_share` | 0 to 0.5 | 0.1 | 0.15 | 0 | Share of downpipes that leak heavily and carry a long streak. |
| `leak_length` | 0.3 to 1.5 m | 0.8 | 0.9 | 0.8 | Length of a heavy leak streak. |
| `iron_rust` | 0 to 1 | 0.3 | 0.5 | 0 | How orange (rust) a streak is when its source is an iron joint or bracket. |
| `eave_streaks` | 0 to 1 | 0.3 | 0.5 | 0.7 | Streaks hanging from eave lines, gutter ends and cap overhangs. |

#### `foot` (WK FOOT), owner: walls, priority: MUST
Acts on roles: wall.masonry, wall.trim, wall.industrial. Reads masks: height, dampness, drip (pipe feet), tx_cavity, shade.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `splash_height` | 0.1 to 0.6 m | 0.25 | 0.28 | 0.3 | Height of the dirt splash band at the wall foot (15 to 35 cm in 1926). |
| `splash_strength` | 0 to 1 | 0.4 | 0.5 | 0.35 | How dark the band is at the ground line. |
| `splash_ragged` | 0 to 1 | 0.6 | 0.7 | 0.6 | Ragged top edge of splash dots and short upward fingers. |
| `finger_height` | 0 to 0.2 m | 0.08 | 0.1 | 0.1 | Height of the splash fingers above the band. |
| `pipe_foot_boost` | 0 to 2 | 1 | 1.4 | 0 | Extra heavy splash and damp where a downpipe ends. |
| `tide_share` | 0 to 1 | 0.3 | 0.45 | 0.15 | Share of house lengths that carry a damp tide-mark (older rows only). |
| `tide_height` | 0.3 to 1.3 m | 0.7 | 0.8 | 0.5 | Ragged top of the damp tide-mark. |
| `tide_strength` | 0 to 1 | 0.3 | 0.4 | 0.25 | Darkening inside the tide-mark. |
| `tide_green` | 0 to 1 | 0.2 | 0.3 | 0.4 | How green the damp zone is. |
| `salt_bloom` | 0 to 0.1 | 0.02 | 0.03 | 0.04 | Share of the band covered by white salts along its top. |
| `mortar_wear` | 0 to 1 | 0.4 | 0.5 | 0.2 | Recessed, eroded mortar in the lowest 0.6 m. |
| `spall_share` | 0 to 0.2 | 0.05 | 0.07 | 0.04 | Share of bricks or blocks with a flaked face near the foot. |
| `wear_height` | 0.2 to 0.9 m | 0.5 | 0.6 | 0.4 | How high mortar wear and spalls reach. |

#### `steps` (WK STEPS), owner: walls, priority: MUST
Acts on roles: wall.trim (the steps are found by the step masks, not by object). Reads masks: step_top, step_edge, entry_rand, edge_dist, footfall.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `whitened_share` | 0 to 1 | 0.5 | 0.55 | 0 | Share of doorsteps that are whitened or donkey-stoned (40 to 70 %; medium confidence for Durham). |
| `scrubbed_share` | 0 to 1 | 0.3 | 0.35 | 0 | Share that are only scrubbed pale. |
| `frame_m` | 0.03 to 0.12 m | 0.06 | 0.07 | 0.07 | Real width of the white frame along nosing and riser (4 to 10 cm). |
| `frame_dots` | 4 to 20 | 8 | 8 | 8 | Smallest frame width in plate dots (widened with distance up to Inflate Limit). |
| `boot_grey` | 0 to 1 | 0.3 | 0.3 | 0.3 | Boots grey the centre of the tread (30 %). |
| `dish_depth` | 0 to 0.012 m | 0.004 | 0.005 | 0.003 | Depth of the worn dish in the tread (relief, faded with distance). |
| `nosing_chips` | 0 to 1 | 0.3 | 0.3 | 0.2 | Share of steps with a chipped nosing or corner. |
| `wear_polish` | 0 to 1 | 0.4 | 0.5 | 0.2 | Polish of the worn centre. |

#### `wallgrowth` (WK WALL GROWTH), owner: walls, priority: SHOULD
Acts on roles: wall.masonry, wall.trim, wall.plaster, roof.tile (painted moss, algae, lichen). Reads masks: moss_site, algae_site, dampness, drip, lichen_site, height.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `moss_amount` | 0 to 2 | 0.5 | 0.4 | 1.2 | Painted moss at wall feet, drips, copings. |
| `algae_amount` | 0 to 2 | 0.8 | 1 | 1 | Green-black algae film at pipe outlets and shaded feet. |
| `lichen_amount` | 0 to 2 | 0 | 0 | 0.6 | Lichen. 1926 coal town: NONE (the smoke killed it). Courtyard: sparse colonies. |
| `moss_height` | 0.1 to 1 m | 0.3 | 0.35 | 0.5 | How high up a wall moss may reach from the foot. |
| `patch_dots` | 8 to 40 | 15 | 15 | 15 | Smallest moss patch width in plate dots (patches of 15 dots or more survive the painter). |
| `drip_moss` | 0 to 1 | 0.3 | 0.4 | 0.5 | Moss below run-off lines. |
| `cap_moss` | 0 to 1 | 0.3 | 0.3 | 0.6 | Moss along copings and wall caps. |
| `roof_moss` | 0 to 1 | 0 | 0 | 0.4 | Moss on roof surfaces (probably very little in 1926). |
| `tone_steps` | 3 to 6 | 5 | 5 | 4 | Number of flat painted tones in a moss patch. |
| `clump_stretch` | 1 to 3 | 1.8 | 1.8 | 1.5 | How much taller than wide a clump is (drip shape). |
| `relief` | 0 to 0.02 m | 0.005 | 0.006 | 0.008 | Height of moss relief (a bump on the incoming normal, faded with distance). |
| `lichen_dots` | 4 to 16 | 8 | 8 | 8 | Lichen disc size in plate dots. |
| `brightness_floor` | 0.12 to 0.4 | 0.25 | 0.25 | 0.25 | Lowest plate brightness of a moss patch (it must stay lighter than the stone and above the film-black zone). |

#### `wallcracks` (WK WALL CRACKS), owner: walls, priority: SHOULD
Acts on roles: wall.masonry, wall.trim, wall.plaster. Reads masks: corner, reveal, height, tx_cavity, house flag.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `crack_amount` | 0 to 2 | 0.3 | 0.3 | 0.5 | How many cracks (the master Amount scales it too). |
| `crack_dots` | 2 to 8 | 3.5 | 3.5 | 3.5 | Smallest crack width in plate dots (3 dots needs contrast 0.11). |
| `crack_contrast` | 0.04 to 0.2 | 0.11 | 0.11 | 0.11 | Smallest crack contrast against the surround. |
| `stepped_cracks` | 0 to 1 | 0 | 1 | 0 | Stepped mining cracks on the houses the set file flags (1 or 2 of 28). |
| `corner_chips` | 0 to 1 | 0.3 | 0.4 | 0.5 | Chips at wall corners and opening corners. |
| `chip_cm` | 2 to 12 | 5 | 5 | 6 | Chip size in centimetres (chips of about 5 cm and bigger read). |
| `plaster_cracks` | 0 to 1 | 0 | 0 | 0.5 | Map cracks and corner cracks in plaster. |
| `spall_patches` | 0 to 1 | 0.15 | 0.2 | 0.3 | Spalled patches near the foot. |
| `near_only` | 6 to 30 m | 15 | 15 | 12 | Cracks fade out beyond this distance (the painter invents its own texture there). |
| `slope_mm` | 0 to 5 | 1.5 | 1.5 | 1.5 | Real slope of a crack edge so a lamp lights one side. |
| `dull` | 0 to 1 | 1 | 1 | 1 | Cracks are dull: roughness back to 0.9, shine cut 35 %, water film cut 45 %. |

#### `paint` (WK PAINT), owner: walls, priority: COULD
Acts on roles: timber.paint (doors, window frames, fascia). Reads masks: height, footfall (door line), shade.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `paint_dark` | 0.5 to 1 | 0.85 | 0.78 | 0.9 | General darkening of paint (0.70 to 0.85 in 1926). |
| `flake_share` | 0 to 0.5 | 0.15 | 0.2 | 0 | Share of painted area that has lost flakes. |
| `door_scuff` | 0.1 to 0.5 m | 0.25 | 0.3 | 0.25 | Height of kicked scuffs at the foot of doors (bare grey wood). |
| `latch_grease` | 0 to 1 | 0.4 | 0.4 | 0.2 | Dark hand-grease patch at the latch. |
| `gloss_loss` | 0 to 1 | 0.4 | 0.5 | 0.3 | How much the paint has lost its gloss. |

#### `dirt` (WK GROUND DIRT), owner: ground, priority: MUST
Acts on roles: ground.sett, ground.flag, ground.channel, ground.kerb (gravel and earth in other sets). Reads masks: footfall, keepclear, lowness, crown, wall_dist, shade, vertical_foot, prop_dist, seam_dist, entry_rand, step_foot.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `film` | 0 to 2 | 0.5 | 0.6 | 0.4 | Broad soft film of soot and dust, 0.5 to 3 m patches. NOT ash or coal dust (the rubbish layer has those). |
| `film_scale` | 0.5 to 4 m | 1.6 | 1.6 | 1.6 | Patch size of the film. |
| `film_darkness` | 0 to 0.6 | 0.25 | 0.3 | 0.2 | Darkening of the film (at most about one third). |
| `film_max_share` | 0 to 0.5 | 0.25 | 0.25 | 0.25 | Ceiling on the share of a surface the film may darken by a third or more. |
| `film_near_walls` | 0 to 1 | 1 | 0.5 | 1 | Keeps the film off the places the rubbish layer already dirties (wall foot, gutter strip). 1 = film everywhere; 0.5 = half strength there. |
| `polish` | 0 to 1 | 0.4 | 0.5 | 0 | Traffic polish: worn lanes are lighter and smoother. |
| `polish_lift` | 0 to 0.2 | 0.05 | 0.05 | 0.05 | Brightness added to polished lanes. |
| `polish_rough` | 0 to 1 | 0.3 | 0.3 | 0.3 | Roughness taken off polished lanes when dry. |
| `water_marks` | 0 to 1 | 0.3 | 0.4 | 0.3 | Dried puddle rings and tide lines in low spots. |
| `rust_halo` | 0 to 1 | 0.5 | 0.7 | 0 | Rust stain on the ground round the foot of iron posts and pipes (10 to 25 cm). |
| `rust_halo_m` | 0.05 to 0.4 m | 0.18 | 0.18 | 0.18 | Reach of the rust halo. |
| `drum_ring` | 0 to 1 | 0.5 | 0.5 | 0 | Rust bleed ring on the ground at the foot of the fire drum (the ash ring is already in the rubbish layer). |
| `tar_patches` | 0 to 1 | 0.3 | 0.5 | 0 | Tar patches over lost setts: scalloped edges, speckle of chippings. |
| `tar_max_share` | 0 to 0.06 | 0.03 | 0.03 | 0 | Ceiling on tar patches as a share of road area (2 to 4 %). |
| `tar_splash` | 0 to 1 | 0.3 | 0.3 | 0 | Splashes of tar at the kerb foot. |
| `tar_gloss` | 0 to 1 | 0.6 | 0.6 | 0.6 | How glossy new tar is (near black when wet). |
| `scrub_strip` | 0 to 1 | 0 | 0.6 | 0 | Pale scrubbed strip on the flags in front of a whitened or scrubbed doorstep (reads the same door random as the steps layer). |
| `scrub_strip_m` | 0.2 to 0.8 m | 0.4 | 0.4 | 0.4 | Reach of the scrubbed strip. |

#### `groundcracks` (WK GROUND CRACKS), owner: ground, priority: MUST
Acts on roles: ground.flag, ground.kerb, ground.sett (hard ground only). Reads masks: edge_dist, seam_dist, cover_dist, footfall, tx_cell (flags, setts), tx_cavity, crown.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `flag_cracks` | 0 to 2 | 1 | 1 | 0 | Amount of flag cracking. |
| `flag_fine_share` | 0.05 to 0.2 | 0.11 | 0.11 | 0 | Share of flags with a fine crack (8 to 15 %). |
| `flag_broken_share` | 0.01 to 0.06 | 0.03 | 0.03 | 0 | Share broken in two or three with a gap (2 to 4 %). |
| `flag_tilt_share` | 0.02 to 0.08 | 0.04 | 0.04 | 0 | Share tilted or sunk (3 to 6 %). |
| `tilt_lip` | 3 to 20 mm | 8 | 8 | 8 | Height of the raised edge of a tilted flag (throws a dark shadow line). |
| `corner_chip_share` | 0.03 to 0.15 | 0.07 | 0.07 | 0 | Share of flags with a chipped corner. |
| `kerb_chips` | 0 to 2 | 1 | 1 | 0 | Amount of kerb damage. |
| `kerb_chip_share` | 0.1 to 0.5 | 0.28 | 0.28 | 0 | Share of kerb length with edge chips (20 to 35 %). |
| `kerb_break_share` | 0 to 0.15 | 0.067 | 0.067 | 0 | Share of kerb stones cracked or broken (1 in 15). |
| `kerb_scuffs` | 0 to 1 | 0.3 | 0.3 | 0 | Pale wheel scuffs on kerb faces. |
| `kerb_joint_open` | 3 to 20 mm | 8 | 8 | 8 | Width of open, dark kerb joints. |
| `sett_disturb` | 0 to 2 | 0.7 | 0.7 | 0 | Amount of disturbed setts (tilted, sunk, missing, ash or tar filled). |
| `sett_disturbed_share` | 0.02 to 0.08 | 0.04 | 0.04 | 0 | Share of the sett field disturbed (3 to 6 %), gathered round seams, covers and wheel bands. |
| `open_joint_share` | 0.05 to 0.25 | 0.14 | 0.14 | 0 | Share of sett joints open and dark (10 to 20 %). |
| `missing_share` | 0 to 0.01 | 0.003 | 0.003 | 0 | Share of setts missing (dark rectangle). |
| `sunken_patch` | 0.3 to 1.5 m | 0.8 | 0.8 | 0.8 | Length of a sunken patch. |
| `crack_dots` | 2 to 8 | 3.5 | 3.5 | 3.5 | Smallest crack width in plate dots. |
| `crack_contrast` | 0.04 to 0.2 | 0.11 | 0.11 | 0.11 | Smallest crack contrast. |
| `near_only` | 8 to 30 m | 15 | 15 | 15 | Cracks fade out beyond this distance. |
| `max_contrast` | 0.4 to 0.9 | 0.75 | 0.75 | 0.75 | Guard: no harsh black grid. Sett joints may not exceed this contrast. |
| `dull` | 0 to 1 | 1 | 1 | 1 | Cracks are dull so the wet look cannot wash them out. |

#### `groundmoss` (WK GROUND MOSS), owner: ground, priority: MUST
Acts on roles: ground.sett, ground.flag, ground.channel, ground.kerb (ground.earth, stone.natural in other sets). Reads masks: moss_site, algae_site, tx_cavity, tx_joint, shade, dampness, footfall, keepclear, existing_growth.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `joint_share` | 0.03 to 0.3 | 0.08 | 0.1 | 0.3 | Share of joint length carrying painted moss in the best (gutter-side) strip. |
| `shade_bias` | 0 to 1 | 0.6 | 0.6 | 0.6 | How much shade favours moss over sun. |
| `ribbon_dots` | 3 to 12 | 4 | 4 | 4 | Smallest moss ribbon width in plate dots (a 1 to 3 cm joint ribbon is drawn wider near the camera). |
| `ribbon_m` | 0.01 to 0.06 m | 0.02 | 0.02 | 0.02 | Real ribbon width. |
| `broken_len` | 0.1 to 0.8 m | 0.3 | 0.3 | 0.4 | Length of a broken ribbon piece. |
| `algae_fan` | 0 to 1 | 0.6 | 0.6 | 0.3 | Dark green-black algae fan under every downpipe outlet and gully. |
| `algae_radius` | 0.3 to 1 m | 0.55 | 0.55 | 0.55 | Reach of an algae fan. |
| `liverwort` | 0 to 1 | 0 | 0.1 | 0 | The one bright green: 0 to 2 patches of 10 to 40 cm in damp shade. |
| `far_band` | 0 to 1 | 0.5 | 0.5 | 0.3 | Beyond the pieces distance: a slightly greener, darker strip along gutter and wall foot instead of single plants. |
| `far_band_m` | 0.2 to 0.8 m | 0.45 | 0.45 | 0.45 | Width of the far band. |
| `moss_value` | 0.25 to 0.5 | 0.36 | 0.36 | 0.36 | Plate brightness of dry moss (lighter than the stone; painted values under 0.12 are black on the film). |

#### `iron` (WK IRON), owner: ground, priority: MUST
Acts on roles: iron, iron.post, iron.pipe, fire (cast iron, steel, drum, rails). Reads masks: height, object zmin and zmax, drip_kind, vertical_foot.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `rust_cover` | 0 to 1 | 0.3 | 0.35 | 0 | Share of the lower part of an iron object with paint chipped back to rust. |
| `rust_height` | 0.2 to 1.2 m | 0.55 | 0.55 | 0.55 | How high rust reaches from the foot of a post. |
| `chip_share` | 0.1 to 0.5 | 0.3 | 0.3 | 0.3 | Share of paint chipped in the rust zone. |
| `collar_spacing` | 1.2 to 2.5 m | 1.9 | 1.9 | 1.9 | Spacing of pipe collars and joints where rust rings sit. |
| `collar_rust` | 0 to 1 | 0.5 | 0.5 | 0 | Share of collars with rust. |
| `metallic_drop` | 0 to 1 | 0.6 | 0.6 | 0.6 | Rust lowers Metallic by up to this fraction (cast iron 0.6, steel 0.5, brass 0.9). |
| `heat_scale` | 0 to 1 | 0.3 | 0.3 | 0 | Heat-blued scale on the fire drum only. |
| `soot_halo` | 0 to 1 | 0.5 | 0.5 | 0 | Sooty halo above the drum vent holes and black rim. |
| `paint_keep` | 0 to 1 | 0.6 | 0.6 | 0.6 | Share of the original paint kept (black or dark green). |
| `rust_run` | 0.05 to 0.3 m | 0.12 | 0.12 | 0.12 | Length of rust runs below fixings. |

#### `growth` (WK GROWTH (3D pieces)), owner: growth, priority: MUST
Acts on roles: ground.sett, ground.flag, ground.channel, ground.kerb (scatter targets; others by settings). Reads masks: weed_site, moss_site, keepclear, footfall, rubbish_heap, wall_dist, seam_dist, shade, dampness, existing_growth.

| dial | range | kit | sooty 1926 | courtyard (kept) | what it does |
|---|---|---|---|---|---|
| `weeds_amount` | 0 to 2 | 1 | 1 | 0.1 | Amount of weed pieces (grass tufts, rosettes). 0 = none. |
| `cushions_amount` | 0 to 2 | 1 | 1 | 1.5 | Amount of moss cushion pieces. 0 = none. |
| `distance` | 8 to 40 m | 18 | 18 | 25 | Pieces are laid only up to this far from the camera (the camera of the picture being drawn). |
| `distance_fade` | 2 to 10 m | 5 | 5 | 5 | Length of the fade-out at the pieces distance. |
| `piece_size` | 0.5 to 2 | 1 | 1 | 1 | Size of every piece (1 = as built to the period sizes). |
| `weed_cover` | 0 to 0.03 | 0.01 | 0.01 | 0.001 | Green cover of weeds as a share of ground area inside the pieces distance (0.5 to 2 % in 1926). |
| `gutter_tuft_share` | 0.02 to 0.1 | 0.05 | 0.05 | 0 | Share of gutter-side joint length with a visible tuft (3 to 8 %). |
| `wall_foot_share` | 0.01 to 0.08 | 0.035 | 0.035 | 0 | Share of wall-foot length with a plant (2 to 5 %). |
| `cushion_cover` | 0 to 0.03 | 0.008 | 0.008 | 0.02 | Moss cushion cover as a share of ground area inside the pieces distance. |
| `min_spacing` | 0.05 to 0.4 m | 0.15 | 0.15 | 0.15 | Nearest two pieces of one kind may be. |
| `toadflax_clumps` | 0 to 3 | 0 | 1 | 0 | Ivy-leaved toadflax trails on damp mortar: 0 to 2 clumps in the whole street. |
| `rubbish_thin_max` | 0.2 to 0.7 | 0.45 | 0.45 | 0.45 | Weeds grow at full density through rubbish thinner than this mask value. |
| `rubbish_heap_min` | 0.5 to 0.95 | 0.75 | 0.75 | 0.75 | No weeds (and no moss above 0.6) on rubbish heavier than this mask value; between the two it thins out linearly. |
| `dead_grass_share` | 0 to 0.5 | 0.15 | 0.15 | 0.15 | Share of grass tufts that are dead and straw-coloured. |
| `flower_share` | 0 to 0.3 | 0.08 | 0.08 | 0 | Share of dandelions in flower or seed-clock (a few only). |
| `max_pieces` | 500 to 6000 | 2500 | 2500 | 2500 | Hard ceiling on pieces in one picture (drawing time). |
| `wet_dark` | 0.4 to 1 | 0.7 | 0.7 | 0.7 | Colour multiple of wet pieces (richer green, darker). |
| `tilt_random` | 0 to 1 | 0.5 | 0.5 | 0.5 | How much each piece leans. |

**Colours** (plate sRGB 0 to 255 unless said; they are START values for the plate, to be tuned against the painter-size pictures; wet = dry x 0.76 to 0.88 for stone, brick, mortar, soot, wood; moss, algae and leaves darken more and get richer; whitening goes grey):

| layer | colour | sooty 1926 | courtyard | source |
|---|---|---|---|---|
| soot | soot tint | (77, 64, 56) | (92, 102, 77) grey-green dust and algae film | period G1; courtyard study 12b |
| runoff | washed pale stripe | wall colour x 1.10 to 1.25 (never below 0.18 plate brightness) | n/a | period G2, painted look 7 |
| runoff | rust streak | (120, 70, 45) dry, (80, 50, 36) wet | none | period S2 |
| foot | splash band | (62, 52, 45) dry, (45, 38, 33) wet | (95, 100, 85) dry grey-green | period G4 |
| foot | salt bloom | (215, 210, 200) | (225, 222, 212) | period S5 |
| steps | whitened stone | (228, 222, 208) dry, (170, 165, 150) wet | n/a | period S8 |
| steps | scrubbed sandstone | (195, 180, 155) dry, (145, 130, 108) wet | n/a | period S8 |
| wallgrowth / groundmoss | moss dry | HSV (98 deg, 0.45, 0.42) = (77, 107, 59) | the add-on moss tones (linear 0.035,0.075,0.022 / 0.085,0.15,0.04 / 0.15,0.22,0.065 / 0.055,0.105,0.03) | painted look 11; period M1; courtyard 12b |
| wallgrowth / groundmoss | moss wet | HSV (108 deg, 0.55, 0.30) = (43, 77, 34); never below plate 0.25 brightness for readability | brighter saturated green | painted look 11 |
| wallgrowth / groundmoss | algae film | dry (105, 112, 82), wet (48, 62, 42) | same | period M2 |
| groundmoss | liverwort | dry (95, 142, 65), wet (55, 110, 45) | n/a | period M3 |
| dirt | tar new / weathered / chippings | (24, 22, 20) glossy / (50, 48, 44) matt / (100, 98, 92) | n/a | period S6 |
| dirt | rust halo on stone | (160, 110, 80) | n/a | period S1 |
| iron | fresh rust / old rust | (150, 80, 45) / (90, 58, 42) | n/a | period S1, S3 |
| growth | weed leaf dry / wet | HSV (100 deg, 0.50, 0.40) = (68, 102, 51) / HSV (110 deg, 0.58, 0.30) = (40, 77, 32) | fresh green to yellow-green | painted look 11; period W1 |
| growth | dead grass / dandelion flower | (175, 152, 95) / (240, 195, 35) | straw | period W1 |
