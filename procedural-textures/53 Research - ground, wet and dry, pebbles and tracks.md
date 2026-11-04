# 53 Research: ground, wet and dry, pebbles and tracks

What this file is: what real ground does and how game and film artists make it, gathered on 4 November 2026 before planning the store's ground tools (decision 69, your words: "Can we work on ground tools now. Maybe start with dry dirt ground, wet dirt ground, then adding making separate rocks/pebbles layers. Then add a tracks layer that automatically changes according to conditions of wet or dry. So human tracks, car tyre tracks, cart when tracks. The last two will need to add things like sink holes and depressions according to age and so on. Hmm maybe researching real world examples first. Look at how game studios do it."). Sources are at the end. The plan that follows from it is `53 Plan for Opus - ground tools.md`.

## 1. How artists build ground: layers, bottom to top

Every studio breakdown says the same thing in different words: ground is built as a stack of layers, each sitting on the one below by **height**, not by paint. The order:

1. **The base shape.** Big soft height variation first: hollows, humps, the camber of a road. Nothing else until this reads as ground you could walk on. "Always start with building height" (Chen, 80.lv). Everything after reads its position in this height.
2. **The soil.** One photographed or made surface for the dirt itself. Its colour and roughness are what the wet dial later changes.
3. **Stones, big to small, in several layers.** Professionals make rocks and pebbles in four or five size layers, big first, and let each layer settle where the layer above it leaves room (Zeltner's dirt generator: "rocks and pebbles created in 5 different layers from big rocks to tiny pebbles"). Small pebbles gather at the foot of bigger rocks and in hollows (Experience Points: pebbles scattered by the ground's occlusion, "so that the small pebbles will scatter there first"). Each stone layer is blended by height: a stone shows where it stands higher than the soil, and the soil covers its foot.
4. **The thin stuff on top.** Dust, leaves, needles, grass, ash: thin layers that lie in the hollows and against the foot of things, blended by height so they pool rather than paint.
5. **Wear, last.** Tracks, the polished path, the worn kerb: changes to the height and the colour where use happens.

Two rules repeat in every source:

- **Blend by height, never by a soft mask.** A pebble that fades in with a soft edge reads as painted; a pebble whose foot is buried by the soil's own height reads as lying there. Unreal's landscape layers, Substance's Height Blend and the Houdini forum all say it.
- **Water finds the low places first** (fxguide): puddles, damp and mud are not scattered, they sit in the hollows of the base shape. That one fact breaks up any repeating texture and is why a flat ground with painted puddles reads wrong.

## 2. Wet and dry: what changes

From the fxguide survey of wet rendering in games (Lagarde and others):

