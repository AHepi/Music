"""What this does: copies the newer and missing film kit files into the explainer-film plugin's kit, from an
explicit list (nothing is copied by pattern, so pictures, models and round 5's working files cannot slip in).
Files the plugin had improved on its own are not in the list; they are merged by hand afterwards.
It prints each copy and writes a list of what it did (JSON) beside itself.

Use: python3 -I copy_film_kit_to_plugin.py FILM_KIT PLUGIN_KIT [--dry-run]
"""
import json
import os
import shutil
import sys

FILM_KIT, PLUGIN_KIT = sys.argv[1], sys.argv[2]
DRY_RUN = '--dry-run' in sys.argv

# film kit path -> plugin kit path (the plugin keeps the numbered documents in docs/ with a "paper-look - " prefix)
DOCS = {name: f'docs/paper-look - {name}' for name in [
    '01 How to make a film with this kit.md', '05 Lessons and traps.md', '07 Composing a shot.md']}

# older in the plugin and never changed there (each plugin copy equals an earlier film kit version): overwrite
NEWER = [
    'paper-film/scenes/cinema-chapter.js', 'paper-film/scenes/cinema-kit.js', 'paper-film/scenes/graphics.js',
    'paper-film/stage/cinema-stage.js', 'paper-film/stage/cinema-stage.html',
    'paper-film/tools/check_shot.py', 'paper-film/tools/profile_frame.mjs', 'paper-film/tools/render-paper-film.mjs',
]

MISSING = [
    '.gitignore',
    'narration-tools/estimate_timeline.py',
    # tools
    'paper-film/tools/make_state_picture.py', 'paper-film/tools/make_behind_picture.py',
    'paper-film/tools/fit_station_proxies.py', 'paper-film/tools/station_plates.py',
    # shared scene code for built-and-painted places
    'paper-film/scenes/projected-set.js', 'paper-film/scenes/pit-village-effects.js',
    # worked examples (scenes)
    'paper-film/scenes/notice-corner.js', 'paper-film/scenes/people-test.js', 'paper-film/scenes/lockout-test.js',
    'paper-film/scenes/projection-test.js', 'paper-film/scenes/works-states-test.js', 'paper-film/scenes/lazy-loading-test.js',
    'paper-film/scenes/inflation-chapter-2-newcomers.js',
    'paper-film/scenes/inflation-chapter-2-newcomers/page-3.js', 'paper-film/scenes/inflation-chapter-2-newcomers/page-4.js',
    'paper-film/scenes/inflation-chapter-2-newcomers/page-5.js', 'paper-film/scenes/inflation-chapter-2-newcomers/placeholder.js',
    'paper-film/scenes/inflation-chapter-2-newcomers/works-effects.js',
    'paper-film/scenes/house-sample.js', 'paper-film/scenes/house-sample/house-set.js', 'paper-film/scenes/house-sample/page-1.js',
    'paper-film/scenes/cinema-test-relief.js', 'paper-film/scenes/graphics-test.js',
    'paper-film/scenes/sam-3d-petrol-station-test.js', 'paper-film/scenes/station-proxies-test.js',
    # Blender: the pit village (street, set dressing, props library, three shots), figures, chapter 2's props, checker tests
    'paper-film/blender/pit-village/build_street.py', 'paper-film/blender/pit-village/set_dressing.py',
    'paper-film/blender/pit-village/fetch_street_textures.py', 'paper-film/blender/pit-village/assemble_notice_corner.py',
    'paper-film/blender/pit-village/assemble_people_test.py', 'paper-film/blender/pit-village/assemble_lockout.py',
    'paper-film/blender/pit-village/props/build_scripted_props.py', 'paper-film/blender/pit-village/props/convert_poly_haven.py',
    'paper-film/blender/pit-village/props/download_poly_haven.py', 'paper-film/blender/pit-village/props/make_sheet.py',
    'paper-film/blender/pit-village/props/paint_prop_pictures.py', 'paper-film/blender/pit-village/props/poly_haven_choices.py',
    'paper-film/blender/pit-village/props/prop_library.py', 'paper-film/blender/pit-village/props/readability_test.py',
    'paper-film/blender/pit-village/props/render_contact_sheet.py', 'paper-film/blender/pit-village/props/scripted_kit.py',
    'paper-film/blender/pit-village/props/fonts/00 Fonts - where to get them.md',
    'paper-film/blender/pit-village/props/fonts/abrilfatface-OFL.txt', 'paper-film/blender/pit-village/props/fonts/alfaslabone-OFL.txt',
    'paper-film/blender/pit-village/props/fonts/oldstandardtt-OFL.txt',
    'paper-film/blender/figures/build_figures.py', 'paper-film/blender/figures/figure_sheet.py',
    'paper-film/blender/figures/fetch_cloth_textures.py',
    'paper-film/blender/inflation-chapter-2-newcomers/props/build_chapter_2_props.py',
    'paper-film/blender/inflation-chapter-2-newcomers/props/chapter_2_choices.py',
    'paper-film/blender/inflation-chapter-2-newcomers/props/paint_chapter_2_pictures.py',
    'paper-film/blender/tests/notice_corner_test_scene.py', 'paper-film/blender/tests/run-checker-tests.sh',
    # examples: timelines and check files (small JSON)
    'examples/notice-corner/shot-check.json', 'examples/notice-corner/timeline.json',
    'examples/people-test/shot-check.json', 'examples/people-test/timeline.json',
    'examples/projection-test/camera.json', 'examples/projection-test/timeline.json',
    'examples/lockout-test/timeline.json', 'examples/house-sample/timeline.json',
    'examples/inflation-chapter-2-newcomers/timeline-estimated.json',
    'examples/inflation-chapter-2-newcomers/works-w1-shot-check.json',
    'examples/inflation-chapter-2-newcomers/works-w1-working-shot-check.json',
    'examples/inflation-chapter-2-newcomers/works-w2-shot-check.json',
    'examples/inflation-chapter-2-newcomers/works-w2-slowed-shot-check.json',
    'examples/inflation-chapter-2-newcomers/works-w3-shot-check.json',
    # chapter 1's captions and transcripts (text; its recordings, stills and cover stay out)
    'examples/austerity-chapter-1/captions.srt', 'examples/austerity-chapter-1/captions.vtt',
] + [f'examples/austerity-chapter-1/transcripts/page{n}-words.json' for n in range(1, 11)]

LIMIT_BYTES = 5 * 1024 * 1024
done = []
for source_name, target_name in [(name, DOCS[name]) for name in DOCS] + [(name, name) for name in NEWER + MISSING]:
    source = os.path.join(FILM_KIT, source_name)
    target = os.path.join(PLUGIN_KIT, target_name)
    size = os.path.getsize(source)
    if size > LIMIT_BYTES:
        sys.exit(f'refused: {source_name} is {size} bytes, over the 5 MB limit')
    kind = 'overwrite' if os.path.exists(target) else 'new'
    if not DRY_RUN:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(source, target)
    done.append({'from': source_name, 'to': target_name, 'kind': kind, 'bytes': size})
    print(f'{kind:9} {size:8} {target_name}')
print(f'{len(done)} files, {sum(d["bytes"] for d in done)} bytes{" (dry run: nothing copied)" if DRY_RUN else ""}')
if not DRY_RUN:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'copied.json'), 'w') as f:
        json.dump(done, f, indent=1)
