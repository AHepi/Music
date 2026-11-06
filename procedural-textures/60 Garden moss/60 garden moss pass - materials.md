# Materials - moss pass

What this file is: the material list for the surfaces this pass changed (the moss on the rocks), in the form `Before you build.md` asks for. Everything not listed here is as in the earlier builders' lists (`earlier60/materials - first pass.md`, `- second pass.md`, `- closer pass.md`, `- rocks pass.md`).

The owner's words: "Ok. I meant the rocks with moss. Not the pavement lol. Those are still lacking a lot of detail"

Who is here: the inn's guests and the maid, as in the earlier lists. The rocks are older than any of them, set by the garden's maker long ago and never moved; the moss on them is decades old, kept damp by the pond and the rain, and nobody walks on it except at the basin's front stone, where a guest stands to wash (its middle stays bare).

| What | Made of | How it has aged | Where the wear sits | Surface |
|---|---|---|---|---|
| Moss on the 120 bank boulders, the 14 small rocks round the basin, the lantern's seat and mound, the single rocks, the two flat stones in the near water, the rock beside the basin, the basin's front stone, the post pads | real moss: soft cushions with thickness (3.5 cm deep in the middle, 4.5 cm on the near rocks), a pile of tufts about 2 cm high on them | old cushions dark olive, young ones yellow-green, dry brown tips in places; each scattered rock its own amount (0.5 to 1.35 times) | thick on the tops and in the hollows and cracks, thinning to nothing at frayed edges, creeping over the rims and hanging a little down the sides; none on the sharp ridges, where it dries and is rubbed; little on the basin's front stone (stood on) and the post pads (dry under the eaves) | the store's rocks tool, `moss_style='cushions'` (the moss tool's cushions over the shelf's photographed moss `forest_leaves_02`: PBR colour, roughness, normal); tufts laid by the particle system |
| Bare stone of those rocks | grey granite (`lichen_rock`, as the rocks pass) | old | pale lichen crusts (rosettes 2 to 6 cm) on the bare faces; the stone round and under the cushions stained green, green in its cracks | shelf `lichen_rock` (PBR), the tool's lichen 0.7 |
| Moss on the stone basin | real moss, as on the rocks | old: the basin has stood in the drip of the spout for years | on its rim and top, in patches down its sides, thick round its damp foot | the moss tool's `grow` (amount 0.7, so stone shows between the patches on its rim) on a closed copy of the basin (the basin is open underneath and the tool needs a closed shape) |
| Where the rocks meet the soil | moss tufts on the soil, short grass, a few ferns | old | moss spilling from each rock's foot in patches, thinning out 20 to 25 cm away; grass round it; ferns at the biggest rocks on dry soil and one behind the basin | the moss tool's `feet` (tufts and the grass tool's turf), the store's `fern` part |

Made in code: the cushions' shapes, their tufts' places, the moss at the feet (the store's moss tool).

## The second change: the pools on the path

The owner's words: "The pools of water on the pavement also need to be semi transparent. Right now, it looks like a liquid mirror"

| What | Made of | How it has aged | Where the wear sits | Surface |
|---|---|---|---|---|
| Pools in the slabs' hollows (the long one mirroring the hanging lantern, the smaller ragged ones) | rainwater a few millimetres to 2 cm deep over the split granite | fresh after rain | deepest in the middle of each hollow; shallow at the edges, where the stone shows through and the water thins to nothing | made in code: the earlier water (dark, glossy, faint ripple) mixed with a see-through surface: half mirror looking straight down, more at a glancing look; the stone seen through it darker and a little warmer; fading out over the outer third of each pool; the pool that mirrors the hanging lantern keeps more of its mirror (its glint is the close view's warm light) |
| The store puddle by the veranda | rainwater | fresh | as before | a copy of the store's `MADE • puddle water`, made see-through the same way |

## Traps

- The moss tool remakes a stone as even small faces before it grows moss on it, which needs a closed shape: on the carved basin, open underneath, it grew almost nothing until it was given a closed copy.
- The cushions' sheen, tinted their young green, lit every mossy top lime under the dusk sky; turned down, the moss reads as moss.
- A fern the feet tool sets at a random side of a rock can land on the path in front of something else (it landed in front of the maid's bucket): set the ferns near the path by hand.
- Water made see-through by bending the light (refraction) leaves the stone under it unlit, because light that bends through the water is not drawn here (caustics off): a see-through surface that does not bend the light keeps the stone lit.
- Too see-through, the pools read as pale dry patches where a lamp lights the slab under them: the stone under the water has to be darker than the dry stone round it.
