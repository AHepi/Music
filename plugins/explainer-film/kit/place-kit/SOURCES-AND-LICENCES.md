# Sources and licences of the place kit

What this file is: where every part of `kit/place-kit/` came from, what was carried over, what was written new, what was left
out, and which licence governs anything that is not the plugin's own. Read it before copying a file out of the kit or adding a
file to it. Third-party code that is ever added keeps its own licence file next to it and a note here saying where it came from.

## The short answer

The place kit is the plugin's own work. It contains no third-party code, no third-party picture, no photograph and no model. The
only things it uses that it does not own are listed under "What it uses at run time".

## What was carried over (rules and numbers, not code)

The kit was made on 22 October 2026 from what the film owner's own projects had learned about believable places, and the code was
written new for the plugin, in its own plain words, with every number moved into the house-numbers table
(`kit/film-settings.json`, sections `place_...`) or a data file, each marked measured, judged or invented with its source:

| Part of the kit | Carried from (the film owner's own work) | What is new |
|---|---|---|
| Wear layers (`wear/layers/`) and their order | the weathering kit, the wet street and the street re-checks (the order dirt, grime, weathering, water, cracks, edge wear, moss, rubbish; the grime budget of about a quarter of an area and a third darker; roughness about 0.9 dry and 0.3 wet) | every layer is written new as a node group with a fixed interface, masks by name and an exact-zero amount |
| Surface recipes (`surfaces/heights.py`, `data/surfaces.json`) | the texture cookbook's relief tests (tile sizes, normal strengths, the rule that a normal map's green channel is flipped by a DirectX file), the garden character job (designed shapes read at film size, not scans) | twenty height recipes in numpy that tile without a seam, calibrated by slope |
| Normal maps (`surfaces/normals.py`, `checks/normals_test.py`) | the lessons "set the colour space before writing pixels", "a flipped green channel looks plausible" | the direction check against the map's own height and the end-to-end test light with a flipped control |
| Ground, ruts and roads (`surfaces/roads.py`, `ground_mesh.py`, `displacement.py`) | the coal mine yard's ground code and depths (a graded grid, ruts 0.15 m deep with a variation of about 0.13 to 0.21 m, gauge 1.24 m, banks, normal strength x 0.6 where displacement is on; the lighter 5 to 15 cm road of this kit is its own first try) | a plain height function of position; a uniform fine grid for a plain rectangle that is small enough, a graded grid for a big one, and a split in place for any other shape (a curved road, a ground with a trench); the audit measures the ruts from the real surface by rays |
| Plants and litter (`growth/`) | the garden ground builder (at least 8 tuft meshes, a scale range of 3 to 1, colours pulled 45 percent toward grey) and the street's litter masks | pieces built in numpy, joined per kind, with exact-zero gates and a recount from stored roots |
| Construction check (`checks/construction.py`) | the garden bridge checks (a bridge that "made no sense" was rebuilt from the ground up and then proved) | rest patches, joints, spans, flicker, doorways and buried lights, written new |
| Scale facts (`data/real_world_facts.json`) | the street and mine work's sizes | each fact carries its confidence (strong, weak, guess) and its source |
| Rented-card client and job taker (`render/client.py`, `render/worker/`) | the film owner's pay-per-second render set-up (the job kinds put, get, info, run, ping; pieces of about 6 MB; the card order OptiX, CUDA, HIP) | the client reads the person's own settings at run time and never prints them; a fake card is used in the tests |
| Renderer rule (`render/renderer_choice.py`) | the film owner's rule of 21 October 2026: Cycles where lamps, windows, lanterns or fires are lit, EEVEE when they are off | the rule as code with the reasons it prints |
| Picture measures (`calculators/picture_measures.py`) | the garden job's picture checks (value range, detail energy, flat windows, strong colour, squint) | a style guard made from the first honest picture and marked provisional |

Where the film owner's own notes on an add-on for gardens were used, only the rules they teach were taken (which things to check,
which traps to avoid) and they were rewritten in the kit's own words. No code, no file and no name from any add-on was copied.

## What it uses at run time (not shipped, not copied)

| What | Licence | How the kit uses it |
|---|---|---|
| Blender 5.2 | GNU General Public License | run as a program (`blender -b`); never bundled. The kit's code that runs inside Blender uses its `bpy`, `bmesh`, `mathutils` and the numpy that ships with it |
| numpy | BSD | used inside Blender (it ships there) and by the plain tools |
| Pillow | MIT-CMU (HPND) | used only by plain tools outside Blender (`picture_measures.py`, the picture tests); a check fails if code that runs inside Blender imports it |
| The `runpod` Python library | MIT | imported only by the job taker on a rented card (`worker/handler.py`), where it is kept on the card's own store; never bundled |
| RunPod's REST interface | the account owner's own terms | called by `render/client.py` with the person's own key and endpoint, read at run time |
| Poly Haven textures and models | CC0 (public domain) | NOTHING is shipped. `data/polyhaven_choices.json` is a small, even-handed sample of names read from the public Poly Haven list on 23 October 2026 (one or two per kind of surface and a few everyday props), not a shopping list: a helper searches the site for what its own place needs; they are fetched at run time, the real size is read before use, and every downloaded picture is opened and checked for stickers, brands and digits |
| Scenario's Blender skills (installed in the film owner's project) | the skills' own licences | their rules (use normals, never leave a plain colour, check the colour space) are summarised in the kit's own words in `skills/surfaces-wear-and-construction/`; no text of them is copied. Where this kit decides against one of them, `DEVIATIONS.md` says so |

## Where the real-world sizes come from

`data/real_world_facts.json` is judged, not measured: each fact has a range, a unit, a confidence and a source sentence. A fact
marked guess can only give a LOOK in the audit, never a fail, until a person confirms it with a real source. A place's own facts
file (`--real-world-facts`) is put on top of the generic fact of the same id (the keys it gives replace the generic ones; the keys it leaves out, such as the roles the fact applies to, stay).

## Rules for adding to the kit

1. Write new code in plain words; one name per thing; a note at the top of each file starting "What this does".
2. Any third-party code goes in its own folder with its licence file and a line in the table above saying where it came from and
   what was changed. Nothing is pasted in without its licence.
3. No picture, texture, model or font is added: they stay out of the repository and are fetched at run time.
4. No key, endpoint id, machine id, volume id, personal name, email or personal folder is written anywhere in the kit.
   `check_presets.py` scans for them (and for the rented-card settings folder used as a path).
5. No code names a kind of place (`data/banned_place_nouns.json`); data files and examples may.
