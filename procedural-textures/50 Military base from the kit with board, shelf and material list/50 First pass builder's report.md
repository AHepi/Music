# First pass builder's report (military base, kit with board, shelf and material list)

What this file is: the builder's final report, returned as text and saved by the coordinating session, shortened, unchanged in substance.

Finished 21:25 (deadline 21:55; stopped about 30 minutes early by its own choice: each change needed a test and a 4-minute redraw, and it judged the risk of breaking a picture inside every band not worth it). `final.png` 540 x 960, 64 samples plus finishing. `render_final.py WIDTH HEIGHT SAMPLES OUT.png` builds, lights, draws and finishes in one go, reading textures from the kit's shelf (1080 x 1920 at 8 samples took 2 min 42 s; 64 samples estimated 20 minutes or more). `materials.md` was the first deliverable and was kept true as the scene changed.

## What it built
A British army camp at dusk after rain, 1915. A duckboard track to a timber watch tower with a lit cabin at the vanishing point. Left: bell tents (one lit, door open), a hurricane lantern on a crate, a bucket, a rifle stack, a sandbag wall, a guardroom hut with a lit window and a thin smoke ribbon, a coil of barbed wire, loose planks, a long puddle mirroring the lantern. Right: a field gun, a second lantern, a puddle, drums and crates, a telegraph line. Far tents, hazy hills, a low sun behind the tower, grass tufts. Surfaces from the shelf: muddy_tracks, old_planks_02, distressed_painted_planks, rusty_corrugated_iron, rusty_metal_02, hessian_380, rough_linen. Wear: mud at the tent feet, splashes on the boards, rust streaks under the tower roof and sill, seams on the canvas.

## Light and frame
Low amber sun behind the tower (rim light, long shadows, glow in the haze); a thin blue haze box thinning with height; blue-black ambient; three small warm lights (tower window, lanterns, hut window), each light outside its glow body. Camera 1.55 m, 26 mm, horizon about 45 percent down. Finishing: mild brush softening, heavier smoothing of the sky, bloom from the brightest lights only, vignette, cool shadows and warm lights, grain.

## Pictures and measures (brightness / warm / cool / warm light)
p1 to p8 small debugging pictures (18 to 37 s); p9 540 x 960 (0.25 / 49 / 11 / 3.4, out of band); p11 inside every band; p14, p16 inside; final_try and final_b to final_e at 64 samples, about 4 min each, all inside; big_test 1080 x 1920 at 8 samples; final.png 0.28 / 22 / 34 / 4.1, inside every band.

## What it found and fixed
A black sky (a world-wide volume swallowed it; replaced by a bounded haze box); the ground vanished (the box's bottom on the ground plane); pale sand-coloured ground from grazing reflections of the horizon (dark blue ambient, sky boosted for the camera only); a lit tent door as a glowing slab; lamp halos blown out; wire stakes crossing the gun; a rope coil reading as a tyre; broken foreground boards; sky grain.

## What it did not do
Tents and tower still clean low-poly shapes (seams, mud and stains on the canvas, no patches or tears); the sandbag wall mostly hidden; the wire only a coil; the gun cropped at the right edge, shield and trail hard to read; the smoke ribbon faint; the middle-distance ground dark and plain; no tent patches, wire fence or larger gun; no full-size 64-sample picture.
