# 03 Research - Ucupaint

Written 19 October 2026. Everything marked "ran" was run on this machine (Linux, 4 processor cores, no graphics card, Blender 5.2.2 started without a screen).

## The short answer

**Ucupaint is a free add-on for Blender that lets you build a material as a stack of layers, the way a paint program does, and then turn the finished stack into flat pictures (colour, roughness, normal, height).** It is real, well kept and widely used. It loads and runs on Blender 5.2.2 here, and I could build layer stacks and bake pictures from it with no screen and no graphics card.

But for **our** job it does not help much:

* It makes the same pictures Blender's own nodes would make. It is a tidy way of arranging nodes, not a new way of making texture. When I compared its pictures with our "photograph" method (the bake harness), the inside of every shape matched to within a fraction of one brightness step. So it cannot make our pictures more exact.
* It cannot read a fitted description, and it has nothing that fits a texture to a reference picture. A plain default stack scored 0.115 against the brick reference on our compare tool (0.1 is what a different kind of surface scores).
* Its noise, cells and wave layers are **not seamless** (they do not wrap round the edges of a tile). We measured that. Our own seamless noise from `lib/recipe_tools.py` can be swapped in as the picture-maker of a layer, and I ran that and it stayed seamless, but it is a hack.
* To run it without a screen I needed two workarounds (written out below). It is built for people clicking in the interface, so scripting it is fragile.

**Verdict: borrow ideas from it (the layer-stack arrangement, the "transition" edge effects, and a few lessons). Do not build the job on it.** One narrow thing may still be worth a try later: baking edge-wear and corner-shadow masks from real geometry for the coal-mine scene (it ran here on a test cube, but I did not judge the result on real scene geometry).

---

## 1. What Ucupaint is

**One plain sentence:** Ucupaint is a Blender add-on that builds the material nodes for you from a list of layers (a colour layer, a brick layer, a dirt layer with a mask, and so on) and can bake the result into ordinary picture files.

**Concrete example first.** In the test I ran, I made a flat square and told Ucupaint, by script:

1. add a layer "Base": a solid brown-orange colour;
2. add a layer "Bricks" on top: a brick pattern, mixed in by multiplying;
3. add a layer "Soot" on top: a dark colour, but only showing where a noise pattern (its "mask") lets it through.

Ucupaint built all the Blender nodes behind that, and one command baked colour, roughness, normal and height pictures from it at 1254 x 1254 dots in 7.9 seconds.

**The general rule.** Ucupaint keeps a list of layers. Each layer has: a source (what makes the picture of the layer: a colour, a Blender texture such as brick or noise, or a painted image), a place on the surface (scale, rotation), a "blend mode" (how it mixes with the layers below it, such as Multiply or Add), an opacity, optional masks (black-and-white pictures that say where the layer shows), and a switch for each "channel" (colour, metallic, roughness, normal). It writes this into a Blender node group and keeps it up to date when you change a setting.

Words used in this guide, each with one meaning:

* **layer**: one item in the stack.
* **mask**: a black-and-white picture on a layer that says where the layer shows.
* **channel**: one kind of surface information: colour, metallic, roughness, normal.
* **bake**: turn the live node setup into a flat picture file.
* **seam**: the visible jump where the right edge of a tile meets the left edge when you repeat it.
* **photograph route**: our own method in `lib/bake_harness.py`: a straight-down camera over a square, showing one channel at a time as plain light.

