# Requests from the growth builder to the foundation and the integrator

Plain words. Each line says what, why, and the smallest change. Nothing here was changed by the growth builder: the files of `apply/`, `masks/`, `harness/`, `sets/` and `presets/` are untouched.

## For the foundation (the masks)

1. **`keepclear` is 1.0 along the whole outer half of every pavement (from about 3.3 m from the middle of the road to the house wall), for the whole length of the street, not only at the doorsteps.**
   What I saw (street pack, `gp_e` green channel): at y = 3, 6, 8 and 10 m, x = 3.4 to 4.35 reads 1.00 on every row; the only gap in the first 40 m is y 36.1 to 39.0. The rule in the set file is "doorstep strip 0.5 m (reach) from the entrances"; the pavement-walk line is footfall 0.5, which should give keep-clear 0 (the trodden gate starts at 0.5 and reaches 1 at 0.7). So something else puts 1.0 there (the doorstep rule's distance map looks suspect: `masks/footfall.py`, `auto_door_strip`, the `_step_top_coarse` distance).
   Why it matters: no weed or moss may stand where keep-clear is 0.5 or more (P6), so **the wall foot can have no plant at all** (the plan's "2 to 5 % of wall-foot length with a plant" and the ivy-leaved toadflax at damp mortar are impossible on this pack). The wall-foot population of the growth layer is built and tested on a made-up scene but sits at 0 in the street.
   Smallest change: check `keepclear` against the doorstep rule alone (a disc of about 1.2 m round each entrance plus 0.5 m); if the wall-foot band is meant to be clear on purpose, say so and I will drop the wall-foot dial from the street look.
2. `rubbish_heap` is drawn on the ground plan only where the earlier litter layer's mask is; litter lying on the kerb top (higher than the flags) shares its x and y with plants at the kerb foot. The growth layer therefore keeps 5 cm clear of the litter pieces in x and y only (not in height). If the foundation's litter-proximity measure should be in three dimensions, say so.

## For the integrator (look and set values)

3. The look's growth block has `inflate_limit` 6. The growth layer does not use it (plants keep their resolution); it uses its own dial `piece_inflate_limit` (default 3, as the plan says). Nothing to change; the preset may carry `piece_inflate_limit` too if you want it visible.
4. New dials of the growth layer (all in `growth/dials_growth.py`, kit defaults suit any set): `piece_inflate_limit`, `moss_smother_from`, `moss_smother_to`, `existing_avoid`, `avoid_m`, `colour_gain`, `colour_sat`, `min_dots_scale`, `show_kind`, `realise`, `cand_density_scale`. The plate brightness is set in `growth/species.json` (`material.albedo_gain` 8, `saturation_gain` 0.8, `wet_dark_boost` 2.4): the plants are lit only by the dusk lamps and must land at plate brightness 0.30 to 0.35 on a 0.19 wet road, so their albedo is lifted; the look's `colour_gain` 1 means "as in species.json".
5. The set-specific choices of the growth layer are in `growth/growth_sets/<set id>.json` (a sidecar, because builders may not edit `sets/`). Please move each file into the set file as the key `growth` (the code reads the set file first). Same for `growth/looks_growth/*.json` (extra dial defaults per look).
6. `wet_dark` is 0.7 in the look. The plants' wet/dry brightness lands at 0.64 to 0.84 (moss band 0.55 to 0.85) with the species file's `wet_dark_boost` 2.4; if the preset's `wet_dark` changes, the P2 band must be re-measured.
7. The harness's `runner.py` calls `scale_module.set_scale` for every picture; the growth layer wraps that function once (`growth/apply_growth.py`, `_install_scale_hook`) so the plants know the dot size. If the runner ever stops calling it, the widening stays at its default dot angle.

## Not mine, noticed

8. `harness/measure_zones.py` `pieces_test` counts a weed "within 5 cm of a rubbish piece" by the distance between the two plants' origins in x and y; a rubbish lump's origin is its centre, so this is stricter than the distance to its surface. The growth layer passes it (0 of 123 to 210 weeds) because it measures to the surface, also in x and y only.
