# 57 The Japanese garden, first builder - report

What this file is: the first builder's report, word for word (5 November 2026, 20:07 to 21:29). Saved by the session (a builder cannot save files whose names begin with REPORT).

---

I finished at 21:29, 18 minutes before the deadline. There are two pictures: the garden (final.png) and a close view of the wet path made from the owner's second picture (closeup.png). Both are 540 x 960, drawn with 64 samples, and both measure inside every band. All files are in /home/claude/build-57-garden/work. I couldn't test the full-size redraw (1080 x 1920); I expect it to take about 20–25 minutes on the two processors.

**What I built** (from the owner's picture, without the fish)
A Japanese garden after rain, beside an old timber inn, at dusk.
- **Near:** a wet path of split stone slabs runs along the inn's veranda. Rainwater lies in hollows in the slabs and mirrors the cloudy sky. Red maple leaves are stuck to the stones, and there is gravel and moss in the joints. A blue-and-white jar stands in the near left corner, and a pair of wooden clogs sits on the step stone.
- **Left:** the veranda, with boards, red posts with peeling paint and a deep eave with rafters and tile ends. Three hanging lanterns are lit, and one paper screen glows.
- **Right:** a stone water basin with a bamboo spout pouring into it and a ladle across it, a bamboo fence tied with black cord, ferns, bamboo stems, and red maple branches overhead.
- **Middle:** a pond with water-lily leaves and a few pink flowers, mossy rocks and stepping stones. A lit stone lantern stands on rocks in the water, and a red arched bridge crosses the pond.
- **Behind:** the inn has two storeys of dark timber, white plaster and paper screens, some of them lit. It has a balcony railing, curved tiled roofs with turned-up corners and a small front gable. Around it are maples and a pine, misty mountains behind, and a cloudy dusk sky.

**Light and framing**
- **Light:** dusk with a low sun hidden behind the inn and a cool light from above in the shadows. The warm light comes from the lanterns, the stone lantern and the lit screens; each lit screen has its own small light outside it. A thin blue haze lies over the pond and the inn. The store's finishing step does the glow and colour.
- **Framing:** the camera is at standing eye height on the path, looking along it, so the path leads the eye to the bridge and the inn in the upper middle. The eave frames the top left, and the jar and fence frame the bottom corners.

**Every picture** (time to draw · brightness / warm / cool / warm light)
| Picture | Size, samples | Time | Measures | What changed |
|---|---|---|---|---|
| test01 | 270x480, 16 | 22 s | 0.12 / 47% / 38% / 2.1% | First draw: too dark and too warm |
| test02 | 270x480, 16 | 22 s | 0.14 / 48% / 33% / 2.3% | Brighter sky, smaller jar |
| test03 | 540x960, 24 | 100 s | 0.15 / 47% / 36% / 2.2% | Blue scrolls painted on the jar |
| test04 | 540x960, 24 | 115 s | 0.16 / 39% / 40% / 2.1% | Pond brought nearer, sooty rafters, haze added |
| test05 | 270x480, 16 | 28 s | 0.16 / 31% / 48% / 2.1% | First inside every band |
| test06 | 540x960, 32 | 145 s | 0.17 / 32% / 46% / 2.0% | Puddle mirrors the near lantern |
| test07 | 540x960, 32 | 146 s | 0.17 / 34% / 46% / 2.0% | Slabs no longer look like foil, mountains visible |
| test08 | 540x960, 32 | 144 s | 0.18 / 35% / 43% / 2.1% | Puddle put back on the lantern's reflection, exposure up |
| close01 | 270x480, 16 | 30 s | 0.07 / 14% / 72% / 0.0% | First close view |
| test09 | 540x960, 32 | 154 s | 0.17 / 34% / 44% / 2.1% | Rough slabs with hollows, clouds |
| close02 | 270x480, 16 | ~30 s | 0.14 / 22% / 55% / 0.2% | Puddles now mirror the sky |
| test10 | 540x960, 32 | 147 s | 0.18 / 35% / 43% / 2.1% | Wider leaf lobes, gravel bed |
| final, 1st | 540x960, 64 | 290 s | 0.18 / 35% / 42% / 2.2% | |
| close view, 1st | 540x960, 64 | 298 s | 0.16 / 23% / 50% / 0.2% | |
| final, 2nd | 540x960, 64 | 315 s | 0.18 / 35% / 42% / 2.2% | Fence moved into the frame, broader leaves |
| close view, 2nd | 540x960, 64 | 318 s | 0.16 / 24% / 50% / 0.2% | Warm light too low; brightened at the finishing step only, kept at 4.2 → **closeup.png** (0.21 / 26% / 43% / 0.5%) |
| final, 3rd | 540x960, 64 | 303 s | 0.18 / 35% / 41% / 2.2% | Slightly stronger pond mirror → **final.png** |

The warm share sits at 35%, close to the 36% top of its band.

**The owner's two later messages**
- **"Give this picture."** I took this as two things: make the path look like the second picture, and draw that picture itself.
  - On the path I rebuilt the near slabs with rough tops and worn round edges. The hollows hold water that mirrors the sky, with a ripple.
  - The fallen leaves now have seven toothed lobes, veins and a stalk. There is gravel and moss in the joints, and high clouds for the puddles to mirror.
  - The close view is drawn from the same scene (add `--closeup` to the command). It is dusk in the film's look, so it is darker and bluer than the owner's golden-sun photograph.
- **"Use PBR wherever possible."** The photographed (PBR) surfaces now carry the stones, rocks, boards, plaster, soil and gravel.
  - I moved the slabs' small bumps into the photographed surface and replaced about 300 modelled pebbles with a photographed gravel bed.
  - Real shape is kept only where it has to be: the slab hollows (water must lie in them), the roof tiles, rafters and lattice (the look asks for relief), and leaves and plants (their outline is their shape).

**What I checked and fixed** (by looking at the full-size picture part by part)
- Path stones looked like crinkled foil.
- Puddles looked like black holes because they mirrored the dark eave or a steep dusk sky.
- The jar's pattern read as polka dots.
- The clogs read as two boxes.
- The mountains were hidden below the roof.
- The fence was standing just outside the frame.
- The leaves read as stars.
- The shadows were too warm.

The ladle, the falling water, the clogs and the stone lantern now read at full size.

**What I did not do**
- No light rays through the air.
- No steps up to the inn.
- No flowering shrubs.
- No lotus; there are water lilies instead.
- The pine is simple, and the mountains are smooth.
- I did not touch the store or the plugin, because the kit is a frozen copy.

**Made here that the store lacks** (for the rule that every new set updates the plugin): all of these are functions in render_final.py.
- The rough slab with a hollow that holds a puddle.
- Puddle water that mirrors strongly enough to read in a close view.
- A Japanese roof (curved, corners turned up, rows of tiles, tile ends, rafters) with a front gable.
- The arched bridge.
- A lit stone lantern whose panes let light out.
- The basin with spout, falling water and ladle.
- The bamboo fence with ties, and bamboo stems with leaves.
- The hanging lantern, and paper screens (lit and dim).
- Maple crowns made by putting leaves on the store's bare tree; toothed fallen leaves with veins.
- Water lilies, ferns, the blue-and-white jar, the high cloud deck, and haze added to far things such as the mountains.

**Lessons for the Traps list**
- A puddle under an eave mirrors the eave and reads as black.
- Water seen from above mirrors only a little of a dusk sky; its mirror has to be made stronger.
- Leaves with narrow lobes read as stars.
- The camera's default far limit of 100 m hides distant mountains.
- Lights show to the camera unless hidden.
- One mishap of mine: a stop command matched its own shell and stopped it. It cost about a minute and damaged no files.

Files are in /home/claude/build-57-garden/work:
- final.png
- closeup.png
- render_final.py
- materials.md
- notes.md
