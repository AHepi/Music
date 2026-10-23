# Blender 5.2 traps (each one cost a round somewhere)

What this is: the short list of Blender behaviours that surprised builders on this project, with how to avoid each.
"Tested" means it was run in Blender 5.2.2 while this file was written; "from the notes" means the project's own notes
record it. The kit's code already works around them; this is for when you write your own code.

1. **Set an image's colour space BEFORE writing its pixels.** Tested: a new image given pixels of 0.5, then set to
   Non-Color, came back as 0, 0, 0, 1 (black). Set the colour space right after `images.new`, then write, and never set
   it again.
2. **Image rows are bottom-up in Blender, and numpy pictures are read top-first.** Flip rows when you move a picture
   between them, or a normal map's green channel and a mask's up and down are wrong (from the notes). Colour pictures
   are sRGB; data pictures (normal, roughness, height, masks) are Non-Color.
3. **An Attribute node on an object that lacks the property reads 0** in both EEVEE and Cycles (tested in the
   weathering work). A layer that reads `pk_<layer>_amount` is silently off on every object that does not have it.
   Write the property on every object of the roles that need the layer, and read the report of which materials got it.
4. **Zero-user data is dropped when the file is saved.** The garden's saved file lost 58 materials and a node group the
   stages had replaced. If you replace a material or a mesh and want it back later (undo), give the original a fake user.
5. **Python's own errors do not change the exit code of a headless run.** Tested: `blender -b --python script.py` where the
   script raises still exits 0, unless you add `--python-exit-code 1`; `sys.exit(3)` in the script does reach the shell as 3.
   The launcher passes `--python-exit-code 1`.
6. **Blender's own Python has numpy but no Pillow, no OpenCV and no SciPy.** Tested. Anything that imports them fails inside
   Blender with ModuleNotFoundError. Plain Python outside Blender (the judge, the picture measures) may use numpy and Pillow.
7. **`use_auto_smooth` is gone** (tested: the mesh has no such attribute). For smooth shading with sharp edges use a Bevel
   modifier with harden normals plus a Weighted Normal modifier, and shade smooth.
8. **Cycles' device is a preference, not a scene setting.** Choose the compute type (OptiX, then CUDA) in the
   preferences, enable the devices, then set the scene's device to GPU. Print the devices. On one rented host Cycles ran on
   25 processor cores because the card was not enabled (from the notes). A GPU job that finds no GPU should stop and say so.
9. **EEVEE needs a screen.** With only the `bpy` module there is no libEGL; with the full program under a virtual screen
   (`xvfb-run -a`) EEVEE works. Cycles on the processor needs no screen.
10. **Blender's noise, cell and wave nodes do not tile**, even at whole-number scales (tested in the cookbook work). For a
    seamless tile make the height picture from periodic functions or noise made in Fourier space.
11. **Geometry Nodes multi-input sockets read their links in reverse order.** If a scatter picks the wrong piece, count the
    realised triangles of each piece against the pick table in a test.
12. **A Math node `DOT_PRODUCT` returns its answer on `outputs['Value']`**, not on the first output (from the notes).
13. **Negative emission clips to 0** in plain-light debug views; keep debug values positive (from the notes).
14. **Bump Distance** defaults to a nearly flat 0.001; use 0.02 to 0.1 for a visible bump, and never set Strength where
    Distance is the real fix.
15. **A light inside its own glow box is blocked in Cycles.** Put the glow box in front of the lamp and hide it from the
    lamp's rays.
16. **Free disk.** A saved test scene or a few EXR pictures fill a small disk. Keep big files on the rented store; turn
    `.blend1` backups off; if free space falls under about 0.4 GB, stop and report. And when a planning or filming check
    fails, look at the free disk (`df -h`) before you blame your change: the filming plan keeps a 4 GB reserve, and a
    machine with 1.3 GB free failed the check for that reason alone (from the notes, lesson 140).
17. **Geometry Nodes modifier inputs moved in Blender 5.2.** Set them with `mod.properties.inputs.<identifier>.value`, not
    `mod[identifier]` (from the notes: an add-on written for 5.1 broke this way, and the first courtyard test of the
    Japanese garden failed until a small shim in the builder's own script fixed it, leaving the person's add-on untouched).
    Test one input in your own Blender before building on it: `explainer-film-setup` prints a "Blender 5.2 probe" block
    that says which way works in the installed Blender.
18. **A collection's light-linking entries do not name their object in Blender 5.2.** Pair them with the collection's
    objects in order (from the notes, lesson 120; the kit's `set_dressing.light_reaches` does it for you), and check the
    first light with a small test picture. The setup probe also reads one pairing and says what it found.
19. **Build thousands of small shapes in bulk, never one object at a time.** One at a time gets slower as it goes: the
    garden's leaves took 7 minutes made one by one and about 10 seconds built in bulk from arrays (measured). Build them
    as arrays (`foreach_set`) into ONE mesh for each material, keep each mesh under about 300,000 triangles before
    displacement (judged, coal mine), and keep the number of objects low: object count, not triangles, is what slows
    scripts and exports. The audit holds the count to the house number `place_audit.objects_total_max`.
20. **Several helpers on one computer: give each Blender run a thread limit.** `blender -t 2` (or the computer's cores
    divided by the number of helpers), so they do not starve each other (the coal mine's six builders ran this way). The
    plugin's commands take it from the environment: `EXPLAINER_FILM_BLENDER_THREADS=2` before the command, and the
    launcher adds `-t 2`.
21. **Try a tool you have not used on tiny meshes first**, in the real Blender version, before you rely on it. Probes in
    the garden work found tools that fill only one colour slot, refuse objects with modifiers, or report the wrong
    settings: report what works and what breaks.
