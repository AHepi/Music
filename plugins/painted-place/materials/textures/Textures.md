# Scanned surfaces

What this folder is: the photographed texture sets the dressing uses for the surfaces the street bundle never had (weathered timber, deck planks, bark, damp sand, driftwood) and for real stone grain over the bundle's own stone. All six are from Poly Haven and are CC0 (public domain): free to use, change and share, no credit required (the authors are named in `manifest.json` anyway). Each set is three pictures, 2048 x 2048 (the palm bark 2048 x 4096): colour (`diff`), roughness (`rough`, how matte) and height (`disp`, used as bumps). They were re-saved smaller (JPEG quality 88; roughness and height as grey) on 2 November 2026. The pictures a scene uses are packed into its dressed .blend, so the file carries them to another machine.

| Set | Real size of one picture | Used for | How it is laid on |
|---|---|---|---|
| `rough_wood` | 0.5 m | weathered boards (walls, posts, piles, planks, fences, boats), and driftwood (paler, greyer) | from three sides in the object's own space; grain along the object's longest side; each board its own patch and shade; then the plugin's peeling paint and rain streaks on top |
| `wood_planks_grey` | 1.5 m | a deck or floor laid as one flat slab | from three sides; planks along the slab's longer side; each plank shifted along its own length by a different amount, so a long deck does not repeat |
| `palm_tree_bark` | 1.3 m across, 2.6 m up (Poly Haven lists 1.3 x 1.3 m, but the picture is twice as tall as wide) | trunks named palm or coconut | from three sides; rings round the trunk |
| `bark_willow_02` | 2.15 m | every other trunk | from three sides; furrows up the trunk |
| `damp_beach_sand` | 2.0 m | the `sand` role | flat in world space at two sizes, mixed by a slow noise so the tile never shows |
| `sandstone_cracks` | 2.0 m | grain over the street's stone (wall shades, dressings, flags, rocks; never the setts) | multiplies their colour by the scan's own light and dark (average brightness kept) and adds its relief (14 mm on flags, where it breaks up reflections; 6 mm elsewhere); every ashlar block, flag and laid stone samples its own patch |

`scans.py` builds the materials; every dressed object carries its real scale and grain direction (`pp_scale`, `pp_grain`) for them, and every object and copy samples its own patch. `apply_by_role.py --no-scans` dresses without them (code-made timber, bark, sand and driftwood, no stone grain) for a before-and-after: run it on the undressed PLACE.blend, because a file dressed with the scans keeps them. If this folder is missing, the dressing falls back to the code-made materials by itself, and `tests/test_scans.py` fails if the folder is there but a picture or a manifest entry is broken.

## Adding a set

1. Pick a CC0 set on polyhaven.com whose real size you know (the site gives it).
2. Download the 2K JPEG `diff`, `rough` and `disp` pictures into a folder named after the set.
3. Add its entry to `manifest.json` (name, real size in metres, authors, the three file names, source, licence) and its average brightness (`mean_luminance`, from the colour picture in linear light).
4. Use it in `scans.py`, and add a row above.

## Traps

- Builders' shapes have no texture layout (UVs), so normal maps cannot be used (there is no direction to read them in); the height picture gives the bumps instead.
- A scanned colour straight from the picture is a daylight colour: every material darkens and dulls it into the look's range first (sand that is right in daylight turns to snow beside a fire).
- Planks pictures have their own board lines: they go only on flat slabs, never on timber the builder or the plugin already built from boards (the lines would cross the real boards).
- A small picture repeats: the 0.5 m wood is stretched along the grain and sampled per board; ground is sampled at two sizes. A new set used over large areas needs the same.