**Former names (checked in the project's own history):** the add-on was first called **yTexLayer** (late 2018), renamed **yPaint** on 11 December 2019, and renamed **Ucupaint** on 24 January 2020 "to avoid confusion with yPanel" (commit messages 281142d8, 15c8607f, 67767cfd). Many internal names still start with "yp" or "y_" (for example the command `wm.y_new_layer`). The first commit in the history is dated 31 December 2017.

---

## 2. Checking what the chat answer said

| What the chat said | Verdict | Evidence |
|---|---|---|
| "Ucupaint provides free, open-source layer-based painting inside Blender." | **True** (with a small correction). | Licence is GPL-3.0-or-later; free. It is mainly a layer **manager** for materials; "painting" means you can also paint on image layers with Blender's own paint tools (not tested here, needs the screen). |
| "It supports masks, material channels and baking." | **True, and I ran all three.** | Masks (noise and cell masks), channels (colour, roughness, normal, plus a height picture) and baking all ran headless on 5.2.2. See section 4. |
| "A particularly useful replacement for Mixar's texture-layer editor." | **Unverifiable, probably a muddle.** | "Mixar" is a real product name but it is not an add-on. See section 3. I could not confirm that Mixar has a "texture-layer editor" at all. And we do not use Mixar, so there is nothing to replace. |

**What "Mixar" could be.** I found this (web search; I could not open every page):

* **Mixar** (Mixar AI, company Adeveda Enterprises Pvt Ltd, India, in beta) describes itself as "an AI-native fork of Blender built for agentic 3D asset creation" (agentcommunity.org page, which I read). That means a separate copy of Blender with an AI helper built in, not an add-on for ordinary Blender. A search-result mirror of its README says it is based on Blender 5.0 with "deep integrations for texture painting". The agentcommunity page does not mention texture painting or layers. So the name is real, and "texture painting" is claimed by a mirror, but I found nothing about a layer editor and no release or activity data.
* Names it could be confused with: **Mixer** (Ubisoft's add-on for several people editing a Blender scene together, not texturing), **Quixel Mixer** (a separate texturing program with layers), **Texture Mixer** (a Blender add-on, listed as alpha), **PBR Mixer** (another Blender add-on), **Mixos** (texturing in a web browser), **Mixamo** (Adobe's rigging service).

Whichever was meant, Ucupaint does not replace Mixar: Ucupaint has no AI, and it works inside normal Blender.

---

## 3. The real project

| Fact | What I found | Where it came from |
|---|---|---|
| Author | Yusuf Umar ("ucupumar"), with credited contributors | repository, extension page |
| Official sites | github.com/ucupumar/ucupaint ; extensions.blender.org/add-ons/ucupaint/ ; wiki ucupumar.github.io/ucupaint-wiki/ | fetched |
| Licence | GPL-3.0-or-later (GitHub shows GPL-3.0; the extension manifest says SPDX GPL-3.0-or-later) | repository, manifest in the zip I downloaded |
| Latest release | **2.4.9, dated 29 July 2026** (git tag date 2026-07-29; extension page agrees). Earlier tags: 2.4.8 on 14 June 2026, 2.4.7 on 25 May 2026 | git tags I cloned; extension page |
| Newest code | The main branch is already numbered 3.0.0 (not released). Last commit when I cloned: 19 October 2026 | clone |
| Activity | About 20 to 65 commits a month from March to October 2026 (counted from the history: Mar 19, Apr 46, May 56, Jun 64, Jul 63, Aug 63, Sep 31, Oct 18 so far). 2,640 commits in all | clone |
| Popularity | 2.3 thousand stars, 73 forks, 95 open issues, 5 open pull requests (GitHub page today). 304,335 downloads and a 5.0 rating from 146 reviews on the Blender extensions site | fetched |
| Blender versions | README: "works with all official versions of Blender starting from Blender 2.76". Extension platform build: Blender 4.2 LTS and newer. **Here: loads and runs on 5.2.2** | README, extension page, my tests |
| Does it phone home? | The extension-platform build has **no network permission** (files only) and does **not** contain the self-updater. The GitHub-branch version does contain a self-updater (downloads a zip from GitHub and can replace the add-on folder). I used only the platform build | manifest in the zip; file list; code reading |
| Recent fix that matters to us | 2.4.9 itself fixes "cannot open attributes output from geometry nodes (Blender 5.2)", so the author is actively tracking Blender 5.2 | tag message |

Date note: the extension page says the add-on "was first published March 25th, 2024" on the platform; the project itself is older (2017).

---

## 4. Tested here

Everything below was run with `blender -b` (no screen), 2 threads, Cycles on the processor. Downloaded files stayed in `third-party/ucupaint/`, each in its own folder (see the end of this section). I read the add-on's code for risky behaviour before running it (details in 4.1).

### 4.1 Download, safety reading, install, does it load on 5.2.2

* **Downloaded** the platform build, `add-on-ucupaint-v2.4.9.zip` (2,030,653 bytes), from the extensions site. Its SHA-256 equals the hash in the download address. The proxy did not block anything. I also cloned the project's history with git (about 96 MB) to read the code and the dates.
* **Safety reading before running.** I searched the release code for network calls, running other programs, deleting files, `eval` and `exec`. Result: no network use in the platform build (one unused `import requests` in `ui.py`, never called); no programs started; file deletions only of temporary pictures made during baking, of images you ask it to remove, and of tiles when it swaps UDIM tiles. It registers a few Blender event handlers (for example before saving, to auto-save images). Nothing alarming. The GitHub version's updater is the risky part (downloads and replaces the add-on), so I did not run that version.
* **Installed two ways, both worked:**
  1. The new way (an "extension"): `BLENDER_USER_RESOURCES=<my folder> blender -b --factory-startup --command extension install-file -r user_default --enable <zip>`. It printed `STATUS Installed "ucupaint"` and `Ucupaint 2.4.9 is registered!`. (The zip has an extra folder level; the installer coped with it.)
  2. The old way (a folder in `scripts/addons`): copied the folder in, `addon_utils.enable('ucupaint')`, registered, 119 commands available.
* **Gotcha 1: turn it on with `default_set=True`.** `addon_utils.enable(..., default_set=False)` failed with `KeyError: 'bl_ext.user_default.ucupaint'` because Ucupaint looks itself up in the preferences while registering. With `default_set=True, persistent=False` it works, and nothing is saved to disk.
* Registration prints four harmless warnings about enum defaults.
* **What it adds:** 119 commands whose names start with `y_` (inside `bpy.ops.wm`). Layer types you can add: IMAGE, BRICK, CHECKER, GRADIENT, MAGIC, MUSGRAVE, NOISE, VORONOI, WAVE, GABOR, VCOL (vertex colour), COLOR, BACKGROUND, GROUP, HEMI, EDGE_DETECT, AO. Blend modes: 19 (Mix, Add, Subtract, Multiply, Screen, Overlay, Difference, Divide, Darken, Lighten, Hue, Saturation, Value, Color, Soft Light, Linear Light, Dodge, Burn, Exclusion).

### 4.2 Making a layer stack by script (no screen)

Ran: `y_quick_ypaint_node_setup(type='BSDF_PRINCIPLED')` (makes the Ucupaint group and four channels: Color, Metallic, Roughness, Normal), then `y_new_layer(...)` many times.

* Worked: COLOR, BRICK, NOISE, VORONOI, CHECKER, GRADIENT, MAGIC, WAVE, GABOR, HEMI, EDGE_DETECT, AO and GROUP (a "folder" layer). A layer took about 15 to 20 milliseconds to add.
* **Failed: the MUSGRAVE layer type** on 5.2.2: `Node type ShaderNodeTexMusgrave undefined`. Blender folded the Musgrave texture into the Noise texture in version 4.1; Ucupaint 2.4.9 (and, from reading the code, the main branch) still asks for the old node. Use NOISE instead.
* Small gotchas: `solid_color` takes three numbers (red, green, blue), not four. Layers are listed **top layer first** (index 0 is the top).
* **Procedural masks by script worked:** `y_new_layer_mask(type='NOISE')` and `type='VORONOI'` on a layer. The mask types offered: IMAGE, BRICK, CHECKER, GRADIENT, MAGIC, MUSGRAVE, NOISE, VORONOI, WAVE, VCOL, HEMI, OBJECT_INDEX, COLOR_ID, BACKFACE, EDGE_DETECT, MODIFIER, GABOR, AO.
* **Wear stack ran:** base colour, bricks (multiply), "soot" with a noise mask, "moss" with a cell mask, then baked. The picture shows green moss patches and dark soot over brick, as expected (`out/t11/wear_stack_colour.png`).
* **Did not work:** adding a mask modifier (a ramp or curve that sharpens a mask) with `y_new_mask_modifier`: "poll() failed, context is incorrect". I did not find a way round this, so I could not make a sharp-edged patch mask from a noise mask this way.
* Stack opacity (`channels[0].intensity_value`), blend type per layer channel, mapping scale (`layer.scale`, `mask.scale`) and switching channels on (`channels[i].enable`) all worked by script.

### 4.3 What Ucupaint generates (so we know what is inside)

* One main group called "Ucupaint Material" (outputs: Color, Metallic, Roughness, Normal).
* Inside it, **one sub-group per layer** (named `.yP Layer <name>`), each holding: a texture node (for example a Brick Texture node), a Mapping node, a few Mix and Math nodes for opacity and blend, and an image-texture node for each image mask.
* The textures are Blender's ordinary texture nodes. So everything Ucupaint draws could be drawn by our own recipes with the same nodes.

### 4.4 Can our recipe node groups be used as layers?

**Not by a button; yes by a hack, and I ran the hack.**

* The layer type called GROUP means a **folder of layers**, not "use my node group as the source".
* Hack: inside a layer's own sub-group I replaced the Noise node with a node group (a wrapper around our `tileable_noise_group`, with an input called Vector and outputs called Factor and Color, like Blender's Noise node), linked in the same places, then changed layer settings (blend type, switched the layer off and on, set the scale) so Ucupaint rebuilt its connections, then baked.
* **Result:** the swap survived all of that, the layer still used our group, and the baked picture had a **seam ratio of 1.03** (1.0 means seamless), identical before and after the rebuild (largest difference 0).
* **Limits:** it is not a supported feature; the layer's panel would not show our group's settings; Ucupaint's own bump-from-layer needs extra neighbour copies of the source node that I did **not** swap, so I did not test a normal channel with the swapped source.

