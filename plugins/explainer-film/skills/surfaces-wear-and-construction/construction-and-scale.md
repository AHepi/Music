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
- A cottage: footing, timber frame or log wall, plaster or boards between the posts, thatch or shingle on rafters, a
  chimney through the roof with a flashing, a door with a step, shutters on hinges.
- A stable: the same frame, a floor with a drain, three stalls divided by posts and rails, a manger at the front of each,
  a plank door, hooks for tack.
- A fence: posts set into the ground, rails fixed to the posts, never rails floating between posts.
- A cart: an axle-tree under the bed, wheels with spokes on the axle ends, shafts fixed to the bed.
- A well: a ring of stone on the ground, two posts, a beam, a rope and a bucket.
- A trough: a hollowed log or boards on legs that stand on the ground.
- Give wood and stone character as SHAPE (age and damage in the geometry, `the-required-steps.md` step 2): no two planks
  alike, tiles of different tones with a few slipped or missing, posts a little out of plumb. That is what read at film
  size in the garden.

## The facts table (real-world sizes)

Write each fact as: number, unit, source and confidence (strong, weak or guess). Put the numbers in the brief as limits
and in the acceptance tests. A weak fact gets a note so that builders do not treat it as law. Facts set the SIZE; the style
note sets how much detail. `place-kit/data/real_world_facts.json` has about forty generic facts (marked weak or guess,
from common building and prop practice); the place's own facts file adds or replaces them, and the planner's research
should confirm each one with a real source.

Starter numbers for a mediaeval forest village. ALL are from memory and are judged, WEAK: confirm or replace them by
research before they become law.

| What | Size |
|---|---|
| single-storey cottage | 4 to 5 m wide by 6 to 8 m long |
| eaves height | 2.0 to 2.4 m |
| thatch pitch | 45 to 55 degrees; thatch 25 to 35 cm thick |
| door | 1.6 to 1.9 m high and 0.7 to 0.9 m wide |
| window opening | 0.4 to 0.6 m |
| stable stall | 1.5 to 1.8 m wide and 2.4 to 3 m long; manger 0.9 to 1.1 m high |
| horse shoulder height | 1.3 to 1.6 m |
| cart gauge | 1.2 to 1.5 m (the coal-mine yard used 1.24 m) |
| wide boards | 20 to 30 cm |

## What the construction check measures

`explainer-film-place construction` builds a contact graph from the ground upward and says, for every part, what carries
it. Every number is judged unless marked; all are house numbers in `film-settings.json` (section `place_construction`).
- **Touching** means within 5 mm. A part is carried only when it rests on something through a patch of at least 16
  square centimetres within 8 mm, and the carrier is itself carried, all the way down to the ground. Touching is not
  carrying: a part that touches a carrier only along an edge, or that is carried only by something that floats, fails.
- **Overlap** between two joined parts at least 4 cm.
- **Span**: no stretch between supports longer than 1.38 m (from the garden's 1.4 m), found by rays straight down every
  5 cm along planks and beams.
- **Floating**: a gap over 5 mm fails. A gap between 5 mm and the carrier's expected gap is reported as short.
- **Hung**: a part carried from above (a lantern on a hook) is allowed only for roles that may hang.
- **Ground seating**: a part meant to stand on the ground is within 2 cm of the ground height (invented).
- **Doorway floor**: a floor within 0.30 m below the sill (invented).
- **Inside-out closed parts** fail: a mesh whose volume is negative shows only from inside. The street's scene study found
  73 such parts that nobody had noticed.
- **Coplanar faces**: two overlapping faces within 1 mm of the same plane flicker. The garden had 77 deck faces fighting a
  plinth top.
- **Buried lights**: a light inside solid stone, or a glow box buried inside a stone lantern, reads as a flat white
  cut-out (the garden's lantern); put the glow box 3 cm proud of its opening. A lamp inside its own glow box is blocked
  in Cycles.
- **Walkability** along declared routes: rays every 5 cm, steps between neighbours at most 2 cm, slope at most 1 in 20.
- **Exempt on purpose**: scatter pieces (leaves, tufts, litter, pebbles, moss cushions) are floating by design. The report
  names the exemption and says why.

`explainer-film-place audit` also runs the **scale check**: each object's size against the facts table. It warns when a
size is out of range and fails beyond the fail factor (1.5 times: invented). A 1.0 m door fails; a 1.7 m door passes.

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
