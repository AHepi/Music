# 23 Plan - 3D petrol station with painted light

What this is: how to turn the petrol station (canopy, posts, kiosk, pump island) and the forecourt and
road into 3D objects while keeping the painting's light, for painting 409 (chapter 2, page 7). The
other cars, hedges, houses and sky stay painted. Chosen from three designs by two independent judges
(log 23); not built yet.

## A concrete example first

The front canopy post today is paint stretched over a depth picture, so it bends when the camera
moves. In this plan it becomes a plain box standing exactly where the painted post stands, and the
painting is shone onto it from where it was painted, like a slide projector. From the painting's own
view you see exactly the painting. When the camera pushes in, the post slides in front of the kiosk
like a real post, and the strip of kiosk wall it uncovers comes from a cleaned copy of the painting.

## The parts

- **Simple shapes, fitted to the painting** (one Blender script): the forecourt and road as flat
  ground with a kerb, the pump island as a low slab, the two posts as boxes, the canopy as a slab with
  a striped edge, the kiosk as boxes with its windows set a little in and the painted shop interior on
  a card behind the glass. The pumps become boxes drawn to their painted outlines (which removes the
  ghost edges of log 22); the red car stays the SAM 3D model, set with all four wheels on the ground.
- **They wear the painting**: every shape shows the painting projected from where it was painted,
  unlit, so the colours and brushwork are untouched. What the camera newly sees behind a post or
  the canopy comes from cleaned copies of the painting (free, made here).
- **Stays painted**: the queued cars (as upright cut-outs standing on the road), hedges, houses,
  poles, sky.

## The light (the heart of it)

The rule: light painted onto something that doesn't move is already right from any camera position,
so it stays painted. Real lights are added only where paint can't be right.

| Light in the painting | What happens |
|---|---|
| Three canopy lamps (warm amber) | Stay painted on everything still. Real lamps at the same spots light and shade only things that move or are new (if the red car rolls under the canopy, it brightens and its shadow moves with it). |
| Kiosk glow (warm yellow) | Stays painted; a real light just inside the window for anything that moves near it. |
| Red car's headlights | Beams become 3D light cones fixed to the car; the pools on the ground come back from the original painting (the cleaned copy is what broke them in log 22). |
| Wet ground | Small glints at each lamp's mirror point on the ground, which slide as the camera moves, so the forecourt reads wet. |
| Queued cars' headlights, night sky | Stay painted. |

Still things keep their painted shadows and cast no 3D shadow (otherwise shadows double). Only a
moving thing casts a live shadow. A soft contact shadow under the car's wheels grounds it.

## Camera moves it allows

A push in up to about 1.3 times, pans of about 6 degrees, small sideways or up-down moves of about
half a metre: enough for the camera rule (at most three short moves a shot).

## Cost and risk

- Cost: nothing on fal (reuses the clean background of log 22; the rest is scripted or made here).
- Main risk: AI paintings are not perfectly consistent in perspective. If a box sits more than 2-3
  pixels off its painted edge, a sliver of one thing gets printed on another and ghost edges come
  back on a push.

## First test (proves or kills it before any lighting work)

Build only the forecourt, the island slab, the two posts and the kiosk front box; check them against
the painting with a wireframe overlay (every main edge within 3 pixels) before drawing anything; then
draw two stills: the painting's view (must match the painting) and the end of a 1.25 times push
toward the island. Pass: the posts stay straight and slide cleanly in front of the kiosk, with no
smear. No cost.
