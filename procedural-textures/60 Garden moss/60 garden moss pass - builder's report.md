# 60 The Japanese garden's mossy rocks and see-through pools - builder's report

What this file is: the report, word for word, of the fresh builder who gave every mossy rock in the garden real moss (decision 90) and made the path's pools see-through (decision 91; 6 November 2026, 12:55 to 14:28), from the plugin and the owner's words alone, with the brief `A change the owner asks for.md`. Saved by the session. Its words are in `60 garden moss pass - builder text.md`; the owner's later words about the pools reached it at about 13:39 with its clock moved to 14:45.

---

Report from the moss builder (build 57 garden). I worked to the kit's "A change the owner asks for.md" and kept every picture inside the bands in "The look.md". I finished at 14:28, 17 minutes before the 14:45 clock, so the session has time for its own Cycles picture. The end of this report says why I stopped there.

## What I changed

**1. The rocks with moss** ("I meant the rocks with moss. Not the pavement lol. Those are still lacking a lot of detail")
- **Every mossy rock** now has real moss on it instead of a green colour painted on the stone. That covers the 120 rocks along the pond and channel banks, the 14 round the basin, the lantern's seat and its pile of rocks, the single rocks, the two flat stones in the near water, the rock beside the basin, the basin's front stone and the pads under the veranda posts.
  - The moss is soft cushions with real thickness: 3.5 cm, and 4 cm on the near rocks. It is thick on the tops and in the cracks, with frayed edges, and creeps over the rims.
  - Tiny tufts about 2 cm high sit on the cushions, laid by the particle system. Pale lichen spots cover the bare stone.
  - Each rock along the bank gets its own amount of moss.
  - This comes from the store's new real-moss tool (decision 90). The rocks are still made by rules and laid by the particle system, as in the rocks pass.
- **The colour:** the store's moss came out as lime-green felt at dusk. I made it darker and more olive, turned down its sheen, and made its lumps show more.
- **The stone basin** now grows the same moss on its rim, sides and foot. Stone shows between the patches.
- **Real bumps** from the rock photograph's height picture are now on the lantern's rocks and the single rocks too, not only the four nearest the eye.
- **Where rocks meet the soil** there are now moss tufts and grass. I set four ferns by hand behind rocks and the basin, away from the path.
- **Left alone:** the paving, the stepping stones and the stone lantern, which is carved, not a rock.

**2. The pools on the path** ("semi transparent… looks like a liquid mirror")
- **Which pools:** all the pools in the slabs' hollows and the store puddle by the veranda, in both views.
- **Before:** they were solid, dark mirrors.
- **Now:** the stone under the water shows through, darker and a little warmer. The water reflects about half the light looking down, and more at the low angle of the main view. Each pool fades out towards its shallow edge, so there is no hard mirror outline. The lamps still light the stone under the water.
- **Exception:** the pool that reflects the hanging lantern keeps more of its reflection, about 0.8 against 0.5 for the others. That lantern's reflection is what keeps the close view's warm light inside its band.
- **One change to the light:** I raised the close view's brightness setting from 4.4 to 4.8. Without the bright sky in its pools, the close view's warm light had dropped below its band (0.28%). At 4.8 it is back inside, and overall brightness is the same as the earlier close view (0.21).

## Pictures
Measures are brightness / warm / cool / warm light. All are 540x960 unless marked "small".

