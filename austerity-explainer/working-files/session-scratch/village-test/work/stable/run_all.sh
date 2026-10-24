#!/bin/bash
R=/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test
W=$R/work/stable
export PATH=/home/user/Music/plugins/explainer-film/bin:$PATH
export EXPLAINER_FILM_BLENDER_THREADS=2
BL=/home/user/work/blender-app/blender-5.2.2-linux-x64/blender
cd $W
cp $R/scene/ground.blend $W/scene.blend
s=$(date +%s)
$BL -t 2 -b --disable-autoexec $W/scene.blend --python $W/run_stage.py --python-exit-code 1 -- $W/scene.blend > $W/build.log 2>&1
echo "build exit $? $(( $(date +%s)-s )) s" > $W/steps.log
s=$(date +%s)
explainer-film-place finish-part --blender $BL --scene $W/scene.blend --settings $R/plan/place-settings.json --owner stable --quick --save-as $W/part.blend > $W/finish_part.log 2>&1
echo "finish-part exit $? $(( $(date +%s)-s )) s" >> $W/steps.log
s=$(date +%s)
explainer-film-place construction --blender $BL --scene $W/part.blend --settings $R/plan/place-settings.json --owner stable --out $W/construction.json > $W/construction.log 2>&1
echo "construction exit $? $(( $(date +%s)-s )) s" >> $W/steps.log
s=$(date +%s)
explainer-film-place normals-test --blender $BL --scene $W/part.blend --settings $R/plan/place-settings.json --out $W/normals.json > $W/normals.log 2>&1
echo "normals-test exit $? $(( $(date +%s)-s )) s" >> $W/steps.log
s=$(date +%s)
explainer-film-place combine --blender $BL --scene $R/scene/ground.blend --stages $R/stages/stage_stable.py --order plain --owners $R/plan/ownership.json --out $W/combine.json > $W/combine.log 2>&1
echo "combine exit $? $(( $(date +%s)-s )) s" >> $W/steps.log
echo ALLDONE >> $W/steps.log