### 4.5 Baking headless, and are the pictures exact?

**Baking works without a screen, after two workarounds** (both written into `scripts/example_headless_stack_to_maps.py`):

* **Workaround 1.** The bake command normally runs a "pop-up" function first that sets a flag called `no_layer_using`. A script call skips the pop-up, so the bake crashes with `'YBakeChannels' object has no attribute 'no_layer_using'`. Fix used: set `YBakeChannels.no_layer_using = False` on the class before calling.
* **Workaround 2.** The bake code asks Blender for "the current 3D view, window and screen" (for example `bpy.context.space_data.type`). With no screen these are empty and it crashes with `'NoneType' object has no attribute 'type'`. Fix used: Blender's factory file still contains a window with a 3D view, so I lend that to the call with `bpy.context.temp_override(window=..., screen=..., area=..., region=...)`.

With those two in place, `bpy.ops.wm.y_bake_channels(width=..., height=..., samples=1, margin=0, fxaa=False, uv_map='UVMap', bake_device='CPU')` ran, and it needed no graphics card (the device setting defaults to CPU).

Pictures it made for a stack with colour, roughness and normal switched on: **Color, Roughness, Normal and Displacement (the height)**. Metallic was not baked (no layer had it switched on; I did not look further into why). Asking for `use_float_for_displacement=True` gave a height picture with 31,029 different levels once saved as a 16-bit PNG (our reference height maps are 16-bit, so this fits).

