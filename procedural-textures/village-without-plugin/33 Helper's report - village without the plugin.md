# 33 Helper's report - village without the plugin

What this file is: the build helper's own report, word for word, from the control test (Sonnet at maximum effort, Blender through its MCP connection only, no plugin, no rented cards, no pictures, 23 October 2026). Run time 2 h 22 min, 296 tool calls.

The village is built and saved, and all five pictures are rendered at 1200 x 800. I worked only inside the village-control folder and used only Blender MCP tools. I did not use the Skill tool, any skill, the internet, remote machines or git, and I did not touch the plugin, because this was a no-plugin control run.

**Deliverables** (in /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-control/)
- Scene: `village.blend` (99 MB). It uses no image files and no external references.
- Pictures in `pictures/`:
  - `01_village_from_above.jpg`: wide view of the whole village from above.
  - `02_road_at_eye_level.jpg`: standing on the road at eye height, looking along it.
  - `03_stable_close.jpg`: close view of the stable.
  - `04_cottage_close.jpg`: close view of one cottage.
  - `05_road_surface_closeup.jpg`: close-up of the road surface.
- The build scripts are in `scripts/`, about 5,000 lines of Python. `build_all.py` is the master that rebuilds everything.

**What I built**
- **Setting:** a clearing in a dense forest, lit by a low morning sun from the south-west (31 degrees up) with a light haze.
- **Roads:** three dirt roads: a winding main road of about 300 m, a short lane to the stable and a farm track.
  - Each road has two real wheel ruts with soil heaped beside them, a trodden middle strip with patchy grass, and ragged verges.
  - About a dozen puddles sit in the ruts. Hoof prints are pressed into the ground, most clearly near the close-up camera, and dung, pebbles, twigs, straw and dry leaves are scattered along the roads.
- **Buildings:** five cottages, each with a different look.
  - Three are half-timbered with plaster and two are fieldstone. Roofs are thatch or individually laid wooden shingles.
  - Each has a door, shutters, a stone step and a stone chimney.
  - Several have fenced gardens with a few broken rails.
- **Stable:** a 12 m timber stable with four empty stalls, open or half-open doors, mangers, hay racks, straw on the floor and a loft with a hoist beam. A cart is parked in front, with a hitching rail, a trough and horse collars and a halter left hanging on the posts.
- **Props:** a well, signpost, lantern posts, benches, barrels, crates, sacks, hay bales, a haystack, woodpiles, chopping blocks, a wheelbarrow, ladders, jugs, bee skeps, boulders, fallen logs and stumps.
- **Forest:** about 2,200 trees (oak, beech, birch, spruce, pine and a few dead ones), 1,400 ferns, bushes, grass tufts and wildflowers.

**How**
Everything is Python run through `execute_blender_code`. All meshes are generated with numpy and all 29 materials are procedural node networks.
- **Terrain:** the ground mesh is refined from 4 m cells down to about 3 cm around the roads, so ruts, hoof prints and puddle hollows are real geometry. Per-vertex values such as road coverage, rut depth and wetness drive the ground material, which blends dirt, mud, gravel, grass and leaf litter.
- **Buildings and trees:** buildings are parametric generators. Trees are grown as branch skeletons with leaf shapes on them, and conifers use cards with a procedural needle pattern.
- **Rendering:** Cycles on the CPU at 112 samples with denoising, AgX colour management. Each image took 6 to 7.6 minutes.

**Problems met**
- A tool call dies after 60 seconds, so long jobs and renders ran in background threads that I polled.
- Blender crashed once when I started a second render during another, and I killed it myself once. Both times I restarted it and reopened the saved `village.blend`.
- A world-level haze volume turned every render black, so the haze is a large finite box instead.
- Smoke volumes over the chimneys made rendering about 70 times slower, and the alpha-card version looked wrong, so I left chimney smoke out.

**Weak spots**
- Leaves are simple kite shapes and the spruce needles repeat a pattern, so trees hold up at a distance but not close up.
- The finest road detail is bump-mapped, and hoof prints are subtle outside the camera zones.
- Cottage interiors are empty and the windows are dark glass.
- The thatch and plaster look somewhat soft and clean.
- The sky has almost no visible clouds.
