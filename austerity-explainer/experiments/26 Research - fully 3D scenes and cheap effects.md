# Making the backgrounds truly 3D, plus cheap effects: tools, prices and tests

Research for chapter 3 onward. I read the pages and ran the tests on 13 October 2026. Nothing was bought, nobody was signed up and no project picture was uploaded. Each test is marked **tested here** or **their page says**.

---

## What I found, in short

**A concrete example first.** I put the chapter 2 brick works and model town (page 3; about 136,000 triangles) into Blender and had it draw one tall 1080 × 1920 frame on this machine.

- Blender's fast renderer, EEVEE, **does crash when started the usual way**, as the project notes say (lesson 67).
- It **works when Blender is given a virtual screen.** A virtual screen is a pretend display; the program for it (Xvfb) is already installed here. With it, Blender draws through software graphics, which means the processor does the 3D drawing that a graphics card normally would. A frame then took **about 20 seconds**.
- Blender's accurate renderer, Cycles, took **100 to 165 seconds** for the same frame.

Your camera rule keeps most shots still. So a 3D background can be drawn **once per shot** and reused behind everything that moves. I call that still picture a **plate**. **(tested here)**

What the findings mean:

1. **The tearing comes from guessing depth from a flat painting.** Every route that really fixes it puts true 3D shapes under the picture: shapes built in Blender, shapes made by an AI object maker, or a whole AI-made 3D place.

2. **The best fit with your painted look is to work in the opposite order to today:**
   - build the scene in 3D first;
   - draw one plate;
   - have Flux paint over that plate in the series style;
   - shine the painting back onto the same 3D shapes (the projection used in logs 22 to 24).

   I tested the "shine back" half for free. I used Blender's painterly filter as a stand-in for the AI paint-over: a filter that turns small detail into flat, brush-like patches while keeping edges sharp. I then moved the camera 0.6 and 1.5 units sideways, 2 units forward and 0.8 units up. **Nothing tore or smeared.** Surfaces the first camera never saw showed the model's own surface instead of a smear. In my rough test those surfaces were too dark; they need matching light.

3. **Baked light makes 3D models cheap to draw.** Baked light means the light is worked out once in Blender and painted onto the model. Baking it for the brick works took **47 seconds**. The film's browser then drew a test frame in **0.31 seconds instead of 0.85**. **(tested here)**

4. **Splat worlds work in the film's browser but are heavy.** A splat world is a 3D place made of millions of soft coloured dots, which is what AI world makers produce. With World Labs' public sample street:
   - 500,000 dots: **7 seconds a frame**;
   - 2 million dots: **25 seconds**;
   - the 2-million file capped to 600,000 dots: **9 seconds**.

   Drawing at half the picture size was no faster, because the cost follows the number of dots. Real sideways moves worked with no tearing. **(tested here)**

5. **Most atmosphere effects are almost free here:** haze, dust, rain, snow, sparks, light beams, ink outlines, grain and vignette.
   - Smoke, a crowd of 400 cut-outs, glow and mirror-wet ground each add about **0.3 to 0.4 seconds** a frame.
   - Background blur adds about **1 second**.
   - A painterly filter on every frame adds **2.5 to 4.7 seconds** in the browser, but only **1.6 seconds** inside Blender, once per plate.
   - Grain, vignette and a colour grade added afterwards with ffmpeg cost about **2 minutes for a whole chapter**. **(tested here)**

6. **Tripo makes single objects, not scenes.**
   - **Its free plan is no good for the film.** Tripo keeps all rights to what free users make, the models are public and use is non-commercial. Uploading a painting there would also publish it.
   - **Through fal it costs 20 to 40 US cents a model, marked "commercial use".** Tripo's own API is about the same (30 credits ≈ 30 US cents), and its Pro plan is US$20 a month. An API is a way for a script to use a service. **(their pages say)**

7. **The cheapest object makers on fal are SAM 3D (already used in log 22) and TRELLIS, at 2 US cents a run.** **(their pages say)**

8. **The strongest "one painting → whole 3D place" service is World Labs Marble.** Its own three.js splat library, Spark, ran here. **(tested here)**
   - It costs about **US$1.26 a world through its API**, with a US$5 minimum purchase.
   - Its app costs **US$35 a month** for commercial rights. The free plan is non-commercial and cannot download.
   - It would need your paintings uploaded, which is your decision.

9. **Licence traps for a public film about Britain:**
   - Tencent's open Hunyuan models forbid using or **displaying** their output in the UK, EU and South Korea.
   - Apple's SHARP is research-only.
   - The larger Depth Anything 3 models are non-commercial.
   - Sketchfab models marked NC (non-commercial) are out.

10. **Nothing good at turning a picture into 3D runs on this machine itself**, because those tools need large NVIDIA graphics cards. The practical paths are a hosted service (fal or World Labs) or building in Blender, which runs here.

---

## The five most promising routes

Money is in US dollars. About US$3 of the US$10 fal allowance is left. Anything new needs your yes.