**How exact compared with our photograph route?** Same stack, same square, both made in one Blender session: Ucupaint's own bake, and our photograph method (straight-down camera, one channel shown as plain light, 4 samples with a box filter, as in `bake_harness.py`). Compared dot by dot (brightness steps out of 255):

| Size | Colour: error inside shapes | Colour: error on edges | Colour: share of dots off by more than 8 steps | Roughness: biggest error anywhere |
|---|---|---|---|---|
| 512 | 0.28 | 5.7 | 7.3 % | 2 steps |
| 1254 | 0.26 | 4.5 | 3.1 % | 1 step |
| 2508 | 0.25 | 3.7 | 1.6 % | 1 step |

Plain reading: **inside shapes the two routes are the same picture** (a quarter of one step is rounding). **On edges they differ** because the photograph averages 4 samples per dot (soft, anti-aliased edges) while Ucupaint's bake at 1 sample takes one point per dot (hard, jagged edges). Roughness matched to within rounding everywhere. So Ucupaint's baking is exact to what the nodes say, and it neither adds nor loses accuracy compared with ours. If we ever used a Blender bake instead of the photograph, we should use several samples to keep soft edges.

**Gotcha 2 (a real one for us): a colour texture feeding a single-number channel.** My first roughness picture was coloured (red, green and blue different), because the noise layer's Color output was feeding the Roughness channel. In the colour-noise case the roughness picture matched our photograph poorly (average error 15.7 steps, correlation 0.76). Setting `channel.socket_input_name = 'Factor'` (the grey output) fixed it (error 0.28). Lesson: always feed single-number channels from a grey output.

