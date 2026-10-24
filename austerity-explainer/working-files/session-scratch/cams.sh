# usage: cams.sh PREFIX OUTDIR
. /tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/env.sh
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad
P=$1; OUT=$2
shot() { # name lens camx camy camz lookx looky lookz
cat > $S/cam_tmp.py <<PY
import bpy
from mathutils import Vector
c = bpy.data.objects['cam']; c.data.lens = $2
c.location = ($3, $4, $5)
c.rotation_euler = (Vector(($6, $7, $8)) - c.location).to_track_quat('-Z', 'Y').to_euler()
bpy.context.view_layer.update()
result = 'ok'
PY
$C run-file $S/cam_tmp.py > /dev/null 2>&1
F=$($C render_viewport_to_path "{\"output_path\":\"$P-$1.png\"}" 2>&1 | grep filepath | sed 's/.*: "\(.*\)".*/\1/')
cp "$F" $OUT/ && echo "$OUT/$P-$1.png"
}
shot overview 35 -0.6 -3.0 1.3   -0.05 0.25 0.35
shot cart 40 0.05 -1.1 0.38   0.45 -0.05 0.12
shot barrels 45 -1.05 -0.75 0.4   -0.7 0.15 0.1
shot crates 40 -0.55 -1.0 0.55   -0.2 0.35 0.18
shot lamp 60 0.6 -1.0 1.3   0.0 0.75 1.1
F=$($C render_thumbnail_to_path "{\"output_path\":\"$P-thumb.png\"}" 2>&1 | grep filepath | sed 's/.*: "\(.*\)".*/\1/'); cp "$F" $OUT/