- **Wet is darker and shinier, not a different texture.** Water fills the pores of a rough surface, so it reflects less light diffusely (darker, more saturated) and more light as a mirror (sharper highlights). The darkening is strongest for mid-tone surfaces; near-black and near-white change least. The relationship is a curve, not a fixed share.
- **Porous things change a lot, sealed things little.** Soil, brick, stone, sand, cloth go very dark when wet; metal, glass, paint barely change colour and only gain a film of shine.
- **Four states of wetness, as games stage them:** dry; damp (darker, a little gloss); wet (dark, glossy, the surface's bumps still showing in the reflection); flooded (a flat mirror in the low places, the ground hidden under it). A good ground tool needs all four on one surface at once, decided by height: flooded in the deepest hollows, wet round them, damp beyond, dry on the crowns.
- **Drying is uneven.** Shine goes first, darkness stays: "a drying surface can look matte but still dark". Crowns and sun-side slopes dry first; hollows, shade and the foot of walls stay wet. Puddles shrink from their edges in, leaving a dark ring, then a pale crust of fine silt.
- **One asphalt example gave numbers:** diffuse scaled to 0.1 to 0.3 of dry, specular 5 to 10 times. For our look, the store's SURFACE materials already have a `Wet` dial that darkens and glosses; the ground tool should drive that dial from height and from the tracks, not from a flat number.

**Dry ground has its own signs, not just the absence of wet:** a pale crust, fine dust in a thin layer that takes marks, cracked mud where a puddle dried (polygons 5 to 30 cm across, wide and irregular when it dried fast in sun, small and regular in shade; the plates curl up at the edges in the last stage), and a bleached colour. Dry dirt roads also get **washboard** ripples across the way where vehicles go fast, and lose their fines as dust, so stones stand proud of a dry road and are buried in a wet one.

## 3. How tracks form and age (the real thing)

**Wheel ruts.** Two parallel grooves where the wheels run, pressed and worn into the ground. On soft ground the wheel pushes the soil sideways and down, so each rut has a **raised lip (berm) on both sides** and a flat or rounded bottom; on firm ground there is no lip, only a shallow worn trough. Ruts are deepest where vehicles slow, turn, start and stop (gateways, corners, the bottom of slopes), and shallow on the straight. Once a rut exists it **holds water**, water softens the ground, the next wheel deepens it: ruts and puddles are the same thing in the end. A road used by one kind of vehicle has one pair of ruts at that vehicle's wheel spacing with a strip of grass or gravel between ("a two-rut road"); a road used by many has ruts crossing ruts, widening at turns. Measurements for the period: a cart's wheels about 1.4 to 1.5 m apart (the Maltese study: 125 to 150 cm between rut centres; Roman and later carts the same), iron tyres 5 to 8 cm wide; a motor car of 1910 to 1920 about 1.4 m track, tyres about 9 to 12 cm wide, lorries wider and heavier; a motor tyre leaves a flatter, wider, shallower groove than a narrow iron cart tyre, which cuts a narrow deep slot. In deep mud the tyre's tread prints in the floor of the rut; a cart tyre prints a plain band, sometimes with the nail heads.

**Footprints.** In wet mud a boot sinks, the mud slumps outward so the print is bigger and softer-edged than the boot, the heel deepest, water pooling in it within minutes; the edge is thrown up a little. In firm damp mud the print is sharp and holds the hobnails. In dry dust a boot leaves only a brushed-clean oval where the dust was pushed aside, "sometimes only a fraction of an inch deep", seen by its colour change more than its depth. Many feet on one line make a **path**: a trodden strip 40 to 60 cm wide, lower than the ground beside it, polished in the middle, puddled in its hollows, the grass worn to earth along it (the army camp photographs show this between the tent lines).

**Ageing, from the tracking guides** (the same for a boot, a hoof or a wheel):

| Age | What it looks like |
|---|---|
| Fresh (hours) | sharp edges, dark damp floor with a sheen, loose crumbs and "mud balls" standing on the rim about to fall in, water not yet pooled |
| Half a day | surface drying paler, edges beginning to soften, crumbs fallen in, water pooled in the deep part |
| A day | everything dry on top, edges rounded, crumbs cemented, the floor matte but still darker than the crust; in rain the edges wash down |
| Days | rounded shallow hollow, debris blown or washed in, cracked floor where a puddle dried, the lip gone; a new track across it is sharper |

So **age is read from four things:** edge sharpness, the darkness and sheen of the floor, what has fallen or blown into the track, and whether the water in it is fresh (clear, in the whole groove) or old (shrunk to the deepest part, with a dry ring). A tracks tool that takes an age dial should move those four together.

**Potholes and sink-holes** (unpaved road engineering): they start where water stands in a rut or a low spot; traffic pounds the softened spot out into a round hollow with a steep front edge and a splashed-out back edge; the hollow fills with water and grows at its rim. They sit in the wheel lines, at gateways and where the road is flat with no camber to shed water. A road with a good crown has ruts but few holes; a flat, old, tired road has both.

## 4. How games draw tracks (what we can borrow, what we cannot)

- **Spintires and MudRunner** keep the mud as a height map and carve every wheel into it as it passes: the track strip is drawn into the heights, newer tracks over older, with a raised lip; tread detail is a second pass of parallax on top; wet and mud splashes are decals; the mud's colour is chosen by the slope of the carved surface (steep sides one texture, flat floor another). We cannot carve at run time, but the ideas carry: **a track is a change of height along a line, with a lip, and its colour follows the new slope.**
- **Batman: Arkham Origins and most snow games** accumulate footprints into a height texture under the ground and displace a tessellated mesh with it; the same technique is named for sand and mud. In Blender this is simply **displacement on a subdivided ground**, which we have.
- **Unreal terrain materials** blend layers by height with painted weights; "auto-materials" choose the layer by slope and height so steep faces are rock and hollows are mud. For us: **the soil, the pebbles and the wet decide by the ground's own height and slope**, and the builder paints only where a track goes.
- **Decal tracks** (the cheap way): tread patterns projected onto flat ground. They read as painted the moment the light is low, because nothing casts a shadow. Our look is low lamplight, so **tracks must be real depth**, not pictures.

## 5. What this means for the store's ground tools

1. **One ground object, subdivided, with real height,** is the foundation; everything else reads its height. The tool should make it (a plane with soft hollows and humps, an optional camber along a road line) or take the builder's own.
2. **Dry dirt and wet dirt are one material with a wetness that varies over the ground**, driven by height (hollows wet, crowns dry) and by a wetness number the builder sets for the whole place, with the four states on one surface; flooded hollows get the puddle tool's water.
3. **Stones are separate objects in size layers** (the store already lays setts and ballast stones this way), placed by the ground's own hollows and by the builder's say, buried to their feet by the soil, more of them where the ground is dry and worn (fines gone), fewer where it is mud.
4. **Tracks are carved into the ground's height along a line the builder gives:** a pair of grooves at a chosen wheel spacing and tyre width (cart, motor car, lorry), with a lip when soft, flat and shallow when firm, deeper at the ends and turns of the line; a single trodden strip for a footpath; single footprints as small stamps along a line with a stride. Each kind takes the ground's wetness: in mud it is deep, lipped and puddled; dry it is a shallow trough with pale crushed edges and dust.
5. **Age is one dial** that moves edge sharpness, floor darkness and sheen, debris in the groove, and how much water remains, together; potholes appear in old wet ruts at the points the builder names (gateways, turns) or at the deepest points of the line.
6. **Nothing places itself.** The builder gives the line, the kind of vehicle, the wetness and the age; the tool makes the marks there and nowhere else. The ground's own hollows decide only where the wet and the pebbles gather within the area the builder gives.

## Sources

- Lagarde and others, "Game environments, part C: making wet environments", fxguide: the wet/dry BRDF survey (darkening curve, porous vs sealed, the drying stages, water in the low places).
- Pavel Zagrebelnyy, "Mud and water of Spintires: MudRunner", Game Developer: the mud height field, tracks carved as strips, colour by slope, wet and mud decals.
- Colin Barré-Brisebois, "Deformable snow rendering in Batman: Arkham Origins", GDC 2014: height accumulation and tessellated displacement, named for sand and mud too.
- Pierre Zeltner, "Dirt generator in Substance Designer", 80.lv: rocks and pebbles in five size layers, grass covering the small stones.
- Yuting Chen, "Forest ground material", 80.lv; "Forest ground substance breakdown", 80.lv; Experience Points, "Environment artist fundamentals": height first, height blends, pebbles gathering by occlusion.
- Artur Schütz, "Landscape layer blending and height blending"; MythicLemon, "Paint textures on a landscape with layers": Unreal's height-blended layers and auto-materials by slope.
- Wikipedia, "Rut (roads)", "Puddle", "Mudcrack"; Dutch Fiber Trading, "Rutting in roads"; Renolith, "Understanding rutting"; Sandpoint Excavation, "What causes road rutting"; Enviroad, "Pothole formation on unpaved roads": how ruts form, hold water and become holes; crown and drainage.
- Jones and others, "The morphological variability of Maltese cart ruts" (Journal of Archaeological Science: Reports): rut widths 15 to 30 cm at the top, 5 to 15 at the base, 125 to 150 cm between centres.
- Tracking guides (Nature Mentor, "How to tell if animal tracks are fresh"; Trudave, "Tracking in baked summer mud"; Canada Fever, "Aging animal tracks"; Private Lands Wildlife, "Deer tracks"): how prints look in wet mud, firm mud and dust, and the ageing table.

## Traps

- The game techniques carve at run time; ours carve once, in code, along a line the builder gives. Do not build a simulation.
- Decal tracks (pictures projected on flat ground) look right in daylight demos and wrong under a low lamp: no shadow in the groove. Real depth or nothing.
- Wet darkening is a curve: the same dial turned on a pale dust and a dark mud must not darken both by the same share.
- The cart ruts' measurements are from stone; in mud the top is wider and the lip adds to it.
