# Requests from the ground builder to the integrator (things I must not change myself)

1. Move the ground section into the set files. Today it sits in `kits/weathering/ground/ground_sets/<set id>.json` (the layers read `settings.ground` first, then this file).
   The street one has `role_dials`, `rings`, `readable` and `dial_sheet`; the courtyard one has `role_dials` only. Moving it into `sets/*.json` under the key `ground` changes nothing.
2. The bus's picture-based masks (`tx_*`) read a constant rectangle for setts and flags (one value per tile, the defaults are used) and the texture is set to EXTEND, not REPEAT.
   The ground layers read the pictures themselves (own Image Texture nodes, REPEAT, UV, per-material index `wk_tx_index`), so they work, but every other layer that reads `M Tx ...`
   on setts or flags gets the defaults. Worth a look in `masks/bus.py`.
3. The extra dials (`moss_lift`, `ref_brightness`, `film_octaves` ...) are registered by `ground/dials_ground.py` at register time. If you want them in the preset files, they need a
   `ground` block in the look (`ground/looks_ground/<look id>.json` is read for now, `{layer: {dial: value}}`).
4. The P7 first-picture line (+3.4 s against 2.26 s) cannot be met by any layer that adds nodes: every active kit layer costs about 5 s of EEVEE shader compile once per scene file
   (measured: one layer 5-6 s, all four 15-17 s, with element-pruned groups and without). The plate drawing time itself is inside the line. Please decide whether the first-picture line
   counts for the whole kit or per layer.
5. `harness/lint_no_set_names.py` accepts the ground code today (0 hits). The sets' names stay in the sidecar JSON only.
6. `harness/remote.py` syncs only the kit folder and the job files to the machine, so a `feature_report.json` written beside a builder's notes never reaches the runner there and the camera
   `flag_close` falls back to its own look_at. Pass the folders of `feature_report_dirs` as `extra_roots` to `run_batch` (the ground builder aimed its own extra cameras instead, with
   `ground/runner_ground.py`).
7. `presets/sooty_1926.json` pins every Appendix A dial of the four layers, so a default written by the layers (or a value in `ground/looks_ground/<look>.json`) never wins. The values the
   ground builder would like in the preset: groundcracks `near_only` 20, `site_bias` 0.9 (extra dial); dirt `polish_lift` 0; iron `rust_cover` 0.5. The period shares measured on the
   plan pictures are already inside their caps at the preset's own values.
8. P2 (wet look): the element wet-to-dry lines ask each element's dots to be no brighter wet than dry; none of the four ground layers meets it (ratios 1.0 to 3.5) and the road's
   wet-to-dry ratio is 0.05 off in 5 of 16 pictures. If the line is meant for every layer, a shared fix (a wet-state matt on the layer's dots) may belong in the kit's hook.
