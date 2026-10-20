# Notes - brick reuse trial

What this file is: the plain-words report of the BRICK reuse trial. The question was "how much of the tools can be used on the other textures
now?". I answered it for brick by building it: a brick wall made from the shared slate layers (taken unchanged from the frozen snapshot),
with only their settings changed, plus the smallest new parts I could not avoid. Everything is in this folder
(`reuse_trials/brick/`, 55 MB). Written on 20 October.

---

## 1. The short answer

**Brick needs no change to any shared layer.** COLOUR AND FADE, DAMAGE, OUTLINE AND SHADOW and COMBINE ran exactly as they are in the
snapshot (the checksums still match). Only their settings differ from slate. MOSS also ran unchanged, but it has no job on this brick wall, so
it is switched off.

Three small new parts were needed:

| new part | nodes | why no shared layer could do it |
|---|---|---|
| **GRIME** (`grime.py`), a new paint layer with the same sockets as the others | 161 | Soot runs over bricks AND mortar, and the mortar has mottled patches. MOSS and DAMAGE only paint on the pieces, and COLOUR AND FADE lies under the mortar paint. |
| **BRICK HEIGHT RULE** (`height_rule.py`), a box after COMBINE | 13 | COMBINE's "height from brightness" rule is slate's rule, and no setting changes it. On brick it cuts off the top 7 % of dots and flattens the height map (height group 0.30). The brick reference's own rule gives height group 0.60. |
| **BRICK LAYOUT** (`brick_layout.py`), the small layout the task asked for | 118 | Not strictly needed: the shared slate LAYOUT also makes a good brick wall by settings alone (overall score 0.646 against 0.654). The new layout gives the proper half-brick running bond; the slate one slides each course by a random amount. |

**Counted in nodes** (one node = one small step Blender works out for every dot):
- Shared, unchanged: 1,530. That is COLOUR AND FADE 419, DAMAGE 439, OUTLINE AND SHADOW 216, COMBINE 22, MOSS 419 (built but off) and the seamless-noise helper 15.
- New: 292. That is BRICK LAYOUT 118, GRIME 161 and BRICK HEIGHT RULE 13.
- The recipe's own wiring is 10 nodes, copied from the slate recipe.
- So **84 % of the nodes are shared** (79 % if the switched-off MOSS is not counted).
- With the shared slate LAYOUT instead of the brick layout, the new part is only GRIME and the height rule (174 nodes), and **91 %** is shared (89 % without MOSS).

**Counted in lines of code** (comment lines not counted):
- Reused unchanged: 987 lines (the four paint layers, COMBINE and the interface helper; 792 without MOSS), plus 171 for the shared LAYOUT if it is used.
- New boxes: 211 lines (brick layout 92, GRIME 93, height rule 26).
- Recipe wiring: 134 lines, mostly a copy of the slate recipe.
- Settings: 37 lines.
- Tools and tests: 388 lines.

**How close is it?** At the like-for-like size (1254 dots) the trial scores **same-kind 0.654** (colour group 0.642) on the seed set I tuned on. Over
three seed sets it averages **0.615** (colour 0.584). The brick's own earlier recipe tile, scored the same way, has **0.725** (colour 0.750). The
first layered brick had 0.194 (colour 0.152). So the layered route has climbed most of the way, but the earlier brick recipe still looks closer
and scores higher. Section 4 has the full table.

---

## 2. What was reused, and how