| Time | Picture | Measures | Result |
|---|---|---|---|
| 12:57 | earlier script with the fresh kit (small, 12 samples) | 0.23 / 34% / 30% / 4.3% | inside |
| 13:03 | v1 final | 0.22 / 33% / 33% / 4.0% | inside |
| 13:07 | v1 close | 0.20 / 31% / 35% / 0.5% | inside |
| 13:11 | v2 final | 0.22 / 34% / 33% / 4.0% | inside |
| 13:16 | v3 close | 0.21 / 33% / 32% / 0.5% | inside |
| 13:20 | v4 final | 0.22 / 34% / 32% / 4.1% | inside |
| 13:26 | v5 close | 0.21 / 33% / 32% / 0.5% | inside |
| 13:30 | v5 final | 0.22 / 34% / 32% / 4.1% | inside |
| 13:37 | v6 final (64 samples) | 0.22 / 34% / 32% / 4.1% | inside |
| 13:43 | v6 close (64 samples) | 0.21 / 34% / 32% / 0.5% | inside |
| 13:45 | water test w1 close (small) | 0.19 / 32% / 32% / 0.2% | warm light low |
| 13:46 | water test w1 final (small) | 0.22 / 34% / 31% / 4.0% | inside |
| 13:48 | water test w2 close (small) | 0.19 / 33% / 32% / 0.3% | warm light low |
| 13:50 | water test w3 final (small) | 0.22 / 34% / 31% / 4.0% | inside |
| 13:57 | w4 close | 0.19 / 33% / 33% / 0.28% | warm light low |
| 14:04 | w5 close | 0.20 / 34% / 33% / 0.37% | warm light low; at 4.8 brightness: 0.21 / 34% / 31% / 0.42%, inside |
| 14:12 | w6 final | 0.22 / 34% / 32% / 3.9% | inside |
| 14:20 | w7 final = **final.png** | 0.22 / 34% / 32% / 3.9% | inside |
| 14:27 | w7 close = **closeup.png** | 0.21 / 34% / 31% / 0.43% | inside |

I looked at each one at full size and in 2–4x crops beside the earlier picture.

## What I checked and fixed
- **The fresh kit already changed the earlier script.** The store's rock tool now adds moss cushions by default, so the earlier script drawn today shows bright lime cushions the owner never saw. My script sets every moss choice itself.
- **No moss grew on the basin at first.** The store's grow tool needs a closed shape, and the basin is open underneath, so it grew almost nothing. I grow the moss on a hidden closed copy of the basin instead.
- **A fern landed on the path twice**, once in front of the bucket and once at the basin's front stone. The store's feet tool puts ferns on a random side of a rock, so I set the ferns by hand.
- **Lime felt:** the first moss read as smooth lime felt. I turned down the sheen, made the greens darker and the lumps stronger.
- **Pools too faint:** at first the pools read as pale, dry patches. I gave them half reflection and a darker stone under the water.
- **Close view too dark:** I fixed its warm light as described above. To test brightness settings I re-finished the saved raw picture, which takes seconds instead of a six-minute redraw.
- **The script runs** from another folder.

## For the owner's two questions (from the kit)
- **Eevee:** no. The kit's Traps.md says Eevee is slower than Cycles on this computer, which has no graphics card. A small test scene took 33–41 s in Eevee against 3.7 s in Cycles, and the azalea took 27.0 s against 13.2 s.
- **PBR:** yes for the rocks. They use the shelf's photographed `lichen_rock` set: colour, roughness, normal and height pictures. The moss cushions sit over the photographed `forest_leaves_02` set. The water is made in code, because there is no photographed set for water.

## What I did not do
- **The pools could be even more see-through.** I stopped here because the close view's warm light is only just inside its band (0.43% against 0.40%), and each try costs both full pictures, about 12 minutes.
- **The plugin and the store are untouched**, because they are outside my folders. The project rule says new tools and lessons go into `plugins/painted-place`, so these should be added there:
  - The grow tool needs a closed shape.
  - The feet tool puts ferns on a random side of rocks, so they can land on a path.
  - The moss's sheen reads lime at dusk.
  - Water made see-through by bending the light leaves the stone under it unlit, because that kind of lighting is switched off here.
  - Semi-transparent pools lower the close view's warm light.
- **Nothing in this report came from memory.**

## Command for the session's final picture
`python3 /home/claude/build-57-garden/moss/render_final.py 540 960 64 OUT.png`
This takes about 5.5 minutes. Add `--closeup` after the arguments for the close view, which takes about 6.5 minutes. The script's defaults draw exactly final.png and closeup.png.

Files are in /home/claude/build-57-garden/moss:
- final.png
- closeup.png
- render_final.py
- change.md
- notes.md
- materials - moss pass.md

---

## Traps

- This is the builder's own account; what the session checked afterwards is in the project story, log 60.
