# The interface of the slate layers - exact socket names (read this before you write a layer)

**What this page is.** The slate recipe is made of separate boxes (Blender calls them node groups) that you can open and switch off one by one
in the Shader editor: LAYOUT, COLOUR AND FADE, DAMAGE, MOSS, OUTLINE AND SHADOW and COMBINE. For the boxes to fit together they all have to
have the same sockets (the little dots on the left and the right side of a box). This page lists those sockets, spelled exactly as in
Blender, and the few rules that go with them. **It is fixed.** If you build a layer, you can rely on every name and meaning below; if you
think something must change, say so instead of changing it, because four people are building against it at the same time.

Words used (one word for each thing): a **tile** is the picture that repeats; **tile units** are shares of the tile (1.0 = the whole base tile;
at 1254 dots per tile, 0.0064 means 8 dots); a **dot** is one dot of a picture; a **slate** is one roof slate; a **joint** is the dark gap
between two slates of a row or between two rows; a **layer** is one of the four boxes that make colour, height and roughness; the **bundle**
is the eleven numbers LAYOUT gives to every layer.

## 1. The picture in words

```
          Vector (the tile coordinate)
             |
          LAYOUT  ---- eleven numbers for every dot (the BUNDLE) ----+------------+------------+------------+
                                                                      |            |            |            |
                                                              COLOUR AND FADE    MOSS  <---- DAMAGE   OUTLINE AND SHADOW
                                                                      |            |  (Damage Mask) |            |
                                                                      +------------+------+---------+------------+
                                                                                          |
                    LAYOUT's base_height --------------------------------------------> COMBINE --> Colour, Roughness, Metallic, Height
```
A layer never sees another layer's picture. It sees the bundle (where the slates are) and, if its file says so, the declared links (section 5).

## 2. The layout bundle: what LAYOUT gives every layer (11 numbers per dot)

These are the output sockets of the LAYOUT box and the same eleven input sockets of every layer box. All are plain numbers (floats). **Names are
written with small letters and underscores exactly like this.** "Typical" = what the default settings give on the slate reference size (1254 dots per tile).