| # | Route | Money | Effort | Camera freedom | What I tested | Biggest risk |
|---|---|---|---|---|---|---|
| 1 | **Paint over and shine back.** Build the set in Blender (for example a 1926 Glasgow street, the pithead, a Roman office). Draw one plate per shot. Flux paints over it in the series style, guided by the plate's distance picture. The stage shines that painting back onto the same 3D shapes. | About **4 to 10 cents a shot**, so about $1 to $2.50 a chapter | Medium to high: sets must be built, but they are reusable | Sideways, forward and up moves of the size your rule allows; draw plates a bit wider than the frame | The shine-back part, with a free stand-in for the paint-over: holds on moves of 0.6 to 1.5 units sideways and 2 forward | The AI paint-over may shift edges by a few pixels (lesson 80). Surfaces the plate never saw need matching light. Every painting still needs the period and symbol check. |
| 2 | **Blender sets with baked light, drawn live in the stage.** Same sets, no paint-over. Light is baked onto painted-looking textures; ink outlines, grain and a paper overlay pull them toward the illustrated look. | $0 to about $1 a chapter (a few AI-painted textures) | High: more modelling and texture painting | Any move | Baking: 47 seconds. Drawing: 0.31 instead of 0.85 seconds a frame. | Can look like a model railway unless the textures are painted well (your notes on the plain house and factory). |
| 3 | **Blender plates for still shots.** EEVEE draws each still shot's background once, with soft shadows, haze and the painterly filter. Only camera moves need many frames: 60 frames take about 20 to 25 minutes, or 16 seconds a frame with two Blender copies at once. The stage puts the cut-outs, graphics and effects on top. | Free | Medium: the stage and Blender cameras must match, and things must layer in the right order | Full 3D; frames only needed for moves | EEVEE 15 to 27 seconds a frame; two at once about 16.5 seconds a frame | A whole page drawn frame by frame would take 34 to 61 hours, so it only works because the camera stays still. |
| 4 | **A splat world from one painting** (World Labs Marble). The painting becomes an explorable 3D place shown in the stage with Spark. | About **$1.26 a world** through the API ($5 minimum), or $35 a month in the app; a separate service and account | Low to medium: three.js must be updated from 0.169 to 0.180 or newer for Spark | Full 3D within the world | Drawing their public sample street here: 7 to 25 seconds a frame | Invents what the painting didn't show, so period details must be checked. Soft or needle-like dots up close. Cannot be relit. Figures are not supported (use cut-outs). Needs uploads and payment: your decision. |
| 5 | **Paintings only far away; the near half 3D.** Sky and distant skyline stay painted (they barely move with the camera). The street, forecourt and buildings are Blender blocks; hero props come from SAM 3D or TRELLIS (2 cents) or Tripo through fal (20 to 40 cents). Each wears the projected painting, as in logs 22 to 24. | Cents a page | Medium: the smallest change to today's kit | Moderate; the far painting must stay far | Logs 22 to 24 (earlier rounds) | Needs a proper repaint behind every object (lesson 78), and AI paintings' perspective doesn't add up (lesson 80). |

These combine. For example, route 3 plates can be painted over as in route 1, with route 5's painting kept for the sky, and with the cheap effects listed further down.

---

## What I tested myself, with the numbers

The machine: 4 processors, no graphics card. Every frame is 1080 × 1920. Timings vary by about ±10%. Some early Blender runs overlapped with web-page reading (Cycles at 32 samples and part of the effects list), so those few may be 10 to 20% high.

### Blender (version 5.2.2)

Test scene: the town plus both brick works plus props, about 136,300 triangles. Samples are passes per pixel; more samples means less speckle and more time.

| Set-up | Seconds a frame |
|---|---|
| EEVEE started the usual way, with no screen | **Crashes** ("Couldn't open libEGL.so.1") |
| EEVEE with the virtual screen, 16 samples (graphics: Mesa llvmpipe, OpenGL 4.5) | 26.8 for the first frame (setting up), then 24.7 and 19.8. A lighter view (town plus works A) took 17.2. |
| EEVEE, 64 samples | 61 to 75 |
| EEVEE, 16 samples, with ray tracing on | 34 to 45 |
| EEVEE, 16 samples, haze box added | 21.7 (plain was 17.2) |
| EEVEE, 16 samples, Freestyle ink lines | 31.5 |
| EEVEE, 16 samples, painterly filter in Blender's compositor (size 9) | 18.8 |
| Haze, lines and painterly filter together | 42 |
| Two EEVEE copies at once | 32 to 34 each, so about 16.5 a frame overall |
| Cycles, 32 samples plus noise removal | 102 (may be a little high) |
| Cycles, 128 samples plus noise removal | 165 |
| Workbench (flat preview look only) | 1.3 (the first frame 4.2) |

Baking light with Cycles:
- Light only, works A, 1024-pixel picture, 64 samples, using the model's existing second layout (the one its corner shading already uses): **46.9 seconds**.
- Full colour, 1024 pixels, 32 samples: 10.9 seconds.
- Full colour, 2048 pixels, 64 samples: 68.9 seconds.

### The film's hidden browser (software graphics, three.js)

**Effects test scene:** the Glasgow tenement painting as a backdrop, works A (33,950 triangles), the ground and one warm lamp with shadows. It draws in **about 0.86 seconds a frame**. Each line below is that scene plus one effect. This scene is lighter than a real page, so read the **difference**. Grabbing each frame adds another 70 to 100 ms, not counted.

