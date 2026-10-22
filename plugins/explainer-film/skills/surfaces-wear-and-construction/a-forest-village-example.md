# A worked example: a village in the forest

What this is: how the request below would be planned and built with this skill, from the words to the report. It is a
PLAN, written before the village exists: it shows what each step decides. The tests prove the gates work; they do not
prove the village looks good. Fresh checkers and the person's own eyes judge that. Numbers marked invented must be
confirmed by the planner's research before they become law.

**The request, word for word:** "Build a village in the forest. Needs unkept dirt roads like they've been driven down
by horse and carriage, an empty stable, a few cottages, some scattered mediaeval props." It says nothing about surfaces,
wear or realism, and it does not say "Blender". Still, the village is built in Blender, so this skill applies.

## What the words mean for the settings

- "unkept dirt roads": look `neglected` for the lane roles (see the table in `SKILL.md`).
- "like they've been driven down by horse and carriage": two wheel ruts a cart's gauge apart, hoof prints between them,
  the lane shape cut into the ground (`roads`), the dirt-road surface on top (`wear-recipes.md`, the lane).
- "an empty stable": a stable with no horses but used: look `lived_in`, old straw and dung left, chew marks on the rails.
  Not `derelict`: that is for ruins.
- "a few cottages": 3 or 4, look `lived_in`.
- "scattered mediaeval props": barrels, buckets, crates, a handcart, a well, a woodpile and chopping block, a ladder, a
  fence, sacks, hay: not a modern thing among them.
- "in the forest": damp state (trees keep the ground damp and shaded), moss on the shaded and damp sides, a forest edge of
  trees, stumps, logs, rocks, ferns, bramble and nettles, kept off the lanes.

## Parts and owners

Build the ground first, then the others side by side, then combine.

| Part (owner) | What it makes |
|---|---|
| `roads_and_ground` (first, serial) | the graded ground mesh, two lanes with ruts and hoof prints, the verge, puddle hollows. Its height is then frozen and everyone else is seated on it. |
| `cottages` | 3 or 4: stone footing, timber frame with wattle-and-daub plaster or log walls, thatch or shingle roof, chimney, door and step, shutters |
| `stable` | timber frame, three stalls with posts and rails, a manger in each, a plank door, tack hooks, an earth or plank floor with a drain, straw remnants, old dung |
| `props` | barrels with iron bands, buckets, crates, a handcart, a well, a woodpile and chopping block, a ladder, a leaning fence, sacks, hay litter |
| `forest_edge` | pines and broadleaf trees, stumps, fallen logs, rocks, ferns, bramble, nettles, leaf litter, kept off the lanes |

## Roles

Every visible object gets exactly one role: `ground.dirt_road`, `ground.forest_floor`, `ground.floor_earth` (inside the
stable), `wall.plaster`, `wall.timber_frame`, `roof.thatch`, `timber.post`, `timber.beam`, `timber.plank`, `stone.footing`,
`iron.fitting`, `prop.wood`, `prop.straw`, `tree.bark`, `plant.foliage`, and the glow role for a lit window. A barrel's wood
and its iron bands are two roles (one for each material).

## Settings (a fragment; the whole file is `place-kit/data/examples/forest-village-place-settings.json`)

```
"place": "village", "place_type": "village", "look": "lived_in", "state": "damp",
"look_by_role": { "ground.dirt_road": "neglected", "ground.forest_floor": "neglected" },
"roads": [ { "name": "main lane", "polyline": [[0,0],[12,3],[30,2]], "gauge": 1.3, "rut_depth": 0.08, "hoof": true } ],
"off": [ { "layer": "wetness", "roles": ["ground.floor_earth"], "reason": "inside the stable, under the roof: dry earth" } ],
"renderer": "auto"
```
The lane's walking lines go down the two wheel tracks and the middle hoof line (nothing may grow there); the strips of
grass between them are left free. Keep-clear shapes cover the tracks and the doorsteps.

## Renderer

A lit lantern or window means Cycles on a rented card; plain daylight (sun only) means EEVEE. `explainer-film-place
renderer-for` says which and why. This village has a lit window in one cottage, so its pictures are drawn with Cycles.

## The facts table (a starter; judged, WEAK, to be confirmed)

Cottage 4 to 5 m by 6 to 8 m; eaves 2.0 to 2.4 m; thatch pitch 45 to 55 degrees and 25 to 35 cm thick; door 1.6 to
1.9 m by 0.7 to 0.9 m; window opening 0.4 to 0.6 m; stall 1.5 to 1.8 m wide and 2.4 to 3 m long; manger 0.9 to 1.1 m
high; horse shoulder 1.3 to 1.6 m; cart gauge 1.2 to 1.5 m; wide boards 20 to 30 cm. INVENTED and to confirm: the rut
size (12 to 25 cm wide, 5 to 12 cm deep), hoof prints (12 to 14 cm, one every 0.8 to 1.0 m), the strips of grass (about
30 cm each), the thatch displacement (4 to 6 cm). The bank beside each rut (0.3 of its depth) is judged from the coal-mine yard.

## What the finished village should show (16 readable features)

The blind reading test names these from a half-size picture, with keywords that count as a hit. At least 12 of 16.

1. wheel ruts with puddles (rut, puddle)
2. hoof prints (hoof)
3. grass between the ruts (grass, centre)
4. thatch with moss and a sag (thatch, moss)
5. plaster cracks on a timber frame (crack, plaster)
6. silvered planks (silver, weathered, plank)
7. stone footings with moss (footing, stone)
8. soot staining above the chimney (soot, smoke, chimney)
9. empty stalls with straw (stall, straw, empty)
10. dung or straw by the door (dung, straw, door)
11. barrels with rusted bands (barrel, rust)
12. a cart with spoked wheels (cart, wheel)
13. a woodpile and chopping block (woodpile, chopping)
14. a leaning fence (fence)
15. ferns and nettles at the wall feet (fern, nettle)
16. fallen leaves and logs (leaves, log)

## The order of the whole job

1. The planner writes the style note, the facts table (with sources), `place-settings.json`, the ownership table and the
   acceptance list. 2. `roads_and_ground` is built and frozen. 3. The other four parts are built side by side; each runs
   `finish-part`. 4. The integrator combines the parts (both orders), seats them again on the ground, runs `finish` and
   `audit`. 5. `explainer-film-preflight place` must pass before anything is drawn. 6. The renderer draws previews with the
   renderer rule, measures them and makes the guard (provisional). 7. Fresh checkers (look, structure, process, blind
   reader) recompute; a skeptic ranks; one fix round by the owners; a different checker looks again. 8. A plain report:
   what was done, what was measured and what only judged, what was skipped, what was not tested, every failure.
