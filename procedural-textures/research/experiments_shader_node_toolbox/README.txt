Experiments for "02 Research - the shader node toolbox.md" (Blender 5.2.2, CPU Cycles). Every script starts with a plain note of what it does.
Run a script like:  blender -b --disable-autoexec -t 2 --python SCRIPT.py     (some take picture names after "--")

Helpers
  probe_tools.py       render a node group as exact numbers (EXR) or as a lit scene; seam measure
  sweeps.py            "what does this setting do" picture strips (uses ../../lib/make_strip.py)
Listing what Blender 5.2.2 contains
  introspect_nodes.py          -> nodes_shader.json, nodes_geometry.json, nodes_summary.txt (every node, its settings, inputs, outputs)
  list_addable_nodes.py        -> addable_nodes.txt (what can really be added in a shader tree and in a Geometry Nodes tree)
Measurements (numbers, written as json)
  t01_noise_measurements.py, t01b_noise_points.py   -> noise_measurements.json, noise_measurements_2.json
  t03b_map_range_numbers.py                           -> map_range_numbers.json
  t06_misc_checks.py                                  -> misc_checks.json   (use_nodes warning, Float Curve ends, Brick, Voronoi ranges, Gabor, Shader to RGB, Mapping)
  t07_geometry_nodes_textures.py                      -> gn_checks.json + 2 pictures
  t09_more_checks.py                                  -> more_checks.json
  t10_which_patterns_wrap.py                          -> which_patterns_wrap.json
  t11_home_made_brick.py                              -> home_made_brick.json + picture
Pictures (all in pictures/)
  t02_pattern_pictures.py      p*.png   pattern makers
  t03_shaper_pictures.py       s*.png   shapers
  t04_surface_effects.py       e01-e05  Bump and Normal Map
  t04b_surface_effects_3d.py   e10-e15  Displacement, Bevel, AO, Pointiness, Fresnel/Layer Weight, Wireframe
  t05_principled_and_puddles.py  m01 (Principled sweeps), m02 (puddle stages)
Toolbox-only first attempts at the six surfaces
  mini_recipes/toolbox_demo_recipes.py   (bake with lib/bake_harness.py, see its top note); mini_recipes/out/<surface>/ has colour/height/normal/score.json/sheet.png
  (folders ending _hc used height made from the colour brightness)