**Speed.** Ucupaint bake of colour and roughness: 0.2 s at 512, 1.5 s at 1254, 9.5 s at 2508. Our photograph route for the same two channels: 0.8 s, 6.2 s, 20.1 s. The gap is mostly that Ucupaint uses 1 sample and we use 4, so it is not a real speed advantage. All four maps of the example stack at 1254: 7.9 s. The bake size can be anything up to 16384 by the command's settings; I ran up to 2508.

**Are the normal and height maps consistent?** In the reference set, the normal map is a slope calculated from the height, so they agree almost perfectly (our compare tool reads a correlation of about -0.97 and 0.97 between normal and height slopes). In my example stack, Ucupaint's normal and its height picture agreed much less (-0.42 and 0.79). On a different small stack (the first all-channels test, `out/t06`), a Sobel slope worked out from Ucupaint's own height picture matched Ucupaint's normal map to a 1.7 degree average (the normal itself leans about 4.7 degrees on average, so about a third of the lean is not explained by the height). Meaning: Ucupaint bakes normal and height as two separate things and they are not guaranteed to agree; our route (height first, then normal from it) agrees by construction. This is from two small stacks only.

### 4.6 Seamless tiles

* **Nothing in Ucupaint makes a tile seamless.** I baked each texture layer at 512 dots, with default and with 2.5 times scale, and measured the seam ratio with our `texture_compare.seam_ratio` (1.0 is seamless):

| Layer | Seam ratio | Layer | Seam ratio |
|---|---|---|---|
| Brick (scale 1 / 2.5) | 0.70 / 0.30 (no jump) | Noise (1 / 2.5) | 29.4 / 14.2 |
| Checker | 0.00 | Voronoi (1 / 2.5) | 62.0 / 33.4 |
| Wave (1 / 2.5) | 5.1 / 4.2 | Gabor (1 / 2.5) | 15.6 / 7.6 |
| Magic | 2.8 | Gradient | 511 (a ramp has a seam by nature) |

  Brick and checker wrap only because whole bricks or squares fit the tile; noise, cells and Gabor do not wrap.
* The swapped-in seamless noise (4.4) measured 1.03. That is the only seamless result.

### 4.7 Edge effects ("transition" ramp and bump)

Ucupaint can add effects where a mask fades from on to off: a **transition ramp** (a coloured band, which could be a dark outline) and a **transition bump** (a raised or sunk edge). I ran both.

* Transition bump: switched on by script (`show_transition_bump`, `enable_transition_bump` on the Normal channel); the baked normal map showed thin lines along the mask edges and the height picture showed a step per cell. It works.
* Transition ramp: switching on worked and I could edit its colour ramp (the node is inside a sub-group `~yPL Ramp_Copy`); the baked colour changed. But **I did not get a clean dark outline**: these effects need a mask that fades gradually, and a noise mask is mostly mid-grey; I could not add the "sharpen" modifier headless (4.2). So: the feature exists and responds; I have not shown it drawing an outline like our references.

### 4.8 Baking from geometry (for modelling and wear)

Ran on a bevelled cube I unwrapped: `y_bake_to_layer(type='AO')` and `type='POINTINESS'`, with extra class values set the way the pop-up would (it also needs the same workarounds). Both returned FINISHED, in 0.7 s and 0.1 s at 256 dots, and made image layers. The pointiness picture ranged from 0.5 to 1.0 (edges stand out). The AO picture was all white, which is right for a lone convex cube (nothing shades it), so **that test proves it runs, not that the AO is good**. Other types on offer (not run): cavity, dust, bevel normal, multires normal, other-object normal, thickness and more.

### 4.9 Not tested (and why)

