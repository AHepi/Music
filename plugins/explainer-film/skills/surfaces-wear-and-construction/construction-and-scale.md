# Construction and scale (build from the ground up, at real size)

What this is: how to build a place so that it makes sense (every part carried, nothing floating) and is the right
size, and what the construction check and the scale check measure. Every number says what kind it is: **measured**
(from a test or a check on a real scene), **judged** (chosen from evidence) or **invented** (a guess).

**Example first: the garden bridge.** A viewer said the bridge "made no sense", even for an artistic style. It was a
few flat boxes that overlapped, with nothing fixed to anything, four small stone blocks that touched nothing and six
thin sticks under the boards. It was rebuilt from the bottom up: flat footing stones standing on the pond bed, square
posts 14 cm across with a 1.5 cm chamfer on top of the footings, cross beams notched into the post pairs and pegged,
long beams lying on the cross beams, planks across the long beams with a gap between them, round pegs and a few iron
cramps. No stretch between two supports was longer than 1.4 m. A fresh checker then proved it in the saved scene:
59 planks, none on fewer than 2 supports; 18 posts, each on a footing; the longest unsupported stretch 0.85 m; a walk
line along the middle met a plank the whole way. The same checker also found 3 footing stones with a one-sided air gap
of 2.5 to 13.5 cm, so the rule is "prove it, then look at what the proof missed".

## The rule

Build from the ground up, so that every visible part has a visible reason: you can say what carries it and what it
carries. A part that nothing carries looks wrong even in a painted style.

- Walls and sheds: a stone footing on the ground; a sill on the stone; posts on the sill; a wall plate along the top of
  the posts; rafters on the plate; the roof on the rafters; a floor, and a threshold, so a doorway looks onto something
  (the coal-mine engine house once had a door onto nothing).