| part | how it was used | what it does on brick |
|---|---|---|
| layer interface (`layer_interface.py`) | unchanged | every box, old and new, is built with it; GRIME has exactly the same sockets as the shared layers |
| COLOUR AND FADE | **settings only** | the bricks' own colours. Nine reds and oranges from the measured 16-colour palette of the reference; flat round patches inside each brick (the three "no tongues" settings from the inventory: `fade_direction` 0, `fade_length` = `streak_width` = 0.03, `mottle_tallness` 1); some paler and darker bricks; big orange "sun-bleach" areas across bricks; a fine grain |
| DAMAGE | **settings only** | pale spalls at brick edges and corners, in pale tan mortar-like colours; a few hairline cracks; broken corners show mortar colour, not black |
| OUTLINE AND SHADOW | **settings only** | the mortar's flat base colour (the "joint" colour); the thin dark outline round every brick; a short shadow under the top edge; the "lip" turned into a dark lower rim |
| MOSS | unchanged, **off** (`moss.amount` 0) | tried twice as soot (section 6); it did not help, so it is off |
| COMBINE | **settings only** | stacks the five layers (it makes one set of inputs per name in `recipe.stack_order`, so GRIME needed no change there); `tone_blend` 1 |
| LAYOUT (slate) | **settings only**, tried as the alternative | 12 courses of 4 bricks, 20-dot head joints, 18.6-dot bed joints, rounded corners, chipped edges. It works; random course slides instead of a half-brick bond |
| `lib/bake_harness.py`, `lib/texture_compare.py`, `make_normal.py`, `description_audit.py` | as they are | baking, scoring, normal map at strength 6, settings check (`settings.json` is 4.6 KB, passes the 8 KB limit) |

**How the brick settings were chosen.** I measured the reference once, as a guide (`measure_reference_once.py`, `reference_measures.json`):
- **Palette:** taken from the stored 16-colour palette.
- **Layout sizes:** taken from the stored layout numbers.
- **Soot cover and cloud size (two new numbers):** soot clouds cover 11.5 % of the picture once the thin dark ring is removed. A whole cloud is about 60 dots across and 43 dots up and down.

Then I hand-tuned over six rounds of "look, change one or two things, look again". No optimiser, no tracing, nothing per brick.

---

## 3. What was new, and why

1. **GRIME** (new paint layer, last in the stack, 161 nodes). This is far more than the 40 to 60 nodes the inventory guessed: four seamless noises, two cover-share cut-offs and five "paint over" steps. It does two things:
   - **Mortar mottle**: flat pale, palest and dirty patches, about 9 dots, painted only in the gaps.
   - **Soot**: slow up-and-down clouds roughened by fine runs. Each cloud has a solid middle that breaks up into flat specks at its rim, in two tones (a lighter soot that lets the brick show through, and a dark heart).

   It reads only Vector, Tile Count, `gap_mask`, its own Seed and its settings. Amount 0 switches it off through the shared `finish_layer`. The independence test showed that switching it off changes colour only inside its own mask. I did not separately bake its mask at Amount 0. The inventory's part 3 ("low-spot darkening" for gravel) was **not** written.
2. **BRICK HEIGHT RULE** (13 nodes, after COMBINE). It makes the height from the finished colour by the brick reference's rule:
   - The rule: height = 2.533 × (grey − 38.7) / 255.
   - Where it comes from: a straight line fitted once to the 12-point curve stored in `recipes/brick/generator/sampler_model_brick.json`. Its worst miss is 6.3 of 255.
   - Why it matters: COMBINE's built-in rule (2.5 × (brightness − 9.5)) is slate's. With it, 6.9 % of the dots sit at the very top of the height range, against 0.1 % in the reference.
   - Effect, in the same bake: height group 0.299 → 0.597, normal group 0.456 → 0.634, overall 0.538 → 0.654.
   - The reference's height also had a slight blur. A shader sees one dot at a time, so this rule cannot do that.
3. **BRICK LAYOUT** (118 nodes). The task asked for it, and it gives the eleven bundle numbers like the slate LAYOUT does:
   - 12 courses with a half-brick bond;
   - every upright joint moved by its own random amount, so brick lengths differ;
   - 20.4-dot head joints and 18.6-dot bed joints;
   - rounded corners (9 dots) and edge dents;
   - mortar low, bricks high in the bare relief.

   It is optional: the shared LAYOUT with brick settings scores almost the same (section 4).

No shared layer was copied or changed. There is no `*_changed_for_brick.py` file.

---

## 4. Scores, like for like