* **The interface.** A real Blender window did start on a virtual screen (Xvfb, software drawing, no graphics card), but the screenshot came back entirely black, and my script ran from a timer which has no 3D view (the same crash as workaround 2). So I never saw Ucupaint's panels and did not test clicking, **painting strokes**, preview mode, decals, UDIM tiles, image atlas, vertex colour painting, drivers, or the PSD export.
* The main (3.0.0, unreleased) branch: read, not run (it contains the self-updater).
* Normal channel with a swapped-in group source (4.4).
* Mask modifiers, BACKGROUND and VCOL layers, `y_merge_layer`, copy and paste of layers, large layer counts (the Texture Mixer listing warns that 8+ layers slow its own viewport; I did not test Ucupaint's).
* Anything on the six reference tiles: Ucupaint was not asked to reproduce them (it cannot be driven by a description).

### 4.10 Where the test files are

Everything is in `proc-work/third-party/ucupaint/`: `download_extension/` (the zip), `extracted_2.4.9/` (unpacked release), `git_clone_untrusted/` (history, read only), `blender_user_ext_route/` and `legacy_route/` (the two install tests), `scripts/` (my test scripts, each starting with a plain note; `example_headless_stack_to_maps.py` is the tidy worked example), `out/` (pictures: `example/` has colour, roughness, normal, height at 1254 and a compare sheet against brick; `t07_*` the exactness tests; `t09/sheet.png` every layer type; `t11/` the wear stack). Total about 170 MB; the downloads were about 100 MB (the 2 MB zip and the 96 MB git history); the rest is my own output.

---

## 5. Judged against our needs

1. **Pixel-accurate matching of a reference from a compact fitted description.** No help. It cannot read a description, and what it draws is what native nodes draw (shown by the exactness test). Its brick layer is Blender's Brick node with straight edges, far from the painted irregular outlines in our reference. An untuned stack scored 0.115 overall against the brick reference, about the level of a different surface. Accuracy still comes from our own element lists and wear layers.
2. **Many variants and larger areas.** No help beyond what we have. A bake can be big (2508 ran in 9.5 s for colour and roughness), but noise, cells and wave layers are not seamless, so bigger areas would show repeats or seams unless we substitute our seamless groups (the hack in 4.4).
3. **Lessons that transfer to other surfaces.** Some, mostly as ideas (section 7).
4. **Running headless and scripted with no graphics card.** It runs, but only with two workarounds that lean on the add-on's inside workings, one layer type is broken on 5.2.2, and any new version could break them. Our harness is simpler and more stable.
5. **Modelling (the coal-mine scene).** Marginal. The geometry-based bakes (AO, pointiness, others) ran on a test cube. Blender's own bake does the same job without an add-on; Ucupaint's gain is that the results arrive as ready-made layers with masks. I would try it only if we want per-object layered materials with wear masks, and test on the real scene geometry first.

---

## 6. Verdict

* **Use it for:** nothing in the core texture pipeline. If a person wants to hand-tune a material by clicking (not tested here), Ucupaint is the well-regarded free way to do that in Blender 4.2 and later.
* **Borrow ideas from it for:** how to describe a layered surface; the edge-band and edge-bump idea for outlines; the "one stack, several maps" design; and the lessons in section 7.
* **Skip it for:** reproducing references, seamless tiles, and as a dependency of our scripts.

Recommendation in one word: **borrow ideas only.**

---

## 7. What we could take into the job

**Algorithms to re-create as Blender nodes (no Ucupaint needed)**

1. **Outline band from a soft mask edge.** Ucupaint's transition ramp is, in effect: take a mask value m from 0 to 1, make a band that peaks where m is near the middle (for example `band = 1 - abs(2*m - 1)`, sharpened with a power or a ColorRamp), and mix a dark colour in by that band. This is a good fit for the dark painted outlines around bricks, slates and stones. The same band added to the height gives chunky edges. Test it on the brick outlines first.
2. **Edge bump from a mask.** Add a scaled copy of the smoothed mask (or of its band) to the height, then make the normal from the height as we already do. Keeps normal and height in agreement.
3. **Always feed single-number channels from a grey output** (roughness, metallic, height). A colour output into a single-number channel gave a coloured roughness map in my test.

**Workflow and structure**

4. **Describe a surface as an ordered list of layers**, each with: source (our element lists or a seamless noise group), place (scale, rotation, offset), blend mode, opacity, optional mask(s), and which channels it writes to. That is the same shape as our wear, outline and blotch layers, and it can be written into `description.json` and read by a generic generator. The layer record to copy is: `{name, source, scale, rotation, blend, opacity, masks:[{source, scale, blend}], channels:{colour, roughness, height}}`. The 19 blend modes are the standard Photoshop set, which Blender's Mix node already offers.
5. **Make every layer write colour, roughness and height from the same source in one pass**, so a layer cannot colour a place and forget to raise it.
6. **Keep the cross-check "photograph versus bake".** It showed that exactness holds inside shapes and that edge softness depends on samples. Our 4-sample box filter is the right choice for painted edges.
7. **To use Ucupaint's panel on one of our recipes (optional):** wrap our group so it has one input called `Vector` and outputs called `Factor` and `Color`, and swap it for the source node inside the layer's sub-group (the script `t10_custom_group_as_layer.py` shows how).

**File formats**

8. Our height maps are 16-bit PNG; Ucupaint's float displacement bake saved as a 16-bit PNG with 31,029 distinct levels, so nothing is lost either way. Ucupaint's own saved format is just a Blender file with node groups; there is no description format to copy.

**Things to avoid**

9. Do not use `MUSGRAVE` layers on Blender 5.x (use Noise). Do not run the GitHub-branch version without reading its updater. Do not depend on its operators from scripts without the two workarounds.

---

## 8. How to repeat the tests

```
# install once, into a private folder (does not touch your normal Blender settings)
BLENDER_USER_RESOURCES=<folder> blender -b --factory-startup --command extension install-file -r user_default --enable add-on-ucupaint-v2.4.9.zip
# run the worked example: builds a stack, bakes four maps, saves colour/roughness/normal/height PNGs
PYTHONDONTWRITEBYTECODE=1 BLENDER_USER_RESOURCES=<folder> blender -b --factory-startup -t 2 \
   --python third-party/ucupaint/scripts/example_headless_stack_to_maps.py -- <output folder> 1254
```

---

## Sources

| Title | URL | Date | What it gave me |
|---|---|---|---|
| Ucupaint on GitHub (repository page) | https://github.com/ucupumar/ucupaint | read 19 Oct 2026 | Licence, 2.3k stars, 73 forks, 95 open issues, README (Blender 2.76 and later; extensions for 4.2+) |
| Ucupaint repository history (my clone) | https://github.com/ucupumar/ucupaint (git) | latest commit 19 Oct 2026; tag 2.4.9 on 29 Jul 2026 | Real dates for releases, monthly activity, the renames (yTexLayer, yPaint, Ucupaint), the code I read and ran |
| Ucupaint on the Blender extensions site | https://extensions.blender.org/add-ons/ucupaint/ | version 2.4.9, 29 Jul 2026 | Version, Blender 4.2 LTS and newer, licence, 304,335 downloads, 5.0 from 146 reviews, files-only permission, the zip I installed |
| Ucupaint wiki | https://ucupumar.github.io/ucupaint-wiki/ | read 19 Oct 2026 | Page list (Quick setup, Channel, Layer, Mask, Modifier, Bake to Layer, Bake Channels...); no scripting or tiling pages |
| "Ucupaint - Layer based painting for Eevee and Cycles", BlenderNation | https://www.blendernation.com/2024/10/21/ucupaint-layer-based-painting-for-eevee-and-cycles/ | 21 Oct 2024 | Feature list (layers, masks, channels, baking, UDIM, decals, drivers) |
| Mixar (Adeveda Enterprises) | https://agentcommunity.org/m/mixar | read 19 Oct 2026 | Mixar is "an AI-native fork of Blender", beta, Indian company; no texture-layer editor mentioned |
| Mixar app README mirror | https://tomevault.io/tome/Mixar-AI/mixar-app | seen only in a search result (page returned an error when I opened it) | Claim that it is a Blender 5.0 fork with texture-painting features; licence statement unclear |
| Blender extension "Texture Mixer" | https://extensions.blender.org/add-ons/texture-mixer/ | seen in search results only | A different layered-texture add-on, alpha; shows the names that sound alike |
| Search results for "Mixer" | https://gamefromscratch.com/ubisoft-release-mixer-blender-add-on/ | seen in search results only | Ubisoft's Mixer is a collaboration tool, not texturing |
| Our own tools | `proc-work/lib/bake_harness.py`, `recipe_tools.py`, `texture_compare.py` | 19 Oct 2026 | The photograph route, seamless noise, seam ratio and scoring I compared against |
