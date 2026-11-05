# 55 Store helper for the street things - report

What this file is: the report, word for word, of the helper that made seven new parts for the store from what the three street builders made by hand (5 November 2026). Saved by the session.

---

All seven parts are in the store, each with its four cards and its saved part file. Running `tests/test_store_parts.py`, all seven pass: foot, size against the card, nothing floating, every option built, a wrong option refused. The run as a whole still exits 1: it stops at `stair_door`, another helper's part that has no part file yet. Mine all come before it alphabetically, so all of them were checked, but the parts after it were not. I didn't run catalogue.py or touch Store.md. I took about 105 minutes, over the 75 you asked for; most of the extra went on the chimney soot (mistake 7 below).

**The parts** (size at the default options; the card's source names the builders' script and lines)
1. **ash_bin**, 0.56 x 0.53 x 0.75 m. Options: `lid` 'on' / 'off' / 'leaning', `ash` 'heaped' / 'low'.
   - The builders made a solid cone with ash laid on its top. Now it is a hollow drum with a rolled rim, so an open bin has a mouth and the ash sits in it.
   - The dents bend the ribs and the ash along with the wall, so nothing pokes through.
   - The handles hang from lugs, the lid is hollow underneath, and the clinker sits on the ash surface.
2. **drain**, 0.80 x 0.80 x 0.06 m. Option: `kind` 'cover' / 'grate'.
   - The builders used boxes and discs in two store materials. Now it is a frame with a separate lid (gap, lifting holes, raised rings, ribs and studs) or a grate over a black pit.
   - One made iron material puts wear on what stands up and rust in the hollows by itself.
   - Its origin is the road surface, not its lowest point: it goes 5 cm below z = 0. The card's trap says this.
3. **sett_stack**, 1.16 x 0.65 x 0.41 m. Options: `layers` (default 3), `loose` (default 2).
   - The builders stacked plain boxes all the same way. Now each sett is a little out of square with chamfered edges, the courses cross, the top course has gaps, and a made granite shows its grain.
4. **newspaper**, 0.45 x 0.33 x 0.01 m. Option: `kind` 'folded' / 'sheet'.
   - The builders used a 9 x 7 grid rippled by a sine. Now it is finer, with real creases, torn edges, two leaves when folded and one corner turned back. The paper is wet in patches, with no print.
5. **chimney_stack**, 2.75 x 1.00 x 3.10 m. Options: `pots` (default 5), `stone` 'rubble' / 'ashlar' / 'brick', `height` (default 1.4).
   - z = 0 is where it meets the ridge or wall top. A root block goes 1.0 m below, hidden in the roof, as the builder did. Its card carries `foot_z: -1.0`, the same way `teapot_sign` does, so the test skips its centring check.
   - The pots are now turned, hollow and set in mortar. There is a projecting course near the top and a stone cap, and the soot is built into the materials, heaviest at the top.
6. **sack_barrow**, 0.63 x 0.59 x 1.20 m. Option: `sack` False / True.
   - The builders used plain cylinders and solid disc wheels. Now it has rails ending in grips worn pale, a nose plate with straps, stays to the axle and spoked iron-tyred wheels.
   - It leans 17 degrees onto a wall at +Y.
7. **coster_barrow**, 1.24 x 2.25 x 0.96 m. Option: `rest` 'legs' / 'handles'.
   - The builders made the bed, sides and handles from round rods. Now it has a bed of boards on bearers, side boards and a front board, an axle with a wooden block under the bed, 12-spoke wheels with iron rims, grips and legs.
   - With 'handles' it has no legs and is tipped back about the axle until the grips touch the ground.

**What does not read well yet**
- The ash bin's store cards show the lid on, so the ash and clinker only show with the lid 'off' or 'leaning'.
- The chimney stack is small in its cards, because the hidden 1 m root counts in the framing. Its soot reads on the pots and cap but only as streaks on the stack itself.
- The newspaper's creases are shallow; from far off it is a pale patch.
- The drain's flat frame reads pale, and its lifting holes are too small to see.
- The sack on the sack barrow reads as a soft block, with no tied neck.

**Mistakes I made and fixed**
1. The heaped ash came up through the closed lid. With the lid on, the ash now lies low under it, with no clinker.
2. The lid's strap handle was flat the wrong way. Fixed before the first build.
3. The leaning lid hid the bin in the three-quarter card. Moved it to the front-left.
4. Drain:
   - The raised rings would have made solid discs across the lid. Fixed by building them open-ended.
   - The frame's top lay exactly at z = 0, where it would flicker against a road surface. Lifted 1 mm.
   - The worn tops read dark, because a mirror-like metal shows the dark sky. Made the worn iron lighter and only half-metal, and the rust darker.
5. The setts' chamfered edges reached 7 mm under the ground. The stack is now lifted back onto it.
6. The newspaper's turned-back corner had its faces pointing down. They are flipped up now.
7. The chimney soot never went fully black and streaked where there should be none. I changed how the streaks combine with the soot amount. I also lost time chasing a fault that was really the close card cutting off the sooted pot tops.
8. Card text: inside each option's text I quote only that option's own values, because the test tries every quoted word as a value.

**Files I created** (all under /home/claude/music/plugins/painted-place/brief/store/)
- `parts/src/_shapes_street_things.py`, my shared helper. It holds soot over any material and the made materials (bin, worn iron, clinker, clay, mortar, granite, newsprint), plus a heap shape.
- `parts/src/ash_bin.py`, `drain.py`, `sett_stack.py`, `newspaper.py`, `chimney_stack.py`, `sack_barrow.py`, `coster_barrow.py`
- `parts/ash_bin.blend`, `drain.blend`, `sett_stack.blend`, `newspaper.blend`, `chimney_stack.blend`, `sack_barrow.blend`, `coster_barrow.blend`
- `cards/parts/<name> - three.png`, `- close.png`, `- side.png`, `- back.png` for each of the seven (28 pictures)
- Scratch files outside the plugin, safe to delete: /tmp/street_things/ (a check script and look renders).

Two things the plugin did not carry before, which now live in my helper module: soot laid over any material by a per-point soot amount, and cast iron that wears bright on whatever stands proud of the road.

---

## Traps

- This is the helper's own account. What the session checked afterwards is in the project story, log 55: the store's tests, and the cards it looked at.
