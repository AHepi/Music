# The change: the rocks

What this file is: what the owner asked for in this pass, where it shows in the place, and how it will be made. Written before anything was changed (6 November 2026, 09:36).

## What the owner asked for

The owner's words, after seeing the closer pass: "I just realised you can't see perspective. The whole scene is about 7x larger than the set. But that's ok. My bad. The next thing to work on is the rocks. They need to be procedurally generated in a particle system. And better textured"

So, two things, for the rocks only:

1. **Made by rules and laid by a particle system.** Today every rock is a hand-placed ball of noise (`rock()` in the earlier script, about 80 roughened balls joined into one mesh, all at spots typed in by hand).
2. **Better textured.** Today they all wear one material: a dark rock photograph smothered in bright moss, smooth-shaded, so in the picture they read as soft green pillows with no stone in them (look at the pond's edge and the lantern's mound in the earlier final).

The size of the place stays as it is ("But that's ok").

## Where rocks show in the place

From the earlier script (`rock()` calls, lines 765-810) and its pictures:

- **The pond's edge:** a ring of up to 46 rocks round the bank, with gaps where the stepping stones make the edge, under the bridge, and on the near shore (left open in the closer pass so the water shows). In the frame: the right bank behind the basin and the stone lantern, the far bank by the bridge.
- **The channel under the bridge:** 16 rocks on its banks.
- **The stone lantern's mound:** four rocks in the water; the lantern stands on the biggest.
- **Single rocks:** the big feature rock on the right bank (4.4, 5.6); the big flat mossy boulder in the water before the lantern and a smaller flat one beside the path (closer pass); one on the far right bank (3.3, 9.7); one at each end of the bridge.
- **By the basin:** its flat front stone and a small one at its side.
- **Under the veranda:** 18 small flat pads under the posts.
- **The stone basin** is carved stone built by hand and wears the same rock material: it keeps its shape, and takes the new rock surface so it does not stay the one smooth green thing among the new rocks.

Not rocks, and left as they are: the path slabs and the stepping stones (the path, already worked on from the owner's second picture), the pebbles in the bed (the store's stones tool), the stone lantern (the store's part), the inn's stone base.

## How it will be made

- The store's `rocks` tool (made for these words, decision 89): rocks made by rules (a lump broken along a few faces, edges rounded by weather, skin pitted; each shape from its seed), copied onto the ground by Blender's own particle system, covered with the shelf's photographed rock sets (colour, roughness, normal and height pictures used together: PBR, decision 84), each rock its own part of the picture, greyed (garden granite is grey), wet and dark at the feet, moss on the tops.
- **The pond's edge and the channel banks:** `rocks.scatter` of old weathered boulders over a band along the waterline, keeping the earlier gaps (stepping-stone edge, under the bridge, the open near shore), big ones fewer than small, small ones gathered at the feet of the big ones, as on the owner's picture.
- **The rocks with a set place** (the lantern's mound, the single rocks, the basin's stones, the post pads): still particle copies of rule-made shapes, but on spots I give, one tiny face per rock, so the layout stays where the earlier builders put it. Each keeps the earlier rock's place, size and top height; the lantern's seat is a flat-topped stone with its top where the lantern's foot already stands.
- **Small rocks at their feet:** a scatter of small stones round the lantern's mound, the feature rocks and the basin, so the big rocks sit in the ground instead of on it.
- The earlier noise balls stay in the file but hidden from the picture, so everything the earlier builders set on top of them (the stone lantern's height) stays where it was.
- Kept as it is: the layout, the camera, the lights, every other thing and material.
- Checks: draw small, look at full size beside the earlier picture, measure every picture, close view too; then the final at 540 x 960 and the close view.

## Traps

- Particle copies cannot be found by a ray from above: measure heights before scattering, set nothing on a scattered rock (the store's own trap).
- A narrow band holds fewer rocks than asked: read back how many were laid.
- With the low sun ahead of the camera every rock is a dark lump: the lamps and the sky must find their faces.
- Green moss counts as neither warm nor cool in the measure; greyer rocks can move the cool share, which already sits near its floor (31 percent, floor 30).