| socket | what it is | range / units | typical (default settings) |
|---|---|---|---|
| `piece_id` | a random number, the SAME for every dot of one slate and different for each slate (the dots of the joint around a slate carry that slate's number too) | 0..1 | 48 different values in one tile |
| `row` | which row the slate is in: row number / number of rows | 0..1 (8 rows: 0, 0.125, ... 0.875) | the row that crosses the picture edge keeps ONE number (wrapped) |
| `local_x` | across the slate: 0 at its left edge, 1 at its right edge (follows the lean of the joints) | 0..1, cut off outside the slate (0 or 1 in the joint) | a ramp on every slate |
| `local_y` | down the slate: **0 at its top edge, 1 at its bottom edge** | 0..1, cut off outside the slate | a ramp on every slate |
| `piece_width` | width of this slate, joint not included | tile units | median 0.164 (206 dots), 0.08 to 0.2 |
| `piece_height` | height of this slate (its row, minus the band between rows) | tile units | 0.120 (150 dots), rows differ by about 4 percent |
| `edge_distance` | distance from the nearest edge of the slate, measured inwards, along the real (chipped, rounded) outline | tile units, 0 at the edge and everywhere in the joint, up to about 0.06 in the middle of a slate | a chip makes it 0 earlier |
| `top_edge_distance` | distance below the slate's UPPER edge (follows the chips of the top edge) | tile units, 0 at the top edge and above it | 0 to 0.12 |
| `gap_mask` | 1 in the dark joint (between slates of a row and between rows), 0 on the slate; soft over about half a dot at the edge | 0..1 | 7.5 percent of all dots (the reference: 7 percent) |
| `piece_mask` | 1 on the slate, 0 in the joint (`piece_mask` = 1 - `gap_mask`) | 0..1 | 92.5 percent of all dots |
| `base_height` | the relief of the bare slates, before any layer changes it: joints low, slates high, a rounded slope along the edges, a tiny random lift per slate, bottom of a slate a little higher than its top | 0..1 | joint 0.08; slate about 0.50 (plus or minus 0.04); slope 4 dots wide |

Three things that are easy to get wrong:
* **`local_y` runs DOWN the slate** (0 = top), but the Vector's y runs UP the picture (see section 4). Use `local_y` for anything that belongs to the slate (drips, shadow, lip) and Vector for anything that belongs to the whole picture (a slow colour change across the roof).
* In the joint the slate numbers are still defined (the joint belongs to the slate beside it) but cut off: use `gap_mask` or `piece_mask` to know where the slate really is.
* The bundle is made once per bake by LAYOUT. Layers must not try to recompute it.

Any other surface that can make the same eleven numbers (bricks, planks, tiles, plates) can use the same COLOUR AND FADE, DAMAGE and MOSS boxes: that is the reuse claim.
(`row` and `piece_width` etc. then mean "the row of bricks", "the brick's width".) What "the same eleven numbers" means: the names above, 0..1 and tile-unit ranges as above, `local_y` 0 at the top.

## 3. What every layer box looks like from outside

**Inputs** (in this order; the order does not matter to the recipe, the names do):

| socket | kind | meaning |
|---|---|---|
| `Vector` | vector | the tile coordinate: x = 0..1 left to right, y = 0..1 from the BOTTOM to the TOP of the picture. Use it for seamless noise (section 4). |
| `Tile Count` | number | how many base tiles fit across the whole picture (1 normally; 2 for a 2 x 2 area of new content). The recipe sets it from `recipe.tiles_across`. |
| the eleven bundle sockets | numbers | `piece_id`, `row`, `local_x`, `local_y`, `piece_width`, `piece_height`, `edge_distance`, `top_edge_distance`, `gap_mask`, `piece_mask`, `base_height` (section 2) |
| `Seed` | number | the layer's OWN random seed. Change it and only this layer's pattern changes. Defaults: colour_and_fade 11, damage 21, moss 31, outline_and_shadow 41 (layout 1). |
| `Amount` | number 0..1 | overall strength. **0 switches the layer off: Mask, Height and Roughness are exactly 0.** (`finish_layer` in `layer_interface.py` guarantees it.) |
| the layer's own controls | numbers or colours | whatever the layer builder wants to offer (each one is also a setting `layer.control`, section 6) |
| declared links | numbers | only if the layer's file declares them (section 5) |

**Outputs** (exactly these four, every layer):

| socket | kind | meaning |
|---|---|---|
| `Mask` | number 0..1 | where the layer paints. 1 = the layer's Colour fully covers what is below. |
| `Colour` | colour (linear, like every colour in Blender) | the colour the layer paints where its Mask is 1. It may vary across the surface. |
| `Height` | number, **0 = no change**, small plus and minus | the change this layer makes to the surface height. Heights are on the 0..1 scale of the final Height map: a slate stands about 0.42 above the joint; a visible chip is about -0.05 to -0.15; moss about +0.02 to +0.05. COMBINE adds them to `base_height`. A layer must already have applied its own Mask to it (0 where it does nothing). |
| `Roughness` | number, **0 = no change**, minus = smoother, plus = rougher | the change this layer makes to roughness. COMBINE adds them to the base roughness (0.8). Fresh slate smoother (minus), moss and damage rougher (plus). |

**The rule for the bottom layer.** COLOUR AND FADE is the bottom of the stack. COMBINE uses its Colour as the paint EVERYWHERE; its Mask is only a debug picture.
The three other layers paint over it where their Mask is.

## 4. Coordinates, tiling and sizes (the rules that keep the tile seamless)

1. **Sizes are tile units.** Every width, radius, scale and distance you write in a layer is a share of the tile (the bundle's distances are tile units already).
   That is why the same recipe looks the same at 512, 1254 and 2508 dots. Never write "8 dots". Write 0.0064 and say "(8 dots at 1254)".
2. **Noise must be the seamless kind.** Blender's own Noise node does NOT repeat at the tile edge. Use `LayerBuilder.tileable_noise(Vector, scale, detail, roughness, seed)`
   (it uses `lib/recipe_tools.tileable_noise_group`). `scale` = how many noise features fit across the WHOLE picture, so write it as
   *features per base tile x Tile Count*, for example `b.mul(b.input('Tile Count'), 12.0)`. Then a 2 x 2 area has twice as many features and the same look per dot.
3. **Feed noise the Vector, not the slate coordinates.** `Vector` repeats exactly. To give every slate its own pattern, add `piece_id` x a big number to the noise `Seed`
   (LAYOUT does exactly that for its chips: `seed = piece_id x 500 + layout seed x 7`).
4. **Random numbers per slate or per row**: use `LayerBuilder.hash4(vector, w)` (White Noise): the same inputs always give the same numbers. For "a different number for every slate" feed it `piece_id`.
5. **Whole numbers only** for anything that counts (rows, slates, copies): the tile only repeats exactly if counts are whole.
6. **Prove it** with `tests/half_tile_test.py` (section 8) before you hand your layer back.

## 5. Declared links: the ONLY way a layer may see another layer

A layer may read another layer's output only through a link written in its own file as a line in `DECLARED_LINKS`, and the link must be listed in this table and in the guide.
The recipe wires every declared link by itself (it reads the list) and refuses a circle (A reads B and B reads A).

| layer that reads | its input socket | comes from | plain meaning |
|---|---|---|---|
| MOSS | `Damage Mask` | DAMAGE's `Mask` | where the slate is damaged, so moss can avoid fresh damage or gather next to old damage |

That is the only declared link for now. A layer that needs another (for example "damage prefers faded slates") adds one line to its own `DECLARED_LINKS`
in the form `('Label', 'float', default, 'plain words', ('source layer key', 'Output name'))` AND adds the row to this table. The independence tests list these rows as the allowed exceptions.

## 6. Settings, controls and seeds

* Every control is a **setting named `layer.control`**, for example `moss.amount`, `damage.break_colour`, `layout.corner_radius`. Layer keys: `layout`, `colour_and_fade`, `damage`, `moss`, `outline_and_shadow`, `combine`, and `recipe` for the recipe itself.
* **Order of strength** (the later wins): the default written in the layer's own file (the `CONTROLS` list) < `recipe/settings.json` < the parameters given to the bake (for example `--params '{"moss.amount": 0.5}'`).
  `settings.json` holds only what a person has chosen to set; the full list of every control with its default is the controls table `recipe/controls.md` (made by `recipe/make_controls_table.py`).
* **To add a control to your layer**: add one line to your file's `CONTROLS`, for example
  `Control('drip_length', 'Drip Length', 0.08, 0.0, 0.5, 'how far a moss drip runs down a slate, in tile units')` (setting name, socket label, default, lowest, highest, plain sentence).
  It becomes a socket on your box and a setting `moss.drip_length`, and you read it inside `build_group` with `b.input('Drip Length')`. A colour control uses `kind='colour'` and a `'#rrggbb'` default
  (converted from ordinary colour numbers to linear for you). A control that changes how many nodes the box has (a count) uses `build_time=True` and is read from `li.resolve(...)` while building instead of being a socket.
* **Do not edit `settings.json`** while the other layers are being built (four people, one file). Put your tuned values in your file's `CONTROLS` defaults; they are written into `settings.json` at the end.
* Defaults should be **measured guesses** from the reference as a GUIDE (palette of up to 12 colours, patch sizes, share of moss, ...). Nothing may be copied from the picture slate by slate or patch by patch, no per-slate lists, no automatic optimiser.

## 7. COMBINE: how the layers meet

* Stack order (bottom first), setting `recipe.stack_order`: `colour_and_fade, moss, damage, outline_and_shadow`.
* Colour: start with the bottom layer's Colour; then for each next layer `colour = mix(colour so far, layer Colour, layer Mask)`.
* Height: `base_height + Height Gain x (sum of all layers' Height)`, cut to 0..1. (`Height Gain` default 1.)
* Roughness: `Base Roughness (0.8) + sum of all layers' Roughness`, cut to 0..1.
* Metallic: one number for the whole surface (0 for slate). Layers do not make metallic.
* The recipe's outputs are `Colour`, `Roughness`, `Metallic`, `Height` (what `lib/bake_harness.py` photographs).

## 8. How to write, bake and test your layer

1. Open your own file in `layers/` (the placeholder explains what to keep). Keep `LAYER_KEY`, `GROUP_NAME`, `DEFAULT_SEED`, `CONTROLS`, `DECLARED_LINKS`, `build_group(parameters)` and end with `b.finish_layer(mask, colour, height, roughness)`. Edit only that file.
2. The helper `LayerBuilder` (in `layer_interface.py`, a thin layer over `lib/contrib/builder.py`) lets you write nodes like a list of sums: `b.add`, `b.sub`, `b.mul`, `b.div`, `b.mn`, `b.mx`, `b.lt`, `b.gt`, `b.frac`, `b.floor`, `b.maprange(value, from_min, from_max, to_min, to_max, clamp, interpolation)`,
   `b.smoothstep`, `b.mix(colour_a, colour_b, factor)`, `b.mixf`, `b.ramp`, `b.window`, `b.noise`, `b.tileable_noise`, `b.noise01`, `b.hash4`, `b.gauss_like`, `b.vec`, `b.xyz`, `b.sqrt`, `b.exp`, `b.power`, `b.sum_of`, `b.input('Socket Name')`, `b.bundle()`.
   Read `layers/layout.py` for a long example and `layers/damage.py` for the shortest.
3. **Bake your layer alone** (debug view) with the harness, for example the damage mask at 512 dots:
   `blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- recipes/slate_layers/recipe/slate_recipe.py OUT_FOLDER --size 512 --params '{"debug_view": "damage.mask"}'`
   The picture is in `colour.png` (grey) and, exactly (16 bit), in `height.png`. Views: `<layer>.mask`, `<layer>.colour`, `<layer>.height`, `<layer>.roughness` (height and roughness are shown as 0.5 + 5 x or 2 x the change),
   and `bundle.<name>` for any of the eleven numbers, plus `bundle.piece_colour` and `bundle.joints`. For several views in one Blender run use `tests/bake_tools.py`.
4. **Bake the whole recipe**: the same command without `--params`, with `--size 1254 --normal-reference slate`.
5. **Prove the tile repeats**: `python3 -I tests/half_tile_test.py 512 OUT_FOLDER` (slides everything by half a tile and compares; also with `recipe.tiles_across` = 2).
6. **Prove independence**: `python3 -I tests/independence_test.py 384 OUT_FOLDER` (Amount 0 and Seed + 1 for every layer; the share of dots that changed outside the layer's own mask must be 0 except for the declared links).
7. Time: the skeleton (layout + four empty layers) takes about 13 seconds per picture at 1254 dots and 4 samples. Please keep your layer under about 20 seconds more.

## 9. Not done yet / limits of this interface (honest)

* The bundle has no per-corner distances and no "distance to the nearest joint corner"; a layer that wants those must compute them from `local_x`, `local_y`, `piece_width`, `piece_height`.
* `edge_distance` and `gap_mask` are decided per dot, so on a slate edge they have a one-dot staircase unless Cycles takes several samples per dot (the harness takes 4; 16 is cleaner, see `tests/bake_tools.py`).
* The layout does not model overlap (a slate lying over the slate below with a real shadow); the dark band between rows and OUTLINE AND SHADOW stand in for it.
* Slate widths come from six independent random numbers per row, scaled to fill the row; the widest slate in 48 is about 1.2 times the median (the reference has one at 2 times). More spread needs a heavier-tailed random number.
