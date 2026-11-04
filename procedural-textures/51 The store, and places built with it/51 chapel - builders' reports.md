# 51 Chapel: the two builders' reports

What this file is: the reports of the chapel's two fresh Sonnet builders, word for word (saved by the session). The first was given `51 chapel first pass - builder text.md` and the kit copy with the store (12:18 to 13:23, clock 13:58); the second was given `51 chapel second pass - builder text.md`, the first's script, picture and material list, and the same kit (13:28 to 14:15, clock 14:48). The second pass was the first run under decision 68 (the second pass as a standing part of every build).

---

## First pass

REPORT: the chapel is built and the final picture is drawn. I stopped at 13:23, about 35 minutes before the 13:58 clock. The picture is /home/claude/build-51-chapel/work/final.png (540 x 960).

**What I built**
- A small British Nonconformist chapel, about 1900, at dusk on a wet lane. I used the kit's board photos only for materials and wear, and set it in a mill town.
- The chapel is a gable-fronted gritstone building: the front in courses of dressed stone (the store's stone tool), darkened and cooled so it is not beige; the gable in stone too, with a lit round window; a stone band under the gable, a plaque with no words, and a pair of tall windows with one lit; a double door with a fanlight, one leaf open and the interior glowing orange; three worn steps with a hung lantern by the door; a slate roof with deep eaves, an overhang, barge boards, a ridge and a bellcote; downpipes at both front corners, a stack, a lean-to vestry with a lit window and a chimney with a smoke ribbon.
- In front of it: a flagged path to the steps with kerbs, worn flags, ragged puddles with a wet rim and ripple, fallen leaves and a drain grating; a low railing with spear tops across the front, with an open gate between stone piers; a graveyard with leaning headstones (no words) and grass tufts; two lit gas lamps; the lane in wet setts with a mud gutter and two long puddles placed where the lamps would mirror; far terraces with a few lit windows behind, lost in the haze.
- What the keeper and the congregation left: a besom broom, a zinc bucket and a hurricane lantern by the door; a boot scraper at the foot of the steps, an umbrella and a milk can at the gate piers, a blank notice board.

**Lighting and framing:** the door glow is the main light, with a small warm light just outside the glass lighting the steps and path; the lit window, the two gas lamps and the hung lantern are small secondary lights; a cool moon light and a cool area light over the yard keep the shadows blue-black; the sky and thin haze from the store's sky tool, shifted to teal and slate; the camera at standing height, 6 m back from the gate, on the centre line (I started closer and moved back because the gate piers filled the frame); Cycles with denoise, then the store's finishing step.

**Pictures:** t2 to t18 at 540 x 960; brightness 0.17 to 0.25 throughout; warm share too high until t8 (40 to 55 percent), inside every band from t8 on. Final at 128 samples: 6 min 5 s; brightness 0.25, warm 26%, cool 42%, warm light coverage 3.0%. A 1080 x 1920 script check at 4 samples: 1 min 15 s, inside every band.

**Checked and fixed:** roof slopes that came out as a V; door glow, glass and frames hidden inside the wall; too warm and the stone too beige (cooled, with soot, damp and rain streaks); headstones that read as balls; a smoke ribbon that crossed the roof like a beam. Tried and dropped: a rain-streak layer (scratches) and paper scraps (grey cards).

**Not done:** the chapel's sides and back (never seen); the roof's slate courses barely visible; the broom, bucket and boot scraper small and partly hidden; the setts even in tone; the notice board a dim panel; no leading in the glass; no tracery in the round window. New techniques for the plugin: stain planes (see-through soot, damp, rust and mud), a tint helper, the railing, headstone and terrace code, an amber window glow, a slate-courses roof, a cool area fill over a yard.

---

## Second pass

REPORT: dressing pass on the chapel (finished 14:15 by the computer's clock, deadline 14:48). final.png at 540 x 960, 64 samples, 3 min 39 s. Layout, camera and lights unchanged; the one new light is the keeper's lantern.

**What I changed (the bottom third and the path):** left of the path a red-brown wheelbarrow of stove ash with clinker, a shovel in an ash spill, and a lit hurricane lantern on the setts; between the puddles a black iron coal scuttle with coal tipped out, a coal-dust smear and a closed hymn book; lower down a wet umbrella lying across the setts and horse droppings with oat straws; right of the path a milk churn by the gate pier and two old boards over the gutter mud. Surfaces and wear: boot-mud smears, green damp at the gutter and kerbs, ash along the path, pale worn smears on the steps, soot and damp on the two visible headstones, faint grime over the bottom setts.

**Pictures:** d1 to d21 at 540 x 960, 16 to 24 samples, about a minute each; three finals at 64 samples (3 min 21 s to 3 min 39 s); the last measures brightness 0.24, warm 28%, cool 44%, light 3.6%, inside every band.

**Checked and fixed:** frame positions found by projecting ground points through the camera (the bottom edge is only about 2 m wide); solid mud and cinder patches that read as brown paper replaced by soft see-through smears; sacks that read as stones replaced by the scuttle and lantern; smears over the glossy flags and puddles that killed the shine removed or thinned; the churn and the lantern checked against the puddles' reflection paths.

**Not done:** polished wheel tracks on the setts, rust runs at the railing feet, lichen on the far headstones, a 1080 x 1920 redraw. Still weak: the new things dark, read mainly by outline; the bottom 100 px plain setts; the umbrella thin; the dung heap reads as a dark rock; the barrow's wheel a plain disc.

## Traps

- Both builders stopped early (35 and 33 minutes). The second put its things in the middle of the lane, where they read as rubbish; the rule "where its owner would put it down, never in the open road" is now in `Second pass.md`.
- The second builder reported that wide soft smears on glossy ground kill the shine, and anything standing between a puddle and a lamp blacks out that puddle's reflection.