- A gate (the canal lock's, built and checked): a heel post and a mitre post standing on the ground, rails tenoned into
  both posts, boards on the rails, iron straps, and a long balance beam lying on top of the heel post.
- A flight of steps: each step on the one below it, the lowest on a core that stands on the bed; the rise from the top
  of one step to the top of the next is 15 to 20 cm, and the check reads it top to top.
- A fence (the coal-mine yard has a post-and-rail one): posts set into the ground, rails fixed to the posts, never rails
  floating between posts.
- A hand cart (the coal-mine yard has a wooden one): an axle under the bed, a wheel on each end of the axle, handles or
  shafts fixed to the bed.
- A basin, a tank or a trough: boards or stone standing on the ground or on legs that stand on the ground.
- Give wood and stone character as SHAPE (age and damage in the geometry, `the-required-steps.md` step 2): no two planks
  alike, tiles of different tones with a few slipped or missing, posts a little out of plumb. That is what read at film
  size in the garden.

## The facts table (real-world sizes)

Write each fact as: number, unit, source and confidence (strong, weak or guess). Put the numbers in the brief as limits
and in the acceptance tests. A weak fact gets a note so that builders do not treat it as law. Facts set the SIZE; the style
note sets how much detail. `place-kit/data/real_world_facts.json` has about twenty-five generic facts (marked weak or guess,
from common building and prop practice); the place's own facts file adds or replaces them, and the planner's research
should confirm each one with a real source.

Starter numbers this project has really used (any place can start from them and then replace them with its own
sourced facts). The kind is in the last column.

| What | Size | Kind and where it comes from |
|---|---|---|
| distance between two wheel ruts of a cart road | 1.24 m | measured in the coal-mine yard's build code; the generic range is 1.0 to 1.8 m (judged) |
| rut depth of a heavily used cart road | 0.15 m (about 0.13 to 0.21 m with its variation), about 0.4 m across at half depth | measured in the same code |
| raised bank beside a rut | about 0.3 of the rut's depth | measured in the same code |
| lightly used road | rut 5 to 15 cm deep | invented |
| longest free stretch between supports | 1.38 m or less | judged from the garden bridge (1.4 m) |
| bridge post | 14 cm across, 1.5 cm chamfer | measured in the garden |
| planks of a bridge or deck | 9 to 17 cm wide, gaps 5 to 14 mm | judged from the garden bridge |
| stone step rise | 15 to 20 cm, top to top | judged (from memory) |
| lock wall | 0.3 to 0.9 m thick | judged, weak (from memory), in the canal lock's own facts file |
| balance beam of a narrow lock gate | 2.5 to 4 m | judged, weak (from memory) |
| a door | 1.6 to 2.3 m high, 0.6 to 2.0 m wide | judged, weak (the generic facts) |
| a window opening | 0.3 to 1.5 m wide | judged, weak (the generic facts) |

## What the construction check measures

`explainer-film-place construction` builds a contact graph from the ground upward and says, for every part, what carries
it. Every number is judged unless marked; all are house numbers in `film-settings.json` (section `place_construction`).
- **Touching** means within 5 mm. A part is carried only when it rests on something through a patch of at least 16
  square centimetres within 8 mm, and the carrier is itself carried, all the way down to the ground. Touching is not
  carrying: a part that touches a carrier only along an edge, or that is carried only by something that floats, fails.
- **Overlap** between two joined parts at least 4 cm.
- **Framed in** (checked, plugin 1.4.0 fix round): a part joined at least 4 cm into TWO or more carried parts, such as a gate rail tenoned into both posts, counts as carried, and it needs no role that may hang. A part joined into only
  ONE carried part, with its other end in the air, is "hung": allowed only for roles that may hang. The roles that may hang (data `roles.json`, `may_hang`): `timber.door`, `timber.shutter`, `timber.fence`, `iron.fitting`, `prop.rope`
  and `glass.window`. So a gate's leaf is a `timber.fence` or `timber.door`; a frame whose rails are `timber.beam` needs both ends in posts.
- **Sunk in**: a part may sit up to 4 cm into what carries it and still counts as resting on it (a board bedded into its post, a post set into the ground; `place_construction.sunk_in_centimetres_max`, invented). The facts say how
  far it sits in, in millimetres. A stake driven 4 cm or more into the top of a carried part, and sticking out above it, is carried by it.
- **Afloat**: a part that goes down through a water plane and out above it (a boat, a pile in a river) is carried by the water. A hull that hangs 3 cm above the water is reported as "floating in the air" (a fail). For a boat, model the hull below the waterline
  as well as above it; the check does not need its underside exactly on the water plane.
- **Span**: no stretch between supports longer than 1.38 m (from the garden's 1.4 m), found by rays straight down every
  5 cm along planks and beams.
- **Floating**: a gap over 5 mm fails. A gap between 5 mm and the carrier's expected gap is reported as short.
- **Hung**: a part carried from above (a lantern on a hook) is allowed only for roles that may hang.
- **Ground seating**: a part meant to stand on the ground is within 2 cm of the ground height (invented). The ground is read at the SAME five points under the part's box that `pk.seat_on_ground` uses (its centre and its four
  corners pulled in a tenth), so a part that was seated is not failed for another corner; a point with no ground object under it is unknown, not height 0; and the report names the ground object and height it measured against.
  A wall that stands on a canal bed beside a higher towpath is read against the bed. If the ground named is not the one the part stands on, a corner of its box lies over the other ground object: move that corner clear.
- **Doorway floor**: a floor within 0.30 m below the sill (invented).
- **Inside-out closed parts** fail: a mesh whose volume is negative shows only from inside. An object with a negative scale (a mirrored wall) is turned back before this test, so a mirrored wall is not called inside out. The street's scene study found
  73 such parts that nobody had noticed.
- **Coplanar faces**: two overlapping faces within 1 mm of the same plane flicker. The garden had 77 deck faces fighting a
  plinth top.
- **Buried lights** (point, spot and area lamps; a sun shines from far away, so where its object sits does not matter): a light inside solid stone, or a glow box buried inside a stone lantern, reads as a flat white
  cut-out (the garden's lantern); put the glow box 3 cm proud of its opening. A lamp inside its own glow box is blocked
  in Cycles.
- **Walkability** along declared routes: rays every 5 cm, steps between neighbours at most 2 cm, slope at most 1 in 20.
- **Exempt on purpose**: scatter pieces (leaves, tufts, litter, pebbles, moss cushions) are floating by design. The report
  names the exemption and says why.

`explainer-film-place audit` also runs the **scale check**: each object's size against the facts table. It warns when a
size is out of range and fails beyond the fail factor (1.5 times: invented). A 1.0 m door fails; a 1.7 m door passes.
Sizes are read from the object's OWN sides (the smallest rectangle that holds it seen from above, and its height), so a wall turned 45 degrees is still as thick as it is. The step rise is read by the construction check, top
to top, and judged by the role `stone.step` (not by a name): a flight of 17 cm steps passes whether it is built from slabs on a core or from solid blocks, and one 1.8 m block called a step fails.

## The scene study before building (when the place already exists)

Measure gaps yourself with rays; do not trust a number from a helper's note. In the garden two studies of the same scene
disagreed slightly on gap sizes, so the plan said "re-measure first". The scene had a veranda step 23 cm in the air,
bridge posts 2 to 7 cm short of the boards, wall caps floating 6.5 cm and a roof 22 cm off its posts. All were found by
a ray check, none by eye at the hero camera.

Traps:
- Touching is not carried (above).
- Two faces that fight (z-fighting) are fixed by moving one of them 1 cm (the garden lowered the plinth top 1 cm so 77
  faces stopped fighting). Shortening a part by a few millimetres instead can leave what it carried floating. Run the
  check again after any such change.
- A support must be a real part with a size, not a hidden helper plane: the audit reads the geometry that is drawn.
