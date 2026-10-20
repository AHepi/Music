What this folder is: the working files for the guide "02 Research - geometry nodes, curves, modifiers and physics for surface detail.md"
(one folder up). Everything here was run in Blender 5.2.2 on this CPU-only machine. Plain command for any script that is not marked "plain Python":
    /home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python SCRIPT.py -- [arguments]
Every file starts with a plain note saying what it does.

THE SEVEN RECIPES (each builds real geometry, photographs it from above, writes colour.png, height.png (16 bit), normal.png, normal_geometry.png, photo.json)
  recipe_brick_layout.py        brick wall (row layout, bevel, tileable noise, mortar)                 111 s at 1254 px (with ambient occlusion), 31 s without
  recipe_slate_layout.py        overlapping slate roof (tilted slates, ragged edges, moss)               94 s
  recipe_gravel_rigidbody.py    gravel dropped with Rigid Body physics, three settle rounds for the wrap 263 s (834 stones, about 60 s of it physics)
  recipe_curve_ruts.py          mud with wheel ruts made from curves + Geometry Proximity, puddles, stones 132 s
  recipe_riveted_metal.py       riveted steel straps and braces, rivets from curves, rust, edge wear    157 s
  recipe_wood_planks.py         planks with curve-made grain, cracks and knots                           114 s
  recipe_gravel_scatter_gn.py   gravel with no physics: Repeat-zone relaxation + convex-hull stones      140 s (geometry itself about 1-3 s)
  Run one:  ... --python recipe_brick_layout.py -- OUT_FOLDER --size 1254 --ao 0.8      (--ao 0 = much faster colour picture)
  Run all six of the first group + score them:  bash run_all_full_bakes.sh ;  the seventh + strips:  bash run_extras.sh

SHARED BUILDING BLOCKS
  gn_tools.py       GeoWriter (build Geometry Nodes groups from Python), the "photo booth" (height/colour/normal materials, photograph_geometry), repeating (tileable)
                    noise groups, colour ramp helper, modifier input setter for Blender 5.2. Sits on lib/bake_harness.py and lib/recipe_tools.py; changes nothing in lib/.
  layout_tools.py   the row layout group (bricks, slates, planks) with wrap-around copies
  relax_tools.py    the relax-points-on-a-wrapping-tile group (Repeat zone)

TESTS AND EXPERIMENTS (numbers are in the guide; raw results in out/)
  t01_zdepth_routes.py         six ways to draw height, compared with the truth                      -> out/t01_zdepth/results.json
  probe_gn_api.py              what the Geometry Nodes Python API looks like in 5.2 (prints only)
  t02_layout_check.py, t02b_accumulate_semantics.py    row layout numbers; Accumulate Field Leading/Trailing
  t03_rigidbody_ghost_probe.py Python-stepped Rigid Body and kinematic ghost updates (run with -- plain  or  -- ghost)
  t05_modifier_gallery.py      12 modifier pictures                                                  -> out/t05_modifiers_sheet.png
  t06_relax_repeat_zone.py     random vs Poisson vs Repeat zone vs Simulation zone spacing           -> out/t06_relax/results.json
  t06b_bake_node.py            Bake node headless                                                    -> out/t06_relax/bake_node_results.json
  t07_wrap_tests.py + measure_wrap.py (plain Python)   wrap on/off seam measurements                  -> out/t07_wrap_sheet.png, out/t07_wrap/seams.json
  t09_capture_attribute.py     Capture Attribute / Store Named Attribute before Realize Instances    -> out/t09_capture_results.json
  t08_boolean_speed.py         Boolean timing                                                        -> out/t08_boolean_speed.json
  hybrid_height_experiment.py (plain Python)  geometry height vs hybrid vs colour-brightness height scored against the references -> out/hybrid/*/hybrid_results.json
                    (the pictures of those variants were deleted to save space except for brick; re-run the script to make them again)
  collect_results.py (plain Python)  gathers all bake numbers -> results_summary.json, out/results_tables.md
  fig_settings_strips.py, fig_relax_points.py, make_overview_sheet.py   the figures in out/
  analyse_reference_palettes.py (plain Python)  main colours of the reference pictures (analysis only; no recipe reads a reference picture) -> reference_palettes.json
  list_assets.py, measure_edge_bias.py, dbg_*.py     small helpers used while debugging (kept as a record)

RESULTS FOLDERS
  out/full/<recipe>/     the final 1254 x 1254 sets, photo.json (settings + timings), score.json and sheet.png (comparison with the reference)
  out/gravel_noghost, out/gravel_rounds, out/gravel_test, out/gravel_ghost_check   512 / 64 px physics experiments (no ghosts / three rounds / ghosts)
  out/strips/            "what does this setting do" strips for the brick recipe
  out/overview_all_recipes.png   every recipe next to its reference
