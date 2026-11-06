# Materials - rocks pass

What this file is: the material list for the surfaces this pass changed (the rocks), in the form `Before you build.md` asks for. Everything not listed here is as in the earlier builders' lists (`earlier59/materials - first pass.md`, `- second pass.md`, `- closer pass.md`).

Who is here: the inn's guests and the maid, as in the earlier lists. The rocks are older than any of them: set by the garden's maker long ago, never moved, weathered and grown over since; nobody walks on them except the basin's front stone, where a guest stands to wash.

| What | Made of | How it has aged | Where the wear sits | Surface |
|---|---|---|---|---|
| Boulders along the pond's bank and the channel's (120, 0.16 to 1.1 m across) | grey granite, each its own rule-made shape: a lump broken along a few faces, edges rounded by weather, skin pitted | old: edges well rounded, lichen on the faces, moss on the tops | moss on the upward faces; feet dark and glossy where they meet the wet soil; a dark wet band 7 cm above the pond's water where they stand in it | shelf `lichen_rock` (colour, roughness, normal, height pictures), greyed, moss by the moss tool in the earlier builders' brighter green |
| The lantern's seat | a flat-topped granite slab | weathered flat, its rim rounded | moss on its top round the lantern's foot; wet band at the water | `lichen_rock`, moss 0.9 |
| The lantern's mound (three boulders) and the single boulders (right bank, far bank, both ends of the bridge) | granite boulders | as the bank's | as the bank's | `lichen_rock`, moss 1.0 |
| Two flat stones in the near water, before the lantern and beside the path | flat granite stones | old, rounded rims | thick moss on the tops, wet band at the water; real bumps (near the eye) | `lichen_rock`, moss 0.9, 3 cm relief from the height picture |
| The basin's front stone | a flat granite stone | worn by feet | little moss: its middle is stood on; wet from splashes; real bumps | `lichen_rock`, moss 0.35, 3 cm relief |
| The rock beside the basin and 14 small rocks at the basin's foot (8 to 30 cm) | granite | old | moss on tops, wet feet | `lichen_rock`, moss 0.6 to 1.0; the one beside the basin with 3 cm relief |
| Pads under the veranda's posts (18) | flat granite stones | old, dry under the eaves | thin moss only (0.25); hidden by the deck's edge | `lichen_rock` |
| The stone basin (shape unchanged) | carved granite | old, its rim grown over | moss on the rim and upward faces | `lichen_rock`, moss 0.9 (was the earlier dark rock smothered in bright moss) |

Every rock grows its own amount of moss (0.35 to 1.4 times the amount listed, by its own random number), as shaded and open rocks differ.

Made in code: every rock shape (the store's rocks tool's rules), laid by Blender's particle system.

## Traps

- The rocks' particle copies cannot be found by a ray from above: nothing may be set on them afterwards (the earlier noise balls are kept, hidden, for what was already set on them).
- The tool's flat stones default to a dark smooth sea rock (`seaside_rock`); in the basin's shade it drew a black patch, so every rock here wears `lichen_rock`.
