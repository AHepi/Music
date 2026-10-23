# Two worked examples: a Japanese garden and a small canal lock

What this is: two places this project really built, walked through the steps of this skill, with their real numbers.
Read one of them before you plan a place of your own, then copy the shape of the work and never the content. Every
number says what kind it is: **measured** (taken from a check, a render or a count on the real scene), **judged**
(chosen from evidence) or **invented** (a guess). Where a number is a pass or a fail of a gate, the gate is named.

The canal lock was built with this very plugin (the smoke test of the first 1.4.0 build). The garden was built before
the plugin existed, with the same ideas done by hand, and it is the place the construction rules and the "shape reads,
shader marks barely do" rule come from. Neither is a plan for your place: yours has its own parts, its own look and
its own facts.

---

## Example 1. A small canal lock side (built with the plugin)

**What was built (measured):** one 12 m side of a small canal lock. A brick lock wall (near side and far side) with
stone coping, a flight of stone steps going down a trench in the towpath, a gravel towpath, grass verges, two water
surfaces (the part-emptied chamber and the higher pound behind the gate), a two-leaf timber gate with balance beams, and
five props (two bollards, a crate, a barrel with two iron bands, a rope coil). 94 objects, 16 roles, 16 materials.
Built by a helper who had never used the plugin and followed only its steps.

**Step 0, the rules of the place.** A style note (chunky and simple, bevels 1 to 3 cm, a muted palette, soft overcast
light, no photographic grain), a small facts file of the lock's own sizes (a lock wall 0.3 to 0.9 m thick, a step
rise 8 to 70 cm counting the block under it, a balance beam 2 to 5 m: all judged, weak, from memory, to confirm), and
an ownership table. The settings and the ownership table are in
`${CLAUDE_PLUGIN_ROOT}/kit/place-kit/data/examples/canal-lock-place-settings.json` and `canal-lock-ownership.json`.

**Step 1, parts and owners.** Four owners: `ground_and_water` (the bed, the towpath, the verges, the water; built first
and frozen), `walls_and_steps`, `lock_gate` and `props`. Each is a stage file made from `place-kit/data/templates/
stage_template.py`. They were combined in two commands: the ground alone into `ground-frozen.blend`, then the other
three with `--order both` from it (plain order, reverse order and the run twice all came out the same: 1.6 s,
measured). Combining the ground with the others in one command fails the order test, because everything else is
seated on the ground.

**Steps 2 and 3, shapes and roles.** Every object was given its role as it was made (`pk.new_part_object`), so the
settings needed no role rules. The gate was built as a real frame: heel post and mitre post, rails tenoned into both
posts, boards on the rails, iron straps, a balance beam on top of the heel post. The construction check passed 88 of
88 parts carried before the pass was run (measured).

**Step 4, the place type and the pass.** A canal has no place type, so the settings started from `harbour` (the
nearest) and the look and state were then set by hand: look `lived_in`, state `damp` (the harbour preset also asks for
wetness on stone and moss on timber, and the settings kept that). The preset's own start was look `neglected`, state
`wet`: the preset is a starting point and the person's words decide. One road was written for the towpath (1.8 m wide,
gauge 0.9 m, rut depth 5 cm, hoof prints on, because the style note called the towpath trodden by the animals that
towed boats; judged). `finish` took 27 to 28 s on this slow computer (measured). What it reported (measured, final
run): 94 objects with UVs and 1024 px normal maps, 33 bevelled by the kit, displacement on 4 objects, 70 objects bent,
leaned or lumped by the damage step (18 left alone), the nine wear layers in 15 materials, 66 plant pieces and 101
litter pieces with none on a wheel track, a worn path or a puddle.

**Step 5, the audit, round by round (measured).** Round 1: 5 FAIL. Round 2: 2 FAIL. Round 3: 1 FAIL. Round 4: pass, 0
to fix, 1 to look at (grass has no displacement; wanted, not required), 18 passed. Some failures were the helper's own
faults, fixed in the geometry; some were faults of the plugin itself (listed below). No requirement was lowered. The
final audit also held: 88 parts carried, 46 sizes fitting the lock's own facts, 13 normal maps Non-Color, tangent and
pointing the right way (`normals-test`: sun from +X reads 0.794 against 0.415 for the flipped-green control), 0
percent plain boxes. `explainer-film-preflight place` then passed: 0 to fix, 2 to look at (the grass; no fresh checker
had looked yet).

**Step 8, pictures.** A hero picture 1200 x 800 with EEVEE here (80 s, 48 samples), and two close-ups 1600 x 1067 in one
job on the rented card, one with EEVEE and one with Cycles (96 samples, 3.7 s for the Cycles draw): 49.5 s of billed
work in all, no waiting in the queue. All three carried the same scene hash as the audited file (measured).

**Did the pictures show the treatments?**
- Measured: with the wear on against master 0, tiny 480 x 320 pictures differ by 3.7 percent (hero) and 2.8 percent
  (close-up) in mean pixel change, and 33 and 41 percent of the pixels move by more than 8 of 255.
