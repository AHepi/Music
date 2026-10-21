#!/bin/bash
# What this file does (plain words): builds stage/kit_copy/, a fresh COPY of the film kit's stage, scenes and renderer (the same way the first painter test and the behind step did),
# so the new wet FRONT painting and the new wet BEHIND painting can be shone onto the film's real lockout 3D set the way the film does it, WITHOUT touching the film project.
# Big files (the 3D sets, node_modules, other assets) are links to the film project's own files and are only read.
# Three small edits are made to the COPY of the lockout scene file (the film's file is never touched):
#   1. the two painting file names can be given in the address (?painting=NAME&behind=NAME), so one copy shows every combination (the same edit as the first test);
#   2. any "finishing look" value of the scene can be overridden from the address with lk_NAME=NUMBER (for example lk_contrast=1.0), so one copy can show what each look setting does.
#   3. (the brightness fix) ?tone=painted turns on the stage's new look value toe and a lighter frame edge (vignette 0.25), see tools/patch_engine.py. With nothing in the address, all three edits do nothing: the scene is the film's own.
# The paintings are saved as real JPEGs of quality 92, like the film's own lockout-painted.jpg and lockout-behind.jpg (1536 x 2730), next to the film's files in the copy:
#   lockout-r2-front.jpg = the new front painting (front_painting_final.png)    lockout-r2-behind.jpg = the new behind painting (behind_painting_final.png)
# Run: bash tools/set_up_stage_copy.sh
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
FILM=/home/user/Music/austerity-explainer/film-kit
K="$HERE/kit_copy"
PAINT="$HERE/../paint"
rm -rf "$K"; mkdir -p "$K/paper-film/tools" "$K/examples/lockout-test" "$K/assets/models/pit-village"
cp -r "$FILM/paper-film/stage" "$K/paper-film/stage"
cp -r "$FILM/paper-film/scenes" "$K/paper-film/scenes"
cp "$FILM/paper-film/tools/render-paper-film.mjs" "$K/paper-film/tools/"
ln -s "$FILM/paper-film/node_modules" "$K/paper-film/node_modules"
ln -s "$FILM/paper-film/pieces" "$K/paper-film/pieces"
ln -s "$FILM/paper-film/package.json" "$K/paper-film/package.json"
cp "$FILM/examples/lockout-test/timeline.json" "$K/examples/lockout-test/"
# the other scenes' timelines (for drawing another existing scene before and after the fix)
for d in "$FILM"/examples/*; do n=$(basename "$d"); if [ "$n" != lockout-test ]; then ln -s "$d" "$K/examples/$n"; fi; done
for d in "$FILM"/assets/*; do n=$(basename "$d"); if [ "$n" != models ]; then ln -s "$d" "$K/assets/$n"; fi; done
for d in "$FILM"/assets/models/*; do n=$(basename "$d"); if [ "$n" != pit-village ]; then ln -s "$d" "$K/assets/models/$n"; fi; done
for f in "$FILM"/assets/models/pit-village/*; do ln -s "$f" "$K/assets/models/pit-village/$(basename "$f")"; done
python3 -I - <<PY
import cv2
K = "$K/assets/models/pit-village/"
for src, name in (("$PAINT/front_painting_final.png", "lockout-r2-front.jpg"), ("$PAINT/behind_painting_final.png", "lockout-r2-behind.jpg")):
    img = cv2.imread(src)
    assert img.shape[:2] == (2730, 1536), (src, img.shape)
    cv2.imwrite(K + name, img, [cv2.IMWRITE_JPEG_QUALITY, 92])
PY
python3 -I - <<PY
p = "$K/paper-film/scenes/lockout-test.js"
s = open(p).read()
a = "loadTexture(\`\${SET}/lockout-painted.jpg\`), loadTexture(\`\${SET}/lockout-behind.jpg\`)"
assert s.count(a) == 1
s = s.replace(a, "loadTexture(\`\${SET}/\${new URLSearchParams(location.search).get('painting') ?? 'lockout-painted.jpg'}\`), loadTexture(\`\${SET}/\${new URLSearchParams(location.search).get('behind') ?? 'lockout-behind.jpg'}\`)")
b = "const VIEW = new URLSearchParams(location.search).get('view') ?? 'move';"
assert s.count(b) == 1
s = s.replace(b, b + "\n// (copy only) THE BRIGHTNESS FIX, switched on from the address (?tone=painted): the stage's new look value toe (the filmic curve may brighten but no longer darkens dark painted values) and a lighter dark frame edge (vignette 0.30 -> 0.25). Without it the scene is the film's own. In the real film these two values would simply be written into the look line below.\nconst PAINTED_TONE = new URLSearchParams(location.search).get('tone') === 'painted';\nconst PAINTED_TONE_LOOK = { toe: 1, vignette: 0.25 };\n// (copy only) finishing look values can be overridden from the address: lk_contrast=1.0 sets look.contrast; nothing in the address = the film's own look\nconst LOOK_OVERRIDES = Object.fromEntries([...new URLSearchParams(location.search)].filter(([k]) => k.startsWith('lk_')).map(([k, v]) => [k.slice(3), Number(v)]));")
c = "look: { exposure: 1.0, aperture: close ? 1.6 : 2.5, maxBlur: close ? 10 : 7, glowThreshold: 0.9, glowStrength: 0.6, contrast: 1.04, vignette: 0.3, fade } };"
assert s.count(c) == 1
s = s.replace(c, "look: { exposure: 1.0, aperture: close ? 1.6 : 2.5, maxBlur: close ? 10 : 7, glowThreshold: 0.9, glowStrength: 0.6, contrast: 1.04, vignette: 0.3, fade, ...(PAINTED_TONE ? PAINTED_TONE_LOOK : {}), ...LOOK_OVERRIDES } };")
s = "// NOTE (plain words): COPY of the film kit's lockout-test.js, made for the wet street painter test, round 2 (stage step). Three changes only: the painting and the behind picture file names can be given in the address (?painting=NAME&behind=NAME), the brightness fix can be switched on from the address (?tone=painted), and any look value can be overridden from the address (lk_NAME=NUMBER). With nothing in the address it is the film's own scene.\n" + s
open(p, "w").write(s)
PY
du -sh "$K"; ls -la "$K/assets/models/pit-village" | grep r2
