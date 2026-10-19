# Notes for everyone building a part of the mine (read first)

Where: ./
- lib/mine_common.py  the shared toolbox (READ IT FULLY before you start; do NOT edit it). LAYOUT, ground_height(), track_point(), surface_material(), plain_material(), glow_material(), MeshBuilder, use_real_displacement(), preview_stage(), render_preview().
- textures_ready/     the prepared pictures + maps (brick, slate, wood, metal, mud, gravel). Do not edit.
- pictures/           the design pictures: pithead_building_with_headframe.png, headframe_tower.png, chimney_with_smoke.png, mine_cart_with_coal.png, curved_rail_track.png, reference_scene_screenshot.jpg (the finished look we are aiming for: a painted, moody dusk pit village in a TALL portrait frame).
- tests/test_swatches.py, tests/test_ground_displacement.py  show how materials, MeshBuilder and real displacement are used.

Run Blender like this (always with -t 2 so six helpers do not starve each other):
  /home/user/work/blender-app/blender-5.2.2-linux-x64/blender -b --disable-autoexec -t 2 --python YOUR_SCRIPT.py -- args
Keep preview photos small (<= 900 px, <= 40 samples, under about 2 minutes each).

Rules of the job
- Plain Blender only. Do NOT use the explainer-film plugin, the Astra add-on, anything under /home/user/Music/plugins or /home/user/Music/austerity-explainer. Do not touch git.
- Only create/edit your own files: modules/<yourmodule>.py, previews/<yourmodule>_preview.py, out/<yourmodule>_*.png and out/<yourmodule>_report.json. Do not read or edit other helpers' files.
- Your module must define  build(collection_name='Mine') -> dict  that creates the part in WORLD coordinates (objects sit at the origin with points already in place, as MeshBuilder does) according to mc.LAYOUT, seats things on the ground with mc.ground_height(x, y), and returns {'objects': [names], 'notes': '...'}. It must NOT create cameras, world/sky, render settings or scene lights, unless your brief says so. Importing: sys.path.insert(0, <lib folder>); import mine_common as mc.
- Look: all large surfaces must use the uploaded surfaces through mc.surface_material('brick'|'slate'|'wood'|'metal'|'mud'|'gravel', tint=..., ...). Use plain_material only for small things (glass, glow, rope, coal black, stone-grey footings). Use mc.use_real_displacement(obj) on big close-up surfaces where the bumps matter (brick walls, slate roof, mud, gravel, ballast); keep an eye on render time. Variation=0.25 breaks up repetition; use tint to make parts differ.
- Match the design pictures: shapes, proportions, details, wear. This is a painted, slightly stylised, gritty industrial look; chunky, readable shapes beat tiny detail. Study your picture(s), build, render previews from 3 angles (front-left 3/4 like the reference camera, a close detail view, a back/side view), LOOK at them (use the Read tool on the png) next to the design picture, fix what is wrong, repeat until it honestly looks right. Fix z-fighting (surfaces on the same plane), floating or sunk parts, stretched or mirrored textures, wrong scale.
- Known facts: normal maps are already flipped for Blender and verified. Coplanar faces render black/flicker: keep 1-2 cm apart. Horizontal quad panels need the ground not at exactly the same height. Real displacement relief is already tuned small (mud 6 cm, gravel 4 cm, brick 3 cm); do not make tiles smaller than the defaults except for small objects.
- Efficiency: build thousands of shapes in ONE MeshBuilder per material group (one object per group), not one Blender object per shape. Aim for under ~300k triangles for your whole part before displacement.
- Finish by writing out/<yourmodule>_report.json {object_count, triangle_count, uses_real_displacement: [...], build_seconds, known_flaws: [...]} and give your final answer as the structured result. Be honest about flaws.