- Judged by eye: normal maps clearly (brick courses, wood grain, gravel); dirt, grime and moss faint at hero size and
  clearer in the close-ups; weeds yes but sparse; damage as shape yes (crooked boards, a leaning gate leaf); the
  waterline stain, the litter and the rubbish not visible; the water a flat dark slab in EEVEE and far better in
  Cycles; the value range compressed (1 percent at 0.21, 99 percent at 0.65) and the detail energy 1.4 against the
  style note's 3 to 9. This is why the renderer rule now picks Cycles when water is in view.

**What the build found wrong with the plugin itself** (all fixed in the 1.4.0 fix round; each has a test): a scene whose
objects had no material at all passed the audit; `undo` crashed after the kit added the sun; the roads step rebuilt a
thin towpath strip as a grid, filled the trench cut in it and moved the stairs up 2 m without saying; the ground-seat
check read raw box corners, so a wall beside higher ground failed for no reason; the plain-box check failed stone and
steps that no verb bevelled; correct joinery (rails tenoned into two posts) was called a failure; there was no role
for steps; and `combine --order both` with the ground in the list failed. Lesson: a gate is only as good as the cases it
was tested on, so build one small place of your own kind early and read every FAIL.

---

## Example 2. The Japanese garden (built by hand, before the plugin)

**What it was (measured):** a walled courtyard garden with a hall and veranda, a pond with a plank bridge on piers, 43
stones (rocks, pond-edge and stepping stones) and a gravel court raked in lines, a stone lantern, a basin, a maple and
a pine, bamboo, a tile roof and plaster walls. It was built in Blender on 18 October, improved on 21 October (a plan
of 11 ranked improvements, four builders and one final step) and given its character on 22 October (details as
designed parts of its own art style: planks with rounded edges, tiles in different tones, walls with cracks, moss
cushions, 12 tuft shapes, a bridge that stands up).

**The look.** Realistic surfaces kept inside the garden's own art style (few, big, clean marks rather than
photographic noise), with the weathering kept calm on stone. The style note turned the film owner's rule into "the
rule for every builder": wear, moss, cracks and stains are designed parts of the style.

**What a ray check found before any rebuilding (measured):** a veranda step floating 23 cm in the air; bridge posts
2.2, 2.5, 5.0 and 4.4 cm short of the boards; wall caps floating 6.5 cm; a roof 22 cm off its posts; a lantern glow box
buried in solid stone (it read as a flat white cut-out); 77 deck faces fighting the plinth top (fixed by lowering the
plinth top 1 cm). None of these was visible at the hero camera. This is why the construction check is a required
step.

**The bridge, rebuilt from the bottom up (measured by a fresh checker in the saved scene):** flat footing stones on the
pond bed; square posts 14 cm across with a 1.5 cm chamfer; cross beams notched and pegged into the post pairs; long
beams on the cross beams; planks across them with a gap between; round pegs and a few iron cramps. 59 planks, none on
fewer than 2 supports; 18 posts, each on a footing; the longest unsupported stretch 0.85 m (the rule is 1.4 m or less);
a walk line along the middle met a plank the whole way. The same checker found 3 footing stones with a one-sided air
gap of 2.5 to 13.5 cm: prove it, then look at what the proof missed.

**Surfaces and shape (measured counts, judged results):** 85 materials use 17 real normal-map pictures, each checked
to point the right way. Maple leaves went from 20 to 34 cm wide to 5 to 12 cm (the real size) and were counted at
56,000. The gravel court was changed from dark pink-brown to pale grey with straight rake lines every 12 cm, about 1.5
cm high (judged). Rocks were to be set about a third into the ground (22 percent before; judged). Concept pictures
showed what "designed wear" meant before anything was built.

**What the garden taught the plugin:**
1. Shape read at film size and shader wear barely did: planks that are all different, tiles that are chipped and slipped,
   tufts with seed heads, moss cushions. So the pass has a damage step that works in the geometry.
2. A builder's claim is not a measurement. One builder wrote that 9.8 percent of the planks carried moss; a fresh checker
   counted 0.6 percent olive dots on one run of planks and 3.8 percent on the other.
3. A weathering layer that is right on a wall can look like a sticker on a lantern or stripes on a rock: tone the layers
   down on stone and keep the marks few and soft.
4. The squint test missed (0.883 and 0.873 against a line of 0.92) because the maple and the pond followed the concept
   pictures. Report it and let the person decide; never remove character to chase a number.
5. Still weak after the last round (judged): the lawn colour under the tufts was an old smeared scan, the moss cushion
   banks still heaped up, and drip stains, slipped tiles and ripples only read close up.

---

## What to copy into your own place

- The shape of the work: a style note and a facts table first; the ground built first and frozen; a few owners; every
  object given its role as it is made; the pass; the audit read line by line; fresh checkers; a plain report.
- The numbers you may reuse carry their kind: a gauge of 1.24 m between wheel ruts and a rut depth of 0.15 m belong
  to a coal-mine yard that was built earlier in this project (measured in its build code); the garden's 1.4 m longest
  free span and its bevel sizes are judged. Your place has its own facts: write them down with a source.
- The words that decided the settings were the person's words (kept, lived in, unkempt, ruined; dry, damp, wet), not the
  place type. Read the table in `SKILL.md`.
