### 7.4 How people make rubbish masks and litter in Blender today (research)

Again from searches; I say what I could read and what I only saw summarised.

| way | what I found | did I test it | my reading |
|---|---|---|---|
| **a mask picture from the street's plan** (a flat picture of where things lie, read by world position) | not a named technique in what I found; it is how the wetness layer's own bake works (one picture of the whole street, `tools/06_bake_maps_and_export.py`) | **Yes** (section 7.5) | the mask is a plain picture, so the person can paint it, the same picture can drive the muck layer, the scattered pieces and the glb's second texture coordinates |
| **masks from what the wetness layer already knows** | the layer has the gutter (the road's `Lowness`: 0 on the crown, 1 at the gutter), the pavement's kerb side, and the wall foot (`Wall Band`, measured from the cottage floor) | **No**, I used the plan picture instead | they sit inside the materials, so they cannot drive scattered pieces, nor be painted by hand, nor know doorsteps, rain pipes or props; but for a quick gutter-and-wall-foot dirt on ANY street they are free: plug `Lowness` and the wall band into a dirt colour |
| **distance to walls with Geometry Nodes** (the Geometry Proximity node) | the manual: it finds "the closest location on the target geometry" and gives its "Distance"; "the Map Range node is often helpful to use with the distance output to create a falloff with a maximum distance" ([manual](https://docs.blender.org/manual/en/4.2/modeling/geometry_nodes/geometry/sample/geometry_proximity.html)). Used on the ground's points with the walls as target it gives "near a wall" for any street | **No** | the right choice for a street that has no plan file; it needs a check that it ignores wall faces above head height |
| **ambient occlusion, bevel and pointiness nodes** for corners and edges | BlenderNation 2019 ([article](https://www.blendernation.com/2019/02/10/better-edge-and-cavity-masking-with-cycles/)): pointiness was the best procedural edge detector, the Bevel node later better, the AO node "much more convenient than baking"; a bug report says the AO node is close to unusable on bevelled models ([bug 90134](https://developer.blender.org/T90134)); a shader seller says Bevel and Pointiness only work in Cycles ([listing](https://blendermarket.com/products/principled-bsdf-wear-material), Blender 2.9 to 3.2, not checked for 5.2) | **No** | in the plate renderer (EEVEE) these would be screen-dependent and come and go with the camera; a world-position picture does not |
| **a painted muck layer in the ground material** (procedural dust, cinders, mud, driven by a mask) | everywhere; no single source | **Yes** | cheap; reads as a darker, duller strip; the first thing that makes the gutter look used |
| **small pieces scattered with Geometry Nodes** (Distribute Points on Faces, then Instance on Points) | the manual's "Scatter on Surface" page ([manual](https://docs.blender.org/manual/sr/latest/modeling/geometry_nodes/generate/scatter_on_surface.html), seen in a search summary): density per square metre or a fixed number, a **Distribution Mask** (near 1 scatter, near 0 none), a Selection; Poisson disk keeps the points apart; the points then take instances of a collection. Paid scatter packs exist ("Trash Scatter", "Scattercraft": not used) | **Yes** | the pieces are real small objects, so they catch the light and cast a shadow: they read as litter even when the muck layer is faint |
| **decals** (flat pictures of a stain laid on the ground) | common in games; no Blender source read | **No** | would suit the paper and leaf shapes at plate size; extra pictures to make |

### 7.5 The prototype: what I built, what it cost, what it looked like

**What it is** (`tools/b10_rubbish_plan_mask.py` makes the mask; `tools/b11_rubbish_prototype.py` has `add_muck()` and `build_pieces()` / `build_scatter()`; a first try, not a tool):

* **The mask** (section 7.3, `pictures/rubbish_plan_mask_lockout.jpg`): 450 x 4200 dots (2 cm), three channels. One for the street alone and one with the lockout shot's props. Each takes about a second to make.
* **The muck layer**, on the road, the pavements, the gutter and the kerb stones: the mask's red channel darkens the colour, puts cinder-coloured grit speckles (about 5 mm) on top, makes the surface duller (roughness toward 0.95, specular x0.45 to 1, coat x0.3 to 1) and adds a faint bump from the grit; the blue channel adds brown mud (roughness 0.4 again: wet mud shines a little). It chains after the joint picture: the code takes whatever feeds the Principled BSDF, so wetness, then joints, then rubbish.
* **The pieces:** eleven small objects built from simple shapes (cinder lumps, clinker, two coals, torn paper, sodden paper, a dead leaf, straw, a crock sherd, a stick; 1 to 10 cm), with plain materials (cinder grey-black, coal black, paper grey-brown, leaf brown, straw yellow-brown, china white, stick brown); **nothing printed on any of them**. Geometry Nodes places them: Distribute Points on Faces (Poisson disk, no two nearer than 6 cm) over the road, pavements, gutter and kerbs, the density being the mask's green channel times 140 (try 1) or 45 (try 2) a square metre, only up to 90 m (try 1) or 32 m (try 2) along the street; then Instance on Points with a random piece, a random turn and a random size of 0.7 to 1.5.

**What it cost** (this machine, two threads):

| | street, main camera 540 x 960, wet | close 640 x 480 | lockout shot 540 x 960 |
|---|---|---|---|
| no rubbish (joint picture only) | 74.9 s | 77.2 s | 205.1 s |
| try 1 (7,939 pieces street / 8,291 lockout, muck 1.0) | 88.8 s (with joints off: 71.8 s pieces only, 74.4 s muck only) | 89.0 s | 234.3 s |
| try 2 (1,990 / 2,180 pieces, muck 1.5) | 71.0 s | 90.8 s | 212.7 s |

So the layer costs 0 to 14 seconds on a street picture and 8 to 29 seconds on the lockout picture (+4 % in try 2, +14 % in try 1); the building of the nodes takes a fraction of a second. Memory was not measured.

**What it looks like** (`pictures/rubbish_try1_street.jpg`, `rubbish_try1_lockout.jpg`, `rubbish_try1_on_joint_picture.jpg`, `rubbish_try2_street.jpg`, `rubbish_try2_lockout.jpg`):
* **In the lockout shot it reads well** (try 2): cinders, coal bits and a few scraps lie round the drum's foot with a dark ash-and-soot stain, slack is spilled round the heap, there are scraps round the cart wheel and the sacks, and a ragged line of coal and grit lies along the right gutter and the foot of the right wall. Nothing looks modern and nothing is readable. At 540 x 960 the pieces are 1 to 6 dots wide.
* **In the street's main view it is faint:** try 1 shows dark flecks along the gutters and the wall foot; try 2 shows fewer; the muck layer's darkening is visible in the gutter and at the wall foot but easy to lose. **Both are dials** (density, amount): try 2 is the "faint" end, try 1 the "heavy" end; a good setting is between them, found by looking at a 100 % crop of a full-size plate (I did not).
* **It chains with the joint picture without trouble** (`rubbish_try1_on_joint_picture.jpg`): the joints still show beside the dirt.

**Weak spots I can see (not fixed):**
1. The mask's patches are blobby and the household factor makes seams every 4.5 m (visible in the picture of the mask): smooth the factor and use a finer noise.
2. The wall foot is dirtied only on the PAVEMENT; the walls' own foot (soot, mud splash up to 25 cm) is not done.
3. The pieces ignore wetness (dry colours; sodden paper is simply darker) and the props (a cinder could sit under a sack); I did not check for pieces inside props.
4. The straw (3 mm thick) is too thin to read at plate size; paper and leaf are the readable ones; a few larger shapes would help.
5. The muck layer has no joint awareness: dust sits in the joints and on the stones alike.
6. The rubbish is placed on the ground the camera sees: for another shot the y limit and the density need setting again.
7. The 1926 look of the colours (cinder, coal, ash, straw, paper) is my choice from section 7, not from a photograph.
