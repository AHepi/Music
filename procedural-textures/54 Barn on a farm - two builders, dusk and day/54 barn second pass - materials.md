# Materials: a barn on a farm, second pass (dressing)

What this file is: the list of what the second pass adds to the first builder's farmyard, written before dressing and kept true while dressing. The first builder's list (`first pass/materials.md`) still holds for everything it names; this one only adds. One line per thing: what · made of · how it has aged · where the wear sits · which surface it uses.

## Who uses this place (the first builder's people, kept)

- **Who is here (not in the picture):** an old carter and a young woman farm hand, November 1915, on a small mixed farm in the south of England; the farmer's sons are at the war.
- **What they do all day:** milk at dawn and dusk, muck out, cart roots from the clamp in the field and dung out to it, fork hay down, water the horse, mend things in the barn doorway.
- **What they left when they stepped out of frame (added by this pass):** the afternoon's cartload of mangolds tipped against the foot of the dry-stone wall beside the lane; the farm hand's wicker skep half filled from it, set down at the heap's foot, and her fork stuck in the heap where she left off when she went to light the lanterns; her trodden way off the lane to the heap.

## What this pass adds (as built)

| what | made of | how it has aged | where the wear sits | surface used |
|---|---|---|---|---|
| heap of mangolds, tipped against the wall foot on the left verge, bottom left of the frame (about 330 roots) | mangold roots, 11 to 14 cm across, 25 to 33 cm long, fat at the crown tapering to a tail | lifted a week ago: skins dull orange-yellow to red, soil caked on the tail ends and in patches | soil darkest on the tails; dull where soiled, a little sheen where clean after the rain | made in code (each root its own colour, soil by its own height and by noise, roughness follows the soil) |
| roots rolled out of the heap | the same | the same | six lie on the verge between the heap and the lane, none in the lane or on the trodden way | made in code |
| roots dropped near the eye | the same | the same | three that bounced off the cart as it came along the lane, lying in the verge's grass below the skep, none in the lane or on the trodden way | made in code |
| soil spilled where the cart tipped | earth off the roots | wet | a smear round the heap's foot on the verge, off the lane's glossy ruts (it hardly shows at the final size) | store tool `stain.on_ground` (mud, strength 0.55) |
| wicker skep (round farm basket), half full of mangolds | woven willow bands going in and out over the stakes, a thick rim, two loop handles, a dark liner | greyed and dark with wet | the rim and handles rubbed pale by hands; at the heap's lane-side foot, on the edge of her trodden way | made in code (woven bands in relief; `willow, greyed and wet`, colour broken by noise; rim `willow rim, rubbed pale`) |
| the farm hand's root fork, stuck in the heap | ash shaft, a D handle, iron tines buried in the roots | shaft greyed | the grip and the D rubbed pale by hands | made in code (`ash shaft, greyed`, `ash grip, rubbed pale`; tines `RUST • rain-aged iron`) |
| her way off the lane to the heap | the verge's earth, trodden bare | wet, boot prints in it | from the lane's left edge to the skep and the heap's foot; the grass worn off along it | store tools `tracks.path` (0.45 m, age 0.45) and `tracks.footprints` (age 0.12), carved before the grass grows |
| the near forkfuls of dropped hay (the first builder's, nearer than 4 m) | hay | trodden flat into the mud | short strands, most pressed dark; the one beside the skep almost all dark | the first builder's `straw_clump`, called with more strands, shorter, more trodden (the pale ones read as stars, and beside the skep as matchsticks) |
| moss on the dry-stone wall | moss | patches | on the cope and the ledges (upward faces) and up the foot, in patches | `add_moss` made in code over the first builder's `SURFACE • old_stone_wall_02` copy |
| sheet of rusty corrugated iron nailed askew over rotten boards, barn front left of the door, above the gate | corrugated iron, 0.95 x 0.85 m, nailed top and bottom | rusted orange-brown, wavy where nailed over uneven boards | a rust run on the boards below it | made in code (real corrugations), `SURFACE • rusty_corrugated_iron` copy (lighter, Grime 0.35, Wet 0.3); nails `MADE • rusty nail heads`; run `stain.on_wall` (rust) |
| damp runs on the barn gable | rain water | dark streaks | under the loft door, under each air slit's sill, under the right eaves (they hardly show at the final size) | store tool `stain.on_wall` (damp) |

## Kept true while dressing

- **The stone trough by the gate and the carter's bucket were not built.** Worked out before building: from the eye the trough's water would be a sliver 3 px high and the trough a plain block at 10 m, so it would not be named. The fork in the heap, the trodden way and the tin patch took its place.
- **A sack of chaff leant on the near gate post was built and taken out:** at the final size it read as a boulder (a smooth egg shape, the sacking too fine to see).
- **The mangolds were made darker and slimmer after the first picture:** at first they were round and peach-pink and read as a heap of peaches.
- **The two rolled roots on the farm hand's trodden way were moved off it.**
- **Three dropped roots were added near the eye in the last picture,** in the dark verge below the skep, so the heap's story reaches the bottom edge.
- **The skep's rim and handles were rubbed pale** in the last pictures: with the rim the same grey as the weave, the basket's mouth did not show.
