#!/bin/bash
# usage: measure_wear.sh LOOK STATE
S=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/plugin-work/kit
export BLENDER=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
LOOK=$1; STATE=$2
python3 -I -B /home/user/Music/plugins/explainer-film/kit/place-kit/place_command.py finish --scene $S/probe2/flat_hut.blend --look $LOOK --state $STATE --save-as $S/probe2/m_$LOOK.blend > /dev/null 2>&1
$BLENDER -b --disable-autoexec $S/probe2/m_$LOOK.blend --python $S/render/add_camera.py -- $S/probe2/m_${LOOK}_cam.blend > /dev/null 2>&1
cp $S/place-settings.json $S/probe2/place-settings.json
$BLENDER -b --disable-autoexec $S/probe2/m_${LOOK}_cam.blend --python /home/user/Music/plugins/explainer-film/kit/calculators/tests/fixtures/place/probe_place.py -- renders $S/probe2/m_$LOOK.json --size 160 107 --samples 8 > /dev/null 2>&1
python3 - <<PY
import json
d=json.load(open('$S/probe2/m_$LOOK.json'))
rel=d['mean_difference_as_it_is_vs_removed']/d['mean_brightness_removed']
print('$LOOK/$STATE relative change %.1f%%' % (rel*100), 'master0 max diff', d['max_difference_master_zero_vs_removed'], {k: round(v/d['mean_brightness_removed']*100,2) for k,v in d['mean_difference_only_one_layer_vs_removed'].items()})
PY