| Effect added | ms a frame | Difference |
|---|---|---|
| None (base) | 860 to 885 | — |
| Haze (three.js fog) | 897 | about 0 |
| 3 light beams (soft see-through cones) | 935 | +60 |
| 20,000 dust motes | 818 | about 0 |
| 4,000 rain streaks | 904 | +30 |
| 8,000 snowflakes | 870 | about 0 |
| 600 sparks | 840 | about 0 |
| Smoke or steam (40 big soft puffs) | 1,280 | +410 |
| Crowd of 400 painted cut-outs | 1,233 | +360 |
| 5 full-frame see-through layers | 1,193 | +320 |
| Ink outlines (inverted-hull trick) | 825 | about 0 |
| Toon shading instead of realistic | 391 | −480 (cheaper) |
| No shadows | 505 | −370 |
| Baked light map, no lamp | **314** | −560 (cheaper) |
| Grain and vignette pass | 867 | about 0 |
| Glow (bloom) | 1,200 | +330 |
| Background blur (BokehPass) | 1,943 | +1,070 |
| Painterly filter, radius 4 | 3,413 | +2,540 |
| Painterly filter, radius 6 | 5,567 | +4,700 |
| Mirror-wet ground (half-size reflection) | 1,245 | +375 |
| Glow, blur and grain together | 2,521 | +1,650 |