Every row below:
- is 1254 dots;
- was scored by `lib/texture_compare.py brick` (the "same kind" score, 0 to 1);
- has its normal map made from the height by `make_normal.py` at strength 6 (the brick reference's strength).

All scores are in `final_scores.json`; the same bakes with COMBINE's own height rule are in `final_scores_combine_height_rule.json`.

| tile | same-kind (overall) | colour group | height group | normal group | tiling |
|---|---|---|---|---|---|
| **trial, seed set 1** (the one I tuned on) | **0.654** | **0.642** | 0.597 | 0.634 | 1.000 |
| trial, seed set 2 (every seed + 100) | 0.615 | 0.595 | 0.556 | 0.618 | 0.970 |
| trial, seed set 3 (every seed + 200) | 0.577 | 0.516 | 0.551 | 0.612 | 1.000 |
| **trial, mean of the three** | **0.615** | **0.584** | 0.568 | 0.621 | 0.990 |
| trial with the SHARED slate LAYOUT, seed set 1 | 0.646 | 0.634 | 0.583 | 0.633 | 1.000 |
| trial seed set 1 with COMBINE's own height rule (no new height box) | 0.538 | 0.642 | 0.299 | 0.456 | 1.000 |
| trial, mean of three with COMBINE's own height rule | 0.503 | 0.584 | 0.282 | 0.440 | 0.990 |
| **baseline: the brick's earlier recipe, new tile 11** | **0.725** | **0.750** | 0.704 | 0.566 | 0.962 |
| the same tile with its normal remade by `make_normal.py` at strength 6 | 0.725 | 0.750 | 0.704 | 0.566 | 0.962 |
| the first layered brick (stored score) | 0.194 | 0.152 | 0.154 | 0.000 | 1.000 |

(The surveyor's figure for all 8 of the earlier recipe's new tiles is 0.708 on average, from 0.684 to 0.730. I re-scored only tile 11.)

**Where the trial is behind tile 11** (seed set 1):
- colour feature sizes (spectrum 0.33 against 0.52; scale 0.74 against 1.00): my patches run 17 dots before they change, against 13 in the reference;
- colour edge sharpness (gradient 0.51 against 0.61);
- how closely height follows colour (0.54 against 0.995). Mine follows it TOO exactly (0.997 against the reference's 0.974), because I cannot blur;
- normal-height agreement (0.00 against 0.70), for the same reason.

**Where the trial is equal or ahead:**
- colour spread (0.865 against 0.855);
- normal tilt and components (0.65 and 0.93 against 0.42 and 0.71);
- height contrast (0.96 against 0.77);
- seam (1.00 against 0.96).

**The seed matters a lot.** The colour group goes from 0.642 to 0.516 across the three seed sets. That spread is wider than the 0.03 to 0.07 the
inventory expected. I tuned on seed set 1 only (one look at another seed in round 3), so seed set 1 is the flattering number. The fair number is
the mean.

---

## 5. Proof tests (all run and measured; files in `checks/`)

- **Half-tile shift test** (512 dots; `checks_run.py` part 1, measured by `checks_analyse.py`). It slides the picture by half a tile and checks that it equals the plain picture rolled round. Result: **the tile repeats**.
  - Finished colour: average difference 2.9 of 255, and 0.03 % of dots differ by more than 40. A wrongly rolled control gives 32.4 and 31 %.
  - Brick map: 1.0 and 0.3 %. Edge distance: 0.8 and 0 %.
  - GRIME mask: 6.0 and 5.7 % (control 67 and 41 %). I checked where those 5.7 % lie. They are spread over the many one-dot edges of its specks, and are no denser at the old picture edge than at any other mortar row (0.199 against 0.17 to 0.21). Not a seam.
  - With 2 tiles across: again it repeats (colour 4.7 and 0.14 %), and the picture is NOT a copy of itself one base tile over (29 and 25 %), so it is new content.
- **Seam score** in the like-for-like bakes: 1.00, 0.97 and 1.00.
- **2 x 2 repeat** (`repeat_2x2_brick.jpg`): I looked. No seam is visible. The repeat of soot clusters shows, as any one-tile repeat does.
- **Independence test** (320 dots; `checks/checks_tables.md`):
  - **Amount 0**: every layer changes colour only inside its own mask (0.0 % outside, for every layer).
  - Height changed outside the mask on 0.004 % to 0.37 % of dots (OUTLINE 0.37 %). I think this comes from the height rule: a colour change too small for the colour threshold (2 of 255) becomes a height change above the height threshold (2.533 × 2/255 = 0.02 > 0.002). That explanation is by reasoning; I did not test it.
  - **Seed + 1** rows show changes outside the mask (DAMAGE 6 %, OUTLINE 0.8 %, GRIME 15 %). That is expected and not a leak: they are measured against the OLD seed's mask, while the new pattern lies in new places. I did not bake the new-seed masks, so these rows prove nothing either way.
  - MOSS (off) changes nothing either way, as it must.
- **Snapshot fingerprints**: `sha256sum -c checksums.txt` reports OK for all seven files after all my runs. No cache folder was written into the snapshot.

---

## 6. Does it read as brick? (honest)

**Yes, at a glance.** `sheet_brick.jpg` shows:
- an old red-orange brick wall in a running bond;
- mottled grey-brown mortar;
- a dark outline round each brick;
- pale spalls and soot.

All four final tiles read as brick (`final_seed_sets.jpg`).

**Next to the reference, or up close, it is clearly weaker than the earlier brick recipe's tile:**
- **Soot** is small dark flecks and blotches. The reference has larger soft dark smudges that run down over two or three courses.
- **Spalls** show as pale bands along the lower edges and at corners. DAMAGE was built for slate, where flakes gather at the lower edge. The reference's spalls are ragged patches anywhere along an edge.
- **Patches inside the bricks** are flat cells with fairly straight edges, a cut-paper look. The reference's are ragged and grainy.
- **Mortar** is a little darker and more even than the reference's.
- **The right-hand shadow** of each brick is missing. OUTLINE AND SHADOW has no left/right-specific shadow.

---

## 7. What is missing to make it better

1. **Soot as smudges, not flecks.** GRIME's speck size is one size only. Small specks give flecks; big specks gave isolated black blobs in round 6. A second, larger soft tone (a smear that darkens without specks) is the likely fix. It is a GRIME code change, in my own file.
2. **Spalls anywhere along the edge.** DAMAGE always prefers the lower edge (side and top reach are fixed shares of it). The fix is a code change in a copy, or a small SPALL layer.
3. **Ragged patch edges.** Try more of COLOUR AND FADE's `edge_ragged` and `streak_bend` (only 0.004 and 0.01 were tried).
4. **Height.** Mix a little real relief into the height rule (`height_rule.blend` about 0.9) so height follows colour less perfectly. Not tried.
5. **Seeds.** Tune looking at three seed sets at once, not one.
6. **Take MOSS out of the stack** (`recipe.stack_order`). It is off, but its 419 nodes are still worked out for every dot. I kept it in to show that "Amount 0 = nothing" holds.
7. **Right-hand shadow.** The EDGE LIGHT layer suggested for metal would also serve brick.

---

## 8. Failures (recorded as they happened)

- **MOSS as soot, twice.**
  - First as drips: a comb of dark drips hung from the top of every brick. It read like slate moss, not soot (`rounds/round_1_sheet_a.jpg`).
  - Then as dark clumps only: almost no visible difference (`rounds/round_2_sheet.jpg`).
  - Result: MOSS is off.
- **GRIME first version.** Two hard cut-offs made hard-edged black blobs (round 1). I rewrote it so a cloud dissolves into specks at its rim.
- **Round 3 overshoot.** Too much soot (37 % dark dots against the reference's 24 %) looked like ink splashes, and stronger corner spalls made beige wedges. Both were pulled back in round 4.
- **Round 6 went backwards.** Bigger soot specks gave isolated black blobs, and the colour group fell to 0.598 from 0.642. I went back to round 5's settings.
- **More grain made the colour gradient score worse** (0.48 → 0.14).
- **640- and 768-dot views scored with the compare tool are NOT like for like.** Enlarging blurs them, so their "scale" and "gradient" scores drop to 0. I used them for looking only. Every number in this report is from 1254-dot bakes.
- **Blender run 7 failed at once.** My command chain stopped before it wrote `final_sets.json`, so Blender got an empty list. Nothing was baked; run 8 repeated it.
- **A scratch helper I wrote to edit `settings.json` broke the file once** (a stray comma). Fixed by hand before any bake used it.
- **COMBINE's height rule** turned out to be slate-only (section 3). That is why the height box had to be added.
- **GRIME is 161 nodes**, about three times the inventory's estimate.

---

## 9. What I did not test, and what I am unsure of

- **Two runs make the final maps.** The final colour, roughness and metallic were baked in run 8, before the height box was switched on. The final height was baked in run 9 with it on. By its code the height box only changes the Height output, so the maps match the current `settings.json`. I did not re-bake the colour to prove it.
- Roughness and metallic were not checked against anything (the reference has none). Metallic is 0.
- **Independence "Seed + 1" rows** are not a clean proof (section 5). The small height changes with Amount 0 are explained by reasoning only.
- **The 2 x 2 area of new content** (`recipe.tiles_across` 2) passed the half-tile test, but I did not look at it or score it.
- The shared slate LAYOUT variant was baked with seed set 1 only.
- **Not done:** the "what each layer adds" ladder, GRIME's part 3 (low spots, for gravel), and anything for the right-hand shadow.
- Timings were taken while another helper was baking at the same time: 2.8 minutes per full 1254 set (colour, height and roughness about 55 seconds each); about 17 seconds per 512-dot view.
- **Unsure:** whether the inventory's "settings only" verdict for DAMAGE on brick is fair. It runs by settings, but the spalls do not sit where brick spalls sit.

---

## 10. Files in this folder

- **The recipe:**
  - `brick_recipe.py`: the recipe the harness loads. It imports the shared layers ONLY from the snapshot and refuses to run if any came from elsewhere. It keeps `shift`, `debug_view`, `recipe.tiles_across` and `recipe.stack_order`, and adds `recipe.layout` and `recipe.height_rule`.
  - `settings.json`: all brick settings (4.6 KB).
- **New boxes:** `brick_layout.py`, `grime.py`, `height_rule.py`.
- **Pictures:**
  - `sheet_brick.jpg`: reference | earlier recipe tile 11 | this trial, then the same enlarged, then the bricks and each layer's mask.
  - `repeat_2x2_brick.jpg`: the trial tile laid 2 x 2.
  - `final_seed_sets.jpg`: the four final tiles side by side.
- **Final bakes:** `final/seeds_1`, `seeds_2`, `seeds_3` and `shared_slate_layout_seeds_1`. Each holds colour, 16-bit height, roughness, metallic, normal (strength 6), `score.json` and `score_combine_height_rule.json`. Seed set 1 also keeps its height and normal from COMBINE's own rule.
- **Scores:** `final_scores.json`, `final_scores_combine_height_rule.json`, and `baseline_tile_11/` (scores only; its pictures were deleted after scoring).
- **Tests:**
  - `checks/`: `checks_tables.md`, `half_tile_results.json`, `independence_results.json`, `node_counts.json`, `node_counts_with_shared_slate_layout.json`, and the layer masks (`masks/`).
  - `rounds/`: the six tuning rounds (sheets, the views asked for, logs; the view pictures themselves were deleted to save space).
- `look/`: three JPEGs I looked at once at the start (the reference whole and a corner, and the earlier tile 11).
- **Tools:** `count_nodes_with_shared_layout.py` (run 11), `run_views.py`, `final_bake.py`, `checks_run.py`, `checks_analyse.py`, `final_scores.py`, `make_look_sheet.py`, `make_brick_sheet.py`, `seed_sets_sheet.py`, `measure_reference_once.py` and `reference_measures.json`.
- `blender_runs.log`: every Blender start. There were **11**: 6 tuning rounds, 1 failed start, the final bake, the height-only bake, the checks, and one node count.

**To bake it again** (from `proc-work`):

`blender -b --disable-autoexec -t 2 --python reuse_trials/brick/final_bake.py -- reuse_trials/brick/final 1254 '{"seeds_1": {}}'`

then `python3 -I reuse_trials/brick/final_scores.py`.

The plain harness (`blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- reuse_trials/brick/brick_recipe.py OUT --size 1254 --normal-reference brick`) should also work, because it loads the recipe the same way, but **I did not run it** in this trial. It would make the harness's own normal maps, not the strength-6 one used for the scores.
