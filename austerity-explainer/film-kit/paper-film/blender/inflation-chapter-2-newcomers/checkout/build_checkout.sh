#!/usr/bin/env bash
# What this does: builds "the checkout" for chapter 2 (plan 34, part 1 "B. The checkout"), the film's opening picture, in
# order, into the checkout's own folder (assets/models/inflation-chapter-2-newcomers/checkout), never beside the pit
# village's notice corner or the Works:
#   1. (--fetch SCRATCH) the free Poly Haven models and surfaces in checkout_choices.py, downloaded into SCRATCH/downloads
#      and turned into the checkout's own prop library (checkout/props, with its own index.json); the three surfaces the
#      scripted props wear are kept beside the room's in checkout/textures; Poly Haven's steel frame shelves come ten
#      times too big (21.4 m tall): the assembly shrinks them
#   2. (--fonts FOLDER) the lettered pictures (paint_checkout_pictures.py: the newspaper bill, BREAD, MILK, BUTTER, CHEESE,
#      CHECKOUT, PETROL · DIESEL) into checkout/textures; the fonts: fonts/00 Fonts - where to get them.md
#   3. the film's files: assemble_checkout.py --export (checkout-set.glb, checkout-signs.glb, checkout-camera-c1.json,
#      checkout-shot.json)
#   4. (--plates FOLDER) the plates (assemble_checkout.py's PLATES) as PNG into FOLDER, then each as a JPEG (quality 95)
#      beside the film's files; the render log is kept as FOLDER/plates.log (look in it for "Shadow buffer full" and
#      "Could not allocate shadow atlas")
#   5. an empty .blend in the scratch or plates folder (checkout-empty.blend) for the shot checker to open first: the
#      checkout is built from an empty scene, so the checker needs no base file
# Use (from anywhere; a virtual screen is needed for the plates: Xvfb :96 -screen 0 1920x1080x24 &):
#   paper-film/blender/inflation-chapter-2-newcomers/checkout/build_checkout.sh [--fetch SCRATCH] [--fonts FOLDER] [--plates FOLDER]
# Then the shot checker (from the kit's top folder):
#   BLEND=FOLDER/checkout-empty.blend paper-film/tools/check-shot.sh paper-film/blender/inflation-chapter-2-newcomers/checkout/assemble_checkout.py \
#       examples/inflation-chapter-2-newcomers/checkout-c1-shot-check.json OUT [PICTURE]
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
kit=$(cd "$here/../../../.." && pwd)
checkout="$kit/assets/models/inflation-chapter-2-newcomers/checkout"
BLENDER=${BLENDER:-/home/user/work/blender-app/blender-5.2.2-linux-x64/blender}
fetch=""; fonts=""; plates=""
while [[ $# -gt 0 ]]; do
  case $1 in
    --fetch) fetch=$(mkdir -p "$2" && cd "$2" && pwd); shift 2 ;;
    --fonts) fonts=$(cd "$2" && pwd); shift 2 ;;
    --plates) mkdir -p "$2"; plates=$(cd "$2" && pwd); shift 2 ;;
    *) echo "build_checkout.sh: unknown setting $1"; exit 1 ;;
  esac
done
# 1. the Poly Haven models and surfaces
if [[ -n $fetch ]]; then
  python3 -I "$kit/paper-film/blender/pit-village/props/download_poly_haven.py" "$fetch/downloads" --choices "$here/checkout_choices.py" \
    --textures "$checkout/textures"
  "$BLENDER" -b --python "$kit/paper-film/blender/pit-village/props/convert_poly_haven.py" -- --choices "$here/checkout_choices.py" --scratch "$fetch"
  for surface in ash_veneer metal_plate asphalt_02; do
    python3 -I -c "import sys; from PIL import Image; Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2], quality=88); \
Image.open(sys.argv[3]).convert('RGB').save(sys.argv[4], quality=92)" \
      "$fetch/downloads/surfaces/$surface/Diffuse.jpg" "$checkout/textures/${surface}_colour.jpg" \
      "$fetch/downloads/surfaces/$surface/nor_gl.jpg" "$checkout/textures/${surface}_normal.jpg"
  done
fi
# 2. the lettered pictures
if [[ -n $fonts ]]; then
  python3 -I "$here/paint_checkout_pictures.py" "$checkout/textures" --fonts "$fonts"
fi
# 3. the film's files
DISPLAY=${DISPLAY:-:96} "$BLENDER" -b --python "$here/assemble_checkout.py" -- --export
# 4. the plates
if [[ -n $plates ]]; then
  DISPLAY=${DISPLAY:-:96} "$BLENDER" -b --python "$here/assemble_checkout.py" -- --plates "$plates" > "$plates/plates.log" 2>&1
  grep -n "Shadow buffer full\|Could not allocate shadow atlas" "$plates/plates.log" && echo "build_checkout.sh: shadow faults in the plates' log" || true
  for picture in "$plates"/checkout-*-plate.png; do
    python3 -I -c "import sys; from PIL import Image; Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2], quality=95)" \
      "$picture" "$checkout/$(basename "${picture%.png}").jpg"
  done
fi
# 5. an empty .blend for the shot checker
empty="${plates:-${fetch:-$checkout}}/checkout-empty.blend"
[[ $empty == "$checkout/checkout-empty.blend" ]] && empty="${TMPDIR:-/tmp}/checkout-empty.blend"
"$BLENDER" -b --python-expr "import bpy, sys; bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.preferences.filepaths.save_version = 0; \
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1])" -- "$empty" > /dev/null
echo "build_checkout.sh: done ($checkout); for the shot checker: BLEND=$empty"