**Splat worlds with Spark 2.3.1** (World Labs' public "Narrow European cobblestone lane" sample):

| Splat set-up | Seconds a frame |
|---|---|
| 500,000 dots | 6.5 to 7.7 |
| 2 million dots | 24 to 27 |
| 2 million dots at half picture size | 23 to 26 (no gain) |
| 2 million dots capped to 600,000 by detail levels | 7.6 to 9.3, plus 11.8 seconds of preparation when loading |

Detail levels (Spark's "LoD", level of detail) show fewer, larger dots for things further away. The capped version looked almost as clean as the full one. The 500,000-dot file showed needle-like streaks.

**Shine-back test:** drawing the plate shone onto the town and works took 0.29 to 0.32 seconds a frame.

### ffmpeg after filming

300 frames:
- reading only: 0.9 seconds;
- plus grain: 1.2 seconds;
- plus vignette: 4.1 seconds;
- grain, vignette and contrast together: 5.3 seconds, about **2 minutes for a whole chapter**.

### For comparison: the stage today (project notes, not tested)

About 2.7 to 3 seconds a frame on painted-room pages and 12 to 16 seconds on detailed-model pages. Chapter 2's 8,110 frames took about 6 to 7 hours.

---

## Tool comparison

### A. Object makers (one picture → one 3D object)

All prices are as published on 13 October 2026. "fal" means fal's hosted version, which fal marks "commercial use".

| Tool | Price | Free tier | Licence for a public, monetised video | Runs here? | Script/API | Output | Painted input | Weak points |
|---|---|---|---|---|---|---|---|---|
| **Tripo (own site)** | Pro $20 a month (3,000 credits ≈ 200 models); Max $90 a month; Team $110 a seat; credit packs from $10 for 1,000 | 200 credits a month ≈ 13 models; "Public Models · Non-Commercial Use"; 15 exports | Free: **no** (Tripo keeps all rights, terms 5.2.1). Paid: yes, you hold the rights and Tripo won't train on your inputs. | No, hosted | Yes (v3 API) | GLB; FBX for quad meshes; conversion to others | Untested by me. Turn "delight" off to keep painted light. | Objects only. Parts mode can't carry textures. |
| **Tripo API** | About $0.01 a credit (2024 announcement). Picture → textured model 30 credits; +20 more detailed texture; +20 more detailed shape; +20 split into parts; picture → splat 30 credits (about 4 minutes) | 2,000 credits for new API accounts in 2024; current amount unknown | Pay-as-you-go counts as paid | No | Yes | Same | Same | The v2 API stops on 1 November 2026 |
| **Tripo through fal** | H3.1: $0.20 bare, $0.30 textured, $0.40 HD texture (+$0.20 detailed shape, +$0.05 quad). v2.5 the same. P1 $0.40 to $0.50. P2 $1.00 to $1.30. TripoSplat $0.05. | No | fal says commercial use | No | Yes (already used for paintings) | GLB/FBX; splats as PLY | Unknown | — |
| **TripoSR / TripoSG / TripoSplat** (open) | Free | — | MIT (fine) | TripoSR maybe on processors (not tested); the others need a graphics card | Code | GLB / OBJ / PLY | Older quality (TripoSR) | TripoSplat makes objects only, up to 262,000 dots |
| **Meshy** | Pro $20 a month (1,000 credits); Premium $40; Ultra $100. fal: Meshy 7.1 $0.80 bare, $1.20 textured. | 100 credits a month, up to 10 assets, downloads limited | Free: CC BY 4.0, so credit Meshy. Paid: private and yours. | No | Yes (Pro and up; textured = 30 API credits) | FBX, OBJ, USDZ, GLB, STL, .blend | Unknown | Small free allowance |
| **Rodin (Hyper3D)** | Creator $30 a month (≈60 models); Business $120 a month (API). fal: $0.40 (+$0.80 HighPack); Fast $0.10. | Pay per result at $1.50 a credit | Paid: "any use". Free: not stated. | No | Business plan or fal | GLB etc. | Strong shapes (secondary source) | API only on Business |
| **Hunyuan3D, open (2.1)** | Free | — | **Risky:** Tencent licence forbids using or displaying the output in the UK, EU and South Korea | No (10 to 29 GB graphics card) | Code | Mesh | Good textures (vendor claims) | Territory clause |
| **Hunyuan3D through fal** | v3 and v3.1 Pro $0.375 (+$0.15 PBR materials, +$0.15 extra views, +$0.15 triangle count); v3.1 Rapid $0.225; v2 $0.16 bare or $0.48 textured; mini $0.10; mini turbo $0.08 | No | fal says commercial use; how Tencent's territory clause applies to hosted versions is unclear | No | Yes | GLB | Unknown | — |
| **TRELLIS / TRELLIS.2** (Microsoft) | fal: TRELLIS **$0.02**; TRELLIS.2 $0.25 / $0.30 / $0.35 (512 / 1024 / 1536 detail); re-texturing endpoint | Open weights | MIT (fine) | No (about 24 GB graphics card, secondary sources) | fal | GLB, PLY, splats | fal tags it "stylized" | Small holes in meshes (secondary source) |
| **Stable Fast 3D / SPAR3D** (Stability AI) | Free | Weights need a Hugging Face account | Free if annual revenue is under US$1M | SF3D's README says it runs on processors | Code | GLB | Older (2024) | Not on fal now. Not tested. |
| **SAM 3D Objects** (Meta) | fal **$0.02**; "Align" (places objects and people together) $0.02 | Weights need approval | SAM licence (commercial use fine) | No | fal | GLB per object, splat PLY, a combined scene | **Tested in log 22:** good from the painting's view after projection | Hidden sides are invented. Layout needed fitting. |
| Hi3D v3.0 / Pixal3D (fal) | $2.10 to $9.10 / $0.30 to $0.42 | — | fal commercial | No | fal | GLB | Unknown | Hi3D is expensive |

On quality: I found no independent test on painted pictures. A blog by a competitor (Sloyd) citing a "Top 3D AI" ranking on 3 August 2026 put Tripo v3.1 first. Other 2026 guides rank Tripo and Meshy first for hosted use and TRELLIS.2 first for open use. **Treat these as opinions.**

**A cheap comparison test (your yes needed):** one painted cut-out (say, the cart or the lathe) through TRELLIS, SAM 3D, Tripo H3.1, Hunyuan v3.1 Rapid and TRELLIS.2 would cost about **$0.82**.

### B. World makers (one picture → a whole 3D place)

| Tool | Price | Free tier | Licence | Runs here? | API | Output | Shown in three.js / Blender | Weak points |
|---|---|---|---|---|---|---|---|---|
| **World Labs Marble app** | Standard $20 a month (≈12 worlds, splat downloads); **Pro $35** (≈25 worlds, detailed meshes, **commercial rights**); Max $95 (≈75) | 7,000 credits ≈ 4 worlds, **no downloads, non-commercial** | Paid: yours. Inputs licensed to World Labs (training; paid users can opt out; inputs may be visible to others). | Hosted | — | Splats as SPZ or PLY (about 2M or 500k dots); rough collision mesh; ≈600k-triangle textured GLB, taking up to an hour | **Spark (tested here)**; Blender 5.3 imports SPZ and PLY | Invents beyond the painting; people "not well supported"; needs a sign-up and uploads |
| **World Labs API** | $1 per 1,250 credits, $5 minimum. World 1,500 + 80 for a picture ≈ **$1.26**; draft ≈ $0.18 | Separate from the app | Credit buyers own outputs; commercial use allowed | Hosted | Yes | Same | Same | Spending can run past the balance and be billed later |
| **Hunyuan World 1.0** (fal) | $0.30 a world (typical wait about 9 minutes); panorama only $0.15 | — | fal says commercial; the open version carries the UK/EU/South Korea clause | Hosted | fal | Layered mesh world file (optional Draco compression) | three.js mesh loaders; Blender | Panorama-based |
| FlashWorld, Lyra, Matrix-3D, HunyuanWorld-Voyager / Mirror | Free code | — | Apache 2.0 / NVIDIA / MIT / Tencent | No: need big NVIDIA cards (A100, H100 or 24 to 80 GB) | Code | 3D splats / points | Spark / Blender 5.3 | Would need a rented graphics card (money) |
| Apple SHARP | Free | — | **Research only** | No | — | Splats | — | Not allowed for the film |

Marble also has **Chisel**: you upload a rough GLB or FBX block-out (say, a Blender street) and it generates a detailed world around it. That is a way to control period layout. **(their page says; app only, not in the API)**

### C. Showing 3D: renderers and splat viewers

| Tool | Licence and cost | Runs here | Notes |
|---|---|---|---|
| Blender EEVEE | Free | **Yes, with the virtual screen (tested)** | 15 to 27 seconds a frame at 16 samples. Blender 5.3 adds "Material Lighting" nodes for toon and stylised shading (release notes). |
| Blender Cycles | Free | Yes (tested) | 100 to 165 seconds a frame. Use it for baking, not for filming. |
| Blender Workbench | Free | Yes (tested) | 1.3 seconds; flat preview look only |
| **Spark 2.3.1** (World Labs) | MIT, free | **Yes (tested)** | Needs three.js 0.180 or newer; the stage uses 0.169. Mixes splats with normal 3D models. Has its own background-blur settings. |
| GaussianSplats3D | MIT | Probably | Its author says it is no longer developed and recommends Spark |
| Blender 5.3 (beta until 4 Nov 2026) | Free | Not tested | Imports splats (PLY, SPZ); all three renderers draw them. Its own notes say "performance is not ideal". |
| KIRI 3DGS Render, BlendSplat (Blender add-ons) | Free | Not tested | Secondary sources |

### D. Free 3D models and textures for 1920s Britain and Italy

| Source | Licence | Account | What's useful | Checked |
|---|---|---|---|---|
| Poly Haven | **CC0**: any use, no credit | No | 521 models (barrels, lanterns, school desks, tool chests, industrial lamps, an iron gate), 868 textures (brick, cobbles, slate, plaster) | Counted through its public API today |
| Kenney | **CC0** | No | Simple props (low-detail style) | Licence page |
| Blendkit (BlenderKit renamed itself in June 2026) | "Royalty Free" (commercial use, no resale) or CC0 | Probably (not confirmed) | Large Blender library | Licence page |
| Sketchfab | Mostly **CC BY** (credit in the description); avoid NC | **Yes, account needed** | Search today found: tenements, UK terraced houses and shops, Victorian street lamps, a coal-mine cage and wagons, steam locomotives, Italian village and piazza scenes, typewriters, printing presses. **No colliery headframe or pithead winding gear.** | Public search API |
| Smithsonian Open Access 3D | **CC0** where marked | No | Museum objects (OBJ, glTF) | Secondary, 2020 |
| ambientCG / Quaternius | CC0 | No | Textures / simple models | Secondary |

Procedural building generators:
- **Buildify** (free Geometry Nodes add-on from 2022; licence not confirmed);
- a free Wallachian house generator (May 2026);
- a US$7 "Evergrande" generator ("free for any use").

**None is period-specific.** The project's own approach of building by script (used for the town and works) is still the surest way to get 1920s British terraces, a pithead headframe or a Roman ministry façade right.

### E. Making 3D look painted

| Method | Cost here | Holds still on camera moves? | Notes |
|---|---|---|---|
| **AI paint-over shone back** (route 1) | 4 to 10 cents a shot; shine-back drawing 0.3 seconds a frame | **Yes**: brushwork sticks to surfaces | Tested with a free stand-in |
| Painterly filter in Blender (Kuwahara node) | **+1.6 seconds** a plate | Still shots only | Tested; looks like brush patches on brick |
| Painterly filter in the stage | +2.5 to 4.7 seconds a frame | **No**: "boils" on moves | Tested. Maxime Heckel's article explains it. |
| Painted textures (AI-painted, or the filter baked into textures) | Cents | Yes | Not tested |
| Ink lines: inverted hull in three.js / Freestyle in Blender | ~0 / +14 seconds a frame | Yes | Both tested. Grease Pencil Line Art not tested. |
| Toon shading | Cheaper than realistic | Yes | Tested in three.js. Blender 5.3 adds lighting nodes for it. |
| Baked soft light, haze, grain, paper overlay | ~0 | Yes | Pieces tested |
| StableGen (Blender add-on: AI textures from several views) | — | Yes | GPL-3.0; needs an NVIDIA card and ComfyUI, so **not usable here** |

---

## Effects: what each adds, what it costs here

Costs are the differences measured above, unless marked otherwise. Chapter 3 examples follow your outline: the 1922 cuts including council homes, the return to gold in 1925, the miners and the 1926 General Strike, and Italy under De Stefani.

| Effect | What it adds to this story | Cost here | How |
|---|---|---|---|
| Haze or fog | Coal-smoke air over a mining town, a London morning; separates near from far in the tall frame | ~0 in the stage; +4.5 seconds a plate in Blender | three.js fog; Blender haze box |
| Light beams | Lamplight through a tenement or Treasury window, pithead lamps | +60 ms | See-through cones (tested); `three-good-godrays` (zlib-style licence) not measured |
| Dust motes | Still interiors: the economists' offices, a miner's kitchen | ~0 | Points |
| Smoke and steam | **Chimneys working, then going cold** when the pits are locked out; locomotives; kettles | +410 ms for 40 big puffs (fewer is cheaper) | Soft sprites or flipbooks; `three.quarks` (MIT) not measured |
| Rain | Hardship; council homes left half-built after the 1922 cuts | +30 ms | Line streaks |
| Snow | The miners' lockout dragging into winter 1926 | ~0 | Points |
| Wet-ground reflections | Lamplit cobbles (chapter 2 repainted these dry because coins had no reflection; true 3D makes real reflections possible) | +375 ms | three.js Reflector, flat ground only |
| Lamp flicker | Gas lamps, miners' lamps, candles | ~0 | Animate brightness (not measured; trivial) |
| Glow (bloom) | **Gold bars for the return to gold**, furnace mouths, lamps | +330 ms | UnrealBloomPass or `postprocessing` (Zlib licence) |
| Background blur | Focus pulls from a cut-out figure to the scene | +1,070 ms (the stage already has its own lens blur) | Nearly free when part of a Blender plate; Spark has its own |
| Film grain and vignette | An archive-documentary feel | ~0 in the stage; 1 to 15 ms a frame in ffmpeg | `noise`, `vignette`, `curves`, `lut3d` |
| Painterly filter | Turns 3D into brushwork | See table E | Blender compositor (plates) |
| Paper texture overlay | Ties back to chapter 1's paper | ~0 | Multiply layer or ffmpeg blend |
| Parallax layers | Depth from near and far cut-out layers | +320 ms for five full-frame layers | Planes |
| Sparks | Steelworks, forges | ~0 | Points |
| Crowds of cut-outs | **The General Strike crowds**, dole queues, Italian factory gates | +360 ms for 400 figures | InstancedMesh, one draw |
| Ink outlines | Links to chapter 1's engravings | ~0 | Inverted hull |
| Also worth knowing (not measured) | Cloud shadows sliding over the town, window-frame light patterns, falling leaflets, **blank** banners waving, heat shimmer over furnaces, a colour grade | Cheap: one textured light or one extra pass each | Standard three.js; keep banners blank and avoid any movement's flag (house rules) |

The kit's existing rule still applies: dust, smoke and every other effect belong to their page and are put away with it (lessons 16, 17 and 29).

---

## Detailed notes

### Tripo, scoped properly

**Free plan (Tripo Studio):**
- 200 credits a month ≈ 13 models; one task at a time; 10 models stored; 15 exports (model H2.5 only).
- "Public Models · Non-Commercial Use".
- Tripo's terms (section 5.2.1): for free users, Tripo "retains all rights … in the Inputs and Outputs".
- Its help page: commercial use only on a paid plan.
- So an uploaded painting would be published and Tripo would own the result. **Not usable for the film, and it breaks the no-upload rule.**

**Paid plans:**
- Pro US$20 a month (US$240 a year): 3,000 credits ≈ 200 models (about US$0.16 each), private models, commercial use, 10 tasks at a time. Adds Smart Segmentation (splits a model into parts), building from several views of one object, and a Blender bridge.
- Max US$90 a month (25,000 credits, 8K textures).
- Team US$110 a seat a month, or US$55 a seat billed yearly.
- New users get 50% off the first month.
- The toggle between monthly and yearly showed the same Pro and Max prices.

**API (programs, scriptable):**
- Picture → model: 20 credits bare, 30 with standard texture.
- Extras: +10, +20 or +30 for texture quality (up to 8K); +20 for a more detailed shape; +20 for split parts (cannot carry textures); +5 for quad; +10 for low-poly.
- Segmentation 40 credits; rigging 25.
- Picture → Gaussian splat: 30 credits fixed, about 4 minutes. It is made for objects on a clean background, not scenes.
- At US$0.01 a credit (Tripo's 2024 announcement; I couldn't see the current top-up page without signing in), a textured model costs about **US$0.30**, the same as fal.
- The API's "delight" setting, which removes lighting painted into the picture, is on by default with the newest texture model. **Turn it off to keep your painted light.**
- fal's H3.1 endpoint has no such setting. Which texture model fal uses is not stated.

**Formats:** GLB (FBX when quad); conversion to FBX, OBJ, USDZ or STL for 5 to 10 credits.

**Scenes:** none. Tripo makes one object at a time. Splitting into parts happens inside one object.

**Quality:** I found only vendor or blog rankings, which put it at or near the top. Nothing tested on painted pictures. Not tested by me.

**Open siblings:** TripoSR (MIT; its README gives graphics-card figures, and running on processors is not stated), TripoSG (MIT, needs a card) and TripoSplat (MIT; fal US$0.05).

### Where SAM 3D fits

It is already proven on your petrol station (log 22, 2 cents). fal now lists it as producing a GLB **and** a splat per object, plus a combined scene file. TRELLIS (MIT, 2 cents) is the other very cheap option. Both work best on solid foreground objects (cars, pumps, carts) that then wear the projected painting (lesson 74).

### Splat worlds in practice

- **Drawing cost follows the number of dots, not the picture size.** In my test, half size saved nothing.
- **For held shots**, draw the splat once as a plate (25 seconds), then reuse it.
- **For moves**, cap the dots (600,000 drew in about 9 seconds a frame and looked clean).
- **Upgrade needed:** Spark 2.x needs three.js 0.180 or newer, so the stage would need its three.js upgraded and its pages re-checked. I did not test Spark with the stage's 0.169.
- **Blender 5.3** (beta until 4 November 2026) will import splats directly, so a splat world could also be drawn in Blender together with your models.

### EEVEE on this machine: how

- Start a virtual screen (`Xvfb :97`), then run Blender with `DISPLAY=:97`. It finds Mesa's software graphics (llvmpipe, OpenGL 4.5).
- Plain `blender -b` aborts for lack of `libEGL.so.1`.
- The first frame includes about 10 to 35 seconds of setting up.
- Two Blender copies at once raise the total speed by about a third.
- Haze over the whole world turned the sky black; a haze box around the set worked.

### Baking light

The models already carry a second layout for their corner shading, so a full light bake drops straight into it: 47 seconds for works A. In the stage it becomes an unlit texture times the light map, drawn at about a third of the time of live lamps and shadows. A brand-new layout made automatically gave poor packing, so reuse or hand-tune the layouts.

### The paint-over step (not run, it costs money)

- fal's FLUX depth-control endpoint costs US$0.04 per megapixel, so about 8 cents for a full 1080 × 1920 plate and less at a smaller size. Flux edits were about 10 cents in log 22.
- Expect a few pixels of drift at edges (lesson 80). Keep the painted edges soft, or let the 3D silhouettes win.
- Draw plates wider than the frame. In my test, the near corner outside the first camera's view fell back to the plain model.

### Free depth tools that could run here (not tested)

These would replace fal depth pictures:
- MoGe-2 (MIT, open download);
- Depth Anything 3 small, base, metric and mono models (Apache 2.0); its large and giant models are **CC BY-NC, not allowed**;
- Marigold (Apache 2.0; also on fal for about $0.0006 a second).

---

## What I checked, what I didn't, what I'm unsure of

**Checked:**
- each tool's own pricing, terms and licence pages where they loaded (Tripo's needed a real browser);
- fal prices through the account's price lookup and fal's model pages;
- licence files read directly from each project;
- whether Hugging Face makes you sign in to download each model;
- all the tests above, run in my scratch folder.

**Not checked:**
- **any paid generation:** no tool's quality on your paintings, beyond SAM 3D in log 22;
- the AI paint-over step itself;
- Spark inside the actual stage;
- whole pages drawn with these methods;
- Blender 5.3;
- Grease Pencil Line Art, three-good-godrays, three.quarks, TripoSR, MoGe or Depth Anything run locally;
- the Skybox AI service: its current prices and licence weren't found, so I left it out;
- the independent 3D Arena ranking: the page wouldn't load.

**Unsure:**
- whether Tencent's territory clause follows Hunyuan models hosted on fal (fal says commercial use);
- Tripo's current API credit price and free API credits;
- whether Blendkit's free downloads need an account;
- my effects timings are on a simpler scene than a real page: trust the differences, not the totals.

---

## My test files

All in this session's working folder:

- `research-3d-evidence.jpg`: one sheet with all the key pictures: the render test, painterly crops, the shine-back test, baked light, splat detail, effects.
- `blender-tests/`
  - `render_anim.py`, `look_test.py`, `bake_lightmap.py`
  - `matrix.log`, `looks.log`
  - `render-sheet.jpg`, `looks-crops.jpg`
  - `out/` (frames, light map)
- `splat-test/`
  - `fx-bench.html`, `run-fx.mjs`, `fx-results.txt`, `fx-results-2.txt`, `fx-sheet-all.jpg`, `baked-compare.jpg`
  - `splat.html`, `run-splat.mjs`, `compare-lod.jpg`, `sheet-lane500k.jpg`
  - `proj-demo.html`, `run-proj.mjs`, `proj-sheet.jpg`, `proj-crops.jpg`
- `web/`: saved page texts, licence files, Sketchfab and Poly Haven search results.

The project's own files were only read, never changed. Copies of works A, the town, one painting and one cut-out were made inside the scratch folder.

---

## Sources (all read 13 October 2026)

**Tripo**
- Pricing: https://www.tripo3d.ai/pricing
- Commercial use help page: https://www.tripo3d.ai/help/privacy-policy/how-to-use-tripo-models-commercially
- Terms (last updated 11 July 2025): https://www.tripo3d.ai/terms
- API billing and v2 retirement notice: https://platform.tripo3d.ai/docs/billing , https://platform.tripo3d.ai/docs/introduction
- API announcement (2024): https://www.tripo3d.ai/blog/announcement-tripo-openapi-platform-payment-system
- Developer docs: https://developers.tripo3d.com/en/docs/generation-image-to-model , https://developers.tripo3d.com/en/docs/generation-image-to-splat , https://developers.tripo3d.com/en/docs/billing.md , https://developers.tripo3d.com/en/pricing

**fal model pages and price lookup**
- https://fal.ai/models/tripo3d/h3.1/image-to-3d
- https://fal.ai/models/tripo3d/tripo/v2.5/image-to-3d
- https://fal.ai/models/tripo3d/p1/image-to-3d
- https://fal.ai/models/tripo3d/p2/image-to-3d
- https://fal.ai/models/tripo3d/triposplat
- https://fal.ai/models/fal-ai/hunyuan-3d/v3.1/pro/image-to-3d
- https://fal.ai/models/fal-ai/hunyuan-3d/v3.1/rapid/image-to-3d
- https://fal.ai/models/fal-ai/hunyuan3d-v3/image-to-3d
- https://fal.ai/models/fal-ai/hunyuan3d/v2
- https://fal.ai/models/fal-ai/trellis
- https://fal.ai/models/fal-ai/trellis-2
- https://fal.ai/models/fal-ai/sam-3/3d-objects
- https://fal.ai/models/fal-ai/hunyuan_world/image-to-world
- https://fal.ai/models/fal-ai/hyper3d/rodin/v2.5
- https://fal.ai/models/fal-ai/hyper3d/rodin/v2.5/fast
- https://fal.ai/models/meshy/v7.1/image-to-3d
- https://fal.ai/models/fal-ai/pixal3d
- https://fal.ai/models/hitem3d/hi3d/v3.0/image-to-3d
- fal price lookup (connected account): flux-control-lora-depth, marigold-depth, sam-3/3d-align, hunyuan3d mini turbo

**Meshy and Rodin**
- https://www.meshy.ai/pricing
- https://docs.meshy.ai/en/webapp/pricing
- https://docs.meshy.ai/en/api/pricing
- https://hyper3d.ai/pricing

**Licences and model cards**
- Hunyuan3D 2.1: https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/LICENSE and its README
- HunyuanWorld 1.0: https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanWorld-1.0/main/LICENSE and its README
- TRELLIS.2: https://raw.githubusercontent.com/microsoft/TRELLIS.2/main/LICENSE , https://huggingface.co/microsoft/TRELLIS.2-4B
- TRELLIS: https://raw.githubusercontent.com/microsoft/TRELLIS/main/LICENSE
- Stable Fast 3D: https://raw.githubusercontent.com/Stability-AI/stable-fast-3d/main/README.md and its LICENSE.md
- SPAR3D: https://raw.githubusercontent.com/Stability-AI/stable-point-aware-3d/main/LICENSE.md
- SAM 3D: https://raw.githubusercontent.com/facebookresearch/sam-3d-objects/main/LICENSE
- Tripo open models: TripoSR, TripoSG and TripoSplat LICENSE files at https://raw.githubusercontent.com/VAST-AI-Research/ (TripoSR README too)
- Apple SHARP: https://raw.githubusercontent.com/apple/ml-sharp/main/LICENSE_MODEL
- FlashWorld: https://raw.githubusercontent.com/imlixinyang/FlashWorld/main/LICENSE and its README
- Matrix-3D: https://raw.githubusercontent.com/SkyworkAI/Matrix-3D/main/LICENSE
- Lyra: https://raw.githubusercontent.com/nv-tlabs/lyra/main/LICENSE , https://huggingface.co/nvidia/Lyra
- Depth Anything 3: https://raw.githubusercontent.com/ByteDance-Seed/Depth-Anything-3/main/README.md
- MoGe: https://raw.githubusercontent.com/microsoft/MoGe/main/README.md
- Marigold: https://raw.githubusercontent.com/prs-eth/Marigold/main/LICENSE.txt
- Hugging Face sign-in checks: https://huggingface.co/api/models/ (stabilityai, microsoft, tencent, facebook, apple, VAST-AI, depth-anything, Ruicheng)

**World Labs**
- App pricing: https://marble.worldlabs.ai/pricing
- API pricing: https://docs.worldlabs.ai/api/pricing.md
- Export file specs: https://docs.worldlabs.ai/marble/export/specs.md
- Mesh export: https://docs.worldlabs.ai/marble/export/mesh.md
- Exporting to Spark: https://docs.worldlabs.ai/marble/export/gaussian-splat/spark.md
- API FAQ: https://docs.worldlabs.ai/api/faq.md
- Prompt guidelines: https://docs.worldlabs.ai/marble/create/prompt-guides/index.md
- Image prompt tips: https://docs.worldlabs.ai/marble/create/prompt-guides/image-prompt.md
- Chisel basics: https://docs.worldlabs.ai/marble/create/chisel-tools/chisel-basics.md
- Generate-world API reference: https://docs.worldlabs.ai/api/reference/worlds/generate.md
- Terms of service: https://www.worldlabs.ai/terms-of-service
- Sample file used in my test: https://wlt-ai-cdn.art/example_exports/narrow_european_cobblestone_lane/

**Splat viewers and Blender**
- Spark: https://sparkjs.dev/ , npm package @sparkjsdev/spark 2.3.1
- GaussianSplats3D: https://raw.githubusercontent.com/mkkellogg/GaussianSplats3D/main/README.md
- Blender 5.3 release notes: https://developer.blender.org/docs/release_notes/5.3/ , https://developer.blender.org/docs/release_notes/5.3/rendering/ , https://developer.blender.org/docs/release_notes/5.3/eevee/
- Secondary on KIRI and BlendSplat: https://radiancefields.com/blender-5.3-will-bring-native-3d-gaussian-splat-import-and-rendering
- Blender manual:
  - https://docs.blender.org/manual/en/latest/compositing/types/creative/kuwahara.html
  - https://docs.blender.org/manual/en/latest/render/freestyle/index.html
  - https://docs.blender.org/manual/en/latest/grease_pencil/modifiers/generate/line_art.html
  - https://docs.blender.org/manual/en/latest/modeling/modifiers/modify/uv_project.html
  - https://docs.blender.org/manual/en/latest/render/cycles/baking.html
  - https://docs.blender.org/manual/en/latest/render/eevee/index.html

**Free assets**
- Poly Haven: https://polyhaven.com/license , https://api.polyhaven.com/assets?type=models
- Kenney: https://kenney.nl/support
- Blendkit: https://www.blendkit.com/docs/licenses/ , https://www.blenderkit.com/articles/goodbye-blenderkit-hello-blendkit/
- Sketchfab: https://sketchfab.com/developers/download-api , search API https://api.sketchfab.com/v3/search
- Smithsonian (secondary, 2020): https://www.cgchannel.com/2020/03/get-2000-free-3d-models-from-the-smithsonian-collection/
- Buildify: https://www.cgchannel.com/2022/07/download-free-blender-3d-building-generator-buildify/
- Wallachian house generator: https://www.blendernation.com/2026/05/26/free-download-generate-wooden-houses-with-this-geometry-nodes-setup/
- Evergrande generator: https://superhivemarket.com/products/procedural-buidings-evergrande

**Painterly and effects**
- https://blog.maximeheckel.com/posts/on-crafting-painterly-shaders/
- Susurrus (Codrops): https://tympanus.net/codrops/?p=113145
- StableGen: https://github.com/Zaws77/StableGen
- three-good-godrays licence: https://raw.githubusercontent.com/ameobea/three-good-godrays/main/LICENSE
- npm pages: postprocessing 6.39.5 (Zlib), three.quarks 0.17.1 (MIT), three-nebula 13.3.0 (MIT), n8ao 2.0.1 (ISC)
- three.js docs: https://threejs.org/docs/#api/en/materials/MeshBasicMaterial.lightMap

**Rankings (secondary, treat as opinions)**
- https://www.sloyd.ai/blog/ai-3d-model-generator-rankings
- https://app.cinevva.com/guides/ai-3d-model-generators
- https://medium.com/ideas-with-wings/best-ai-3d-model-generators-in-2026-tripo-ai-vs-meshy-rodin-kaedim-and-more-7eea7b05eb11

**Project files read**
- project story, Decisions, Lessons, style rules, lessons and traps
- experiments 22 to 24
- chapter 2 contact sheets and round-20 stills, paintings, painted rooms, cut-outs and Blender models
