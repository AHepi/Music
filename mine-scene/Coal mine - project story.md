# Coal mine - project story

## The goal

Build a coal-mine scene in Blender from the colour pictures, normal maps and displacement (height) maps you uploaded, and take a tall portrait photo of it that feels like the dusk pit village in your reference screenshot. You asked me not to use the film plugin; I also left the Astra add-on out, because I was not sure which one "plugin" meant.

## Where things stand

- **Done:** a full coal-mine scene and one finished photo, 1080 x 1920 pixels: "01 Coal mine - dusk photo 1080x1920.png". It shows a tall brick chimney with a plume of smoke, a steel headframe (the tower with the two big wheels), a brick engine house with a slate roof and glowing windows, mine carts on a curved track, a muddy yard with puddles, a row of village houses, hills, and a painted dusk sky.
- **Your pictures and maps are all used:** brick, slate, wood, rusted metal, mud and gravel. The mud, gravel, brick and slate show real bumps pushed out of your height maps, not just shading.
- **Stopped on purpose:** three reviewers had just started checking the scene (look and mood, materials, parts overlapping). You said "that's fine for now", so I stopped them. Their findings do not exist.
- **Known rough edges** (reported by the builders, not yet fixed): the headframe's front-left footing may touch the crate and plank pile beside the engine-house door; the inside of the engine house is nearly black; the carts' coal lumps look a little sharp-cornered up close; the stone parts (door frame, chimney base, footings) use a plain grey stone made in code, not one of your six pictures; the sky is a painted picture made in code, not a Blender sky.
- **Not tested:** the photo was rendered once at full size (128 samples, 8 minutes 11 seconds). I have not rendered other views at full size.

## How the pieces fit

| Piece | What it does | What it hands on |
|---|---|---|
| `lib/prepare_textures.py` | Turns your colour pictures and maps into the files Blender reads: flips the normal maps' green channel, smooths the height maps, makes a "how shiny" map for mud and metal | The prepared texture folder (not saved here; it is your upload) |
| `lib/mine_common.py` | The shared toolbox: where each big thing stands, the six materials, a fast shape builder that works out picture coordinates by itself, the ground height | Every part below |
| `modules/engine_house.py` | Brick building, door, windows, slate roof, shed, lamp | Objects |
| `modules/headframe.py` | The steel tower, rivets, wheels, ropes | Objects |
| `modules/chimney_and_smoke.py` | Brick chimney and the smoke plume | Objects |
| `modules/track_and_carts.py` | Rails, sleepers, stones, three carts, coal | Objects |
| `modules/ground_and_yard.py` | The muddy ground, ruts, puddles, coal lumps, timber, fence, lamp post | Objects |
| `modules/village_and_sky.py` | Village houses, hills, the painted sky, the lights | Objects, the sky and the lights |
| `assemble_mine.py` | Builds all parts, adds the engine-house floor and a soft warm light from the camera's side, sets the camera, takes the photo | The photo and a short report |

To make it again: unpack your uploads, run `lib/prepare_textures.py` (see its first lines), then
`blender -b --disable-autoexec --python assemble_mine.py -- OUT_NAME --width 1080 --samples 128`.

## Word list

- **Normal map:** a picture that tells Blender which way each tiny bit of surface faces, so flat things look bumpy.
- **Height map (displacement map):** a picture where brighter means higher; Blender can push the surface out by it.
- **Real displacement:** Blender cuts the surface into very small pieces and really moves them, so edges and shadows are true.
- **Headframe:** the steel tower over a mine shaft, carrying the wheels the lift rope runs over.
- **Engine house:** the building behind the headframe.
- **Render / photo:** the computer works out what a camera would see, one tiny dot at a time.
- **Samples:** how many times each dot is worked out; more is smoother and slower.

## Log (added to, never rewritten)

1. **Opened your upload safely.** Unpacked the zip into its own folder. It holds only normal and height maps for six surfaces; the colour pictures came from your message. The two mud colour pictures differ: only the blue-puddle one has maps.
2. **Checked the maps point the right way.** Measured them against each other: your normal maps have their green channel pointing down (the other convention), so I flipped it in a copy. The height maps are bright = high.
3. **Test panels.** Rendered each surface with raking light, normal map only and with real displacement; they agree, so the maps are consistent. First test of the ground looked like grass spikes: the relief was 30 cm tall; I lowered it to 6 cm (mud) and 4 cm (gravel). One panel rendered pure black: my test had it at exactly the same height as the floor.
4. **Built the shared toolbox** (`mine_common.py`).
5. **Six helpers built the six parts at the same time** (2 hours 41 minutes). Each checked its work against your design pictures.
6. **First assembly** (45 seconds at small size) worked, and showed: the smoke looked like giant black balloons; the headframe hid the engine house; the foreground was a field of coal rubble; the doorway looked onto nothing because nobody had built a floor.
7. **Fixes:** thinner, lighter, more irregular smoke leaving the chimney on a rising path; coal heaps moved out of the foreground; the track bent toward the camera so it sweeps across the bottom of the picture like in your screenshot; a floor in the engine house; a soft warm light from the camera's side so the mud and brick show their warm colours; ground made level around the buildings; far hills no longer hidden by the ground's bank; camera and exposure chosen by comparing ten small test photos with your screenshot. A first attempt at test cameras silently used the same camera three times (I typed the settings the wrong way); caught by looking.
8. **Reviewers started, then stopped** at your request.
9. **Final photo** rendered at 1080 x 1920, 128 samples, 8 minutes 11 seconds.

## Next step

Replace the picture textures with fully procedural Blender materials (the new texture job) and photograph the same scene again to see how close they get.
